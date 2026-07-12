# -*- coding: utf-8 -*-
"""
patch_pribory_trejderov_v1.py
────────────────────────────────────────────────────────────────────
ПРИБОРЫ ПОСЛЕ АРХИВАРИУСА — их не было вообще, не мы сломали.

ЖАЛОБА ШЕФА (12.07): «показатели в кабинете... не меняются, приборы
тоже после архивариуса нет ни у кого».

РАЗБОР: update_stats_panel() в ui_torg.py — старый код, ещё из -2.
Ветки прописаны ТОЛЬКО для A01(Искра)/A02(Морж)/A03(Паникёр)/
A04(Ганс)/A05(Архивариус). Для A06(Брут)/A07(Авантюрист)/
A08(Консерватор)/A09(Исполнитель) отдельной ветки НЕТ — код падает
в общую заглушку «Приборы появятся при подключении агента» и стоит
там навсегда, сколько бы Совет ни работал. Пробел старый, наши
патчи (магик/душа/температура/якоря) его не касались — просто
раньше никто не долистывал кабинет до трейдеров, чтобы заметить.

ЧТО ДЕЛАЕТ: добавляет ДВЕ ветки в update_stats_panel(), ПЕРЕД
заглушкой-фоллбэком (она остаётся — safety net на случай будущих
слотов):

  A06/A07/A08 (трейдеры) — один код на всех троих (pre=brut/avan/cons,
  та же связка, что уже использует _apply_agent_result): ВЕРДИКТ
  (APPROVED/REJECTED), при входе — НАПРАВЛЕНИЕ/ВХОД-СТОП/ЛОТ, при
  отказе — ПРИЧИНА. Поля читает из sig — те же avan_verdict/
  avan_direction/... что уже пишет мозг A07 (проверено по user_msg).

  A09 (Исполнитель) — ОРДЕРОВ (из 3), TASK_SCORE, летопись строкой.

Идемпотентно. .bak рядом. Из КОРНЯ репы:
    python patch_pribory_trejderov_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "PRIBORY_TREJDEROV_V1"
TARGET = Path("Биржа") / "ui_torg.py"

OLD = '''        if state["active_agent"] != "A01":
            with stats_ref["element"]:
                ui.html('<div style="color:rgba(255,255,255,0.3); font-size:11px; '
                        'padding:10px; text-align:center;">Приборы появятся при подключении агента</div>')
            return'''

NEW = '''        # ''' + MARKER + ''': трейдеры (A06/A07/A08) — приборов не было ВООБЩЕ,
        # код падал сразу в заглушку ниже. Один шаблон на троих — та же
        # связка pre=brut/avan/cons, что уже использует _apply_agent_result.
        if state["active_agent"] in ("A06", "A07", "A08"):
            pre = {"A06": "brut", "A07": "avan", "A08": "cons"}[state["active_agent"]]
            _label = _agent_label(roster, state["active_agent"])
            tsig = state.get(f"{pre}_signal", {})
            tst  = state.get(f"{pre}_stats", {})
            if not tsig:
                with stats_ref["element"]:
                    ui.html(f'<div style="color:rgba(255,255,255,0.3); font-size:11px; '
                            f'padding:10px; text-align:center;">{_label} ещё не смотрел(а) '
                            f'стол — нажми РЫНОК (нужен сигнал Искры)</div>')
                return
            verdict = tsig.get(f"{pre}_verdict", "—")
            v_ok = (verdict == "APPROVED")
            v_color = "#00ff88" if v_ok else "rgba(255,255,255,0.5)"
            body = (
                '<div style="display:flex; justify-content:space-between; margin-bottom:7px;">'
                '<span style="color:rgba(255,255,255,0.45); font-size:10px;">ВЕРДИКТ</span>'
                f'<span style="color:{v_color}; font-size:11px; font-weight:700;">{verdict}</span></div>'
            )
            if v_ok:
                direction = tsig.get(f"{pre}_direction", "—") or "—"
                entry = tsig.get(f"{pre}_entry", "—")
                stop  = tsig.get(f"{pre}_stop", "—")
                lot   = tsig.get(f"{pre}_lot", "—")
                body += (
                    '<div style="display:flex; justify-content:space-between; margin-bottom:7px;">'
                    '<span style="color:rgba(255,255,255,0.45); font-size:10px;">НАПРАВЛЕНИЕ</span>'
                    f'<span style="color:rgba(0,204,255,0.9); font-size:11px; font-weight:700;">{direction}</span></div>'
                    '<div style="display:flex; justify-content:space-between; margin-bottom:7px;">'
                    '<span style="color:rgba(255,255,255,0.45); font-size:10px;">ВХОД / СТОП</span>'
                    f'<span style="color:rgba(255,255,255,0.7); font-size:11px;">{entry} / {stop}</span></div>'
                    '<div style="display:flex; justify-content:space-between; margin-bottom:10px;">'
                    '<span style="color:rgba(255,255,255,0.45); font-size:10px;">ЛОТ</span>'
                    f'<span style="color:rgba(255,255,255,0.7); font-size:11px;">{lot}</span></div>'
                )
            else:
                reason = tsig.get(f"{pre}_reason", "—") or "—"
                body += (
                    '<div style="margin-bottom:10px;">'
                    '<span style="color:rgba(255,255,255,0.45); font-size:10px;">ПРИЧИНА</span>'
                    '<div style="color:rgba(255,255,255,0.7); font-size:10px; font-style:italic;'
                    f'margin-top:3px; line-height:1.4;">«{reason}»</div></div>'
                )
            body += (
                '<div style="border-top:1px solid rgba(255,255,255,0.08); padding-top:8px;'
                'color:rgba(255,255,255,0.35); font-size:9px; line-height:1.7;">'
                f'взглядов: {tst.get("runs","—")} · '
                f'входов: {tst.get("approved","—")} · '
                f'пасов: {tst.get("rejected","—")}</div>'
            )
            with stats_ref["element"]:
                ui.html(f'<div style="padding:10px 12px; '
                        f'font-family:\\'JetBrains Mono\\',monospace;">{body}</div>')
            return

        # ''' + MARKER + ''': Исполнитель (A09) — тоже приборов не было.
        if state["active_agent"] == "A09":
            esig = state.get("executor_signal", {})
            if not esig:
                with stats_ref["element"]:
                    ui.html('<div style="color:rgba(255,255,255,0.3); font-size:11px; '
                            'padding:10px; text-align:center;">Исполнитель ещё не '
                            'подводил итог — нажми РЫНОК (нужен сигнал Искры)</div>')
                return
            fdna = esig.get("final_dna", {})
            sent = fdna.get("orders_sent", "—")
            tsk  = fdna.get("task_score", "—")
            hist = esig.get("history_dna", "") or "—"
            with stats_ref["element"]:
                ui.html(f\'\'\'
                <div style="padding:10px 12px; font-family:'JetBrains Mono',monospace;">
                  <div style="display:flex; justify-content:space-between; margin-bottom:7px;">
                    <span style="color:rgba(255,255,255,0.45); font-size:10px;">ОРДЕРОВ</span>
                    <span style="color:rgba(0,204,255,0.9); font-size:11px; font-weight:700;">{sent} из 3</span>
                  </div>
                  <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="color:rgba(255,255,255,0.45); font-size:10px;">TASK_SCORE</span>
                    <span style="color:rgba(255,255,255,0.7); font-size:11px;">{tsk}</span>
                  </div>
                  <div style="border-top:1px solid rgba(255,255,255,0.08); padding-top:8px;
                              color:rgba(255,255,255,0.35); font-size:9px; line-height:1.4;">
                    {hist}
                  </div>
                </div>
                \'\'\')
            return

        if state["active_agent"] != "A01":
            with stats_ref["element"]:
                ui.html('<div style="color:rgba(255,255,255,0.3); font-size:11px; '
                        'padding:10px; text-align:center;">Приборы появятся при подключении агента</div>')
            return'''


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ ПРИБОРЫ ТРЕЙДЕРОВ И ИСПОЛНИТЕЛЯ (A06-A09) ═══")

    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — ты в КОРНЕ репы?")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ уже пропатчено ({MARKER}) — ничего не делаю.")
        return 0

    if OLD not in src:
        print("✗ не нашёл заглушку «Приборы появятся при подключении агента» "
              "в ожидаемом виде. Файл правился вручную? Сверь глазами.")
        return 2

    bak = TARGET.with_suffix(".py.bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        print(f"• бэкап: {bak}")

    src = src.replace(OLD, NEW, 1)
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ {TARGET}: приборы для A06/A07/A08 (трейдеры) + A09 (Исполнитель).")
    print(f"  Маркер: {MARKER}")
    print("\nПерезапусти кабинет и щёлкни по Брут/Илье/Василию/Исполнителю —")
    print("приборы больше не заглушка.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
