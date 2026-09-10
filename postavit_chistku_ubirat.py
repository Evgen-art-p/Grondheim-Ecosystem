# -*- coding: utf-8 -*-
# CHISTKA_UBIRAET_V2 — менеджер не только показывает, но и убирает
"""
МЕНЕДЖЕР ЧИСТКИ УЧИТСЯ УБИРАТЬ

Первая версия показывала и отправляла к командам. А команды из
консоли не запускаются: путь идёт через папку с кириллицей.

ТЕПЕРЬ В ОКНЕ:

  · бэкапы цеха — кнопка «убрать»: всё уезжает в архив с манифестом;
  · память — выбор жителя и слоя, потом «убрать»; метки и маяки в
    выбор НЕ попадают, их клинер сам не предлагает;
  · репозиторий — прежняя кнопка уборки, она уже умела;
  · атлас — кнопки НЕТ и не будет: это торговая история, из неё
    считаются веса. Только строка с командой, чтобы нажать нельзя
    было случайно.

Правила уборки здесь не переписываются — зовутся функции самих
клинеров, чтобы кнопка и клинер никогда не разошлись.

ТРЕБУЕТ: CHISTKA_U_BRATA_V1 (заменяет его функцию целиком) и свежий
`ГОРОД/chistka.py` с функциями уборки.

БЕЗОПАСНОСТЬ: .bak_chistka2, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_chistku_ubirat.py --suho
    python postavit_chistku_ubirat.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "CHISTKA_UBIRAET_V2"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Брат" / "ui_brat.py"

NACHALO = "    # ── CHISTKA_U_BRATA_V1: менеджер чистки ──"
KONEC = "    # PATCH_BRAT_TIK_V1 — суточный тик из кабинета\n"

NOVOE = '''    # ── CHISTKA_U_BRATA_V1 · CHISTKA_UBIRAET_V2 ──────────────
    # Клинеров четыре, реестр ведёт ГОРОД/chistka.py. Здесь только
    # показываем и зовём — правила уборки живут в самих клинерах.
    # Из терминала это не запустить: путь через папку с кириллицей.

    async def do_chistka():
        """Список клинеров, что нашлось, слово Брата и уборка."""
        import asyncio
        loop = asyncio.get_event_loop()

        try:
            import sys as _sys
            _k = str(_REPO_ROOT_FOR_IMPORT)
            if _k not in _sys.path:
                _sys.path.insert(0, _k)
            _g = str(_REPO_ROOT_FOR_IMPORT / "ГОРОД")
            if _g not in _sys.path:
                _sys.path.insert(0, _g)
            import chistka as CH
        except Exception as e:
            ui.notify(f"⚠ менеджер чистки не поднялся: {e}",
                      color="negative")
            return

        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "
            "border-radius:16px; min-width:620px; max-width:800px; "
            "padding:20px;"
        ):
            ui.html('<div style="color:rgba(255,255,255,0.9); '
                    'font-weight:700; font-size:0.9rem; '
                    'letter-spacing:0.08em;">🧹 ЧИСТКА</div>')
            ui.html('<div style="color:rgba(255,255,255,0.45); '
                    'font-size:0.72rem; margin:6px 0 12px;">'
                    'Ничего не удаляется. Всё переезжает в чулан с '
                    'манифестом — что, откуда и как вернуть.</div>')
            telo = ui.element("div").style("max-height:56vh; "
                                           "overflow-y:auto;")
            with telo:
                ui.html('<div style="color:rgba(255,255,255,0.55); '
                        'font-size:0.8rem;">Смотрю, что накопилось… '
                        'несколько секунд.</div>')
            with ui.row().style("gap:8px; margin-top:14px; width:100%;"):
                ui.button("закрыть", on_click=dlg.close).props("flat").style(
                    "color:rgba(255,255,255,0.4); font-size:0.75rem;")
                ui.element("div").style("flex:1")
                ui.button("уборка репозитория",
                          on_click=lambda: (dlg.close(), do_uborka())
                          ).props("flat no-caps").style(
                    "padding:8px 18px; border-radius:8px; font-size:0.78rem; "
                    "background:rgba(120,168,201,0.20); "
                    "border:1px solid rgba(120,168,201,0.50); color:#fff;")
        dlg.open()

        async def _narisovat():
            try:
                razvedka = await loop.run_in_executor(None, CH.razvedat)
                slova = await loop.run_in_executor(
                    None, CH.slovo_brata, razvedka)
            except Exception as e:
                telo.clear()
                with telo:
                    ui.html(f'<div style="color:rgba(255,120,120,0.9); '
                            f'font-size:0.8rem;">Разведка споткнулась: '
                            f'{e}</div>')
                return

            async def _ubrat_bak():
                n, kuda = await loop.run_in_executor(
                    None, CH.ubrat_bak_ceha, False)
                ui.notify(f"перенесено {n} → {kuda}" if n
                          else "нечего убирать", color="positive")
                await _narisovat()

            async def _ubrat_pam(zhitel, sloy):
                if not zhitel or not sloy:
                    ui.notify("выбери жителя и слой", color="warning")
                    return
                n = await loop.run_in_executor(
                    None, CH.ubrat_pamyat, zhitel, sloy, False)
                ui.notify(f"{zhitel}: перенесено {n} файл(ов)" if n
                          else f"{zhitel}: в «{sloy}» пусто",
                          color="positive" if n else "warning")
                await _narisovat()

            telo.clear()
            with telo:
                for c in CH.spisok():
                    d = razvedka.get(c["имя"], {}) or {}
                    if d.get("беда"):
                        ui.html(f'<div style="margin:8px 0; padding:10px; '
                                f'border-radius:8px; '
                                f'background:rgba(255,120,120,0.06); '
                                f'border:1px solid rgba(255,120,120,0.25); '
                                f'color:rgba(255,180,180,0.85); '
                                f'font-size:0.76rem;"><b>{c["имя"]}</b> — '
                                f'не смотрится: {d["беда"]}</div>')
                        continue
                    opasno = c.get("опасно")
                    cvet = ("rgba(255,200,120," if opasno
                            else "rgba(120,168,201,")
                    with ui.element("div").style(
                        f"margin:8px 0; padding:10px 12px; border-radius:8px; "
                        f"background:{cvet}0.06); border:1px solid {cvet}0.28);"
                    ):
                        ui.html(
                            f'<div style="display:flex; '
                            f'justify-content:space-between; '
                            f'align-items:baseline;">'
                            f'<span style="color:rgba(255,255,255,0.9); '
                            f'font-weight:700; font-size:0.82rem;">'
                            f'{"⚠ " if opasno else ""}{c["имя"]}</span>'
                            f'<span style="color:rgba(255,255,255,0.55); '
                            f'font-size:0.74rem;">{d.get("файлов", 0)} '
                            f'файл(ов)</span></div>'
                            f'<div style="color:rgba(255,255,255,0.45); '
                            f'font-size:0.72rem; margin-top:3px;">'
                            f'{c["что"]} · в {c["куда"]}</div>'
                            + "".join(
                                f'<div style="color:rgba(255,255,255,0.55); '
                                f'font-size:0.72rem; margin-top:2px;">· {s}'
                                f'</div>'
                                for s in (d.get("строки") or [])[:5]))

                        if c["имя"] == "бэкапы_цеха" and d.get("файлов"):
                            ui.button("убрать в архив",
                                      on_click=_ubrat_bak
                                      ).props("flat no-caps dense").style(
                                "margin-top:8px; font-size:0.72rem; "
                                "color:rgba(120,168,201,0.95);")

                        elif c["имя"] == "память" and d.get("файлов"):
                            with ui.row().style("gap:6px; margin-top:8px; "
                                                "align-items:center;"):
                                kto = ui.select(
                                    CH.zhiteli_pamyati(), label="житель"
                                ).props("dense outlined").style(
                                    "min-width:130px; font-size:0.72rem;")
                                chto = ui.select(
                                    CH.sloi_pamyati(), value="разговоры",
                                    label="слой"
                                ).props("dense outlined").style(
                                    "min-width:120px; font-size:0.72rem;")
                                ui.button(
                                    "убрать",
                                    on_click=lambda: _ubrat_pam(
                                        kto.value, chto.value)
                                ).props("flat no-caps dense").style(
                                    "font-size:0.72rem; "
                                    "color:rgba(120,168,201,0.95);")
                            ui.html('<div style="color:rgba(255,255,255,0.35); '
                                    'font-size:0.68rem; margin-top:4px;">'
                                    'метки и маяки в выбор не идут — это '
                                    'нажитое, оно убирается только из '
                                    'командной строки, поимённо.</div>')

                        elif opasno:
                            ui.html('<div style="color:rgba(255,200,120,0.75); '
                                    'font-size:0.68rem; margin-top:6px;">'
                                    'кнопки нет намеренно: это торговая '
                                    'история, из неё считаются веса.</div>')
                            ui.html(f'<div style="color:rgba(255,255,255,0.35); '
                                    f'font-size:0.68rem; margin-top:2px; '
                                    f'font-family:monospace;">'
                                    f'{c["как убрать"]}</div>')

                if slova:
                    ui.html('<div style="margin:14px 0 4px; '
                            'color:rgba(255,255,255,0.55); '
                            'font-size:0.72rem; letter-spacing:0.08em;">'
                            'ЧТО Я ОБ ЭТОМ ДУМАЮ</div>')
                    for s in slova:
                        ui.html(
                            f'<div style="margin:5px 0; padding:9px 12px; '
                            f'border-radius:8px; '
                            f'background:rgba(255,255,255,0.03); '
                            f'border-left:2px solid rgba(120,168,201,0.5); '
                            f'color:rgba(255,255,255,0.75); '
                            f'font-size:0.76rem; line-height:1.5;">{s}</div>')

        await _narisovat()

'''


def main():
    print()
    print("ЧИСТКА УБИРАЕТ" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()
    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return
    if NACHALO not in txt:
        print("!! сперва postavit_chistku_u_brata.py")
        return
    if txt.count(KONEC) != 1:
        print(f"!! шов конца встречается {txt.count(KONEC)} раз(а)")
        return

    n1 = txt.index(NACHALO)
    n2 = txt.index(KONEC, n1)
    novy = txt[:n1] + NOVOE + txt[n2:]

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    print("  функция менеджера — заменена целиком")
    print("  синтаксис после правки — валиден")
    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_chistka2"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_brat.py.bak_chistka2")
    print("Не забудь обновить ГОРОД/chistka.py — в нём новые функции.")
    print()


if __name__ == "__main__":
    main()
