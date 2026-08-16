# -*- coding: utf-8 -*-
"""
postavit_ruku_rynka.py · MARKER: RUKA_RYNKA_V1

ЧТО ЧИНИТ
─────────
На Бирже никто не судил новый бар.

  * `hooks._aktivirovat_ordera` — превращает заявку (PENDING/WATCHING)
    в открытую позицию, когда рынок её взял;
  * `hooks._settle_positions`   — закрывает позицию по стопу, по
    колоколу выхода или по воле трейдера, пишет PnL, дневник, Атлас
    и суд по исходу.

Обе руки целы и написаны давно — но их НЕ ЗОВЁТ НИКТО. Раньше их
дёргал старый путь Совета, который ушёл вместе с Искрой 06.08.
Тестер зовёт свою копию, но тестер не заводится.

Итог на сегодня: заявка ставится и висит вечно, позиция не
закрывается никогда, журнал сделок не пополняется, судья молчит,
опыт трейдера не растёт. Всё, что стоит НА закрытии сделки, стоит.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Кладёт в `Биржа/hooks.py` одну честную руку `rynok_novyy_bar()`:
   берёт бары через ОБЩИЙ кран (`feed_source`, тот же, что у кадра и
   у трейдера), считает рынок, активирует созревшие заявки, потом
   закрывает то, что рынок закрыл. Ничего не решает — только физика.

2. В `Биржа/council.py` ставит её ПЕРВЫМ шагом `wake_council()` —
   до Архивариуса и трейдеров. Одна дверь: и кнопка РЫНОК, и вахта
   идут через неё, второй правды не заводим.

Порядок внутри бара: сперва активация, потом закрытие. Это
консервативно — заявка, взятая на этом же баре, может на нём же
выбить стоп, и мы считаем худший случай, а не удобный.

БЕЗОПАСНОСТЬ
────────────
Идемпотентен (маркер), пишет .bak рядом, проверяет ast.parse и
py_compile ДО записи. Корень репо ищет сам. Ничего не удаляет.

Запуск: двойной щелчок или  py postavit_ruku_rynka.py
        py postavit_ruku_rynka.py --suho   (показать, не трогая)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RUKA_RYNKA_V1"
SUHO = "--suho" in sys.argv


# ═══════════════════════════════════════════════════════════
# КОРЕНЬ РЕПО — ищем сами, руками пути не пишем
# ═══════════════════════════════════════════════════════════
def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "hooks.py").exists()
            and (p / "Биржа" / "council.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    # соседние папки — репо часто лежит внутри «проекты»
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        otvet = input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] ")
        if otvet.strip().lower() in ("", "y", "д", "да"):
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
    print("✗ Это не корень репо (нужны main.py и Биржа/hooks.py)")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# ТЕКСТ РУКИ — в hooks.py
# ═══════════════════════════════════════════════════════════
RUKA = '''

# ═══════════════════════════════════════════════════════════
# РЫНОК СУДИТ ПЕРВЫМ (RUKA_RYNKA_V1)
# ═══════════════════════════════════════════════════════════
# Обе руки ниже были написаны давно и работали — но их перестал
# звать кто бы то ни было, когда 06.08 ушёл старый путь Совета
# вместе с Искрой. Заявка висела вечно, позиция не закрывалась
# никогда, журнал сделок не рос, судья молчал.
#
# Это ФИЗИКА, а не суждение: рынок делает своё дело до того, как
# кто-то за столом откроет рот. Поэтому рука зовётся первым шагом
# wake_council — раньше Архивариуса и раньше трейдеров.
def rynok_novyy_bar(symbol: str, timeframe: str,
                    window=None, point=None) -> dict:
    """Рассудить новый бар: что взято, что закрыто.

    Бары берутся ОБЩИМ краном (feed_source) — тем же, из которого
    рисуется кадр и смотрит трейдер. Второго источника не заводим:
    режим РЕАЛ/ТЕСТЕР переключается в одном месте и действует на всех.

    Порядок внутри бара — сперва активация заявок, потом закрытие.
    Консервативно: заявка, взятая на этом баре, может на нём же
    выбить стоп, и мы считаем именно так, а не как удобнее.

    Возвращает {"активировано": N, "закрыто": M, "позиций": K} —
    сводку для ленты кабинета. Ничего не решает и никого не судит.
    """
    itog = {"активировано": 0, "закрыто": 0, "позиций": 0, "причина": ""}

    bars, _p = window, point
    if not bars:
        try:
            from feed_source import bars as _src_bars
            bars, _p = _src_bars(symbol, timeframe, 300)
        except Exception as e:
            itog["причина"] = f"кран молчит: {e}"
            return itog
    if point is not None:
        _p = point
    if not bars:
        itog["причина"] = "нет баров"
        return itog

    md = build_market_data(bars[-300:], symbol=symbol,
                           timeframe=timeframe, point=_p)
    if not md:
        itog["причина"] = "williams_core вернул пусто"
        return itog

    state = {"chain_data": {"market_data": md}}
    cd = state["chain_data"]
    # Подушка безопасности Вильямса — экстремум второго бара назад.
    if len(bars) >= 3:
        cd["_bar_back2_low"] = bars[-3].get("low")
        cd["_bar_back2_high"] = bars[-3].get("high")

    # 1. заявки: рынок взял — становится позицией
    bylo = len(load_trading_state().get("positions", []) or [])
    _otkrytyh_do = sum(1 for p in (load_trading_state().get("positions") or [])
                       if p.get("status") not in ("WATCHING", "PENDING"))
    try:
        _aktivirovat_ordera(state)
    except Exception as e:
        print(f"[РЫНОК] ⚠️  заявки не рассудились: {e}")

    # 2. закрытие: стоп / колокол / воля трейдера
    t = load_trading_state()
    cd["open_positions"] = t.get("positions", []) or []
    _otkrytyh_posle_akt = sum(1 for p in cd["open_positions"]
                              if p.get("status") not in ("WATCHING", "PENDING"))
    # ВАЖНО: _settle_positions переписывает cd["open_positions"] тем же
    # словарём (chain — это и есть cd). Считать по нему ПОСЛЕ вызова
    # нельзя — он уже новый. Запоминаем число ДО.
    _bylo_v_stole = len(cd["open_positions"])
    try:
        _settle_positions(state)
    except Exception as e:
        print(f"[РЫНОК] ⚠️  позиции не закрылись: {e}")

    stalo = load_trading_state().get("positions", []) or []
    itog["активировано"] = max(0, _otkrytyh_posle_akt - _otkrytyh_do)
    itog["закрыто"] = max(0, _bylo_v_stole - len(stalo))
    itog["позиций"] = len(stalo)

    if itog["активировано"] or itog["закрыто"]:
        print(f"[РЫНОК] 📊 бар {md.get('bar_time', '')} · "
              f"взято {itog['активировано']}, закрыто {itog['закрыто']}, "
              f"в работе {itog['позиций']} (было {bylo})")
    return itog


# RUKA_RYNKA_V1 - marker
'''

# ═══════════════════════════════════════════════════════════
# ВСТАВКА В council.py
# ═══════════════════════════════════════════════════════════
YAKOR_COUNCIL = '''    summary = {"woke": [], "verdicts": {}, "orders": None,
               "idle": False, "results": {}}
'''

VSTAVKA_COUNCIL = '''    # ── РЫНОК СУДИТ ПЕРВЫМ (RUKA_RYNKA_V1) ──────────────────
    # Физика раньше мнений: что рынок взял и что закрыл, решается до
    # того, как за столом кто-то откроет рот. Без этого шага заявка
    # висела вечно, а позиция не закрывалась никогда — обе руки в
    # hooks.py были целы, но их не звал никто с 06.08.
    try:
        import hooks as _hr
        _rynok = _hr.rynok_novyy_bar(symbol, timeframe,
                                     window=window, point=point)
        if _rynok.get("активировано") or _rynok.get("закрыто"):
            _emit({"type": "рынок", **_rynok})
    except Exception as _er:
        print(f"[РЫНОК] ⚠️  бар не рассужен: {_er}")

''' + YAKOR_COUNCIL


def pravit(put: Path, proverka, pravka) -> bool:
    """Общая механика: маркер → бэкап → правка → ast → запись."""
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {put.name}: маркер уже стоит — пропускаю")
        return True
    ok, prichina = proverka(tekst)
    if not ok:
        print(f"  ✗ {put.name}: {prichina}")
        return False
    novyy = pravka(tekst)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон, не пишу)")
        return True
    bak = put.with_suffix(put.suffix + f".bak_ruka_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}: правка легла (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    if SUHO:
        print("Сухой прогон — ничего не записываю.\n")

    hooks = koren / "Биржа" / "hooks.py"
    council = koren / "Биржа" / "council.py"

    print("\n1. Рука рынка в hooks.py")
    ok1 = pravit(
        hooks,
        lambda t: (("def _settle_positions" in t
                    and "def _aktivirovat_ordera" in t
                    and "build_market_data" in t),
                   "не нашёл в файле _settle_positions/_aktivirovat_ordera"),
        lambda t: t.rstrip("\n") + "\n" + RUKA,
    )

    print("\n2. Вызов в council.py — первым шагом Совета")
    ok2 = pravit(
        council,
        lambda t: (t.count(YAKOR_COUNCIL) == 1,
                   f"якорь найден {t.count(YAKOR_COUNCIL)} раз — жду ровно один"),
        lambda t: t.replace(YAKOR_COUNCIL, VSTAVKA_COUNCIL, 1),
    )

    if not (ok1 and ok2):
        print("\n✗ Не всё легло — смотри выше. Файлы целы.")
        return 1

    if not SUHO:
        import py_compile
        for f in (hooks, council):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1

    print("\nГотово. Теперь на каждом баре (кнопка РЫНОК и вахта):")
    print("  заявка, которую рынок взял → становится позицией;")
    print("  позиция, которую рынок закрыл → закрывается, пишет PnL,")
    print("  дневник, Атлас и суд по исходу.")
    print("\nПроверить живьём: открой кабинет, нажми РЫНОК — в консоли")
    print("должна появиться строка [РЫНОК] 📊, как только будет что судить.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
