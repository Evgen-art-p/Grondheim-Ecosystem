# -*- coding: utf-8 -*-
# KARTINA_SVOYA_V1
"""
КАРТИНА — как ЭТОТ трейдер читает рынок. Своя у каждого.

СЛОВА ШЕФА
    «Нет первого и последнего... Место — это СТОЛ, один на всех со
    всеми фактами. Есть бар, посмотрели: Вася решил, что это волна
    одна, Петя — другая, один одно ждёт, другой другое, а может, кто
    все три входа делать будет. Наша задача — дать.»

ЗАКОН ЭТОГО ФАЙЛА
    Стол общий, чтение личное. На одном и том же баре двое видят
    разное, и оба правы: волны — это интерпретация, а не свойство
    рынка. Поэтому картина живёт ПРИ ТРЕЙДЕРЕ, а не при инструменте, и
    ничьё объявление не обязывает соседа.

    Чужие картины не показываются намеренно (слово Шефа 16.08): пока
    каждый не разобрался в своём чтении, подсматривание сведёт всех в
    одно мнение.

ЗАЧЕМ
    Чтобы чтение не терялось между барами. Без памяти трейдер каждый
    раз начинает с чистого листа и честно пишет «нет первой волны» —
    хотя волна была, просто предыдущего бара для него не существовало.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_KOREN = Path(__file__).resolve().parent.parent
PUSTO = {"точка_ноль": None, "волна": None, "откат": None, "заметки": []}


def _put(ceh: str, slot: str) -> Path:
    return (_KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh / "слоты"
            / slot / "данные" / "картина.json")


def _vsya(ceh: str, slot: str) -> dict:
    try:
        return json.loads(_put(ceh, slot).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sohranit(ceh: str, slot: str, d: dict):
    p = _put(ceh, slot)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    except Exception as e:
        print(f"[КАРТИНА] не записалась: {e}")


def chitat(ceh: str, slot: str, symbol: str) -> dict:
    s = (symbol or "").strip().upper()
    d = json.loads(json.dumps(PUSTO))
    d.update((_vsya(ceh, slot).get(s) or {}))
    return d


def obyavit(ceh: str, slot: str, symbol: str, chto: str, kto: str = "",
            cena=None, bar: str = "", pochemu: str = "") -> tuple:
    """Записать в СВОЮ картину. Ничего ни у кого не спрашиваем."""
    s = (symbol or "").strip().upper()
    if not s:
        return False, "не сказано, по какому инструменту"
    chto = (chto or "").strip().lower()
    vsya = _vsya(ceh, slot)
    moya = vsya.get(s) or json.loads(json.dumps(PUSTO))
    seychas = datetime.now().isoformat(timespec="seconds")
    zapis = {"кто": kto or slot, "почему": (pochemu or "").strip()[:500],
             "когда": seychas}
    if cena is not None:
        try:
            zapis["цена"] = float(cena)
        except Exception:
            return False, f"цена не число: {cena}"
    if bar:
        zapis["бар"] = bar

    if chto in ("точка_ноль", "точка ноль", "ноль"):
        # новая точка ноль — значит и волна, и откат другие
        moya = json.loads(json.dumps(PUSTO))
        moya["точка_ноль"] = zapis
        itog = f"твоя точка ноль {s}: {zapis.get('цена')} ({bar})"
    elif chto in ("волна", "первая_волна", "первая волна"):
        if not moya.get("точка_ноль"):
            return False, ("в твоей картине нет точки ноль — от чего "
                           "волна? назови сперва её")
        moya["волна"] = zapis
        itog = f"твоя волна {s} до {zapis.get('цена')}"
    elif chto in ("откат",):
        if not moya.get("волна"):
            return False, "в твоей картине нет волны — откатывать нечему"
        moya["откат"] = zapis
        itog = f"ты видишь откат к своей волне {s}"
    elif chto in ("заметка", "мысль"):
        moya.setdefault("заметки", []).append(zapis)
        moya["заметки"] = moya["заметки"][-10:]
        itog = "записал в твою картину"
    elif chto in ("стереть", "сломалась", "чисто"):
        moya = json.loads(json.dumps(PUSTO))
        itog = f"твоя картина {s} чистая"
    else:
        return False, (f"не понял «{chto}». Можно: точка_ноль, волна, "
                       f"откат, заметка, стереть")

    vsya[s] = moya
    _sohranit(ceh, slot, vsya)
    return True, itog


def slovami(ceh: str, slot: str, symbol: str) -> str:
    """Своя картина словами. Только то, что он сам записал."""
    d = chitat(ceh, slot, symbol)
    tn = d.get("точка_ноль")
    L = [f"=== ТВОЯ КАРТИНА · {(symbol or '').upper()} ==="]
    if not tn:
        L.append("Пусто. Ты ещё не называл(а) свою точку ноль —")
        L.append("посмотри и назови, если видишь конец коррекции.")
    else:
        L.append(f"ТОЧКА НОЛЬ: {tn.get('цена')} на баре {tn.get('бар')}")
        if tn.get("почему"):
            L.append(f"   ты сказал(а): {tn['почему']}")
        v = d.get("волна")
        L.append(f"ВОЛНА: до {v.get('цена')}" if v else "ВОЛНА: не названа")
        if v and v.get("почему"):
            L.append(f"   ты сказал(а): {v['почему']}")
        o = d.get("откат")
        L.append("ОТКАТ: видишь" if o else "ОТКАТ: не назван")
        if o and o.get("почему"):
            L.append(f"   ты сказал(а): {o['почему']}")
    zam = d.get("заметки") or []
    if zam:
        L.append("ТВОИ ЗАМЕТКИ:")
        for z in zam[-3:]:
            L.append(f"   · {z.get('почему', '')} ({z.get('когда', '')[:16]})")
    return "\n".join(L)


# KARTINA_SVOYA_V1 - marker
