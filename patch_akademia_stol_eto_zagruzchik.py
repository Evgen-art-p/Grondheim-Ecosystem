# -*- coding: utf-8 -*-
# AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1
"""
СТОЛ — ЭТО ТО, ЧТО ПОЛОЖИЛИ. Не то, что валяется в папке.

ЧТО БЫЛО СЛОМАНО (моя недоделка в AKADEMIA_GLAZA_V_CHATE_V1)
    «Что лежит на столе» я определил как самую свежую картинку в папке
    руды. Это неверно по самой природе руды: она ОБЩАЯ и НЕ
    РАСХОДУЕТСЯ — прочитанные файлы остаются лежать навсегда.
    Получилось, что на столе вечно что-то лежит, даже когда сегодня
    ничего не клали. Картинка цеплялась к каждой реплике, и на модели
    без зрения разговор молчал. Убрать её можно было только руками,
    вытащив файл из папки, — то есть никак.

ЧТО СТАНОВИТСЯ
    Стол = список загрузчика за эту сессию (state["руда"]). Положил
    страницу — она на столе, про неё можно спрашивать. Нажал CLEAR —
    стол пуст, картинка больше никуда не уходит, работает любая
    модель. Кнопка уже есть, новых ручек не нужно.

    Ничего не грузил — на столе пусто, и чат ведёт себя как раньше.
    Файлы в руде при этом целы: их по-прежнему можно дать читать
    кнопкой «Прочитать», руда не тронута.

ПОРЯДОК: накатывать ПОСЛЕ patch_akademia_glaza_v_chate.py.

ЗАПУСК из корня репо:
    python patch_akademia_stol_eto_zagruzchik.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1"
TARGET = Path("Академия") / "ui_akademia.py"
BAK = Path("Академия") / "ui_akademia.py.bak_stol_eto_zagruzchik"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — сам помощник
# ═══════════════════════════════════════════════════════════
A1_OLD = '''# AKADEMIA_GLAZA_V_CHATE_V1
def _kartinka_na_stole():
    """Что за картинка сейчас лежит на столе: (путь, data-url) или
    (None, ""). Берём самую свежую в руде — стол общий, и лежит на нём
    то, что положили последним.

    Нужно, чтобы про картинку можно было СПРОСИТЬ, а не только «дать
    прочитать». Раньше чат не нёс изображение вовсе, и ученик отвечал
    по имени файла — то есть выдумывал.
    """
    import base64 as _b64
    papka = _RUDA / "изображения"
    if not papka.exists():
        return None, ""
    fajly = [f for f in papka.iterdir()
             if f.is_file() and f.suffix.lower() in _KARTINKA_MIME_STOL]
    if not fajly:
        return None, ""
    fp = max(fajly, key=lambda f: f.stat().st_mtime)
    try:
        data = fp.read_bytes()
    except Exception:
        return None, ""
    mime = _KARTINKA_MIME_STOL.get(fp.suffix.lower(), "image/png")
    return fp, f"data:{mime};base64,{_b64.b64encode(data).decode('ascii')}"
'''

A1_NEW = '''# AKADEMIA_GLAZA_V_CHATE_V1 + AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1
def _kartinka_na_stole(ruda_sessii=None):
    """Что за картинка лежит на столе СЕЙЧАС: (путь, data-url) или
    (None, ""). Стол — это последняя картинка, которую положили в
    загрузчик за эту сессию.

    Нужно, чтобы про картинку можно было СПРОСИТЬ, а не только «дать
    прочитать». Раньше чат не нёс изображение вовсе, и ученик отвечал
    по имени файла — то есть выдумывал.

    AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1. Сначала здесь бралась самая
    свежая картинка ИЗ ПАПКИ руды — и это было неверно: руда общая и
    не расходуется, файлы лежат в ней всегда. Выходило, что на столе
    вечно что-то есть, даже когда сегодня ничего не клали, и убрать
    это можно было только вытащив файл руками. Стол — то, что
    положили; CLEAR в загрузчике его убирает.
    """
    import base64 as _b64
    kartinki = [r for r in (ruda_sessii or [])
                if r.get("вид") == "изображение" and r.get("путь")]
    if not kartinki:
        return None, ""
    fp = Path(kartinki[-1]["путь"])
    if not fp.exists() or fp.suffix.lower() not in _KARTINKA_MIME_STOL:
        return None, ""
    try:
        data = fp.read_bytes()
    except Exception:
        return None, ""
    mime = _KARTINKA_MIME_STOL.get(fp.suffix.lower(), "image/png")
    return fp, f"data:{mime};base64,{_b64.b64encode(data).decode('ascii')}"
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — место вызова: передаём список загрузчика
# ═══════════════════════════════════════════════════════════
A2_OLD = '''        _fp_stol, _url_stol = _kartinka_na_stole()
'''

A2_NEW = '''        # AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1: стол — список загрузчика этой
        # сессии, а не всё, что накопилось в папке руды.
        _fp_stol, _url_stol = _kartinka_na_stole(state.get("руда"))
'''

PRAVKI = [
    ("стол берётся из загрузчика", A1_OLD, A1_NEW),
    ("место вызова", A2_OLD, A2_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0
    if "AKADEMIA_GLAZA_V_CHATE_V1" not in src:
        print("✗ сначала накати patch_akademia_glaza_v_chate.py")
        return 1

    novyy = src
    for imya, old, new in PRAVKI:
        n = novyy.count(old)
        if n != 1:
            print(f"✗ якорь «{imya}»: найден {n} раз (нужно 1). "
                  f"Файл изменился — патч НЕ применён, оригинал цел.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Ничего не грузил — на столе пусто, чат работает на любой")
    print("  модели. Положил страницу — про неё можно спрашивать.")
    print("  Убрать со стола — кнопка CLEAR в загрузчике.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
