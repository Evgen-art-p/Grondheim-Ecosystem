# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · ТЕКУЩЕЕ МЕСТО — карточка /zhitel/{id} показывает фон
того места, где житель РЕАЛЬНО СЕЙЧАС, не только постоянную прописку.
Маркер: ZHITEL_TEKUSHAYA_LOKACIA_V1

ЗАМЫСЕЛ ШЕФА: клик по точке на карте — это не просто переход в чат,
а переброс «в ту локацию, где он есть». Сейчас (PATCH_FON_PO_PROPISKE)
карточка берёт фон СТАТИЧНОЙ прописки — дом жителя навсегда, даже если
он прямо сейчас на смене на Бирже. Диалог с Верой на сессии показывал
бы фон Торгового Квартала, а не Биржи, где она физически сидит.

ЧТО МЕНЯЕМ (минимально, тем же местом кода, той же функцией
_bg_for_mask — сигнатуру не трогаем):
  БЫЛО: propiska = паспорт.прописка (статика)
        → передаётся в _bg_for_mask(..., propiska=propiska)
  СТАЛО: tekushaya_lokacia = sostoyanie.gde_ya(dom) — читает ЖИВОЕ
        место (по умолчанию = прописка, если житель дома; РЕАЛЬНОЕ
        место, если штампует калибровка/прогулка)
        → передаётся туда же (_bg_for_mask ищет image.* в
        GRONDHEIM_CITY/локации/{tekushaya_lokacia}/ — код лукапа
        не меняется, меняется что в него подаём)

ЧЕСТНОСТЬ: если sostoyanie.py не найден (старая установка) — тихий
откат на прописку, как было. Ничего не падает, просто не хватает
одной живой детали, поведение прежнее.

Идемпотентен: если "tekushaya_lokacia" уже есть в файле — не трогает.

Запуск из корня репо:  python patch_zhitel_tekushaya_lokacia.py
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

ANCHOR = '''def page_zhitel(zid: str = ""):
    p, dom = find_dom(zid) if zid else (None, None)
    propiska = p.get("прописка") if p else None  # PATCH_FON_PO_PROPISKE

    # статика дома жителя + ковчега (общий фон прибытия) + локации прописки
    try:
        from nicegui import app
        if dom is not None and dom.exists():
            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))
        if KOVCHEG_DIR.exists():
            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))
        if propiska:  # PATCH_FON_PO_PROPISKE: своя статика, не ждём захода на /lokacia/{id}
            _loc_dir = LOKACII_DIR / propiska
            if _loc_dir.exists():
                app.add_static_files(f"/lokacia-static/{propiska}", str(_loc_dir))
    except Exception:
        pass

    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")

    # ФОН по маске → прописке → ковчегу
    bg = _bg_for_mask(dom, mask=None, propiska=propiska)'''

INSERT = '''def page_zhitel(zid: str = ""):
    p, dom = find_dom(zid) if zid else (None, None)
    propiska = p.get("прописка") if p else None  # запасной вариант — дом

    # PATCH_ZHITEL_TEKUSHAYA_LOKACIA: фон карточки — по ЖИВОМУ месту
    # (sostoyanie.gde_ya), не по вечной прописке. Житель на сессии —
    # видим Биржу, не Торговый Квартал. Сам замысел: карта переносит
    # "в ту локацию где он есть", не в дом по умолчанию.
    tekushaya_lokacia = propiska
    if dom is not None:
        try:
            _repo = Path(__file__).resolve().parent.parent
            if str(_repo) not in sys.path:
                sys.path.insert(0, str(_repo))
            import sostoyanie as _sost
            _r = _sost.gde_ya(dom)
            if _r.get("локация"):
                tekushaya_lokacia = _r["локация"]
        except Exception:
            pass  # sostoyanie нет — тихий откат на прописку, как было

    # статика дома жителя + ковчега (общий фон прибытия) + ТЕКУЩЕЙ локации
    try:
        from nicegui import app
        if dom is not None and dom.exists():
            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))
        if KOVCHEG_DIR.exists():
            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))
        if tekushaya_lokacia:  # своя статика, не ждём захода на /lokacia/{id}
            _loc_dir = LOKACII_DIR / tekushaya_lokacia
            if _loc_dir.exists():
                app.add_static_files(f"/lokacia-static/{tekushaya_lokacia}", str(_loc_dir))
    except Exception:
        pass

    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")

    # ФОН по маске → ТЕКУЩЕМУ месту (не прописке!) → ковчегу
    bg = _bg_for_mask(dom, mask=None, propiska=tekushaya_lokacia)'''


def install():
    print("═══ PATCH ZHITEL_TEKUSHAYA_LOKACIA_V1 — живое место в карточке ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "tekushaya_lokacia" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if ANCHOR not in src:
        print("  ✖ якорь не найден — файл менялся руками, останавливаюсь. "
              "Покажи текущий page_zhitel(), поправлю точечно.")
        return False

    src = src.replace(ANCHOR, INSERT)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ карточка жителя теперь смотрит на sostoyanie.gde_ya()")
    print("  ✔ фон и статика — по текущему месту, не только прописке")
    print("  ✔ синтаксис чист")
    print("\n  Открой /zhitel/{id} жителя на смене — фон покажет здание,")
    print("  где он реально сейчас, а не постоянный дом.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
