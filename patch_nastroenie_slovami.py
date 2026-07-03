# patch_nastroenie_slovami.py
"""
Очистка: заряд → настроение словами, рудимент «открытых слоёв» — вон.

Что было не так (увидел Шеф):
  1. Заряд уходил в душу голым числом с инструкцией-расшифровкой —
     работало, но LLM держит тон по словам лучше, чем по числу.
  2. Строка «Тебе открыты слои памяти: ...» осталась от замысла
     «заряд открывает слои», который так и не стал реальным чтением,
     а после камня MEMORY_REQUEST (воля жителя, подъём безусловный)
     начала ВРАТЬ: внушала LLM ложную границу, будто дальше
     «открытых» слоёв лезть нельзя. Декорация — вон.

После патча в душу вместо числа и списка слоёв идёт одна строка
настроения, посчитанная из того же заряда:
     заряд >  0.55  → «тебе тепло и светло, на подъёме»
     заряд >  0.2   → «тебе спокойно-хорошо, лёгкая теплота»
     |заряд| <= 0.2 → «ты ровно, в покое»
     заряд > -0.55  → «тебе неспокойно — что-то задело»
     иначе          → «тебе тяжело, ты на взводе»

Сам расчёт слоёв в dvizhok.py НЕ трогается — лежит швом на будущее
(если сильное чувство однажды само будет выбрасывать воспоминание).
Патчится только подача в душу (ui_zhitel.py).

Запуск из КОРНЯ репо:
    python patch_nastroenie_slovami.py

Идемпотентен. Бэкап: жители/ui_zhitel.py.bak_nastroenie
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "жители" / "ui_zhitel.py"
MARKER = "PATCH_NASTROENIE_SLOVAMI"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    # ── 1. хелпер настроения на уровне модуля (рядом с _ubrat_memory_request) ──
    anchor_helper = (
        'def _ubrat_memory_request(text: str) -> str:\n'
        '    """PATCH_ZHITEL_VSPOMINAET: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""\n'
        '    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]\n'
        '    return "\\n".join(lines).strip()\n'
    )
    if anchor_helper not in src:
        print("✗ не нашёл _ubrat_memory_request — сначала накати patch_zhitel_vspominaet.py")
        return

    helper = (
        anchor_helper +
        '\n'
        '\n'
        f'def _nastroenie_slovami(zaryad: float) -> str:\n'
        f'    """{MARKER}: заряд движка → настроение живыми словами.\n'
        '    LLM держит тон по словам лучше, чем по голому числу с инструкцией."""\n'
        '    try:\n'
        '        z = float(zaryad)\n'
        '    except Exception:\n'
        '        z = 0.0\n'
        '    if z > 0.55:\n'
        '        return "тебе тепло и светло, ты на подъёме"\n'
        '    if z > 0.2:\n'
        '        return "тебе спокойно-хорошо, лёгкая теплота"\n'
        '    if z >= -0.2:\n'
        '        return "ты ровно, в покое"\n'
        '    if z >= -0.55:\n'
        '        return "тебе неспокойно — что-то задело"\n'
        '    return "тебе тяжело, ты на взводе"\n'
    )
    src = src.replace(anchor_helper, helper, 1)

    # ── 2. подача в душу: число+слои → одна строка настроения ──
    anchor_soul = (
        '            soul += (\n'
        '                f"Сейчас твой заряд (внутреннее состояние): {stol[\'заряд\']} "\n'
        '                f"(от -1 до 1; отрицательный — тревога/обида, положительный — тепло/радость, "\n'
        '                f"0 — покой).\\n"\n'
        '                f"Тебе открыты слои памяти: {\', \'.join(stol[\'открыто\'])}.\\n"\n'
        '                f"Отвечай коротко, по-человечески, исходя из своей личности выше и текущего "\n'
        '                f"заряда — не упоминай слова \'заряд\' или \'слои\' напрямую, просто веди себя в тон."\n'
        '            )\n'
    )
    if anchor_soul not in src:
        print("✗ не нашёл блок заряда в душе — файл изменился, откатываю")
        return

    new_soul = (
        f'            # {MARKER}: настроение словами вместо голого числа.\n'
        '            # Строка «открыты слои» убрана: после MEMORY_REQUEST подъём\n'
        '            # безусловный, список слоёв внушал LLM ложную границу.\n'
        '            soul += (\n'
        '                f"Сейчас твоё настроение: {_nastroenie_slovami(stol[\'заряд\'])}.\\n"\n'
        '                f"Отвечай коротко, по-человечески, исходя из своей личности выше и "\n'
        '                f"настроения — не называй его прямо, просто веди себя в тон."\n'
        '            )\n'
    )
    src = src.replace(anchor_soul, new_soul, 1)

    # ── бэкап + запись ──
    backup = TARGET.with_name(TARGET.name + ".bak_nastroenie")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— заряд теперь идёт в душу настроением словами, слои из души убраны.")
    print("— проверь: python main.py → /zhitel/{id} → тон ответов по настроению")


if __name__ == "__main__":
    main()
