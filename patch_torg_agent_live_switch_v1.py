# -*- coding: utf-8 -*-
"""
patch_torg_agent_live_switch_v1.py
─────────────────────────────────────────────────────────────
ПОРТРЕТ + ОТЧЁТ НА КАЖДОМ АГЕНТЕ · Биржа/ui_torg.py · _apply_agent_result

ДИАГНОЗ (слово Шефа, подтверждено чтением кода):
  Большой портрет в правой колонке ("АКТИВНЫЙ АГЕНТ") и окно отчётов
  переключались ТОЛЬКО когда отрабатывала Искра (A01). У веток
  A02-A09 не было ДВУХ вещей:
    1. state["active_agent"] = aid  — без неё update_avatar() не
       знает, кого рисовать, всю цепочку думает что активна Искра.
    2. update_avatar() / update_viewer(...) — вызывались только у A01,
       у остальных только update_avatar_states() (красит МАЛЕНЬКИЕ
       пузырьки active/done, не большой портрет и не окно отчёта).

  Итог: пузырьки в хедере светились по ходу Совета честно, а большой
  портрет и окно отчётов справа — молчали для всех, кроме A01.

ЛЕЧЕНИЕ:
  В каждую ветку A02...A09 добавлены три строки (по образцу A01):
    state["active_agent"] = <aid>
    update_avatar()
    update_vitals()
    update_viewer(f"# {icon} {label} ({aid})\\n\\n{narrative}")
  Ставятся ПОСЛЕ того, как ветка положила данные в state (сохраняем
  порядок: сначала данные, потом отрисовка — тот же порядок, что у A01).

Запуск из КОРНЯ репо (Windows/PowerShell):
    python patch_torg_agent_live_switch_v1.py

Идемпотентно: маркер AGENT_LIVE_SWITCH_V1 — повторный запуск скажет
"уже пропатчено" и ничего не тронет второй раз.
─────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Биржа" / "ui_torg.py"
MARKER = "# AGENT_LIVE_SWITCH_V1 — маркер идемпотентности"

REPLACEMENTS = []

# ── A02 МОРЖ ──
REPLACEMENTS.append(("A02", '''            state["chat_history"].append({
                "role": "assistant", "agent": "A02",
                "content": (f"🦭 Посмотрел. Пасть: {sig.get('morj_status','—')}, резинка "
                            f"{'натянута' if sig.get('tension_peak') else 'вяло'}. Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"🦭 Морж: {sig.get('morj_status','—')}", type="positive")''',
'''            state["active_agent"] = "A02"   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# 🦭 {_agent_label(roster,'A02')} (A02)\\n\\n{narrative or '*(нет текста)*'}")
            state["chat_history"].append({
                "role": "assistant", "agent": "A02",
                "content": (f"🦭 Посмотрел. Пасть: {sig.get('morj_status','—')}, резинка "
                            f"{'натянута' if sig.get('tension_peak') else 'вяло'}. Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"🦭 Морж: {sig.get('morj_status','—')}", type="positive")'''))

# ── A03 ПАНИКЁР ──
REPLACEMENTS.append(("A03", '''            state["chat_history"].append({
                "role": "assistant", "agent": "A03",
                "content": (f"😱 Толпа: {sig.get('panic_phase','—')}. "
                            f"{sig.get('crowd_sentiment','')} Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"😱 Паникёр: {sig.get('panic_phase','—')}", type="positive")''',
'''            state["active_agent"] = "A03"   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# 😱 {_agent_label(roster,'A03')} (A03)\\n\\n{narrative or '*(нет текста)*'}")
            state["chat_history"].append({
                "role": "assistant", "agent": "A03",
                "content": (f"😱 Толпа: {sig.get('panic_phase','—')}. "
                            f"{sig.get('crowd_sentiment','')} Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"😱 Паникёр: {sig.get('panic_phase','—')}", type="positive")'''))

# ── A04 ГАНС ──
REPLACEMENTS.append(("A04", '''            state["chat_history"].append({
                "role": "assistant", "agent": "A04", "content": f"🎯 Фрактал: {prey}. Отчёт справа."})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"🎯 Ганс: {'фрактал вне Красной' if valid else 'пусто'}", type="positive")''',
'''            state["active_agent"] = "A04"   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# 🎯 {_agent_label(roster,'A04')} (A04)\\n\\n{narrative or '*(нет текста)*'}")
            state["chat_history"].append({
                "role": "assistant", "agent": "A04", "content": f"🎯 Фрактал: {prey}. Отчёт справа."})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"🎯 Ганс: {'фрактал вне Красной' if valid else 'пусто'}", type="positive")'''))

# ── A05 АРХИВАРИУС ──
REPLACEMENTS.append(("A05", '''            state["chat_history"].append({
                "role": "assistant", "agent": "A05",
                "content": (f"📚 Похожих случаев в Атласе: {n_}. Уверенность: {conf}. Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"📚 Архивариус: {conf} ({n_} случаев)", type="positive")''',
'''            state["active_agent"] = "A05"   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# 📚 {_agent_label(roster,'A05')} (A05)\\n\\n{narrative or '*(нет текста)*'}")
            state["chat_history"].append({
                "role": "assistant", "agent": "A05",
                "content": (f"📚 Похожих случаев в Атласе: {n_}. Уверенность: {conf}. Отчёт справа.")})
            update_chat_display()
            update_avatar_states()
            ui.notify(f"📚 Архивариус: {conf} ({n_} случаев)", type="positive")'''))

# ── A06/A07/A08 ТРЕЙДЕРЫ (общий блок) ──
REPLACEMENTS.append(("A06/A07/A08", '''            state["chat_history"].append({"role": "assistant", "agent": aid, "content": line})
            update_chat_display()
            update_avatar_states()

        # ── A09 ИСПОЛНИТЕЛЬ ──''',
'''            state["active_agent"] = aid   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# {icon} {_nm} ({aid})\\n\\n{narrative or '*(нет текста)*'}")
            state["chat_history"].append({"role": "assistant", "agent": aid, "content": line})
            update_chat_display()
            update_avatar_states()

        # ── A09 ИСПОЛНИТЕЛЬ ──'''))

# ── A09 ИСПОЛНИТЕЛЬ ──
REPLACEMENTS.append(("A09", '''            line = f"📋 Исполнитель: ордеров {sent} из 3 · task_score {tsk}. {sig.get('history_dna','')}"
            ui.notify(f"📋 Исполнитель: {sent} из 3", type="positive")
            state["chat_history"].append({"role": "assistant", "agent": "A09", "content": line})
            update_chat_display()
            update_avatar_states()''',
'''            state["active_agent"] = "A09"   # AGENT_LIVE_SWITCH_V1
            update_avatar()
            update_vitals()
            update_viewer(f"# 📋 {_agent_label(roster,'A09')} (A09)\\n\\n{state['reports']['A09']}")
            line = f"📋 Исполнитель: ордеров {sent} из 3 · task_score {tsk}. {sig.get('history_dna','')}"
            ui.notify(f"📋 Исполнитель: {sent} из 3", type="positive")
            state["chat_history"].append({"role": "assistant", "agent": "A09", "content": line})
            update_chat_display()
            update_avatar_states()'''))


def _patch():
    if not TARGET.exists():
        print(f"[ПАТЧ] ❌ Не найден {TARGET} — запусти из корня репо.")
        raise SystemExit(1)

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[ПАТЧ] ✅ ui_torg.py уже пропатчен (AGENT_LIVE_SWITCH_V1) — пропускаю.")
        return False

    changed = 0
    for label, old, new in REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changed += 1
            print(f"[ПАТЧ] 🔧 {label}: портрет+виталы+отчёт добавлены")
        elif new in src:
            print(f"[ПАТЧ] ↺ {label}: уже на месте")
        else:
            print(f"[ПАТЧ] ⚠️  {label}: блок не совпал — проверь вручную")

    if changed == 0:
        print("[ПАТЧ] ⚠️  ничего не изменилось.")
        return False

    src = src.rstrip() + "\n\n" + MARKER + "\n"
    TARGET.write_text(src, encoding="utf-8")
    print(f"[ПАТЧ] 💾 ui_torg.py сохранён (веток исправлено: {changed} из 6).")
    return True


def main():
    print("═" * 62)
    print("  ПОРТРЕТ + ОТЧЁТ НА КАЖДОМ АГЕНТЕ · AGENT_LIVE_SWITCH_V1")
    print("═" * 62)
    _patch()
    print("═" * 62)
    print("  ✅ ГОТОВО. ПЕРЕЗАПУСТИ студию (файл на диске не подхватится")
    print("     старым процессом сам).")
    print("     Проверка: жми РЫНОК или ТЕСТЕР — портрет справа и окно")
    print("     отчёта должны меняться на КАЖДОМ агенте по ходу цепочки,")
    print("     не только на Искре.")
    print("═" * 62)


if __name__ == "__main__":
    main()
