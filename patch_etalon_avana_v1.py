# -*- coding: utf-8 -*-
"""
patch_etalon_avana_v1.py
────────────────────────────────────────────────────────────────────
ЭТАЛОН АВАНА — кольцо замыкается на ОДНОМ человеке (Илья, A07).
После отладки на нём — клон на Брута (A06) и Василия (A08).

ТРИ ШАГА:

  1. СТАВИТ ДВЕРЬ  Биржа/nositel.py (новый файл).
     Мост между РОЛЬЮ (слот) и РОДОМ (житель). ОДНА дверь на все девять
     мозгов + hooks — не вписываем сборку души в каждый мозг, иначе через
     месяц одиннадцать копий разъедутся (ровно болезнь четырёх магиков).

  2. ЧИТАЮЩИЙ КОНЕЦ  мозг A07:
       было:  from studio.grondheim_memory import format_soul_for_agent
              soul = format_soul_for_agent("A07_AVANTURIST", ...)   → ""
              (studio/ снесена — импорт падал ВСЕГДА, трейдер работал
               голым промптом; обещание «твоя ДНК — ниже» было пустым)
       стало: nositel.dusha_slota("торговый_хаос", "A07") → ИЛЬЯ,
              его род, натура, история и ЕГО ЯКОРЯ (нога Опыта) в промпт.
     Два места (run_avan + chat_with_avan) — оба.

     И УБИВАЕТ ПЯТУЮ КОПИЮ МАГИКА: _MY_MAGIC = 100002 (константа в мозге)
     → магик берётся из МАСКИ, единственной правды (Закон Пары).

  3. ПИШУЩИЙ КОНЕЦ  hooks._judge_trader_by_result (был честный no-op):
       magic закрытой позиции → resolve_by_magic → ИЛЬЯ →
       вывод по Котину (считает КОД, не LLM) → в ЕГО ЖЕ якоря.
     Рутина в опыт не идёт (якорей 7-10 — это ОПЫТ, не журнал; факт
     сделки и так в pnl.jsonl = ПАМЯТЬ роли). Значимо: минус ПРОТИВ
     ветра — всегда; |pnl_r| >= 2R — всегда.

ТРЕБУЕТ (проверяет сам): patch_magic_v_masku_v1, patch_dvizhok_stol_
  chisto_vyvod_v1, patch_dvizhok_yakorya_yadro_v1.

Идемпотентно. .bak рядом. Из КОРНЯ репы:
    python patch_etalon_avana_v1.py
    python proverka_koltsa.py        # проверка кольца, ASCII-имя
"""
from __future__ import annotations
import io
import shutil
import sys
from pathlib import Path

MARKER_BRAIN = "AVAN_NOSITEL_V1"
MARKER_HOOKS = "JUDGE_TRADER_NOSITEL_V1"

ROOT = Path(".").resolve()
BIRZHA = Path("Биржа")
BRAIN = (Path("GRONDHEIM_CITY") / "Биржа" / "цеха" / "торговый_хаос" /
         "слоты" / "A07" / "мозг.py")
HOOKS = BIRZHA / "hooks.py"
DOOR_SRC = Path("nositel.py")              # лежит рядом с патчем
DOOR_DST = BIRZHA / "nositel.py"

# ══ ШАГ 2: мозг A07 ══════════════════════════════════════════════

# 2a. магик — из маски, не константой
OLD_MAGIC = '_MY_MAGIC = 100002   # паспорт трейдера (как у Исполнителя)\n'
NEW_MAGIC = (
    "# " + MARKER_BRAIN + ": магик — из МАСКИ носителя (Закон Пары), не константой.\n"
    "# Копий магика было ПЯТЬ (дом, этот файл, hooks, промт A09, лор) — так они\n"
    "# и разъезжаются. Правда одна: маски/работа/mask.json жителя.\n"
    "_CEH  = _CEH_DIR.name      # 'торговый_хаос'\n"
    "_SLOT = _SLOT_DIR.name     # 'A07'\n"
    "\n"
    "\n"
    "def _my_magic():\n"
    '    """Магик ТОГО, кто сидит в этом слоте. Нет носителя → None."""\n'
    "    try:\n"
    "        from nositel import magic_slota\n"
    "        return magic_slota(_CEH, _SLOT)\n"
    "    except Exception as e:\n"
    '        print(f"[AVAN] ⚠️  магик из маски не прочитан ({e})")\n'
    "        return None\n"
)

OLD_POS = '        if p.get("magic") == _MY_MAGIC and p.get("status") == "OPEN":\n'
NEW_POS = (
    "    _magic = _my_magic()   # " + MARKER_BRAIN + "\n"
    "    if _magic is None:\n"
    "        return None        # без магика свою позицию не опознать — честно\n"
    "    for p in positions:\n"
    '        if p.get("magic") == _magic and p.get("status") == "OPEN":\n'
)
OLD_POS_FULL = (
    "    mine = None\n"
    "    for p in positions:\n"
    + OLD_POS
)
NEW_POS_FULL = (
    "    mine = None\n"
    + NEW_POS
)

