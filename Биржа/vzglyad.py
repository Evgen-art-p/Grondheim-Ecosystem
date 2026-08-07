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

# Слот трейдера один. Характер даёт носитель, а не слот — закон
# Картриджа («они все сами по себе разные»). Сменил носителя —
# сменил характер, архитектуру не трогаешь.
TREYDER_CEH, TREYDER_SLOT = "торговый_хаос", "A06"


# ═════════════════════════════════════════════════════════════
# ШАГ 1 — ВЗГЛЯД. Голая картинка, ни одного числа.
# ═════════════════════════════════════════════════════════════
VOPROS_VZGLYAD = """Перед тобой график. Больше ничего — ни показаний
приборов, ни подсказок. Смотри своими глазами.

Первой строкой ответь ровно одним словом:
ВИЖУ — если на правом краю складывается рабочая картина;
МИМО — если нет: намешано, линии сплелись, ничего не выделяется,
       или движение уже ушло без тебя.

МИМО — нормальный ответ и самый частый. Отказ это работа, а не её
отсутствие. Не выдумывай картину, если её нет.

Дальше 2–4 строки: что именно ты видишь. Только то, что нарисовано —
как идут линии друг относительно друга, где цена по отношению к ним,
что с гистограммой внизу. Без выводов о будущем."""


# ═════════════════════════════════════════════════════════════
# ШАГ 2 — ПРИБОРЫ. Только если увидел.
# ═════════════════════════════════════════════════════════════
VOPROS_PRIBORY = """Ты увидел картину и сказал:

{vzglyad}

Теперь показания приборов по тому же графику:

{pribory}

Сверь их с тем, что видел глазом. Если прибор говорит не то, что ты
разглядел, — так и скажи, это важнее, чем сойтись.

Ответь так:
РЕШЕНИЕ: ВХОД | ЖДУ | МИМО
СТОРОНА: BUY | SELL | —
СТОП: цена, за которой ты неправ (или —)
ПОЧЕМУ: 2–3 строки своими словами

ВХОД бери только если сходится всё сразу: направление большой воды,
откат состоялся, бар в ту же сторону и стоп выходит коротким. Не
сошлось хоть одно — ЖДУ или МИМО. Длинный стоп означает, что движение
ушло без тебя: это не повод входить осторожнее, это повод пропустить."""


def _dusha_treydera() -> str:
    """Личность носителя со всем нажитым — то же, что видит его кабинет."""
    try:
        from nositel import dusha_slota
        d = dusha_slota(TREYDER_CEH, TREYDER_SLOT)
        return d.get("душа") or d.get("dusha") or ""
    except Exception:
        return ""


def _kartinka(put: Path) -> list:
    return [{"base64": base64.b64encode(put.read_bytes()).decode("ascii"),
             "mime_type": "image/png", "name": put.name}]


def _pervoe_slovo(otvet: str) -> str:
    """ВИЖУ или МИМО из первой строки. Не разобрали — считаем МИМО:
    непонятный ответ не повод тратить второй вызов."""
    for s in (otvet or "").strip().splitlines():
        s = s.strip().upper()
        if not s:
            continue
        if s.startswith("ВИЖУ"):
            return "ВИЖУ"
        if s.startswith("МИМО"):
            return "МИМО"
        break
    return "МИМО"


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
              kadr_put: Optional[Path] = None) -> dict:
    """Один взгляд трейдера. Возвращает что увидел и что решил.

    on_event(dict) — вести в кабинет, может быть None.
    """
    def _ev(d):
        if on_event:
            try:
                on_event(d)
            except Exception:
                pass

    itog = {"symbol": symbol, "timeframe": timeframe, "кадр": None,
            "взгляд": "", "увидел": False, "приборы": "", "решение": ""}

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

    dusha = _dusha_treydera()

    # ── ШАГ 1: смотрит. Ни одного числа в запросе. ──
    vzglyad = llm.chat_with_images(
        system=dusha, user_text=VOPROS_VZGLYAD, images=_kartinka(put),
        agent_id="treyder", slot_id=TREYDER_SLOT)
    itog["взгляд"] = vzglyad or ""
    _ev({"type": "vzglyad", "текст": itog["взгляд"]})

    if _pervoe_slovo(vzglyad) != "ВИЖУ":
        itog["решение"] = "МИМО"
        _ev({"type": "reshenie", "решение": "МИМО",
             "почему": "картины не увидел"})
        return itog

    itog["увидел"] = True

    # ── ШАГ 2: только теперь приборы ──
    bars, point = source_bars(symbol, timeframe, count=400)
    if not bars or len(bars) < 42:
        itog["решение"] = "МИМО"
        _ev({"type": "reshenie", "решение": "МИМО", "почему": "баров мало"})
        return itog

    pribory, md = _pribory_tekstom(symbol, timeframe, bars, point)
    itog["приборы"] = pribory
    _ev({"type": "pribory", "текст": pribory})

    reshenie = llm.chat_with_images(
        system=dusha,
        user_text=VOPROS_PRIBORY.format(vzglyad=vzglyad, pribory=pribory),
        images=_kartinka(put),
        agent_id="treyder", slot_id=TREYDER_SLOT)
    itog["решение"] = reshenie or ""
    _ev({"type": "reshenie", "текст": itog["решение"]})

    # Стол в шину — для дневника и для ведения позиции.
    # Код ничего не решает, только кладёт факты рядом с решением.
    try:
        from hooks import load_trading_state, save_trading_state
        ts = load_trading_state()
        ts["market_data"] = md
        ts["vzglyad"] = {"кадр": str(put), "взгляд": vzglyad,
                         "решение": itog["решение"]}
        save_trading_state(ts)
    except Exception:
        pass

    return itog
