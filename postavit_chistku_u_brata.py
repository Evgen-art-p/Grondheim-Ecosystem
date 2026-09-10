# -*- coding: utf-8 -*-
# CHISTKA_U_BRATA_V1 — кнопка «Уборка» становится менеджером
"""
МЕНЕДЖЕР ЧИСТКИ НА КНОПКЕ У БРАТА

ПОЧЕМУ НЕ ИЗ ТЕРМИНАЛА. Путь до города идёт через папку с кириллицей,
а консоль Windows её режет — модуль просто не запустится. Значит
место у него одно: кабинет Брата.

ЧТО ДЕЛАЕТ ПАТЧ. Кнопка «Уборка» перестаёт быть кнопкой одного
уборщика и становится входом в менеджер: список клинеров, у каждого
видно, сколько нашлось, и слово Брата поверх цифр.

    репозиторий  копии, отработавшие патчи, разовое
    бэкапы_цеха  .bak в слотах торгового цеха
    память       разговоры, отклик, архив жителей
    атлас        Атлас и лента PnL — торговая история, помечен

Выбрал строку — открывается прежнее окно уборки для репозитория
(оно уже работает и ничего не теряет) или подробность по другим.
Слово Брата — не пересказ цифр: он говорит, что память забита
протоколом, а не опытом; у кого следов нет вовсе; у кого нет маяков.

ТРЕБУЕТ: `ГОРОД/chistka.py` и `chistilshchik_pamyati.py` в корне.
Нет их — менеджер честно скажет и покажет то, что смог.

ЧЕГО НЕ ТРОГАЕТ: сам уборщик, старое окно уборки — оно остаётся и
зовётся из менеджера. Ничего не удаляется нигде.

БЕЗОПАСНОСТЬ: .bak_chistka, идемпотентен, синтаксис до записи,
`--suho` не трогает диск.

    python postavit_chistku_u_brata.py --suho
    python postavit_chistku_u_brata.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "CHISTKA_U_BRATA_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
FAJL = _REPO / "Брат" / "ui_brat.py"

YAKOR_FN = "    # PATCH_BRAT_TIK_V1 — суточный тик из кабинета\n"

TELO = '''    # ── CHISTKA_U_BRATA_V1: менеджер чистки ──────────────────
    # Клинеров стало четыре, и каждый жил сам по себе. Реестр ведёт
    # ГОРОД/chistka.py — здесь только показываем. Из терминала это
    # не запустить: путь через папку с кириллицей, консоль её режет.

    async def do_chistka():
        """Список клинеров, что нашлось у каждого, и слово Брата."""
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
            "border-radius:16px; min-width:600px; max-width:780px; "
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
                        'это занимает несколько секунд.</div>')
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

        telo.clear()
        with telo:
            for c in CH.spisok():
                d = razvedka.get(c["имя"], {}) or {}
                if d.get("беда"):
                    ui.html(
                        f'<div style="margin:8px 0; padding:10px; '
                        f'border-radius:8px; '
                        f'background:rgba(255,120,120,0.06); '
                        f'border:1px solid rgba(255,120,120,0.25); '
                        f'color:rgba(255,180,180,0.85); font-size:0.76rem;">'
                        f'<b>{c["имя"]}</b> — не смотрится: {d["беда"]}</div>')
                    continue
                opasno = c.get("опасно")
                cvet = ("rgba(255,200,120," if opasno
                        else "rgba(120,168,201,")
                ui.html(
                    f'<div style="margin:8px 0; padding:10px 12px; '
                    f'border-radius:8px; background:{cvet}0.06); '
                    f'border:1px solid {cvet}0.28);">'
                    f'<div style="display:flex; justify-content:space-between; '
                    f'align-items:baseline;">'
                    f'<span style="color:rgba(255,255,255,0.9); '
                    f'font-weight:700; font-size:0.82rem;">'
                    f'{"⚠ " if opasno else ""}{c["имя"]}</span>'
                    f'<span style="color:rgba(255,255,255,0.55); '
                    f'font-size:0.74rem;">{d.get("файлов", 0)} файл(ов)'
                    f'</span></div>'
                    f'<div style="color:rgba(255,255,255,0.45); '
                    f'font-size:0.72rem; margin-top:3px;">{c["что"]} · '
                    f'в {c["куда"]}</div>'
                    + "".join(
                        f'<div style="color:rgba(255,255,255,0.55); '
                        f'font-size:0.72rem; margin-top:2px;">· {s}</div>'
                        for s in (d.get("строки") or [])[:5])
                    + f'<div style="color:rgba(255,255,255,0.35); '
                      f'font-size:0.68rem; margin-top:5px; '
                      f'font-family:monospace;">{c["как убрать"]}</div>'
                    + '</div>')

            if slova:
                ui.html(
                    '<div style="margin:14px 0 4px; '
                    'color:rgba(255,255,255,0.55); font-size:0.72rem; '
                    'letter-spacing:0.08em;">ЧТО Я ОБ ЭТОМ ДУМАЮ</div>')
                for s in slova:
                    ui.html(
                        f'<div style="margin:5px 0; padding:9px 12px; '
                        f'border-radius:8px; '
                        f'background:rgba(255,255,255,0.03); '
                        f'border-left:2px solid rgba(120,168,201,0.5); '
                        f'color:rgba(255,255,255,0.75); '
                        f'font-size:0.76rem; line-height:1.5;">{s}</div>')

'''

# кнопка зовёт менеджер вместо одного уборщика
STARAYA_KNOPKA = '''                        # KNOPKA_UBORKI_V1: рядом с Тиком — как просил Шеф.
                        ui.button("Уборка",
                                  on_click=do_uborka
                                  ).props("flat").classes("brat-gate")'''
NOVAYA_KNOPKA = '''                        # KNOPKA_UBORKI_V1: рядом с Тиком — как просил Шеф.
                        # CHISTKA_U_BRATA_V1: кнопка ведёт в менеджер —
                        # клинеров четыре, а кнопка знала одного.
                        ui.button("Уборка",
                                  on_click=do_chistka
                                  ).props("flat").classes("brat-gate")'''


def main():
    print()
    print("ЧИСТКА У БРАТА" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("файл:", FAJL)
    print()

    if not FAJL.exists():
        print("!! файла нет — запускать из корня репы")
        return
    txt = FAJL.read_text(encoding="utf-8")

    if MARKER in txt:
        print("Уже стоит. Ничего не меняю.")
        return

    beda = []
    if txt.count(YAKOR_FN) != 1:
        beda.append(f"шов для функции: {txt.count(YAKOR_FN)} совпадений")
    if txt.count(STARAYA_KNOPKA) != 1:
        beda.append(f"кнопка «Уборка»: {txt.count(STARAYA_KNOPKA)} совпадений")
    if beda:
        print("ОТКАЗЫВАЮСЬ, файл не тронут:")
        for b in beda:
            print("  ·", b)
        return

    novy = txt.replace(YAKOR_FN, TELO + YAKOR_FN, 1)
    novy = novy.replace(STARAYA_KNOPKA, NOVAYA_KNOPKA, 1)

    try:
        ast.parse(novy)
    except SyntaxError as e:
        print("!! после правки синтаксис сломан — ничего не записал:", e)
        return

    print("  функция менеджера — вставлена")
    print("  кнопка «Уборка» — ведёт в менеджер")
    print("  синтаксис после правки — валиден")

    if SUHO:
        print()
        print("Сухой прогон: на диске ничего не изменилось.")
        return

    shutil.copy2(FAJL, FAJL.with_suffix(".py.bak_chistka"))
    FAJL.write_text(novy, encoding="utf-8")
    print()
    print("Готово. Бэкап: ui_brat.py.bak_chistka")
    print("Не забудь положить ГОРОД/chistka.py и chistilshchik_pamyati.py.")
    print()


if __name__ == "__main__":
    main()
