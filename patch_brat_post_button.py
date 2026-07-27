# PATCH_NAZNACHIT_POST_V1
"""
PATCH_NAZNACHIT_POST_V1 -- новая дверь в кабинете Брата: кнопка «Пост»
рядом с «Роль». Сажает резидента на пост (библиотекарь/хранитель_
архива/ректор/будущие) через rezidenty.posadit() -- список постов
читается живым сканом GRONDHEIM_CITY/посты/, ничего не хардкожено.
Раньше такой двери не было вообще -- «Роль» это другой, несвязанный
механизм (Workshop_ID/Turbo_Role в mask.json, Закон Пары для Биржи).

Идемпотентно: если маркер PATCH_NAZNACHIT_POST_V1 уже стоит в файле — патч
молча выходит, повторно не наложится. Бэкап .bak делается один раз,
при первом применении.

Запуск из корня репо:  python patch_brat_post_button.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Брат/ui_brat.py')
MARKER = 'PATCH_NAZNACHIT_POST_V1'

REPLACEMENTS = [
    ('def zapisat_studenta(zid: str, kurs: str = ""):', '# PATCH_NAZNACHIT_POST_V1 -- Брат сажает резидента на ПОСТ (не Закон Пары,\n# а rezidenty.py: библиотекарь / хранитель_архива / ректор / другие\n# посты, что заведут себе цеха сканом папки GRONDHEIM_CITY/посты/).\n# Это ДРУГОЙ акт, чем «Роль» выше: «Роль» -- Workshop_ID/Turbo_Role в\n# mask.json самого жителя (Закон Пары, Биржа-стиль воркеров). Пост --\n# отдельный файл-связка в GRONDHEIM_CITY/посты/{id}/хранитель.json,\n# личность и роль развязаны законом rezidenty.py. Раньше в кабинете\n# Брата двери на посты не было вообще -- сажали руками через код.\ndef list_posty_dlya_ui() -> list:\n    """Все посты города -- как их видит менеджер резидентов. Пусто --\n    честный список, ни одного поста ещё не заведено."""\n    try:\n        import rezidenty\n        return rezidenty.list_posty()\n    except Exception:\n        return []\n\n\ndef naznachit_post(zid: str, post_id: str):\n    """Сажает жителя на пост через rezidenty.posadit(). Не проверяет\n    род/тип -- закон rezidenty.py: любой резидент может занять любой\n    пост, если Брат его туда посадил. Возвращает (успех, сообщение)."""\n    p, dom = find_dom(zid)\n    if p is None or dom is None:\n        return False, "житель не найден"\n    imya = p.get("Official_Name", "")\n    if not imya:\n        return False, "у жителя нет имени -- не могу посадить"\n    try:\n        import rezidenty\n        return rezidenty.posadit(post_id, imya, zid)\n    except Exception as e:\n        return False, str(e)\n\n\ndef zapisat_studenta(zid: str, kurs: str = ""):'),
    ('    async def do_naznachit_rol():', '    async def do_naznachit_post():\n        """Брат сажает жителя на ПОСТ (библиотекарь/хранитель_архива/\n        ректор/...) -- сканирует GRONDHEIM_CITY/посты/ живьём, ничего\n        не хардкодит (Закон Картриджа): новый пост появится сам, как\n        только кто-то заведёт его папку."""\n        zhiteli = list_zhiteli()\n        if not zhiteli:\n            ui.notify("Жителей ещё нет -- роди их в Странице Жизни", color="warning")\n            return\n        posty = list_posty_dlya_ui()\n        if not posty:\n            ui.notify("Постов в городе ещё нет -- ни один цех их не завёл", color="warning")\n            return\n\n        pick: dict = {"zhitel": None}\n\n        with ui.dialog() as dlg, ui.card().style(\n            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "\n            "border-radius:16px; min-width:380px; max-width:460px; padding:20px;"\n        ):\n            body = ui.element("div")\n\n            def render():\n                body.clear()\n                with body:\n                    if pick["zhitel"] is None:\n                        ui.html(\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n                                \'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n                                \'🪑 ПОСТ · кого сажаем?</div>\')\n                        for z in zhiteli:\n                            nm = z.get("Official_Name", "?")\n                            def _pick_z(z=z):\n                                pick["zhitel"] = z\n                                render()\n                            ui.button(nm, on_click=_pick_z).props("flat no-caps").style(\n                                "width:100%; text-align:left; font-family:monospace; "\n                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n                                "padding:8px 12px; border-radius:8px; "\n                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n                        ui.button("отмена", on_click=dlg.close).props("flat").style(\n                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n                    else:\n                        zn = pick["zhitel"].get("Official_Name", "?")\n                        ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n                                f\'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n                                f\'🪑 {zn} → на какой пост?</div>\')\n                        for post in posty:\n                            zanyat = post.get("занят")\n                            kto = post.get("житель", "")\n                            sub = f" · сейчас: {kto}" if zanyat else " · вакансия"\n                            def _confirm(post_id=post["id"], nazvanie=post["название"], sub=sub):\n                                ok, msg = naznachit_post(pick["zhitel"].get("ID_Object", ""), post_id)\n                                if ok:\n                                    ui.notify(f"🪑 {zn} → {nazvanie} ({msg})", color="positive")\n                                    dlg.close()\n                                else:\n                                    ui.notify(f"⚠ {msg}", color="negative")\n                            ui.button(post["название"] + sub, on_click=_confirm).props("flat no-caps").style(\n                                "width:100%; text-align:left; font-family:monospace; "\n                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n                                "padding:8px 12px; border-radius:8px; "\n                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n                        def _back_z():\n                            pick["zhitel"] = None\n                            render()\n                        ui.button("← назад", on_click=_back_z).props("flat").style(\n                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n\n            render()\n        dlg.open()\n\n    async def do_naznachit_rol():'),
    ('                ui.button("Роль",\n                          on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL\n                          ).props("flat no-caps").style(\n                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n                    "background:linear-gradient(135deg,rgba(120,168,201,0.15),rgba(120,168,201,0.08)); "\n                    "border:1px solid rgba(120,168,201,0.35); color:#fff;")', '                ui.button("Роль",\n                          on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL\n                          ).props("flat no-caps").style(\n                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n                    "background:linear-gradient(135deg,rgba(120,168,201,0.15),rgba(120,168,201,0.08)); "\n                    "border:1px solid rgba(120,168,201,0.35); color:#fff;")\n                ui.button("Пост",\n                          on_click=do_naznachit_post  # PATCH_NAZNACHIT_POST_V1\n                          ).props("flat no-caps").style(\n                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "\n                    "background:linear-gradient(135deg,rgba(189,0,255,0.15),rgba(189,0,255,0.08)); "\n                    "border:1px solid rgba(189,0,255,0.35); color:#fff;")'),
]

# REPLACE_ALL — можно встречаться много раз, меняем ВСЕ вхождения
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
    bak = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")

if __name__ == "__main__":
    main()

# PATCH_NAZNACHIT_POST_V1 — маркер идемпотентности