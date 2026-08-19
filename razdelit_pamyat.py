# -*- coding: utf-8 -*-
"""
razdelit_pamyat.py · MARKER: PAMYAT_RABOTA_ZHIZN_V1

ЧТО НАШЛОСЬ У НИНЫ
──────────────────
Она за столом просит: «похожий случай, когда Аллигатор открыт, но AO
падает» — и мост честно поднимает 172 следа. Полез смотреть, что это
за следы:

    resonance: 175 записей   archive: 149   sensory: 1
    «привет» · «чаю, из твоих рук — хоть яду»
    «нина, если бы у тебя была коронная фраза как у трейдера?»
    «нина, на рынке как успехи?» — *отрывается от холста…*

Это ВАШИ РАЗГОВОРЫ и учёба, а не торговая практика. Сделок у неё
ноль. Она ищет опыт — а получает свою же болтовню про холст, и потом
на этом «опыте» отвечает за столом.

ПОЧЕМУ ОТДЕЛИТЬ БЫЛО НЕЛЬЗЯ
───────────────────────────
В движке есть Закон Слоёв: контекст входа решает, куда осядет запись.

    факт/работа/дом → sensory · общение → resonance · учёба → archive

Но САМ КОНТЕКСТ в запись НЕ ПИШЕТСЯ — остаётся только имя слоя. А в
sensory валятся сразу три контекста: и работа, и дом, и сухой факт.
Отделить работу от жизни задним числом нечем.

ЧТО ДЕЛАЕТ ПАТЧ (движок общий — правка на ВСЕХ жителей)
───────────────────────────────────────────────────────
1. Контекст пишется В САМУ ЗАПИСЬ. С этого дня видно, откуда след:
   работа, общение, учёба, дом, факт.

2. `vspomnit(..., o_chyom=...)` — можно спросить память по делу:

       o_chyom="работа"  — только рабочие следы
       o_chyom="жизнь"   — общение и дом
       o_chyom=""        — всё, как раньше (дом, разговор с Шефом)

3. Мост (`nositel.vspomnit_slotom`) с Биржи спрашивает РАБОЧЕЕ. Значит
   за столом трейдер получит либо свою практику, либо честное «следа
   нет, решай без этого» — и это правда его положения, а не болтовня
   под видом опыта.

ПРО СТАРЫЕ ЗАПИСИ — ЧЕСТНО
──────────────────────────
У них контекста нет, восстановить его неоткуда. Разбираем по слою,
как велит Закон Слоёв:

    archive → учёба      resonance → общение      sensory → неизвестно

При поиске РАБОЧЕГО старые записи без контекста НЕ поднимаются. Это
осознанный выбор: лучше честное «следа нет», чем чужой разговор,
выданный за практику. Из памяти при этом ничего не пропадает — дома
житель по-прежнему помнит всё.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py razdelit_pamyat.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PAMYAT_RABOTA_ZHIZN_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "жители" / "dvizhok.py").exists()
            and (p / "Биржа" / "nositel.py").exists())


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


# ── 1. закон слоёв дополняем разделением работа/жизнь ──
ST_ZAKON = '''# контекст входа → в какой слой осядет (Закон Слоёв)'''
NOV_ZAKON = '''# PAMYAT_RABOTA_ZHIZN_V1: какой контекст считается РАБОТОЙ, а какой
# ЖИЗНЬЮ. Нужно затем, что за столом житель просит опыт — и должен
# получить практику, а не разговоры о холсте. У Нины 18.08 на запрос
# «Аллигатор открыт, но AO падает» поднялось 172 следа, и все до
# одного были беседами и учёбой: сделок у неё ноль.
RABOCHIE_KONTEKSTY = ("работа", "факт")
ZHIZNENNYE_KONTEKSTY = ("общение", "дом")

# Старые записи контекста не имеют — разбираем по слою, как велит
# Закон Слоёв ниже. sensory остаётся неизвестным: туда падали сразу
# три контекста, и восстанавливать их гаданием мы не будем.
SLOY_KONTEKST = {"archive": "учёба", "resonance": "общение"}


def kontekst_zapisi(z: dict) -> str:
    """Откуда след. Нет пометки — берём по слою; sensory неизвестен."""
    k = str(z.get("контекст") or "").strip()
    if k:
        return k
    return SLOY_KONTEKST.get(str(z.get("слой") or ""), "")


# контекст входа → в какой слой осядет (Закон Слоёв)'''

# ── 2. контекст пишется в запись ──
ST_ZAPIS = '''        return {
            "тронуло":     round(trogaet, 3),
            "заряд":       round(self.charge, 3),
            "открыто":     sloi,
            "осело_в":     osel_v,'''
NOV_ZAPIS = '''        return {
            "тронуло":     round(trogaet, 3),
            "заряд":       round(self.charge, 3),
            "открыто":     sloi,
            "осело_в":     osel_v,
            # PAMYAT_RABOTA_ZHIZN_V1: контекст доходит до записи.
            # Раньше он решал слой и терялся — и отделить работу от
            # жизни задним числом было нечем.
            "контекст":    kontekst,'''

# ── 3. поиск умеет спрашивать по делу ──
ST_VSPOMNIT = '''    def vspomnit(self, zapros: str, limit: int = 6) -> str:'''
NOV_VSPOMNIT = '''    def vspomnit(self, zapros: str, limit: int = 6,
                 o_chyom: str = "") -> str:'''

ST_OTBOR = '''        naydeno = []
        for z in zapisi:
            fakt = str(z.get("факт", "")).lower()'''
NOV_OTBOR = '''        # PAMYAT_RABOTA_ZHIZN_V1: о чём спрашиваем — о работе или о
        # жизни. За столом нужна практика, а не разговоры; дома —
        # наоборот. Пусто — ищем везде, как раньше.
        nuzhno = (o_chyom or "").strip().lower()
        naydeno = []
        for z in zapisi:
            if nuzhno:
                k = kontekst_zapisi(z)
                if nuzhno.startswith("работ"):
                    if k not in RABOCHIE_KONTEKSTY:
                        continue
                elif nuzhno.startswith("жизн"):
                    if k not in ZHIZNENNYE_KONTEKSTY:
                        continue
            fakt = str(z.get("факт", "")).lower()'''

# ── 4. мост с Биржи спрашивает рабочее ──
ST_MOST = '''def vspomnit_slotom(ceh: str, slot: str, zapros: str, limit: int = 6) -> str:'''
NOV_MOST = '''def vspomnit_slotom(ceh: str, slot: str, zapros: str, limit: int = 6,
                    o_chyom: str = "работа") -> str:'''

ST_MOST2 = '''        return d.vspomnit(zapros, limit=limit) or ""'''
NOV_MOST2 = '''        # PAMYAT_RABOTA_ZHIZN_V1: мост зовут С БИРЖИ — значит спрашиваем
        # ПРАКТИКУ. Нет практики — честное «следа нет»; это правда его
        # положения, а не повод подсунуть разговор о холсте.
        try:
            return d.vspomnit(zapros, limit=limit, o_chyom=o_chyom) or ""
        except TypeError:
            # движок старый, без разделения — не ломаемся
            return d.vspomnit(zapros, limit=limit) or ""'''


def pravit(put: Path, pary: list, imya: str) -> bool:
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"  · {put.name}: маркер уже стоит")
        return True
    beda = [st[:38].replace("\n", " ") for st, _ in pary if t.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден → «{b}…»")
        return False
    novyy = t
    for st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    shutil.copy2(put, put.with_suffix(
        put.suffix + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}"))
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    dvizhok = koren / "жители" / "dvizhok.py"
    nositel = koren / "Биржа" / "nositel.py"

    print("\n1. Движок жителей — контекст в запись и поиск по делу")
    print("   (движок один на всех — правка касается каждого жителя)")
    if not pravit(dvizhok, [(ST_ZAKON, NOV_ZAKON), (ST_ZAPIS, NOV_ZAPIS),
                            (ST_VSPOMNIT, NOV_VSPOMNIT),
                            (ST_OTBOR, NOV_OTBOR)], "pamyat"):
        return 1

    print("\n2. Мост с Биржи спрашивает практику, а не разговоры")
    if not pravit(nositel, [(ST_MOST, NOV_MOST), (ST_MOST2, NOV_MOST2)],
                  "pamyat"):
        return 1

    if not SUHO:
        import py_compile
        for f in (dvizhok, nositel):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nЧто изменится за столом:")
        print("  было — 172 следа, и все про холст и знакомство;")
        print("  станет — «следа нет, решай без этого», пока практики нет.")
        print("\nДома житель по-прежнему помнит ВСЁ: из памяти ничего не")
        print("пропало, просто на работе поднимается рабочее.")
        print("\nПрактика появится, когда начнут закрываться сделки —")
        print("судья по исходу написан, но при закрытии его пока не зовут.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
