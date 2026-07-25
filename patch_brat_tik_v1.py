# -*- coding: utf-8 -*-
# PATCH_BRAT_TIK_V1 — кнопка «Тик» в кабинете Брата
"""
Правит Брат/ui_brat.py: рядом с «Прописка» и «Роль» встаёт кнопка
«⏱ Тик» — суточный тик города прямо из кабинета.

ЛОГИКУ НЕ ДУБЛИРУЕМ. Кнопка зовёт сам tik.py — его же nayti_doma()
и его же Dvizhok. Один способ остужать город на весь Грондхейм;
консоль (python tik.py) остаётся рабочей ровно как была, это просто
вторая дверь к той же руке.

Отчёт уходит В ЧАТ, а не в правую панель: панель перерисовывается
таймером каждые 15 секунд и затёрла бы результат. Чат живёт.

Идемпотентно: маркер PATCH_BRAT_TIK_V1 — второй прогон молчит.
Бэкап перед правкой, ast.parse после — не сошлось, не пишем.

Запуск ИЗ КОРНЯ РЕПО:
    python patch_brat_tik_v1.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "Брат" / "ui_brat.py"
TIK = ROOT / "tik.py"

MARKER = "# PATCH_BRAT_TIK_V1"


# ── 1. Функция do_tik() — перед do_propiska() ────────────────
ANCHOR_FUNC = '''    async def do_propiska():
        """Брат связывает жителя и локацию: диалог житель → локация →
        домашний промпт → запись в паспорт жителя."""'''

BLOCK_FUNC = '''    # PATCH_BRAT_TIK_V1 — суточный тик из кабинета
    async def do_tik():
        """Город выдыхает. Та же рука, что `python tik.py`.

        Логику не повторяем: берём nayti_doma() и Dvizhok из самого
        tik.py. Меняется он — меняется и кнопка, расхождения не будет.
        Отчёт кладём в чат: правую панель затирает таймер.
        """
        import sys as _sys
        _root = str(Path(__file__).resolve().parent.parent)
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        try:
            import tik as _tik
        except Exception as ex:
            ui.notify(f"⚠ tik.py не поднялся: {ex}", color="negative")
            return

        try:
            doma = _tik.nayti_doma()
        except Exception as ex:
            ui.notify(f"⚠ жителей не обошёл: {ex}", color="negative")
            return
        if not doma:
            ui.notify("Жителей не нашёл — остужать некого", color="warning")
            return

        ui.notify(f"⏱ выдох города — {len(doma)} жител(ей)...", color="info")

        stroki = ["⏱ СУТОЧНЫЙ ТИК — город выдохнул", ""]
        stroki.append(f"{'житель':14s} {'было':>8s} {'стало':>8s} {'тишины':>9s}")
        stroki.append("─" * 45)

        dvinulos = 0
        for dom in doma:
            try:
                d = _tik.Dvizhok(dom)
            except Exception as ex:
                stroki.append(f"{dom.name[:14]:14s}  ⚠ {ex}")
                continue

            imya = d.p.get("Official_Name") or dom.name
            try:
                r = d.ostyt_po_vremeni()
            except Exception as ex:
                stroki.append(f"{str(imya)[:14]:14s}  ⚠ {ex}")
                continue

            if not r.get("остыл"):
                stroki.append(f"{str(imya)[:14]:14s} {r['было']:>+8.3f} "
                              f"{'—':>8s} {'—':>9s}  ({r.get('причина','')})")
                continue

            try:
                d.sохранить()      # осадка на диск — как в консоли
            except Exception as ex:
                stroki.append(f"{str(imya)[:14]:14s}  ⚠ не осело: {ex}")
                continue
            dvinulos += 1

            znak = ""
            if abs(r["было"]) > 0.8 and abs(r["стало"]) <= 0.8:
                znak = "  ← архив закрылся, отпустило"
            elif abs(r["стало"]) < 0.001:
                znak = "  ← покой"
            sutok = r["часов"] / 24.0
            stroki.append(f"{str(imya)[:14]:14s} {r['было']:>+8.3f} "
                          f"{r['стало']:>+8.3f} {sutok:>8.1f}д{znak}")

        stroki.append("─" * 45)
        stroki.append(f"выдохнули: {dvinulos} из {len(doma)}")
        if dvinulos == 0:
            stroki.append("")
            stroki.append("Время не шло — остужать нечего. Это не ошибка.")

        state["chat"].append({"role": "assistant",
                              "content": "\\n".join(stroki)})
        update_chat()
        ui.notify(f"⏱ выдохнули: {dvinulos} из {len(doma)}",
                  color="positive" if dvinulos else "info")

    async def do_propiska():
        """Брат связывает жителя и локацию: диалог житель → локация →
        домашний промпт → запись в паспорт жителя."""'''


# ── 2. Кнопка в шапке — перед «Прописка» ─────────────────────
ANCHOR_BTN = '''                ui.button("Прописка",
                          on_click=do_propiska  # PATCH_PROPISKA_BRAT
                          ).props("flat no-caps").style('''

BLOCK_BTN = '''                ui.button("⏱ Тик",
                          on_click=do_tik  # PATCH_BRAT_TIK_V1
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(80,200,140,0.15),rgba(80,200,140,0.08)); "
                    "border:1px solid rgba(80,200,140,0.35); color:#fff;")
                ui.button("Прописка",
                          on_click=do_propiska  # PATCH_PROPISKA_BRAT
                          ).props("flat no-caps").style('''


def main():
    print("═══ PATCH_BRAT_TIK_V1 ═══")
    print(f"корень: {ROOT}\n")

    if not TARGET.exists():
        print(f"✗ {TARGET} не найден. Запускай ИЗ КОРНЯ репо.")
        return False
    if not TIK.exists():
        print(f"⚠ {TIK} не найден — кнопка встанет, но нажимать нечего.")

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("= патч уже накатан")
        return True

    novyy = src
    for imya, ank, blok in (
        ("функция do_tik()", ANCHOR_FUNC, BLOCK_FUNC),
        ("кнопка в шапке", ANCHOR_BTN, BLOCK_BTN),
    ):
        if ank not in novyy:
            print(f"✗ якорь не найден: {imya}")
            print("  Файл ui_brat.py менялся — правь вручную.")
            return False
        novyy = novyy.replace(ank, blok, 1)
        print(f"✓ {imya}")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки файл не парсится: {e}")
        print("ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_tik")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"✓ бэкап: {bak.name}")
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
        print("✅ ГОТОВО. В кабинете Брата, рядом с «Прописка» — «⏱ Тик».")
        print("   Отчёт падает в чат. Консоль `python tik.py` работает как была.")
    else:
        print("❌ Не докатилось — смотри выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
