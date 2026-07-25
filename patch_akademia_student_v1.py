# -*- coding: utf-8 -*-
# PATCH_AKADEMIA_STUDENT_V1 — «студент» в диалоге «Роль» Брата
"""
Правит Брат/ui_brat.py:

  1. TIPY получает четвёртый пункт: "студент".
  2. Рядом с naznachit_rol() заводится zapisat_studenta() — пишет
     тип "студент" в паспорт, активирует маску работы на Академию
     (Workshop_ID="Академия", Turbo_Role="студент"), и занимает
     первое свободное место (1..10) в
     GRONDHEIM_CITY/Академия/ученики.json — том же файле, что
     читает ui_akademia.py.
  3. Диалог «Роль»: если выбран тип "студент" — вместо полей
     Цех/Слот/Фраза спрашивает только курс (необязательно) и
     зовёт zapisat_studenta(). Остальные типы — как было, без
     изменений в поведении.

Идемпотентно: если "студент" уже в TIPY — второй прогон не трогает
файл. Бэкап перед правкой, ast.parse после — не сошлось, не пишем.

Запуск ИЗ КОРНЯ РЕПО:
    python patch_akademia_student_v1.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "Брат" / "ui_brat.py"

# ── 1. TIPY: добавляем студента ──────────────────────────────
ANCHOR_TIPY = '        TIPY = ["резидент", "хранитель", "воркер"]'
NEW_TIPY = '        TIPY = ["резидент", "хранитель", "воркер", "студент"]  # PATCH_AKADEMIA_STUDENT_V1'

# ── 2. Новые функции — вставляются после naznachit_rol() ───────
ANCHOR_FUNCS = '''        return True, "роль назначена"
    except Exception as e:
        return False, str(e)


OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")'''

BLOCK_FUNCS = '''        return True, "роль назначена"
    except Exception as e:
        return False, str(e)


# ── PATCH_AKADEMIA_STUDENT_V1 — Брат записывает жителя студентом ──
# Тип "студент" — не воркер (не садится в цех), а пришедший поучиться
# в Академию. Пишет тип в паспорт (та же рука, что naznachit_rol),
# активирует маску «работа» с Workshop_ID="Академия", и занимает
# первое свободное место в GRONDHEIM_CITY/Академия/ученики.json —
# том же файле, что читает кабинет Академии (Закон Картриджа: одна
# правда о местах, не два реестра).
AKADEMIA_MEST_VSEGO = 10
AKADEMIA_UCHENIKI = Path("GRONDHEIM_CITY/Академия/ученики.json")


def _akademia_ucheniki_chitat() -> dict:
    import json
    if not AKADEMIA_UCHENIKI.exists():
        return {"места": []}
    try:
        return json.loads(AKADEMIA_UCHENIKI.read_text(encoding="utf-8"))
    except Exception:
        return {"места": []}


def zapisat_studenta(zid: str, kurs: str = ""):
    """Пишет тип «студент», активирует маску работы на Академию,
    занимает первое свободное место (1..10). Полные 10 — честный
    отказ, не перезаписываем чужое место. Возвращает (успех, сообщение)."""
    p, dom = find_dom(zid)
    if p is None or dom is None:
        return False, "житель не найден"
    try:
        import json

        data = _akademia_ucheniki_chitat()
        zapisi = data.get("места", []) or []
        zanyato = {int(z.get("место", 0)) for z in zapisi
                  if str(z.get("место", "")).isdigit()}
        mesto = next((n for n in range(1, AKADEMIA_MEST_VSEGO + 1)
                     if n not in zanyato), None)
        if mesto is None:
            return False, "все 10 мест в Академии заняты"

        # ── тип в паспорт (та же рука, что naznachit_rol) ──
        passport_path = dom / "passport.json"
        p["тип"] = "студент"
        passport_path.write_text(
            json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

        # ── маска «работа» — Академия, не цех ──
        mask_path = dom / "маски" / "работа" / "mask.json"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        mask = {}
        if mask_path.exists():
            try:
                mask = json.loads(mask_path.read_text(encoding="utf-8"))
            except Exception:
                mask = {}
        mask["_note"] = ("маска 'работа' (слой 2 паспорта). "
                         "Активирована Братом — студент Академии.")
        mask["_активна"] = True
        mask["Workshop_ID"] = "Академия"
        mask["Turbo_Role"] = "студент"
        mask["Core_Phrase"] = mask.get("Core_Phrase", "")
        mask_path.write_text(
            json.dumps(mask, ensure_ascii=False, indent=2), encoding="utf-8")

        # ── место в Академии ──
        zapisi.append({
            "место": mesto,
            "житель": p.get("Official_Name", ""),
            "курс": kurs,
        })
        data["места"] = zapisi
        AKADEMIA_UCHENIKI.parent.mkdir(parents=True, exist_ok=True)
        AKADEMIA_UCHENIKI.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        return True, f"место {mesto}"
    except Exception as e:
        return False, str(e)


OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")'''

# ── 3. Диалог: ветка "студент" вместо Цех/Слот/Фраза ────────────
ANCHOR_DIALOG = '''                        ws = ui.input("Цех (Workshop_ID)").props("dark outlined").style(
                            "width:100%; font-size:0.8rem; margin-bottom:8px;")
                        role = ui.input("Слот роли (Turbo_Role)").props("dark outlined").style(
                            "width:100%; font-size:0.8rem; margin-bottom:8px;")
                        phrase = ui.input("Коронная фраза (Core_Phrase)").props(
                            "dark outlined").style("width:100%; font-size:0.8rem;")

                        async def _confirm():
                            ok, msg = naznachit_rol(
                                pick["zhitel"].get("ID_Object", ""),
                                pick["tip"],
                                (ws.value or "").strip(),
                                (role.value or "").strip(),
                                (phrase.value or "").strip(),
                            )
                            if ok:
                                ui.notify(f"⚙ {zn}: роль назначена ({pick['tip']})", color="positive")
                                dlg.close()
                            else:
                                ui.notify(f"⚠ {msg}", color="negative")'''

BLOCK_DIALOG = '''                        if pick["tip"] == "студент":
                            # PATCH_AKADEMIA_STUDENT_V1: студент — не цех,
                            # а Академия. Цех/слот/фраза здесь не нужны.
                            ui.html('<div style="color:rgba(255,255,255,0.45); font-size:0.68rem; '
                                    'margin-bottom:6px; text-transform:uppercase; letter-spacing:0.06em;">'
                                    'курс (необязательно)</div>')
                            kurs = ui.input("Курс").props("dark outlined").style(
                                "width:100%; font-size:0.8rem;")

                            async def _confirm():
                                ok, msg = zapisat_studenta(
                                    pick["zhitel"].get("ID_Object", ""),
                                    (kurs.value or "").strip(),
                                )
                                if ok:
                                    ui.notify(f"🎓 {zn}: записан(а) в Академию ({msg})", color="positive")
                                    dlg.close()
                                else:
                                    ui.notify(f"⚠ {msg}", color="negative")
                        else:
                            ws = ui.input("Цех (Workshop_ID)").props("dark outlined").style(
                                "width:100%; font-size:0.8rem; margin-bottom:8px;")
                            role = ui.input("Слот роли (Turbo_Role)").props("dark outlined").style(
                                "width:100%; font-size:0.8rem; margin-bottom:8px;")
                            phrase = ui.input("Коронная фраза (Core_Phrase)").props(
                                "dark outlined").style("width:100%; font-size:0.8rem;")

                            async def _confirm():
                                ok, msg = naznachit_rol(
                                    pick["zhitel"].get("ID_Object", ""),
                                    pick["tip"],
                                    (ws.value or "").strip(),
                                    (role.value or "").strip(),
                                    (phrase.value or "").strip(),
                                )
                                if ok:
                                    ui.notify(f"⚙ {zn}: роль назначена ({pick['tip']})", color="positive")
                                    dlg.close()
                                else:
                                    ui.notify(f"⚠ {msg}", color="negative")'''


def main():
    print("═══ PATCH_AKADEMIA_STUDENT_V1 ═══")
    print(f"корень: {ROOT}\n")

    if not TARGET.exists():
        print(f"✗ {TARGET} не найден. Запускай ИЗ КОРНЯ репо.")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if 'zapisat_studenta' in src:
        print("= патч уже накатан — zapisat_studenta уже в файле")
        return True

    novyy = src
    izmeneno = []

    if ANCHOR_TIPY not in novyy:
        print("✗ якорь TIPY не найден — файл менялся, правь вручную.")
        return False
    novyy = novyy.replace(ANCHOR_TIPY, NEW_TIPY, 1)
    izmeneno.append("TIPY += студент")

    if ANCHOR_FUNCS not in novyy:
        print("✗ якорь для вставки функций не найден.")
        return False
    novyy = novyy.replace(ANCHOR_FUNCS, BLOCK_FUNCS, 1)
    izmeneno.append("zapisat_studenta()")

    if ANCHOR_DIALOG not in novyy:
        print("✗ якорь диалога не найден.")
        return False
    novyy = novyy.replace(ANCHOR_DIALOG, BLOCK_DIALOG, 1)
    izmeneno.append("ветка диалога «студент»")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки файл не парсится: {e}")
        print("ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_akademia_student")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"✓ бэкап: {bak.name}")
    print(f"✓ правки: {', '.join(izmeneno)}")
    return True


if __name__ == "__main__":
    ok = main()
    print()
    if ok:
        print("✅ ГОТОВО. В кабинете Брата -> «Роль» -> «студент» — привязка к Академии.")
    else:
        print("❌ Не докатилось — смотри сообщения выше.")
    print("`шесть·проверено·до·корня`")
