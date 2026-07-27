# PATCH_ARKHIV_KATALOG_PERSIST_V1
"""
PATCH_ARKHIV_KATALOG_PERSIST_V1 -- разбор изображения больше не живёт
один ход чата. Раньше (patch_arkhiv_vizual.py): картинка анализируется,
результат виден в чате и исчезает бесследно на следующем сообщении.

По образцу старой студии (`-2`, studio/workshop/ref_indexer.py):
vision-анализ картинки пишется ОДИН раз, но результат уходит не в
эфемерный чат, а в ПОСТОЯННЫЙ каталог (assets_catalog.json там,
Архив/архив/каталог.json здесь). Дальше запись находится через
nayti_zapisi() в любом будущем разговоре с Хранителем — не забывается.

Помечается статусом "черновик" -- автомат не решает вместо Хранителя,
он видит и правит запись руками, как и раньше для текста (Закон
Архива: своё решение важнее автоматической галочки).

Требует: сначала patch_arkhiv_vizual.py -- этот патч достраивает то,
что первый добавил (использует уже существующий _analiz_kartinki).

Идемпотентно: если маркер PATCH_ARKHIV_KATALOG_PERSIST_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_arkhiv_katalog_persist.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET_KHRANITEL = Path('Архив/khranitel_arkhiva.py')
TARGET_UI = Path('Архив/ui_arkhiv.py')
MARKER = 'PATCH_ARKHIV_KATALOG_PERSIST_V1'

OLD_NAYTI_TAIL = '''        out.append(z)
        if len(out) >= limit:
            break
    return out


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста. Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════'''

NOVYI_NAYTI_TAIL = '''        out.append(z)
        if len(out) >= limit:
            break
    return out


# PATCH_ARKHIV_KATALOG_PERSIST_V1: постоянная запись -- по образцу
# старой студии (ref_indexer.py): разбор изображения пишется в
# каталог один раз и остаётся там навсегда, а не живёт один ход чата.
def dobavit_v_katalog(zapis: dict) -> None:
    """Добавляет запись в каталог архива. Не подменяет решение
    Хранителя -- новые записи от загрузчика метятся статусом
    "черновик", Хранитель видит их и может поправить/убрать руками
    (Закон Архива: своё решение важнее автоматической галочки)."""
    _ARKHIV.mkdir(parents=True, exist_ok=True)
    kat = _read_json(_KATALOG, {"записи": []}) or {"записи": []}
    zapisi = kat.setdefault("записи", [])
    zapisi.append(zapis)
    _KATALOG.write_text(json.dumps(kat, ensure_ascii=False, indent=2),
                        encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста. Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════'''

OLD_HANDLE_RUDA_IMG = '''            razbor = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")
            state["чат"][-1] = {"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                "content": f"🖼 «{imya_f}»: {razbor} "
                                          f"(в архив не легло само — Хранитель решает руками)"}
            ui.notify(f"🖼 разобрано: {imya_f}", type="positive")
            update_chat()'''

NOVYI_HANDLE_RUDA_IMG = '''            razbor = await _analiz_kartinki(
                dest, state.get("model"),
                "Опиши, что на изображении: структура, детали, текст если "
                "есть. Коротко и по делу, не выдумывай того, чего не видно.")
            # PATCH_ARKHIV_KATALOG_PERSIST_V1: разбор уходит в каталог
            # черновиком -- не только в чат, который забудется через ход.
            try:
                import khranitel_arkhiva as _khr2
                _khr2.dobavit_v_katalog({
                    "название": Path(imya_f).stem,
                    "раздел": "медиа",
                    "теги": ["автозагрузка", "изображение"],
                    "файл": f"изображения/{imya_f}",
                    "описание": razbor,
                    "статус": "черновик — принято автоматически, не проверено Хранителем",
                    "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                _zapisano = True
            except Exception:
                _zapisano = False
            _hvost = ("записано в каталог черновиком — Хранитель проверит"
                     if _zapisano else
                     "в архив не легло само — Хранитель решает руками")
            state["чат"][-1] = {"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                "content": f"🖼 «{imya_f}»: {razbor} ({_hvost})"}
            ui.notify(f"🖼 разобрано: {imya_f}", type="positive")
            update_chat()'''

OLD_SENO = '''            seno = " ".join([
                str(z.get("название", "")),
                str(z.get("раздел", "")),
                " ".join(z.get("теги", []) or []),
                str(z.get("файл", "")),
            ]).lower()'''

NOVYI_SENO = '''            # PATCH_ARKHIV_KATALOG_PERSIST_V1: описание тоже участвует в
            # поиске -- иначе разбор картинки (лежит именно там) никогда
            # не найдётся текстовым запросом.
            seno = " ".join([
                str(z.get("название", "")),
                str(z.get("раздел", "")),
                " ".join(z.get("теги", []) or []),
                str(z.get("файл", "")),
                str(z.get("описание", "")),
            ]).lower()'''

REPLACEMENTS_KHRANITEL = [
    (OLD_NAYTI_TAIL, NOVYI_NAYTI_TAIL),
    (OLD_SENO, NOVYI_SENO),
]

REPLACEMENTS_UI = [
    (OLD_HANDLE_RUDA_IMG, NOVYI_HANDLE_RUDA_IMG),
]


def _primenit(target: Path, marker: str, replacements: list, bak_suffix: str):
    if not target.exists():
        print(f"⚠ не найден {target} — запускай из корня репо")
        sys.exit(1)
    text = target.read_text(encoding="utf-8")
    if marker in text:
        print(f"✓ {marker} уже стоит в {target} — патч не нужен")
        return
    for old, new in replacements:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    bak = target.with_suffix(target.suffix + bak_suffix)
    if not bak.exists():
        bak.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {target} (бэкап: {bak})")


def main():
    _primenit(TARGET_KHRANITEL, MARKER, REPLACEMENTS_KHRANITEL, ".bak_katalog_persist")
    _primenit(TARGET_UI, MARKER, REPLACEMENTS_UI, ".bak_katalog_persist")


if __name__ == "__main__":
    main()
