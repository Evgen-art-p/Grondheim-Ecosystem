# -*- coding: utf-8 -*-
# POLKA_PO_MOMENTU_V1
"""
ПОЛКА ЗНАНИЙ ДЕЛИТСЯ ПО МОМЕНТУ РАБОТЫ, А НЕ ПО ТЕМАМ.

Слово Шефа 08.09:

> Он из дальнейшего разбора, когда уже вошёл и видит, что правильно
> идёт, может определить, где он зашёл в своей структуре, и дальше
> спланировать, сколько пройти можно.
>
> Про место — какая это волна C там или какая — упростить: просто
> конец волны и всё, а уже если хочет, потом разберётся.

═══ ЧТО БЫЛО НЕ ТАК ═══

Полка разложена по темам: индикаторы, паттерны, входы, разворотный
бар, Котин. И вся она лежит перед трейдером РАЗОМ, на каждом взгляде —
загрузчик берёт все файлы папки по алфавиту.

В момент входа ему нужно немного: идёт ли ход, выдохся ли, есть ли
некрон. А получает он всё сразу, включая разметку волн по номерам и
таблицу трёх мест входа — вещи, которые до входа не решают ничего и
только сбивают.

Это уточняет запись от 06.09. Мы тогда решили, что подробный разбор
структуры лишний. Он НЕ лишний — он на другом шаге: разбор это
инструмент ВЕДЕНИЯ, а не входа. До входа номера сбивают; после входа,
когда ты уже в ходе и времени полно, вопрос «куда я попал» становится
рабочим: у начала движения впереди много, у конца — доехать бы.

═══ КАК ДЕЛИТСЯ ═══

Загрузчик (`_znaniya_roli`) берёт только ФАЙЛЫ папки и пропускает
подпапки. Значит деление делается само, без правки загрузчика:

    знания/              ← лежит перед ним всегда: ЧТОБЫ ВОЙТИ
    знания/ведение/      ← достаётся рукой: ЧТОБЫ ВЕСТИ

**Переезжает в ведение:**
  · «Три места на одной структуре» (из PATTERNY.md) — таблица с
    волной C и номерами. Место теперь одно: конец хода;
  · весь VHODY.md — разбор трёх мест по риску. Пригодится, когда он
    уже в рынке и решает, рано зашёл или поздно;
  · «Чего не бывает» с отношениями волн (треть, половина, две трети) —
    это про «сколько ещё пройдёт», то есть чистое ведение.

**Остаётся на виду:** индикаторы (горб, дивер, приседающий),
разворотный бар, флэт, фрактальность, параллельный рынок, волна по AO,
Котин. Всё, что нужно, чтобы увидеть ход и его конец.

**Новая рука `razbor_struktury`** — достать разметку, когда он уже
вошёл и хочет прикинуть, сколько ещё можно пройти. В описании прямо
сказано: до входа это не нужно.

═══ ЧЕГО ПАТЧ НЕ ДЕЛАЕТ ═══

Ничего не удаляет: файлы ПЕРЕЕЗЖАЮТ в подпапку, ни строчки не
теряется. Не трогает загрузчик, промпт, стол, кадр. Не трогает
INDIKATORY, RAZVOROTNYY_BAR и Котина.

Откат простой: перенести файлы из `знания/ведение/` обратно наверх.

Запускать из корня репозитория:
    python postavit_polku_po_momentu.py

Идемпотентен (маркер POLKA_PO_MOMENTU_V1). Рядом .bak.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "POLKA_PO_MOMENTU_V1"
BAZA = "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты"
SLOTY = ("A06", "A07", "A08")
RUKI = "Биржа/ruki_treydera.py"


# ── кусок «три места», который уезжает из PATTERNY ──────────────────
TRI_MESTA = """## Три места на одной структуре

Одна и та же картина даёт три разных входа, и они отличаются риском,
а не правильностью:

| Где | Что это | Кому |
|---|---|---|
| внутри волны C | ехать на коррекции | **никому** |
| разворотный бар на конце C | сигнал разворота, тренд не подтверждён | агрессивному |
| первый откат после волны 1 нового импульса | импульс состоялся, откат состоялся | осторожному, это канон |

Разворотный бар на конце коррекции — это **сигнал разворота**, а не
вход по тренду: тренда в этот момент ещё нет, он только рождается.
После него идёт первая волна нового движения, и безопасный вход — на
откате уже к ней.

---

"""

TRI_MESTA_ZAMENA = """## Место одно: конец хода

Раньше здесь лежала таблица трёх мест на одной структуре — с волной C
и номерами волн. Она переехала в `ведение/`: до входа номера не решают
ничего и только сбивают.

В момент входа место одно — **конец хода**. Раньше ты его возьмёшь или
позже, это про твой вкус к риску, а не разные фигуры с именами.

Уже вошёл и хочешь прикинуть, сколько ещё можно пройти? Тогда разметка
пригодится — позови руку `razbor_struktury`.

---

