#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ZAKON_KARTRIDZHA_V1
"""
ЗАКОН КАРТРИДЖА ДЛЯ СОВЕТА — вставил и работает, вынул и нет.

    python patch_zakon_kartridzha.py            посмотреть
    python patch_zakon_kartridzha.py --sdelat   накатить

Запускать из КОРНЯ.

ЧТО БЫЛО НЕ ТАК

    Закон Картриджа записан у тебя прямо в мозге A06: слот несёт с
    собой всё, а кто он и в каком цехе — узнаёт из своего пути. По
    этому закону в городе живёт всё: Академия не держит реестра курсов,
    посты сканируются, локации сканируются, страница работы сканирует.

    Кроме одного места. В `Биржа/council.py` лежал вбитый список трёх
    трейдеров с именами их функций. Это и была причина, по которой
    картридж не вставлялся: положи папку хоть десять раз — Совет зовёт
    троих поимённо и о новых не знает.

ЧТО СТАНЕТ

    Совет сканирует цех. Есть папка слота с мозгом — трейдер за столом.
    Нет папки — нет трейдера. Три, десять, женский цех и мужской — код
    трогать не надо.

    Как Совет понимает, как звать новый мозг:
      1. смотрит запись слота в манифесте цеха: «движок» (какую функцию
         звать) и «ключ» (приставка полей решения);
      2. записи нет — зовёт функцию `run`, а ключ выводит из имени
         слота.

    Старым троим менять ничего не пришлось: их движок и ключ вписаны в
    манифест этим же патчем, мозги не тронуты вовсе.

ПРО НОВЫЙ КАРТРИДЖ

    Папка `слоты/{имя}/` с мозгом, промптом и знаниями — и он в Совете.
    Если мозг скопирован со старого, впиши ему в манифесте свой «ключ»,
    иначе двое будут писать вердикт в одну строку стола.

    Целый цех копируется вместе с манифестом и работает сразу: там уже
    и движки, и ключи.
"""
import argparse
import ast
import json
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
SOVET = KOREN / "Биржа" / "council.py"
MANIFEST = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "manifest.json")
MARKER = "# ZAKON_KARTRIDZHA_V1 - marker"
BAK = ".bak_kartridzh"

# что вписать старым троим, чтобы Совет звал их как раньше
STARYE = {
    "A06": ("run_brut", "brut"),
    "A07": ("run_avan", "avan"),
    "A08": ("run_cons", "cons"),
}

