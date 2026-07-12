# -*- coding: utf-8 -*-
"""
patch_klon_dushi_v2.py
────────────────────────────────────────────────────────────────────
КЛОН ЧИТАЮЩЕГО КОНЦА — v2. ЧИНИТ ТО, ЧТО v1 НЕ СМОГ.

v1 положил восемь мозгов, но СПОТКНУЛСЯ НА ИСКРЕ (A01): у неё вызов
chat() многострочный и с ВИСЯЧЕЙ ЗАПЯТОЙ — вставка температуры дала
SyntaxError, и предохранитель ОТКАТИЛ файл (сработал честно, не молча).
v2 чинит вставку. Уже подключённые мозги он не трогает — возьмёт только
A01 (и любой другой, что v1 откатил).

Эталон отлажен на Илье (A07): душа носителя в промпт + натура в
температуру + магик из маски. Прогон 12.07 показал, что он работает —
Авантюрист впервые сказал «опираюсь на свои же якоря». Клоним форму.

ПОЧЕМУ СЕЙЧАС, А НЕ ПОСЛЕ УЧЁБЫ (довод из кода, не из вкуса):
  пишущий конец УЖЕ общий — hooks._judge_trader_by_result судит по магику,
  а магики стоят у ВСЕХ ТРЁХ трейдеров (100001/2/3). Нажми Шеф «УЧИТЬ»
  сейчас — рынок начнёт писать выводы в паспорта Брута и Василия, а они
  этих выводов НЕ ЧИТАЮТ: душа мёртвая. Опыт копился бы в людях, которые
  его не видят. Поэтому сначала цепочка, потом жизнь.

ЧТО ДЕЛАЕТ С КАЖДЫМ МОЗГОМ (кроме A07 — он уже эталон):
  1. МЁРТВАЯ ДУША → ЖИВОЙ НОСИТЕЛЬ.
     Было:  from studio.grondheim_memory import format_soul_for_agent
            soul = format_soul_for_agent("A06_BRUT", dept="trading")
            → studio/ снесена, импорт падал ВСЕГДА (лог: «Душа не
              загрузилась (No module named 'studio')») — все работали голыми.
     Стало: nositel.dusha_slota(цех, слот) → носитель по МАСКЕ (Закон Пары).
            Пара берётся ИЗ ПУТИ мозга — ни одного хардкода личности.
            Контора не ломается: её слоты зовутся «архивариус»/«исполнитель»,
            а не A05/A09 — путь знает правду, выдумка не нужна.
  2. НАТУРА → ТЕМПЕРАТУРА. В chat() добавляется temperature из заряда и
     натуры носителя (stress_to_temperature была мёртвой — никто не звал).
  3. МАГИК ИЗ МАСКИ (только у трейдеров A06/A08): константа _MY_MAGIC
     убивается, магик берётся из маски — единственной правды.

ЧЕГО НЕ ДЕЛАЕТ (сознательно):
  • ПИШУЩИЙ конец сенсоров. У трейдера судья — рынок и R. А что рынок
    должен записать в паспорт МОРЖУ, который не торгует? Это решение
    Шефа, не механика. Их sync_to_dna остаётся мёртвым до разговора.
  • Порядок «Род впереди маски» и «сверку с опытом» — это правки ТЕКСТА
    задачи, у каждой роли свой. Сделаем прицельно, увидев, как заговорят.

БЕЗОПАСНОСТЬ: каждый мозг — .bak, затем py_compile. НЕ КОМПИЛИТСЯ →
  файл откатывается из бэкапа автоматически. Молча ничего не ломаем.

Требует: patch_etalon_avana_v1 (дверь nositel.py).
Идемпотентно.  Из КОРНЯ репы:  python patch_klon_dushi_v1.py
"""
from __future__ import annotations
import io
import py_compile
import re
import sys
from pathlib import Path

MARKER = "KLON_DUSHI_V1"
CEHA = Path("GRONDHEIM_CITY") / "Биржа" / "цеха"
NOSITEL = Path("Биржа") / "nositel.py"

# ── шаблон: мёртвая душа отдельным блоком (run_*) ───────────────
RE_SOUL_RUN = re.compile(
    r'[ \t]*soul = ""\n'
    r'[ \t]*try:\n'
    r'[ \t]*from studio\.grondheim_memory import format_soul_for_agent[^\n]*\n'
    r'[ \t]*soul = format_soul_for_agent\([^\n]*\)\n'
    r'[ \t]*except Exception as e:\n'
    r'[ \t]*print\(f"\[(?P<tag>[^\]]+)\][^\n]*\)\n'
)

