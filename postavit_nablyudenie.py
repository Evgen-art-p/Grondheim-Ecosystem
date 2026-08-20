# -*- coding: utf-8 -*-
"""
postavit_nablyudenie.py · MARKER: NABLYUDENIE_V1

СЛОВО ШЕФА (20.08)
──────────────────
«Она видит картину ясно, это важно. Да, это не её сигнал — после этого
она должна свой ждать. Вот здесь начинается работа трейдера: увидел,
похоже, проверил, наблюдай, если видишь — вот-вот твой сигнал.»

И на вопрос, кто снимает наблюдение: «если точка сломалась, хоть
структурно, хоть нет — Нина в любом случае увидит».

ЧТО БЫЛО
────────
Тридцать мест на двух инструментах, тридцать отказов, причина одна и та
же её словами: «есть разворотный бар и точка ноль, но мне нужен откат к
новой волне, а не просто разворот».

Ключ будил её ровно в секунду рождения точки — то есть в чужой момент.
Ответить «да» там она не могла по устройству своего выбора. А дальше
город замолкал, и всё, что она увидела, пропадало.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
У трейдера появляется ТРЕТИЙ ответ. Было два — вход или отказ. Стало
три: вход / НАБЛЮДАЮ / мимо.

    НАБЛЮДАЮ: <за чем слежу и чего жду>   — беру на карандаш
    УХОЖУ                                  — снимаю наблюдение

Ритуал строкой, как ВЫБОР у трейдера и РУКА у архивариуса: работает на
любой модели, ничего не ломает, если модель его не написала.

Ключ пробуждения получает вторую причину открыть дверь:

    точка родилась            → зовём (как было)
    трейдер сказал НАБЛЮДАЮ   → зовём, пока он наблюдает      ← новое
    своя позиция или заявка   → зовём (как было)

Снимает наблюдение ТОЛЬКО сам трейдер — словом УХОЖУ или входом. Код
не гасит его ни при сломе точки, ни по числу баров: по слову Шефа, она
увидит слом сама и скажет.

Наблюдение лежит по паре и по слоту, рядом с точкой, и переживает
перезапуск. В прогоне по истории оно чистится вместе с точкой — там
город прыгает через месяцы, и вчерашнее наблюдение к новому месту
отношения не имеет.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не подсказывает, когда наблюдать и когда входить. Не судит, дождалась
она своего сигнала или нет. Это её работа, и теперь у неё есть, чем её
делать.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ ключа пробуждения — патч это проверит.
Запуск: py postavit_nablyudenie.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "NABLYUDENIE_V1"
NUZHEN = "KLYUCH_PROBUZHDENIYA_V1"
SUHO = "--suho" in sys.argv

SLOTY = {"A06": "brut", "A07": "avan", "A08": "cons"}


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "council.py").exists()
            and (p / "Биржа" / "hooks.py").exists()
            and (p / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
                 / "слоты").is_dir())


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


# ══ hooks.py: где лежит наблюдение ═══════════════════════════

H_YAKOR = "def zabyt_tochku(symbol: str = \"\", timeframe: str = \"\") -> bool:"

H_RUKA = '''# ═══════════════════════════════════════════════════════════
# NABLYUDENIE_V1 — «беру на карандаш», второй ключ пробуждения
# ═══════════════════════════════════════════════════════════
# Слово Шефа: «увидел, похоже, проверил — наблюдай, если видишь, что
# вот-вот твой сигнал». Трейдер, которому родившаяся точка не его
# момент, больше не теряет увиденное: он говорит НАБЛЮДАЮ, и город
# будит его дальше, пока он сам не скажет УХОЖУ или не войдёт.
#
# Снимает наблюдение ТОЛЬКО трейдер. Код не гасит его ни при сломе
# точки, ни по числу баров: слом он увидит сам и скажет.

def nablyudenie(symbol: str = "", timeframe: str = "",
                slot: str = "") -> dict:
    """Что трейдер взял на карандаш по этой паре. Пусто — не наблюдает."""
    try:
        t = load_trading_state()
        para = _para_tochki(symbol, timeframe)
        return ((t.get("наблюдения") or {}).get(para) or {}).get(slot) or {}
    except Exception:
        return {}


def vzyat_na_karandash(symbol: str, timeframe: str, slot: str,
                       za_chem: str = "", bar: str = "") -> None:
    """Трейдер сказал НАБЛЮДАЮ. Запоминаем — за чем и с какого бара."""
    try:
        t = load_trading_state()
        para = _para_tochki(symbol, timeframe)
        polka = t.setdefault("наблюдения", {}).setdefault(para, {})
        bylo = polka.get(slot) or {}
        polka[slot] = {
            "за_чем": (za_chem or "").strip()[:400],
            "с_бара": bylo.get("с_бара") or bar,
            "последний_бар": bar,
        }
        save_trading_state(t)
        if not bylo:
            print(f"[НАБЛЮДЕНИЕ] 👁 {slot} взял на карандаш {para}")
    except Exception as e:
        print(f"[НАБЛЮДЕНИЕ] записать не вышло ({e}) — работаем дальше")


def snyat_nablyudenie(symbol: str = "", timeframe: str = "",
                      slot: str = "", pochemu: str = "") -> bool:
    """Трейдер сказал УХОЖУ (или вошёл). Наблюдение снимается."""
    try:
        t = load_trading_state()
        para = _para_tochki(symbol, timeframe)
        polka = (t.get("наблюдения") or {}).get(para) or {}
        if slot not in polka:
            return False
        polka.pop(slot, None)
        save_trading_state(t)
        print(f"[НАБЛЮДЕНИЕ] ✕ {slot} снял наблюдение по {para}"
              + (f": {pochemu}" if pochemu else ""))
        return True
    except Exception as e:
        print(f"[НАБЛЮДЕНИЕ] снять не вышло ({e}) — работаем дальше")
        return False


'''

# прогон чистит наблюдение вместе с точкой
H_YAKOR2 = '''        bylo = bool((polka.get(para) or {}).get("alive"))
        if para in polka:
            polka.pop(para, None)
            t["точки"] = polka
            save_trading_state(t)
        return bylo'''

H_NOV2 = '''        bylo = bool((polka.get(para) or {}).get("alive"))
        if para in polka:
            polka.pop(para, None)
            t["точки"] = polka
        # NABLYUDENIE_V1: прогон прыгнул — вчерашнее наблюдение к новому
        # месту отношения не имеет. В живом городе эта рука не зовётся.
        (t.get("наблюдения") or {}).pop(para, None)
        save_trading_state(t)
        return bylo'''

# ══ council.py: ключ + ловля слова ═══════════════════════════

C_YAKOR = '''        return {"будим": False, "почему": "точки нет и позиции нет"}'''

C_NOV = '''        # NABLYUDENIE_V1: второй ключ — трейдер сам взял на карандаш.
        # Снимает только он: словом УХОЖУ или входом.
        if slot:
            n = hooks.nablyudenie(symbol, timeframe, slot)
            if n:
                za = (n.get("за_чем") or "").strip()
                return {"будим": True,
                        "почему": "наблюдает" + (f": {za[:80]}" if za else "")}

        return {"будим": False, "почему": "точки нет, наблюдения нет, "
                                          "позиции нет"}'''

C_YAKOR2 = '''def _klyuch_probuzhdeniya(symbol: str, timeframe: str) -> dict:'''
C_NOV2 = '''def _klyuch_probuzhdeniya(symbol: str, timeframe: str,
                          slot: str = "") -> dict:'''

C_YAKOR3 = '''        _k = _klyuch_probuzhdeniya(_p["symbol"], _p["timeframe"])'''
C_NOV3 = '''        _k = _klyuch_probuzhdeniya(_p["symbol"], _p["timeframe"], slot)'''

C_YAKOR4 = '''        sig = r.get("signal", {}) or {}
        summary["verdicts"][aid] = sig.get(f"{pre}_verdict")'''

C_NOV4 = '''        sig = r.get("signal", {}) or {}
        # NABLYUDENIE_V1: ловим слово трейдера — НАБЛЮДАЮ / УХОЖУ.
        _uslyshat_nablyudenie(slot, _p["symbol"], _p["timeframe"],
                              r.get("narrative", ""),
                              sig.get(f"{pre}_verdict"))
        summary["verdicts"][aid] = sig.get(f"{pre}_verdict")'''

C_YAKOR5 = '''_ZHIVYE_STATUSY = ("WATCHING", "PENDING", "OPEN")'''

C_NOV5 = '''_ZHIVYE_STATUSY = ("WATCHING", "PENDING", "OPEN")


def _uslyshat_nablyudenie(slot: str, symbol: str, timeframe: str,
                          skazal: str, verdikt: str) -> None:
    """NABLYUDENIE_V1: услышать слово трейдера про наблюдение.

    НАБЛЮДАЮ: <за чем>  — берём на карандаш, будим дальше
    УХОЖУ               — снимаем
    вход (APPROVED)     — снимаем: дальше ведёт позиция

    Слова нет — ничего не меняем. Молчание не отменяет прежнего
    решения и не заводит нового.
    """
    try:
        import hooks
        tekst = (skazal or "")
        verh = tekst.upper()
        if (verdikt or "").upper() == "APPROVED":
            hooks.snyat_nablyudenie(symbol, timeframe, slot, "вошёл")
            return
        if "УХОЖУ" in verh:
            hooks.snyat_nablyudenie(symbol, timeframe, slot, "сказал УХОЖУ")
            return
        if "НАБЛЮДАЮ" in verh:
            za = ""
            for stroka in tekst.splitlines():
                if "НАБЛЮДАЮ" in stroka.upper():
                    za = stroka.split(":", 1)[1] if ":" in stroka else stroka
                    break
            bar = ""
            try:
                bar = str((hooks.load_trading_state().get("рынок") or {})
                          .get("бар") or "")
            except Exception:
                pass
            hooks.vzyat_na_karandash(symbol, timeframe, slot, za, bar)
    except Exception as e:
        print(f"[НАБЛЮДЕНИЕ] слово не разобрано ({e}) — работаем дальше")'''


def _mozg_pravki(pre: str) -> list:
    return [(
        '        "diary_entry: input, action, result(=null). Ничего вне JSON."',
        '        # NABLYUDENIE_V1: третий ответ — «беру на карандаш».\n'
        '        # Слово Шефа: увидел, похоже, проверил — наблюдай, если\n'
        '        # видишь, что вот-вот твой сигнал. Пока наблюдаешь, тебя\n'
        '        # будят на каждом баре; снять наблюдение можешь только ты.\n'
        '        "Если это НЕ твой вход, но картина может дозреть до него — '
        'напиши в narrative отдельной строкой: НАБЛЮДАЮ: за чем следишь и '
        'чего ждёшь. Тебя будут звать на каждом баре, пока наблюдаешь.\\n"\n'
        '        "Передумал, картина рассыпалась, ждать больше нечего — '
        'напиши строкой: УХОЖУ. Наблюдение снимаешь только ты сам.\\n"\n'
        '        "Вошёл — наблюдение снимется само.\\n"\n'
        '        "diary_entry: input, action, result(=null). Ничего вне JSON."'
    )]


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
    bak = f.with_suffix(f".py.bak_nablyud_{datetime.now():%Y%m%d_%H%M%S}")
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

    c = koren / "Биржа" / "council.py"
    if NUZHEN not in c.read_text(encoding="utf-8"):
        print("✗ Сперва накати ключ пробуждения — наблюдению не на что")
        print("  опереться: дверь всё равно будет открыта всегда.")
        return 1

    if not _pravit(koren / "Биржа" / "hooks.py",
                   [(H_YAKOR, H_RUKA + H_YAKOR), (H_YAKOR2, H_NOV2)],
                   "hooks.py"):
        return 1
    if not _pravit(c, [(C_YAKOR5, C_NOV5), (C_YAKOR2, C_NOV2),
                       (C_YAKOR, C_NOV), (C_YAKOR3, C_NOV3),
                       (C_YAKOR4, C_NOV4)], "council.py"):
        print("\n⚠️  hooks.py поправлен, council.py нет — верни hooks.py из")
        print("   свежей .bak_nablyud_* и покажи мне вывод.")
        return 1

    sloty = koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
    for slot, pre in SLOTY.items():
        mozg = sloty / slot / "мозг.py"
        if not mozg.exists():
            print(f"· {slot}: мозга нет — пропускаю")
            continue
        if not _pravit(mozg, _mozg_pravki(pre), f"{slot}/мозг.py"):
            print(f"\n⚠️  {slot} не поправлен. Остальное цело, копии рядом.")
            return 1

    if SUHO:
        return 0
    print("\nЧто появится в логе:")
    print("  [НАБЛЮДЕНИЕ] 👁 A06 взял на карандаш EURUSD H4")
    print("  [КЛЮЧ] 🔑 A06: наблюдает: жду откат к первой волне")
    print("  [НАБЛЮДЕНИЕ] ✕ A06 снял наблюдение: сказал УХОЖУ")
    print("\nВ прогоне по истории наблюдение чистится вместе с точкой —")
    print("там город прыгает через месяцы. В живом городе оно живёт,")
    print("пока трейдер сам его не снимет.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
