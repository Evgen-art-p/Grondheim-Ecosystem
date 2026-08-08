# -*- coding: utf-8 -*-
# VZGLYAD_PERVYY_V1
"""
ВЗГЛЯД ПЕРВЫЙ — трейдер смотрит, потом считает.

СЛОВО ШЕФА (06.08): «трейдер не должен просыпаться от сигналов, он
должен глянуть, увидеть паттерн и работать; не увидел — не работает,
а уже с паттерном работает и индюков подключает».

ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ КОНВЕЙЕРА, КОТОРЫЙ БЫЛ СНАЧАЛА
    Там код искал сигнал и будил трейдера на готовое. Решал код, а
    трейдер оформлял — и тогда учить глаз было незачем.
    Здесь наоборот. Первым идёт ВЗГЛЯД на голую картинку, без единого
    числа. Не увидел картины — конец, никаких вычислений. Увидел —
    только тогда подключаются индикаторы, чтобы уточнить то, что он
    уже разглядел.

    Так и торгует человек, и так же учит Вильямс: первый уровень —
    два соседних бара, инструменты приходят с уровнями, а не наоборот.

ЦЕНА
    Не увидел — один вызов модели и всё. Увидел — два. Раньше молчание
    стоило вызова конвейера целиком; теперь дороже, но иначе глаз не
    работает вовсе.

ПРАВО ПРОМОЛЧАТЬ ЖИВЁТ ТАМ, ГДЕ ЕМУ МЕСТО
    Не у кода в пороге, а у того, кого этому учили. «Не читается,
    ухожу» — законный и самый частый ответ.

ЧЕГО ЗДЕСЬ НЕТ НАРОЧНО
    Код не решает за трейдера и не подсказывает ему вход. Он рисует,
    считает по запросу и проносит решение дальше. Ни одного порога,
    ни одной команды.
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in sys.path:
    sys.path.insert(0, str(_BIRZHA))

# Трейдеров трое, и каждый подключается НЕЗАВИСИМО — не собрание, не
# голосование: посмотрел сам, решил сам. Характер даёт носитель в
# слоте (закон Картриджа), поэтому слоты и различаются только тем,
# кто в них сидит.
TREYDER_CEH = "торговый_хаос"
TREYDERY = ("A06", "A07", "A08")
TREYDER_SLOT = TREYDERY[0]          # с кем работаем, если не сказано


# ═════════════════════════════════════════════════════════════
# ШАГ 1 — ВЗГЛЯД. Голая картинка, ни одного числа.
# ═════════════════════════════════════════════════════════════
VOPROS_VZGLYAD = """Перед тобой рынок. Смотри.

Расскажи своими словами, что здесь происходит — так, как рассказал бы
человеку, который стоит рядом. Не по списку и не по пунктам: что видишь,
то и говори.

Вильямс на первом уровне велит следить за рынком бар за баром и прямо
предупреждает: не подгонять под увиденное готовый образец. Поэтому
никаких шаблонов от тебя не ждут. Ждут, что ты посмотришь.

Если работы здесь нет — так и скажи, это нормальный и самый частый
ответ. Если есть — скажи, что бы ты сделал и почему.

Не хватает чего-то, чтобы решить, — попроси. Отдельной строкой:

    ПРИБОРЫ: что именно тебе нужно

Например: ПРИБОРЫ: куда смотрит старший этаж; или: ПРИБОРЫ: где
последние фракталы и какой выйдет стоп. Проси только то, чего не видно
глазом, — считать за тебя то, что и так нарисовано, никто не станет."""


# ═════════════════════════════════════════════════════════════
# ШАГ 2 — ПРИБОРЫ. Только если увидел.
# ═════════════════════════════════════════════════════════════
VOPROS_PRIBORY = """Ты попросил приборы. Вот они:

{pribory}

Смотри на ту же картинку и договаривай. Если прибор говорит не то, что
ты разглядел глазом, — так и скажи: глаз важнее, чем сойтись с цифрой.

