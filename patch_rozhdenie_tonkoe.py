# patch_rozhdenie_tonkoe.py
# ROZHDENIE_TONKOE_V1 · рождение ТОНКОЙ ЛИЧНОСТЬЮ в КОВЧЕГ (паспорт-пирог, слой 1)
# ─────────────────────────────────────────────────────────────
# Закон (Шеф): паспорт = слоёный пирог.
#   СЛОЙ 1 ЛИЧНОСТЬ — рождается. Чистая Лия. Маски НЕТ.
#   СЛОЙ 2 ПРОПИСКА — пусто при рождении (null). Брат впишет позже.
#   Рождён → ПРЕБЫВАЕТ в ковчеге (прописки нет, не определён).
#
# Делает три вещи:
#   1. zavesti_sloi → тонкое рождение в жители/ковчег/{имя}/:
#        passport.json = ЛИЧНОСТЬ (маска вычищена, "прописка": null)
#        маски/работа/mask.json = маска (слой 2, _активна: false)
#   2. rodit_pasport_kusochek → отключаем (старый путь по профессии не нужен,
#      дом теперь в ковчеге; иначе плодит лишний файл-кусочек по профессии).
#   3. Печать _Creator_Seal_Hash — НЕ трогаем (живёт в save_object, блокчейн заложен).
#
# Идемпотентно. Бэкап в .bak_tonkoe. `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import ast, shutil, sys
from pathlib import Path

MARKER = "ROZHDENIE_TONKOE_V1"
TARGET = Path(__file__).resolve().parent / "ui_registry.py"

NEW_FUNC = '''def zavesti_sloi(obj: dict) -> str:  # ROZHDENIE_TONKOE_V1
    """
    Рождение ТОНКОЙ ЛИЧНОСТЬЮ в КОВЧЕГ (паспорт-пирог, слой 1).

    Закон: паспорт = пирог. Рождается слой 1 (личность). Маска и прописка —
    НЕ при рождении. Брат впишет прописку позже (слой 2).

        GRONDHEIM_CITY/жители/ковчег/{имя}/      ← все новорождённые сюда
            passport.json   ← ЛИЧНОСТЬ (маска вычищена, "прописка": null)
            core/ resonance/ sensory/ archive/
            маски/работа/mask.json  ← маска (слой 2, _активна: false)

    Житель ПРЕБЫВАЕТ в ковчеге, пока Брат не пропишет. Возвращает путь дома.
    """
    import json as _json
    name = _safe_name(obj.get("Official_Name", ""))
    if name == "без_имени":
        return ""

    # ── ДОМ В КОВЧЕГ — не по профессии! Все пребывающие вместе. ──
    dom = ZHITELI_DIR / "ковчег" / name
    dom.mkdir(parents=True, exist_ok=True)

    # 4 слоя памяти — наш закон
    for sloy in ("core", "resonance", "sensory", "archive"):
        (dom / sloy).mkdir(parents=True, exist_ok=True)

    # ── РАСЦЕПЛЕНИЕ: маска (слой 2) уезжает в маски/работа/, пока не активна ──
    maska_rabota = dom / "маски" / "работа"
    maska_rabota.mkdir(parents=True, exist_ok=True)
    _MASKA_POLYA = ("Social_Rank", "Profession", "Area_of_Responsibility",
                    "Access_Level", "Workshop_ID", "Turbo_Role", "Quarter",
                    "Core_Phrase")
    _maska = {"_note": "маска 'работа' (слой 2 паспорта). Активирует Брат при прописке.",
              "_активна": False}
    for _k in _MASKA_POLYA:
        _maska[_k] = obj.get(_k, "")
    (maska_rabota / "mask.json").write_text(
        _json.dumps(_maska, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── ЯКОРЬ-ЛИЧНОСТЬ: вычищаем маску, ставим прописку=null ──
    lichnost = dict(obj)
    for _k in _MASKA_POLYA:
        lichnost.pop(_k, None)          # маска ушла в файл
    lichnost["прописка"] = None         # ПРЕБЫВАЕТ в ковчеге (слой 2 пуст)

    pasport_json = _json.dumps(lichnost, ensure_ascii=False, indent=2)
    (dom / "passport.json").write_text(pasport_json, encoding="utf-8")
    (dom / "core" / "anchor.json").write_text(pasport_json, encoding="utf-8")

    # пустые заготовки слоёв (память придёт с движком)
    (dom / "resonance" / "emotional_weights.json").write_text("{}", encoding="utf-8")
    (dom / "resonance" / "event_log.jsonl").write_text("", encoding="utf-8")
    (dom / "sensory" / "sensory_memory.json").write_text(
        _json.dumps({"entries": [], "_note": "оперативка · пусто при рождении"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (dom / "archive" / "archive.jsonl").write_text("", encoding="utf-8")

    (dom / "_слои_заведены.txt").write_text(
        "core · resonance · sensory · archive\\n"
        "ПРЕБЫВАЕТ в ковчеге · прописки нет · маска в маски/работа/", encoding="utf-8")

    # ── фото из временной → в дом (avatar) ──
    try:
        import shutil as _sh
        _src = obj.get("_image_path", "") or ""
        if _src and Path(_src).exists():
            _ext = Path(_src).suffix or ".png"
            _dst = dom / f"avatar{_ext}"
            _sh.copyfile(_src, _dst)
            lichnost["_image_path"] = str(_dst)
            lichnost["avatar"] = f"avatar{_ext}"
            try:
                Path(_src).unlink(missing_ok=True)
            except Exception:
                pass
            _pj = _json.dumps(lichnost, ensure_ascii=False, indent=2)
            (dom / "passport.json").write_text(_pj, encoding="utf-8")
            (dom / "core" / "anchor.json").write_text(_pj, encoding="utf-8")
    except Exception:
        pass

    return str(dom)
'''


def main():
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — положи патч в корень репо рядом с ui_registry.py")
        sys.exit(1)
    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже на месте — пропускаю")
        return

    lines = src.split("\n")
    # 1) заменить zavesti_sloi целиком
    start = next((i for i, ln in enumerate(lines) if ln.startswith("def zavesti_sloi(obj: dict)")), None)
    if start is None:
        print("✗ не нашёл def zavesti_sloi — стоп"); sys.exit(1)
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("def ")), None)
    if end is None:
        print("✗ не нашёл конец zavesti_sloi — стоп"); sys.exit(1)
    lines = lines[:start] + NEW_FUNC.split("\n") + [""] + lines[end:]
    src = "\n".join(lines)

    # 2) отключить старый rodit_pasport_kusochek в save_object
    #    (дом теперь в ковчеге, кусочек по профессии не нужен)
    old_call = "                    try:\n                        _kus = rodit_pasport_kusochek(obj)"
    new_call = "                    try:\n                        _kus = \"\"  # ROZHDENIE_TONKOE_V1: кусочек по профессии отключён (дом в ковчеге)"
    if old_call in src:
        src = src.replace(old_call, new_call, 1)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"✗ синтаксис: {e}"); sys.exit(1)

    if not TARGET.with_suffix(".py.bak_tonkoe").exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".py.bak_tonkoe"))
    TARGET.write_text(src, encoding="utf-8")
    print(f"✓ {MARKER}: рождение тонкой личностью в ковчег, маска в слой 2, кусочек отключён")


if __name__ == "__main__":
    main()
