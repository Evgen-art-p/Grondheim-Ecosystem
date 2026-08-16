# -*- coding: utf-8 -*-
# RUKI_TREYDERA_V1
"""
РУКИ ТРЕЙДЕРА — математика по просьбе, а не по рельсам.

ЗАКОН ЭТОГО ФАЙЛА
    Ни одна рука ничего не решает и не советует. Руки считают и
    отдают ЧИСЛА. Что эти числа значат — говорит трейдер.
    КАНОН_ВХОДА.md §1④: индикаторы — ориентиры, НЕ сигналы; путь по
    их комбинации ищет трейдер. §1⑥: математику считает код, решает
    LLM и только на готовом.

    Поэтому здесь нет и не будет: «сигнал есть», «вход годится»,
    «структура подтверждена», «рекомендую». Только факт и его цена.

ПОЧЕМУ ЭТО ВАЖНО
    Раньше код сам решал, какую математику посчитать, — исходя из
    роли, прибитой к слоту. Трейдер не просил: ему приносили. Теперь
    он просит сам, и его личный выбор паттерна наконец на что-то
    влияет.
"""
from __future__ import annotations

import json
import sys as _sys
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))


def shema(rabochiy_etazh: str = "") -> list:
    """Описание рук для модели. Формулировки нарочно сухие: рука —
    это прибор, а не советчик."""
    import masshtab
    etazhi = ", ".join(masshtab.LESTNICA)
    nizhe = masshtab.nizhe(rabochiy_etazh) or "—"
    vyshe = masshtab.vyshe(rabochiy_etazh) or "—"
    return [
        {"type": "function", "function": {
            "name": "stol_na_etazhe",
            "description": (
                "Накрыть стол на указанном этаже: Аллигатор, AO, фракталы, "
                "разворотный бар, окно объёма, натяжение, цена. Голые "
                f"показания, без выводов. Этажи: {etazhi}. "
                f"На ступень ниже твоего рабочего — {nizhe}, выше — {vyshe}."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string",
                         "description": "например H1"}},
                "required": ["этаж"]}}},
        {"type": "function", "function": {
            "name": "izmerit_volnu",
            "description": (
                "Померить волновую структуру на указанном этаже: длина в "
                "барах от четвёртого пересечения нуля AO назад до текущего "
                "бара, читается ли внутри пятёрка, направление и цена "
                "разворотного бара, дивергенция, ангуляция. Числа, не "
                "вердикт."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string",
                         "description": "например H1"}},
                "required": ["этаж"]}}},
        {"type": "function", "function": {
            "name": "moy_dnevnik",
            "description": (
                "Твои последние записи: что ты решал, чем кончилось. "
                "Своя память, не чужая."),
            "parameters": {"type": "object", "properties": {
                "сколько": {"type": "integer",
                            "description": "по умолчанию 5"}},
                "required": []}}},
    ]


def _chislo(x):
    return x if isinstance(x, (int, float)) and x == x else None


def ruki(symbol: str, ceh: str, slot: str, self_key: str,
         dnevnik_fn=None) -> dict:
    """Собрать руки для этого трейдера. Возвращает {имя: функция}."""

    def _stol(args: dict) -> str:
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                return f"Такого этажа нет: {tf}. Есть: {', '.join(masshtab.LESTNICA)}"
            import stol as _s
            t = _s.nakryt(symbol, tf, self_key=self_key)
            return f"=== СТОЛ · {symbol} {tf} ===\n" + _s.slovami(t)
        except Exception as e:
            return f"стол на {tf} не накрылся: {e}"

    def _volna(args: dict) -> str:
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                return f"Такого этажа нет: {tf}"
            from feed_source import bars as _bars
            from williams_core import build_market_data
            b, point = _bars(symbol, tf, 300)
            if not b or point is None:
                return f"котировок {symbol} {tf} не дали"
            md = build_market_data(b, symbol=symbol, timeframe=tf,
                                   point=point)
            wf = (md or {}).get("wave_form") or {}
            d = {
                "этаж": tf,
                "длина_волны_баров": _chislo(wf.get("dlina")),
                "структура_читается": wf.get("struktura_chitaetsya"),
                "почему": wf.get("struktura_prichina"),
                "разворотный_бар_направление": wf.get("bdb_dir"),
                "разворотный_бар_цена": _chislo(wf.get("bdb_price")),
                # ВАЖНО: дивергенция и ангуляция живут НЕ в форме волны.
                # Проверено 15.08: в wave_form есть divergence_dir, а
                # сама дивергенция — md["divergence_ao"], ангуляция же
                # меряется резинкой Джастин (отрыв цены от Аллигатора)
                # в md["rubber_band"]. Читать их из wave_form — значит
                # вечно отдавать пустоту.
                "дивергенция_в_волне": wf.get("divergence_dir"),
                "дивергенция_AO": (md or {}).get("divergence_ao"),
                "ангуляция_отрыв_пунктов":
                    _chislo(((md or {}).get("rubber_band") or {})
                            .get("distance_now")),
                "ангуляция_доля_от_максимума":
                    _chislo(((md or {}).get("rubber_band") or {})
                            .get("tension_ratio")),
                "ангуляция_на_пике":
                    ((md or {}).get("rubber_band") or {}).get("is_peak"),
                "разворотный_бар_некрона": (md or {}).get("necron_bar"),
                "компас": (md or {}).get("global_bias"),
                "окно_измерения_баров": wf.get("window"),
            }
            return ("=== ВОЛНА · измерено, не истолковано ===\n"
                    + json.dumps(d, ensure_ascii=False, indent=1))
        except Exception as e:
            return f"волна на {tf} не померилась: {e}"

    def _dnevnik(args: dict) -> str:
        n = int(args.get("сколько") or 5)
        if dnevnik_fn is None:
            return "дневник недоступен"
        try:
            zapisi = dnevnik_fn(n) or []
            if not zapisi:
                return "записей пока нет"
            return ("=== ДНЕВНИК · последние " + str(len(zapisi)) + " ===\n"
                    + json.dumps(zapisi, ensure_ascii=False, indent=1)[:3000])
        except Exception as e:
            return f"дневник не прочитался: {e}"

    return {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik}


# RUKI_TREYDERA_V1 - marker
