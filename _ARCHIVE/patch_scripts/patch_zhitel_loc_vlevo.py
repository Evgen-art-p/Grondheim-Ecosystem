# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · АВАТАРКА ЛОКАЦИИ ВЛЕВО — под загрузчик файлов.
Маркер: ZHITEL_LOC_VLEVO_V1

По слову Шефа: аватарка локации должна стоять СЛЕВА, под загрузчиком
файлов — не справа под аватаром жителя (туда прошлый патч поставил её
по ошибке). Показатели агента (заряд/оптика/натура) остаются справа.

ЧТО ДЕЛАЕТ:
  1. Убирает блок плашки локации из правой колонки (RIGHT).
  2. Ставит его в левую колонку (LEFT), под ui.upload, над списком
     файлов — образ места, куда житель принимает руду, прямо под
     воронкой этой руды.

Требует: patch_zhitel_panel.py уже накатан (плашка существует справа).
Идемпотентен: маркер ZHITEL_LOC_VLEVO в файле → не трогаем.

Запуск из корня репо:  python patch_zhitel_loc_vlevo.py
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

# ── Блок плашки в ПРАВОЙ колонке (ставим пустую строку вместо него) ──
PRAVAYA_BLOK = '''                # аватарка ЛОКАЦИИ где житель сейчас (под аватаром жителя)
                _loc_thumb = _lokacia_thumb(tekushaya_lokacia)
                _mesto_zag, _mesto_pod = _mesto_podpis(dom, tekushaya_lokacia, p)
                if _loc_thumb:
                    ui.html(
                        f'<div class="zloc-strip">'
                        f'<div class="zloc-thumb" style="background-image:url(\\'{_loc_thumb}\\');"></div>'
                        f'<div class="zloc-meta"><div class="zloc-zag">{_mesto_zag}</div>'
                        f'<div class="zloc-pod">{_mesto_pod}</div></div></div>'
                    )

                # ЖИВЫЕ ПОКАЗАТЕЛИ агента (как в старом кабинете — под точкой)'''

PRAVAYA_ZAMENA = '''                # место (заголовок) для панели показателей — считаем здесь,
                # сама плашка локации переехала ВЛЕВО (ZHITEL_LOC_VLEVO_V1)
                _mesto_zag, _mesto_pod = _mesto_podpis(dom, tekushaya_lokacia, p)

                # ЖИВЫЕ ПОКАЗАТЕЛИ агента (как в старом кабинете — под точкой)'''

# ── Левая колонка: врезаем плашку под upload, над списком файлов ──
LEVAYA_BLOK = '''                    ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")
                    refs["files"] = ui.element("div").classes("file-list")
                    update_files()'''

LEVAYA_ZAMENA = '''                    ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")
                    # ZHITEL_LOC_VLEVO_V1: аватарка локации где житель сейчас —
                    # под загрузчиком руды, над списком файлов
                    _loc_thumb_l = _lokacia_thumb(tekushaya_lokacia)
                    if _loc_thumb_l:
                        _lz, _lp = _mesto_podpis(dom, tekushaya_lokacia, p)
                        ui.html(
                            f'<div class="zloc-strip" style="margin:8px;">'
                            f'<div class="zloc-thumb" style="background-image:url(\\'{_loc_thumb_l}\\');"></div>'
                            f'<div class="zloc-meta"><div class="zloc-zag">{_lz}</div>'
                            f'<div class="zloc-pod">{_lp}</div></div></div>'
                        )
                    refs["files"] = ui.element("div").classes("file-list")
                    update_files()'''


def install():
    print("═══ PATCH ZHITEL_LOC_VLEVO_V1 — аватарка локации влево ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_LOC_VLEVO" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if "zloc-strip" not in src:
        print("  ✖ patch_zhitel_panel.py ещё не накатан — сначала он")
        return False

    for name, a in (("правый блок", PRAVAYA_BLOK), ("левый загрузчик", LEVAYA_BLOK)):
        if a not in src:
            print(f"  ✖ якорь «{name}» не найден — файл менялся, останавливаюсь. "
                  f"Покажи текущий ui_zhitel.py.")
            return False

    src = src.replace(PRAVAYA_BLOK, PRAVAYA_ZAMENA)
    src = src.replace(LEVAYA_BLOK, LEVAYA_ZAMENA)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ плашка локации убрана справа")
    print("  ✔ плашка локации встала слева, под загрузчиком файлов")
    print("  ✔ показатели агента остались справа под аватаром")
    print("  ✔ синтаксис чист")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
