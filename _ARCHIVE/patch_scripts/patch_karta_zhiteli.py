# -*- coding: utf-8 -*-
"""
PATCH: КАРТА · ТОЧКИ ЖИТЕЛЕЙ — ui_grondheim.py учится рисовать жителей.
Маркер: KARTA_ZHITELI_V1

ЗАМЫСЕЛ ШЕФА (переворот, уже воплощённый в sostoyanie.py): карта не
вычисляет, где житель. Житель сам держит своё место (state.json /
прописка). Карта тупо зовёт gde_ya() и светит точку. Никакого
_find_agent_zone, никакого fuzzy, никаких приоритетов внутри карты.

ЧТО ДЕЛАЕТ ПАТЧ (текстовые правки существующего файла, не переписывает
с нуля — риск ниже, дифф на виду):

  1. Добавляет load_zhiteli() — сканирует дома жителей, для каждого
     зовёт sostoyanie.gde_ya(дом). Бездомных (локация=None) не рисует —
     ставить некуда, это честно, не выдумка.
  2. Добавляет CSS для точки (.grond-zhitel / .grond-zhitel--active —
     активная светится и пульсирует: явный штамп места отличим от
     дефолтного «дома»).
  3. _canvas_html() принимает жителей, раскладывает точки СЕТКОЙ внутри
     прямоугольника их локации (простая раскладка, без наворотов —
     как в -2 zone_counters, но проще).
  4. render() зовёт load_zhiteli() и передаёт в _canvas_html().

Идемпотентен: если "load_zhiteli" уже есть в файле — патч не трогает
файл (уже накатан). Иначе — падает громко, если якорь не найден
(значит файл изменился не так, как я ожидал — лучше остановиться,
чем тихо испортить).

Запуск из корня репо:  python patch_karta_zhiteli.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "ГОРОД" / "ui_grondheim.py"
MARKER = "KARTA_ZHITELI_V1"

# ═══════════════════════════════════════════════════════════════
# Вставки (анкеры — точные строки из живого файла, сверено byte-в-byte)
# ═══════════════════════════════════════════════════════════════

ANCHOR_1 = 'GRONDHEIM_CSS = r"""'

INSERT_1 = '''def load_zhiteli() -> list:
    """Скан домов жителей -> список для карты: кто, где сейчас, как.

    ЗАКОН (замысел Шефа): карта НЕ вычисляет место — житель сам его
    держит (sostoyanie.gde_ya). Бездомных (локация=None, нет прописки
    и не в сессии) не рисуем — ставить некуда, это честно.
    """
    import json as _json
    root = Path("GRONDHEIM_CITY/жители")
    out = []
    if not root.exists():
        return out
    _repo = Path(__file__).resolve().parent.parent
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    try:
        import sostoyanie as sost
    except Exception:
        return out  # состояния ещё нет — карта честно рисует только здания
    for passport_path in sorted(root.glob("*/*/passport.json")):
        dom = passport_path.parent
        try:
            p = _json.loads(passport_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        r = sost.gde_ya(dom)
        loc = r.get("локация")
        if not loc:
            continue  # бездомный — ставить некуда
        out.append({
            "id": p.get("ID_Object", dom.name),
            "имя": p.get("Official_Name", dom.name),
            "локация": loc,
            "дома": r.get("дома", True),
        })
    return out


'''

ANCHOR_2 = '''.grond-empty{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-size: 0.85rem; color: rgba(255,255,255,0.5);
  letter-spacing: 0.06em; text-align: center; pointer-events: none; z-index: 5;
}
"""'''

INSERT_2 = '''.grond-empty{
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-size: 0.85rem; color: rgba(255,255,255,0.5);
  letter-spacing: 0.06em; text-align: center; pointer-events: none; z-index: 5;
}

.grond-zhitel{
  position: absolute; border-radius: 50%; z-index: 3; box-sizing: border-box;
  background: radial-gradient(circle, rgba(201,168,76,0.55), rgba(201,168,76,0.12));
  border: 1px solid rgba(201,168,76,0.5);
}
.grond-zhitel--active{
  position: absolute; border-radius: 50%; z-index: 4; box-sizing: border-box;
  background: radial-gradient(circle, rgba(0,220,240,0.9), rgba(0,140,160,0.3));
  border: 1px solid rgba(0,220,240,0.9);
  box-shadow: 0 0 10px rgba(0,220,240,0.55);
  animation: grondPulse 1.6s ease-in-out infinite;
}
@keyframes grondPulse{
  0%,100%{ transform: scale(1); }
  50%{ transform: scale(1.3); }
}
"""'''

ANCHOR_3 = '''def _canvas_html(locations: list) -> str:
    sectors = ""
    for loc in locations:
        sectors += (
            '<div class="grond-sector" onclick="window.grondOpen && window.grondOpen(\\'%s\\')" '
            'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;">%s</div>'
            % (_esc(loc["id"]), loc["x"], loc["y"], loc["w"], loc["h"], _esc(loc["name"]))
        )
    empty = ""
    if not locations:
        empty = ('<div class="grond-empty">Локаций пока нет.<br>'
                 'Роди их в Странице Жизни — появятся на карте.</div>')
    return (
        '<div class="grond-canvas" style="width:%dpx;height:%dpx;'
        'background-image:url(\\'%s\\');background-size:%dpx %dpx;">%s</div>%s'
        % (CITY_W, CITY_H, CITY_IMAGE, CITY_W, CITY_H, sectors, empty)
    )'''

