# -*- coding: utf-8 -*-
"""
patch_grondheim_visual_map.py
PATCH_GRONDHEIM_VISUAL_MAP — визуальная карта города (ГОРОД), две сцены.

Что делает:
  1. Кладёт новый файл  ui_grondheim.py  в корень репо (визуальная карта).
  2. Копирует картинки сцен:
       grondheim.png       -> GRONDHEIM_CITY/карта/static/grondheim.png
       hram_kompleks.png   -> GRONDHEIM_CITY/карта/static/hram_kompleks.png
     (картинки должны лежать РЯДОМ с этим патчем при запуске —
      см. подготовительный шаг ниже).
  3. Патчит ui_brat.py — убирает 4 старые кнопки тулбара
     (Храм / Торговый / Мастеров / Живая книга), оставляет одну «ГОРОД».
  4. Патчит main.py — регистрирует /grondheim и статику /karta_static.

Запуск из КОРНЯ репо (там же main.py, ui_brat.py):
    python patch_grondheim_visual_map.py

Безопасность: перед правкой ui_brat.py и main.py делает .bak-копии.
Если патч уже применён (метка PATCH_GRONDHEIM_VISUAL_MAP найдена) —
не патчит повторно, сообщает и выходит.

`шесть·проверено·до·корня`
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "PATCH_GRONDHEIM_VISUAL_MAP"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak_grondheim_visual_map")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  · бэкап: {bak.name}")


# ──────────────────────────────────────────────────────────
# ШАГ 1 — новый файл ui_grondheim.py
# ──────────────────────────────────────────────────────────

def step_1_ui_grondheim():
    src = ROOT / "ui_grondheim.py"
    if src.exists() and MARK in _read(src):
        print("[1] ui_grondheim.py — уже на месте, пропускаю.")
        return
    here_src = Path(__file__).resolve().parent / "_payload_ui_grondheim.py"
    if not here_src.exists():
        print("[1] ОШИБКА: не найден _payload_ui_grondheim.py рядом с патчем.")
        sys.exit(1)
    shutil.copy2(here_src, src)
    print("[1] ui_grondheim.py положен в корень репо.")


# ──────────────────────────────────────────────────────────
# ШАГ 2 — картинки сцен
# ──────────────────────────────────────────────────────────

def step_2_images():
    static_dir = ROOT / "GRONDHEIM_CITY" / "карта" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    pairs = [
        ("grondheim.png", static_dir / "grondheim.png"),
        ("hram_kompleks.png", static_dir / "hram_kompleks.png"),
    ]
    for name, dest in pairs:
        src = Path(__file__).resolve().parent / name
        if not src.exists():
            print(f"[2] ОШИБКА: не найден {name} рядом с патчем. "
                  f"Положи картинку рядом со скриптом и перезапусти.")
            sys.exit(1)
        shutil.copy2(src, dest)
        print(f"[2] {name} -> {dest.relative_to(ROOT)}")


# ──────────────────────────────────────────────────────────
# ШАГ 3 — патч ui_brat.py: 4 кнопки -> одна «ГОРОД»
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


def step_3_patch_ui_brat():
    path = ROOT / "ui_brat.py"
    if not path.exists():
        print("[3] ОШИБКА: ui_brat.py не найден в корне репо.")
        sys.exit(1)
    text = _read(path)
    if MARK in text:
        print("[3] ui_brat.py — патч уже применён, пропускаю.")
        return
    if OLD_TOOLBAR not in text:
        print("[3] ОШИБКА: старый тулбар не найден один-в-один — "
              "файл, видимо, менялся. Патч не применён, правь руками "
              "по образцу (ищи 'ТУЛБАР: врата').")
        sys.exit(1)
    _backup(path)
    text = text.replace(OLD_TOOLBAR, NEW_TOOLBAR)
    _write(path, text)
    print("[3] ui_brat.py — тулбар заменён на одну кнопку «ГОРОД».")


# ──────────────────────────────────────────────────────────
# ШАГ 4 — патч main.py: регистрация /grondheim + статика
# ──────────────────────────────────────────────────────────

OLD_MAIN_HEAD = '''from dotenv import load_dotenv
load_dotenv()  # читаем .env до импорта страниц

from nicegui import ui

# ── БРАТ — врата мира (единая дверь: запустил Брата → попадаешь везде) ──
from ui_brat import page_brat

@ui.page("/brat")
def _brat():
    page_brat()'''

NEW_MAIN_HEAD = '''from dotenv import load_dotenv
load_dotenv()  # читаем .env до импорта страниц

from pathlib import Path
from nicegui import ui, app

# ── СТАТИКА КАРТЫ — картинки сцен (grondheim.png, hram_kompleks.png) ──
# PATCH_GRONDHEIM_VISUAL_MAP
_KARTA_STATIC_DIR = Path(__file__).resolve().parent / "GRONDHEIM_CITY" / "карта" / "static"
_KARTA_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files("/karta_static", str(_KARTA_STATIC_DIR))

# ── БРАТ — врата мира (единая дверь: запустил Брата → попадаешь везде) ──
from ui_brat import page_brat

@ui.page("/brat")
def _brat():
    page_brat()

# ── ГОРОД — визуальная карта (две сцены) ── PATCH_GRONDHEIM_VISUAL_MAP
from ui_grondheim import page_grondheim
@ui.page("/grondheim")
def _grondheim():
    page_grondheim()'''


def step_4_patch_main():
    path = ROOT / "main.py"
    if not path.exists():
        print("[4] ОШИБКА: main.py не найден в корне репо.")
        sys.exit(1)
    text = _read(path)
    if MARK in text:
        print("[4] main.py — патч уже применён, пропускаю.")
        return
    if OLD_MAIN_HEAD not in text:
        print("[4] ОШИБКА: ожидаемый блок не найден один-в-один в main.py — "
              "файл, видимо, менялся. Патч не применён, правь руками: "
              "добавь app.add_static_files('/karta_static', ...) и "
              "@ui.page('/grondheim') рядом с регистрацией /brat.")
        sys.exit(1)
    _backup(path)
    text = text.replace(OLD_MAIN_HEAD, NEW_MAIN_HEAD)
    _write(path, text)
    print("[4] main.py — добавлены /grondheim и статика /karta_static.")


# ──────────────────────────────────────────────────────────

def main():
    print("=== PATCH_GRONDHEIM_VISUAL_MAP ===")
    step_1_ui_grondheim()
    step_2_images()
    step_3_patch_ui_brat()
    step_4_patch_main()
    print()
    print("Готово. Запусти: python main.py")
    print("Кабинет Брата -> кнопка «ГОРОД» -> карта Грондхейма.")
    print("Клик по Храмовому комплексу -> сцена Гексагон/Ковчег.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
