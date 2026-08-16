# -*- coding: utf-8 -*-
# CHTENIE_KNIGI_V1
"""
ЧТЕНИЕ ДЛИННОГО — общая рука города.

ЗАЧЕМ
    Раньше длинный текст резался молча: житель получал первые 50 000
    знаков, Академия — 20 000, а хвост исчезал без единого слова.
    Человек честно рассказывал, что понял из начала, и не знал, что
    была ещё книга. Тишина здесь хуже потолка.

ЗАКОН ЭТОГО ФАЙЛА
    Рука ЧИТАЕТ И РЕЖЕТ. Она не думает и не выжимает — думает тот,
    кому текст принесли. Режет по абзацам: мысль не должна рваться
    посреди фразы ради ровного счёта знаков.
"""
from __future__ import annotations

from pathlib import Path

# Размер одной части. Не потолок книги — книга читается целиком,
# просто по частям. У нынешних моделей окно много больше, но части
# держат внимание и дают ровный осадок в память.
KUSOK = 50000


def prochitat(path) -> str:
    """Честный текст файла. Не текст — пустая строка, без выдумок.

    UTF-8 строго → cp1251 (русские книги из Windows) → utf-8 с
    заменой. Нули или море замен — это не книга, а картинка или архив.
    """
    try:
        raw = Path(path).read_bytes()
    except Exception:
        return ""
    t = ""
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            t = raw.decode("cp1251")
        except UnicodeDecodeError:
            t = raw.decode("utf-8", errors="replace")
    if "\x00" in t:
        return ""
    if "\ufffd" in t and len(t) > 200 and t.count("\ufffd") / len(t) > 0.10:
        return ""
    return t


def narezat(tekst: str, kusok: int = KUSOK) -> list:
    """Порезать по абзацам на части не длиннее kusok.

    Абзац длиннее части (сплошная простыня без пустых строк) режется
    по предложениям, а уж если и предложение великанское — по счёту.
    Лучше грубый разрез, чем потерянный хвост.
    """
    tekst = tekst or ""
    if len(tekst) <= kusok:
        return [tekst] if tekst.strip() else []

    chasti, tek = [], ""
    for abzac in tekst.split("\n\n"):
        if len(abzac) > kusok:
            if tek:
                chasti.append(tek)
                tek = ""
            fraza = ""
            for kus in abzac.replace("! ", "!\x01").replace("? ", "?\x01") \
                            .replace(". ", ".\x01").split("\x01"):
                if len(fraza) + len(kus) + 1 > kusok:
                    if fraza:
                        chasti.append(fraza)
                    while len(kus) > kusok:
                        chasti.append(kus[:kusok])
                        kus = kus[kusok:]
                    fraza = kus
                else:
                    fraza = (fraza + " " + kus).strip()
            if fraza:
                tek = fraza
            continue
        if len(tek) + len(abzac) + 2 > kusok:
            chasti.append(tek)
            tek = abzac
        else:
            tek = (tek + "\n\n" + abzac) if tek else abzac
    if tek.strip():
        chasti.append(tek)
    return [c for c in chasti if c.strip()]


def skazat_o_razmere(imya_fajla: str, tekst: str, chastey: int) -> str:
    """Строка для чата: сколько знаков и на сколько частей поделили."""
    znakov = len(tekst)
    stranic = max(1, znakov // 2000)
    if chastey <= 1:
        return f"«{imya_fajla}» · {znakov} знаков (≈{stranic} стр.)"
    return (f"«{imya_fajla}» · {znakov} знаков (≈{stranic} стр.) — "
            f"читаю целиком, по частям: {chastey}")


# CHTENIE_KNIGI_V1 - marker