Что делаешь и почему? Если входишь — назови сторону и цену, за которой
ты неправ."""


def _dusha_treydera(slot: str = TREYDER_SLOT) -> str:
    """Личность носителя со всем нажитым — то же, что видит его кабинет."""
    try:
        from nositel import dusha_slota
        d = dusha_slota(TREYDER_CEH, slot)
        return d.get("душа") or d.get("dusha") or ""
    except Exception:
        return ""


def _kartinka(put: Path) -> list:
    return [{"base64": base64.b64encode(put.read_bytes()).decode("ascii"),
             "mime_type": "image/png", "name": put.name}]


def _prosba_o_priborah(otvet: str) -> str:
    """Что трейдер попросил, если попросил. Пусто — не просил.

    Городской закон: житель сам решает, чего ему не хватает, и просит
    (так же устроены MAYAK_REQUEST и просев). Мы не решаем за него,
    какие цифры ему нужны, и не суём их, пока он смотрит.
    """
    for stroka in (otvet or "").splitlines():
        st = stroka.strip()
        if st.upper().startswith("ПРИБОРЫ"):
            return st.split(":", 1)[1].strip() if ":" in st else "все"
    return ""


def _pribory_tekstom(symbol: str, timeframe: str, bars: list,
                     point: float) -> str:
    """Показания словами. Считаем ТОЛЬКО когда трейдер уже посмотрел —
    до этого вычислять незачем, он их всё равно не увидит."""
    from williams_core import build_market_data
    from global_anchor import global_trend

    md = build_market_data(bars, symbol, timeframe, point=point)
    if not md:
        return "приборы не собрались", {}

    st = global_trend(symbol, timeframe, as_of_date=bars[-1].get("date"))
    al = md.get("alligator", {}) or {}
    nb = md.get("necron_bar", {}) or {}
    rb = md.get("rubber_band", {}) or {}
    fr = md.get("fractals", {}) or {}
    mfi = md.get("mfi", {}) or {}

    L = []
    L.append(f"Большая вода (старший этаж {st.get('senior_tf') or '—'}): "
             f"{st.get('bias')}"
             + ("  ← старший спит, фильтра нет" if st.get("bias") == "NONE" else ""))
    L.append(f"Аллигатор рабочего: челюсть {al.get('jaw')}, зубы {al.get('teeth')}, "
             f"губы {al.get('lips')}; открыт баров подряд: {al.get('bars_open')}")
    if rb.get("tension_ratio") is not None:
        L.append(f"Натяжение от губ: сейчас {rb.get('distance_now')} п., "
                 f"пик за движение {rb.get('distance_max')} п. "
                 f"(доля от пика {rb.get('tension_ratio')})")
    L.append(f"Разворотный бар: "
             + (f"есть, {nb.get('direction')}, край {nb.get('stop_price') or nb.get('extremum')}"
                if nb.get("direction") else "нет"))
    f_up = (fr.get("last_up") or {}).get("price")
    f_dn = (fr.get("last_down") or {}).get("price")
    L.append(f"Последние фракталы: вверх {f_up}, вниз {f_dn}")
    if mfi:
        L.append(f"Объём/размах: {mfi}")
    L.append(f"Цена сейчас: {bars[-1].get('close')}")
    return "\n".join(f"— {x}" for x in L), md


def posmotret(symbol: str, timeframe: str,
              on_event: Optional[Callable] = None,
              kadr_put: Optional[Path] = None,
              slot: str = TREYDER_SLOT) -> dict:
    """Один взгляд ОДНОГО трейдера. Что увидел и что решил.

    slot — кого зовём: A06 / A07 / A08. Каждый смотрит сам и решает
    сам; их ответы не сводятся и не голосуются. Один кадр можно дать
    всем троим — получишь три независимых мнения на одну картинку.

    on_event(dict) — вести в кабинет, может быть None.
    """
    def _ev(d):
        if on_event:
            try:
                on_event(d)
            except Exception:
                pass

    itog = {"symbol": symbol, "timeframe": timeframe, "слот": slot, "кадр": None,
            "взгляд": "", "просил": "", "приборы": "", "решение": ""}

    import grafik
    from feed_source import bars as source_bars
    import llm

    # ── кадр: одна картинка и Шефу на экран, и трейдеру в запрос ──
    put = grafik.kadr(symbol, timeframe, kuda=kadr_put)
    if put is None:
        itog["взгляд"] = "⚠ кадр не нарисовался (нет matplotlib или баров)"
        _ev({"type": "error", "text": itog["взгляд"]})
        return itog
    itog["кадр"] = str(put)
    _ev({"type": "kadr", "путь": str(put)})

    dusha = _dusha_treydera(slot)

    # ── СМОТРИТ. Ни одного числа в запросе. ──
    vzglyad = llm.chat_with_images(
        system=dusha, user_text=VOPROS_VZGLYAD, images=_kartinka(put),
        agent_id="treyder", slot_id=slot)
    itog["взгляд"] = vzglyad or ""
    _ev({"type": "vzglyad", "текст": itog["взгляд"], "слот": slot})

    prosba = _prosba_o_priborah(vzglyad)
    if not prosba:
        # Приборов не просил — значит и не нужны. Ничего больше не
        # считаем и не тратим: он посмотрел и сказал.
        itog["решение"] = itog["взгляд"]
        return itog

    itog["просил"] = prosba
    _ev({"type": "prosba", "текст": prosba})

    # ── ПОПРОСИЛ — ДАЁМ. Только теперь считаем. ──
    bars, point = source_bars(symbol, timeframe, count=400)
    if not bars or len(bars) < 42:
        itog["решение"] = itog["взгляд"] + "\n\n(приборов нет: баров мало)"
        return itog

    pribory, md = _pribory_tekstom(symbol, timeframe, bars, point)
    itog["приборы"] = pribory
    _ev({"type": "pribory", "текст": pribory})

    dogovorka = llm.chat_with_images(
        system=dusha,
        user_text=VOPROS_PRIBORY.format(pribory=pribory),
        images=_kartinka(put),
        history=[{"role": "user", "content": VOPROS_VZGLYAD},
                 {"role": "assistant", "content": vzglyad}],
        agent_id="treyder", slot_id=slot)
    itog["решение"] = dogovorka or ""
    _ev({"type": "reshenie", "текст": itog["решение"], "слот": slot})

    # Стол в шину — для дневника и для ведения позиции.
    # Код ничего не решает, только кладёт факты рядом с решением.
    try:
        from hooks import load_trading_state, save_trading_state
        ts = load_trading_state()
        ts["market_data"] = md
        ts.setdefault("vzglyad", {})[slot] = {
            "кадр": str(put), "взгляд": vzglyad, "решение": itog["решение"]}
        save_trading_state(ts)
    except Exception:
        pass

    return itog
