# PATCH_REKTOR_STOL_OTCHETY_V1
"""
PATCH_REKTOR_STOL_OTCHETY_V1 -- три правки кабинета Ректора:

  1. Стол (стейдж) раздёлен на чат + отчёты, как везде в городе
     (жители/Академия/Архив: split-view с chat-log и viewer рядом).
     Раньше в столе был ТОЛЬКО чат -- карточка кандидата жила в левой
     колонке отдельно, без пары "чат слева, отчёты справа".
  2. В новые "отчёты" пока идёт то же самое, что Ректор и так видит
     про кандидата (место/курс/оценки/экзамены/диплом) -- update_viewer()
     теперь пишет в ОБА места (левая карточка + новый стол-viewer),
     один источник правды, не два.
  3. Чёрный текст слева под "КАНДИДАТ" (ui.markdown без цвета -- полз
     чёрным по тёмному стеклу) -- явный белый цвет на обоих панелях.

Идемпотентно: если маркер PATCH_REKTOR_STOL_OTCHETY_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_rektor_stol_otchety.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_rektor.py')
MARKER = 'PATCH_REKTOR_STOL_OTCHETY_V1'

OLD_REFS = '''    avatar_ref = {"element": None}
    vitals_ref = {"element": None}'''

NEW_REFS = '''    avatar_ref = {"element": None}
    vitals_ref = {"element": None}
    stage_viewer_ref = {"element": None}  # PATCH_REKTOR_STOL_OTCHETY_V1'''

OLD_UPDATE_VIEWER = '''    def update_viewer():
        if not viewer_ref["element"]:
            return
        viewer_ref["element"].clear()
        with viewer_ref["element"]:
            if not kandidat_imya:
                ui.markdown("*Открой кабинет через кнопку «Учёба» в кабинете жителя.*")
                return
            zap = _rek.najti_zapis(kandidat_imya)
            md = ""
            if zap:
                md += f"**Место:** {zap.get('место','—')} · **Курс:** {zap.get('курс') or '—'}\\n\\n"
                otsenki = zap.get("оценки", [])
                md += "**Оценки:** " + (", ".join(
                    f"{o['предмет']}: {o['оценка']}" for o in otsenki) or "нет") + "\\n\\n"
                ekz = zap.get("экзамены", [])
                md += "**Экзамены:** " + (", ".join(
                    f"{e['предмет']}: {e['результат']}" for e in ekz) or "нет") + "\\n\\n"
                dip = zap.get("диплом")
                md += f"**Диплом:** {dip['профессия'] if dip else 'не выдан'}\\n"
            else:
                md += "*Пока не студент(ка) — кандидат(ка) на собеседовании.*\\n"
            ui.markdown(md)'''

NEW_UPDATE_VIEWER = '''    def update_viewer():
        # PATCH_REKTOR_STOL_OTCHETY_V1: один источник правды -- пишем
        # в ОБА места (карточка слева + отчёты в столе), не дублируем
        # логику расчёта md.
        if not kandidat_imya:
            md = "*Открой кабинет через кнопку «Учёба» в кабинете жителя.*"
        else:
            zap = _rek.najti_zapis(kandidat_imya)
            md = ""
            if zap:
                md += f"**Место:** {zap.get('место','—')} · **Курс:** {zap.get('курс') or '—'}\\n\\n"
                otsenki = zap.get("оценки", [])
                md += "**Оценки:** " + (", ".join(
                    f"{o['предмет']}: {o['оценка']}" for o in otsenki) or "нет") + "\\n\\n"
                ekz = zap.get("экзамены", [])
                md += "**Экзамены:** " + (", ".join(
                    f"{e['предмет']}: {e['результат']}" for e in ekz) or "нет") + "\\n\\n"
                dip = zap.get("диплом")
                md += f"**Диплом:** {dip['профессия'] if dip else 'не выдан'}\\n"
            else:
                md += "*Пока не студент(ка) — кандидат(ка) на собеседовании.*\\n"
        for _ref in (viewer_ref, stage_viewer_ref):
            el = _ref.get("element")
            if not el:
                continue
            el.clear()
            with el:
                ui.markdown(md)'''

OLD_LEFT_VIEWER = '''                    with ui.element("div").style("padding:6px 14px 14px 14px;"):
                        viewer_ref["element"] = ui.element("div")'''

NEW_LEFT_VIEWER = '''                    with ui.element("div").style("padding:6px 14px 14px 14px;"):
                        # PATCH_REKTOR_STOL_OTCHETY_V1: явный белый цвет --
                        # markdown без стиля рисовался чёрным по тёмному стеклу
                        viewer_ref["element"] = ui.element("div").style(
                            "color: rgba(255,255,255,0.86); font-size:0.82rem; line-height:1.5;")'''

OLD_STAGE_SPLIT = '''                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        chat_ref["element"] = ui.element("div").classes("chat-log")
                        with chat_ref["element"]:
                            ui.html('<div class="chat-msg-system">SYSTEM: кликни по пузырьку Ректора.</div>')'''

NEW_STAGE_SPLIT = '''                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        chat_ref["element"] = ui.element("div").classes("chat-log")
                        with chat_ref["element"]:
                            ui.html('<div class="chat-msg-system">SYSTEM: кликни по пузырьку Ректора.</div>')
                        # PATCH_REKTOR_STOL_OTCHETY_V1: отчёты рядом с чатом,
                        # как везде в городе (жители/Академия/Архив)
                        stage_viewer_ref["element"] = ui.element("div").classes("viewer")'''

REPLACEMENTS = [
    (OLD_REFS, NEW_REFS),
    (OLD_UPDATE_VIEWER, NEW_UPDATE_VIEWER),
    (OLD_LEFT_VIEWER, NEW_LEFT_VIEWER),
    (OLD_STAGE_SPLIT, NEW_STAGE_SPLIT),
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_stol_otchety")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
