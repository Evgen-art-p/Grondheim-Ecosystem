# -*- coding: utf-8 -*-
"""
postavit_poisk_s_daty.py · MARKER: POISK_S_DATY_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Сделай, пожалуйста, в тестере, чтобы начинался С даты, а не ДО даты.»

ЧТО БЫЛО НЕ ТАК
───────────────
Поле в кабинете называлось «с даты», а искатель от неё шёл НАЗАД — и
брал последние места ДО неё. Шеф ставил 28.04, ожидая начать оттуда, а
получал пять мест, где нужное оказывалось последним, и четыре взгляда
уходили на дорогу.

Имя обещало одно, код делал другое. Виноват я: поле назвал по-людски, а
подключил к тому, что было под рукой.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Даёт искателю второй способ ходить: `s_momenta` — идти ВПЕРЁД от даты,
беря места по порядку, как они случались.

    s_momenta пусто → всё как было: назад от конца истории
    s_momenta задан → вперёд от этой даты, в хронологическом порядке

Кабинет переключается на новый способ: поле «с даты» теперь и правда
значит «с даты».

Порядок мест меняется тоже: раньше первым шёл самый свежий, теперь —
самый ранний после указанной даты. Так и надо для проверки: сперва
точка, потом её волна, потом откат.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ поля даты в кабинете — патч это проверит.
Запуск: py postavit_poisk_s_daty.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "POISK_S_DATY_V1"
NUZHEN = "PROGON_S_DATY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "kandidaty.py").exists()
            and (p / "Биржа" / "ui_torg.py").exists())


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


# ── искатель: второй способ ходить ───────────────────────────

K_YAKOR = '''def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,'''
K_NOV = '''def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,
          s_momenta: str = "",   # POISK_S_DATY_V1: идти ВПЕРЁД от даты'''

K_YAKOR2 = '''    nayden = []
    mimo = 0                       # OKNO_ISKATELYA_V1: прошли мимо рамки'''

K_NOV2 = '''    # POISK_S_DATY_V1: слово Шефа — «чтобы начинался С даты, а не ДО».
    # Поле в кабинете называлось «с даты», а ход шёл назад: нужное
    # место оказывалось последним, а четыре взгляда уходили на дорогу.
    # Теперь второй способ ходить — вперёд, в том порядке, в каком всё
    # и случалось: точка, её волна, откат.
    _vperyod = bool(s_momenta)
    if _vperyod:
        nachalo_i = None
        for j, b in enumerate(vse):
            if b.get("date", "") >= s_momenta:
                nachalo_i = j
                break
        if nachalo_i is None:
            return []
        nachalo_i = max(OKNO_RASCHYOTA, nachalo_i)
        konec_i = min(len(vse) - 1, nachalo_i + predel_barov)
        hod = range(nachalo_i, konec_i + 1)
    else:
        hod = None

    nayden = []
    mimo = 0                       # OKNO_ISKATELYA_V1: прошли мимо рамки'''

K_YAKOR3 = '''    nachalo = max(OKNO_RASCHYOTA, konec - predel_barov)
    for i in range(konec, nachalo - 1, -1):
        if posledniy_i is not None and (posledniy_i - i) < otstup:
            continue'''

K_NOV3 = '''    nachalo = max(OKNO_RASCHYOTA, konec - predel_barov)
    # POISK_S_DATY_V1: вперёд или назад — дальше всё одинаково.
    for i in (hod if _vperyod else range(konec, nachalo - 1, -1)):
        if posledniy_i is not None and abs(posledniy_i - i) < otstup:
            continue'''


# ── кабинет: поле «с даты» теперь и значит «с даты» ──────────

U_YAKOR = '''                        _kd.iskat(s, t, skolko=skolko, govorit=print,
                                  do_momenta=_ot_daty)'''

U_NOV = '''                        _kd.iskat(s, t, skolko=skolko, govorit=print,
                                  s_momenta=_ot_daty)   # POISK_S_DATY_V1'''


def _pravit(f: Path, pary: list, imya: str) -> bool:
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ {imya}: якорь найден {n} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return False
    novyy = t
    for yakor, zamena in pary:
        novyy = novyy.replace(yakor, zamena, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ {imya}: после правки не разбирается — {e}")
        return False
    if SUHO:
        print(f"· {imya}: правка готова (сухой прогон)")
        return True
    bak = f.with_suffix(f".py.bak_sdaty2_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ {imya}: НЕ компилируется ({e}) — откатил из {bak.name}")
        return False
    print(f"✓ {imya}: правка легла (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    u = koren / "Биржа" / "ui_torg.py"
    if NUZHEN not in u.read_text(encoding="utf-8"):
        print("✗ Сперва накати postavit_progon_s_daty.py — без поля даты")
        print("  этому патчу нечего переключать.")
        return 1

    if not _pravit(koren / "Биржа" / "kandidaty.py",
                   [(K_YAKOR, K_NOV), (K_YAKOR2, K_NOV2),
                    (K_YAKOR3, K_NOV3)], "kandidaty.py"):
        return 1
    if not _pravit(u, [(U_YAKOR, U_NOV)], "ui_torg.py"):
        print("\n⚠️  искатель поправлен, кабинет нет — верни kandidaty.py")
        print("   из свежей .bak_sdaty2_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nТеперь поле «с даты» значит «с даты»:")
    print("   с даты: 2026.04.20    ловить: 3")
    print("   → первым будет самое РАННЕЕ место после 20 апреля,")
    print("     дальше по порядку, как всё и случалось.")
    print("\nПусто — по-прежнему назад от конца истории, как было.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
