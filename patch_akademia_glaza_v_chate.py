# -*- coding: utf-8 -*-
# AKADEMIA_GLAZA_V_CHATE_V1
"""
УЧЕНИК ПЕРЕСТАЁТ СОЧИНЯТЬ ПРО КАРТИНКУ. Две правки в ui_akademia.py.

ЧТО БЫЛО СЛОМАНО. В Академии два пути к ученику, и картинку нёс
только один:
    кнопка «Прочитать» — изображение прикреплялось, ученик видел;
    ЧАТ                — уходил только текст переписки.
А в переписке лежало имя файла. Спросишь «что на картинке?» — ученик
картинки не видит, видит имя «trch8_str03.png» и сочиняет вокруг него.
Отсюда и старая фотография площади вместо страницы книги. Модель и
зрение были ни при чём: проверка показала, что смотреть она умеет.

ПРАВКА 1 — ЧАТ ВИДИТ ТО, ЧТО ЛЕЖИТ НА СТОЛЕ (_sprosit_uchenika)
    К вопросу прикрепляется свежая картинка из руды — та, что сейчас
    на столе. Теперь про неё МОЖНО спросить, а не только «дать
    прочитать». Ученик и Шеф смотрят на одно и то же.
    Картинки нет — всё как раньше, лишних трат не будет.

ПРАВКА 2 — СНАЧАЛА ЧТО ВИЖУ, ПОТОМ ЧТО ЧУВСТВУЮ (чтение со стола)
    Было: «посмотри своей натурой, вынеси суть плюс личный отклик» —
    наблюдение и натура смешаны в один вопрос, и натура побеждает.
    Реставратор икон видел слои копоти вместо баров.
    Стало: две части. Сперва буквально что на картинке, и только
    потом отклик. Натура не отменяется — она встаёт ВТОРОЙ, после
    того как посмотрели.

    Заодно из запроса убрано ИМЯ ФАЙЛА. Оно и было той соломинкой,
    за которую хваталась выдумка: имя есть, картинки нет — сочиняем
    по имени. Судить теперь можно только по изображению.

    И добавлено право сказать «не разглядела». Без него модель обязана
    что-то ответить — а обязанность отвечать и рождает выдумку.

ЗАПУСК из корня репо:
    python patch_akademia_glaza_v_chate.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "AKADEMIA_GLAZA_V_CHATE_V1"
TARGET = Path("Академия") / "ui_akademia.py"
BAK = Path("Академия") / "ui_akademia.py.bak_glaza_v_chate"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — помощник «что лежит на столе»
# ═══════════════════════════════════════════════════════════
A1_OLD = '''_PROCHITANO_REESTR = _RUDA / "прочитано.json"
_KARTINKA_MIME_STOL = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                       ".webp": "image/webp", ".gif": "image/gif"}
'''

A1_NEW = '''_PROCHITANO_REESTR = _RUDA / "прочитано.json"
_KARTINKA_MIME_STOL = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                       ".webp": "image/webp", ".gif": "image/gif"}


# AKADEMIA_GLAZA_V_CHATE_V1
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

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — чат прикрепляет картинку
# ═══════════════════════════════════════════════════════════
A2_OLD = '''        messages = [{"role": "system", "content": promt}]
        for m in (istoria or [])[-10:]:
            r = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": r, "content": m.get("content", "")})
        messages.append({"role": "user", "content": vopros})
'''

A2_NEW = '''        messages = [{"role": "system", "content": promt}]
        for m in (istoria or [])[-10:]:
            r = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": r, "content": m.get("content", "")})
        # AKADEMIA_GLAZA_V_CHATE_V1: к вопросу прикрепляем то, что лежит
        # на столе. Раньше чат нёс один текст, и на вопрос «что на
        # картинке?» ученик отвечал по имени файла из переписки — то
        # есть сочинял. Картинки нет — всё как раньше.
        _fp_stol, _url_stol = _kartinka_na_stole()
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

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 3 — чтение со стола: сперва смотрим, потом чувствуем
# ═══════════════════════════════════════════════════════════
A3_OLD = '''                vopros = (f"На столе изображение: {fp.name}. Посмотри своей натурой, "
                         f"вынеси концентрат — 5-8 строк, суть плюс личный отклик.")
'''

A3_NEW = '''                # AKADEMIA_GLAZA_V_CHATE_V1: наблюдение и натура разведены
                # по времени. Раньше они стояли в одном вопросе, и натура
                # побеждала: реставратор икон видел слои копоти вместо
                # баров. Имя файла убрано из запроса — оно и было той
                # соломинкой, за которую хваталась выдумка.
                vopros = (
                    "Перед тобой изображение. Ответь двумя частями.\\n\\n"
                    "ЧТО ВИЖУ — только то, что действительно нарисовано. "
                    "Буквально, без толкований и сравнений. Есть чертёж, "
                    "схема или график — назови, что именно на нём начерчено. "
                    "Есть текст — о чём он. Не разглядела или мелко — так и "
                    "напиши, это нормальный ответ, догадываться не нужно.\\n\\n"
                    "ЧТО ЭТО ВО МНЕ — и только теперь твой отклик своей "
                    "натурой, 2-3 фразы.\\n\\n"
                    "Суди по самой картинке. Её название ничего не значит.")
'''

PRAVKI = [
    ("помощник «что на столе»", A1_OLD, A1_NEW),
    ("чат прикрепляет картинку", A2_OLD, A2_NEW),
    ("сперва что вижу, потом что чувствую", A3_OLD, A3_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

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
    print(f"  {len(src)} → {len(novyy)} символов")
    print("\n  Теперь про картинку со стола можно СПРОСИТЬ в чате.")
    print("  Учти: пока картинка лежит в руде, она уходит с каждой")
    print("  репликой — это стоит денег. Дочитали страницу — жми CLEAR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
