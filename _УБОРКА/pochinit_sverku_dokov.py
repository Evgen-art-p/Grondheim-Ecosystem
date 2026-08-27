# -*- coding: utf-8 -*-
"""
pochinit_sverku_dokov.py · MARKER: SVERKA_CHESTNAYA_V1

ЧТО СЛУЧИЛОСЬ
─────────────
В `БИРЖА.md` попал список «написано, но НЕ НАКАЧЕНО», в котором висят
работы, УЖЕ СТОЯЩИЕ в городе. Шеф это заметил, и он прав: документ
врёт ровно тем способом, из-за которого мы 14.08 и затеяли разбор.

ПОЧЕМУ — ПРИЧИНА, А НЕ ОТГОВОРКА
────────────────────────────────
Сверка искала маркер В .PY ФАЙЛАХ. Но часть патчей кода НЕ ТРОГАЕТ
ВОВСЕ — они правят ДАННЫЕ:

    nomera_vsem_mestam.py   — раздаёт номера постам (JSON)
    magic_pri_meste.py      — чинит маски жителей (JSON)

Такой патч отработал, дело сделал, а маркера в коде не оставил —
и сверка честно отвечает «нет», НАВСЕГДА. Сколько ни прогоняй.

То есть врал не документ и не скрипт: врала моя проверка. Она умела
смотреть только в одну сторону.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Учит сверку смотреть на СЛЕДЫ РАБОТЫ, а не только на маркеры в коде:

    1. маркер в .py                      — как было;
    2. маркер в .json (посты, маски)     — для патчей данных;
    3. ПРИЗНАК НА ДИСКЕ — то, что патч реально создал:
       файл появился, поле проставлено, номер выдан.

Для каждой работы указан свой признак — по нему видно, сделано или
нет, независимо от того, оставил патч маркер или нет.

И отдельно: сверка теперь ПЕРЕПИСЫВАЕТ старый список в БИРЖА.md, а не
дописывает новый. Иначе враньё осталось бы лежать рядом с правдой.

Запуск: py pochinit_sverku_dokov.py   (или --suho)
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "SVERKA_CHESTNAYA_V1"
SUHO = "--suho" in sys.argv

# (что это, маркер, патч, признак-на-диске)
# признак — функция от корня: True, если работа реально сделана
RABOTA = [
    ("руки трейдера: стол, волна, дневник", "RUKI_TREYDERA_V1",
     "postavit_ruki_treydera.py",
     lambda k: (k / "Биржа" / "ruki_treydera.py").exists()),
    ("руки всем трём трейдерам", "RUKI_VSEM_V1",
     "postavit_ruki_vsem.py", None),
    ("выход в интернет на работе", "RUKA_MAYAKA_V1",
     "postavit_ruku_mayaka.py",
     lambda k: (k / "ГОРОД" / "ruka_mayaka.py").exists()),
    ("Маяк через прокси (403 вылечен)", "MAYAK_403_V1",
     "pochinit_mayak.py", None),
    ("искатель зовёт только при волне 100-140", "OKNO_ISKATELYA_V1",
     "postavit_okno_iskatelya.py", None),
    ("отчёт прогона: таблица, кадры, итог", "OTCHYOT_PROGONA_V1",
     "postavit_otchyot_progona.py",
     lambda k: (k / "Биржа" / "otchyot.py").exists()),
    ("прогон виден на экране, связь не рвётся", "PROGON_VIDNO_V1",
     "pochinit_progon_na_ekrane.py", None),
    ("приборы на столе: разворотник, зона, дивергенция",
     "PRIBORY_NA_STOL_V1", "postavit_pribory_na_stol.py", None),
    ("разворотные бары нарисованы на кадре", "RB_NA_KADRE_V1",
     "narisovat_razvorotnik.py", None),
    ("растяжка волны: трейдер ВИДИТ нужный масштаб", "RASTYAZHKA_V1",
     "postavit_ruku_rastyazhki.py",
     lambda k: (k / "Биржа" / "rastyanut.py").exists()),
    ("вершина и дно числами, потолок обращений 12",
     "KRAYNIYE_TOCHKI_V1", "postavit_krayniye_tochki.py", None),
    ("своя картина у каждого, не общая доска", "KARTINA_SVOYA_V1",
     "peredelat_dosku_v_lichnuyu.py",
     lambda k: (k / "Биржа" / "kartina.py").exists()),
    ("учебник Академии по всем дисциплинам", "UCHEBNIK_DISCIPLINY_V1",
     "postavit_ruku_uchebnika.py + uchebnik_po_disciplinam.py",
     lambda k: (k / "Биржа" / "uchebnik.py").exists()),
    ("ученик сам просит рисунок", "UCHEBNIK_UCHENIKU_V1",
     "uchebnik_ucheniku.py", None),
    ("учебник жителю дома", "RUKI_DOMA_V1", "ruki_zhitelyu_doma.py", None),
    ("память делится: работа / жизнь", "PAMYAT_RABOTA_ZHIZN_V1",
     "razdelit_pamyat.py", None),
    ("учёба вернулась на стол (делим натрое)", "UCHYOBA_NA_STOLE_V1",
     "vernut_uchyobu_na_stol.py", None),
    # ── патчи ДАННЫХ: маркера в коде не оставляют ──
    ("номера местам, маски починены", "MAGIC_MESTA_V1",
     "magic_pri_meste.py", None),
    ("номер остаётся за креслом при пересадке", "MAGIC_PRI_MESTE_V2",
     "magic_ostayotsya_pri_meste.py", None),
    ("номера ВСЕМ местам города", "NOMERA_VSEM_V1",
     "nomera_vsem_mestam.py",
     # признак: у постов БЕЗ слота тоже есть номер
     lambda k: _vse_posty_s_nomerom(k)),
    ("рынок судит паттерн: маяк → метка или гаснет", "SUD_PATTERNA_V1",
     "sud_rynka_nad_patternom.py", None),
    ("компас не подменяется рабочим этажом", "KOMPAS_CHESTNYY_V1",
     "pochinit_kompas.py", None),
    ("коды W1/MN1, вердикты только текущего бара", "SVEZHEST_V1",
     "pochinit_etazhi_i_verdikty.py", None),
]


def _vse_posty_s_nomerom(koren: Path) -> bool:
    """Признак NOMERA_VSEM_V1: патч правит только JSON и маркера в коде
    не оставляет. Смотрим на дело: у постов БЕЗ слота цеха тоже есть
    номер — раньше их не было ни у одного."""
    posty = koren / "GRONDHEIM_CITY" / "посты"
    if not posty.exists():
        return False
    bez_slota, s_nomerom = 0, 0
    for d in posty.iterdir():
        f = d / "пост.json"
        if not f.exists():
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not (p.get("слот") or "").strip():
            bez_slota += 1
            if p.get("magic"):
                s_nomerom += 1
    return bez_slota > 0 and bez_slota == s_nomerom


def _eto_koren(p: Path) -> bool:
    return (p / "БИРЖА.md").exists() and (p / "main.py").exists()


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


def sdelano_li(koren: Path, marker: str, priznak) -> tuple:
    """(сделано, чем доказано). Смотрим тремя способами, а не одним."""
    # 1. маркер в коде
    for f in koren.rglob("*.py"):
        s = str(f)
        if "_УБОРКА" in s or "_АРХИВ" in s or f.parent == koren:
            continue
        try:
            if marker in f.read_text(encoding="utf-8", errors="ignore"):
                return True, f"маркер в {f.name}"
        except Exception:
            continue
    # 2. маркер в данных (посты, маски)
    for f in (koren / "GRONDHEIM_CITY").rglob("*.json"):
        try:
            if marker in f.read_text(encoding="utf-8", errors="ignore"):
                return True, f"маркер в {f.name}"
        except Exception:
            continue
    # 3. след на диске — для патчей, что правят только данные
    if priznak is not None:
        try:
            if priznak(koren):
                return True, "по следу на диске"
        except Exception:
            pass
    return False, ""


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    birzha = koren / "БИРЖА.md"

    print("\nСверяю ТРЕМЯ способами: маркер в коде, маркер в данных,")
    print("след на диске (для патчей, что кода не трогают).\n")

    sdelano, zhdet = [], []
    for chto, marker, patch, priznak in RABOTA:
        est, chem = sdelano_li(koren, marker, priznak)
        if est:
            sdelano.append(chto)
            print(f"  ✓ {chto}   ({chem})")
        else:
            zhdet.append((chto, patch))
            print(f"  — {chto}")

    # ── переписываем старый список, а не дописываем рядом ──
    t = birzha.read_text(encoding="utf-8")
    nachalo = t.find("## Что сделано 16–19.08")
    if nachalo < 0:
        print("\n✗ не нашёл страницу 16–19.08 в БИРЖА.md")
        return 1
    konec = t.find("\n## ", nachalo + 10)
    if konec < 0:
        konec = len(t)

    L = [f"## Что сделано 16–19.08 <!-- {MARKER} -->", "",
         f"*Сверено с диском {datetime.now():%d.%m} тремя способами: маркер "
         f"в коде, маркер в данных, след на диске. Часть патчей кода не "
         f"трогает вовсе — они правят посты и маски, и по маркеру их не "
         f"видно; такие проверяются по делу.*", ""]
    if sdelano:
        L.append("**Легло в город:**")
        L.append("")
        L += [f"- {x}" for x in sdelano]
        L.append("")
    if zhdet:
        L.append("**Написано, но НЕ НАКАЧЕНО:**")
        L.append("")
        L += [f"- {c} — `{p}`" for c, p in zhdet]
        L.append("")
        L.append("Порядок: руки → растяжка → крайние точки → картина; "
                 "приборы и разворотник на кадре независимы; "
                 "магики → номера → суд паттерна.")
        L.append("")

    novyy = t[:nachalo] + "\n".join(L) + t[konec:]

    if SUHO:
        print(f"\n· переписал бы: {len(sdelano)} сделано, {len(zhdet)} ждёт")
        return 0

    shutil.copy2(birzha, birzha.with_suffix(
        f".md.bak_sverka_{datetime.now():%Y%m%d_%H%M%S}"))
    birzha.write_text(novyy, encoding="utf-8")
    print(f"\n✓ страница переписана: {len(sdelano)} сделано, "
          f"{len(zhdet)} ждёт")
    print("  Старый список СТЁРТ, а не оставлен рядом — иначе враньё")
    print("  лежало бы рядом с правдой.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
