# -*- coding: utf-8 -*-
# LENIVAYA_POLKA_V1 — список сразу, этажи по клику
"""
ЛЕНИВАЯ ПОЛКА · терминал больше не висит

ДОЛГ, ОТЛОЖЕННЫЙ ШЕФОМ 03.09 и названный им заново 10.09:
«кабинет из терминала тянет весь список — просто список; при клике
на инструмент подтягивает все ТФ конкретного инструмента, всё, что
есть».

КАК БЫЛО. Кнопка ТЕРМИНАЛ шла в терминал за КАЖДЫМ инструментом на
КАЖДОМ этаже сразу: четырнадцать инструментов на шесть этажей —
восемьдесят четыре похода. Опрос тянулся так долго, что страница
успевала уйти из-под него, и в коде из-за этого стоит отдельная
защита «окно могло уйти». Оттуда же и урезание: этажей девять было,
оставили шесть — не потому что остальные не нужны, а потому что
опрос не выдерживал.

КАК СТАЛО. Два шага вместо одного:

  · кнопка ТЕРМИНАЛ спрашивает ТОЛЬКО СПИСОК инструментов — один
    поход, мгновенно, и берутся все, без потолка;
  · раскрыл папку инструмента — вот тогда идём за его этажами, и
    сразу за ВСЕМИ, что знает насос, а не за шестью.

Побочная выгода: причина урезания исчезла. Платим только за тот
инструмент, который открыли, — значит этажей можно давать все.

ЧТО ПРАВИТСЯ, три шва в `Биржа/ui_torg.py`:
  1. список этажей — полный, из карты насоса, а не шесть избранных;
  2. кнопка ТЕРМИНАЛ — быстрый список вместо полного опроса;
  3. полка — папки для неразведанных инструментов и разведка при
     раскрытии.

Старый полный опрос НЕ удаляется — он остаётся под рукой как
`_sobrat_iz_terminala` на случай, если понадобится собрать всё разом.

БЕЗОПАСНОСТЬ: .bak_polka, идемпотентен, синтаксис до записи,
`--suho` не трогает диск. Не нашёлся шов — патч отказывается целиком
и не трогает файл: полка — живой экран, полумеры тут хуже отказа.

    python postavit_lenivuyu_polku.py --suho
    python postavit_lenivuyu_polku.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "LENIVAYA_POLKA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Биржа" / "ui_torg.py"

# ═══ ШОВ 1: функции разведки рядом с прежним опросом ═══
YAKOR_1 = '''    def _sobrat_iz_terminala() -> tuple:'''

VSTAVKA_1 = '''    # ── LENIVAYA_POLKA_V1 ──────────────────────────────────────
    # Список — сразу и целиком. Этажи — только у того инструмента,
    # который открыли. Раньше платили за всё сразу, оттого и висело.

    def _vse_etazhi_nasosa() -> tuple:
        """Все этажи, какие знает насос, от старших к младшим."""
        try:
            import sys as _s
            _b = str(_HERE)
            if _b not in _s.path:
                _s.path.insert(0, _b)
            import mt5_feed as _mf
            karta = dict(getattr(_mf, "_TF_MAP", {}) or {})
        except Exception:
            karta = {}
        if not karta:
            return _TERM_ETAZHI
        poryadok = ["MN1", "W1", "D1", "H12", "H8", "H4", "H2", "H1",
                    "M30", "M20", "M15", "M12", "M10", "M6", "M5",
                    "M4", "M3", "M2", "M1"]
        est = [tf for tf in poryadok if tf in karta]
        # то, чего нет в нашем порядке, но есть у насоса — в хвост
        est += [tf for tf in karta if tf not in est]
        return tuple(est)

    def _otkryt_terminal():
        """(mt5, беда). Связь открыта — закрывать зовущему."""
        try:
            import sys as _s
            _b = str(_HERE)
            if _b not in _s.path:
                _s.path.insert(0, _b)
            import mt5_feed as _mf
        except Exception as e:
            return None, None, f"насос не поднялся: {e}"
        mt5 = _mf._terminal()
        if mt5 is None:
            return None, None, ("MetaTrader5 для питона не установлен — "
                                "поставь его и перезапусти город")
        try:
            if not mt5.initialize():
                oshibka = ""
                try:
                    oshibka = f" ({mt5.last_error()})"
                except Exception:
                    pass
                return None, None, ("терминал не отвечает" + oshibka +
                                    ". Запусти MetaTrader и войди в счёт")
        except Exception as e:
            return None, None, f"связь с терминалом не открылась: {e}"
        return mt5, _mf, ""

    def _spisok_iz_terminala() -> tuple:
        """Только ИМЕНА инструментов. Один поход, без баров."""
        mt5, _mf, beda = _otkryt_terminal()
        if beda:
            return [], beda
        try:
            vse = mt5.symbols_get() or []
        except Exception as e:
            return [], f"терминал не отдал список: {e}"
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
        if not vse:
            return [], ("терминал на связи, но инструментов не отдал — "
                        "проверь, что счёт залогинен")
        vidnye = [getattr(s, "name", "") for s in vse
                  if getattr(s, "visible", False)]
        vidnye = [n for n in vidnye if n]
        if not vidnye:
            vidnye = [getattr(s, "name", "") for s in list(vse)[:10]]
            vidnye = [n for n in vidnye if n]
        return vidnye, ""

    def _etazhi_instrumenta(imya: str) -> tuple:
        """Все живые этажи ОДНОГО инструмента. Платим только за него."""
        mt5, _mf, beda = _otkryt_terminal()
        if beda:
            return [], beda
        aktivy = []
        try:
            try:
                info = mt5.symbol_info(imya)
                if info is not None and not getattr(info, "visible", True):
                    mt5.symbol_select(imya, True)
            except Exception:
                pass
            for tf in _vse_etazhi_nasosa():
                kod = (getattr(_mf, "_TF_MAP", {}) or {}).get(tf)
                if kod is None:
                    continue
                try:
                    bary = mt5.copy_rates_from_pos(imya, kod, 0, 2)
                except Exception:
                    bary = None
                if bary is None or len(bary) == 0:
                    continue          # этаж молчит — на полку не кладём
                try:
                    from datetime import datetime as _dt
                    posledniy = _dt.fromtimestamp(
                        int(bary[-1]["time"])).strftime("%Y.%m.%d %H:%M")
                except Exception:
                    posledniy = "?"
                aktivy.append({
                    "name": f"{imya} {tf}", "path": "", "symbol": imya,
                    "timeframe": tf, "bars": 0,
                    "date_from": "терминал", "date_to": posledniy,
                    "источник": "терминал",
                })
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass
        if not aktivy:
            return [], f"{imya}: терминал не отдал ни одного этажа"
        return aktivy, ""

    async def _razvedat_instrument(imya: str):
        """Раскрыли папку — сходить за этажами именно этого."""
        razvedano = state.setdefault("разведано", set())
        if imya in razvedano or state.get("развед_идёт") == imya:
            return
        state["развед_идёт"] = imya
        try:
            ui.notify(f"📡 {imya}: смотрю этажи…", type="info")
        except Exception:
            pass
        import asyncio as _a
        try:
            aktivy, beda = await _a.get_event_loop().run_in_executor(
                None, _etazhi_instrumenta, imya)
        finally:
            state["развед_идёт"] = ""
        if beda:
            print(f"[ПОЛКА] ⚠️  {beda}")
            try:
                ui.notify(f"⚠ {beda}", type="warning")
            except Exception:
                pass
            return
        est = state.get("loaded_assets") or []
        byli = {(a.get("symbol"), a.get("timeframe")) for a in est}
        novye = [a for a in aktivy
                 if (a["symbol"], a["timeframe"]) not in byli]
        state["loaded_assets"] = est + novye
        razvedano.add(imya)
        print(f"[ПОЛКА] 📂 {imya}: этажей {len(aktivy)}")
        try:
            update_files_display()
        except Exception as e:
            print(f"[ПОЛКА] полка не перерисовалась: {e}")

    def _raskryli_papku(imya: str, otkryta: bool):
        """Обработчик раскрытия. Задачей — рисовать нельзя блокируя."""
        if not otkryta:
            return
        if imya in (state.get("разведано") or set()):
            return
        try:
            import asyncio as _a
            _a.get_event_loop().create_task(_razvedat_instrument(imya))
        except Exception as e:
            print(f"[ПОЛКА] разведка не пошла: {e}")

'''

# ═══ ШОВ 2: кнопка ТЕРМИНАЛ берёт только список ═══
YAKOR_2 = '''        _tiho(ui.notify, "📡 спрашиваю терминал… это небыстро",
              type="info")
        import asyncio as _a
        aktivy, beda = await _a.get_event_loop().run_in_executor(
            None, _sobrat_iz_terminala)'''

VSTAVKA_2 = '''        # LENIVAYA_POLKA_V1: спрашиваем ТОЛЬКО СПИСОК — один поход.
        # Этажи подтянутся при раскрытии папки, каждый за себя.
        _tiho(ui.notify, "📡 спрашиваю терминал…", type="info")
        import asyncio as _a
        imena, beda = await _a.get_event_loop().run_in_executor(
            None, _spisok_iz_terminala)
        if not beda:
            state["term_spisok"] = imena
            state.setdefault("разведано", set())
            print(f"[ТЕРМИНАЛ] 📋 инструментов {len(imena)} — "
                  f"этажи по клику")
        aktivy = []'''

# ═══ ШОВ 3: полка показывает и неразведанные ═══
YAKOR_3 = '''            for sym in order:
                idxs = groups[sym]
                has_active = active in idxs
                with ui.expansion(
                    f"{sym}  ·  {len(idxs)} ТФ",
                    value=has_active,
                ).classes("w-full").style('''

VSTAVKA_3 = '''            # LENIVAYA_POLKA_V1: инструменты из терминала, у которых
            # этажи ещё не смотрели, тоже стоят на полке — пустой
            # папкой. Раскрыл — сходили. Так список виден сразу, а
            # платим только за открытое.
            for sym in (state.get("term_spisok") or []):
                if sym not in groups:
                    groups[sym] = []
                    order.append(sym)

            for sym in order:
                idxs = groups[sym]
                has_active = active in idxs
                _podpis = (f"{sym}  ·  {len(idxs)} ТФ" if idxs
                           else f"{sym}  ·  раскрой — посмотрю этажи")
                with ui.expansion(
                    _podpis,
                    value=has_active,
                    on_value_change=lambda e, s=sym: _raskryli_papku(
                        s, bool(getattr(e, "value", False))),
                ).classes("w-full").style('''


def main():
    print()
    print("ЛЕНИВАЯ ПОЛКА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return

    shvy = [("функции разведки", YAKOR_1, VSTAVKA_1 + YAKOR_1),
            ("кнопка ТЕРМИНАЛ", YAKOR_2, VSTAVKA_2),
            ("полка", YAKOR_3, VSTAVKA_3)]

    beda = [imya for imya, yakor, _ in shvy if txt.count(yakor) != 1]
    if beda:
        print("ОТКАЗЫВАЮСЬ, файл не тронут. Не нашлись швы:")
        for b in beda:
            print("  ·", b)
        print("Полка — живой экран, половина правки хуже отказа.")
        return

    novy = txt
    for imya, yakor, zamena in shvy:
        novy = novy.replace(yakor, zamena, 1)
        print(f"  {imya}: вставлено")

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_polka"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_torg.py.bak_polka")
    print("ТЕРМИНАЛ теперь мгновенный, этажи — по раскрытию папки.")
    print()


if __name__ == "__main__":
    main()
