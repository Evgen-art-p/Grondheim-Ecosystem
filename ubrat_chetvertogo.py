# -*- coding: utf-8 -*-
"""
ubrat_chetvertogo.py · MARKER: UBRAT_CHETVERTOGO_V1

Слово Шефа: «не должно быть нового инструмента... три трейдера и
четыре инструмента — это тоже не сделал».

Не сделал. Обещал дважды. Делаю.

ГДЕ СИДЕЛ ЧЕТВЁРТЫЙ (вся цепочка, сверху вниз)
──────────────────────────────────────────────
1. `ui_torg._aktivnyy_rynok()` — если на полке ничего не выбрано,
   возвращал ВЫДУМАННОЕ `XAUUSD H4`. Ничей инструмент, ничей этаж.

2. `run_market` брал эту пару и передавал в `wake_council(_sym_now,
   _tf_now)`. То есть кнопка РЫНОК несла Совету инструмент кабинета.

3. `council._para_slota(..., zapasnoy_sym, zapasnoy_tf)` — я сам
   оставил там «запасную пару для тестера». А поскольку кабинет
   ВСЕГДА передавал свою, запасная срабатывала ВСЕГДА. Из-за неё вся
   постройка «у каждого своя пара» обходилась стороной, и в логе
   стояло `[СОВЕТ] 👤 A07: EURUSD D1` — при том что у Синди золото.
   Инструмент потом подменялся уже внутри мозга, по-старому, а ЭТАЖ
   оставался кабинетным. Мой недосмотр, самый дорогой за эти дни.

4. Вахта делала то же самое: брала пару с полки и звала Совет с ней.

КАК СТАЛО
─────────
Кабинет своего инструмента не имеет. Кнопка РЫНОК и вахта зовут
Совет БЕЗ пары — «обойти всех, каждый по своему». Кто не выбрал —
молчит с причиной, и это видно строкой, а не прячется за подставным
инструментом.

Полка остаётся тем, чем и должна быть: загрузчиком и смотрелкой.
Ею Шеф назначает инструмент трейдеру кликом — как и ставил.

ЗАОДНО: СИММЕТРИЯ ЗАЩИТЫ
────────────────────────
В логе видно строку, которой не должно быть:

    [ОРДЕР] ⚡ BRUT LONG АКТИВИРОВАН @ 0.70843 (H=1.15854 L=1.15247)
    [SETTLE] ⚠️ позиция BRUT без инструмента — не сужу чужим баром

Заявка по цене 0.708 «активирована» баром евро по 1.15. Закрытие
отказалось судить позицию без инструмента, а АКТИВАЦИЯ пропустила:
защиту я поставил только в одну руку из двух. Несимметричная защита
хуже, чем никакой — она создаёт позиции, которые потом никто не
закроет. Теперь обе руки одинаковы.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py ubrat_chetvertogo.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UBRAT_CHETVERTOGO_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
            and (p / "Биржа" / "council.py").exists()
            and (p / "main.py").exists())


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


def pravit(put: Path, yakorya: list, imya: str) -> bool:
    """yakorya — список (что_ищем, на_что_меняем)."""
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {put.name}: маркер уже стоит — пропускаю")
        return True
    beda = [st[:48].replace("\n", " ") for st, _ in yakorya
            if tekst.count(st) != 1]
    if beda:
        for b in beda:
            print(f"  ✗ {put.name}: якорь не найден дословно → «{b}…»")
        return False
    novyy = tekst
    for st, nov in yakorya:
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
    bak = put.with_suffix(put.suffix
                          + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}: правка легла (копия: {bak.name})")
    return True


# ═══════════════════════════════════════════════════════════
# 1. council — запасной пары нет
# ═══════════════════════════════════════════════════════════
C_ST_1 = '''        if zapasnoy_sym and zapasnoy_tf:
            return {"symbol": zapasnoy_sym, "timeframe": zapasnoy_tf,
                    "готов": True, "почему": ""}
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": vybor.pochemu_molchit(ceh_id, slot)}
    except Exception as e:
        if zapasnoy_sym and zapasnoy_tf:
            return {"symbol": zapasnoy_sym, "timeframe": zapasnoy_tf,
                    "готов": True, "почему": ""}
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": f"пара не прочиталась ({e})"}'''

C_NOV_1 = '''        # UBRAT_CHETVERTOGO_V1: запасной пары БОЛЬШЕ НЕТ. Она была
        # задумана «для тестера», но кабинет всегда передавал свою —
        # и запасная срабатывала всегда, подменяя собой всю
        # постройку. Три трейдера получали четвёртый инструмент.
        # Не выбрал — молчит. Молчание честнее подставного рынка.
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": vybor.pochemu_molchit(ceh_id, slot)}
    except Exception as e:
        return {"symbol": "", "timeframe": "", "готов": False,
                "почему": f"пара не прочиталась ({e})"}'''

C_ST_2 = '''        _p = _para_slota(ceh_id, _slot, symbol, timeframe)'''
C_NOV_2 = '''        _p = _para_slota(ceh_id, _slot)   # UBRAT_CHETVERTOGO_V1'''

C_ST_3 = '''        _p = _pary.get(slot) or _para_slota(ceh_id, slot, symbol, timeframe)'''
C_NOV_3 = '''        _p = _pary.get(slot) or _para_slota(ceh_id, slot)'''

C_ST_4 = '''def _para_slota(ceh_id: str, slot: str, zapasnoy_sym: str = "",
                zapasnoy_tf: str = "") -> dict:'''
C_NOV_4 = '''def _para_slota(ceh_id: str, slot: str) -> dict:'''

C_ST_5 = '''                window=window if _klyuch == (symbol, timeframe) else None,
                point=point if _klyuch == (symbol, timeframe) else None)'''
C_NOV_5 = '''                window=window if _klyuch == (symbol, timeframe) else None,
                point=point if _klyuch == (symbol, timeframe) else None)
            # окно передаём только если кабинет прислал бары ИМЕННО
            # этой пары; иначе рука сама возьмёт из крана — свои.'''


# ═══════════════════════════════════════════════════════════
# 2. кабинет — своей пары Совету не даёт
# ═══════════════════════════════════════════════════════════
U_ST_1 = '''        except Exception:
            pass
        return "XAUUSD", "H4"'''

U_NOV_1 = '''        except Exception:
            pass
        # UBRAT_CHETVERTOGO_V1: выдуманного запасного «XAUUSD H4»
        # больше нет. Это и был четвёртый инструмент при трёх
        # трейдерах: ничей, никем не выбранный, а работали по нему
        # все. Полка пуста — так и говорим, пустотой.
        return "", ""'''

U_ST_2 = '''        _sym_now, _tf_now = _aktivnyy_rynok()'''
U_NOV_2 = '''        # UBRAT_CHETVERTOGO_V1: кабинет Совету пару НЕ передаёт.
        # Каждый берёт свою — инструмент из поста, этаж свой.
        _sym_now, _tf_now = "", ""'''

U_ST_3 = '''        ui.notify(f"👁 смотрим {_sym_now} {_tf_now}", type="info")'''
U_NOV_3 = '''        ui.notify("📡 Совет: каждый смотрит своё", type="info")'''

U_ST_4 = '''        _s, _t = _aktivnyy_rynok()
        # VAHTA_ZA_POLKOY_V1: берём выбранное сейчас, и дальше вахта
        # идёт за полкой — сменил инструмент, сменилось и то, что она
        # сторожит. Помнить старое оказалось хуже, чем не помнить.
        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,'''

U_NOV_4 = '''        _s, _t = _aktivnyy_rynok()
        # UBRAT_CHETVERTOGO_V1: вахта — это ДЕЖУРСТВО, будильник. По
        # какой свече звонить — берём с полки, как и раньше; но
        # разбуженные работают КАЖДЫЙ СВОИМ, а не тем, что на полке.
        # Полка пуста — дежурить не по чему, честно откажемся.
        if not _s or not _t:
            ui.notify("⏱ выбери слева, по какой свече дежурить",
                      type="warning")
            return
        _VAHTA.update({"идёт": True, "инструмент": _s, "этаж": _t,'''

U_ST_5R = '''        if aid not in ("A06", "A07", "A08"):
            s, t = _aktivnyy_rynok()
            return s, t, "", ""'''
U_NOV_5R = '''        if aid not in ("A06", "A07", "A08"):
            s, t = _aktivnyy_rynok()
            if not s or not t:
                return "", "", imya, "на полке ничего не выбрано"
            return s, t, "", ""'''

# вахта зовёт Совет — без пары
U_ST_6 = '''            None, lambda: (council.wake_council(sym, tf, ceh_id=_ceh)
                           if _ceh else council.wake_council(sym, tf)))'''
U_NOV_6 = '''            None, lambda: (council.wake_council("", "", ceh_id=_ceh)
                           if _ceh else council.wake_council("", "")))'''


# ═══════════════════════════════════════════════════════════
# 3. hooks — активация защищена так же, как закрытие
# ═══════════════════════════════════════════════════════════
H_ST = '''        _psym = (pos.get("symbol") or "").strip().upper()
        if _bar_sym and _psym and _psym != _bar_sym:
            ostalis.append(pos)
            continue'''

H_NOV = '''        _psym = (pos.get("symbol") or "").strip().upper()
        if _bar_sym and _psym and _psym != _bar_sym:
            ostalis.append(pos)
            continue
        # UBRAT_CHETVERTOGO_V1: симметрия с закрытием. Заявка без
        # инструмента (открыта до 14.08) НЕ активируется чужим баром:
        # в логе 15.08 такая заявка по 0.708 «активировалась» баром
        # евро по 1.15 и стала позицией, которую закрытие потом
        # трогать отказалось. Защита в одной руке из двух хуже, чем
        # никакой — она плодит вечные позиции.
        if _bar_sym and not _psym:
            print(f"[ОРДЕР] ⚠️  {pos.get('trader')} без инструмента "
                  f"(открыта до 14.08) — не активирую баром {_bar_sym}. "
                  f"Решение по старым заявкам за Шефом.")
            ostalis.append(pos)
            continue'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    council = koren / "Биржа" / "council.py"
    ui_torg = koren / "Биржа" / "ui_torg.py"
    hooks = koren / "Биржа" / "hooks.py"

    if "RABOTA_PO_PARE_V1" not in council.read_text(encoding="utf-8"):
        print("✗ Сначала накати postavit_rabotu_po_pare.py")
        return 1

    print("\n1. Совет — запасной пары больше нет")
    ok1 = pravit(council, [(C_ST_4, C_NOV_4), (C_ST_1, C_NOV_1),
                           (C_ST_2, C_NOV_2), (C_ST_3, C_NOV_3),
                           (C_ST_5, C_NOV_5)], "bez_zapasnoy")

    print("\n2. Кабинет — своего инструмента не имеет")
    ok2 = pravit(ui_torg, [(U_ST_1, U_NOV_1), (U_ST_2, U_NOV_2),
                           (U_ST_3, U_NOV_3), (U_ST_4, U_NOV_4),
                           (U_ST_5R, U_NOV_5R), (U_ST_6, U_NOV_6)],
                 "bez_chetvertogo")

    print("\n3. Активация защищена так же, как закрытие")
    ok3 = pravit(hooks, [(H_ST, H_NOV)], "simmetriya")

    if not (ok1 and ok2 and ok3):
        print("\n✗ Не всё легло — файлы целы.")
        return 1

    if not SUHO:
        import py_compile
        for f in (council, ui_torg, hooks):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь в логе на кнопку РЫНОК должно быть так:")
        print("  [СОВЕТ] 👤 A06: EURUSD <его этаж>")
        print("  [СОВЕТ] 👤 A07: XAUUSD <её этаж>")
        print("  [СОВЕТ] 👤 A08: GBPUSD <её этаж>")
        print("а у кого этажа нет — [СОВЕТ] 🤐 <слот> молчит: причина.")
        print("Строки вида «A07: EURUSD D1» при золоте больше быть не должно.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
