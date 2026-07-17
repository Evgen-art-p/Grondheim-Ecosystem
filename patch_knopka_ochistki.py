# -*- coding: utf-8 -*-
"""
patch_knopka_ochistki.py
════════════════════════════════════════════════════════════════════
КНОПКА ОЧИСТКИ В КАБИНЕТЕ — вместо ручного запуска двух скриптов

Слово Шефа: «эти скрипты же полезные... может, их в интерфейс на
кнопки посадим?» — да, это регулярное действие после каждого патча
кода, незачем лезть в консоль каждый раз.

ДОБАВЛЯЕТ: кнопку «🧹 ОЧИСТИТЬ» в тулбар рядом с УЧИТЬ. По клику —
диалог подтверждения (действие меняет файлы на диске, по правилу
подтверждения перед разрушающим действием), затем:
  • атлас (atlas_trading.jsonl) и лента (trading_pnl.jsonl) —
    АРХИВИРУЮТСЯ (переименовываются с меткой времени, не удаляются)
    и обнуляются — как ochistit_atlas.py;
  • открытые позиции в trading_state.json — очищаются — как
    ochistit_pozicii.py.
Логика — прямой порт этих двух скриптов внутрь кабинета, использует
те же ATLAS_PATH/PNL_PATH/load_trading_state/save_trading_state из
hooks.py (один источник правды, не дублируем константы путей).

ИДЕМПОТЕНТЕН (маркер KNOPKA_OCHISTKI_V1). Бэкап — один раз.
Запуск из корня Grondheim-Ecosystem:
    python patch_knopka_ochistki.py
"""
import io
import sys
from pathlib import Path

MARKER = "KNOPKA_OCHISTKI_V1"


def find_ui_torg() -> Path:
    for p in (Path("Биржа") / "ui_torg.py",
              Path("GRONDHEIM_CITY") / "Биржа" / "ui_torg.py"):
        if p.exists():
            return p
    print("[ПАТЧ] ✗ не найден ui_torg.py — запусти из корня")
    sys.exit(1)


HELPER = '''
                        # ''' + MARKER + ''': кнопка очистки истории — вместо ручного
                        # запуска ochistit_atlas.py/ochistit_pozicii.py из консоли.
                        # Диалог подтверждения — действие меняет файлы на диске
                        # (архивирует, не удаляет).
                        def _ochistit_istoriyu():
                            def _do_clean():
                                from hooks import (ATLAS_PATH, PNL_PATH,
                                                    load_trading_state,
                                                    save_trading_state)
                                from datetime import datetime as _dt
                                stamp = _dt.now().strftime("%Y%m%d_%H%M%S")
                                lines_out = []
                                for _path, _label in ((ATLAS_PATH, "Атлас"),
                                                       (PNL_PATH, "лента PnL")):
                                    if not _path.exists():
                                        lines_out.append(f"{_label}: не найден")
                                        continue
                                    _lines = [l for l in _path.read_text(
                                        encoding="utf-8").splitlines() if l.strip()]
                                    if not _lines:
                                        lines_out.append(f"{_label}: и так пуст")
                                        continue
                                    _archive = _path.with_name(
                                        f"{_path.stem}_archive_{stamp}{_path.suffix}")
                                    _archive.write_text(
                                        _path.read_text(encoding="utf-8"),
                                        encoding="utf-8")
                                    _path.write_text("", encoding="utf-8")
                                    lines_out.append(
                                        f"{_label}: архивировано {len(_lines)} строк")
                                _ts = load_trading_state()
                                _n_pos = len(_ts.get("positions", []) or [])
                                _ts["positions"] = []
                                save_trading_state(_ts)
                                lines_out.append(
                                    f"открытые позиции: очищено {_n_pos}")
                                ui.notify(" · ".join(lines_out),
                                          type="positive", timeout=8000)

                            with ui.dialog() as _dlg, ui.card().style(
                                    "background:#1a1f2e;"
                                    "border:1px solid rgba(255,255,255,0.1);"):
                                ui.label("Очистить историю сделок?").style(
                                    "font-weight:700;color:rgba(255,255,255,0.9);"
                                    "font-size:14px;")
                                ui.label(
                                    "Атлас и лента PnL будут АРХИВИРОВАНЫ (не "
                                    "удалены, лежат рядом с меткой времени) и "
                                    "обнулены. Открытые позиции очистятся. "
                                    "Используй перед чистым прогоном после "
                                    "правок кода."
                                ).style("color:rgba(255,255,255,0.55);"
                                        "font-size:12px;max-width:340px;"
                                        "margin:8px 0 14px 0;line-height:1.5;")
                                with ui.row().style(
                                        "gap:8px;justify-content:flex-end;"
                                        "width:100%;"):
                                    ui.button("Отмена",
                                              on_click=_dlg.close).props(
                                        "flat").style("color:rgba(255,255,255,0.5);")

                                    def _confirm():
                                        _do_clean()
                                        _dlg.close()
                                    ui.button("Очистить",
                                              on_click=_confirm).props(
                                        "color=negative").style(
                                        "font-weight:700;")
                            _dlg.open()

'''


