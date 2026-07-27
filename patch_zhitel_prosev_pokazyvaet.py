# PATCH_ZHITEL_PROSEV_POKAZYVAET_V1
"""
PATCH_ZHITEL_PROSEV_POKAZYVAET_V1 -- видимость того, что именно ушло
в "🪞 Осмыслить". Раньше: список моментов (sobrat_dlya_proseva) шёл
ТОЛЬКО в промпт LLM -- Шеф видел только финальный вывод, но не мог
понять, какие факты его породили (в том числе была ли среди них
картинка). Теперь: список показывается в чате ДО вызова модели, с
иконкой 🖼/📄, чтобы отличить изображение от текста.

Не меняет сам механизм просева (dvizhok.sobrat_dlya_proseva/dopisat_vyvod
не трогаем) -- только делает видимым то, что уже происходило внутри.

Идемпотентно: если маркер PATCH_ZHITEL_PROSEV_POKAZYVAET_V1 уже стоит
в файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_zhitel_prosev_pokazyvaet.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('жители/ui_zhitel.py')
MARKER = 'PATCH_ZHITEL_PROSEV_POKAZYVAET_V1'

OLD_BLOK = '''        momenty = _dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify("пока накопилось мало — рано осмыслять", color="warning")
            return
        state["waiting"] = True
        ui.notify(f"🪞 {name} осмысляет {len(momenty)} момент(ов)", color="info")
        spisok = "\\n".join(f"— [{m['тонус']}] {m['факт']}" for m in momenty)'''

NOVYI_BLOK = '''        momenty = _dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify("пока накопилось мало — рано осмыслять", color="warning")
            return
        state["waiting"] = True
        ui.notify(f"🪞 {name} осмысляет {len(momenty)} момент(ов)", color="info")
        spisok = "\\n".join(f"— [{m['тонус']}] {m['факт']}" for m in momenty)
        # PATCH_ZHITEL_PROSEV_POKAZYVAET_V1: видимость -- Шеф видит, ЧТО
        # именно ушло в осмысление, до самого вывода. Иконка отличает
        # изображение от текста по расширению файла в самом факте.
        _KARTINKA_ZNAKI = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        def _ikonka(fakt: str) -> str:
            return "🖼" if any(e in fakt.lower() for e in _KARTINKA_ZNAKI) else "📄"
        _spisok_pokaz = "\\n".join(
            f"{_ikonka(m['факт'])} [{m['тонус']}] {m['факт'][:100]}" for m in momenty)
        state["chat"].append({"role": "zhitel",
                              "content": f"🪞 Осмысляю по этим моментам:\\n{_spisok_pokaz}"})
        update_chat()'''

REPLACEMENTS = [
    (OLD_BLOK, NOVYI_BLOK),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_prosev_pokaz")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
