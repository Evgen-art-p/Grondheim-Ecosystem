# -*- coding: utf-8 -*-
# UBRAT_MYORTVOE_V1
"""
УБРАТЬ МЁРТВОЕ — сношу тот диалог, что ты забраковал.

    python patch_ubrat_myortvoe.py --suho    посмотреть
    python patch_ubrat_myortvoe.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_myortvoe.

ЧТО СНОСИТСЯ

    Диалог do_rabota в кабинете Брата — та табличка со списком мест,
    которую я сделал под три слота Биржи и которую ты забраковал.
    Кнопка на неё уже не ведёт: она открывает Страницу Работы. А сам
    код лежал в файле мёртвым грузом — семь тысяч знаков, которые
    ничего не делают и путают всякого, кто откроет файл.

    Ничего живого патч не трогает: ни кнопку, ни «Роль», ни страницу.
    Только этот кусок.

    Если кнопка вдруг всё ещё зовёт этот диалог — патч откажется
    сносить и скажет об этом, чтобы не оставить тебя со сломанной
    кнопкой.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
BRAT = KOREN / "Брат" / "ui_brat.py"
MARKER = "# UBRAT_MYORTVOE_V1 - marker"
BAK = ".bak_myortvoe"

MYORTVOE = '    async def do_rabota():\n        """RABOTA_KNOPKI_V1: места Биржи — принять и уволить.\n\n        Работа не вкручена в личность: правда о найме живёт в документе\n        места (слоты/{слот}/должность.json), у жителя остаётся мягкая\n        отметка в паспорте. Здесь только две руки — принять и уволить;\n        сам бланк должности заводится пультом из корня.\n        """\n        try:\n            import sys as _sys\n            _b = str(_REPO_ROOT_FOR_IMPORT / "Биржа")\n            if _b not in _sys.path:\n                _sys.path.insert(0, _b)\n            import rabota as R\n        except Exception as e:\n            ui.notify(f"⚠ механизм работы не найден: {e}", color="negative")\n            return\n\n        mesta = R.spisok()\n        if not mesta:\n            ui.notify("Мест не нашёл — цехов с манифестом нет", color="warning")\n            return\n\n        pick: dict = {"mesto": None}\n\n        with ui.dialog() as dlg, ui.card().style(\n            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "\n            "border-radius:16px; min-width:380px; max-width:460px; padding:20px;"\n        ):\n            body = ui.element("div")\n\n            def render():\n                body.clear()\n                with body:\n                    if pick["mesto"] is None:\n                        ui.html(\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n                                \'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">\'\n                                \'🪑 РАБОТА · места Биржи</div>\')\n                        for m in mesta:\n                            kto = m["кто_сидит"] or "— свободно"\n                            hvost = "" if m["документ"] else "  (без документа)"\n                            nadpis = (f\'{m["слот"]} · {m["роль"] or m["название"]}\'\n                                      f\' · {kto}{hvost}\')\n\n                            def _pick_m(m=m):\n                                pick["mesto"] = m\n                                render()\n\n                            ui.button(nadpis, on_click=_pick_m).props("flat no-caps").style(\n                                "width:100%; text-align:left; font-family:monospace; "\n                                "font-size:0.78rem; color:rgba(255,255,255,0.75); "\n                                "padding:8px 12px; border-radius:8px; "\n                                "background:rgba(255,255,255,0.04); margin-bottom:4px;")\n                        ui.button("отмена", on_click=dlg.close).props("flat").style(\n                            "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")\n                        return\n\n                    m = pick["mesto"]\n                    kto = m["кто_сидит"]\n                    ui.html(f\'<div style="color:rgba(255,255,255,0.9); font-weight:700; \'\n                            f\'font-size:0.9rem; margin-bottom:10px; letter-spacing:0.06em;">\'\n                            f\'🪑 {m["слот"]} · {m["роль"] or m["название"]}</div>\')\n\n                    _confirm = None\n                    _podpis = "принять"\n\n                    if not m["документ"]:\n                        ui.html(\'<div style="color:rgba(255,180,60,0.85); font-size:0.75rem; \'\n                                \'margin-bottom:10px;">У места нет документа должности. \'\n                                \'Заведи его из корня: python rabota_pult.py --zavesti — \'\n                                \'и возвращайся.</div>\')\n                    elif kto:\n                        ui.html(f\'<div style="color:rgba(255,255,255,0.6); font-size:0.75rem; \'\n                                f\'margin-bottom:10px;">Сейчас на месте: <b>{kto}</b>. \'\n                                f\'Уволишь — место освободится, отметка у него погаснет, \'\n                                f\'дневник уедет к нему домой.</div>\')\n                        prich = ui.input("Причина (ляжет в трудовую историю)").props(\n                            "dark outlined").style("width:100%; font-size:0.8rem;")\n                        _podpis = "уволить"\n\n                        def _confirm():\n                            ok, msg = R.uvolit(m["цех"], m["слот"],\n                                               pochemu=(prich.value or "").strip())\n                            if ok:\n                                ui.notify(f"🪑 {msg}", color="positive")\n                                dlg.close()\n                            else:\n                                ui.notify(f"⚠ {msg}", color="negative")\n                    else:\n                        ui.html(\'<div style="color:rgba(255,255,255,0.45); font-size:0.75rem; \'\n                                \'margin-bottom:8px;">Место свободно — кого сажаем?</div>\')\n                        _zh = list_zhiteli()\n                        _opts = {}\n                        for z in _zh:\n                            _nm = (z.get("Official_Name") or "").strip()\n                            if _nm:\n                                _opts[_nm] = _nm\n                        if not _opts:\n                            ui.html(\'<div style="color:rgba(255,180,60,0.85); font-size:0.75rem;">\'\n                                    \'Жителей ещё нет — роди их в Странице Жизни.</div>\')\n                        else:\n                            sel = ui.select(_opts, value=next(iter(_opts))).props(\n                                "dark outlined").style(\n                                "width:100%; font-size:0.8rem; margin-bottom:8px;")\n                            prich = ui.input("Почему он (в трудовую историю)").props(\n                                "dark outlined").style("width:100%; font-size:0.8rem;")\n\n                            def _confirm():\n                                ok, msg = R.prinyat(m["цех"], m["слот"],\n                                                    (sel.value or "").strip(),\n                                                    pochemu=(prich.value or "").strip())\n                                if ok:\n                                    ui.notify(f"🪑 {msg}", color="positive")\n                                    dlg.close()\n                                else:\n                                    ui.notify(f"⚠ {msg}", color="negative")\n\n                    def _back():\n                        pick["mesto"] = None\n                        render()\n\n                    with ui.row().style("gap:8px; margin-top:14px; width:100%;"):\n                        ui.button("← назад", on_click=_back).props("flat").style(\n                            "color:rgba(255,255,255,0.4); font-size:0.75rem;")\n                        ui.element("div").style("flex:1")\n                        if _confirm is not None:\n                            ui.button(_podpis, on_click=_confirm).props("flat no-caps").style(\n                                "padding:8px 20px; border-radius:8px; font-weight:700; "\n                                "font-size:0.8rem; "\n                                "background:linear-gradient(135deg,rgba(120,168,201,0.30),"\n                                "rgba(120,168,201,0.18)); "\n                                "border:1px solid rgba(120,168,201,0.55); color:#fff;")\n\n            render()\n        dlg.open()\n\n'


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("=" * 56)
    print("УБРАТЬ МЁРТВОЕ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("=" * 56)

    if not BRAT.exists():
        print("x не вижу Брат/ui_brat.py — запускай из КОРНЯ репо")
        return 1

    tekst = BRAT.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже убрано")
        return 0
    if "async def do_rabota(" not in tekst:
        print("  мёртвого диалога нет — файл и так чистый")
        return 0
    if "on_click=do_rabota" in tekst:
        print("  x кнопка всё ещё зовёт этот диалог — сперва поставь")
        print("    postavit_stranicu_raboty.py, иначе кнопка сломается")
        return 1
    if tekst.count(MYORTVOE) != 1:
        print("  x кусок не совпал знак в знак — файл не трогаю.")
        print("    Значит его правили руками. Покажи файл, снесу точно.")
        return 1

    tekst = tekst.replace(MYORTVOE, "", 1)
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_brat.py"):
        return 1

    if a.suho:
        print(f"  + снесу {len(MYORTVOE)} знаков мёртвого кода")
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_ubrat_myortvoe.py")
        return 0

    shutil.copy2(BRAT, BRAT.with_suffix(BRAT.suffix + BAK))
    BRAT.write_text(tekst, encoding="utf-8")
    print(f"\n+ снесено {len(MYORTVOE)} знаков "
          f"(копия рядом: ui_brat.py{BAK})")
    print("\nКнопка «Работа» как вела на страницу, так и ведёт.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
