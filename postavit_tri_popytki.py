# -*- coding: utf-8 -*-
"""
postavit_tri_popytki.py · MARKER: TRI_POPYTKI_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Стоп ставит за разворотник. Если его выбило, то не попала — ждёт
следующий разворотник. Так три раза. После третьего думает: то ли она
делает?»

ЗАЧЕМ ЭТО НУЖНО
───────────────
Мы собрали три события — точка, волна, откат. Это ГДЕ смотреть. А
ЧЕМ входить, у трейдера на столе не было: я вчера трижды подставлял
стоп от себя (за точкой, за фракталом, за максимумом отката) и все три
раза промахнулся — на живом месте фрактал вообще оказался не с той
стороны.

Правило Шефа снимает вопрос: стоп за тем же баром, по которому входишь.
Разворотник и есть мера риска, и она короткая — за это его и любят.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. **Стоп назван на столе.** Рядом с разворотным баром встаёт прямая
   строка: вход за ним, стоп за ним же, столько-то пунктов риска. Не
   расчёт «сколько взять» и не совет входить — просто цена, которую
   трейдер и так должен назвать, чтобы Исполнитель принял заявку.

2. **Попытки считаются.** Выбило стоп — попытка засчитана, ждём
   следующий разворотник. Счётчик живёт при точке: новая точка — новый
   счёт с нуля.

3. **На третьей — вопрос себе.** На столе появляется:

       ПОПЫТКИ: 3-я на этой структуре — то ли ты делаешь?

   Это не запрет и не блокировка. Город не мешает войти в четвёртый
   раз: он говорит вслух то, что трейдер и сам должен был заметить.
   Решение остаётся его.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ края волны — патч это проверит.
Запуск: py postavit_tri_popytki.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TRI_POPYTKI_V1"
NUZHEN = "KRAY_VOLNY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "stol.py").exists())


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


# ── 1. hooks: выбило стоп → попытка засчитана ────────────────

H_YAKOR = '''        closed.append(record)'''

H_NOV = '''        closed.append(record)

        # TRI_POPYTKI_V1: выбило стоп — попытка засчитана. Слово Шефа:
        # «не попала, ждёт следующий разворотник, так три раза; после
        # третьего думает, то ли она делает». Счётчик живёт при точке:
        # новая точка — новый счёт с нуля. Город не запрещает четвёртый
        # вход, он только говорит вслух то, что трейдер и сам заметил.
        if reason == "STOP_LOSS":
            try:
                _t = load_trading_state()
                _isk = _blok_tochki(
                    _t, _para_tochki(pos.get("symbol") or symbol,
                                     md.get("timeframe") or ""))
                _isk["попыток"] = int(_isk.get("попыток") or 0) + 1
                save_trading_state(_t)
                print(f"[ПОПЫТКА] ✗ стоп выбил · попытка "
                      f"{_isk['попыток']} на этой структуре")
            except Exception as _ep:
                print(f"[ПОПЫТКА] не сосчиталась ({_ep}) — работаем дальше")'''

# новая точка — новый счёт
H_YAKOR2 = '''                isk["konec_volny_2"] = None   # KONEC_VOLNY_2_V1'''
H_NOV2 = '''                isk["konec_volny_2"] = None   # KONEC_VOLNY_2_V1
                isk["попыток"] = 0            # TRI_POPYTKI_V1'''


# ── 2. стол: чем входить и какая попытка ─────────────────────

S_YAKOR = '''        # KONEC_VOLNY_2_V1: откат — третья координата, рядом с точкой и'''

S_NOV = '''        # TRI_POPYTKI_V1: чем входить. Разворотник — он же и мера риска:
        # вход за ним, стоп за ним же. Не совет входить, а цена, которую
        # трейдер и так обязан назвать, чтобы заявку приняли.
        "попыток": int(isk.get("попыток") or 0),
        # KONEC_VOLNY_2_V1: откат — третья координата, рядом с точкой и'''

S_YAKOR2 = '''        # KONEC_VOLNY_2_V1: и откат к ней — если он уже кончился.'''

S_NOV2 = '''        # TRI_POPYTKI_V1: вход и стоп — по разворотному бару, и какая
        # это попытка на текущей структуре.
        (lambda _rb, _t: (
            (f"ВХОД: заявка за разворотником @ {_rb.get('цена')}, "
             f"стоп за ним же"
             if _rb.get("есть") else "ВХОД: разворотного бара сейчас нет")
            + ((f"   ·   ПОПЫТКА {_t.get('попыток')}-я на этой структуре"
                + ("  — то ли ты делаешь?"
                   if int(_t.get("попыток") or 0) >= 3 else ""))
               if int(_t.get("попыток") or 0) else "")
        ))(p.get("разворотный_бар") or {}, p.get("точка_ноль") or {}),
        # KONEC_VOLNY_2_V1: и откат к ней — если он уже кончился.'''

S_YAKOR3 = '''        "цена_сейчас": ((md or {}).get("price") or {}).get("close"),'''
S_NOV3 = '''        "попыток": int(isk.get("попыток") or 0),   # TRI_POPYTKI_V1
        "цена_сейчас": ((md or {}).get("price") or {}).get("close"),'''


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
    bak = f.with_suffix(f".py.bak_popytki_{datetime.now():%Y%m%d_%H%M%S}")
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
    h = koren / "Биржа" / "hooks.py"
    if NUZHEN not in h.read_text(encoding="utf-8"):
        print("✗ Сперва накати pochinit_kray_volny.py")
        return 1

    if not _pravit(h, [(H_YAKOR, H_NOV), (H_YAKOR2, H_NOV2)], "hooks.py"):
        return 1
    if not _pravit(koren / "Биржа" / "stol.py",
                   [(S_YAKOR3, S_NOV3), (S_YAKOR, S_NOV),
                    (S_YAKOR2, S_NOV2)], "stol.py"):
        print("\n⚠️  hooks поправлен, стол нет — верни его из свежей")
        print("   .bak_popytki_* и покажи мне вывод.")
        return 1

    if SUHO:
        return 0
    print("\nТеперь на столе, ниже структуры:")
    print("  — ВХОД: заявка за разворотником @ 1.17416, стоп за ним же")
    print("  — ВХОД: ... · ПОПЫТКА 3-я на этой структуре — то ли ты делаешь?")
    print("\nГород не запрещает четвёртый вход. Он только называет счёт.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
