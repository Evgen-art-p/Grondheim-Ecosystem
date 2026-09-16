# -*- coding: utf-8 -*-
# OSTUDIT_V1
"""
ОСТУЖАЛКА — холодный душ ОДНОМУ жителю.

СЛОВО ШЕФА (16.09)
    «Тик есть кнопка в кабинете Брата, но она всех — это просто один
    тик жизни. А ему холодный душ нужен, он в таком состоянии
    практически всегда.»

ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ТИКА
    Тик — выдох ВСЕГО города: сутки прошли, все чуть остыли по времени.
    Душ — адресный и сильный: одного, сейчас, до ровного.
    Тик про время. Душ про состояние.

ЗАЧЕМ ВООБЩЕ
    Заряд идёт в ДВА места сразу:
      · в промпт словами — «придавлен(а), несёшь тяжесть»;
      · в ТЕМПЕРАТУРУ модели: минус давит → стресс → температура выше →
        голова думает хаотичнее.
    При заряде под минус единицу житель не смотрит, а сочиняет. Видели
    живьём: Илья описал на кадре уровень, которого там нет.

КАК ОСТУЖАЕТ
    Тем же дыханием, каким его нагрузило: маленькие глотки vdoh, и
    после каждого смотрим, куда пошёл заряд. Не двинулся — честно
    говорим и останавливаемся, а не крутим вхолостую.
    Ведёт к НУЛЮ, не в плюс: эйфория — такая же кривая оптика, только
    с другой стороны.

ЧЕГО НЕ ТРОГАЕТ
    Память, выводы, якоря, метки. Опыт — не состояние, и стирать его
    вместе с усталостью нельзя.

Дома жителей и движок берём из tik.py — единственной правды о том, где
кто живёт. Меняется он — меняется и душ, расхождения не будет.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

ROVNO = 0.10      # |заряд| ниже этого — человек ровен
SHAGOV = 40       # потолок глотков, чтобы не крутиться вечно


def _tik():
    """tik.py из корня — та же рука, что у кнопки Тик."""
    koren = Path(__file__).resolve().parent.parent
    if str(koren) not in sys.path:
        sys.path.insert(0, str(koren))
    import tik as t
    return t


def _zaryad_doma(d) -> float:
    """Заряд со стола, без побочек (стол чистый — в память не пишет)."""
    try:
        stol = d.nakryt_stol_chisto() or {}
        return round(float(stol.get("заряд") or 0.0), 3)
    except Exception:
        return 0.0


def _stol(d) -> dict:
    try:
        return d.nakryt_stol_chisto() or {}
    except Exception:
        return {}


def slovami(z: float) -> str:
    if z > 0.3:
        return "на подъёме"
    if z < -0.3:
        return "придавлен, несёт тяжесть"
    return "ровно"


def temperatura(z: float, stol: dict | None = None) -> float:
    """Та же формула, что у носителя — видно, как думает голова."""
    dna = (stol or {}).get("натура") or {}
    try:
        upor = float(dna.get("Stubbornness", 0.5) or 0.5)
    except Exception:
        upor = 0.5
    stress = max(0.0, -z)
    light = 0.5 + max(0.0, z) / 2.0
    t = 0.70 + stress * 0.45 - (light - 0.5) * 0.30
    t = 0.70 + (t - 0.70) * (1.0 - 0.5 * upor)
    return round(max(0.3, min(1.2, t)), 2)


def spisok() -> list:
    """Кто есть и в каком состоянии.

    [{дом, имя, заряд, состояние, температура, крайний}]
    Ничего не меняет — только смотрит.
    """
    try:
        t = _tik()
        doma = t.nayti_doma() or []
    except Exception as e:
        print(f"[ДУШ] ⚠ жителей не обошёл: {e}")
        return []

    out = []
    for dom in doma:
        try:
            d = t.Dvizhok(dom)
        except Exception:
            continue
        stol = _stol(d)
        if not stol:
            continue
        z = round(float(stol.get("заряд") or 0.0), 3)
        imya = stol.get("кто_я")
        if not imya:
            try:
                imya = d.p.get("Official_Name") or dom.name
            except Exception:
                imya = dom.name
        out.append({
            "дом": dom,
            "имя": str(imya),
            "заряд": z,
            "состояние": slovami(z),
            "температура": temperatura(z, stol),
            "крайний": abs(z) > 0.8,
        })
    out.sort(key=lambda x: -abs(x["заряд"]))
    return out


def ostudit(dom, do: float = ROVNO) -> dict:
    """Холодный душ одному. Возвращает что было, что стало и шаги.

    Тонус ПРОТИВ перекоса: придавленного греем, разогнанного студим.
    Силу берём маленькую и смотрим на отклик — заряд ведёт себя
    по-своему, и подгонять его формулой было бы враньём.
    """
    try:
        t = _tik()
        d = t.Dvizhok(Path(dom))
    except Exception as e:
        return {"остыл": False, "причина": f"движок не поднялся: {e}"}

    stol = _stol(d)
    imya = stol.get("кто_я") or Path(dom).name
    bylo = round(float(stol.get("заряд") or 0.0), 3)

    if abs(bylo) <= do:
        return {"остыл": False, "имя": imya, "было": bylo, "стало": bylo,
                "причина": "и так ровен — душ не нужен"}

    z, shagi = bylo, []
    for _ in range(SHAGOV):
        tonus = "плюс" if z < 0 else "минус"
        sila = min(0.35, max(0.05, abs(z) / 3.0))
        try:
            d.vdoh("покой", sila=sila, svezhest=1.0, tonus=tonus)
        except Exception as e:
            return {"остыл": False, "имя": imya, "было": bylo, "стало": z,
                    "причина": f"вдох не прошёл: {e}", "шаги": shagi}
        # оседаем после КАЖДОГО глотка: иначе движок поднимет стол с
        # диска заново и вода польётся мимо (проверено на пробе)
        try:
            d.sохранить()
        except Exception:
            pass
        novyy = _zaryad_doma(d)
        shagi.append((z, novyy))
        if abs(novyy - z) < 0.005:
            z = novyy
            return {"остыл": True, "имя": imya, "было": bylo, "стало": z,
                    "шаги": shagi, "уперся": True,
                    "температура_было": temperatura(bylo, stol),
                    "температура_стало": temperatura(z, stol)}
        z = novyy
        if abs(z) <= do:
            break

    return {"остыл": True, "имя": imya, "было": bylo, "стало": z,
            "шаги": shagi, "уперся": abs(z) > do,
            "температура_было": temperatura(bylo, stol),
            "температура_стало": temperatura(z, stol)}


def _ruchnoy_zapusk():
    """Можно и без кнопки: python жители/ostudit.py"""
    lyudi = spisok()
    if not lyudi:
        print("Жителей не нашёл.")
        return
    print(f"\n{'№':>2}  {'кто':<16} {'заряд':>7}  {'состояние':<26} темп.")
    print("-" * 58)
    for i, ch in enumerate(lyudi, 1):
        znak = "🔥" if ch["крайний"] else ("·" if abs(ch["заряд"]) <= ROVNO else " ")
        print(f"{i:>2}. {ch['имя'][:16]:<16} {ch['заряд']:>+7.2f}  "
              f"{ch['состояние']:<26} {ch['температура']:.2f} {znak}")
    print("-" * 58)
    try:
        n = input("\nКого остудить? номер (Enter — никого): ").strip()
    except Exception:
        n = ""
    if not n:
        print("Никого не трогал.")
        return
    try:
        ch = lyudi[int(n) - 1]
    except Exception:
        print("Не понял номер — никого не трогал.")
        return
    r = ostudit(ch["дом"])
    if not r.get("остыл"):
        print(f"\n{r.get('имя')}: {r.get('причина')}")
        return
    for a, b in r.get("шаги", []):
        print(f"  {a:+.2f} → {b:+.2f}")
    print(f"\n{r['имя']}: было {r['было']:+.2f} → стало {r['стало']:+.2f} "
          f"({slovami(r['стало'])})")
    print(f"температура головы: {r['температура_было']:.2f} → "
          f"{r['температура_стало']:.2f}")
    if r.get("уперся"):
        print("⚠ до ровного не дошёл — маятник упёрся.")
    print("Память, выводы и якоря не тронуты.")


if __name__ == "__main__":
    _ruchnoy_zapusk()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# OSTUDIT_V1 - marker