STEZHKI = (
    ('сканер вместо списка', '# трое трейдеров за столом\n_TRADERS = [\n    ("A06", "торговый_хаос", "A06", "run_brut", "brut"),\n    ("A07", "торговый_хаос", "A07", "run_avan", "avan"),\n    ("A08", "торговый_хаос", "A08", "run_cons", "cons"),\n]\n', '# ═══════════════════════════════════════════════════════════\n# ZAKON_KARTRIDZHA_V1 — СОВЕТ БОЛЬШЕ НЕ ДЕРЖИТ СПИСКА\n# ═══════════════════════════════════════════════════════════\n# Здесь лежал вбитый список трёх трейдеров. Это было единственное\n# место в городе, где Закон Картриджа нарушался: слот несёт с собой\n# всё, но Совет звал троих ПОИМЁННО — и новый картридж, сколько его\n# ни клади в папку, никто не звал.\n#\n# Теперь Совет СКАНИРУЕТ цех, как всё прочее в городе сканирует папки.\n# Вставил картридж — он в Совете. Вынул — его нет. Хоть три, хоть\n# десять.\n#\n# Как Совет понимает, как звать мозг:\n#   1. запись слота в манифесте цеха: «движок» (какую функцию звать)\n#      и «ключ» (приставка полей решения);\n#   2. записи нет — зовём функцию `run`, ключ выводим из имени слота.\n_CEH_TORGOVYY = "торговый_хаос"\n\n\ndef _dver_mozga(brain, skazano: str = "") -> str:\n    """Как звать этот мозг. Сказано в манифесте — зовём так."""\n    if skazano and getattr(brain, skazano, None):\n        return skazano\n    if getattr(brain, "run", None):\n        return "run"                       # общая дверь картриджа\n    est = [n for n in dir(brain)\n           if n.startswith("run_") and callable(getattr(brain, n, None))]\n    return est[0] if len(est) == 1 else ""\n\n\ndef _treydery(ceh_id: str = _CEH_TORGOVYY) -> list:\n    """Кто сегодня за столом. Списка не держим — смотрим цех."""\n    korn = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh_id\n    sloty_dir = korn / "слоты"\n    if not sloty_dir.is_dir():\n        return []\n\n    skazano = {}\n    try:\n        m = json.loads((korn / "manifest.json").read_text(encoding="utf-8"))\n        for s in m.get("слоты", []) or []:\n            if s.get("слот"):\n                skazano[s["слот"]] = s\n    except Exception:\n        pass\n\n    imena = list(skazano) + [d.name for d in sorted(sloty_dir.iterdir())\n                             if d.is_dir() and d.name not in skazano]\n    out = []\n    for slot in imena:\n        if not (sloty_dir / slot / "мозг.py").exists():\n            continue                       # папка без мозга — не картридж\n        zapis = skazano.get(slot, {})\n        brain = _slot_brain(ceh_id, slot)\n        if brain is None:\n            continue\n        dver = _dver_mozga(brain, zapis.get("движок", ""))\n        if not dver:\n            print(f"[СОВЕТ] не понял, как звать {ceh_id}/{slot} — пропускаю. "\n                  f"Впиши «движок» в манифест цеха.")\n            continue\n        klyuch = (zapis.get("ключ") or slot).strip().lower()\n        out.append((slot, ceh_id, slot, dver, klyuch))\n    return out\n\n\ndef _stol_klyuchi(ceh_id: str = _CEH_TORGOVYY) -> dict:\n    """слот -> ключ на столе. Тоже из сканера, не из головы."""\n    return {slot: pre for _aid, _c, slot, _fn, pre in _treydery(ceh_id)}\n'),
    ('ключи стола из сканера', '# кто где живёт в столе (проверено на диске: A06/A07/A08 :: мозг.py)\n_STOL_KEY = {"A06": "brut", "A07": "avan", "A08": "cons"}\n', '# ZAKON_KARTRIDZHA_V1: было вбито {"A06": "brut", ...}. Теперь ключи\n# приходят от того же сканера, что и сами трейдеры, — один источник.\n'),
    ('стирание вердикта', '    key = _STOL_KEY.get(slot)\n', '    key = _stol_klyuchi().get(slot)\n'),
    ('зовём всех, кто в цехе', '    # ── трое трейдеров ──\n    for aid, ceh, slot, fn, pre in _TRADERS:\n', '    # ── трейдеры: сколько картриджей в цехе, столько и зовём ──\n    _za_stolom = _treydery()\n    if not _za_stolom:\n        print("[СОВЕТ] в цехе нет ни одного картриджа с мозгом")\n    for aid, ceh, slot, fn, pre in _za_stolom:\n'),
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


def pravit_manifest(suho: bool) -> bool:
    if not MANIFEST.exists():
        print("  x манифеста торгового цеха нет")
        return False
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  x манифест не читается: {e}")
        return False
    tronuli = 0
    for s in m.get("слоты", []) or []:
        imya = s.get("слот")
        if imya in STARYE and not s.get("движок"):
            s["движок"], s["ключ"] = STARYE[imya]
            tronuli += 1
    if not tronuli:
        print("  манифест: движок и ключ уже прописаны")
        return True
    print(f"  манифест: впишу движок и ключ для {tronuli} слотов")
    if not suho:
        shutil.copy2(MANIFEST, MANIFEST.with_suffix(".json" + BAK))
        MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ЗАКОН КАРТРИДЖА ДЛЯ СОВЕТА" +
          ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not SOVET.exists():
        print("x не вижу Биржа/council.py — запускай из КОРНЯ")
        return 1

    print("\nманифест цеха:")
    if not pravit_manifest(suho):
        return 1

    print("\nСовет:")
    tekst = SOVET.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано")
        return 0
    if "\nimport json" not in tekst:
        tekst = tekst.replace("import importlib",
                              "import json\nimport importlib", 1)
        print("  + json для чтения манифеста")
    for nazv, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n != 1:
            print(f"  x якорь «{nazv}» найден {n} раз — файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  + {nazv}")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "council.py"):
        return 1
    if suho:
        print("\nЭто был показ. Накатывать: "
              "python patch_zakon_kartridzha.py --sdelat")
        return 0

    shutil.copy2(SOVET, SOVET.with_suffix(SOVET.suffix + BAK))
    SOVET.write_text(tekst, encoding="utf-8")
    print(f"\n+ накатано (копия рядом: council.py{BAK})")
    print("\nЖми РЫНОК — должно быть как раньше, трое.")
    print("Потом положи четвёртую папку в слоты/ и жми снова:")
    print("Совет позовёт и её, без единой правки кода.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
