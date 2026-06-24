# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ДВА ФАЙЛА — куча + паспорт-кусочек на свой этаж       ║
║  Новый город · ступень 2 (рождаем только паспорт)           ║
║                                                              ║
║  Что делает (точечно, в ui_registry.py):                    ║
║    1. Добавляет rodit_pasport_kusochek() — кладёт кусочек    ║
║       в GRONDHEIM_CITY/жители/{предназначение}/{имя}.json    ║
║       Этаж = предназначение (Profession). Растёт сам         ║
║       (Закон Картриджа: новое слово → новый этаж).           ║
║    2. В save_object: после save_catalog (куча, НЕ трогаем)   ║
║       рождает кусочек рядом. ДВА ФАЙЛА буквально.            ║
║    3. Отключает generate_agent_files (папки-слои) —          ║
║       это СЛЕДУЮЩИЙ шаг. Сейчас только паспорт, без памяти.  ║
║                                                              ║
║  Идемпотентно. `шесть·проверено·до·корня`                    ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_DVA_FILA_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ Два файла уже включены — пропускаю (идемпотентно)")
        return

    # ── ВСТАВКА 1: функция рождения кусочка ──
    # Садится после save_catalog() — рядом с записью кучи.
    anchor_func = (
        'def save_catalog(catalog: list[dict]):\n'
        '    """Save catalog to JSON file."""\n'
        '    CATALOG_FILE.write_text(\n'
        '        json.dumps(catalog, ensure_ascii=False, indent=2),\n'
        '        encoding="utf-8"\n'
        '    )\n'
    )
    if anchor_func not in src:
        fail("функция save_catalog не найдена дословно — файл изменился, покажи свежий")

    new_func = anchor_func + '''

# ── PATCH_DVA_FILA: рождение паспорта-кусочка на свой этаж ──
# Новый город. Кусочек ложится туда, где место жителя — по предназначению.
# Путь = принадлежность (Закон Пары). Этажи растут сами из предназначений.
ZHITELI_DIR = Path("GRONDHEIM_CITY/жители")


def _safe_name(s: str) -> str:
    """Чистим имя/предназначение для имени файла/папки."""
    s = (s or "").strip()
    for ch in '/\\\\:*?"<>|':
        s = s.replace(ch, "_")
    return s or "без_имени"


def rodit_pasport_kusochek(obj: dict) -> str:
    """
    Рождает ОДИН паспорт-кусочек рядом с кучей.
    Падает на этаж по предназначению (Profession):
        Вася трейдер → GRONDHEIM_CITY/жители/трейдер/Вася.json
    Если предназначения нет — этаж 'без_предназначения'.
    Папки-слои НЕ создаёт (это следующий шаг). Только файл-паспорт.
    Возвращает путь кусочка (str) или "" если нечего рожать.
    """
    name = _safe_name(obj.get("Official_Name", ""))
    if name == "без_имени":
        return ""
    naznach = _safe_name(obj.get("Profession", "") or "без_предназначения")

    etazh = ZHITELI_DIR / naznach
    etazh.mkdir(parents=True, exist_ok=True)

    out = etazh / f"{name}.json"
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)
'''
    src = src.replace(anchor_func, new_func, 1)

    # ── ВСТАВКА 2: вызвать кусочек после save_catalog(catalog) в save_object ──
    # Якорь — строка записи кучи внутри save_object (отступ берём автоматически).
    save_line = None
    for ln in src.splitlines():
        if ln.strip() == 'save_catalog(catalog)' and ln.startswith(' ' * 8):
            save_line = ln
            break
    if save_line is None:
        fail("вызов save_catalog(catalog) внутри save_object не найден — покажи свежий")

    indent = save_line[:len(save_line) - len(save_line.lstrip())]
    kus_lines = [
        '',
        '# ── PATCH_DVA_FILA: второй файл — паспорт-кусочек на свой этаж ──',
        'try:',
        '    _kus = rodit_pasport_kusochek(obj)',
        '    if _kus:',
        '        ui.notify(f"Паспорт-кусочек: {_kus}", type="positive", timeout=4000)',
        'except Exception as _e:',
        '    ui.notify(f"⚠ кусочек не родился: {_e}", type="warning")',
    ]
    save_new = save_line + "\n" + "\n".join(
        (indent + kl) if kl else "" for kl in kus_lines
    )
    src = src.replace(save_line, save_new, 1)

    # ── ВСТАВКА 3: отключить generate_agent_files (папки-слои) ──
    # Это следующий шаг. Сейчас только паспорт, без памяти.
    # Глушим вызов: оборачиваем условие в False (отступ берём от строки).
    gaf_line = None
    for ln in src.splitlines():
        if ln.strip() == 'if obj.get("Object_Type_Class") == "agent":' and ln.startswith(' ' * 8):
            gaf_line = ln
            break
    if gaf_line is not None:
        g_indent = gaf_line[:len(gaf_line) - len(gaf_line.lstrip())]
        gaf_new = (
            g_indent + '# PATCH_DVA_FILA: папки-слои отключены — это СЛЕДУЮЩИЙ шаг.\n'
            + g_indent + '# Сейчас рождаем только паспорт (куча + кусочек). Памяти нет.\n'
            + g_indent + 'if False and obj.get("Object_Type_Class") == "agent":'
        )
        src = src.replace(gaf_line, gaf_new, 1)
        print("[ПАТЧ] ✓ generate_agent_files (папки-слои) отключён — следующий шаг")
    else:
        print("[ПАТЧ] ⚠ блок agent/generate_agent_files не найден — папки, возможно, уже не вызываются")

    # ── метка ──
    src = src.replace(
        '║  Студия «Шесть Пальцев»                                    ║',
        '║  Студия «Шесть Пальцев»                                    ║\n'
        f'║  {MARK} · куча + кусочек на свой этаж              ║',
        1,
    )
    if MARK not in src:
        # запасная метка
        src = MARK + "\n" + src

    TARGET.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✓ Два файла включены.")
    print("       • куча catalog.json — как была (НЕ трогаю)")
    print("       • кусочек → GRONDHEIM_CITY/жители/{предназначение}/{имя}.json")
    print("       • папки-слои отключены (следующий шаг)")
    print()
    print("[ПАТЧ] Проверка: роди Васю с Profession='трейдер' →")
    print("       появится GRONDHEIM_CITY/жители/трейдер/Вася.json рядом с кучей.")


if __name__ == "__main__":
    main()
