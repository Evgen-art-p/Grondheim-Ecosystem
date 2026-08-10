# -*- coding: utf-8 -*-
# KADR_I_VAKANSIYA_V1
"""
СВОЙ КАДР КАЖДОМУ СНИМКУ · ПУСТОЕ МЕСТО МОЛЧИТ

    python patch_kadr_i_vakansiya.py --suho    посмотреть
    python patch_kadr_i_vakansiya.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копии рядом: .bak_kadr_vakansiya.

── 1. КАРТИНКА БЫЛА ВЧЕРАШНЯЯ ──────────────────────────────────

    Рисовалка всегда писала в ОДИН файл с одним именем — Биржа/кадр.png.
    Браузер, увидев знакомый адрес, показывает то, что уже лежит у него
    в кармане, и новую картинку даже не спрашивает. Отсюда и случай
    08.08: подпись честно говорит GBPUSD H4, а на графике заголовок
    EURUSD H1 — старый кадр. То же самое могло уехать и трейдеру в
    глаз: он читает файл по тому же пути.

    Стало: каждый снимок получает своё имя и ложится в Биржа/кадры/ —
    инструмент, этаж, время. Двух одинаковых адресов больше нет.
    Папка не растёт: старые кадры подчищаются, последние двадцать
    остаются (по ним видно, что смотрели).

── 2. ПУСТОЕ МЕСТО ГОВОРИЛО ────────────────────────────────────

    Мозг слота — это РОЛЬ, и он запускался сам по себе, не спрашивая,
    сидит ли за столом человек. В логе 08.08 это видно голыми глазами:
    у A07 «за столом Илья, температура 0.58», а у A06 и A08 «вакансия,
    носителя нет» — и всё равно вердикт, вход, лот.

    Так быть не должно. Решение принимает житель, а не стул. Пустое
    место теперь честно молчит и говорит в ленте, что смотреть некому.
    Вердикт при этом обнуляется штатным порядком (Совет и так стирает
    вердикт того, кто не ответил) — старое решение с прошлого бара в
    рынок не поедет.

    Наняли человека — место заговорило снова, ничего перенакатывать
    не надо.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не трогает промпты, знания и рецепты входа — это следующий,
    отдельный разговор. Не трогает тестер.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
GRAFIK = KOREN / "Биржа" / "grafik.py"
SLOTY = (KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
         / "слоты")
SLOTS = ("A06", "A07", "A08")
MARKER = "# KADR_I_VAKANSIYA_V1 - marker"
BAK = ".bak_kadr_vakansiya"

# ── 1. свой кадр каждому снимку ───────────────────────────────
STAROE_KADR = '''    if kuda is None:
        kuda = Path(__file__).resolve().parent / "кадр.png"
'''

NOVOE_KADR = '''    if kuda is None:
        # KADR_I_VAKANSIYA_V1: своё имя каждому снимку. Один файл на
        # все кадры значил, что браузер и глаз трейдера получают по
        # знакомому адресу вчерашнюю картинку.
        from datetime import datetime as _dt
        _papka = Path(__file__).resolve().parent / "кадры"
        _papka.mkdir(parents=True, exist_ok=True)
        _chisto = lambda s: "".join(
            c for c in str(s) if c.isalnum() or c in "-_") or "нет"
        kuda = _papka / (f"{_chisto(symbol)}_{_chisto(timeframe)}_"
                         f"{_dt.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
        try:   # папка не должна расти без края: держим последние 20
            _bylye = sorted(_papka.glob("*.png"),
                            key=lambda f: f.stat().st_mtime)
            for _f in _bylye[:-20]:
                _f.unlink(missing_ok=True)
        except Exception:
            pass
'''

# ── 2. пустое место молчит (одинаково во всех трёх мозгах) ────
STAROE_SLOT = '''    try:
        import stol as _stol
'''

NOVOE_SLOT = '''    # KADR_I_VAKANSIYA_V1: пустое место молчит. Мозг — это РОЛЬ, и он
    # заводился, даже когда за столом никого не было: слот-вакансия
    # выносил вердикт, называл вход и лот. Решает житель, не стул.
    try:
        from nositel import dusha_slota as _dusha
        _kto_sidit = _dusha(_CEH, _SLOT)
    except Exception:
        _kto_sidit = None
    if not _kto_sidit:
        return {"ok": False,
                "error": "вакансия — за столом никого, смотреть некому",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(), "market": {}, "table": {}}

    try:
        import stol as _stol
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"    ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"    ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def odin_fail(put: Path, stezhki: list, suho: bool) -> str:
    imya = put.parent.name if put.name == "мозг.py" else put.name
    if not put.exists():
        print(f"  {imya}: файла нет — пропускаю")
        return "нет"
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  {imya}: уже накатано")
        return "уже"

    for nazv, staroe, novoe in stezhki:
        n = tekst.count(staroe)
        if n == 0:
            print(f"    ✗ {imya}: не нашёл якорь «{nazv}» — файл не трогаю")
            return "сбой"
        if n > 1:
            print(f"    ✗ {imya}: якорь «{nazv}» встречается {n} раз — "
                  f"файл не трогаю")
            return "сбой"
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"    · {nazv} — заменено")

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, imya):
        return "сбой"
    if suho:
        print(f"  {imya}: ✓ готов к накатке (сухой прогон)")
        return "готово"
    shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(tekst, encoding="utf-8")
    print(f"  {imya}: ✓ накатано (копия рядом: *{BAK})")
    return "готово"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not SLOTY.exists() or not GRAFIK.exists():
        print("✗ не вижу Биржу — запускай из КОРНЯ репо")
        return 1

    print("═" * 56)
    print("КАДР И ВАКАНСИЯ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 56)

    itogi = {}
    print("\nсвой кадр каждому снимку:")
    itogi["grafik.py"] = odin_fail(
        GRAFIK, [("своё имя кадру", STAROE_KADR, NOVOE_KADR)], a.suho)

    print("\nпустое место молчит:")
    for slot in SLOTS:
        itogi[slot] = odin_fail(
            SLOTY / slot / "мозг.py",
            [("проверка носителя", STAROE_SLOT, NOVOE_SLOT)], a.suho)

    print("\n" + "─" * 56)
    sboi = [k for k, v in itogi.items() if v == "сбой"]
    if sboi:
        print(f"⚠ не тронуты: {', '.join(sboi)} — якоря разошлись, "
              f"покажи мне эти файлы")
        return 1
    if a.suho:
        print("Сухой прогон прошёл. Накатывать: "
              "python patch_kadr_i_vakansiya.py")
        return 0

    print("Готово. Как проверить:")
    print("  · жми «Взгляд» дважды подряд по разным активам —")
    print("    картинка должна меняться, а не залипать;")
    print("  · жми РЫНОК — A06 и A08 должны честно сказать «вакансия»,")
    print("    отвечать останется один Илья (A07), пока он один за столом.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
