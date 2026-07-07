# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · КАРТА ЛОКАЦИЙ + БОЛЬШАЯ ПЛАШКА ЛОКАЦИИ.
Маркер: ZHITEL_KARTA_BIG_LOC_V1

Две правки по слову Шефа:

  1. КНОПКА "карта" вела на /karta (старое дерево-иерархия). Шеф хочет
     карту ЛОКАЦИЙ (прямоугольники + точки жителей) — это /grondheim.
     Меняем адрес кнопки.

  2. ПЛАШКА ЛОКАЦИИ слева была горизонтальной (мелкая миниатюра 52px +
     текст сбоку). Шеф хочет БОЛЬШОЙ квадрат по ширине панели, подписи
     ВНИЗУ. Перестраиваем CSS: вертикаль, картинка на всю ширину
     (aspect-ratio 1/1 — квадрат), заголовок+подпись снизу.

Требует: patch_zhitel_loc_vlevo.py (плашка уже слева).
Идемпотентен: маркер ZHITEL_KARTA_BIG_LOC в файле → не трогаем.

Запуск из корня репо:  python patch_zhitel_karta_big.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "жители" / "ui_zhitel.py"

# ── 1. Кнопка карта: /karta → /grondheim ──
KNOPKA_OLD = '''                ui.button("карта", on_click=lambda: ui.navigate.to("/karta")) \\
                    .props("flat no-caps").classes("zback").style("margin-right:8px;")'''
KNOPKA_NEW = '''                ui.button("карта", on_click=lambda: ui.navigate.to("/grondheim")) \\
                    .props("flat no-caps").classes("zback").style("margin-right:8px;")'''

# ── 2. CSS плашки: горизонталь → большой квадрат, подписи внизу ──
CSS_OLD = '''.zloc-strip{ flex-shrink:0; display:flex; gap:10px; align-items:center;
  padding:8px; border-radius:14px; border:1px solid rgba(255,255,255,0.08);
  background:rgba(255,255,255,0.03); }
.zloc-thumb{ width:52px; height:52px; border-radius:10px; flex-shrink:0;
  background-size:cover; background-position:center;
  border:1px solid rgba(201,168,76,0.3); }
.zloc-meta{ min-width:0; }
.zloc-zag{ font-size:0.72rem; font-weight:800; color:#c9a84c;
  text-transform:uppercase; letter-spacing:0.06em; }
.zloc-pod{ font-size:0.56rem; color:rgba(255,255,255,0.5);
  letter-spacing:0.04em; margin-top:2px; }'''
CSS_NEW = '''.zloc-strip{ flex-shrink:0; display:flex; flex-direction:column; gap:0;
  border-radius:14px; border:1px solid rgba(255,255,255,0.08);
  background:rgba(255,255,255,0.03); overflow:hidden; }
.zloc-thumb{ width:100%; aspect-ratio:1/1; flex-shrink:0;
  background-size:cover; background-position:center;
  border-bottom:1px solid rgba(201,168,76,0.25); }
.zloc-meta{ min-width:0; padding:10px 12px; text-align:center; }
.zloc-zag{ font-size:0.8rem; font-weight:800; color:#c9a84c;
  text-transform:uppercase; letter-spacing:0.06em; }
.zloc-pod{ font-size:0.58rem; color:rgba(255,255,255,0.5);
  letter-spacing:0.04em; margin-top:3px; }'''


def install():
    print("═══ PATCH ZHITEL_KARTA_BIG_LOC_V1 — карта локаций + большая плашка ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_KARTA_BIG_LOC" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    changed = False

    # правка 1: кнопка
    if KNOPKA_OLD in src:
        src = src.replace(KNOPKA_OLD, KNOPKA_NEW)
        changed = True
        print("  ✔ кнопка «карта» → /grondheim (карта локаций)")
    elif '"/grondheim"' in src and 'ui.button("карта"' in src:
        print("  ○ кнопка уже ведёт на /grondheim")
    else:
        print("  ⚠ кнопку «карта» не нашёл в ожидаемом виде — пропускаю "
              "(проверь вручную адрес /grondheim)")

    # правка 2: CSS плашки
    if CSS_OLD in src:
        src = src.replace(CSS_OLD, CSS_NEW)
        changed = True
        print("  ✔ плашка локации → большой квадрат, подписи внизу")
    else:
        print("  ✖ CSS плашки не в ожидаемом виде — останавливаюсь, "
              "покажи текущий блок .zloc-strip")
        return False

    if not changed:
        print("  ○ нечего менять")
        # всё равно ставим маркер, чтобы не гонять повторно
    src += "\n# ZHITEL_KARTA_BIG_LOC_V1 — маркер идемпотентности\n"

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ синтаксис чист")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
