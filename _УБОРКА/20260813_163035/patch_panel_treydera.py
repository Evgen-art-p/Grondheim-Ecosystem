#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PANEL_TREYDERA_V1
"""
ПАНЕЛЬ ПРИНАДЛЕЖИТ ТРЕЙДЕРУ — кликнул человека, кликнул инструмент.

    python patch_panel_treydera.py            посмотреть
    python patch_panel_treydera.py --sdelat   накатить

Запускать из КОРНЯ (материк или остров).
Ложится поверх patch_instrument_treydera.py.

СЛОВО ШЕФА

    «При клике на трейдера у него активируется своя панель котировок —
    такая же для всех одна, но выбор остаётся у активного трейдера.
    Потом кликнул на следующего, по инструменту — тот берёт его в
    работу. С возможностью спросить, каким инструментом он работает».

ЧТО МЕНЯЕТСЯ

    Панель котировок слева остаётся ОДНА, но принадлежит тому, кто
    сейчас выбран наверху.

      · кликнул трейдера — панель стала его, и сверху мелькнёт, чем он
        работает и откуда это взялось: задал Шеф или взял сам;
      · кликнул инструмент — этот трейдер взял его в работу. Задание
        записано;
      · переключился на другого — у того своё, панель показывает его.

    Спросить всегда можно словами: «каким инструментом ты работаешь» —
    он ответит и скажет, задание это или его выбор.

ЧТО ИСПРАВЛЕНО ЗАОДНО

    Поле «инструмент» убрано из бланка должности на Странице Работы.
    Я положил его туда зря: бланк — про должность, он живёт месяцами,
    а инструмент — задание на сегодня. Теперь назначения лежат
    отдельным листком при Бирже (`Биржа/данные/naznacheniya.json`) и
    ставятся кликом в кабинете.

    Старшинство прежнее: задал Шеф — работает по заданию; не задал, но
    взял сам — по своему; ничего нет — по тому, что открыто в кабинете.
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
VYBOR = KOREN / "Биржа" / "vybor.py"
UI = KOREN / "Биржа" / "ui_torg.py"
STRANICA = KOREN / "ГОРОД" / "ui_rabota.py"
MARKER = "# PANEL_TREYDERA_V1 - marker"
BAK = ".bak_panel"

DOBAVKA = '\n\n# ══════════════════════════════════════════════════════════════\n# НАЗНАЧЕНИЯ ШЕФА (PANEL_TREYDERA_V1)\n# ══════════════════════════════════════════════════════════════\n# Сперва я положил инструмент в бланк должности — и был неправ.\n# Бланк про должность, он живёт месяцами; а инструмент — рабочее\n# задание на сегодня. Теперь назначения лежат отдельным листком при\n# Бирже: Шеф кликнул трейдера, кликнул инструмент — записалось.\n_NAZN = Path(__file__).resolve().parent / "данные" / "naznacheniya.json"\n\n\ndef _nazn_chitat() -> dict:\n    try:\n        import json as _j\n        return _j.loads(_NAZN.read_text(encoding="utf-8"))\n    except Exception:\n        return {}\n\n\ndef naznachit(ceh: str, slot: str, symbol: str) -> tuple:\n    """Шеф даёт трейдеру инструмент. Пусто — снимает задание."""\n    import json as _j\n    d = _nazn_chitat()\n    klyuch = f"{ceh}/{slot}"\n    symbol = (symbol or "").strip().upper()\n    if symbol:\n        d[klyuch] = symbol\n    else:\n        d.pop(klyuch, None)\n    try:\n        _NAZN.parent.mkdir(parents=True, exist_ok=True)\n        _NAZN.write_text(_j.dumps(d, ensure_ascii=False, indent=2),\n                         encoding="utf-8")\n    except Exception as e:\n        return False, str(e)\n    return True, (f"задание: {symbol}" if symbol else "задание снято")\n'
VYBOR_STEZHKI = (("назначения при Бирже", 'def instrument_mesta(ceh: str, slot: str) -> str:\n    """Что назначено месту в бланке должности. Пусто — не назначено."""\n    try:\n        import sys as _s\n        from pathlib import Path as _P\n        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")\n        if _g not in _s.path:\n            _s.path.insert(0, _g)\n        import rabota as _rab\n        for m in _rab.mesta():\n            if m.get("цех") == ceh and m.get("слот") == slot:\n                d = _rab.chitat(m["id"]) or {}\n                return (d.get("инструмент") or "").strip().upper()\n    except Exception:\n        pass\n    return ""\n', 'def instrument_mesta(ceh: str, slot: str) -> str:\n    """Что Шеф задал этому месту. Пусто — не задавал, выбирает сам.\n\n    PANEL_TREYDERA_V1: читаем листок назначений при Бирже, а не бланк\n    должности — бланк про должность, а это про сегодняшнюю работу.\n    """\n    return (_nazn_chitat().get(f"{ceh}/{slot}") or "").strip().upper()\n'),)
UI_STEZHKI = (
    ("панель принадлежит трейдеру", '    def set_active(i):\n        assets = state.get("loaded_assets", [])\n        if 0 <= i < len(assets):\n            state["active_asset"] = i\n            update_files_display()\n            a = assets[i]\n            ui.notify(f"Активен: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n', '    def _slot_agenta(agent_id: str) -> str:\n        """Слот, если это торговое место. Морж и прочие — не в счёт."""\n        row = _agent_row(roster, agent_id) or {}\n        slot = row.get("slot") or row.get("old_id") or agent_id\n        return slot if slot in ("A06", "A07", "A08") else ""\n\n    def set_active(i):\n        """PANEL_TREYDERA_V1: полка принадлежит АКТИВНОМУ трейдеру.\n\n        Кликнул человека наверху — панель стала его. Кликнул инструмент\n        — он взял его в работу. Переключился на другого — у того свой.\n        """\n        assets = state.get("loaded_assets", [])\n        if not (0 <= i < len(assets)):\n            return\n        state["active_asset"] = i\n        a = assets[i]\n        slot = _slot_agenta(state.get("active_agent", ""))\n        if slot:\n            try:\n                from vybor import naznachit as _nazn\n                ok, msg = _nazn(tseh_id, slot, a["symbol"])\n                imya = _agent_label(roster, state["active_agent"])\n                ui.notify(f"🎯 {imya}: {msg}" if ok else f"⚠ {msg}",\n                          type="positive" if ok else "negative")\n                print(f"[ПАНЕЛЬ] 🎯 {imya} ({slot}) ← {a[\'symbol\']}")\n            except Exception as e:\n                ui.notify(f"⚠ задание не записалось: {e}", type="negative")\n        else:\n            ui.notify(f"Активен: {a[\'symbol\']} {a[\'timeframe\']}", type="info")\n        update_files_display()\n'),
    ("смена трейдера — смена панели", '        state["active_agent"] = agent_id\n        update_avatar()\n        update_vitals()\n        update_avatar_states()\n        update_stats_panel()\n', '        state["active_agent"] = agent_id\n        update_avatar()\n        update_vitals()\n        update_avatar_states()\n        update_stats_panel()\n        # PANEL_TREYDERA_V1: панель котировок теперь его — перерисуем,\n        # чтобы было видно, чем он работает.\n        try:\n            update_files_display()\n            _slot = _slot_agenta(agent_id)\n            if _slot:\n                from vybor import instrument_dlya as _idl\n                _ins, _otk = _idl(tseh_id, _slot, "")\n                if _ins:\n                    ui.notify(f"🎯 {_agent_label(roster, agent_id)}: "\n                              f"{_ins} ({_otk})", type="info")\n        except Exception:\n            pass\n'),
)
RABOTA_STEZHKI = (("поле убрано из бланка", 'POLYA = [\n    ("название", "Название должности"),\n    ("чем_занят", "Чем занят — одной строкой"),\n    # INSTRUMENT_NAZNACHIT_ILI_SAM_V1: пусто — работник выберет сам\n    ("инструмент", "Инструмент (пусто — выберет сам)"),\n]\n', 'POLYA = [\n    ("название", "Название должности"),\n    ("чем_занят", "Чем занят — одной строкой"),\n]\n'),)


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


def pravit(put: Path, stezhki, suho: bool, imya: str,
           dobavka: str = "", myagko: bool = False) -> bool:
    if not put.exists():
        if myagko:
            print(f"  {imya}: нет — пропускаю")
            return True
        print(f"  x нет {imya}")
        return False
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return True
    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n != 1:
            if myagko:
                print(f"  {imya}: «{nazv}» не нашлось — пропускаю")
                return True
            print(f"  x {imya}: якорь «{nazv}» найден {n} раз — не трогаю")
            return False
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv}")
    if dobavka:
        tekst = tekst.rstrip("\n") + "\n" + dobavka
        print("    · листок назначений")
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return False
    if suho:
        print(f"  {imya}: + готов")
        return True
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: + накатано")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ПАНЕЛЬ ПРИНАДЛЕЖИТ ТРЕЙДЕРУ" +
          ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not VYBOR.exists():
        print("x нет Биржа/vybor.py — сперва postavit_vybor_metkoy")
        return 1
    if "instrument_mesta" not in VYBOR.read_text(encoding="utf-8"):
        print("x нет механизма инструмента — сперва "
              "patch_instrument_treydera.py")
        return 1

    ok = True
    print("\nназначения:")
    ok &= pravit(VYBOR, VYBOR_STEZHKI, suho, "vybor.py", DOBAVKA)
    print("\nкабинет:")
    ok &= pravit(UI, UI_STEZHKI, suho, "ui_torg.py")
    print("\nстраница работы:")
    ok &= pravit(STRANICA, RABOTA_STEZHKI, suho, "ui_rabota.py",
                 myagko=True)

    print("-" * 62)
    if not ok:
        return 1
    if suho:
        print("Это был показ. Накатывать: "
              "python patch_panel_treydera.py --sdelat")
        return 0
    print("Кликни трейдера наверху, потом инструмент слева — он взял его")
    print("в работу. Переключись на другого: панель покажет его.")
    print("Спроси словами: «каким инструментом ты работаешь».")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
