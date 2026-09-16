# -*- coding: utf-8 -*-
# POSTAVIT_KNOPKU_DUSHA_V1
"""
ПАТЧ: кнопка «❄ Душ» в кабинете Брата, рядом с Тиком.

Запускать из КОРНЯ РЕПО:
    python postavit_knopku_dusha.py

СЛОВО ШЕФА (16.09)
    «Кнопку у Брата сделай, рядом с кнопкой "тик". Она всех — это
    просто один тик жизни. А ему холодный душ нужен.»

ЧЕМ ДУШ ОТЛИЧАЕТСЯ ОТ ТИКА
    Тик — выдох ВСЕГО города: сутки прошли, все чуть остыли по времени.
    Душ — адресный: одного, сейчас, до ровного. Тик про время, душ про
    состояние.

ЧТО ДЕЛАЕТ
    Открывает список жителей с зарядом, состоянием и температурой
    головы. У кого перекос крайний — 🔥. Жмёшь по строке — льётся вода,
    и рядом же видно, что было и что стало.

ГДЕ ЛОГИКА
    В жители/ostudit.py. Кнопка её только зовёт — как кнопка Тик зовёт
    tik.py. Меняется остужалка — меняется и кнопка, расхождения не
    будет.

ТРЕБУЕТ
    Файл жители/ostudit.py на месте. Нет — патч честно откажется.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_dush, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# KNOPKA_DUSHA_V1"


def _nayti_brata():
    kand = [p for p in _KOREN.rglob("ui_brat.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_brat.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


# ── 1. сама рука ────────────────────────────────────────────
STARO_1 = '''    async def do_tik():'''

NOVO_1 = '''    async def do_dush():
        """KNOPKA_DUSHA_V1: холодный душ ОДНОМУ жителю.

        Тик — выдох всего города по времени. Душ — адресный и сильный:
        одного, сейчас, до ровного. Логику не повторяем: берём
        жители/ostudit.py, как Тик берёт tik.py.

        Зачем: заряд идёт и в промпт словами, и в ТЕМПЕРАТУРУ модели.
        Придавленный житель не смотрит, а сочиняет.
        """
        import sys as _sys
        _zh = str(Path(__file__).resolve().parent.parent / "жители")
        if _zh not in _sys.path:
            _sys.path.insert(0, _zh)
        try:
            import ostudit as _ost
        except Exception as ex:
            ui.notify(f"⚠ остужалка не поднялась: {ex}", color="negative")
            return

        try:
            lyudi = _ost.spisok()
        except Exception as ex:
            ui.notify(f"⚠ жителей не обошёл: {ex}", color="negative")
            return
        if not lyudi:
            ui.notify("Жителей не нашёл — остужать некого", color="warning")
            return

        dlg = ui.dialog()
        with dlg, ui.card().style(
                "background:#0e1420; border:1px solid rgba(255,255,255,0.12); "
                "min-width:520px; max-width:92vw;"):
            ui.html('<div style="color:#8fd3ff;font-size:13px;'
                    'letter-spacing:.14em;padding:2px 0 8px 0;">'
                    '❄ ХОЛОДНЫЙ ДУШ · кого остудить</div>')
            ui.html('<div style="color:rgba(255,255,255,0.40);font-size:10px;'
                    'line-height:1.6;padding-bottom:8px;">'
                    'Тик — выдох всего города по времени. Душ — один '
                    'житель, сейчас, до ровного.<br>Память, выводы и '
                    'якоря не трогаются.</div>')

            spisok_box = ui.column().style("width:100%; gap:4px;")

            def narisovat():
                spisok_box.clear()
                with spisok_box:
                    for ch in lyudi:
                        z = ch["заряд"]
                        cvet = ("#ff5c5c" if ch["крайний"]
                                else "#ffd24a" if abs(z) > 0.3
                                else "#3ddc6b")
                        ogon = " 🔥" if ch["крайний"] else ""

                        def _lit(c=ch):
                            r = _ost.ostudit(c["дом"])
                            if not r.get("остыл"):
                                ui.notify(f"{r.get('имя')}: "
                                          f"{r.get('причина')}",
                                          color="warning")
                                return
                            c["заряд"] = r["стало"]
                            c["состояние"] = _ost.slovami(r["стало"])
                            c["температура"] = r.get("температура_стало",
                                                     c["температура"])
                            c["крайний"] = abs(r["стало"]) > 0.8
                            hvost = (" (упёрся)" if r.get("уперся") else "")
                            ui.notify(
                                f"❄ {r['имя']}: {r['было']:+.2f} → "
                                f"{r['стало']:+.2f}{hvost} · температура "
                                f"{r.get('температура_было', 0):.2f} → "
                                f"{r.get('температура_стало', 0):.2f}",
                                color="positive")
                            narisovat()

                        with ui.element("div").style(
                                "display:flex; align-items:center; gap:10px; "
                                "width:100%; padding:6px 10px; "
                                "border:1px solid rgba(255,255,255,0.08); "
                                "border-radius:8px;"):
                            ui.html(
                                f'<div style="flex:1;color:#dfe9f5;'
                                f'font-size:12px;">{ch["имя"]}{ogon}'
                                f'<div style="color:rgba(255,255,255,0.40);'
                                f'font-size:10px;">{ch["состояние"]} · '
                                f'температура {ch["температура"]:.2f}</div>'
                                f'</div>'
                                f'<div style="color:{cvet};font-size:14px;'
                                f'font-weight:600;min-width:62px;'
                                f'text-align:right;">{z:+.2f}</div>')
                            ui.button("❄", on_click=_lit).props(
                                "flat dense").style(
                                "color:#8fd3ff; min-width:34px;")

            narisovat()
            ui.button("Закрыть", on_click=dlg.close).props(
                "flat").classes("brat-gate").style("margin-top:8px;")
        dlg.open()

    async def do_tik():'''


# ── 2. сама кнопка, рядом с Тиком ───────────────────────────
STARO_2 = '''                        # KNOPKA_UBORKI_V1: рядом с Тиком — как просил Шеф.'''

NOVO_2 = '''                        # KNOPKA_DUSHA_V1: рядом с Тиком — как просил Шеф.
                        # Тик — весь город по времени, Душ — один сейчас.
                        ui.button("❄ Душ",
                                  on_click=do_dush
                                  ).props("flat").classes("brat-gate")
                        # KNOPKA_UBORKI_V1: рядом с Тиком — как просил Шеф.'''


ZAMENY = [
    ("рука do_dush", STARO_1, NOVO_1),
    ("кнопка рядом с Тиком", STARO_2, NOVO_2),
]


def main():
    print("=" * 58)
    print("КНОПКА ДУША У БРАТА")
    print("=" * 58)

    fajl = _nayti_brata()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    ost = _KOREN / "жители" / "ostudit.py"
    if not ost.exists():
        print("\n⚠ нет жители/ostudit.py — без него кнопка пустая.")
        print("  Положи остужалку туда и запусти снова.")
        return
    print(f"остужалка: {ost.relative_to(_KOREN)} — на месте")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    print("\n--- ЗАМЕНЫ ---")
    ne = []
    for imya, staro, _n in ZAMENY:
        c = tekst.count(staro)
        print(f"  {'✓' if c == 1 else '⚠ ' + str(c)}  {imya}")
        if c != 1:
            ne.append(imya)
    if ne:
        print(f"\n⚠ не сошлось: {', '.join(ne)} — ничего не тронул.")
        return

    novyy = tekst
    for _i, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_dush")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город и смотри:")
    print("  У Брата рядом с ⏱ Тик — ❄ Душ.")
    print("  Жмёшь — список жителей с зарядом и температурой.")
    print("  Жмёшь ❄ у строки — льётся вода, тут же видно что стало.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_KNOPKU_DUSHA_V1 - marker
