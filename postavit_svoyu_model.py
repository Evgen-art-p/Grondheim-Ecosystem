# -*- coding: utf-8 -*-
# SVOYA_MODEL_POLEM_V1
"""
Слово Шефа (06.09): в старом городе было пустое поле, куда он сам
вписывал модель — сейчас есть только список на 6 вшитых имён
(MODELS_CATALOG), а у OpenRouter моделей без счёта. Добавляет рядом с
выпадающим списком маленькое поле — вписал slug (например
`openai/gpt-4o` или `anthropic/claude-opus-4.1`), нажал Enter или ➜ —
дальше идёт этот же slug, `llm.set_model()` не проверяет список,
берёт любую непустую строку.

Список (MODELS_CATALOG) НЕ убирается — быстрый выбор из шести остаётся
для повседневного, поле — для разового сравнения без правки кода.

ПОПУТНО ПОЧИНЕНО в Академии: там `on_model_change` только клал
`state["model"]`, но НИКОГДА не звал `llm.set_model()` — выбор в
выпадающем списке в Академии визуально менялся, а реально работала
всегда одна и та же модель (что бы ни лежало в `_CURRENT_MODEL` из
llm.py — общего для всего процесса, включая Биржу). Без этой починки
своё поле в Академии тоже ничего бы не меняло.

Запускать из корня репозитория:
    python postavit_svoyu_model.py
Идемпотентен по маркеру в каждом файле.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "SVOYA_MODEL_POLEM_V1"

BIRZHA_FILE = "Биржа/ui_torg.py"
BIRZHA_ANCHOR = (
    '                with ui.element("div").style(\n'
    '                    "margin-right:10px; background:rgba(255,255,255,0.06); "\n'
    '                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"\n'
    '                ):\n'
    '                    _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n'
    '                    ui.select(_opts, value=state["model"], on_change=on_model_change) \\\n'
    "                        .props('dense borderless dark options-dense').style(\"min-width:190px;\")\n"
)
BIRZHA_INSERT = (
    "                svoya_model_ref: dict[str, Any] = {\"element\": None}\n\n"
    "                def _svoya_model(_e=None):\n"
    "                    val = (svoya_model_ref[\"element\"].value or \"\").strip()\n"
    "                    if not val:\n"
    "                        return\n"
    "                    state[\"model\"] = val\n"
    "                    llm.set_model(val)\n"
    "                    ui.notify(f\"модель: {val}\", type=\"info\")\n\n"
    "                with ui.row().style(\"gap:2px; align-items:center; margin-right:10px;\"):\n"
    "                    svoya_model_ref[\"element\"] = ui.input(\n"
    "                        placeholder=\"своя модель с OpenRouter…\").props(\n"
    "                        'dense borderless dark').style(\n"
    "                        \"min-width:170px; color:rgba(255,255,255,0.85); \"\n"
    "                        \"font-size:11px; background:rgba(255,255,255,0.06); \"\n"
    "                        \"border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:2px 8px;\")\n"
    "                    svoya_model_ref[\"element\"].on(\"keydown.enter\", _svoya_model)\n"
    "                    ui.button(\"➜\", on_click=_svoya_model).props(\"flat dense size=sm\").style(\n"
    "                        \"color:rgba(0,255,136,0.75);\")\n\n"
)

AKADEMIYA_FILE = "Академия/ui_akademia.py"
AKADEMIYA_OLD_HANDLER = (
    "    def on_model_change(e):\n"
    "        state[\"model\"] = e.value\n"
)
AKADEMIYA_NEW_HANDLER = (
    "    def on_model_change(e):\n"
    "        state[\"model\"] = e.value\n"
    "        # SVOYA_MODEL_POLEM_V1: раньше здесь модель менялась только на\n"
    "        # экране, а реально звалась всегда одна и та же (глобальная\n"
    "        # _CURRENT_MODEL из llm.py, общая с Биржей).\n"
    "        try:\n"
    "            import sys as _sys\n"
    "            from pathlib import Path as _Path\n"
    "            _repo = _Path(__file__).resolve().parent.parent\n"
    "            if str(_repo / \"Биржа\") not in _sys.path:\n"
    "                _sys.path.insert(0, str(_repo / \"Биржа\"))\n"
    "            import llm as _llm\n"
    "            _llm.set_model(e.value)\n"
    "        except Exception as _ex:\n"
    "            print(f\"[МОДЕЛЬ] не переключилась: {_ex}\")\n"
)
AKADEMIYA_ANCHOR = (
    '                    with ui.element("div").classes("amodel-sel").style("margin-right:6px;"):\n'
    '                        _opts = {m["id"]: f\'{m["name"]} ({m["price"]})\' for m in MODELS_CATALOG}\n'
    '                        ui.select(_opts, value=state["model"], on_change=on_model_change) \\\n'
    "                            .props('dense borderless dark options-dense').style(\"min-width:180px;\")\n"
)
AKADEMIYA_INSERT = (
    "                    svoya_model_ref: dict = {\"element\": None}\n\n"
    "                    def _svoya_model(_e=None):\n"
    "                        val = (svoya_model_ref[\"element\"].value or \"\").strip()\n"
    "                        if not val:\n"
    "                            return\n"
    "                        state[\"model\"] = val\n"
    "                        try:\n"
    "                            import sys as _sys\n"
    "                            from pathlib import Path as _Path\n"
    "                            _repo = _Path(__file__).resolve().parent.parent\n"
    "                            if str(_repo / \"Биржа\") not in _sys.path:\n"
    "                                _sys.path.insert(0, str(_repo / \"Биржа\"))\n"
    "                            import llm as _llm\n"
    "                            _llm.set_model(val)\n"
    "                            ui.notify(f\"модель: {val}\", type=\"info\")\n"
    "                        except Exception as _ex:\n"
    "                            print(f\"[МОДЕЛЬ] не переключилась: {_ex}\")\n\n"
    "                    with ui.row().style(\"gap:2px; align-items:center; margin-right:6px;\"):\n"
    "                        svoya_model_ref[\"element\"] = ui.input(\n"
    "                            placeholder=\"своя модель…\").props(\n"
    "                            'dense borderless dark').style(\n"
    "                            \"min-width:150px; color:rgba(255,255,255,0.85); \"\n"
    "                            \"font-size:11px; background:rgba(255,255,255,0.06); \"\n"
    "                            \"border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:2px 8px;\")\n"
    "                        svoya_model_ref[\"element\"].on(\"keydown.enter\", _svoya_model)\n"
    "                        ui.button(\"➜\", on_click=_svoya_model).props(\"flat dense size=sm\").style(\n"
    "                            \"color:rgba(0,255,136,0.75);\")\n\n"
)


def patch_birzha(root: Path) -> str:
    path = root / BIRZHA_FILE
    if not path.exists():
        return f"НЕТ ФАЙЛА: {path}"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return f"уже стоит: {path}"
    if text.count(BIRZHA_ANCHOR) != 1:
        return f"ЯКОРЬ НЕ НАЙДЕН (не тронуто): {path}"
    bak = path.with_suffix(path.suffix + ".bak_svoya_model")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    text = text.replace(BIRZHA_ANCHOR, BIRZHA_ANCHOR + BIRZHA_INSERT, 1)
    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    path.write_text(text, encoding="utf-8")
    return f"ПРИМЕНЁН: {path}"


def patch_akademiya(root: Path) -> str:
    path = root / AKADEMIYA_FILE
    if not path.exists():
        return f"НЕТ ФАЙЛА: {path}"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return f"уже стоит: {path}"
    if text.count(AKADEMIYA_OLD_HANDLER) != 1:
        return f"ЯКОРЬ (обработчик) НЕ НАЙДЕН (не тронуто): {path}"
    if text.count(AKADEMIYA_ANCHOR) != 1:
        return f"ЯКОРЬ (селектор) НЕ НАЙДЕН (не тронуто): {path}"
    bak = path.with_suffix(path.suffix + ".bak_svoya_model")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    text = text.replace(AKADEMIYA_OLD_HANDLER, AKADEMIYA_NEW_HANDLER, 1)
    text = text.replace(AKADEMIYA_ANCHOR, AKADEMIYA_ANCHOR + AKADEMIYA_INSERT, 1)
    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    path.write_text(text, encoding="utf-8")
    return f"ПРИМЕНЁН: {path}"


def main() -> None:
    root = Path(__file__).resolve().parent
    print(patch_birzha(root))
    print(patch_akademiya(root))


if __name__ == "__main__":
    main()
