# -*- coding: utf-8 -*-
"""
obnovit_doki_19_08.py · MARKER: DOKI_19_08_V1

ЧТО ДЕЛАЕТ
──────────
Обновляет `БИРЖА.md` и `ЛЕТОПИСЬ_ГРОНДХЕЙМА.md` по состоянию на 19.08.

ГЛАВНОЕ ПРАВИЛО ЭТОГО ПАТЧА
───────────────────────────
Пишем ТОЛЬКО про то, что есть НА ДИСКЕ. Перед записью патч сам
проверяет маркеры в коде и делит работу на две части:

    СДЕЛАНО   — маркер в коде есть
    ЖДЁТ      — патч написан, но не накачен

Это не формальность. Сверка 19.08 показала, что из двух десятков
свежих патчей в репозитории лежат единицы: остальные либо не
запускались, либо остались на машине Шефа. Написать о них как о
сделанном значило бы соврать в документе — с чего и начался весь
разбор БИРЖА.md 14.08.

Идемпотентен, .bak рядом.
Запуск: py obnovit_doki_19_08.py   (или --suho)
"""
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "DOKI_19_08_V1"
SUHO = "--suho" in sys.argv

# маркер → (что это, в каком патче лежит)
RABOTA = [
    ("RUKI_TREYDERA_V1", "руки трейдера: стол, волна, дневник",
     "postavit_ruki_treydera.py"),
    ("RUKI_VSEM_V1", "руки всем трём трейдерам",
     "postavit_ruki_vsem.py"),
    ("RUKA_MAYAKA_V1", "выход в интернет на работе",
     "postavit_ruku_mayaka.py"),
    ("MAYAK_403_V1", "Маяк ходит через прокси (403 вылечен)",
     "pochinit_mayak.py"),
    ("OKNO_ISKATELYA_V1", "искатель зовёт только при волне 100-140",
     "postavit_okno_iskatelya.py"),
    ("OTCHYOT_PROGONA_V1", "отчёт прогона: таблица, кадры, итог",
     "postavit_otchyot_progona.py"),
    ("PROGON_VIDNO_V1", "прогон виден на экране, связь не рвётся",
     "pochinit_progon_na_ekrane.py"),
    ("PRIBORY_NA_STOL_V1", "разворотный бар, зона AO+AC, дивергенция на столе",
     "postavit_pribory_na_stol.py"),
    ("RB_NA_KADRE_V1", "разворотные бары нарисованы на кадре",
     "narisovat_razvorotnik.py"),
    ("RASTYAZHKA_V1", "растяжка волны: трейдер ВИДИТ нужный масштаб",
     "postavit_ruku_rastyazhki.py"),
    ("KRAYNIYE_TOCHKI_V1", "вершина и дно числами, потолок обращений 12",
     "postavit_krayniye_tochki.py"),
    ("KARTINA_SVOYA_V1", "своя картина у каждого, не общая доска",
     "peredelat_dosku_v_lichnuyu.py"),
    ("UCHEBNIK_DISCIPLINY_V1", "учебник Академии по всем дисциплинам",
     "postavit_ruku_uchebnika.py + uchebnik_po_disciplinam.py"),
    ("UCHEBNIK_UCHENIKU_V1", "ученик сам просит рисунок",
     "uchebnik_ucheniku.py"),
    ("RUKI_DOMA_V1", "учебник жителю дома",
     "ruki_zhitelyu_doma.py"),
    ("PAMYAT_RABOTA_ZHIZN_V1", "память делится: работа / жизнь",
     "razdelit_pamyat.py"),
    ("UCHYOBA_NA_STOLE_V1", "учёба вернулась на стол (делим натрое)",
     "vernut_uchyobu_na_stol.py"),
    ("MAGIC_MESTA_V1", "номера местам, маски починены",
     "magic_pri_meste.py"),
    ("MAGIC_PRI_MESTE_V2", "номер остаётся за креслом при пересадке",
     "magic_ostayotsya_pri_meste.py"),
    ("NOMERA_VSEM_V1", "номера всем местам города",
     "nomera_vsem_mestam.py"),
    ("SUD_PATTERNA_V1", "рынок судит паттерн: маяк → метка или гаснет",
     "sud_rynka_nad_patternom.py"),
    ("KOMPAS_CHESTNYY_V1", "компас не подменяется рабочим этажом",
     "pochinit_kompas.py"),
    ("SVEZHEST_V1", "коды W1/MN1, вердикты только текущего бара",
     "pochinit_etazhi_i_verdikty.py"),
]


def _eto_koren(p: Path) -> bool:
    return (p / "БИРЖА.md").exists() and (p / "ЛЕТОПИСЬ_ГРОНДХЕЙМА.md").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


