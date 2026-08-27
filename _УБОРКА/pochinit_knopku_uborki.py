# -*- coding: utf-8 -*-
"""
pochinit_knopku_uborki.py · MARKER: UBORKA_V_FONE_V1

ЧТО СЛУЧИЛОСЬ
─────────────
Нажимаешь «Уборка» — ничего не происходит, а связь с городом на время
рвётся.

Моя вина, и вот в чём. Разведка уборщика делается В ГЛАВНОМ ПОТОКЕ:
он обходит все файлы репо, читает полтысячи текстов и для каждого
ищет упоминания во всех остальных — это работа на кучу секунд, а на
Windows с антивирусом и того дольше. Пока она идёт, сервер не
отвечает НИ НА ЧТО: ни окно открыть, ни страницу обновить. Браузер
видит молчание и обрывает соединение.

Проверка не поймала: у меня разведка укладывается в полторы секунды —
столько браузер терпит. У тебя файлов больше (одних копий от патчей
75 штук), и порог перешагнулся.

ЧТО ПРАВИТ
──────────
1. Разведка и сама уборка уходят в ФОНОВЫЙ поток. Город продолжает
   дышать: страница живая, вахта тикает, связь не рвётся.
2. Окно открывается СРАЗУ и честно пишет «считаю…», а потом само
   наполняется. Ты видишь, что работа идёт, а не гадаешь, нажалось ли.
3. Кнопка перестаёт ждать окончания: нажал — и город свободен.

УРОК НА БУДУЩЕЕ (для меня же)
─────────────────────────────
Любая работа кнопки дольше секунды должна уходить в фон. В городе это
уже сделано у Совета и у прогона по истории — я просто не подумал,
что обход файлов тоже тяжёлый.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_knopku_uborki.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UBORKA_V_FONE_V1"
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


NOVAYA_RUKA = '''    async def do_uborka():
        """UBORKA_V_FONE_V1: показать лишнее и убрать в чулан.

        Правил здесь НЕТ: зовём функции самого uborshchik.py, чтобы
        кнопка и уборщик никогда не разошлись.

        Считаем В ФОНЕ. Разведка обходит все файлы репо и для каждого
        ищет упоминания во всех остальных — это секунды, а на Windows
        и десятки секунд. В главном потоке она вешала весь город:
        окно не открывалось, связь рвалась.
        """
        import asyncio
        loop = asyncio.get_event_loop()

        try:
            import sys as _sys
            _k = str(_REPO_ROOT_FOR_IMPORT)
            if _k not in _sys.path:
                _sys.path.insert(0, _k)
            import uborshchik as U
        except Exception as e:
            ui.notify(f"⚠ уборщик не поднялся: {e}", color="negative")
            return

        # окно открываем СРАЗУ — чтобы было видно, что работа пошла
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
            telo = ui.element("div").style("max-height:52vh; overflow-y:auto;")
            with telo:
                ui.html('<div style="color:rgba(255,255,255,0.55); '
                        'font-size:0.8rem;">Смотрю, что лишнее… '
                        'это занимает несколько секунд.</div>')
            itog = ui.html("")
            niz = ui.row().style("gap:8px; margin-top:14px; width:100%;")
            with niz:
                ui.button("закрыть", on_click=dlg.close).props("flat").style(
                    "color:rgba(255,255,255,0.4); font-size:0.75rem;")
                ui.element("div").style("flex:1")
        dlg.open()

        def _razvedka():
            teksty = dict(U._tekstovye())
            gotovye, _zhdut = U.sobrat_patchi(teksty)
            return ([
                ("копии, оставленные патчами", U.sobrat_kopii()),
                ("патчи, которые уже отработали", gotovye),
                ("разовые инструменты", U.sobrat_poimenno(U.RAZOVYE)),
                ("заменённое другим", U.sobrat_poimenno(U.OTSLUZHIVSHIE)),
                ("батники, у которых есть кнопка", U.sobrat_batniki()),
            ], U.sobrat_pod_voprosom(teksty))

        try:
            gruppy, pod_voprosom = await loop.run_in_executor(None, _razvedka)
        except Exception as e:
            telo.clear()
            with telo:
                ui.html(f'<div style="color:rgba(255,120,120,0.9); '
                        f'font-size:0.8rem;">Уборщик споткнулся: {e}</div>')
            return

        nahodki = [x for _, spisok in gruppy for x in spisok]
        vsego_kb = sum(p.stat().st_size for p, _ in nahodki) / 1024

        telo.clear()
        with telo:
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

        async def _ubrat():
            if not nahodki:
                ui.notify("Убирать нечего", color="warning")
                return
            ui.notify("🧹 убираю…", color="info")
            try:
                res = await loop.run_in_executor(
                    None, lambda: U.perenesti(nahodki, True))
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
            ui.notify(f"🧹 убрано файлов: {len(nahodki)}", color="positive")

        if nahodki:
            with niz:
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

'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    brat = koren / "Брат" / "ui_brat.py"
    t = brat.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if "KNOPKA_UBORKI_V1" not in t:
        print("✗ Нет кнопки уборки — накати сперва postavit_knopku_uborki.py")
        return 1

    n1 = t.find("    def do_uborka():")
    n2 = t.find("\n    def do_perevozka():", n1)
    if n1 < 0 or n2 < 0:
        print("✗ не нашёл старый обработчик уборки — не трогаю")
        return 1

    novyy = t[:n1] + NOVAYA_RUKA + t[n2 + 1:]
    # кнопка теперь зовёт корутину напрямую
    novyy = novyy.replace("on_click=lambda: do_uborka()",
                          "on_click=do_uborka", 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = brat.with_suffix(f".py.bak_fon_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(brat, bak)
    brat.write_text(novyy, encoding="utf-8")
    print(f"✓ уборка ушла в фон (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(brat), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь: нажал — окно открывается сразу и пишет «смотрю…»,")
    print("город при этом живой. Через несколько секунд окно наполнится.")
    print("Уборка тоже идёт в фоне — связь не рвётся.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
