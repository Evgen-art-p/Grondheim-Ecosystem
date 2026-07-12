# -*- coding: utf-8 -*-
"""
patch_natura_v_temperaturu_v1.py
────────────────────────────────────────────────────────────────────
НАТУРА → ТЕМПЕРАТУРА. Душа перестаёт быть текстом и начинает
менять то, КАК думает голова.

ПОЙМАНО ПО ВОПРОСУ ШЕФА (12.07): «строка [LLM] у всех одинакова».
Разбор llm.py + мозга A07 глазами:

  1. В llm.py живёт stress_to_temperature(stress, light) — рабочая
     функция школы: состояние → температура модели.
  2. Вызов в мозге:
         chat(system=..., user=..., knowledge=...,
              agent_id="A07_AVANTURIST", slot_id="trading")
     temperature НЕ ПЕРЕДАЁТСЯ. Ни одним мозгом. Никогда.
  → stress_to_temperature() — МЁРТВАЯ ФУНКЦИЯ. Все девять думают на
    дефолтной температуре модели. Натура (упрямство 0.85, автономия 0.9)
    была только БУКВАМИ В ПРОМПТЕ — на поведение головы не влияла никак.

  Третья отрубленная конечность той же серии: dna.json (мёртвый файл),
  sync_to_dna (мёртвый импорт), stress_to_temperature (мёртвый рычаг).

ЧТО ДЕЛАЕТ:
  • nositel.temperatura_slota(цех, слот) — новый мост:
        заряд носителя + его натура → temperature
        stress = max(0, -заряд)      минус ДАВИТ  → горячее, хаотичнее
        light  = 0.5 + max(0,заряд)/2 плюс ГРЕЕТ  → холоднее, точнее
        затем формула школы (llm.stress_to_temperature),
        затем УПРЯМСТВО гасит размах: упрямого мотает меньше — натура держит.
     Илья (упрямство 0.85):  заряд −0.9 → t=0.90 (нервничает)
                             заряд  0.0 → t=0.58 (спокоен, точен)
                             заряд +0.9 → t=0.54
     Мягкий житель (0.3):    заряд −0.9 → t=0.99 — мотает сильнее.
  • мозг A07: передаёт temperature в chat() (оба вызова: решение и разговор).
  • llm.py: строка лога показывает температуру — и ЧЕСТНО пишет
     «t=дефолт (натура не подключена)» для восьми, кого ещё не трогали.
     Строка перестаёт быть одинаковой у всех.
  • попутно: slot_id="trading" → "A07" (в биллинг шёл цех вместо слота).

ЧЕГО НЕ ДЕЛАЕТ (сознательно — решение Шефа):
  Модель у всех по-прежнему ОДНА (OPENROUTER_MODEL из .env). «Агент сам
  выбирает модель из своей ДНК» — отдельный разговор про деньги и качество,
  не тихий патч. Температура — рычаг, который уже построен и просто не
  подключён; модель — новая сущность.

Требует: patch_etalon_avana_v1. Идемпотентно. .bak рядом.
Из КОРНЯ репы:  python patch_natura_v_temperaturu_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "NATURA_V_TEMPERATURU_V1"

NOSITEL = Path("Биржа") / "nositel.py"
LLM = Path("Биржа") / "llm.py"
BRAIN = (Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" /
         "слоты" / "A07" / "мозг.py")

# ── 1. nositel: новый мост натура→температура ───────────────────
NOS_ANCHOR = """# ════════════════════════════════════════════════════════════
# ПИШУЩИЙ КОНЕЦ — суд рынка оседает ОПЫТОМ в носителя
# ════════════════════════════════════════════════════════════"""

NOS_NEW = '''def temperatura_slota(ceh: str, slot: str):
    """НАТУРА → ТЕМПЕРАТУРА. Как думает голова, а не только что читает.

    До этого моста stress_to_temperature() в llm.py была МЁРТВОЙ: ни один
    мозг не передавал temperature, все девять думали на дефолте модели.
    Душа была буквами в промпте — на поведение головы не влияла.

    Заряд — маятник состояния (Чертёж):
        минус ДАВИТ → stress → выше температура (нервный, хаотичный)
        плюс  ГРЕЕТ → light  → ниже температура (спокойный, точный)
    Упрямство — натура: упрямого мотает МЕНЬШЕ (устойчив к состоянию).

    Честный None — носителя нет: тогда мозг зовёт модель как раньше,
    на дефолте (ничего не ломаем).   # ''' + MARKER + '''
    """
    d = dusha_slota(ceh, slot)
    if not d or not d.get("стол"):
        return None
    stol = d["стол"]
    try:
        from llm import stress_to_temperature
    except Exception:
        return None

    charge = float(stol.get("заряд") or 0.0)
    dna = stol.get("натура") or {}
    stubborn = float(dna.get("Stubbornness", 0.5) or 0.5)

    stress = max(0.0, -charge)              # минус давит
    light = 0.5 + max(0.0, charge) / 2.0    # плюс греет
    t = stress_to_temperature(stress, light)

    # упрямый устойчив: натура гасит размах от состояния
    t = 0.70 + (t - 0.70) * (1.0 - 0.5 * stubborn)
    return round(max(0.3, min(1.2, t)), 2)


''' + NOS_ANCHOR

# ── 2. llm.py: строка лога показывает температуру ───────────────
LLM_OLD = ('    print(f"[LLM] → {agent_id} | контекст: {_ctx_size} симв | '
           'модель: {OPENROUTER_MODEL[:30]}")\n')
