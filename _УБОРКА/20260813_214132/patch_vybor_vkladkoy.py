#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VYBOR_VKLADKOY_V1
"""
ВЫБОР — ВКЛАДКОЙ НА СТРАНИЦЕ РАБОТЫ, а не скриптом в терминале.

    python patch_vybor_vkladkoy.py            посмотреть
    python patch_vybor_vkladkoy.py --sdelat   накатить

Запускать из КОРНЯ.

ЗАЧЕМ

    Смотрелец выбора я сделал батником — и был неправ. Выбор входа это
    часть работы человека, и смотреть на него надо там же, где смотрят
    на места и на людей.

ЧТО ПОЯВЛЯЕТСЯ

    Третья вкладка на Странице Работы: МЕСТА | ЖИТЕЛИ | ВЫБОР.

    Слева — все, кто сидит на торговых местах, и дата их выбора.
    Зелёным — у кого записан, жёлтым — у кого нет вовсе. Если у двоих
    записан ОДИН И ТОТ ЖЕ текст, страница про это говорит отдельно:
    либо оба правда так решили, либо метка легла не тому.

    Справа — сам выбор: что записано, когда, и вся история перемен.
    Метки не стираются, поэтому видно, передумывал человек или нет.

    Выбора нет — так и написано, и сказано, что с этим делать: спросить
    в кабинете Биржи и дать объявить строкой ВЫБОР.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
UI = KOREN / "ГОРОД" / "ui_rabota.py"
MARKER = "# VYBOR_VKLADKOY_V1 - marker"
BAK = ".bak_vybor_vkladka"

STEZHKI = (
    ('место под третью вкладку', '                            "rezhim": "места", "zhitel": None}\n', '                            "rezhim": "места", "zhitel": None,\n                            "vybor_kogo": None}\n'),
    ('третья вкладка', '            for _r in ("места", "жители"):\n', '            for _r in ("места", "жители", "выбор"):\n'),
    ('список выборов слева', '    def risovat_derevo():\n        obnovit_schet()\n        if sost["rezhim"] == "жители":\n            risovat_zhiteley()\n            return\n', '    def risovat_vybory():\n        """VYBOR_VKLADKOY_V1: что у трейдеров ЗАПИСАНО, а не сказано.\n\n        Раньше это показывал скрипт из терминала. Место ему здесь:\n        выбор входа — часть работы, и смотреть на него надо там же, где\n        смотрят на места и людей.\n        """\n        refs["derevo"].clear()\n        try:\n            import sys as _s\n            _b = str(Path(__file__).resolve().parent.parent / "Биржа")\n            if _b not in _s.path:\n                _s.path.insert(0, _b)\n            import vybor as _V\n        except Exception as e:\n            with refs["derevo"]:\n                ui.label(f"механизм выбора не поднялся: {e}").style(\n                    "color:rgba(255,180,60,0.85); font-size:0.78rem;")\n            return\n\n        stroki, teksty = [], {}\n        for m in R.mesta():\n            if not m.get("цех") or not m.get("слот"):\n                continue\n            kto = m.get("кто_сидит") or ""\n            if not kto:\n                continue\n            try:\n                ist = _V.istoriya(m["цех"], m["слот"])\n            except Exception:\n                ist = []\n            posl = ist[-1] if ist else {}\n            stroki.append({"кто": kto, "место": m["название"],\n                           "цех": m["цех"], "слот": m["слот"],\n                           "текст": (posl.get("текст") or "").strip(),\n                           "когда": str(posl.get("когда", ""))[:16],\n                           "раз": len(ist)})\n            if posl.get("текст"):\n                teksty.setdefault(posl["текст"].strip().lower(), []).append(kto)\n\n        with refs["derevo"]:\n            if not stroki:\n                ui.label("на местах никого — выбирать некому").style(\n                    "color:rgba(255,255,255,0.35); font-size:0.78rem;")\n                return\n            for s in stroki:\n                def _vyb(s=s):\n                    sost["vybor_kogo"] = s\n                    risovat_kartu()\n\n                est = bool(s["текст"])\n                cvet = ("rgba(80,250,123,0.85)" if est\n                        else "rgba(255,180,60,0.85)")\n                hvost = s["когда"] if est else "выбора нет"\n                ui.button(f\'{s["кто"]}  ·  {s["слот"]}  ·  {hvost}\',\n                          on_click=_vyb).props("flat no-caps").style(\n                    f"width:100%; text-align:left; font-family:monospace; "\n                    f"font-size:0.74rem; color:{cvet}; padding:5px 10px; "\n                    f"border-radius:8px; background:rgba(255,255,255,0.04); "\n                    f"margin-bottom:3px;")\n\n            sovpali = {t: k for t, k in teksty.items() if len(k) > 1}\n            if sovpali:\n                ui.html(\'<div class="rab-podpis">одинаковый выбор</div>\')\n                for t, k in sovpali.items():\n                    ui.label(f\'{", ".join(k)} — «{t[:60]}»\').style(\n                        "color:rgba(255,180,60,0.8); font-size:0.72rem;")\n                ui.label("Либо оба правда так решили, либо метка легла "\n                         "не тому.").style(\n                    "color:rgba(255,255,255,0.45); font-size:0.7rem;")\n\n    def risovat_kartu_vybora():\n        refs["karta"].clear()\n        s = sost.get("vybor_kogo")\n        with refs["karta"]:\n            if not s:\n                ui.label("Выбери человека слева — покажу, что у него "\n                         "записано.").style(\n                    "color:rgba(255,255,255,0.4); font-size:0.82rem;")\n                return\n            try:\n                import sys as _s2\n                _b = str(Path(__file__).resolve().parent.parent / "Биржа")\n                if _b not in _s2.path:\n                    _s2.path.insert(0, _b)\n                import vybor as _V\n                ist = _V.istoriya(s["цех"], s["слот"])\n            except Exception as e:\n                ui.label(f"не читается: {e}").style(\n                    "color:rgba(255,180,60,0.85); font-size:0.8rem;")\n                return\n\n            ui.html(f\'<div style="font-weight:800; font-size:0.92rem;">\'\n                    f\'{s["кто"]}</div>\'\n                    f\'<div style="color:rgba(255,255,255,0.35); \'\n                    f\'font-size:0.68rem; font-family:monospace; \'\n                    f\'margin-bottom:12px;">{s["место"]} · {s["слот"]}</div>\')\n\n            if not ist:\n                ui.label("Выбора нет — метки не записано.").style(\n                    "color:rgba(255,180,60,0.85); font-size:0.85rem;")\n                ui.label("Значит всё, что он говорит про свой вход, взято "\n                         "из книги сейчас, а не решено им однажды. Спроси "\n                         "его в кабинете Биржи: «какой у тебя вход и почему "\n                         "именно он твой» — и пусть объявит строкой ВЫБОР.").style(\n                    "color:rgba(255,255,255,0.5); font-size:0.76rem; "\n                    "margin-top:6px;")\n                return\n\n            posl = ist[-1]\n            ui.label(posl.get("текст", "")).style(\n                "color:rgba(80,250,123,0.9); font-size:0.86rem;")\n            ui.label(f\'выбрано {str(posl.get("когда",""))[:16]}\').style(\n                "color:rgba(255,255,255,0.45); font-size:0.72rem;")\n\n            if len(ist) > 1:\n                ui.html(\'<div class="rab-podpis">передумывал</div>\')\n                for z in reversed(ist[:-1]):\n                    ui.label(f\'{str(z.get("когда",""))[:16]} — \'\n                             f\'{z.get("текст","")}\').style(\n                        "color:rgba(255,255,255,0.5); font-size:0.74rem; "\n                        "font-family:monospace;")\n\n    def risovat_derevo():\n        obnovit_schet()\n        if sost["rezhim"] == "выбор":\n            risovat_vybory()\n            return\n        if sost["rezhim"] == "жители":\n            risovat_zhiteley()\n            return\n'),
    ('карточка выбора справа', '    def risovat_kartu():\n        if sost["rezhim"] == "жители":\n            risovat_kartu_zhitelya()\n            return\n', '    def risovat_kartu():\n        if sost["rezhim"] == "выбор":\n            risovat_kartu_vybora()\n            return\n        if sost["rezhim"] == "жители":\n            risovat_kartu_zhitelya()\n            return\n'),
)


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
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 60)
    print("ВЫБОР ВКЛАДКОЙ" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 60)

    if not UI.exists():
        print("x не вижу ГОРОД/ui_rabota.py — запускай из КОРНЯ")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0

    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            if n == 0:
                print("    (нужен patch_zhiteli_v_rabote — вкладок ещё нет)")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "ui_rabota.py"):
        return 1
    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_vybor_vkladkoy.py --sdelat")
        return 0

    shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
    UI.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: ui_rabota.py{BAK})")
    print("\nСтраница Работы → вкладка ВЫБОР. Батник больше не нужен.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
