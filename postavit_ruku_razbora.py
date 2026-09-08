# -*- coding: utf-8 -*-
# RUKA_RAZBORA_V1
"""
ДОСЫЛ: РУКА `razbor_struktury`, КОТОРАЯ НЕ ВСТАЛА.

ЧТО СЛУЧИЛОСЬ (честно, это промах Брата)

Патч `postavit_polku_po_momentu.py` делал две вещи: переносил разметку
в подпапку `знания/ведение/` и ставил руку, которая её оттуда достаёт.

Перенос прошёл — файлы уехали. А рука не встала: патч метил в строку
`itog = {"stol_na_etazhe": _stol,`, которую к тому моменту уже изменил
`postavit_ruki_zakladok.py` (он вписал туда три свои руки первыми).
Кусок перестал совпадать, патч честно отказался ставить руку и вышел —
но файлы к тому времени уже переехали.

Итог: разметка спрятана, а достать её нечем. Этот патч ставит только
руку. Ничего не переносит.

ЧТО СТАВИТ

`razbor_struktury` — достаёт полку `знания/ведение/` (разметка волн,
три места входа по риску, отношения между волнами). Это инструмент
ВЕДЕНИЯ: зови, когда уже в рынке и прикидываешь, где ты в структуре и
сколько ещё можно пройти. Перед входом не нужно — там вопрос один:
кончился ход или нет.

Запускать из корня репозитория:
    python postavit_ruku_razbora.py

Идемпотентен (маркер RUKA_RAZBORA_V1). Рядом .bak.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "RUKA_RAZBORA_V1"
RUKI = "Биржа/ruki_treydera.py"


SHEMA_OLD = '''        {"type": "function", "function": {
            "name": "chemu_uchili",'''

SHEMA_NEW = '''        {"type": "function", "function": {
            "name": "razbor_struktury",
            "description": (
                "Разметка волн: номера, три места входа по риску, "
                "отношения между волнами. ЭТО ИНСТРУМЕНТ ВЕДЕНИЯ, а не "
                "входа. Зови, когда ты УЖЕ В РЫНКЕ и хочешь прикинуть, "
                "где ты в структуре и сколько ещё можно пройти. Перед "
                "входом это не нужно: там вопрос один — кончился ход "
                "или нет."),
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},
        {"type": "function", "function": {
            "name": "chemu_uchили",'''.replace("chemu_uchили", "chemu_uchili")


ISP_OLD = '''    itog = {"moi_yarlyki": _moi_yarlyki,                # RUKI_ZAKLADOK_V1'''

ISP_NEW = '''    def _razbor_struktury(args: dict) -> str:
        """RUKA_RAZBORA_V1: полка ВЕДЕНИЯ. Лежит в подпапке
        знания/ведение/ и потому НЕ грузится с остальными знаниями на
        каждом взгляде — загрузчик берёт только файлы папки, подпапки
        пропускает. Достаётся рукой, когда трейдер уже в рынке.

        Слово Шефа 08.09: «он из дальнейшего разбора, когда уже вошёл и
        видит, что правильно идёт, может определить, где он зашёл в
        своей структуре, и дальше спланировать, сколько пройти можно».
        """
        try:
            _koren = Path(__file__).resolve().parent.parent
            _p = (_koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh
                  / "слоты" / slot / "знания" / "ведение")
            if not _p.exists():
                return "полки ведения нет"
            _kuski = []
            for f in sorted(_p.iterdir()):
                if f.is_file() and f.suffix.lower() in (".md", ".txt"):
                    _kuski.append(f"\\n\\n===== {f.stem} =====\\n"
                                  + f.read_text(encoding="utf-8"))
            if not _kuski:
                return "полка ведения пуста"
            return ("=== РАЗБОР СТРУКТУРЫ (для ведения, не для входа) ==="
                    + "".join(_kuski)[:6000])
        except Exception as e:
            return f"разбор не прочитался: {e}"

    itog = {"razbor_struktury": _razbor_struktury,      # RUKA_RAZBORA_V1
            "moi_yarlyki": _moi_yarlyki,                # RUKI_ZAKLADOK_V1'''


def main() -> None:
    root = Path(__file__).resolve().parent
    p = root / RUKI
    if not p.exists():
        print(f"НЕ НАШЁЛ: {p}")
        print("Запускать из корня репозитория (там, где лежит main.py).")
        return

    t = p.read_text(encoding="utf-8")
    if MARKER in t or "razbor_struktury" in t:
        print("рука razbor_struktury уже стоит — ничего не трогаю")
        return

    if "RUKI_ZAKLADOK_V1" not in t:
        print("⚠ Не вижу RUKI_ZAKLADOK_V1 — сперва накати")
        print("  postavit_ruki_zakladok.py. Ничего не меняю.")
        return

    bracket = []
    for imya, old in (("схема", SHEMA_OLD), ("исполнители", ISP_OLD)):
        if t.count(old) != 1:
            bracket.append((imya, t.count(old)))
    if bracket:
        print("⚠ Файл отличается от ожидаемого — НИЧЕГО не меняю:")
        for imya, cnt in bracket:
            print(f"   «{imya}»: совпадений {cnt} (нужно 1)")
        print("Пришли Брату свой Биржа/ruki_treydera.py — доведу.")
        return

    t = t.replace(SHEMA_OLD, SHEMA_NEW, 1)
    t = t.replace(ISP_OLD, ISP_NEW, 1)
    t = t.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        import ast
        ast.parse(t)
    except SyntaxError as e:
        print(f"⚠ СИНТАКСИС СЛОМАН: {e} — НЕ сохраняю")
        return

    bak = p.with_suffix(p.suffix + ".bak_ruka_razbora")
    if not bak.exists():
        bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    p.write_text(t, encoding="utf-8")

    print("✔ рука razbor_struktury встала, синтаксис цел")
    print("  Бэкап рядом:", bak.name)
    print("\nПроверить: спроси в чате «покажи разбор структуры» —")
    print("должен позвать руку и выдать разметку из знания/ведение/.")


if __name__ == "__main__":
    main()
