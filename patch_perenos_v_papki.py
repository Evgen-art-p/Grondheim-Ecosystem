# -*- coding: utf-8 -*-
"""
patch_perenos_v_papki.py
PATCH_PERENOS_V_PAPKI — дерево репо = дерево мира. Конец плоского корня.

Зачем: корень репо копил файлы вперемешку (ui_brat.py, ui_karta.py,
ui_registry.py, ui_zhitel.py, dvizhok.py, main.py, .bak-и, патчи) —
к этому моменту в нём уже больше десятка файлов без всякой структуры.
Этот патч раскладывает существующий код по смыслу, один раз, и кладёт
СРАЗУ новую визуальную карту (ГОРОД, ui_grondheim.py) в правильное место
— не плюсом ещё одного файла в корень.

ИТОГОВАЯ СТРУКТУРА:
    main.py                  — точка входа, один файл, в корне
    Брат/
      ui_brat.py               (переезжает из корня)
      ui_registry.py            (переезжает из корня — рождение жителей и локаций)
    жители/
      ui_zhitel.py               (переезжает из корня)
      dvizhok.py                  (переезжает из корня)
    ГОРОД/
      ui_karta.py                 (переезжает из корня)
      ui_grondheim.py               (НОВЫЙ — визуальная карта, две сцены)
      static/
        grondheim.png
        hram_kompleks.png
    GRONDHEIM_CITY/            — ДАННЫЕ, не код. Состав не трогаем.

main.py получает sys.path на Брат/, жители/, ГОРОД/ — импорты вида
"from ui_brat import page_brat" продолжают работать без __init__.py.

ui_karta.py и ui_zhitel.py считают свой "корень репо" от __file__ —
после переезда в подпапку им нужен ОДИН лишний .parent. Патч правит
это автоматически (ищет точную строку, иначе не трогает — безопасно).

Запуск из КОРНЯ репо (рядом main.py, ui_brat.py и т.д.):
    python patch_perenos_v_papki.py

Откат:
    python patch_perenos_v_papki.py --undo

Картинки grondheim.png и hram_kompleks.png должны лежать РЯДОМ с этим
патчем при запуске.

`шесть·проверено·до·корня`
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "PATCH_PERENOS_V_PAPKI"

MOVES = [
    ("ui_brat.py",     "Брат"),
    ("ui_registry.py", "Брат"),
    ("ui_zhitel.py",   "жители"),
    ("dvizhok.py",     "жители"),
    ("ui_karta.py",    "ГОРОД"),
]

# точные строки для правки _ROOT после переезда на 1 уровень глубже
ROOT_FIXES = {
    "ui_zhitel.py": (
        '_ROOT = Path(__file__).resolve().parent\n',
        '_ROOT = Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: '
        'файл в жители/, корень репо — на уровень выше\n',
    ),
    "ui_karta.py": (
        '_ROOT = _Path(__file__).resolve().parent\n',
        '_ROOT = _Path(__file__).resolve().parent.parent  # PATCH_PERENOS_V_PAPKI: '
        'файл в ГОРОД/, корень репо — на уровень выше\n',
    ),
}


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, t: str) -> None:
    p.write_text(t, encoding="utf-8")


# ──────────────────────────────────────────────────────────
# ШАГ 1 — переезд существующих файлов в подпапки
# ──────────────────────────────────────────────────────────

def step_1_move_files():
    for fname, subdir in MOVES:
        src = ROOT / fname
        dest_dir = ROOT / subdir
        dest = dest_dir / fname
        if dest.exists():
            print(f"[1] {subdir}/{fname} — уже на месте, пропускаю.")
            continue
        if not src.exists():
            print(f"[1] ПРЕДУПРЕЖДЕНИЕ: {fname} не найден в корне "
                  f"(возможно, уже перенесён иначе). Пропускаю.")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"[1] {fname} -> {subdir}/{fname}")


# ──────────────────────────────────────────────────────────
# ШАГ 2 — правка _ROOT в переехавших файлах
# ──────────────────────────────────────────────────────────

def step_2_fix_roots():
    for fname, subdir in MOVES:
        if fname not in ROOT_FIXES:
            continue
        path = ROOT / subdir / fname
        if not path.exists():
            print(f"[2] {fname} не найден в {subdir}/ — пропускаю правку пути.")
            continue
        text = _read(path)
        if MARK in text:
            print(f"[2] {fname} — путь уже исправлен, пропускаю.")
            continue
        old, new = ROOT_FIXES[fname]
        if old not in text:
            print(f"[2] ПРЕДУПРЕЖДЕНИЕ: в {fname} не найдена ожидаемая строка "
                  f"_ROOT — файл, видимо, менялся. Путь НЕ исправлен, "
                  f"правь руками (добавь .parent ещё раз к _ROOT).")
            continue
        text = text.replace(old, new)
        _write(path, text)
        print(f"[2] {subdir}/{fname} — путь _ROOT исправлен (на уровень выше).")


# ──────────────────────────────────────────────────────────
# ШАГ 3 — новый файл ui_grondheim.py прямо в ГОРОД/
# ──────────────────────────────────────────────────────────

def step_3_ui_grondheim():
    dest_dir = ROOT / "ГОРОД"
    dest = dest_dir / "ui_grondheim.py"
    if dest.exists():
        print("[3] ГОРОД/ui_grondheim.py — уже на месте, пропускаю.")
        return
    payload = Path(__file__).resolve().parent / "_payload_ui_grondheim.py"
    if not payload.exists():
        print("[3] ОШИБКА: не найден _payload_ui_grondheim.py рядом с патчем.")
        sys.exit(1)
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(payload, dest)
    print("[3] ГОРОД/ui_grondheim.py положен на место.")


# ──────────────────────────────────────────────────────────
# ШАГ 4 — картинки сцен -> ГОРОД/static/
# ──────────────────────────────────────────────────────────

def step_4_images():
    static_dir = ROOT / "ГОРОД" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    for name in ("grondheim.png", "hram_kompleks.png"):
        src = Path(__file__).resolve().parent / name
        dest = static_dir / name
        if not src.exists():
            print(f"[4] ОШИБКА: {name} не найден рядом с патчем.")
            sys.exit(1)
        shutil.copy2(src, dest)
        print(f"[4] {name} -> ГОРОД/static/{name}")


# ──────────────────────────────────────────────────────────
# ШАГ 5 — тулбар ui_brat.py: 4 кнопки -> одна «ГОРОД»
# ──────────────────────────────────────────────────────────

OLD_TOOLBAR = '''                # ── ТУЛБАР: врата (прозрачная плашка, кнопки по центру) ──
                with ui.element("div").classes("stage-toolbar").style(
                    "flex-shrink:0; grid-template-columns:1fr; justify-items:center; "
                    "align-items:end !important; height:auto !important; "
                    "padding:6px 12px 6px !important; "
                    "background:transparent !important; border-bottom:none !important; "
                    "backdrop-filter:none !important;"
                ):
                    with ui.element("div").style(
                        "display:flex; gap:8px; align-items:center; justify-content:center;"
                    ):
                        ui.button("Храм",
                                  on_click=lambda: ui.navigate.to("/hram/index.html")
                                  ).props("flat").classes("brat-gate")  # PATCH_HRAM_GATE
                        ui.button("Торговый").props("flat").classes("brat-gate")
                        ui.button("Мастеров").props("flat").classes("brat-gate")
                        ui.button("Живая книга").props("flat").classes("brat-gate")'''

NEW_TOOLBAR = '''                # ── ТУЛБАР: одни врата — ГОРОД (визуальная карта) ──
                # PATCH_GRONDHEIM_VISUAL_MAP: старые 4 кнопки (Храм/Торговый/
                # Мастеров/Живая книга) убраны — переходы внутри города
                # теперь идут кликом по локации на самой карте, без кнопок.
                with ui.element("div").classes("stage-toolbar").style(
                    "flex-shrink:0; grid-template-columns:1fr; justify-items:center; "
                    "align-items:end !important; height:auto !important; "
                    "padding:6px 12px 6px !important; "
                    "background:transparent !important; border-bottom:none !important; "
                    "backdrop-filter:none !important;"
                ):
                    with ui.element("div").style(
                        "display:flex; gap:8px; align-items:center; justify-content:center;"
                    ):
                        ui.button("ГОРОД",
                                  on_click=lambda: ui.navigate.to("/grondheim")
                                  ).props("flat").classes("brat-gate")  # PATCH_GRONDHEIM_VISUAL_MAP'''


def step_5_patch_toolbar():
    path = ROOT / "Брат" / "ui_brat.py"
    if not path.exists():
        print("[5] ОШИБКА: Брат/ui_brat.py не найден — шаг 1 должен был "
              "его туда положить. Проверь.")
        sys.exit(1)
    text = _read(path)
    if "PATCH_GRONDHEIM_VISUAL_MAP" in text:
        print("[5] Брат/ui_brat.py — тулбар уже патчен, пропускаю.")
        return
    if OLD_TOOLBAR not in text:
        print("[5] ПРЕДУПРЕЖДЕНИЕ: старый тулбар не найден один-в-один — "
              "файл менялся. Тулбар НЕ патчен, правь руками "
              "(ищи 'ТУЛБАР: врата' в Брат/ui_brat.py).")
        return
    text = text.replace(OLD_TOOLBAR, NEW_TOOLBAR)
    _write(path, text)
    print("[5] Брат/ui_brat.py — тулбар заменён на одну кнопку «ГОРОД».")


# ──────────────────────────────────────────────────────────
# ШАГ 6 — новый main.py (sys.path на подпапки + /grondheim + статика)
# ──────────────────────────────────────────────────────────

def step_6_new_main():
    path = ROOT / "main.py"
    if path.exists() and MARK in _read(path):
        print("[6] main.py — уже патчен, пропускаю.")
        return
    payload = Path(__file__).resolve().parent / "_payload_main.py"
    if not payload.exists():
        print("[6] ОШИБКА: не найден _payload_main.py рядом с патчем.")
        sys.exit(1)
    if path.exists():
        bak = path.with_suffix(".py.bak_perenos_v_papki")
        if not bak.exists():
            shutil.copy2(path, bak)
            print(f"[6] бэкап: {bak.name}")
    shutil.copy2(payload, path)
    print("[6] main.py — заменён на версию с sys.path и /grondheim.")


# ──────────────────────────────────────────────────────────

def main():
    if "--undo" in sys.argv:
        undo()
        return
    print("=== PATCH_PERENOS_V_PAPKI ===")
    step_1_move_files()
    step_2_fix_roots()
    step_3_ui_grondheim()
    step_4_images()
    step_5_patch_toolbar()
    step_6_new_main()
    print()
    print("Готово. Структура репо теперь по смыслу:")
    print("  Брат/    — ui_brat.py, ui_registry.py")
    print("  жители/  — ui_zhitel.py, dvizhok.py")
    print("  ГОРОД/   — ui_karta.py, ui_grondheim.py, static/")
    print()
    print("Запусти: python main.py")
    print("Откат:   python patch_perenos_v_papki.py --undo")
    print("шесть·проверено·до·корня")


def undo():
    print("=== ОТКАТ PATCH_PERENOS_V_PAPKI ===")

    # 1) вернуть main.py
    path = ROOT / "main.py"
    bak = path.with_suffix(".py.bak_perenos_v_papki")
    if bak.exists():
        shutil.copy2(bak, path)
        bak.unlink()
        print("[undo] main.py — восстановлен из бэкапа.")
    else:
        print("[undo] main.py — бэкапа нет, не трогаю.")

    # 2) откатить тулбар В ui_brat.py, ПОКА он ещё в Брат/ (до переезда обратно)
    brat_path = ROOT / "Брат" / "ui_brat.py"
    if brat_path.exists():
        text = _read(brat_path)
        if NEW_TOOLBAR in text:
            text = text.replace(NEW_TOOLBAR, OLD_TOOLBAR)
            _write(brat_path, text)
            print("[undo] Брат/ui_brat.py — тулбар вернул на старые 4 кнопки.")
        elif "PATCH_GRONDHEIM_VISUAL_MAP" in text:
            print("[undo] ПРЕДУПРЕЖДЕНИЕ: тулбар патчен, но текст не совпал "
                  "один-в-один (менялся вручную?) — кнопка «ГОРОД» осталась, "
                  "правь руками.")

    # 3) вернуть файлы из подпапок в корень, откатить правку _ROOT
    for fname, subdir in MOVES:
        src = ROOT / subdir / fname
        dest = ROOT / fname
        if not src.exists():
            print(f"[undo] {subdir}/{fname} не найден, пропускаю.")
            continue
        text = _read(src)
        if fname in ROOT_FIXES:
            old, new = ROOT_FIXES[fname]
            if new in text:
                text = text.replace(new, old)
                _write(src, text)
        shutil.move(str(src), str(dest))
        print(f"[undo] {subdir}/{fname} -> {fname} (в корень, путь восстановлен).")

    # 4) убрать пустые папки Брат/жители (если опустели), ГОРОД целиком
    goro_dir = ROOT / "ГОРОД"
    if goro_dir.exists():
        shutil.rmtree(goro_dir)
        print("[undo] ГОРОД/ — удалена целиком (ui_grondheim.py + static).")

    for subdir in ("Брат", "жители"):
        d = ROOT / subdir
        if d.exists() and not any(d.iterdir()):
            d.rmdir()
            print(f"[undo] {subdir}/ — пустая папка убрана.")
        elif d.exists():
            print(f"[undo] {subdir}/ — оставлена (внутри что-то ещё есть).")

    print()
    print("Откат завершён. Структура вернулась к плоскому корню.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
