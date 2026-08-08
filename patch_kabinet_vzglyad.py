# -*- coding: utf-8 -*-
# KABINET_VZGLYAD_V1
"""
ВЗГЛЯД — кабинет и трейдер смотрят ОДНО И ТО ЖЕ, и это видно.

    python patch_kabinet_vzglyad.py --suho    посмотреть
    python patch_kabinet_vzglyad.py           накатить

Запускать из КОРНЯ репо. Идемпотентно. Копия рядом: .bak_vzglyad.

ЧТО БЫЛО НЕ ТАК

    Кнопка РЫНОК звала Совет по золоту на четырёх часах — зашито в
    код словами "XAUUSD", "H4". Кнопка кадра рисовала евро на часовых
    — тоже зашито, потому что она спрашивала у кабинета ключи, которых
    в нём отродясь не было, и молча падала на запасной вариант.

    То есть Шеф смотрел одну картинку, трейдер работал по другому
    инструменту, а полка активов слева не значила ничего. Проверить
    роль в таких условиях нельзя: они не спорят — они про разное.

ЧТО СТАЛО

    Одна пара «инструмент + этаж» на весь кабинет, и берётся она
    оттуда, где Шеф её и выбирает — с полки активов (клик по ТФ
    внутри папки инструмента). Ничего нового заводить не надо: полка
    уже помнит выбор, его просто никто не спрашивал.

    От неё кормятся оба: и кадр, и Совет. Значит трейдер смотрит
    ровно ту картинку, что висит у Шефа на экране.

    И это ВИДНО. Под кадром печатается строка «что смотрим»:
    инструмент, этаж, кран (РЕАЛ или ТЕСТЕР) и время. Кнопка стала
    называться «Взгляд» — она и есть снимок момента: посмотреть
    самому, прежде чем отдавать глазу.

    Заодно убрано «бужу Искру» из уведомления: Искры больше нет,
    а строка осталась и обманывала глаз.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
    Не трогает мозги, стол, найм и котировки. Только кабинет.
    Полка пуста — работаем как раньше, по золоту на H4, и кабинет
    честно об этом говорит.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
CEL = KOREN / "Биржа" / "ui_torg.py"
MARKER = "# KABINET_VZGLYAD_V1 - marker"
BAK = ".bak_vzglyad"

# ── 1. откуда берём инструмент и этаж ─────────────────────────
STAROE_AKTIV = '''        """Что сейчас на полке: символ и рабочий этаж."""
        try:
            s = state.get("symbol") or state.get("актив") or "EURUSD"
            tf = state.get("timeframe") or state.get("tf") or "H1"
            return s, tf
        except Exception:
            return "EURUSD", "H1"
'''

NOVOE_AKTIV = '''        """Что сейчас на полке: символ и рабочий этаж.

        KABINET_VZGLYAD_V1: спрашиваем ПОЛКУ — тот самый актив, по
        которому Шеф кликнул слева. Раньше здесь спрашивались ключи,
        которых в кабинете нет, и ответ всегда был один и тот же
        (EURUSD H1) — кадр жил своей жизнью, Совет своей.
        Полка пуста — честный запасной вариант, как было в кнопке.
        """
        try:
            assets = state.get("loaded_assets", []) or []
            i = state.get("active_asset")
            if assets and i is not None and 0 <= i < len(assets):
                a = assets[i]
                s = (a.get("symbol") or "").strip()
                tf = (a.get("timeframe") or "").strip()
                if s and tf:
                    return s, tf
        except Exception:
            pass
        return "XAUUSD", "H4"
'''

# ── 2. Совет смотрит туда же ──────────────────────────────────
STAROE_SOVET = '''        try:
            loop = asyncio.get_event_loop()
            _market_future = loop.run_in_executor(
                None, lambda: council.wake_council("XAUUSD", "H4", on_event=_on_event))
'''

NOVOE_SOVET = '''        # KABINET_VZGLYAD_V1: инструмент и этаж — с полки, не из кода.
        # Одна пара на кадр и на трейдера: смотрят одно и то же.
        _sym_now, _tf_now = _aktivnyy_rynok()
        ui.notify(f"👁 смотрим {_sym_now} {_tf_now}", type="info")
        try:
            loop = asyncio.get_event_loop()
            _market_future = loop.run_in_executor(
                None, lambda: council.wake_council(_sym_now, _tf_now,
                                                   on_event=_on_event))
'''

# ── 3. под кадром — что именно смотрим ────────────────────────
STAROE_KADR = '''            ui.image(str(p)).style("width:100%; height:auto;")
        return p
'''

NOVOE_KADR = '''            ui.image(str(p)).style("width:100%; height:auto;")
            # KABINET_VZGLYAD_V1: подпись под кадром. Что смотрим и
            # каким краном — иначе глазом реал от истории не отличить.
            _kran = "ТЕСТЕР" if state.get("mode") == "tester" else "РЕАЛ"
            ui.label(f"👁 {symbol} · {tf} · {_kran}").style(
                "color:rgba(139,233,253,0.75); font-size:11px; "
                "letter-spacing:0.06em; padding-top:6px;")
        return p
'''

# ── 4. мелочи, которые обманывают глаз ────────────────────────
STAROE_NOTIFY = '        ui.notify("📡 Поднимаю контур, бужу Искру...", type="info")\n'
NOVOE_NOTIFY = '        ui.notify("📡 Поднимаю контур...", type="info")\n'

STAROE_KNOPKA = '                    ui.button("📈 кадр", on_click=lambda: pokazat_kadr()).props(\n'
NOVOE_KNOPKA = '                    ui.button("👁 Взгляд", on_click=lambda: pokazat_kadr()).props(\n'

STAROE_ZAGLUSHKA = '                                ui.label("Кадр появится здесь — жми «📈 кадр»")\n'
NOVOE_ZAGLUSHKA = '                                ui.label("Кадр появится здесь — жми «👁 Взгляд»")\n'

STEZHKI = (
    ("инструмент с полки", STAROE_AKTIV, NOVOE_AKTIV),
    ("Совет смотрит туда же", STAROE_SOVET, NOVOE_SOVET),
    ("подпись под кадром", STAROE_KADR, NOVOE_KADR),
    ("убрать «бужу Искру»", STAROE_NOTIFY, NOVOE_NOTIFY),
    ("кнопка «Взгляд»", STAROE_KNOPKA, NOVOE_KNOPKA),
    ("заглушка кадра", STAROE_ZAGLUSHKA, NOVOE_ZAGLUSHKA),
)


def proverit_python(tekst: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vremenny = f.name
    try:
        py_compile.compile(vremenny, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vremenny).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    print("═" * 56)
    print("ВЗГЛЯД · кабинет" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 56)

    if not CEL.exists():
        print("✗ не вижу Биржа/ui_torg.py — запускай из КОРНЯ репо")
        return 1

    tekst = CEL.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  уже накатано — ничего не трогаю")
        return 0

    ne_nashlos = []
    for imya, staroe, novoe in STEZHKI:
        n = tekst.count(staroe)
        if n == 0:
            ne_nashlos.append(imya)
            continue
        if n > 1:
            print(f"  ✗ «{imya}» встречается {n} раз — якорь неточен, "
                  f"файл не трогаю")
            return 1
        tekst = tekst.replace(staroe, novoe, 1)
        print(f"  · {imya} — заменено")

    if ne_nashlos:
        print(f"  ✗ не нашёл якоря: {', '.join(ne_nashlos)} — "
              f"файл не трогаю")
        return 1

    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"

    if not proverit_python(tekst):
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Накатывать: "
              "python patch_kabinet_vzglyad.py")
        return 0

    shutil.copy2(CEL, CEL.with_suffix(CEL.suffix + BAK))
    CEL.write_text(tekst, encoding="utf-8")
    print(f"\n✓ накатано (копия рядом: ui_torg.py{BAK})")
    print("\nКак проверить:")
    print("  1. открой кабинет, кликни слева нужный ТФ у нужного актива;")
    print("  2. жми «👁 Взгляд» — под картинкой должно быть написано,")
    print("     что именно смотришь и каким краном;")
    print("  3. жми РЫНОК — вверху мелькнёт «смотрим <актив> <этаж>»,")
    print("     и в отчётах агентов будет тот же инструмент.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