def main():
    path = find_ui_torg()
    src = path.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"[ПАТЧ] ✓ {MARKER} уже применён — идемпотентно")
        return

    orig = src

    # 1. вставляем функцию-обработчик перед местом сборки тулбара.
    #    Якорь: строка объявления learn_btn (там же, где рубильник УЧИТЬ).
    def_anchor = (
        "                        # TORG_LEARN_SWITCH_V1: рубильник учёбы — "
        "рядом со СТОП\n"
    )
    if def_anchor not in src:
        print("[ПАТЧ] ✗ якорь learn_btn не найден — файл изменён?")
        sys.exit(2)
    src = src.replace(def_anchor, HELPER + def_anchor, 1)

    # 2. добавляем саму кнопку сразу после блока learn_btn (после его html-строки)
    btn_anchor = (
        '                        toolbar_refs["learn_btn"].on("click", '
        'lambda: toggle_learn())\n'
        '                        with toolbar_refs["learn_btn"]:\n'
        '                            ui.html("🎓 УЧИТЬ")\n'
    )
    if btn_anchor not in src:
        print("[ПАТЧ] ✗ якорь кнопки learn_btn не найден")
        sys.exit(3)
    btn_inject = (
        btn_anchor
        + '                        # ' + MARKER + ': кнопка очистки истории\n'
        + '                        _clean_btn = ui.element("div").style(\n'
        + '                            "display:flex;align-items:center;padding:6px 14px;'
          'border-radius:7px;"\n'
        + '                            "font-size:12px;font-weight:700;cursor:pointer;"\n'
        + '                            "background:rgba(255,180,0,0.08);'
          'color:rgba(255,180,0,0.85);"\n'
        + '                            "border:1px solid rgba(255,180,0,0.3);")\n'
        + '                        _clean_btn.on("click", lambda: _ochistit_istoriyu())\n'
        + '                        with _clean_btn:\n'
        + '                            ui.html("🧹 ОЧИСТИТЬ")\n'
    )
    src = src.replace(btn_anchor, btn_inject, 1)

    import ast
    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"[ПАТЧ] ✗ правка ломает синтаксис ({e}) — НЕ пишу")
        sys.exit(4)

    bak = path.with_suffix(".py.bak_ochistka_knopka")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")
        print(f"[ПАТЧ] 💾 бэкап: {bak.name}")

    path.write_text(src, encoding="utf-8")
    print("[ПАТЧ] ✅ Кнопка «🧹 ОЧИСТИТЬ» добавлена рядом с УЧИТЬ.")
    print("[ПАТЧ]    Клик → диалог подтверждения → архивирует и обнуляет")
    print("[ПАТЧ]    Атлас/PnL, чистит открытые позиции.")


if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass
    main()
