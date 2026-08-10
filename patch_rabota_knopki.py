# -*- coding: utf-8 -*-
# RABOTA_KNOPKI_V1
"""
КНОПКА «РАБОТА» В КАБИНЕТЕ БРАТА — принять и уволить одним кликом.

    python patch_rabota_knopki.py --suho    посмотреть
    python patch_rabota_knopki.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_rabota_knopki.
Ложится поверх postavit_rabotu.py — без него механизма нет.

ЗАЧЕМ

    Механизм найма уже стоит: у места свой документ, у жителя мягкая
    отметка, приём и увольнение пишутся в трудовую историю. Но рукой
    это делалось только из корня, пультом.

    Кнопка «Роль», что была в кабинете, для Биржи не годится: она
    просит РУКАМИ вписать цех и слот текстом и кладёт их жителю в
    маску — работа приклеивается к личности. Уволить ею нельзя вовсе.

СТАНОВИТСЯ

    Рядом появляется кнопка «Работа». В ней видно все места Биржи
    сразу: слот, должность, кто сидит или что свободно. Выбрал место —
    занято, будет «уволить»; свободно — выбираешь жителя и «принять».
    Причину можно вписать, она ляжет в трудовую историю места.

    Личность при этом не трогается ни в приём, ни в увольнение.

    Кнопку «Роль» не сношу и не правлю: она про тип жителя и про посты
    города (библиотекарь, ректор, хранитель маяка) — это другая дверь,
    и она работает. Биржа теперь ходит своей.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не заводит документы мест — это `python rabota_pult.py --zavesti`
    (или `postavit_rabotu.py --zavesti`). Место без документа кнопка
    честно покажет и объяснит, чего не хватает.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
UI = KOREN / "Брат" / "ui_brat.py"
MARKER = "# RABOTA_KNOPKI_V1 - marker"
BAK = ".bak_rabota_knopki"

# ── 1. сама дверь ─────────────────────────────────────────────
STAROE_FUNC = '''    async def do_naznachit_rol():
        """Брат надевает роль жителю: житель → тип → цех+слот+фраза →
        назначить. Активирует маску «работа», не трогает прописку."""
'''

NOVOE_FUNC = '''    async def do_rabota():
        """RABOTA_KNOPKI_V1: места Биржи — принять и уволить.

        Работа не вкручена в личность: правда о найме живёт в документе
        места (слоты/{слот}/должность.json), у жителя остаётся мягкая
        отметка в паспорте. Здесь только две руки — принять и уволить;
        сам бланк должности заводится пультом из корня.
        """
        try:
            import sys as _sys
            _b = str(_REPO_ROOT_FOR_IMPORT / "Биржа")
            if _b not in _sys.path:
                _sys.path.insert(0, _b)
            import rabota as R
        except Exception as e:
            ui.notify(f"⚠ механизм работы не найден: {e}", color="negative")
            return

        mesta = R.spisok()
        if not mesta:
            ui.notify("Мест не нашёл — цехов с манифестом нет", color="warning")
            return

        pick: dict = {"mesto": None}

        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "
            "border-radius:16px; min-width:380px; max-width:460px; padding:20px;"
        ):
            body = ui.element("div")

            def render():
                body.clear()
                with body:
                    if pick["mesto"] is None:
                        ui.html('<div style="color:rgba(255,255,255,0.9); font-weight:700; '
                                'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">'
                                '🪑 РАБОТА · места Биржи</div>')
                        for m in mesta:
                            kto = m["кто_сидит"] or "— свободно"
                            hvost = "" if m["документ"] else "  (без документа)"
                            nadpis = (f'{m["слот"]} · {m["роль"] or m["название"]}'
                                      f' · {kto}{hvost}')

                            def _pick_m(m=m):
                                pick["mesto"] = m
                                render()

                            ui.button(nadpis, on_click=_pick_m).props("flat no-caps").style(
                                "width:100%; text-align:left; font-family:monospace; "
                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "
                                "padding:8px 12px; border-radius:8px; "
                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")
                        ui.button("отмена", on_click=dlg.close).props("flat").style(
                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")
                        return

                    m = pick["mesto"]
                    kto = m["кто_сидит"]
                    ui.html(f'<div style="color:rgba(255,255,255,0.9); font-weight:700; '
                            f'font-size:0.9rem; margin-bottom:10px; letter-spacing:0.06em;">'
                            f'🪑 {m["слот"]} · {m["роль"] or m["название"]}</div>')

                    _confirm = None
                    _podpis = "принять"

                    if not m["документ"]:
                        ui.html('<div style="color:rgba(255,180,60,0.85); font-size:0.75rem; '
                                'margin-bottom:10px;">У места нет документа должности. '
                                'Заведи его из корня: python rabota_pult.py --zavesti — '
                                'и возвращайся.</div>')
                    elif kto:
                        ui.html(f'<div style="color:rgba(255,255,255,0.6); font-size:0.75rem; '
                                f'margin-bottom:10px;">Сейчас на месте: <b>{kto}</b>. '
                                f'Уволишь — место освободится, отметка у него погаснет, '
                                f'дневник уедет к нему домой.</div>')
                        prich = ui.input("Причина (ляжет в трудовую историю)").props(
                            "dark outlined").style("width:100%; font-size:0.8rem;")
                        _podpis = "уволить"

                        def _confirm():
                            ok, msg = R.uvolit(m["цех"], m["слот"],
                                               pochemu=(prich.value or "").strip())
                            if ok:
                                ui.notify(f"🪑 {msg}", color="positive")
                                dlg.close()
                            else:
                                ui.notify(f"⚠ {msg}", color="negative")
                    else:
                        ui.html('<div style="color:rgba(255,255,255,0.45); font-size:0.75rem; '
                                'margin-bottom:8px;">Место свободно — кого сажаем?</div>')
                        _zh = list_zhiteli()
                        _opts = {}
                        for z in _zh:
                            _nm = (z.get("Official_Name") or "").strip()
                            if _nm:
                                _opts[_nm] = _nm
                        if not _opts:
                            ui.html('<div style="color:rgba(255,180,60,0.85); font-size:0.75rem;">'
                                    'Жителей ещё нет — роди их в Странице Жизни.</div>')
                        else:
                            sel = ui.select(_opts, value=next(iter(_opts))).props(
                                "dark outlined").style(
                                "width:100%; font-size:0.8rem; margin-bottom:8px;")
                            prich = ui.input("Почему он (в трудовую историю)").props(
                                "dark outlined").style("width:100%; font-size:0.8rem;")

                            def _confirm():
                                ok, msg = R.prinyat(m["цех"], m["слот"],
                                                    (sel.value or "").strip(),
                                                    pochemu=(prich.value or "").strip())
                                if ok:
                                    ui.notify(f"🪑 {msg}", color="positive")
                                    dlg.close()
                                else:
                                    ui.notify(f"⚠ {msg}", color="negative")

                    def _back():
                        pick["mesto"] = None
                        render()

                    with ui.row().style("gap:8px; margin-top:14px; width:100%;"):
                        ui.button("← назад", on_click=_back).props("flat").style(
                            "color:rgba(255,255,255,0.4); font-size:0.75rem;")
                        ui.element("div").style("flex:1")
                        if _confirm is not None:
                            ui.button(_podpis, on_click=_confirm).props("flat no-caps").style(
                                "padding:8px 20px; border-radius:8px; font-weight:700; "
                                "font-size:0.8rem; "
                                "background:linear-gradient(135deg,rgba(120,168,201,0.30),"
                                "rgba(120,168,201,0.18)); "
                                "border:1px solid rgba(120,168,201,0.55); color:#fff;")

            render()
        dlg.open()

    async def do_naznachit_rol():
        """Брат надевает роль жителю: житель → тип → цех+слот+фраза →
        назначить. Активирует маску «работа», не трогает прописку."""
'''

# ── 2. сама кнопка ────────────────────────────────────────────
STAROE_KNOPKA = '''                        ui.button("Роль",
                                  on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL
                                  ).props("flat").classes("brat-gate")
'''
NOVOE_KNOPKA = '''                        ui.button("Роль",
                                  on_click=do_naznachit_rol  # PATCH_NAZNACHIT_ROL
                                  ).props("flat").classes("brat-gate")
                        # RABOTA_KNOPKI_V1: Биржа ходит своей дверью —
                        # приём и увольнение по документу места, без
                        # ручного вписывания цеха и слота в личность.
                        ui.button("Работа",
                                  on_click=do_rabota
                                  ).props("flat").classes("brat-gate")
'''

STEZHKI = (
    ("дверь «Работа»", STAROE_FUNC, NOVOE_FUNC),
    ("кнопка «Работа»", STAROE_KNOPKA, NOVOE_KNOPKA),
)


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("═" * 58)
    print("РАБОТА · кнопка у Брата" +
          ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 58)

    if not UI.exists():
        print("✗ не вижу Брат/ui_brat.py — запускай из КОРНЯ репо")
        return 1
    if not (KOREN / "Биржа" / "rabota.py").exists():
        print("✗ нет Биржа/rabota.py — сперва поставь postavit_rabotu.py")
        return 1

    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано — ничего не трогаю")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  ✗ якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  · {nazv} — вставлено")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_brat.py"):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_rabota_knopki.py")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n✓ накатано (копия рядом: ui_brat.py{BAK})")
    print("\nОткрой кабинет Брата — рядом с «Роль» стоит «Работа».")
    print("Внутри: все места Биржи, кто сидит, принять и уволить.")
    print("Документы мест ещё не заведены — кнопка так и скажет,")
    print("заводятся они из корня: python rabota_pult.py --zavesti")
    return 0


if __name__ == "__main__":
    sys.exit(main())
