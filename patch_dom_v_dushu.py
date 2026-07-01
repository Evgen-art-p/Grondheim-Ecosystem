# patch_dom_v_dushu.py
"""
Камень четвёртый, последний в цепочке прописки: домашний промпт — в душу.

До патча: стол (vydoh_stol) несёт кто_я/ядро/историю/чувство/якоря/
скрытый_вкус/тянет_к/натуру — ВСЕГДА, при любом заряде (это не память,
это личность). Дом в этот список не входил вообще: даже прописанный
житель с заполненным "домашний_промпт" в паспорте не понёс бы дом в
разговор — движок его не подавал.

После патча: "дом" ложится на стол рядом с остальными якорями, тем же
принципом — не по |заряду|, не как слой памяти, а как часть личности,
которая носится в себе ВСЕГДА (Закон §2.4 Летописи: "где бы он ни
был — не должен себя забывать... помнить, что есть дом"). Пусто, если
ещё не прописан(а) — пустые поля пропускаются (YAKORYA_V_SOUL_V1),
чтобы не раздувать промпт декорацией без содержания.

Патчит два файла:
  1. жители/dvizhok.py       — vydoh_stol() кладёт "дом" на стол.
  2. жители/ui_zhitel.py     — send() вплетает "дом" в душу LLM.

Запуск из КОРНЯ репо:
    python patch_dom_v_dushu.py

Идемпотентен по каждому файлу отдельно (если один уже пропатчен, а
другой нет — довешивает только недостающее).

Бэкапы: жители/dvizhok.py.bak_dom_v_dushu, жители/ui_zhitel.py.bak_dom_v_dushu
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
MARKER = "PATCH_DOM_V_DUSHU"


def patch_dvizhok():
    target = _ROOT / "жители" / "dvizhok.py"
    if not target.exists():
        print(f"✗ не найден: {target}")
        return False

    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"— dvizhok.py: уже применён — пропускаю")
        return True

    anchor = (
        '            "тянет_к":        self.p.get("Pull_Vector", ""),\n'
        '            "натура":         self.p.get("DNA_Static", {}),\n'
        '        }\n'
    )
    if anchor not in src:
        print("✗ dvizhok.py: не нашёл конец vydoh_stol() — файл изменился, откатываю")
        return False

    new = (
        '            "тянет_к":        self.p.get("Pull_Vector", ""),\n'
        f'            # {MARKER}: дом — носится в себе ВСЕГДА, не по заряду\n'
        '            # (часть личности, не слой памяти). Пусто, если ещё не\n'
        '            # прописан(а) — стол пропустит пустое поле сам.\n'
        '            "дом":            self.p.get("домашний_промпт", ""),\n'
        '            "натура":         self.p.get("DNA_Static", {}),\n'
        '        }\n'
    )
    src = src.replace(anchor, new, 1)

    backup = target.with_name(target.name + ".bak_dom_v_dushu")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(src, encoding="utf-8")
    print(f"✓ dvizhok.py применён, бэкап: {backup.name}")
    return True


def patch_ui_zhitel():
    target = _ROOT / "жители" / "ui_zhitel.py"
    if not target.exists():
        print(f"✗ не найден: {target}")
        return False

    src = target.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"— ui_zhitel.py: уже применён — пропускаю")
        return True

    anchor = (
        "            if stol.get('тянет_к'):\n"
        "                soul += f\"Тебя тянет к: {stol['тянет_к']}\\n\"\n"
        "            if stol.get('натура'):\n"
    )
    if anchor not in src:
        print("✗ ui_zhitel.py: не нашёл блок якорей в send() — файл изменился, откатываю")
        return False

    new = (
        "            if stol.get('тянет_к'):\n"
        "                soul += f\"Тебя тянет к: {stol['тянет_к']}\\n\"\n"
        f"            if stol.get('дом'):  # {MARKER}: дом несёшь в себе ВСЕГДА\n"
        "                soul += f\"Твой дом, который ты носишь в себе всегда: {stol['дом']}\\n\"\n"
        "            if stol.get('натура'):\n"
    )
    src = src.replace(anchor, new, 1)

    backup = target.with_name(target.name + ".bak_dom_v_dushu")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(src, encoding="utf-8")
    print(f"✓ ui_zhitel.py применён, бэкап: {backup.name}")
    return True


def main():
    ok1 = patch_dvizhok()
    ok2 = patch_ui_zhitel()
    if ok1 and ok2:
        print("\n— дом теперь на столе рядом с якорями, при любом заряде.")
        print("— проверь: python main.py → /zhitel/001_GENESIS_LOKA → скажи что-нибудь Локе")


if __name__ == "__main__":
    main()
