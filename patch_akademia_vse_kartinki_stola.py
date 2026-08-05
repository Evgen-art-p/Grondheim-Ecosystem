# -*- coding: utf-8 -*-
# AKADEMIA_VSE_KARTINKI_STOLA_V1
"""
НА СТОЛЕ МОЖЕТ ЛЕЖАТЬ НЕСКОЛЬКО СТРАНИЦ.

ОТКУДА ВЗЯТО. Так сделано в старой студии (репо `-2`,
studio/workshop/utils.py · _collect_images_for_vision): собираются ВСЕ
картинки из списка загрузчика и уходят к модели разом. Там это давно
работает — берём проверенное, а не выдумываем своё.

ЧТО БЫЛО СЛОМАНО (моя недоделка)
    Я брал только ПОСЛЕДНЮЮ картинку из загрузчика. Значит сравнить
    две страницы ученик не мог физически: первая до него не доходила.
    А сравнение — суть учёбы: вот здесь откат кончился, а здесь нет.
    Вот тут ангуляция есть, а тут её нет.

ЧТО СТАНОВИТСЯ
    Уходят все картинки со стола, в том порядке, в каком их клали, и
    ученику говорится, сколько их. Положил две страницы — можно
    спрашивать «чем отличаются». Убрать лишнее — CLEAR в загрузчике.

    Руду при этом не трогаем: в Академии она ОБЩАЯ и не расходуется,
    в отличие от студии, где файл удалялся с диска. Со стола убрали —
    из руды не пропало, другой ученик прочитает.

ЦЕНА. Каждая картинка уходит с КАЖДОЙ репликой. Две страницы — двойная
цена сообщения. Разобрали — чисти стол.

ПОРЯДОК: после patch_akademia_glaza_v_chate.py и
patch_akademia_stol_eto_zagruzchik.py.

ЗАПУСК из корня репо:
    python patch_akademia_vse_kartinki_stola.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "AKADEMIA_VSE_KARTINKI_STOLA_V1"
TARGET = Path("Академия") / "ui_akademia.py"
BAK = Path("Академия") / "ui_akademia.py.bak_vse_kartinki_stola"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — помощник отдаёт СПИСОК
# ═══════════════════════════════════════════════════════════
A1_OLD = '''    положили; CLEAR в загрузчике его убирает.
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

A1_NEW = '''    положили; CLEAR в загрузчике его убирает.

    AKADEMIA_VSE_KARTINKI_STOLA_V1: отдаём ВСЕ картинки со стола, а не
    последнюю. Так сделано в старой студии (_collect_images_for_vision)
    и там работает. Одна картинка = сравнивать не с чем, а сравнение и
    есть учёба: здесь откат кончился, а здесь нет.

    Возвращает список пар (путь, data-url), в порядке укладки.
    """
    import base64 as _b64
    out = []
    for r in (ruda_sessii or []):
        if r.get("вид") != "изображение" or not r.get("путь"):
            continue
        fp = Path(r["путь"])
        if not fp.exists() or fp.suffix.lower() not in _KARTINKA_MIME_STOL:
            continue
        try:
            data = fp.read_bytes()
        except Exception:
            continue
        mime = _KARTINKA_MIME_STOL.get(fp.suffix.lower(), "image/png")
        out.append((fp, f"data:{mime};base64,{_b64.b64encode(data).decode('ascii')}"))
    return out
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — место вызова: прикрепляем все
# ═══════════════════════════════════════════════════════════
A2_OLD = '''        # AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1: стол — список загрузчика этой
        # сессии, а не всё, что накопилось в папке руды.
        _fp_stol, _url_stol = _kartinka_na_stole(state.get("руда"))
        if _url_stol:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": (
                    "(На столе перед тобой лежит изображение. Если речь о нём — "
                    "смотри на само изображение, а не на его название. "
                    "Не разглядела — так и скажи.)\\n\\n" + vopros)},
                {"type": "image_url", "image_url": {"url": _url_stol}},
            ]})
        else:
            messages.append({"role": "user", "content": vopros})
'''

A2_NEW = '''        # AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1: стол — список загрузчика этой
        # сессии, а не всё, что накопилось в папке руды.
        # AKADEMIA_VSE_KARTINKI_STOLA_V1: кладём ВСЕ, чтобы можно было
        # сравнивать страницы между собой.
        _stol = _kartinka_na_stole(state.get("руда"))
        _url_stol = _stol[0][1] if _stol else ""
        if _stol:
            _skolko = ("На столе перед тобой лежит изображение."
                       if len(_stol) == 1 else
                       f"На столе перед тобой {len(_stol)} изображени"
                       f"{'я' if len(_stol) < 5 else 'й'}, по порядку.")
            _content = [{"type": "text", "text": (
                f"({_skolko} Если речь о них — смотри на сами изображения, "
                f"а не на названия. Не разглядела — так и скажи.)\\n\\n" + vopros)}]
            for _fp_i, _url_i in _stol:
                _content.append({"type": "image_url",
                                 "image_url": {"url": _url_i}})
            messages.append({"role": "user", "content": _content})
        else:
            messages.append({"role": "user", "content": vopros})
'''

PRAVKI = [
    ("помощник отдаёт все картинки", A1_OLD, A1_NEW),
    ("к вопросу прикрепляются все", A2_OLD, A2_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0
    if "AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1" not in src:
        print("✗ сначала накати patch_akademia_stol_eto_zagruzchik.py")
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
    print("\n  Положи две страницы — можно спрашивать, чем отличаются.")
    print("  Каждая уходит с каждой репликой: разобрали — жми CLEAR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