# ── шаблон: мёртвая душа внутри сборки system (chat_*) ──────────
RE_SOUL_CHAT = re.compile(
    r'[ \t]*try:\n'
    r'[ \t]*from studio\.grondheim_memory import format_soul_for_agent[^\n]*\n'
    r'[ \t]*soul = format_soul_for_agent\([^\n]*\)\n'
    r'[ \t]*if soul:\n'
    r'[ \t]*system = [^\n]*\n'
    r'[ \t]*except Exception:\n'
    r'[ \t]*pass\n'
)

# ── шаблон: константа магика ────────────────────────────────────
RE_MAGIC = re.compile(r'^_MY_MAGIC = (\d+)[^\n]*\n', re.M)
RE_MAGIC_USE = re.compile(r'== _MY_MAGIC\b')

# ── шаблон: вызов chat( ... ) без temperature ───────────────────
RE_CHAT = re.compile(
    r'(chat\((?:[^()]|\([^()]*\))*?)\)',
    re.S)


def soul_run_block(indent: str, tag: str) -> str:
    i = indent
    return (
        f'{i}# {MARKER}: ДУША — от НОСИТЕЛЯ (маска, Закон Пары), не от трупа из -2.\n'
        f'{i}# Было: format_soul_for_agent из снесённой studio/ — падало ВСЕГДА\n'
        f'{i}# («No module named studio»), работали голыми. Пара — ИЗ ПУТИ мозга.\n'
        f'{i}soul = ""\n'
        f'{i}try:\n'
        f'{i}    from nositel import dusha_slota\n'
        f'{i}    _n = dusha_slota(_CEH, _SLOT)\n'
        f'{i}    if _n:\n'
        f'{i}        soul = _n["душа"]\n'
        f'{i}        print(f"[{tag}] 🧬 За столом: {{_n[\'носитель\'][\'имя\']}}")\n'
        f'{i}except Exception as e:\n'
        f'{i}    print(f"[{tag}] ⚠️  Носитель не поднялся ({{e}}) — работаю без души")\n'
    )


def soul_chat_block(indent: str) -> str:
    i = indent
    return (
        f'{i}try:   # {MARKER}: и в разговоре — ОН, не роль\n'
        f'{i}    from nositel import dusha_slota\n'
        f'{i}    _n = dusha_slota(_CEH, _SLOT)\n'
        f'{i}    if _n and _n["душа"]:\n'
        f'{i}        system = (prompt + "\\n\\n=== КТО ТЫ (душа носителя) ===\\n"\n'
        f'{i}                  + _n["душа"] + "\\n\\n" + work_ctx)\n'
        f'{i}except Exception:\n'
        f'{i}    pass\n'
    )


def magic_block(old_val: str) -> str:
    return (
        f'# {MARKER}: магик — из МАСКИ носителя (Закон Пары), не константой.\n'
        f'# Было: _MY_MAGIC = {old_val} — ещё одна копия правды. Их было пять.\n'
        f'def _my_magic():\n'
        f'    """Магик ТОГО, кто сидит в этом слоте. Нет носителя → None."""\n'
        f'    try:\n'
        f'        from nositel import magic_slota\n'
        f'        return magic_slota(_CEH, _SLOT)\n'
        f'    except Exception:\n'
        f'        return None\n'
    )


PARA_BLOCK = (
    f'\n# {MARKER}: пара (цех, слот) — ИЗ ПУТИ мозга, без хардкода личности.\n'
    f'# Контора не ломается: её слоты зовутся «архивариус»/«исполнитель».\n'
    f'_CEH  = _CEH_DIR.name\n'
    f'_SLOT = _SLOT_DIR.name\n'
)

TEMP_BLOCK = (
    '\n\ndef _my_temp():\n'
    f'    """{MARKER}: натура и состояние носителя → температура головы.\n'
    '    stress_to_temperature() в llm.py была МЁРТВОЙ — никто не передавал\n'
    '    temperature, все думали на дефолте. Натура была буквами в промпте.\n'
    '    None → дефолт модели (носителя нет — ничего не ломаем)."""\n'
    '    try:\n'
    '        from nositel import temperatura_slota\n'
    '        return temperatura_slota(_CEH, _SLOT)\n'
    '    except Exception:\n'
    '        return None\n'
)


