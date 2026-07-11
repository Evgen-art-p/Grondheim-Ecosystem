# -*- coding: utf-8 -*-
"""
patch_torg_learn_switch_v1.py
────────────────────────────────────────────────────────────────────
РУБИЛЬНИК «УЧИТЬ» В КАБИНЕТЕ.

ДЫРА (поймана чтением ui_torg.py, 12.07): кабинет зовёт тестер БЕЗ
параметра learn:
    run_tester(csv_path=..., symbol=..., timeframe=...,
               n_signals=n, on_progress=..., should_stop=...)
→ learn=False всегда → прогон ВСЕГДА стерильный → нога Опыта молчит →
  якоря жителей из кабинета НЕ РАСТУТ НИКОГДА, сколько ни жми ТЕСТЕР.
  Шеф смотрел бы в passport.json и не понимал, почему пусто.

  (Из командной строки --learn есть. Но Шеф работает кнопкой.)

ЛЕЧЕНИЕ: тумблер «УЧИТЬ» в тулбаре, рядом со СТОП. Виден только в
режиме ТЕСТЕР (как «ловить» и СТОП). Гаснет по умолчанию — смотреть
безопасно, калечить только осознанно.

    УЧИТЬ выкл (умолчание) → стерильно: Совет думает, трейдер читает
        свою душу, сделки считаются — но паспорта жителей не трогаются.
    УЧИТЬ вкл → учебный прогон: якоря растут, заряд качается, ДНК живёт.

Требует: patch_tester_sterile_opyt_v1 (иначе стерильность фиктивна —
нога Опыта пишет в паспорт даже без учёбы).

Идемпотентно. .bak рядом. Из КОРНЯ репы:
    python patch_torg_learn_switch_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "TORG_LEARN_SWITCH_V1"
TARGET = Path("Биржа") / "ui_torg.py"
NEED = "TESTER_STERILE_OPYT_V1"

# ── 1. состояние ────────────────────────────────────────────────
OLD_STATE = """        "stop_requested": False,
        "tester_running": False,
"""
NEW_STATE = """        "stop_requested": False,
        "tester_running": False,
        "learn": False,          # """ + MARKER + """: учебный прогон (якоря растут)
"""

# ── 2. тумблер: функция ─────────────────────────────────────────
OLD_STOP_FN = """    def request_stop():
        if not state.get("tester_running"):
            ui.notify("Перебор не идёт", type="warning")
            return
        state["stop_requested"] = True
        ui.notify("⏸ СТОП — останавливаю на следующем кандидате...", type="info")
"""
NEW_STOP_FN = OLD_STOP_FN + """
    def toggle_learn():
        \"\"\"""" + MARKER + """: УЧИТЬ — писать ли выводы из сделок в живых жителей.

        Выкл (умолчание) — стерильно: смотрим, не калеча. Трейдер всё равно
        сидит за столом СОБОЙ (читающий конец души работает всегда), но
        паспорта не трогаются: якоря не растут, заряд не едет.
        Вкл — учебный прогон: рынок судит, вывод оседает в носителя.
        \"\"\"
        if state.get("tester_running"):
            ui.notify("Идёт прогон — переключай до старта", type="warning")
            return
        state["learn"] = not state.get("learn", False)
        on = state["learn"]
        el = toolbar_refs.get("learn_btn")
        if el:
            el.style(
                "display:flex;align-items:center;padding:6px 14px;border-radius:7px;"
                "font-size:12px;font-weight:700;cursor:pointer;" + (
                    "background:rgba(189,0,255,0.15);color:#bd88ff;"
                    "border:1px solid rgba(189,0,255,0.45);"
                    if on else
                    "background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.45);"
                    "border:1px solid rgba(255,255,255,0.08);"
                ))
        ui.notify(
            "🎓 УЧИТЬ включено: якоря жителей будут расти, заряд качаться"
            if on else
            "🧪 УЧИТЬ выключено: стерильно — паспорта жителей не трогаем",
            type="warning" if on else "info")
"""

