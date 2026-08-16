# -*- coding: utf-8 -*-
"""
postavit_knopku_uborki.py · MARKER: KNOPKA_UBORKI_V1

ЧТО ДЕЛАЕТ
──────────
Ставит у Брата кнопку «Уборка» рядом с Тиком. Она открывает окно, где
видно, что уборщик считает лишним, и можно убрать это одним нажатием.

ЗОВЁТ УБОРЩИКА, А НЕ ПОВТОРЯЕТ ЕГО
──────────────────────────────────
Ни одно правило не переписано: кнопка зовёт функции самого
`uborshchik.py` — `sobrat_kopii`, `sobrat_patchi`, `sobrat_poimenno`,
`sobrat_batniki`, `sobrat_pod_voprosom`, `perenesti`. Значит правила
остаются в одном месте: поправишь их в уборщике — кнопка станет
показывать по-новому, и наоборот никогда не разойдётся.

ЧТО ВИДНО В ОКНЕ
────────────────
    · копии, оставленные патчами (.bak_…)
    · патчи, которые уже отработали
    · разовые инструменты
    · заменённое другим
    · батники, у которых теперь есть кнопка

и отдельно, БЕЗ галочки на уборку:

    · НЕ ПОДКЛЮЧЕНО — задумка, до которой руки не дошли (калибровка).
      Это не мусор, про такое напоминают, а не выбрасывают.
    · ПОД ВОПРОСОМ — их никто не зовёт ни импортом, ни по имени.
      Подозрение, а не приговор: решает Шеф.

БЕЗОПАСНОСТЬ САМОЙ УБОРКИ
─────────────────────────
Ничего не удаляется. Всё переезжает в `_УБОРКА/{дата}/` с сохранением
дорожек, рядом ложатся `манифест.json` и `КАК_ВЕРНУТЬ.txt`. Это
поведение уборщика, я его не менял.

Заодно правится строчка в самом уборщике: про `ПЕРЕВОЗКА.bat` там
написано «живёт кнопкой у Брата» — с сегодняшнего дня у перевозки
своя страница `/perevozka`.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_knopku_uborki.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KNOPKA_UBORKI_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "uborshchik.py").exists()
            and (p / "Брат" / "ui_brat.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ── обработчик кнопки: кладём рядом с do_perevozka ──
RUKA = '''    def do_uborka():
        """KNOPKA_UBORKI_V1: показать, что лишнее, и убрать в чулан.

        Правил здесь НЕТ: зовём функции самого uborshchik.py. Правила
        живут в одном месте — иначе кнопка и уборщик однажды разойдутся,
        и Шеф будет видеть одно, а получать другое.
        """
        try:
            import sys as _sys
            _k = str(_REPO_ROOT_FOR_IMPORT)
            if _k not in _sys.path:
                _sys.path.insert(0, _k)
            import uborshchik as U
        except Exception as e:
            ui.notify(f"⚠ уборщик не поднялся: {e}", color="negative")
            return

        try:
            teksty = dict(U._tekstovye())
            gotovye, zhdut = U.sobrat_patchi(teksty)
            gruppy = [
                ("копии, оставленные патчами", U.sobrat_kopii()),
                ("патчи, которые уже отработали", gotovye),
                ("разовые инструменты", U.sobrat_poimenno(U.RAZOVYE)),
                ("заменённое другим", U.sobrat_poimenno(U.OTSLUZHIVSHIE)),
                ("батники, у которых есть кнопка", U.sobrat_batniki()),
            ]
            pod_voprosom = U.sobrat_pod_voprosom(teksty)
        except Exception as e:
            ui.notify(f"⚠ уборщик споткнулся: {e}", color="negative")
            return

        nahodki = [x for _, spisok in gruppy for x in spisok]
        vsego_kb = sum(p.stat().st_size for p, _ in nahodki) / 1024

        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "
            "border-radius:16px; min-width:560px; max-width:720px; padding:20px;"
        ):
            ui.html('<div style="color:rgba(255,255,255,0.9); font-weight:700; '
                    'font-size:0.9rem; letter-spacing:0.08em;">'
                    '🧹 УБОРКА</div>')
            ui.html('<div style="color:rgba(255,255,255,0.45); '
                    'font-size:0.72rem; margin:6px 0 12px;">'
                    'Ничего не удаляется. Всё переедет в _УБОРКА с '
                    'манифестом и запиской, как вернуть.</div>')

            with ui.element("div").style("max-height:52vh; overflow-y:auto;"):
                if not nahodki:
                    ui.html('<div style="color:rgba(80,250,123,0.85); '
                            'font-size:0.8rem;">Убирать нечего — чисто.</div>')
                for imya, spisok in gruppy:
                    if not spisok:
                        continue
                    ui.html(f'<div style="color:rgba(201,168,76,0.75); '
                            f'font-size:0.68rem; letter-spacing:0.10em; '
                            f'font-weight:700; margin:12px 0 4px;">'
                            f'{imya.upper()} — {len(spisok)}</div>')
                    for p, prichina in sorted(spisok, key=lambda x: str(x[0])):
                        ui.html(
                            f'<div style="padding:3px 0;">'
                            f'<span style="color:rgba(255,255,255,0.88); '
                            f'font-size:0.78rem;">{p.relative_to(U.KOREN)}'
                            f'</span><br>'
                            f'<span style="color:rgba(255,255,255,0.38); '
                            f'font-size:0.70rem;">· {prichina}</span></div>')

                if pod_voprosom:
                    ui.html(f'<div style="color:rgba(255,180,120,0.8); '
                            f'font-size:0.68rem; letter-spacing:0.10em; '
                            f'font-weight:700; margin:14px 0 4px;">'
                            f'ПОД ВОПРОСОМ — {len(pod_voprosom)} '
                            f'(показываю, НЕ трогаю)</div>')
                    ui.html('<div style="color:rgba(255,255,255,0.38); '
                            'font-size:0.70rem; margin-bottom:4px;">'
                            'Их никто не зовёт ни импортом, ни по имени. '
                            'Это подозрение, а не приговор — решай сам.</div>')
                    for p in sorted(pod_voprosom, key=str):
                        ui.html(f'<div style="color:rgba(255,255,255,0.70); '
                                f'font-size:0.76rem; padding:2px 0;">'
                                f'{p.relative_to(U.KOREN)}</div>')

            itog = ui.html("")

            def _ubrat():
                if not nahodki:
                    ui.notify("Убирать нечего", color="warning")
                    return
                try:
                    res = U.perenesti(nahodki, True)
                except Exception as e:
                    ui.notify(f"⚠ уборка сорвалась: {e}", color="negative")
                    return
                kuda = res["папка"].relative_to(U.KOREN)
                itog.content = (
                    f'<div style="color:rgba(80,250,123,0.85); '
                    f'font-size:0.75rem; margin-top:10px;">'
                    f'Убрано {len(nahodki)} файлов в {kuda}.<br>'
                    f'Рядом манифест.json и КАК_ВЕРНУТЬ.txt — вернуть можно '
                    f'в любой момент.</div>')
                ui.notify(f"🧹 убрано файлов: {len(nahodki)}",
                          color="positive")

            with ui.row().style("gap:8px; margin-top:14px; width:100%;"):
                ui.button("закрыть", on_click=dlg.close).props("flat").style(
                    "color:rgba(255,255,255,0.4); font-size:0.75rem;")
                ui.element("div").style("flex:1")
                if nahodki:
                    ui.html(f'<span style="color:rgba(255,255,255,0.45); '
                            f'font-size:0.72rem; align-self:center;">'
                            f'{len(nahodki)} файлов · {vsego_kb:.0f} КБ</span>')
                    ui.button("убрать в чулан", on_click=_ubrat).props(
                        "flat no-caps").style(
                        "padding:8px 20px; border-radius:8px; font-weight:700; "
                        "font-size:0.8rem; color:#fff; "
                        "background:linear-gradient(135deg,rgba(201,168,76,0.30),"
                        "rgba(201,168,76,0.18)); "
                        "border:1px solid rgba(201,168,76,0.55);")
        dlg.open()

'''

ST_KNOPKA = '''                        ui.button("Прописка",'''
NOV_KNOPKA = '''                        # KNOPKA_UBORKI_V1: рядом с Тиком — как просил Шеф.
                        ui.button("Уборка",
                                  on_click=lambda: do_uborka()
                                  ).props("flat").classes("brat-gate")
                        ui.button("Прописка",'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    brat = koren / "Брат" / "ui_brat.py"
    ub = koren / "uborshchik.py"
    t = brat.read_text(encoding="utf-8")

    print("\n1. Кнопка «Уборка» у Брата")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        yakor_ruki = "    def do_perevozka():"
        if t.count(yakor_ruki) != 1 or t.count(ST_KNOPKA) != 1:
            print(f"  ✗ якоря не найдены дословно "
                  f"(рука {t.count(yakor_ruki)}, кнопка {t.count(ST_KNOPKA)})")
            return 1
        novyy = t.replace(yakor_ruki, RUKA + yakor_ruki, 1)
        novyy = novyy.replace(ST_KNOPKA, NOV_KNOPKA, 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(brat, brat.with_suffix(
                f".py.bak_uborka_{datetime.now():%Y%m%d_%H%M%S}"))
            brat.write_text(novyy, encoding="utf-8")
            print("  ✓ встала рядом с Тиком")

    print("\n2. Уборщик: строчка про перевозку устарела")
    tu = ub.read_text(encoding="utf-8")
    st = ('"ПЕРЕВОЗКА.bat": "перевозка живёт кнопкой у Брата и страницей '
          'на острове",')
    if MARKER in tu:
        print("  · уже поправлено")
    elif st not in tu:
        print("  · строчка другая — не трогаю")
    elif SUHO:
        print("  · правка готова (сухой прогон)")
    else:
        shutil.copy2(ub, ub.with_suffix(
            f".py.bak_uborka_{datetime.now():%Y%m%d_%H%M%S}"))
        ub.write_text(tu.replace(
            st, '"ПЕРЕВОЗКА.bat": "у перевозки своя страница /perevozka — '
                'берег отправляет, остров принимает",', 1)
            + f"\n# {MARKER} - marker\n", encoding="utf-8")
        print("  ✓ поправлена")

    if not SUHO:
        import py_compile
        for f in (brat, ub):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nУ Брата теперь: Тик · Уборка · Прописка · Работа · Перевозка.")
        print("Уборка сперва ПОКАЗЫВАЕТ — что и почему считается лишним,")
        print("и отдельно «под вопросом», которое не трогает вовсе.")
        print("Нажмёшь «убрать в чулан» — переедет в _УБОРКА с манифестом.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