# 2b. душа в run_avan
OLD_SOUL_RUN = (
    '    soul = ""\n'
    "    try:\n"
    "        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]\n"
    '        soul = format_soul_for_agent("A07_AVANTURIST", dept="trading")\n'
    "    except Exception as e:\n"
    '        print(f"[AVAN] ⚠️  Душа не загрузилась ({e}) — работаю без неё")\n'
)
NEW_SOUL_RUN = (
    '    # ' + MARKER_BRAIN + ": ДУША — от НОСИТЕЛЯ, не от трупа роли из -2.\n"
    "    # Было: format_soul_for_agent('A07_AVANTURIST') из снесённой studio/ →\n"
    "    # импорт падал всегда, soul='' , торговал 'Авантюрист-вообще'.\n"
    "    # Стало: за столом сидит ИЛЬЯ — его род, натура и ЕГО ЯКОРЯ (опыт).\n"
    '    soul = ""\n'
    "    try:\n"
    "        from nositel import dusha_slota\n"
    "        _n = dusha_slota(_CEH, _SLOT)\n"
    "        if _n:\n"
    '            soul = _n["душа"]\n'
    '            print(f"[AVAN] 🧬 За столом: {_n[\'носитель\'][\'имя\']} "\n'
    '                  f"(magic {_n[\'magic\']})")\n'
    "    except Exception as e:\n"
    '        print(f"[AVAN] ⚠️  Носитель не поднялся ({e}) — работаю без души")\n'
)

# 2c. душа в chat_with_avan
OLD_SOUL_CHAT = (
    "    system = prompt + work_ctx\n"
    "    try:\n"
    "        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]\n"
    '        soul = format_soul_for_agent("A07_AVANTURIST", dept="trading")\n'
    "        if soul:\n"
    '            system = prompt + "\\n\\n=== ТВОЁ СОСТОЯНИЕ (душа) ===\\n" + soul + "\\n\\n" + work_ctx\n'
    "    except Exception:\n"
    "        pass\n"
)
NEW_SOUL_CHAT = (
    "    system = prompt + work_ctx\n"
    "    try:   # " + MARKER_BRAIN + ": в разговоре тоже ОН, не роль\n"
    "        from nositel import dusha_slota\n"
    "        _n = dusha_slota(_CEH, _SLOT)\n"
    '        if _n and _n["душа"]:\n'
    '            system = (prompt + "\\n\\n=== КТО ТЫ (душа носителя) ===\\n"\n'
    '                      + _n["душа"] + "\\n\\n" + work_ctx)\n'
    "    except Exception:\n"
    "        pass\n"
)

# ══ ШАГ 3: hooks — пишущий конец ═════════════════════════════════
OLD_JUDGE = '''def _judge_trader_by_result(pos: dict, pnl_r):
    """
    СУД ТРЕЙДЕРА — не построена в этом городе.

    Логика "минус против ветра → накажи, минус по ветру → прости"
    (§12 Котина) остаётся ВЕРНОЙ идеей — но раньше она сразу дёргала
    ДНК через studio.grondheim_memory.sync_to_dna, чего в этом
    городе больше нет физически. Это ровно нога "Опыт" Стола
    Трейдера (Чертёж Единицы, Гл.5.2 — "стол на двух ногах, инвалид"),
    и её нужно строить заново, не восстановлением мёртвого импорта.
    Честный no-op — записи pnl.jsonl эта функция не трогает, факт
    сделки остаётся в журнале в любом случае (_settle_positions уже
    записал его выше).
    """
    return
'''

NEW_JUDGE = '''def _judge_trader_by_result(pos: dict, pnl_r):
    """
    СУД ТРЕЙДЕРА — НОГА ОПЫТА. Построена.   # ''' + MARKER_HOOKS + '''

    Рынок рассудил (Чертёж: САМЫЙ чистый судья, без апелляций) — вывод
    оседает в НОСИТЕЛЯ, не в труп роли из -2:
        magic позиции → resolve_by_magic → житель (Илья/Брут/Василий)
        → вывод по Котину → в ЕГО ЖЕ Anchor_Points (лимит 7-10)

    Это НЕ старый маятник sync_to_dna: тот качал состояние по факту
    (Чертёж Гл.4.2 прямо зовёт его НЕ-опытом, «обучение первого уровня,
    без понимания»). Здесь — ВЫВОД словами, который трейдер прочтёт
    перед следующей сделкой и сможет с ним спорить.

    ОПЫТ ≠ ПАМЯТЬ (Чертёж): факт КАЖДОЙ сделки уже лёг в pnl.jsonl и в
    дневник роли — это память. В якоря (их всего 7-10) идёт только
    значимое: минус ПРОТИВ ветра (тот самый систематический стоп) и
    любая крайность |pnl_r| >= 2R. Рутина в опыт не лезет.

    pnl.jsonl эта функция не трогает. Упадёт — торговый цикл цел.
    """
    try:
        import sys as _s
        from pathlib import Path as _P
        _b = str(_P(__file__).resolve().parent)
        if _b not in _s.path:
            _s.path.insert(0, _b)
        from nositel import sudit_po_kotinu, zapisat_vyvod

        vyvod = sudit_po_kotinu(
            pos.get("direction"),
            pos.get("entry_bias"),      # ветер на баре ВХОДА (уже в позиции)
            pnl_r,
            pos.get("close_reason"),
            pos.get("opened_at"),
        )
        if not vyvod:
            return                      # рутина — живёт в журнале, не в опыте
        zapisat_vyvod(pos.get("magic"), vyvod, pnl_r=pnl_r)
    except Exception as e:
        print(f"[СУД] ⚠️  нога Опыта не сработала ({e}) — сделка в журнале цела")
    return
'''


