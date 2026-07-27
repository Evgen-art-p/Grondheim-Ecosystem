# PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1
"""
PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1 -- убирает разовый эфемерный разбор
картинки ПРИ ЗАГРУЗКЕ (был добавлен patch_akademia_vizual.py).

ПРОБЛЕМА (слово Шефа): загрузчик анализировал картинку сразу при
приёме, результат жил ОДИН ход чата (state["чат"] в памяти процесса,
ни к какому студенту не привязан) и исчезал бесследно. При этом
"📖 Прочитать" (patch_akademia_stol_chtenie.py) УЖЕ делает разбор
активным студентом и СОХРАНЯЕТ его в личную память (dvizhok,
kontekst="учёба") -- та же картинка разбиралась дважды, один раз
впустую.

РЕШЕНИЕ: загрузчик для изображения теперь ведёт себя как для текста --
просто принимает и кладёт на стол, без анализа. Анализ и сохранение --
только через "📖 Прочитать".

Требует: сначала patch_akademia_vizual.py, затем
patch_akademia_stol_chtenie.py -- этот патч исправляет то, что первый
из них добавил.

Идемпотентно: если маркер PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1 уже стоит
в файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_akademia_ruda_bez_analiza.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1'

OLD_HVOST = '''        if vid == "текст":
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"📄 Принял «{imya}» — лёг в руду на просев."})
            ui.notify(f"📄 Принято на просев: {imya}", type="positive")
            update_chat()
        else:
            # PATCH_AKADEMIA_VIZUAL_V1: реальный разбор вместо заглушки
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"🖼 Принял «{imya}» — смотрю…"})
            ui.notify(f"🖼 Принято: {imya} — смотрю...", type="info")
            update_chat()
            razbor = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")
            state["чат"][-1] = {"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                "content": f"🖼 «{imya}»: {razbor}"}
            ui.notify(f"🖼 разобрано: {imya}", type="positive")
            update_chat()'''

NOVYI_HVOST = '''        if vid == "текст":
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"📄 Принял «{imya}» — лёг в руду на просев."})
            ui.notify(f"📄 Принято на просев: {imya}", type="positive")
        else:
            # PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1: разбор при загрузке убран
            # -- жил один ход чата и дублировал то, что уже делает и
            # СОХРАНЯЕТ "📖 Прочитать" (личная память активного студента).
            # Стол только принимает, как и для текста.
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"🖼 Принял «{imya}» — лежит на столе, "
                                           f"разберёт тот, кто сядет читать."})
            ui.notify(f"🖼 Принято: {imya}", type="info")
        update_chat()'''

REPLACEMENTS = [
    (OLD_HVOST, NOVYI_HVOST),
]

REPLACE_ALL = [
]


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_ruda_bez_analiza")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