LLM_NEW = (
    "    # " + MARKER + ": температура в логе. Раньше строка была одинакова у\n"
    "    # всех — потому что temperature никто не передавал и натура не влияла\n"
    "    # на голову. Честно показываем и тех, кого ещё не подключили.\n"
    '    _t = (f" | t={temperature}" if temperature is not None\n'
    '          else " | t=дефолт (натура не подключена)")\n'
    '    print(f"[LLM] → {agent_id} | контекст: {_ctx_size} симв | '
    'модель: {OPENROUTER_MODEL[:30]}{_t}")\n'
)

# ── 3. мозг A07: передаёт температуру (решение) ─────────────────
BRAIN_OLD_RUN = '''    try:
        response = chat(system=system_full, user=user_msg, knowledge=knowledge,
                        agent_id="A07_AVANTURIST", slot_id="trading")
'''
BRAIN_NEW_RUN = '''    # ''' + MARKER + ''': натура и состояние Ильи меняют ТЕМПЕРАТУРУ головы,
    # а не только текст промпта. None → дефолт модели (как было).
    _temp = None
    try:
        from nositel import temperatura_slota
        _temp = temperatura_slota(_CEH, _SLOT)
        if _temp is not None:
            print(f"[AVAN] 🌡 температура из натуры: {_temp}")
    except Exception:
        pass

    try:
        response = chat(system=system_full, user=user_msg, knowledge=knowledge,
                        agent_id="A07_AVANTURIST", slot_id="A07",
                        temperature=_temp)
'''

# ── 4. мозг A07: то же в разговоре ──────────────────────────────
BRAIN_OLD_CHAT = '''    try:
        return chat(system=system, user=question, history=history,
                    agent_id="A07_AVANTURIST", slot_id="trading")
'''
BRAIN_NEW_CHAT = '''    _temp = None   # ''' + MARKER + ''': и в разговоре голова его, не средняя
    try:
        from nositel import temperatura_slota
        _temp = temperatura_slota(_CEH, _SLOT)
    except Exception:
        pass

    try:
        return chat(system=system, user=question, history=history,
                    agent_id="A07_AVANTURIST", slot_id="A07",
                    temperature=_temp)
'''


def die(m, c=1):
    print("✗ " + m)
    return c


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ НАТУРА → ТЕМПЕРАТУРА (оживляем мёртвый рычаг) ═══")

    for p in (NOSITEL, LLM, BRAIN):
        if not p.exists():
            return die(f"не нашёл {p} — ты в КОРНЕ репы? "
                       "(nositel.py ставит patch_etalon_avana_v1)")

    # ── nositel ──
    n = NOSITEL.read_text(encoding="utf-8")
    if MARKER in n:
        print("✓ nositel уже пропатчен (temperatura_slota)")
    else:
        if NOS_ANCHOR not in n:
            return die("nositel: не нашёл заголовок пишущего конца.", 3)
        bak = NOSITEL.with_suffix(".py.bak")
        if not bak.exists():
            bak.write_text(n, encoding="utf-8")
        NOSITEL.write_text(n.replace(NOS_ANCHOR, NOS_NEW, 1), encoding="utf-8")
        print("✓ nositel: temperatura_slota() — заряд+натура → температура")

    # ── llm ──
    l = LLM.read_text(encoding="utf-8")
    if MARKER in l:
        print("✓ llm уже пропатчен (температура в логе)")
    else:
        if LLM_OLD not in l:
            return die("llm.py: не нашёл строку лога [LLM] →. Сверь глазами.", 4)
        bak = LLM.with_suffix(".py.bak")
        if not bak.exists():
            bak.write_text(l, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        LLM.write_text(l.replace(LLM_OLD, LLM_NEW, 1), encoding="utf-8")
        print("✓ llm.py: строка лога показывает t= (и честно — у кого дефолт)")

    # ── мозг ──
    b = BRAIN.read_text(encoding="utf-8")
    if MARKER in b:
        print("✓ мозг A07 уже пропатчен (передаёт температуру)")
    else:
        for old, what in ((BRAIN_OLD_RUN, "вызов chat в run_avan"),
                          (BRAIN_OLD_CHAT, "вызов chat в chat_with_avan")):
            if old not in b:
                return die(f"мозг A07: не нашёл «{what}». Сверь глазами.", 5)
        bak = BRAIN.with_suffix(".py.bak3")
        if not bak.exists():
            bak.write_text(b, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        b = b.replace(BRAIN_OLD_RUN, BRAIN_NEW_RUN, 1)
        b = b.replace(BRAIN_OLD_CHAT, BRAIN_NEW_CHAT, 1)
        BRAIN.write_text(b, encoding="utf-8")
        print("✓ мозг A07: temperature из натуры + slot_id 'trading' → 'A07'")

    print("───")
    print("Теперь в логе строка Ильи будет ОТЛИЧАТЬСЯ от остальных:")
    print("  [AVAN] 🌡 температура из натуры: 0.58")
    print("  [LLM] → A07_AVANTURIST | ... | модель: ... | t=0.58")
    print("  [LLM] → A06_BRUT       | ... | модель: ... | t=дефолт (натура не подключена)")
    print("\nМодель у всех по-прежнему одна (из .env) — это отдельное решение,")
    print("не тихий патч. Скажешь «даём каждому свою» — построю.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
