# -*- coding: utf-8 -*-
# PATCH_AKADEMIA_KURSY_SCAN_V1 — курс: живой скан папки, не свободный текст
"""
Правит Брат/ui_brat.py (поверх PATCH_AKADEMIA_STUDENT_V1, ставить после него):

  1. Заводит list_kursy() — сканирует GRONDHEIM_CITY/Академия/курсы/,
     как Биржа сканирует цеха (Закон Картриджа: курс сам заявляет о
     себе через manifest.json, Брат ничего не держит списком).
     Курсов пока нет ни одного — функция просто вернёт [], это честно.

  2. В диалоге «Роль» → «студент»: свободное поле "Курс" заменяется
     на выпадающий список из list_kursy(). Курсов нет — вместо списка
     подпись «курсов пока нет», запись пройдёт без курса.

Идемпотентно: list_kursy уже в файле — второй прогон не трогает.
Бэкап перед правкой, ast.parse после — не сошлось, не пишем.

Запуск ИЗ КОРНЯ РЕПО, ПОСЛЕ patch_akademia_student_v1.py:
    python patch_akademia_kursy_scan_v1.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "Брат" / "ui_brat.py"

# ── 1. list_kursy() — вставляется между _akademia_ucheniki_chitat()
#       и zapisat_studenta() ────────────────────────────────────
ANCHOR_FUNC = '''def _akademia_ucheniki_chitat() -> dict:
    import json
    if not AKADEMIA_UCHENIKI.exists():
        return {"места": []}
    try:
        return json.loads(AKADEMIA_UCHENIKI.read_text(encoding="utf-8"))
    except Exception:
        return {"места": []}


def zapisat_studenta(zid: str, kurs: str = ""):'''

BLOCK_FUNC = '''def _akademia_ucheniki_chitat() -> dict:
    import json
    if not AKADEMIA_UCHENIKI.exists():
        return {"места": []}
    try:
        return json.loads(AKADEMIA_UCHENIKI.read_text(encoding="utf-8"))
    except Exception:
        return {"места": []}


# ── PATCH_AKADEMIA_KURSY_SCAN_V1 — курсы: живой скан, не список в коде ──
# Тот же Закон Картриджа, что у Биржи с цехами: курс сам заявляет о
# себе (manifest.json в своей папке), Брат только читает по требованию.
# Курсов пока нет — функция честно вернёт [], диалог покажет "пусто",
# не выдумает заглушку.
AKADEMIA_KURSY_DIR = Path("GRONDHEIM_CITY/Академия/курсы")


def list_kursy() -> list:
    """Курсы Академии — папка GRONDHEIM_CITY/Академия/курсы/{id}/.
    Название — из manifest.json ("название" или "title"), нет файла
    или полей — берём имя папки как есть. Возвращает [{"id","title"}]."""
    out = []
    if not AKADEMIA_KURSY_DIR.exists():
        return out
    import json
    for d in sorted(AKADEMIA_KURSY_DIR.iterdir()):
        if not d.is_dir():
            continue
        title = d.name
        mf = d / "manifest.json"
        if mf.exists():
            try:
                m = json.loads(mf.read_text(encoding="utf-8"))
                title = m.get("название") or m.get("title") or d.name
            except Exception:
                pass
        out.append({"id": d.name, "title": title})
    return out


def zapisat_studenta(zid: str, kurs: str = ""):'''

# ── 2. Диалог: свободный ввод курса -> выпадающий список ────────
ANCHOR_DIALOG = '''                            ui.html('<div style="color:rgba(255,255,255,0.45); font-size:0.68rem; '
                                    'margin-bottom:6px; text-transform:uppercase; letter-spacing:0.06em;">'
                                    'курс (необязательно)</div>')
                            kurs = ui.input("Курс").props("dark outlined").style(
                                "width:100%; font-size:0.8rem;")

                            async def _confirm():
                                ok, msg = zapisat_studenta(
                                    pick["zhitel"].get("ID_Object", ""),
                                    (kurs.value or "").strip(),
                                )'''

BLOCK_DIALOG = '''                            ui.html('<div style="color:rgba(255,255,255,0.45); font-size:0.68rem; '
                                    'margin-bottom:6px; text-transform:uppercase; letter-spacing:0.06em;">'
                                    'курс (необязательно)</div>')
                            # PATCH_AKADEMIA_KURSY_SCAN_V1: живой список, не текст руками
                            _kursy_spisok = list_kursy()
                            if _kursy_spisok:
                                _kurs_opts = {"": "— без курса —"}
                                _kurs_opts.update({k["id"]: k["title"] for k in _kursy_spisok})
                                kurs = ui.select(_kurs_opts, value="").props("dark outlined").style(
                                    "width:100%; font-size:0.8rem;")
                            else:
                                ui.html('<div style="color:rgba(255,255,255,0.35); font-size:0.7rem; '
                                        'margin-bottom:4px;">курсов пока нет — запишется без курса</div>')
                                kurs = None

                            async def _confirm():
                                _kurs_val = (kurs.value or "").strip() if kurs is not None else ""
                                ok, msg = zapisat_studenta(
                                    pick["zhitel"].get("ID_Object", ""),
                                    _kurs_val,
                                )'''


def main():
    print("═══ PATCH_AKADEMIA_KURSY_SCAN_V1 ═══")
    print(f"корень: {ROOT}\n")

    if not TARGET.exists():
        print(f"✗ {TARGET} не найден. Запускай ИЗ КОРНЯ репо.")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "def list_kursy" in src:
        print("= патч уже накатан — list_kursy уже в файле")
        return True

    if "def zapisat_studenta" not in src:
        print("✗ zapisat_studenta не найдена — сначала накати "
              "patch_akademia_student_v1.py")
        return False

    novyy = src
    izmeneno = []

    if ANCHOR_FUNC not in novyy:
        print("✗ якорь для list_kursy не найден.")
        return False
    novyy = novyy.replace(ANCHOR_FUNC, BLOCK_FUNC, 1)
    izmeneno.append("list_kursy()")

    if ANCHOR_DIALOG not in novyy:
        print("✗ якорь диалога (поле «Курс») не найден.")
        return False
    novyy = novyy.replace(ANCHOR_DIALOG, BLOCK_DIALOG, 1)
    izmeneno.append("курс -> выпадающий список")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки файл не парсится: {e}")
        print("ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_akademia_kursy")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"✓ бэкап: {bak.name}")
    print(f"✓ правки: {', '.join(izmeneno)}")
    return True


if __name__ == "__main__":
    ok = main()
    print()
    if ok:
        print("✅ ГОТОВО. Курс в диалоге «студент» теперь читается с диска.")
        print("   Появится первый курс в GRONDHEIM_CITY/Академия/курсы/{id}/ —")
        print("   список в диалоге пополнится сам, код трогать не надо.")
    else:
        print("❌ Не докатилось — смотри сообщения выше.")
    print("`шесть·проверено·до·корня`")