# ── 3. видимость в режиме ТЕСТЕР ────────────────────────────────
OLD_VIS = '        for key in ("bars_input", "stop_btn", "bars_label"):'
NEW_VIS = ('        for key in ("bars_input", "stop_btn", "bars_label",\n'
           '                    "learn_btn"):   # ' + MARKER + "\n")

# ── 4. кнопка в тулбаре (после СТОП) ────────────────────────────
OLD_BTN = """                        toolbar_refs["stop_btn"].on("click", lambda: request_stop())
                        with toolbar_refs["stop_btn"]:
                            ui.html("⏸ СТОП")
"""
NEW_BTN = OLD_BTN + """                        # """ + MARKER + """: рубильник учёбы — рядом со СТОП
                        toolbar_refs["learn_btn"] = ui.element("div").style(
                            "display:none;align-items:center;padding:6px 14px;border-radius:7px;"
                            "font-size:12px;font-weight:700;cursor:pointer;"
                            "background:rgba(255,255,255,0.03);color:rgba(255,255,255,0.45);"
                            "border:1px solid rgba(255,255,255,0.08);")
                        toolbar_refs["learn_btn"].on("click", lambda: toggle_learn())
                        with toolbar_refs["learn_btn"]:
                            ui.html("🎓 УЧИТЬ")
"""

# ── 5. проброс в тестер ─────────────────────────────────────────
OLD_CALL = """                lambda: run_tester(
                    csv_path=path, symbol=symbol, timeframe=tf,
                    n_signals=n, on_progress=_on_progress,
                    should_stop=_should_stop,
                )
"""
NEW_CALL = """                lambda: run_tester(
                    csv_path=path, symbol=symbol, timeframe=tf,
                    n_signals=n, on_progress=_on_progress,
                    should_stop=_should_stop,
                    learn=state.get("learn", False),   # """ + MARKER + """
                )
"""

# ── 6. честная строка в чате на старте ──────────────────────────
OLD_MSG = """        state["chat_history"].append({
            "role": "assistant", "agent": "SYSTEM",
            "content": f"▶ ТЕСТЕР: гоню {symbol} {tf} · ловлю {n} срабатываний. СТОП — прервать."})
"""
NEW_MSG = """        _uch = ("🎓 УЧЕБНЫЙ (якоря жителей растут)" if state.get("learn")
                else "🧪 стерильный (паспорта не трогаем)")   # """ + MARKER + """
        state["chat_history"].append({
            "role": "assistant", "agent": "SYSTEM",
            "content": f"▶ ТЕСТЕР: гоню {symbol} {tf} · ловлю {n} срабатываний · "
                       f"{_uch}. СТОП — прервать."})
"""


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запусти из КОРНЯ репы.")
        return 1

    tester = Path("Биржа") / "tester_express.py"
    if tester.exists() and NEED not in tester.read_text(encoding="utf-8"):
        print("✗ сначала patch_tester_sterile_opyt_v1.py — иначе стерильность "
              "фиктивна: нога Опыта пишет в паспорта даже без учёбы.")
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    blocks = [
        (OLD_STATE, NEW_STATE, "состояние кабинета"),
        (OLD_STOP_FN, NEW_STOP_FN, "функция request_stop (после неё — toggle_learn)"),
        (OLD_VIS, NEW_VIS, "видимость кнопок в режиме ТЕСТЕР"),
        (OLD_BTN, NEW_BTN, "кнопка СТОП в тулбаре"),
        (OLD_CALL, NEW_CALL, "вызов run_tester"),
        (OLD_MSG, NEW_MSG, "строка старта тестера в чате"),
    ]
    for old, _new, what in blocks:
        if old not in src:
            print(f"✗ не нашёл блок: {what}. Файл правился вручную? Сверь глазами.")
            return 3

    bak = TARGET.with_suffix(".py.bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")

    for old, new, _ in blocks:
        src = src.replace(old, new, 1)
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ {TARGET}: тумблер «🎓 УЧИТЬ» в тулбаре (виден в режиме ТЕСТЕР).")
    print("   выкл (умолчание) → стерильно: смотрим, не калеча")
    print("   вкл              → якоря жителей растут, заряд качается")
    print(f"   Маркер: {MARKER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
