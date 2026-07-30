# -*- coding: utf-8 -*-
# patch_arkhiv_pravyy_vizual.py — правый загрузчик тоже смотрит картинки
"""
До патча: правый загрузчик («АРХИВ», прямо по разделу) просто клал
файл на диск и писал пустую карточку — теги [], описания нет вообще.
Картинка лежала «слепой»: ни Хранитель, ни кто-либо ещё не мог узнать,
что на ней, не открыв файл руками.

После патча: если загружен файл-картинка — правый загрузчик вызывает
тот же _analiz_kartinki(), что и левый («ЗАГРУЗЧИК»/руда), и пишет
настоящее описание в каталог. Не-картинки (документы и т.п.) ведут
себя как раньше — без изменений.

Идемпотентно: маркер ARKHIV_PRAVYY_VIZUAL_V1, второй раз не портит.

Запуск (из корня Grondheim-Ecosystem):
    python patch_arkhiv_pravyy_vizual.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

TARGET = Path("Архив") / "ui_arkhiv.py"
MARKER = "ARKHIV_PRAVYY_VIZUAL_V1"

YAKOR = '''    async def handle_zapis(e):
        """Запись в архив + каталог. Глубину/оценку Шеф или Хранитель
        правят руками — код за них не сочиняет."""
        imya_f = e.name
        razdel = (zapisi_ref["раздел"].value if zapisi_ref["раздел"] else "прочее") or "прочее"
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        dest_dir = _ARKHIV / razdel
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / imya_f
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не положить в архив: {we}", type="negative")
            return

        kat = _read_json(_KATALOG, {"записи": [], "разделы": RAZDELY}) or {"записи": [], "разделы": RAZDELY}
        zapisi = kat.setdefault("записи", [])
        rel = f"{razdel}/{imya_f}"
        zap_id = Path(imya_f).stem.lower().replace(" ", "_")[:40]
        zapis = {
            "id": zap_id,
            "название": Path(imya_f).stem,
            "раздел": razdel,
            "файл": rel,
            "теги": [],
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        est = next((i for i, z in enumerate(zapisi) if z.get("файл") == rel), None)
        if est is not None:
            zapisi[est] = zapis
        else:
            zapisi.append(zapis)
        kat["разделы"] = RAZDELY
        _write_json(_KATALOG, kat)

        update_arkhiv_info()
        state["чат"].append({
            "role": "assistant", "кто": "АРХИВ",
            "content": f"🗄 «{zapis['название']}» легло в раздел «{razdel}»."})
        update_chat()
        ui.notify(f"В архив, раздел «{razdel}»: {zapis['название']}", type="positive")
        up = zapisi_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass'''

VSTAVKA = '''    async def handle_zapis(e):
        """Запись в архив + каталог. Глубину/оценку Шеф или Хранитель
        правят руками — код за них не сочиняет.

        ARKHIV_PRAVYY_VIZUAL_V1: картинку разбираем по-настоящему —
        тем же вызовом, что и левый загрузчик руды. Без этого файл
        ложился слепым: ни тегов, ни описания, никто не мог узнать,
        что на нём, не открыв руками."""
        imya_f = e.name
        razdel = (zapisi_ref["раздел"].value if zapisi_ref["раздел"] else "прочее") or "прочее"
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        dest_dir = _ARKHIV / razdel
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / imya_f
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не положить в архив: {we}", type="negative")
            return

        is_kartinka = Path(imya_f).suffix.lower() in KARTINKA_EXT
        opisanie = ""
        if is_kartinka:
            state["чат"].append({"role": "assistant", "кто": "АРХИВ",
                                 "content": f"🖼 «{imya_f}» — смотрю…"})
            ui.notify(f"🖼 смотрю: {imya_f}", type="info")
            update_chat()
            opisanie = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")

        kat = _read_json(_KATALOG, {"записи": [], "разделы": RAZDELY}) or {"записи": [], "разделы": RAZDELY}
        zapisi = kat.setdefault("записи", [])
        rel = f"{razdel}/{imya_f}"
        zap_id = Path(imya_f).stem.lower().replace(" ", "_")[:40]
        zapis = {
            "id": zap_id,
            "название": Path(imya_f).stem,
            "раздел": razdel,
            "файл": rel,
            "теги": (["изображение"] if is_kartinka else []),
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if opisanie:
            zapis["описание"] = opisanie
        est = next((i for i, z in enumerate(zapisi) if z.get("файл") == rel), None)
        if est is not None:
            zapisi[est] = zapis
        else:
            zapisi.append(zapis)
        kat["разделы"] = RAZDELY
        _write_json(_KATALOG, kat)

        update_arkhiv_info()
        if is_kartinka and opisanie:
            _soobshchenie = f"🖼 «{zapis['название']}»: {opisanie}"
        else:
            _soobshchenie = f"🗄 «{zapis['название']}» легло в раздел «{razdel}»."
        if is_kartinka:
            state["чат"][-1] = {"role": "assistant", "кто": "АРХИВ",
                                "content": _soobshchenie}
        else:
            state["чат"].append({"role": "assistant", "кто": "АРХИВ",
                                 "content": _soobshchenie})
        update_chat()
        ui.notify(f"В архив, раздел «{razdel}»: {zapis['название']}", type="positive")
        up = zapisi_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass'''


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускай из корня Grondheim-Ecosystem")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"✓ уже применено ({MARKER} найден) — выхожу, ничего не трогаю")
        return

    if YAKOR not in text:
        print("✗ не нашёл ожидаемую функцию handle_zapis в ui_arkhiv.py — файл, "
              "видимо, менялся с тех пор, как я его смотрел. Патч не применён, "
              "ничего не сломано.")
        sys.exit(1)

    if text.count(YAKOR) != 1:
        print(f"✗ ожидаемый кусок встретился {text.count(YAKOR)} раз, должен 1 — "
              "на всякий случай не трогаю файл.")
        sys.exit(1)

    backup = TARGET.with_suffix(TARGET.suffix + ".bak_pravyy_vizual")
    shutil.copy2(TARGET, backup)
    print(f"· бэкап сохранён: {backup}")

    novyy_text = text.replace(YAKOR, VSTAVKA)

    try:
        ast.parse(novyy_text)
    except SyntaxError as e:
        print(f"✗ после патча синтаксическая ошибка: {e}")
        print("  на диск не писал, бэкап можешь удалить.")
        sys.exit(1)

    TARGET.write_text(novyy_text, encoding="utf-8")
    print(f"✓ {TARGET} пропатчен")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✓ py_compile: чисто")
    except py_compile.PyCompileError as e:
        print(f"✗ py_compile ругается: {e}")
        print("  откатываю из бэкапа...")
        shutil.copy2(backup, TARGET)
        print("  откат сделан, ui_arkhiv.py как было")
        sys.exit(1)

    print()
    print("Готово. Правый загрузчик «АРХИВ» теперь реально смотрит на "
          "картинки и пишет описание в каталог — как левый «ЗАГРУЗЧИК».")
    print("СТАРЫЕ картинки, загруженные раньше через правый загрузчик, "
          "этот патч не трогает — они как были без описания, так и остались. "
          "Если нужно — можно отдельно прогнать их через разбор задним числом.")


if __name__ == "__main__":
    main()