def est_marker(koren: Path, marker: str) -> bool:
    for f in koren.rglob("*.py"):
        s = str(f)
        if "_УБОРКА" in s or "_АРХИВ" in s:
            continue
        if f.parent == koren:      # патч-скрипты в корне не считаем
            continue
        try:
            if marker in f.read_text(encoding="utf-8", errors="ignore"):
                return True
        except Exception:
            continue
    return False


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    birzha = koren / "БИРЖА.md"
    letopis = koren / "ЛЕТОПИСЬ_ГРОНДХЕЙМА.md"

    print("\nСверяю с диском, о чём можно писать:")
    sdelano, zhdet = [], []
    for m, chto, patch in RABOTA:
        if est_marker(koren, m):
            sdelano.append((chto, patch))
            print(f"  ✓ {chto}")
        else:
            zhdet.append((chto, patch))
            print(f"  — {chto}  (ждёт: {patch})")

    stranica = ["\n---\n",
                f"## Что сделано 16–19.08 <!-- {MARKER} -->\n",
                "*Сверено с диском в день записи: ниже только то, чей маркер"
                " реально стоит в коде.*\n"]

    if sdelano:
        stranica.append("**Легло в город:**\n")
        for chto, _p in sdelano:
            stranica.append(f"- {chto}")
        stranica.append("")

    if zhdet:
        stranica.append("**Написано, но НЕ НАКАЧЕНО** — патчи лежат, "
                        "маркеров в коде нет:\n")
        for chto, p in zhdet:
            stranica.append(f"- {chto} — `{p}`")
        stranica.append("")
        stranica.append("Порядок накатки важен: руки → растяжка → крайние "
                        "точки → картина; приборы и разворотник на кадре "
                        "независимы; магики → номера → суд паттерна.\n")

    stranica.append("""**О чём этот кусок работы был.** Разбор упёрся в
одно: трейдер сверялся с инструкцией вместо того, чтобы смотреть.
Слово Шефа — «не код рулит агентом, а агент кодом; код даёт математику,
а трейдер собой принимает решение».

Отсюда всё остальное. Разворотного бара НЕ БЫЛО НА СТОЛЕ — её звали
на место ради него, а показать забыли. Кадр рисовал только последние
140 баров рабочего этажа: растянуть нужную волну было нечем, хотя весь
метод Шефа на этом и стоит («растягиваешь зигзаг на 100-140, потом
волну C внутри него»). Руки возвращали текст — картинку трейдер
попросить мог, а увидеть нет.

Замер отсева показал главное: **числами разворотник не отсеять**. Все
признаки дают ровные 11-13%, на 458 сделках. Отсев — это взгляд на
растянутой волне, а не формула. Поэтому кадр научили рисовать
разворотные бары, как в терминале Шефа, и дали растяжку.

**Круг опыта замкнут.** Судья при закрытии звался и раньше — но не
находил человека: магика не было ни у кого, а он ищет по нему. Номер
закреплён за КРЕСЛОМ: пересадил трейдера — номер остался за местом.
И вторая половина суда заработала: рынок судит паттерн, черновик
твердеет в знание или честно гаснет. Проверено — три минуса подряд
погасили маяк, хотя по числу повторов он должен был затвердеть.
Знание твердеет от судьи, а не от повторения.

**Академия перестала быть отдельной.** Учёба поднимается за столом
наравне с практикой (её у трейдеров пока ноль — ни одна сделка не
закрылась). Учебник с картинками книги доступен по запросу и трейдеру,
и ученику, и жителю дома — одному человеку везде, где он бывает.
Новая книга подключается папкой, без правок кода.

**Что осталось дырой.** Двухслойка Шефа (сперва глаз без чисел, потом
счёт под названный режим) не сделана — а именно она может дать первые
входы. Конец коррекции объявлять некому: все трое выбрали откат.
Ключей пробуждения нет — Совет будит всех на каждой свече.
""")

    print("\n1. БИРЖА.md")
    t = birzha.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        yakor = "\n## 1. Что такое Биржа"
        kusok = "\n".join(stranica) + "\n"
        novyy = (t.replace(yakor, kusok + yakor, 1) if yakor in t
                 else t + kusok)
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(birzha, birzha.with_suffix(
                f".md.bak_19_08_{datetime.now():%Y%m%d_%H%M%S}"))
            birzha.write_text(novyy, encoding="utf-8")
            print(f"  ✓ страница 16–19.08 ({len(sdelano)} сделано, "
                  f"{len(zhdet)} ждёт)")

    print("\n2. ЛЕТОПИСЬ_ГРОНДХЕЙМА.md")
    t = letopis.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    elif SUHO:
        print("  · запись готова (сухой прогон)")
    else:
        zapis = f"""
## 16–19.08 — трейдер начал смотреть <!-- {MARKER} -->

Неделя ушла на один вопрос: почему трейдер отвечает как бот. Ответ
оказался не в промпте. Разворотного бара, ради которого его звали, не
было у него на столе. Кадр показывал только последние 140 баров
рабочего этажа — растянуть нужную волну было нечем, хотя весь метод
Шефа на этом и держится. Руки возвращали текст: попросить картинку он
мог, увидеть — нет.

Замер отсева поставил точку в споре: числами разворотный бар отделить
нельзя, все признаки дают одинаковые проценты на четырёх сотнях
сделок. Значит отсев — это взгляд, и его надо дать. Кадр научили
рисовать разворотники, как в терминале Шефа; появилась растяжка любой
волны с подбором этажа под окно 100-140.

Круг опыта замкнулся. Судья при закрытии сделки работал и раньше, но
не находил человека: номер счёта не был привязан ни к кому. Теперь он
принадлежит КРЕСЛУ — пересадил трейдера, номер остался за местом.
Заработала и вторая половина суда: рынок судит паттерн, и черновик
либо твердеет в знание, либо гаснет. Три убыточных входа подряд
погасили маяк, который по числу повторов должен был стать меткой.

Академия перестала быть отдельной комнатой. Учёба поднимается за
рабочим столом наравне с практикой, а учебник с рисунками книги
доступен человеку везде: за столом, на уроке и дома.
"""
        shutil.copy2(letopis, letopis.with_suffix(
            f".md.bak_19_08_{datetime.now():%Y%m%d_%H%M%S}"))
        letopis.write_text(t.rstrip("\n") + "\n" + zapis, encoding="utf-8")
        print("  ✓ запись 16–19.08")

    if not SUHO:
        print("\nВ документе честно разделено: что легло и что ждёт")
        print("накатки. Врать о ненакаченном не стал — с этого и")
        print("начинался разбор БИРЖА.md 14.08.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