def die(msg: str, code: int = 1) -> int:
    print("✗ " + msg)
    return code


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ ЭТАЛОН АВАНА — кольцо на Илье (A07) ═══")

    # ── проверка фундамента ──────────────────────────────────────
    reg = BIRZHA / "cartridge_registry.py"
    dvi = Path("жители") / "dvizhok.py"
    if not reg.exists() or not dvi.exists():
        return die("не вижу Биржа/cartridge_registry.py или жители/dvizhok.py — "
                   "ты в КОРНЕ репы?")
    r_src = reg.read_text(encoding="utf-8")
    d_src = dvi.read_text(encoding="utf-8")
    if "MAGIC_IN_MASK_V1" not in r_src:
        return die("сначала patch_magic_v_masku_v1.py (магик в маске)")
    if "DVIZHOK_STOL_CHISTO_VYVOD_V1" not in d_src:
        return die("сначала patch_dvizhok_stol_chisto_vyvod_v1.py")
    if "DVIZHOK_YAKORYA_YADRO_V1" not in d_src:
        return die("сначала patch_dvizhok_yakorya_yadro_v1.py")
    print("✓ фундамент на месте (магик в маске, рука опыта, якоря/ядро)")

    # ── ШАГ 1: дверь ─────────────────────────────────────────────
    if not DOOR_SRC.exists():
        return die("рядом с патчем нет nositel.py — положи его в корень репы "
                   "(качается вместе с патчем)")
    if DOOR_DST.exists() and "NOSITEL_BRIDGE_V1" in DOOR_DST.read_text(encoding="utf-8"):
        print("✓ дверь Биржа/nositel.py уже стоит")
    else:
        shutil.copyfile(DOOR_SRC, DOOR_DST)
        print(f"✓ дверь поставлена: {DOOR_DST}")

    # ── ШАГ 2: мозг A07 ──────────────────────────────────────────
    if not BRAIN.exists():
        return die(f"не нашёл мозг {BRAIN}")
    b = BRAIN.read_text(encoding="utf-8")
    if MARKER_BRAIN in b:
        print("✓ мозг A07 уже пропатчен")
    else:
        for old, what in ((OLD_MAGIC, "_MY_MAGIC = 100002"),
                          (OLD_POS_FULL, "поиск своей позиции по магику"),
                          (OLD_SOUL_RUN, "мёртвая душа в run_avan"),
                          (OLD_SOUL_CHAT, "мёртвая душа в chat_with_avan")):
            if old not in b:
                return die(f"мозг A07: не нашёл блок «{what}». "
                           "Файл правился вручную? Сверь глазами.", 3)
        bak = BRAIN.with_suffix(".py.bak")
        if not bak.exists():
            bak.write_text(b, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        b = b.replace(OLD_MAGIC, NEW_MAGIC, 1)
        b = b.replace(OLD_POS_FULL, NEW_POS_FULL, 1)
        b = b.replace(OLD_SOUL_RUN, NEW_SOUL_RUN, 1)
        b = b.replace(OLD_SOUL_CHAT, NEW_SOUL_CHAT, 1)
        BRAIN.write_text(b, encoding="utf-8")
        print("✓ мозг A07: читающий конец → Илья; магик из маски; "
              "два мёртвых импорта studio.* вырезаны")

    # ── ШАГ 3: hooks ─────────────────────────────────────────────
    if not HOOKS.exists():
        return die(f"не нашёл {HOOKS}")
    h = HOOKS.read_text(encoding="utf-8")
    if MARKER_HOOKS in h:
        print("✓ hooks уже пропатчен (нога Опыта стоит)")
    else:
        if OLD_JUDGE not in h:
            return die("hooks: не нашёл заглушку _judge_trader_by_result "
                       "в ожидаемом виде. Сверь глазами.", 4)
        bak = HOOKS.with_suffix(".py.bak")
        if not bak.exists():
            bak.write_text(h, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        h = h.replace(OLD_JUDGE, NEW_JUDGE, 1)
        HOOKS.write_text(h, encoding="utf-8")
        print("✓ hooks: _judge_trader_by_result → нога Опыта (magic → носитель)")

    print("───")
    print("КОЛЬЦО ЗАМКНУТО НА ИЛЬЕ:")
    print("  читает свою душу перед сделкой (мозг → nositel → его якоря)")
    print("  дописывает вывод после сделки (hooks → magic → его же якоря)")
    print("\nПроверка:  python proverka_koltsa.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
