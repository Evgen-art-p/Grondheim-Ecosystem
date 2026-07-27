# -*- coding: utf-8 -*-
# PATCH_POST_CHEREZ_ROL_V1
"""
PATCH_POST_CHEREZ_ROL_V1 — одна дверь вместо двух.

Раньше (patch_brat_post_button.py) я добавил отдельную кнопку «Пост»
рядом с «Ролью» — Шеф сказал: костыль, убери, пусть будет одна дверь
(«Роль»), а библиотекарь/архив/ректор просто добавятся в список типов.

Этот патч:
  1) если кнопка «Пост» уже накачена (PATCH_NAZNACHIT_POST_V1) — тихо
     снимает её (функции + диалог + кнопку), возвращая файл к тому
     виду, как будто её и не было;
  2) добавляет три новых типа в список «Роль»: библиотекарь,
     хранитель_архива, ректор. Выбрал такой тип — полей Цех/Слот/
     Фраза НЕ будет (это же не Закон Пары), только подтверждение.
     Пост заводится сам, если ещё не заведён цехом.

Идемпотентно: если PATCH_POST_CHEREZ_ROL_V1 уже стоит — выходит,
второй раз не наложится. Работает и с накаченной кнопкой «Пост»,
и без неё (если patch_brat_post_button.py не запускали вовсе).

Запуск из корня репо:  python patch_post_cherez_rol_v1.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path("Брат/ui_brat.py")
MARKER_NEW = "PATCH_POST_CHEREZ_ROL_V1"
MARKER_OLD_BUTTON = "PATCH_NAZNACHIT_POST_V1"

# ── точные блоки старого патча (кнопка "Пост") — для отката ──────
_OLD_FUNCS_ANCHOR_END = 'def zapisat_studenta(zid: str, kurs: str = ""):'
_OLD_FUNCS_START_MARK = '# PATCH_NAZNACHIT_POST_V1 -- Брат сажает резидента на ПОСТ'
_OLD_FUNCS_START_MARK_EMDASH = '# PATCH_NAZNACHIT_POST_V1 — Брат сажает резидента на ПОСТ'

_OLD_DIALOG_START_MARK = '    async def do_naznachit_post():'
_OLD_DIALOG_ANCHOR_END = '    async def do_naznachit_rol():'

_OLD_BUTTON_START_MARK = '                ui.button("Пост",'
_OLD_BUTTON_ANCHOR_END = '                ui.button("Страница Жизни",'


def _otkatit_knopku_post(text: str) -> str:
    """Убирает кнопку «Пост» (если она есть) — функции, диалог, саму
    кнопку. Возвращает текст без них (или тем же, если и не было)."""
    for start_mark in (_OLD_FUNCS_START_MARK, _OLD_FUNCS_START_MARK_EMDASH):
        if start_mark in text and _OLD_FUNCS_ANCHOR_END in text:
            i0 = text.index(start_mark)
            i1 = text.index(_OLD_FUNCS_ANCHOR_END, i0)
            text = text[:i0] + text[i1:]
            break

    if _OLD_DIALOG_START_MARK in text and _OLD_DIALOG_ANCHOR_END in text:
        i0 = text.index(_OLD_DIALOG_START_MARK)
        i1 = text.index(_OLD_DIALOG_ANCHOR_END, i0)
        text = text[:i0] + text[i1:]

    if _OLD_BUTTON_START_MARK in text and _OLD_BUTTON_ANCHOR_END in text:
        i0 = text.index(_OLD_BUTTON_START_MARK)
        i1 = text.index(_OLD_BUTTON_ANCHOR_END, i0)
        text = text[:i0] + text[i1:]

    return text


# ── новая интеграция в диалог "Роль" ──────────────────────────────
_OLD_TIPY = 'TIPY = ["резидент", "хранитель", "воркер", "студент"]  # PATCH_AKADEMIA_STUDENT_V1'
_NEW_TIPY = '''TIPY = ["резидент", "хранитель", "воркер", "студент",
                "библиотекарь", "хранитель_архива", "ректор"]  # PATCH_AKADEMIA_STUDENT_V1 + PATCH_POST_CHEREZ_ROL_V1
        # PATCH_POST_CHEREZ_ROL_V1: тип -> id поста в rezidenty.py.
        # Библиотекарь/Архив/Ректор — это ПОСТЫ (GRONDHEIM_CITY/посты/),
        # не Закон Пары. Выбрал такой тип — полей Цех/Слот/Фраза не
        # будет, посадка идёт сразу, одним кликом «назначить».
        TIP_TO_POST = {
            "библиотекарь": "bibliotekar",
            "хранитель_архива": "khranitel_arkhiva",
            "ректор": "rektor",
        }'''

_OLD_ELSE = '''                        else:
                            ws = ui.input("Цех (Workshop_ID)").props("dark outlined").style('''
_NEW_ELIF_ELSE = '''                        elif pick["tip"] in TIP_TO_POST:
                            # PATCH_POST_CHEREZ_ROL_V1: пост -- полей нет,
                            # только подтверждение. Личность и роль
                            # развязаны (закон rezidenty.py), Брат просто
                            # сажает жителя на готовый пост.
                            _post_id = TIP_TO_POST[pick["tip"]]
                            _post_info = next((p2 for p2 in list_posty_dlya_ui()
                                              if p2["id"] == _post_id), None)
                            if _post_info and _post_info.get("занят"):
                                ui.html(f'<div style="color:rgba(255,180,60,0.85); font-size:0.75rem; '
                                        f'margin-bottom:10px;">Сейчас на посту: '
                                        f'{_post_info.get("житель","?")} -- назначишь, сменит(ся).</div>')
                            else:
                                ui.html('<div style="color:rgba(255,255,255,0.45); font-size:0.75rem; '
                                        'margin-bottom:10px;">Пост свободен -- полей заполнять не надо, '
                                        'просто подтверди.</div>')

                            async def _confirm():
                                ok, msg = naznachit_post_iz_roli(
                                    pick["zhitel"].get("ID_Object", ""),
                                    _post_id, pick["tip"])
                                if ok:
                                    ui.notify(f"🪑 {zn}: {msg}", color="positive")
                                    dlg.close()
                                else:
                                    ui.notify(f"⚠ {msg}", color="negative")
                        else:
                            ws = ui.input("Цех (Workshop_ID)").props("dark outlined").style('''

_OLD_TAIL = '''        return True, "роль назначена"
    except Exception as e:
        return False, str(e)'''
_NEW_TAIL = '''        return True, "роль назначена"
    except Exception as e:
        return False, str(e)


# PATCH_POST_CHEREZ_ROL_V1 -- та же дверь «Роль», но для ПОСТОВ
# (библиотекарь/хранитель_архива/ректор). Это не Закон Пары -- пост
# живёт в GRONDHEIM_CITY/посты/{id}/хранитель.json, отдельно от
# mask.json жителя. Тип в паспорт пишем для вида в списке жителей
# (та же рука, что naznachit_rol/zapisat_studenta), а само место --
# rezidenty.posadit().
def naznachit_post_iz_roli(zid: str, post_id: str, tip_label: str):
    """Сажает жителя на пост через rezidenty.posadit(). Пост ещё не
    заведён цехом (Академия/Архив ни разу не открывались) -- заводим
    сами, вакансией, чтобы не блокировать назначение порядком открытия
    кабинетов. Возвращает (успех: bool, сообщение: str)."""
    p, dom = find_dom(zid)
    if p is None or dom is None:
        return False, "житель не найден"
    imya = p.get("Official_Name", "")
    if not imya:
        return False, "у жителя нет имени -- не могу посадить"
    try:
        import json
        import rezidenty
        if not rezidenty.get_post(post_id):
            rezidenty.zavesti_post(post_id, tip_label.replace("_", " ").capitalize())
        ok, msg = rezidenty.posadit(post_id, imya, zid)
        if ok:
            passport_path = dom / "passport.json"
            p["тип"] = tip_label
            passport_path.write_text(
                json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        return ok, msg
    except Exception as e:
        return False, str(e)


def list_posty_dlya_ui() -> list:
    """Все посты города -- нужно новой ветке "Роли", чтобы показать,
    свободен пост или занят. Пусто -- ни одного поста не заведено."""
    try:
        import rezidenty
        return rezidenty.list_posty()
    except Exception:
        return []'''


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER_NEW in text:
        print(f"✓ {MARKER_NEW} уже стоит в {TARGET} — патч не нужен")
        return

    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")

    if MARKER_OLD_BUTTON in text:
        text = _otkatit_knopku_post(text)
        print("✓ кнопка «Пост» снята")
    else:
        print("· кнопки «Пост» и не было — пропускаю откат")

    if _OLD_TIPY not in text:
        print("⚠ не нашёл список TIPY — структура файла изменилась с момента патча")
        sys.exit(1)
    text = text.replace(_OLD_TIPY, _NEW_TIPY, 1)

    if _OLD_ELSE not in text:
        print("⚠ не нашёл ветку else (Цех/Слот/Фраза) — структура изменилась")
        sys.exit(1)
    text = text.replace(_OLD_ELSE, _NEW_ELIF_ELSE, 1)

    if _OLD_TAIL not in text:
        print("⚠ не нашёл конец naznachit_rol() — структура изменилась")
        sys.exit(1)
    text = text.replace(_OLD_TAIL, _NEW_TAIL, 1)

    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")
    print(f"# {MARKER_NEW}")


if __name__ == "__main__":
    main()

# PATCH_POST_CHEREZ_ROL_V1 — маркер идемпотентности
