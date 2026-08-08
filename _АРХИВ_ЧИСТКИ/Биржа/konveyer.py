# -*- coding: utf-8 -*-
# KONVEYER_BEZ_SOVETA_V1
"""
КОНВЕЙЕР — Совет без голосов.

РЕШЕНИЕ ШЕФА (06.08): Совет упраздняется, живые голоса из индикаторов
убираются. Живыми остаются трейдер и Архивариус. Остальное —
математика, пусть работает код.

ПОЧЕМУ ЭТО ОКАЗАЛОСЬ МАЛЕНЬКОЙ РАБОТОЙ
    Вся математика сенсоров уже посчитана: `build_market_data` одним
    вызовом даёт Аллигатор, AO, фракталы, MFI, приседающие бары,
    дивергенцию, разворотный бар Necron, резинку Джастин и форму волны,
    а `global_anchor.global_trend` — веер Аллигатора СТАРШЕГО этажа.
    LLM-слоты сенсоров ничего к этому не добавляли: они пересказывали
    уже посчитанное. Значит «сенсоры в код» — это не писать код, а
    перестать звать голоса поверх него.

ПОРЯДОК — ТОТ, ЧТО РЕШИЛ ШЕФ 04.08 (в Совете он был обратный)
    1. МОРЖ ПЕРВЫЙ, от рынка, со СВОЕГО старшего этажа: куда смотрит
       веер большой воды. Спит — расходимся.
    2. ОТКАТ СОСТОЯЛСЯ? Меряем резинкой: натяжение сокращалось и
       перестало. Безразмерно, порогов нет — сравниваем с прошлым
       баром, как глаз сравнивает расстояние до Аллигатора.
    3. ИСКРА ТОЛЬКО ТЕПЕРЬ и только В СТОРОНУ старшего: есть
       разворотный бар или нет.
    4. Есть — накрываем стол и будим ОДНОГО трейдера.

    В Совете было наоборот: Искра будила себя от рынка, Морж наследовал
    её этаж и потому ничего не мог опровергнуть — эхо, не проверка.

ПРАВО ПРОМОЛЧАТЬ СТАЛО БЕСПЛАТНЫМ
    Три места, где конвейер расходится, НЕ разбудив никого: старший
    спит; откат не состоялся; бара нет или он против старшего. Раньше
    «промолчать» стоило вызова модели — теперь это просто return.

ЧЕГО КОНВЕЙЕР НЕ ДЕЛАЕТ
    Не трогает мозг трейдера. Он пишет в общую шину ТЕ ЖЕ ключи
    (iskra/morj/panic/hans), что писали слоты, — только заполняет их
    из кода. Трейдер читает стол как читал, переучивать его не надо.

    Не открывает позиций: этим занята рука-код в hooks.

СТАРЫЙ СОВЕТ НЕ УДАЛЁН. Лежит рядом, можно сравнить и откатиться.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable, Optional

_BIRZHA = Path(__file__).resolve().parent
_REPO = _BIRZHA.parent

# ─────────────────────────────────────────────────────────────
# ГДЕ ЖИВЁТ ТРЕЙДЕР. Один слот — характер даёт носитель, не слот
# (закон Картриджа: «они все сами по себе разные»). Сменил
# носителя — сменил характер, архитектуру не трогаешь.
# ─────────────────────────────────────────────────────────────
TREYDER = ("торговый_хаос", "A06", "run_brut")
ARKHIV = ("контора", "архивариус", "run_arkhiv")

_BRAIN_CACHE: dict = {}


def _brain(ceh_id: str, slot: str):
    """Закон Картриджа для кода — тот же механизм, что в council.py."""
    key = (ceh_id, slot)
    if key in _BRAIN_CACHE:
        return _BRAIN_CACHE[key]
    p = (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh_id
         / "слоты" / slot / "мозг.py")
    if not p.exists():
        _BRAIN_CACHE[key] = None
        return None
    spec = importlib.util.spec_from_file_location(f"_brain_{ceh_id}_{slot}", p)
    if spec is None or spec.loader is None:
        _BRAIN_CACHE[key] = None
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _BRAIN_CACHE[key] = mod
    return mod


# ═════════════════════════════════════════════════════════════
# ШАГ 2 — ОТКАТ СОСТОЯЛСЯ?
# ═════════════════════════════════════════════════════════════

def otkat_sostoyalsya(md_seychas: dict, md_ranshe: dict) -> dict:
    """Состоялся ли откат — по резинке, безразмерно и без порогов.

    Слово Шефа: «идёт ОТ Аллигатора — импульс, идёт К Аллигатору —
    коррекция». Резинка Джастин мерит ровно это: пустоту между ценой
    и Губами. tension_ratio = нынешнее натяжение к максимальному за
    жизнь движения.

        растёт или держится  → импульс идёт, ждать нечего
        сокращается          → откат идёт, ещё рано
        сокращалось и встало → ОТКАТ СОСТОЯЛСЯ, вот сюда и смотрим

    Сравниваем с ПРОШЛЫМ баром, а не с числом — потому порога здесь
    нет и быть не может (в источниках его тоже нет: сон и бодрствование
    определяет глаз).
    """
    rb_now = (md_seychas or {}).get("rubber_band", {}) or {}
    rb_pre = (md_ranshe or {}).get("rubber_band", {}) or {}
    t_now = rb_now.get("tension_ratio")
    t_pre = rb_pre.get("tension_ratio")

    if t_now is None or t_pre is None:
        return {"состоялся": False, "почему": "резинка не натянута — "
                                              "движения для отрыва нет",
                "tension_now": t_now, "tension_prev": t_pre}

    if t_now > t_pre:
        return {"состоялся": False, "почему": "натяжение растёт — импульс идёт",
                "tension_now": t_now, "tension_prev": t_pre}
    if t_now < t_pre:
        return {"состоялся": False, "почему": "натяжение сокращается — откат идёт",
                "tension_now": t_now, "tension_prev": t_pre}
    return {"состоялся": True, "почему": "натяжение перестало сокращаться",
            "tension_now": t_now, "tension_prev": t_pre}


# ═════════════════════════════════════════════════════════════
# НАКРЫТЬ СТОЛ ИЗ КОДА
# ═════════════════════════════════════════════════════════════

def nakryt_stol(md: dict, starshiy: dict, otkat: dict) -> dict:
    """Заполняет те же ключи шины, что писали слоты-голоса.

    Формы не выдумываем: имена полей взяты из того, что читает мозг
    трейдера (`_read_table`). Он не должен заметить подмены — для него
    стол тот же, просто накрыт кодом, а не пересказом.
    """
    nb = md.get("necron_bar", {}) or {}
    rb = md.get("rubber_band", {}) or {}
    wf = md.get("wave_form", {}) or {}
    fr = md.get("fractals", {}) or {}
    al = md.get("alligator", {}) or {}
    mfi = md.get("mfi", {}) or {}

    # Ганс: действительный фрактал — тот, что ЗА пастью (§8 Котина).
    # Сторона берётся по направлению большой воды, а не по «последнему».
    storona = "up" if starshiy.get("bias") == "BULL" else "down"
    f_key = "last_up" if storona == "up" else "last_down"
    f = fr.get(f_key) or {}
    f_price = f.get("price")
    f_valid = False
    if f_price is not None and al.get("teeth") is not None:
        f_valid = (f_price > al["teeth"]) if storona == "up" else (f_price < al["teeth"])

    return {
        "iskra": {
            # Искра — ДАТЧИК, не диспетчер: есть/нет, куда, где край стопа.
            "t1_status": "BAR" if nb.get("direction") else "NONE",
            "trend_direction": nb.get("direction"),
            "zero_point_price": nb.get("stop_price") or nb.get("extremum"),
            "struktura_chitaetsya": bool(wf.get("читается", True)),
            "compass": starshiy.get("bias"),
            "soglasie": (nb.get("direction") == starshiy.get("bias")),
            "dlina": wf.get("dlina"),
        },
        "morj": {
            # Морж — направление большой воды и натяжение. Первый в цепи.
            "morj_status": starshiy.get("bias"),
            "senior_tf": starshiy.get("senior_tf"),
            "tension_peak": rb.get("is_peak"),
            "tension_ratio": rb.get("tension_ratio"),
            "otkat_sostoyalsya": otkat.get("состоялся"),
            "wave_1_validated": wf.get("wave_1_validated"),
        },
        "panic": {
            "panic_phase": mfi.get("phase") or mfi.get("window"),
            "crowd_sentiment": mfi.get("sentiment"),
        },
        "hans": {
            "fractal_valid": f_valid,
            "fractal_side": storona,
            "fractal_price": f_price,
        },
    }


# ═════════════════════════════════════════════════════════════
# ГЛАВНОЕ — ОДИН ПРОХОД КОНВЕЙЕРА НА БАРЕ
# ═════════════════════════════════════════════════════════════

def progon(symbol: str, timeframe: str,
           on_event: Optional[Callable] = None,
           budit_treydera: bool = True) -> dict:
    """Один проход. Возвращает сводку; трейдера будит только если есть о чём.

    on_event(dict) — вести наружу (лента кабинета), может быть None.
    budit_treydera=False — посчитать и показать стол, никого не будя
    (для кабинета: посмотреть, что видит код, не тратя модель).
    """
    def _ev(d):
        if on_event:
            try:
                on_event(d)
            except Exception:
                pass

    itog = {"symbol": symbol, "timeframe": timeframe,
            "разошлись": False, "почему": "", "стол": {}, "трейдер": None}

    import sys
    if str(_BIRZHA) not in sys.path:
        sys.path.insert(0, str(_BIRZHA))
    from feed_source import bars as source_bars
    from williams_core import build_market_data
    from global_anchor import global_trend

    bars, point = source_bars(symbol, timeframe, count=400)
    if not bars or len(bars) < 42:
        itog.update(разошлись=True, почему="баров мало — считать нечем")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog

    # ── ШАГ 1. МОРЖ: направление со СТАРШЕГО этажа, от рынка ──
    starshiy = global_trend(symbol, timeframe, as_of_date=bars[-1].get("date"))
    _ev({"type": "morj", "bias": starshiy.get("bias"),
         "senior_tf": starshiy.get("senior_tf")})

    if starshiy.get("bias") not in ("BULL", "BEAR"):
        itog.update(разошлись=True,
                    почему=f"старший Аллигатор спит ({starshiy.get('senior_tf')}) "
                           f"— большой воды нет, входа нет")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog

    # ── факты рынка на этом и на прошлом баре ──
    md = build_market_data(bars, symbol, timeframe, point=point)
    if not md:
        itog.update(разошлись=True, почему="стол не собрался")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog
    md_pre = build_market_data(bars[:-1], symbol, timeframe, point=point)

    # ── ШАГ 2. ОТКАТ СОСТОЯЛСЯ? ──
    otkat = otkat_sostoyalsya(md, md_pre)
    _ev({"type": "otkat", **otkat})
    if not otkat["состоялся"]:
        itog.update(разошлись=True, почему=otkat["почему"], стол={})
        _ev({"type": "idle", "why": otkat["почему"]})
        return itog

    # ── ШАГ 3. ИСКРА: бар есть? и в сторону ли старшего? ──
    nb = md.get("necron_bar", {}) or {}
    napravlenie = nb.get("direction")
    if not napravlenie:
        itog.update(разошлись=True, почему="разворотного бара нет")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog
    if napravlenie != starshiy["bias"]:
        itog.update(разошлись=True,
                    почему=f"бар {napravlenie} против большой воды "
                           f"{starshiy['bias']} — не наш")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog

    # ── ШАГ 4. НАКРЫВАЕМ СТОЛ И БУДИМ ОДНОГО ТРЕЙДЕРА ──
    stol = nakryt_stol(md, starshiy, otkat)
    itog["стол"] = stol

    from hooks import load_trading_state, save_trading_state
    ts = load_trading_state()
    ts.update(stol)
    ts["market_data"] = md
    save_trading_state(ts)
    _ev({"type": "stol", "стол": stol})

    if not budit_treydera:
        return itog

    ceh, slot, fn = TREYDER
    brain = _brain(ceh, slot)
    if brain is None or not hasattr(brain, fn):
        itog.update(разошлись=True, почему=f"слот трейдера {slot} — вакансия")
        _ev({"type": "idle", "why": itog["почему"]})
        return itog

    try:
        itog["трейдер"] = getattr(brain, fn)(symbol=symbol, timeframe=timeframe)
    except Exception as e:
        itog["трейдер"] = {"ok": False, "error": str(e)}
    _ev({"type": "trader", "result": itog["трейдер"]})
    return itog
