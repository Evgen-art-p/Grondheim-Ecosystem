# -*- coding: utf-8 -*-
"""
PATCH: ui_registry · ЧЕСТНЫЕ ТИПЫ + НАСТОЯЩИЙ БАГ.
Маркер: REGISTRY_TYPES_HONEST_V1

49 ошибок Pylance разобраны на группы:

  ГРУППА 1 (29 штук, regex): те же {"w": None} / {"el": None} виджеты,
  что чинили в ui_zhitel и ui_brat — только тут их 29, не 3. Правится
  ОДНИМ регулярным выражением, не построчно — надёжнее для такого
  количества одинаковых мест.

  ГРУППА 2 (14 штук): obj = {...} в collect_form() — словарь стартует
  строковыми значениями, pyright решает "тут всегда str", потом
  спотыкается на obj["DNA_Static"]=dict, obj["Map_X"]=int, obj["Tags"]=
  list. Та же болезнь, что Группа 1, другая форма (не виджет, а
  собираемый объект). Один: dict.

  ГРУППА 3 (4 штуки): catalog_container/json_container/stats_label/
  image_preview_container = None в начале функции, реальный тип
  назначается позже. Аннотация Any снимает конфликт честно (тип
  реально "определится позже", не выдумываем узкий тип заранее).

  НАСТОЯЩИЙ БАГ (не типы!) — проверено экспериментом на живом nicegui:
  `ui.element("pre")` — это ОБЩИЙ Element, у него физически НЕТ атрибута
  .text. `json_container.text = ...` не бросает ошибку (Python разрешает
  произвольные атрибуты), но НИЧЕГО не обновляет на экране — вешает
  мёртвый атрибут. Вкладка «Экспорт» в реестре, похоже, никогда не
  показывала реальный JSON. Чиню: ui.element("pre") → ui.html(""),
  который поддерживает .set_content() — работает по-настоящему.

Идемпотентен. Запуск из корня репо:  python patch_registry_types_honest.py
"""
import sys
import io
import re
import ast
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
TARGET = REPO / "Брат" / "ui_registry.py"


def install():
    print("═══ PATCH REGISTRY_TYPES_HONEST_V1 — честные типы + баг .text ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "REGISTRY_TYPES_HONEST_V1" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    changed = False

    # ── ГРУППА 1: 29 виджетов {"w"/"el": None} — regex ──
    pattern = re.compile(r'^(\s*)(\w+) = (\{"(?:w|el)": None\})(.*)$', re.MULTILINE)
    src2, n1 = pattern.subn(r'\1\2: dict = \3\4', src)
    if n1:
        src = src2
        changed = True
    print(f"  ✔ группа 1 (виджеты): {n1} правок" if n1 else "  ○ группа 1 уже честна")

    # ── ГРУППА 2: obj = {...} в collect_form ──
    old2 = '''                    obj = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                    }'''
    new2 = '''                    obj: dict = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                    }'''
    if old2 in src:
        src = src.replace(old2, new2, 1)
        changed = True
        print("  ✔ группа 2 (obj в collect_form): 1 правка")
    elif new2 in src:
        print("  ○ группа 2 уже честна")
    else:
        print("  ✖ якорь группы 2 не найден — пропускаю (файл менялся)")

    # ── ГРУППА 3: None-переменные → Any ──
    if "from typing import Optional, Any" not in src and "from typing import Optional" in src:
        src = src.replace("from typing import Optional",
                          "from typing import Optional, Any", 1)
        changed = True

    old3 = '''    catalog_container = None
    json_container = None
    stats_label = None
    image_preview_container = None'''
    new3 = '''    catalog_container: Any = None
    json_container: Any = None
    stats_label: Any = None
    image_preview_container: Any = None'''
    if old3 in src:
        src = src.replace(old3, new3, 1)
        changed = True
        print("  ✔ группа 3 (None-переменные): 4 правки")
    elif new3 in src:
        print("  ○ группа 3 уже честна")
    else:
        print("  ✖ якорь группы 3 не найден — пропускаю (файл менялся)")

    # ── НАСТОЯЩИЙ БАГ: ui.element("pre") не поддерживает .text ──
    old4 = 'json_container = ui.element("pre").classes("reg-json w-full")'
    new4 = 'json_container = ui.html("").classes("reg-json w-full")  # REGISTRY_TYPES_HONEST_V1: element("pre") не поддерживал .text — молча не обновлял экран'
    if old4 in src:
        src = src.replace(old4, new4, 1)
        changed = True
        print("  ✔ баг .text (создание): исправлено")
    elif 'ui.html("").classes("reg-json w-full")' in src:
        print("  ○ баг .text (создание) уже починен")
    else:
        print("  ✖ якорь бага .text (создание) не найден — пропускаю")

    old5 = '''                    json_container.text = json.dumps(clean, ensure_ascii=False, indent=2) if clean else "// Каталог пуст"'''
    new5 = '''                    _json_txt = json.dumps(clean, ensure_ascii=False, indent=2) if clean else "// Каталог пуст"
                    _json_esc = _json_txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    json_container.set_content(_json_esc)  # REGISTRY_TYPES_HONEST_V1: set_content реально обновляет экран'''
    if old5 in src:
        src = src.replace(old5, new5, 1)
        changed = True
        print("  ✔ баг .text (обновление): исправлено")
    elif "json_container.set_content(_json_esc)" in src:
        print("  ○ баг .text (обновление) уже починен")
    else:
        print("  ✖ якорь бага .text (обновление) не найден — пропускаю")

    if not changed:
        print("  ○ нечего менять")
        return True

    src += "\n# REGISTRY_TYPES_HONEST_V1 — маркер идемпотентности\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ синтаксис чист")
    print("\n  Проверь: pyright Брат/ui_registry.py")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