"""


# ── новая рука ──────────────────────────────────────────────────────
RUKA_SHEMA_OLD = '''        {"type": "function", "function": {
            "name": "chemu_uchili",'''

RUKA_SHEMA_NEW = '''        {"type": "function", "function": {
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
            "name": "chemu_uchili",'''

RUKA_ISP_OLD = '''    itog = {"stol_na_etazhe": _stol,'''

RUKA_ISP_NEW = '''    def _razbor_struktury(args: dict) -> str:
        """POLKA_PO_MOMENTU_V1: полка ведения. Лежит в подпапке, и
        потому НЕ грузится с остальными знаниями на каждом взгляде —
        загрузчик берёт только файлы папки, подпапки пропускает.
        Достаётся рукой, когда трейдер уже в рынке."""
        try:
            import os
            _tut = Path(__file__).resolve().parent.parent
            _p = (_tut / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh
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

    itog = {"razbor_struktury": _razbor_struktury,   # POLKA_PO_MOMENTU_V1
            "stol_na_etazhe": _stol,'''


SHAPKA_VEDENIE = """<!-- POLKA_PO_MOMENTU_V1 -->
# Разбор структуры — для ВЕДЕНИЯ, не для входа

Эта полка не лежит у тебя перед глазами постоянно. Ты достаёшь её
рукой `razbor_struktury`, когда уже вошёл и хочешь понять, где ты в
структуре и сколько ещё можно пройти.

Перед входом всё это не нужно. Там вопрос один: кончился ход или нет.
Какая это волна по счёту, C она или не C — до входа не решает ничего и
только сбивает.

---

"""


def _peredvinut(slot_dir: Path, log: list) -> str | None:
    """Перенести материал ведения в подпапку. Возвращает причину отказа."""
    znaniya = slot_dir / "знания"
    if not znaniya.exists():
        return "нет папки знания"
    vedenie = znaniya / "ведение"
    if (vedenie / "VHODY.md").exists() or (vedenie / "RAZMETKA.md").exists():
        return "уже разделено"

    patterny = znaniya / "PATTERNY.md"
    vhody = znaniya / "VHODY.md"
    if not patterny.exists():
        return "нет PATTERNY.md"
    t = patterny.read_text(encoding="utf-8")
    if TRI_MESTA not in t:
        return "PATTERNY.md отличается от ожидаемого (кусок «три места»)"

    vedenie.mkdir(parents=True, exist_ok=True)

    # 1) три места — из паттернов в разметку
    t_new = t.replace(TRI_MESTA, TRI_MESTA_ZAMENA, 1)
    razmetka = SHAPKA_VEDENIE + TRI_MESTA
    (vedenie / "RAZMETKA.md").write_text(razmetka, encoding="utf-8")
    bak = patterny.with_suffix(".md.bak_polka")
    if not bak.exists():
        bak.write_text(t, encoding="utf-8")
    patterny.write_text(t_new.rstrip("\n") + f"\n\n<!-- {MARKER} -->\n",
                        encoding="utf-8")
    log.append("PATTERNY.md → кусок «три места» уехал в ведение/RAZMETKA.md")

    # 2) входы — целиком в ведение
    if vhody.exists():
        (vedenie / "VHODY.md").write_text(
            SHAPKA_VEDENIE + vhody.read_text(encoding="utf-8"),
            encoding="utf-8")
        vhody.unlink()
        log.append("VHODY.md → переехал в ведение/ целиком")
    return None


def main() -> None:
    root = Path(__file__).resolve().parent

    # ── знания по трём слотам ──
    log, uzhe, bracket = [], [], []
    for s in SLOTY:
        d = root / BAZA / s
        if not d.exists():
            bracket.append((s, "нет слота"))
            continue
        prichina = _peredvinut(d, log)
        if prichina == "уже разделено":
            uzhe.append(s)
        elif prichina:
            bracket.append((s, prichina))

    if bracket:
        print("⚠ Не всё сошлось — смотри, что именно:")
        for s, p in bracket:
            print(f"   {s}: {p}")
        if not log:
            print("\nНичего не тронуто. Пришли Брату свои знания — доведу.")
            return
        print()

    for l in log:
        print("✔", l)
    if uzhe:
        print("(уже разделены: " + ", ".join(uzhe) + ")")

    # ── рука ──
    put_ruki = root / RUKI
    if not put_ruki.exists():
        print(f"\n⚠ Не нашёл {RUKI} — руку не поставил.")
        return
    t = put_ruki.read_text(encoding="utf-8")
    if MARKER in t:
        print("\n(рука razbor_struktury уже стоит)")
        return
    if t.count(RUKA_SHEMA_OLD) != 1 or t.count(RUKA_ISP_OLD) != 1:
        print(f"\n⚠ {RUKI} отличается от ожидаемого — руку не ставлю.")
        return
    t = t.replace(RUKA_SHEMA_OLD, RUKA_SHEMA_NEW, 1)
    t = t.replace(RUKA_ISP_OLD, RUKA_ISP_NEW, 1)
    t = t.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        import ast
        ast.parse(t)
    except SyntaxError as e:
        print(f"\n⚠ СИНТАКСИС СЛОМАН: {e} — руку не ставлю")
        return
    bak = put_ruki.with_suffix(put_ruki.suffix + ".bak_polka")
    if not bak.exists():
        bak.write_text(put_ruki.read_text(encoding="utf-8"), encoding="utf-8")
    put_ruki.write_text(t, encoding="utf-8")
    print("✔ рука razbor_struktury встала")

    print("\nЧто теперь лежит перед ним всегда:")
    print("  индикаторы · разворотный бар · флэт · фрактальность ·")
    print("  волна по AO · Котин — всё, чтобы увидеть ход и его конец.")
    print("\nЧто достаётся рукой, когда он уже в рынке:")
    print("  разметка волн, три места по риску, отношения между волнами.")
    print("\nНичего не удалено: файлы переехали в знания/ведение/.")


if __name__ == "__main__":
    main()