def patch_brain(path: Path) -> str:
    """Возвращает строку отчёта по одному мозгу."""
    ceh = path.parents[2].name
    slot = path.parent.name
    who = f"{ceh}/{slot}"

    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        return f"  ✓ {who}: уже пропатчен"
    # УНИВЕРСАЛЬНАЯ ЗАЩИТА: мозг, который уже ходит в мост, не трогаем —
    # не по маркеру (маркеры бывают разные), а по факту. Так эталон A07 и
    # любой вручную подключённый мозг застрахованы от второго слоя правок.
    if "from nositel import" in src or "_CEH " in src or "_CEH=" in src:
        return f"  ✓ {who}: уже подключён к мосту — не трогаю"

    if "_SLOT_DIR" not in src or "_CEH_DIR" not in src:
        return (f"  ⚠ {who}: нет _SLOT_DIR/_CEH_DIR — шасси другое, "
                f"пропускаю (сверь глазами)")

    orig = src
    changes = []

    # 1) пара из пути — вставляем после блока путей
    anchor = re.search(r'^_BIRZHA_CODE\s*=[^\n]*\n', src, re.M)
    if not anchor:
        anchor = re.search(r'^_CEH_DIR\s*=[^\n]*\n', src, re.M)
    if not anchor:
        return f"  ⚠ {who}: не нашёл, куда вписать пару — пропускаю"
    src = src[:anchor.end()] + PARA_BLOCK + src[anchor.end():]
    changes.append("пара из пути")

    # 2) душа (run)
    m = RE_SOUL_RUN.search(src)
    if m:
        indent = re.match(r'[ \t]*', m.group(0)).group(0)
        src = src[:m.start()] + soul_run_block(indent, m.group("tag")) + src[m.end():]
        changes.append("душа→носитель")

    # 3) душа (chat)
    m2 = RE_SOUL_CHAT.search(src)
    if m2:
        indent = re.match(r'[ \t]*', m2.group(0)).group(0)
        src = src[:m2.start()] + soul_chat_block(indent) + src[m2.end():]
        changes.append("душа в разговоре")

    if not m and not m2:
        changes.append("мёртвой души не нашёл")

    # 4) магик из маски (только там, где он был)
    mm = RE_MAGIC.search(src)
    if mm:
        src = RE_MAGIC.sub(magic_block(mm.group(1)), src, count=1)
        src = RE_MAGIC_USE.sub('== _magic', src)
        # в функции, где используется _magic — поднять его
        src = src.replace(
            "    mine = None\n    for p in positions:",
            "    mine = None\n    _magic = _my_magic()   # " + MARKER + "\n"
            "    if _magic is None:\n        return None\n    for p in positions:",
            1)
        changes.append(f"магик {mm.group(1)}→маска")

    # 5) температура: добавить _my_temp() и передать в chat()
    src += TEMP_BLOCK
    n_chat = 0

    def add_temp(mo):
        nonlocal n_chat
        call = mo.group(1)
        if "temperature" in call:
            return mo.group(0)
        n_chat += 1
        # KLON_V2: у Искры (A01) вызов МНОГОСТРОЧНЫЙ и с ВИСЯЧЕЙ ЗАПЯТОЙ:
        #     chat(
        #         slot_id="trading",     ← запятая
        #     )
        # v1 лепил ", temperature=..." после неё → «, tempera» с новой строки →
        # SyntaxError → предохранитель откатил файл (сработал честно).
        # Теперь: подчищаем хвост и висячую запятую перед вставкой.
        tail = call.rstrip()
        if tail.endswith(","):
            return tail + " temperature=_my_temp())"
        return tail + ", temperature=_my_temp())"

    src = RE_CHAT.sub(add_temp, src)
    if n_chat:
        changes.append(f"температура в {n_chat} вызов(а) chat")

    # ── запись + компиляция, откат при поломке ──────────────────
    bak = path.with_suffix(".py.bak_klon")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
    path.write_text(src, encoding="utf-8")
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        path.write_text(orig, encoding="utf-8")
        return f"  ✗ {who}: НЕ КОМПИЛИТСЯ — откатил. ({str(e)[:90]})"

    return f"  ✓ {who}: " + ", ".join(changes)


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ КЛОН ДУШИ — восемь мозгов садятся за стол собой ═══")

    if not NOSITEL.exists():
        print("✗ нет Биржа/nositel.py — сначала patch_etalon_avana_v1.py")
        return 1
    if "NATURA_V_TEMPERATURU_V1" not in NOSITEL.read_text(encoding="utf-8"):
        print("✗ сначала patch_natura_v_temperaturu_v1.py "
              "(без него temperatura_slota нет)")
        return 2
    if not CEHA.exists():
        print(f"✗ не нашёл {CEHA} — ты в КОРНЕ репы?")
        return 3

    brains = sorted(CEHA.glob("*/слоты/*/мозг.py"))
    if not brains:
        print("✗ мозгов не нашёл — структура другая?")
        return 4

    print(f"мозгов на Бирже: {len(brains)}\n")
    for b in brains:
        print(patch_brain(b))

    print("\n───")
    print("Проверка:  python proverka_soveta.py")
    print("Она покажет, КТО сидит за каждым слотом и с какой температурой.")
    print("\nПишущий конец сенсоров НЕ трогал: что рынок должен записать")
    print("Моржу, который не торгует? Это твоё решение, не механика.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
