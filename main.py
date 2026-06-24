# main.py  # PATCH_ROZHENITSA_GATE_APPLIED  # PATCH_KARTA_GATE_APPLIED — запуск мира Грондхейм
"""
Точка входа. Поднимает NiceGUI и регистрирует страницы.

Запуск из КОРНЯ репо:
    python main.py

Перед первым запуском:
    pip install nicegui httpx python-dotenv
    cp .env.example .env   # и впиши OPENROUTER_API_KEY

Откроется:  http://localhost:8080/brat
"""
from dotenv import load_dotenv
load_dotenv()  # читаем .env до импорта страниц

from nicegui import ui

# ── БРАТ — врата мира ──
from ui_brat import page_brat

@ui.page("/brat")
def _brat():
    page_brat()

# ── СТРАНИЦА ЖИЗНИ — бланк паспорта (ступень 2) ──
from ui_rozhenitsa import page_rozhenitsa
@ui.page("/rozhenitsa")
def _rozhenitsa():
    page_rozhenitsa()

# ── КАРТА-ИЕРАРХИЯ — зрение Брата (ступень 1) ──
from ui_karta import page_karta
@ui.page("/karta")
def _karta():
    page_karta()

# Корень → редирект в кабинет Брата
@ui.page("/")
def _index():
    ui.navigate.to("/brat")

# ── РЕЕСТР (если нужен) ──
# from ui_registry import page_registry
# @ui.page("/registry")
# def _registry():
#     page_registry()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Грондхейм · Брат",
        port=8080,
        reload=False,
        show=True,        # сам откроет браузер
        storage_secret="grondheim",
    )
