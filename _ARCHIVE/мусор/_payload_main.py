# main.py  # PATCH_REAL_ZHIZN_APPLIED  # PATCH_ROZHENITSA_GATE_APPLIED  # PATCH_KARTA_GATE_APPLIED  # PATCH_ZHITEL_GATE_APPLIED  # PATCH_PERENOS_V_PAPKI — запуск мира Грондхейм
"""
Точка входа. Поднимает NiceGUI и регистрирует страницы.

Запуск из КОРНЯ репо:
    python main.py

Перед первым запуском:
    pip install nicegui httpx python-dotenv
    cp .env.example .env   # и впиши OPENROUTER_API_KEY

Откроется:  http://localhost:8080/brat

СТРУКТУРА ПАПОК (PATCH_PERENOS_V_PAPKI — дерево репо = дерево мира):
    Брат/        — ui_brat.py, ui_registry.py (Брат прописывает и связывает)
    жители/      — ui_zhitel.py, dvizhok.py (всё про самого жителя)
    ГОРОД/       — ui_karta.py, ui_grondheim.py + static/ (картинки сцен)
    GRONDHEIM_CITY/ — ДАННЫЕ (не код): паспорта жителей, локаций

Страницы (всё доступно через кабинет Брата):
    /brat              — кабинет Брата (врата мира, единая дверь)
    /grondheim         — ГОРОД, визуальная карта (две сцены: общая + храм)
    /karta             — карта города (зрение Брата; клик на жителя → его кабинет)
    /registry          — Страница Жизни (рождение жителя)
    /zhitel/{id}       — кабинет жителя (по ID_Object, напр. 0001_Liya_Heat)
    /zhitel            — кабинет жителя без id → список выбора
    /hram/index.html   — Храм (статика)
"""
import sys
from pathlib import Path

# ── ПУТИ К ПОДПАПКАМ-ПАКЕТАМ ── PATCH_PERENOS_V_PAPKI
# Код мира разложен по смыслу (Брат/, жители/, ГОРОД/), не плоско в корне.
# Чтобы "from ui_brat import ..." и т.п. работали без __init__.py и без
# превращения папок в формальные пакеты — добавляем их в sys.path.
_ROOT = Path(__file__).resolve().parent
for _sub in ("Брат", "жители", "ГОРОД"):
    _p = str(_ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv()  # читаем .env до импорта страниц

from nicegui import ui, app

# ── СТАТИКА КАРТЫ — картинки сцен (grondheim.png, hram_kompleks.png) ──
# PATCH_GRONDHEIM_VISUAL_MAP / PATCH_PERENOS_V_PAPKI
_KARTA_STATIC_DIR = _ROOT / "ГОРОД" / "static"
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
    page_grondheim()

# ── ЧЕРНОВИК ui_rozhenitsa ВЫКЛЮЧЕН (в топку, путь А) ──
# Настоящая Страница Жизни — ui_registry ниже.
# from ui_rozhenitsa import page_rozhenitsa
# @ui.page("/rozhenitsa")
# def _rozhenitsa():
#     page_rozhenitsa()

# ── КАРТА-ИЕРАРХИЯ — зрение Брата (ступень 1) ──
from ui_karta import page_karta
@ui.page("/karta")
def _karta():
    page_karta()

# Корень → редирект в кабинет Брата
@ui.page("/")
def _index():
    ui.navigate.to("/brat")

# ── НАСТОЯЩАЯ СТРАНИЦА ЖИЗНИ · Реестр (полная форма) ──
from ui_registry import page_registry
@ui.page("/registry")
def _registry():
    page_registry()

# ── КАБИНЕТ ЖИТЕЛЯ — единое окно в любого жителя ──
# Путь: запустил Брата → ГРОНДХЕЙМ (карта) → клик «открыть →» на жителе → сюда.
# /zhitel/{id} открывает конкретного жителя по ID_Object (напр. 0001_Liya_Heat).
# /zhitel без id — покажет список выбора.
from ui_zhitel import page_zhitel

@ui.page("/zhitel/{zid}")
def _zhitel(zid: str = ""):
    page_zhitel(zid)

@ui.page("/zhitel")
def _zhitel0():
    page_zhitel("")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Грондхейм · Брат",
        port=8080,
        reload=False,
        show=True,        # сам откроет браузер
        storage_secret="grondheim",
    )
