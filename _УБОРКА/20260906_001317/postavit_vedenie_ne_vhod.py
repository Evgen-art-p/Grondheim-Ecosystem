# -*- coding: utf-8 -*-
# MARKER: VEDENIE_NE_VHOD_V1
"""
ОТКРЫТА ПОЗИЦИЯ — ЗНАЧИТ ВОПРОС ПРО НЕЁ, А НЕ ПРО ВХОД.

ЧТО БЫЛО НЕ ТАК
───────────────
В прогоне трейдер, только что открывший позицию, на следующем событии
отвечал так, будто выбирает вход заново: «сейчас нет явного сигнала
для входа, НАБЛЮДАЮ» — про свою же сделку.

Причина не в модели. Позиция ему кладётся честно — сторона, вход,
стоп, плавающий R. А ВЕСЬ ТЕКСТ ВОКРУГ говорит про вход: «перед тобой
стол и ты сам... входишь — называешь сторону, считаешь entry и stop...
три места входа лежат у тебя в знаниях... не входишь — REJECTED».
Про ведение сказано одной строкой в самом хвосте, в описании формата
ответа. Человек читает задание и отвечает ровно на него.

ЧТО ДЕЛАЕТСЯ
────────────
Когда позиция открыта, В САМОЕ НАЧАЛО запроса встаёт блок ведения:
чем владеешь, сколько это в R, и прямая оговорка — вход уже сделан
тобой, вопрос сейчас про эту сделку, а всё ниже про поиск входа читай
как справку, а не как задание.

Нет позиции — блок пустой, всё как было.

ЧТО НЕ ТРОГАЕТСЯ
────────────────
Ни ведение стопа кодом, ни факты на столе, ни формат ответа, ни
события пробуждения. Патч меняет ТОЛЬКО вопрос, который человеку
задают, — и ничего не решает за него: держать, подтянуть, долить или
закрыть, решает он.

Правится три мозга: A06, A07, A08. Идемпотентен. .bak рядом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "VEDENIE_NE_VHOD_V1"
SLOTY = ("A06", "A07", "A08")
PREFIKSY = {"A06": "brut", "A07": "avan", "A08": "cons"}
STOLY = {"A06": "table_for_brut", "A07": "table_for_avan",
         "A08": "table_for_cons"}


def _nayti_sloty() -> Path:
    hvost = Path("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты")
    nashli, korni = [], []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        for p in (koren / hvost, koren):
            if all((p / s / "мозг.py").exists() for s in SLOTY):
                if p not in nashli:
                    nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл слоты A06/A07/A08.")
        s = input("Перетащи сюда папку «слоты» и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "A06" / "мозг.py").exists():
            return p
        raise SystemExit("не та папка — там нет A06/мозг.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


def _blok(stol: str, pre: str) -> str:
    """Код, который кладётся в мозг ПЕРЕД сборкой user_msg."""
    return f'''
    # ═══ VEDENIE_NE_VHOD_V1 ═══
    # Позиция открыта — значит спрашивать надо про НЕЁ. Раньше весь
    # запрос был про поиск входа, и человек честно отвечал «сигнала
    # для входа нет, НАБЛЮДАЮ» — про собственную сделку.
    _vedenie_blok = ""
    _poz = ({stol}.get("position") or None)
    if _poz:
        _r = _poz.get("floating_r")
        _r_slovami = (f"{{_r}}R" if _r is not None else "R пока не считается")
        _vedenie_blok = (
            "=== У ТЕБЯ ОТКРЫТА ПОЗИЦИЯ. СЕЙЧАС ВОПРОС ПРО НЕЁ ===\\n"
            f"{{_poz.get('direction')}} от {{_poz.get('entry')}}, "
            f"стоп {{_poz.get('stop')}}, лот {{_poz.get('lot')}}, "
            f"открыта {{_poz.get('opened_at')}}.\\n"
            f"Сейчас {{_poz.get('current_price')}} — это {{_r_slovami}}.\\n\\n"
            "Вход уже сделан, и сделал его ТЫ. Не ищи его заново и не "
            "суди, годится ли это место: поздно, ты уже в рынке.\\n"
            "Посмотри на кадр и реши, что делать со сделкой: держать "
            "как есть, подтянуть стоп, долить или закрыть. Стоп по "
            "фракталам ведёт код — трогай его, только если видишь "
            "причину.\\n"
            "Всё, что написано НИЖЕ про поиск входа и три места, — "
            "справка об устройстве, а не задание на сейчас.\\n"
            "Отвечай ключами {pre}_action (HOLD / MOVE_STOP / ADD / "
            "CLOSE) и {pre}_reason.\\n\\n")

'''


YAKOR = "    user_msg = (\n"
VSTAVKA_V_MSG = "        + _instr_blok\n"
VSTAVKA_NOVAYA = "        + _vedenie_blok\n        + _instr_blok\n"


def _pochinit(f: Path, slot: str) -> str:
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже накачено"
    if YAKOR not in src:
        return "! не нашёл сборку запроса — не трогаю"
    if VSTAVKA_V_MSG not in src:
        return "! не нашёл место вставки в запрос — не трогаю"

    novyy = src.replace(YAKOR, _blok(STOLY[slot], PREFIKSY[slot]) + YAKOR, 1)
    novyy = novyy.replace(VSTAVKA_V_MSG, VSTAVKA_NOVAYA, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_vedenie"))
    f.write_text(novyy, encoding="utf-8")
    return "вопрос про ведение, когда позиция открыта (.bak_vedenie рядом)"


def main():
    koren = _nayti_sloty()
    print(f"\nСлоты: {koren}\n")
    for slot in SLOTY:
        try:
            itog = _pochinit(koren / slot / "мозг.py", slot)
        except SyntaxError as e:
            itog = f"! после правки не разбирается ({e}) — файл НЕ тронут"
        print(f"  {slot}: {itog}")
    print("\nГотово. Открыта позиция — спрашиваем про неё, а не про вход.")
    print("Что делать со сделкой, по-прежнему решает трейдер.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