INSERT_3 = '''def _tochki_zhitelej_html(locations: list, zhiteli: list) -> str:
    """Точки жителей — раскладка сеткой внутри прямоугольника ИХ
    локации. Не вычисляем зону — локация уже дана житилем (gde_ya)."""
    by_loc = {}
    for z in zhiteli:
        by_loc.setdefault(z["локация"], []).append(z)
    dot, gap, pad = 13, 4, 6
    points = ""
    for loc in locations:
        residents = by_loc.get(loc["id"], [])
        if not residents:
            continue
        per_row = max(1, (loc["w"] - 2 * pad) // (dot + gap))
        for i, z in enumerate(residents):
            row, col = divmod(i, per_row)
            px = loc["x"] + pad + col * (dot + gap)
            py = loc["y"] + pad + row * (dot + gap)
            cls = "grond-zhitel" if z["дома"] else "grond-zhitel--active"
            title = _esc(z["имя"] + (" · дома" if z["дома"] else " · на месте"))
            points += (
                '<div class="%s" title="%s" '
                'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;"></div>'
                % (cls, title, px, py, dot, dot)
            )
    return points


def _canvas_html(locations: list, zhiteli: list = None) -> str:
    zhiteli = zhiteli or []
    sectors = ""
    for loc in locations:
        sectors += (
            '<div class="grond-sector" onclick="window.grondOpen && window.grondOpen(\\'%s\\')" '
            'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;">%s</div>'
            % (_esc(loc["id"]), loc["x"], loc["y"], loc["w"], loc["h"], _esc(loc["name"]))
        )
    points = _tochki_zhitelej_html(locations, zhiteli)
    empty = ""
    if not locations:
        empty = ('<div class="grond-empty">Локаций пока нет.<br>'
                 'Роди их в Странице Жизни — появятся на карте.</div>')
    return (
        '<div class="grond-canvas" style="width:%dpx;height:%dpx;'
        'background-image:url(\\'%s\\');background-size:%dpx %dpx;">%s%s</div>%s'
        % (CITY_W, CITY_H, CITY_IMAGE, CITY_W, CITY_H, sectors, points, empty)
    )'''

ANCHOR_4 = '''    def render():
        root_ref["el"].clear()
        locations = load_locations()
        with root_ref["el"]:
            with ui.element("div").classes("grond-header"):
                ui.html(
                    f'<div><div class="grond-title">ГРОНДХЕЙМ</div>'
                    f'<div class="grond-sub">зрение Брата · {len(locations)} локаций</div></div>'
                )
                ui.button("← назад", on_click=lambda: ui.navigate.to("/brat")) \\
                    .props("flat").classes("grond-back")

            with ui.element("div").classes("grond-viewport"):
                ui.html(_canvas_html(locations))'''

INSERT_4 = '''    def render():
        root_ref["el"].clear()
        locations = load_locations()
        zhiteli = load_zhiteli()
        with root_ref["el"]:
            with ui.element("div").classes("grond-header"):
                ui.html(
                    f'<div><div class="grond-title">ГРОНДХЕЙМ</div>'
                    f'<div class="grond-sub">зрение Брата · {len(locations)} локаций'
                    f'{f" · {len(zhiteli)} на карте" if zhiteli else ""}</div></div>'
                )
                ui.button("← назад", on_click=lambda: ui.navigate.to("/brat")) \\
                    .props("flat").classes("grond-back")

            with ui.element("div").classes("grond-viewport"):
                ui.html(_canvas_html(locations, zhiteli))'''


def install():
    print(f"═══ PATCH {MARKER} — точки жителей на карте ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "load_zhiteli" in src:
        print(f"  ○ уже накатано — {TARGET.relative_to(REPO)} содержит load_zhiteli")
        print("═══ ничего не менял ═══")
        return True

    for name, anchor in (("ANCHOR_1", ANCHOR_1), ("ANCHOR_2", ANCHOR_2),
                        ("ANCHOR_3", ANCHOR_3), ("ANCHOR_4", ANCHOR_4)):
        if anchor not in src:
            print(f"  ✖ {name} не найден в файле — файл изменился, "
                  f"останавливаюсь, чтобы не испортить. Покажи мне текущий "
                  f"ui_grondheim.py заново.")
            return False

    src = src.replace(ANCHOR_1, INSERT_1 + ANCHOR_1)
    src = src.replace(ANCHOR_2, INSERT_2)
    src = src.replace(ANCHOR_3, INSERT_3)
    src = src.replace(ANCHOR_4, INSERT_4)

    # sys уже импортируется в load_zhiteli через sys.path — нужен import sys
    if "\nimport sys\n" not in src and "import sys\n" not in src.split("\n\n")[0]:
        src = src.replace("import json\nfrom pathlib import Path\nfrom nicegui import ui",
                          "import json\nimport sys\nfrom pathlib import Path\nfrom nicegui import ui")

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ после правки: {e}")
        return False
    print("  ✔ синтаксис после правки — чистый (ast.parse)")

    TARGET.write_text(src, encoding="utf-8")
    print(f"  ✔ обновлён: {TARGET.relative_to(REPO)}")

    print("\n═══ ИТОГ ═══")
    print("  ✔ load_zhiteli() — читает gde_ya(), не вычисляет зону")
    print("  ✔ CSS .grond-zhitel / .grond-zhitel--active (активная пульсирует)")
    print("  ✔ _canvas_html() рисует точки внутри прямоугольника локации")
    print("  ✔ render() зовёт load_zhiteli(), передаёт в canvas")
    print("\n  Открой /grondheim в браузере — жители, у кого есть локация")
    print("  (прописка или активный штамп сессии), встанут точками.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
