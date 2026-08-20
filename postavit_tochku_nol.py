# -*- coding: utf-8 -*-
"""
postavit_tochku_nol.py · MARKER: TOCHKA_ROZHDAETSYA_V1

ЧТО БЫЛО СЛОМАНО
────────────────
Точка ноль в городе построена и жива: `hooks.proverit_tochku`
(TOCHKA_ZHIVA_V1) держит её между барами, гасит по структурному слому
(закрытие ушло за цену точки против её стороны) и по угасшему ритму,
подпитывает свежим разворотником той же стороны.

Но ЗАЖИГАЛА её одна Искра — `слоты/A01/мозг.py`, блок ISKRA_ALIVE_V1.
Слот уехал в архив 06.08, и с тех пор `alive = True` не ставит НИКТО:
поиск по всему репо даёт только архив и _УБОРКУ. Точка вечно мертва,
`proverit_tochku` всегда отвечает «точки нет», а зовёт её только
мёртвая функция в council.py, оставшаяся от Совета.

Из-за этого разворотный бар на столе живёт РОВНО ОДНУ СВЕЧУ. Появился —
трейдер его видит, но откат к новой волне ещё не сложился. Через десять
свечей откат сложился — а начала на столе уже нет, мерить не от чего.
Отсюда и вечное «нет первого отката к новой волне»: это не осторожность,
это устройство.

СЛОВО ШЕФА (20.08)
──────────────────
«Разворотник и есть точка. Посмотрел на график, увидел разворотник и
смотрю от него же волну 1.» И раньше: «начало видят все».

ИСТИННЫЙ БАР — ЭТО МЕСТО, А НЕ СВЕЧА
────────────────────────────────────
КАНОН_ВХОДА §2.1, модуль 6.2 — четыре пункта по порядку:
    1. пятиволновка завершена
    2. дивергенция на AO
    3. цена оторвалась от Аллигатора
    4. и только теперь — разворотный бар
Дословно оттуда: разворотник ВСЕГДА пункт 4, последний; первые три
очерчивают, что мы у конца волны, а бар — печать в этой зоне, не поиск
по всему графику.

Сама свеча везде одинакова (новый экстремум, закрытие в противоположной
половине). Истинной её делает место. Пункты 1-2 город меряет с 18.07:
`izmerit_volnovuyu_strukturu` — горб третьей → переход нуля → дивергенция
пятой, порядок и глубина. Ответ лежит полем `struktura_chitaetsya`.

Померено на EURUSD H4, 1200 баров: разворотных баров 159, структура
читается у 59. У остальных 95 пятая волна не слабее третьей — это не
конец волны, а середина движения. Рождаем на пятидесяти девяти.

Рамку 100-140 сюда НЕ тащим: она срезала бы 59 до 22, а окно — не
фильтр (КАНОН_ВХОДА §5к-5п), оно про масштаб просмотра.

Отсюда же и ключ Авантюриста: он просыпается ровно на рождении точки.
Кто выбрал откат — ждёт дальше, от неё же. Одна правда, не две.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `Биржа/hooks.py` — рука `_vesti_tochku(md)`, зовётся в самом конце
   `rynok_novyy_bar`, то есть на каждом баре, до того как за столом
   кто-то откроет рот:
     · разворотника нет           → ведёт существующую (proverit_tochku)
     · точки нет                  → РОЖДАЕТ
     · точка есть, сторона другая → рождает заново (развернулось)
     · точка есть, сторона та же  → ведёт (там подпитка и слом)
   Пока точка жива, копит два сырых числа: край цены после точки
   (та самая макушка волны 1) и сколько баров прошло.

2. `Биржа/stol.py` — кладёт точку трейдеру как КООРДИНАТУ, не как
   вывод: сторона, цена, сколько баров назад, жива или сломана, куда
   цена от неё ушла и где стоит сейчас. Ни одного суждения — что это
   значит, решает тот, кто смотрит.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не ставит ключей пробуждения. Совет будит как будил — сперва посмотрим
на живых отказах, чего трейдеру ещё не хватает, и только потом ключ.
Не судит, не фильтрует, не советует.

ТОЧКА ЛЕЖИТ ПО ПАРАМ, А НЕ ОДНА НА ЦЕХ
──────────────────────────────────────
Стол цеха — один файл на всех, кто в цехе. Вердикты в нём разложены по
людям (brut/avan/cons), а блок `iskra` был ОДИН, без имени инструмента
внутри. С одним трейдером незаметно; с двумя — Совет обходит их по
очереди, и точка второго затирает точку первого. Первый на следующем
баре читает ЧУЖУЮ цену и меряет от неё свой откат.

Ровно эта же болезнь уже была с позицией, у которой не было поля
«инструмент»: заявка по золоту проверялась барами евро и умирала
протухшей (14-15.08). Лечим тем же способом, до того как рванёт.

Точки переезжают на полку `точки` с ключом «SYMBOL TF». `proverit_tochku`
получает необязательный `para`: пусто — старое поведение (`iskra`),
задано — своя ячейка полки. Ничего из написанного раньше не ломается.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_tochku_nol.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "TOCHKA_ROZHDAETSYA_V1"
SUHO = "--suho" in sys.argv


# ─────────────────────────────────────────────────────────────
# корень ищем сами — путей руками не прописываем
# ─────────────────────────────────────────────────────────────
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


# ═════════════════════════════════════════════════════════════
# ЧАСТЬ 1 — hooks.py: рука рождения
# ═════════════════════════════════════════════════════════════

H_YAKOR_FN = "def rynok_novyy_bar(symbol: str, timeframe: str,"

H_RUKA = '''# ═══════════════════════════════════════════════════════════
# TOCHKA_ROZHDAETSYA_V1 — точку ноль зажигает КОД, а не Искра
# ═══════════════════════════════════════════════════════════
# proverit_tochku (TOCHKA_ZHIVA_V1) умела ВЕСТИ точку между барами,
# но зажигала её только Искра (слоты/A01/мозг.py, ISKRA_ALIVE_V1).
# Слот уехал в архив 06.08 — и alive=True не ставил больше никто.
# Точка вечно мертва, разворотник на столе живёт одну свечу, мерить
# от него откат нечем.
#
# Слово Шефа: «разворотник и есть точка; увидел разворотник и смотрю
# от него же волну 1». Но бар истинен НЕ сам по себе: КАНОН_ВХОДА
# §2.1 (модуль 6.2) — разворотник это пункт ЧЕТВЁРТЫЙ, печать в зоне
# конца волны, а не поиск по всему графику. Зону меряет линейка по AO
# (izmerit_volnovuyu_strukturu, 18.07): горб третьей → переход нуля →
# дивергенция пятой. Её ответ — поле struktura_chitaetsya.
# Рамку 100-140 не берём: окно — не фильтр (§5к-5п).
#
# Это ПОКАЗАНИЕ, а не решение: координата с датой, как фрактал или
# зона. Что она значит — судит трейдер.

def _para_tochki(symbol: str, timeframe: str) -> str:
    """Имя ячейки на полке. У точки должно быть имя пары — иначе
    сосед по цеху подменит её своей."""
    s = (symbol or "").strip().upper()
    tf = (timeframe or "").strip().upper()
    return f"{s} {tf}".strip()


def _blok_tochki(tstate: dict, para: str = "") -> dict:
    """Ячейка точки. Пары нет — старый общий блок `iskra` (так зовут
    те, кто был написан до полки). Пара есть — своя ячейка."""
    if not para:
        return tstate.setdefault("iskra", {})
    return tstate.setdefault("точки", {}).setdefault(para, {})


def _vesti_tochku(md: dict, symbol: str = "", timeframe: str = "") -> dict:
    """Родить точку ноль или вести уже рождённую. Код, без LLM.

    Зовётся на каждом баре из rynok_novyy_bar. Никогда не падает:
    в худшем случае отдаёт {"alive": False}.
    """
    para = _para_tochki(symbol, timeframe)
    try:
        wf = md.get("wave_form") or {}
        napr = wf.get("bdb_dir")
        cena = wf.get("bdb_price")
        price = md.get("price") or {}
        bar = md.get("bar_time")

        t = load_trading_state()
        isk = _blok_tochki(t, para)
        zhiva = bool(isk.get("alive"))
        storona = isk.get("trend_direction")

        # ── разворотник на этом баре: рождение или ведение ──
        # Рождаем ТОЛЬКО в зоне конца волны (модуль 6.2, пункты 1-2):
        # бар без читаемой структуры — середина движения, не конец.
        if napr in ("BULL", "BEAR") and cena is not None \
                and wf.get("struktura_chitaetsya"):
            if (not zhiva) or storona != napr:
                isk["alive"] = True
                isk["trend_direction"] = napr
                isk["zero_point_price"] = cena
                isk["rodilas_na_bare"] = bar
                isk["t1_status"] = "DETECTED"
                isk["neutral_bars_count"] = 0
                isk["barov_s_tochki"] = 0
                isk["kray_posle"] = cena
                isk["struktura_pozadi"] = wf.get("dlina")
                save_trading_state(t)
                print(f"[ТОЧКА] ✦ {para}: родилась {napr} @ {cena} · "
                      f"бар {bar} · структура позади: "
                      f"{wf.get('dlina')} бар.")
                return {"alive": True, "rodilas": True, "direction": napr}
            # та же сторона и точка жива — ведёт proverit_tochku:
            # там подпитка GREEN/SQUAT и структурный слом.

        res = proverit_tochku(md, para)

        # ── пока жива, копим два СЫРЫХ числа: край после точки
        # (та самая макушка волны 1) и сколько баров прошло ──
        if res.get("alive"):
            t = load_trading_state()
            isk = _blok_tochki(t, para)
            isk["barov_s_tochki"] = int(isk.get("barov_s_tochki", 0) or 0) + 1
            kray = isk.get("kray_posle")
            zp = isk.get("zero_point_price")
            napr2 = isk.get("trend_direction")
            hi, lo = price.get("high"), price.get("low")
            if napr2 == "BULL" and hi is not None:
                isk["kray_posle"] = hi if kray is None else max(kray, hi)
            elif napr2 == "BEAR" and lo is not None:
                isk["kray_posle"] = lo if kray is None else min(kray, lo)
            if isk.get("kray_posle") is None and zp is not None:
                isk["kray_posle"] = zp
            save_trading_state(t)
        elif res.get("changed"):
            print(f"[ТОЧКА] ✕ {para}: погасла — {res.get('reason')}")
        return res
    except Exception as e:
        print(f"[ТОЧКА] ⚠️  не рассужена ({e}) — бар цел, работаем дальше")
        return {"alive": False, "reason": f"сбой: {e}", "changed": False}


'''

H_YAKOR_PODPIS = "def proverit_tochku(md: dict) -> dict:"
H_NOV_PODPIS = ("def proverit_tochku(md: dict, para: str = \"\") -> dict:\n"
                "    # TOCHKA_ROZHDAETSYA_V1: para — чья это точка "
                "(«SYMBOL TF»).\n"
                "    # Пусто — старый общий блок, ничего из прежнего "
                "не ломается.")

H_YAKOR_BLOK = '''    tstate = load_trading_state()
    isk = tstate.setdefault("iskra", {})
'''
H_NOV_BLOK = '''    tstate = load_trading_state()
    isk = _blok_tochki(tstate, para)   # TOCHKA_ROZHDAETSYA_V1
'''

H_YAKOR_ZOV = '''    itog["позиций"] = len(stalo)

    if itog["активировано"] or itog["закрыто"]:'''

H_NOV_ZOV = '''    itog["позиций"] = len(stalo)

    # TOCHKA_ROZHDAETSYA_V1: точка ноль — после физики, до трейдеров.
    # Разворотник и есть точка; дальше её ведёт proverit_tochku.
    _vesti_tochku(md, symbol, timeframe)

    if itog["активировано"] or itog["закрыто"]:'''


# ═════════════════════════════════════════════════════════════
# ЧАСТЬ 2 — stol.py: точка ложится трейдеру координатой
# ═════════════════════════════════════════════════════════════

S_YAKOR_FN = 'def _status_alligatora(al: dict) -> str:'

S_RUKA = '''def _tochka_nol(md: dict, symbol: str = "", timeframe: str = "") -> dict:
    """TOCHKA_ROZHDAETSYA_V1: точка ноль на стол — КООРДИНАТА, не вывод.

    Разворотный бар выше по столу — это «есть ли он на ЭТОЙ свече».
    Точка — то же самое, но живущее между барами: вот начало, вот
    когда оно было, вот куда цена от него ушла. От неё трейдер и
    смотрит волну 1, как смотрит Шеф глазом.

    Ни «вход здесь», ни «сигнал». Что это значит — решает трейдер.
    """
    try:
        from hooks import load_trading_state, _blok_tochki, _para_tochki
        isk = _blok_tochki(load_trading_state() or {},
                           _para_tochki(symbol, timeframe))
    except Exception:
        return {}
    if not isk.get("alive"):
        return {"жива": False, "сторона": isk.get("trend_direction"),
                "цена": isk.get("zero_point_price")}
    return {
        "жива": True,
        "сторона": isk.get("trend_direction"),
        "цена": isk.get("zero_point_price"),
        "бар_рождения": isk.get("rodilas_na_bare"),
        "баров_назад": isk.get("barov_s_tochki"),
        "край_после_точки": isk.get("kray_posle"),
        # НЕ длина новой волны — её никто знать не может, точка только
        # родилась. Это отмерено НАЗАД: сколько баров заняла структура,
        # которая только что кончилась (4 перехода нуля AO, канон 18.07).
        "структура_позади_баров": isk.get("struktura_pozadi"),
        "цена_сейчас": ((md or {}).get("price") or {}).get("close"),
    }


'''

S_YAKOR_PRIB = '''        "зона": _zona(md),'''

S_NOV_PRIB = '''        # TOCHKA_ROZHDAETSYA_V1: начало, которое живёт дольше свечи
        "точка_ноль": _tochka_nol(md, symbol, timeframe),
        "зона": _zona(md),'''

S_YAKOR_SLOV = '''        f"зона (AO+AC): {p.get('зона') or '—'}   "'''

S_NOV_SLOV = '''        # TOCHKA_ROZHDAETSYA_V1: от начала трейдер и меряет волну 1
        (lambda _t: (
            f"ТОЧКА НОЛЬ: {_t.get('сторона') or '—'} @ {_t.get('цена')}"
            f"   {_t.get('баров_назад')} бар(ов) назад"
            f"   край после точки: {_t.get('край_после_точки')}"
            f"   структура позади: {_t.get('структура_позади_баров')} бар."
            f"   сейчас: {_t.get('цена_сейчас')}"
            if _t.get("жива") else "ТОЧКА НОЛЬ: нет"))(
                p.get("точка_ноль") or {}),
        f"зона (AO+AC): {p.get('зона') or '—'}   "'''


def _pravit(f: Path, pary: list, imya: str) -> bool:
    """Применяет список (якорь, замена) к файлу. Всё или ничего."""
    t = f.read_text(encoding="utf-8")
    if MARKER in t:
        print(f"· {imya}: маркер уже стоит — пропускаю")
        return True
    for yakor, _ in pary:
        n = t.count(yakor)
        if n != 1:
            print(f"✗ {imya}: якорь найден {n} раз — жду ровно один")
            print(f"  начало якоря: {yakor.splitlines()[0][:70]}")
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
    bak = f.with_suffix(f".py.bak_tochka_{datetime.now():%Y%m%d_%H%M%S}")
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

    ok = _pravit(koren / "Биржа" / "hooks.py",
                 [(H_YAKOR_FN, H_RUKA + H_YAKOR_FN),
                  (H_YAKOR_PODPIS, H_NOV_PODPIS),
                  (H_YAKOR_BLOK, H_NOV_BLOK),
                  (H_YAKOR_ZOV, H_NOV_ZOV)],
                 "hooks.py")
    if not ok:
        return 1
    ok = _pravit(koren / "Биржа" / "stol.py",
                 [(S_YAKOR_FN, S_RUKA + S_YAKOR_FN),
                  (S_YAKOR_PRIB, S_NOV_PRIB),
                  (S_YAKOR_SLOV, S_NOV_SLOV)],
                 "stol.py")
    if not ok:
        print("\n⚠️  hooks.py уже поправлен, stol.py — нет. Верни hooks.py")
        print("   из свежей копии .bak_tochka_* и позови меня.")
        return 1

    if SUHO:
        return 0

    print("\nЧто теперь будет видно:")
    print("  в консоли на баре разворотника — [ТОЧКА] ✦ родилась BULL @ …")
    print("  когда сломается —                 [ТОЧКА] ✕ погасла: …")
    print("  на столе трейдера строкой —       ТОЧКА НОЛЬ: BULL @ 1.0834")
    print("                                    12 бар(ов) назад,")
    print("                                    край после точки: 1.0961")
    print("\nПроверить без модели и без денег:")
    print("  py proverka_stola.py   (или py Биржа/stol.py EURUSD H1)")
    print("\nКлючей пробуждения патч НЕ ставит — Совет будит как будил.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
