# -*- coding: utf-8 -*-
# PATCH_LOKACIA_FON_V1 — образ места фоном страницы
"""
Правит ГОРОД/ui_lokacia.py.

БЫЛО: на странице локации картинка места висела только маленькой
карточкой слева. Фон страницы задавался ОДНИМ ЦВЕТОМ (#050510) —
background-image не ставился вообще. Отсюда чёрный экран у Маяка.

СТАЛО: тот же образ (image.*) уходит в фон страницы — ровно тем же
приёмом, что в Бирже и в кабинете жителя:
    ui.add_head_html("<style>#lbg{background-image:url('...')}</style>")

Затемнение НЕ трогаю: у локации оно своё, мягче биржевого — золотые
блики по углам, чёрный на 50% и лёгкое размытие. Картинка будет
видна, а текст поверх останется читаемым.

Правит ВСЕ локации разом, не только Маяк: способ показывать место
в городе должен быть один (Закон Фрактала). У кого лежит image.* —
у того фон и появится, остальные останутся как были.

Идемпотентно: маркер PATCH_LOKACIA_FON_V1 — второй прогон молчит.
Бэкап перед правкой, ast.parse после — не сошлось, не пишем.

Запуск ИЗ КОРНЯ РЕПО:
    python patch_lokacia_fon_v1.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "ГОРОД" / "ui_lokacia.py"
MARKER = "# PATCH_LOKACIA_FON_V1"

ANCHOR = '''    ui.add_head_html(f"<style>{LOKACIA_CSS}</style>")
    ui.html('<div id="lbg"></div>')'''

BLOCK = '''    ui.add_head_html(f"<style>{LOKACIA_CSS}</style>")

    # PATCH_LOKACIA_FON_V1: образ места — ФОНОМ страницы.
    # Тот же приём, что в Бирже и в кабинете жителя: картинка не только
    # в карточке слева, но и за всем окном. Нет image.* — фон остаётся
    # цветом, как было (честно пусто, а не битая ссылка).
    _bg_lok = _image_url(dom, p or {}) if dom is not None else ""
    if _bg_lok:
        ui.add_head_html(
            f"<style>#lbg{{background-image:url('{_bg_lok}')!important;}}</style>")

    ui.html('<div id="lbg"></div>')'''


def main():
    print("═══ PATCH_LOKACIA_FON_V1 ═══")
    print(f"корень: {ROOT}\n")

    if not TARGET.exists():
        print(f"✗ {TARGET} не найден. Запускай ИЗ КОРНЯ репо.")
        return False

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("= патч уже накатан")
        return True

    if ANCHOR not in src:
        print("✗ якорь не найден — файл ui_lokacia.py менялся.")
        print("  Правь вручную: после add_head_html со стилями вставь")
        print("  установку #lbg{background-image:...} из образа места.")
        return False

    novyy = src.replace(ANCHOR, BLOCK, 1)

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки файл не парсится: {e}")
        print("ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_fon")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"✓ бэкап: {bak.name}")
    print("✓ образ места уходит в фон страницы")

    # подсказка: у кого из локаций картинка вообще есть
    lok_dir = ROOT / "GRONDHEIM_CITY" / "локации"
    if lok_dir.exists():
        s_kartinkoy, bez = [], []
        for d in sorted(lok_dir.iterdir()):
            if not d.is_dir():
                continue
            est = any((d / f"image{e}").exists()
                      for e in (".png", ".jpg", ".jpeg", ".webp"))
            (s_kartinkoy if est else bez).append(d.name)
        print()
        print(f"  с фоном будут ({len(s_kartinkoy)}):")
        for n in s_kartinkoy:
            print(f"    ✓ {n}")
        if bez:
            print(f"  останутся цветом ({len(bez)}) — нет image.*:")
            for n in bez:
                print(f"    · {n}")
    return True


if __name__ == "__main__":
    try:
        import sys as _s
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ok = main()
    print()
    if ok:
        print("✅ ГОТОВО. Открывай Маяк — фон встанет из его же картинки.")
    else:
        print("❌ Не докатилось — смотри выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
