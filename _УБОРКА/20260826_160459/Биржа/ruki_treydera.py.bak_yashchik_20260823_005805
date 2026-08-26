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
        # RUKA_MAYAKA_V1: выход наружу. Раньше житель мог спросить мир
        # только ДОМА — на работе мозг был глухой.
        *_ruka_mayaka_shema(),
        # RASTYAZHKA_V1: главные глаза трейдера. Раньше он видел ровно
        # один кадр — последние 140 баров рабочего этажа, — и растянуть
        # нужную волну не мог ничем.
        {"type": "function", "function": {
            "name": "rastyanut_volnu",
            "description": (
                "ПОКАЗАТЬ картинку куска рынка, растянутого так, чтобы он "
                "занял 100-140 баров. Так смотрят зигзаг целиком, а потом "
                "волну C внутри него. Этаж подбирается сам под длину "
                "куска — можешь не указывать. Ты УВИДИШЬ картинку."),
            "parameters": {"type": "object", "properties": {
                "с": {"type": "string",
                      "description": "начало куска, вид 2025.05.05 20:00"},
                "по": {"type": "string",
                       "description": "конец куска; пусто — до текущего бара"},
                "этаж": {"type": "string",
                         "description": "необязательно, если хочешь свой"}},
                "required": ["с"]}}},
        # KRAYNIYE_TOCHKI_V1: опора для растяжки. Не разметка волн и
        # не фракталы (те всюду и шумят) — вершина и дно, то, что глаз
        # ловит сразу. Числа нужны, чтобы назвать границы точно: на
        # кадре подписи мелкие, дату по картинке не прочесть.
        {"type": "function", "function": {
            "name": "krayniye_tochki",
            "description": (
                "Вершина и дно на куске: когда и почём. Отдельно по первой "
                "и второй половине куска. Голые числа — какая из этих точек "
                "начало твоей волны, решаешь ты, глядя на картинку. Нужны, "
                "чтобы назвать границы для rastyanut_volnu без промаха."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string",
                         "description": "пусто — твой рабочий"},
                "баров": {"type": "integer",
                          "description": "сколько баров назад смотреть, "
                                         "по умолчанию 140"}},
                "required": []}}},
        {"type": "function", "function": {
            "name": "pokazat_etazh",
            "description": (
                "ПОКАЗАТЬ картинку другого этажа целиком, последние 140 "
                "баров. Когда нужно просто взглянуть шире или мельче."),
            "parameters": {"type": "object", "properties": {
                "этаж": {"type": "string", "description": "например M30"}},
                "required": ["этаж"]}}},
        # DOSKA_V1: общая память о структуре. Разворотник нельзя
        # отсеять числами — отсев это взгляд на растянутой волне C.
        # Кто посмотрел и увидел конец коррекции, тот и объявляет
        # точку ноль; от неё пляшут остальные.
        # KARTINA_SVOYA_V1: твоё чтение, не общее. Стол один на всех,
        # факты одинаковые — а волны у каждого свои. Чужих картин ты
        # не видишь: пока каждый не разобрался в своём, подсматривание
        # свело бы всех в одно мнение.
        {"type": "function", "function": {
            "name": "moya_kartina",
            "description": (
                "ТВОЁ чтение этого рынка, как ты его оставил(а) в прошлый "
                "раз: где ТВОЯ точка ноль, пошла ли от неё волна, видишь ли "
                "откат. Смотри ПЕРВЫМ делом — иначе начнёшь с чистого листа "
                "и не увидишь того, что уже разглядел(а) раньше."),
            "parameters": {"type": "object", "properties": {}, "required": []}}},
        {"type": "function", "function": {
            "name": "zapisat_v_kartinu",
            "description": (
                "Записать в СВОЮ картину то, что ты увидел(а). "
                "«точка_ноль» — здесь, по-твоему, кончилась коррекция. "
                "«волна» — от неё пошло движение и дошло досюда. "
                "«откат» — к своей волне видишь откат. "
                "«заметка» — мысль на память. «стереть» — твоя структура "
                "сломалась. Это ТВОЁ чтение: сосед может видеть иначе, и "
                "это нормально."),
            "parameters": {"type": "object", "properties": {
                "что": {"type": "string",
                        "description": "точка_ноль | волна | откат | заметка | стереть"},
                "цена": {"type": "number", "description": "если есть"},
                "бар": {"type": "string",
                        "description": "дата бара, вид 2025.05.05 20:00"},
                "почему": {"type": "string",
                           "description": "что именно ты увидел(а) — своими словами"}},
                "required": ["что"]}}},
        # UCHEBNIK_V_RUKE_V1: картинки из книги, по которой учили.
        # В памяти у неё лежит ПЕРЕСКАЗ рисунка, а не рисунок — можно
        # посмотреть заново, стоя перед живым графиком.
        {"type": "function", "function": {
            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ картинку из того, по чему тебя учили в Академии: "
                "«приседающий бар», «фрактал», «волны AO», «окно объёма». "
                "Ты УВИДИШЬ сам рисунок и авторскую подпись к нему. Полезно, "
                "когда сомневаешься, как выглядит паттерн в учебнике — "
                "сравни с тем, что на графике сейчас. Можно сузить до "
                "дисциплины: финансы, психология, искусство."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string",
                          "description": "тема словами, например «приседающий бар»"},
                "дисциплина": {"type": "string",
                               "description": "необязательно: сузить поиск"}},
                "required": ["о_чём"]}}},
        {"type": "function", "function": {
            "name": "chemu_uchili",
            "description": (
                "Какие дисциплины и сколько рисунков есть в Академии. "
                "Смотри, если не знаешь, о чём вообще можно спросить."),
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},
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
         dnevnik_fn=None, rabochiy_etazh: str = "H4",
         imya_zhitelya: str = "") -> dict:
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

    def _rastyanut(args: dict) -> str:
        """RASTYAZHKA_V1: возвращает МЕТКУ кадра — картинку дошлёт
        разговор. Текстом картинку не передать, а трейдеру нужно
        именно увидеть."""
        try:
            import rastyanut as _r
            d = _r.rastyanut(symbol, str(args.get("с", "")),
                             str(args.get("по", "")),
                             str(args.get("этаж", "")))
        except Exception as e:
            return f"растянуть не вышло: {e}"
        if not d.get("кадр"):
            return d.get("пояснение") or "кадр не нарисовался"
        return (f"[КАДР: {d['кадр']}] {d.get('пояснение', '')} · "
                f"с {d.get('с')} по {d.get('по')}")

    def _pokazat_etazh(args: dict) -> str:
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                return f"такого этажа нет: {tf}"
            import grafik
            put = grafik.kadr(symbol, tf)
        except Exception as e:
            return f"показать {tf} не вышло: {e}"
        if not put:
            return f"котировок {symbol} {tf} не дали"
        return f"[КАДР: {put}] {symbol} {tf}, последние 140 баров"

    def _krayniye(args: dict) -> str:
        """KRAYNIYE_TOCHKI_V1: вершина и дно. Факты, не разметка."""
        tf = str(args.get("этаж", "")).strip().upper()
        try:
            import masshtab
            if not masshtab.est(tf):
                tf = rabochiy_etazh if masshtab.est(rabochiy_etazh) else "H4"
            n = int(args.get("баров") or 140)
            from feed_source import bars as _bars
            b, _p = _bars(symbol, tf, max(n, 60))
        except Exception as e:
            return f"крайние точки не посчитались: {e}"
        if not b:
            return f"котировок {symbol} {tf} не дали"
        b = b[-n:]

        def _kray(kusok, imya):
            if not kusok:
                return f"{imya}: пусто"
            v = max(kusok, key=lambda x: x["high"])
            d = min(kusok, key=lambda x: x["low"])
            return (f"{imya}: вершина {v['high']} ({v.get('date')}) · "
                    f"дно {d['low']} ({d.get('date')})")

        pol = len(b) // 2
        v = max(b, key=lambda x: x["high"])
        d = min(b, key=lambda x: x["low"])
        mezhdu = abs(b.index(v) - b.index(d))
        return ("=== КРАЙНИЕ ТОЧКИ · факты, не разметка ===\n"
                f"{symbol} {tf}, {len(b)} баров "
                f"({b[0].get('date')} → {b[-1].get('date')})\n"
                + _kray(b, "всё окно") + "\n"
                + f"между вершиной и дном: {mezhdu} баров\n"
                + _kray(b[:pol], "первая половина") + "\n"
                + _kray(b[pol:], "вторая половина"))

    def _moya_kartina(args: dict) -> str:
        try:
            import kartina
            return kartina.slovami(ceh, slot, symbol)
        except Exception as e:
            return f"картина не прочиталась: {e}"

    def _zapisat_v_kartinu(args: dict) -> str:
        try:
            import kartina
            ok, m = kartina.obyavit(
                ceh, slot, symbol, str(args.get("что", "")),
                kto=(imya_zhitelya or slot), cena=args.get("цена"),
                bar=str(args.get("бар", "")),
                pochemu=str(args.get("почему", "")))
        except Exception as e:
            return f"записать не вышло: {e}"
        print(f"[КАРТИНА] {'✓' if ok else '✗'} {imya_zhitelya or slot}: {m}")
        return ("Записал(а) в твою картину. " + m) if ok else ("Не записано: " + m)

    def _uchebnik(args: dict) -> str:
        """UCHEBNIK_DISCIPLINY_V1: показать рисунок из Академии.

        Ищет по ВСЕМ дисциплинам: списка книг в коде нет, сканируется
        дерево. Появится новая книга — будет видна сразу.
        """
        o = str(args.get("о_чём", "")).strip()
        tema = str(args.get("дисциплина", "")).strip()
        try:
            import uchebnik as _u
            nashlos = _u.nayti(o, skolko=1, tema=tema)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            try:
                import uchebnik as _u
                spisok = _u.temy()
            except Exception:
                spisok = ""
            gde = f" в дисциплине «{tema}»" if tema else ""
            return (f"по «{o}»{gde} рисунка не нашёл. Что есть в Академии:\n"
                    f"{spisok}")
        p, t, glava, podpis = nashlos[0]
        hvost = f" · {glava}" if glava else ""
        podp = f"\nподпись автора: {podpis}" if podpis else ""
        return f"[КАДР: {p}] учебник · {t}{hvost} · {p.name}{podp}"

    def _chemu_uchili(args: dict) -> str:
        try:
            import uchebnik as _u
            return "=== ЧЕМУ УЧАТ В АКАДЕМИИ ===\n" + _u.temy()
        except Exception as e:
            return f"дисциплины не прочитались: {e}"

    itog = {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik,
            "uchebnik": _uchebnik,          # UCHEBNIK_DISCIPLINY_V1
            "chemu_uchili": _chemu_uchili,
            "moya_kartina": _moya_kartina,            # KARTINA_SVOYA_V1
            "zapisat_v_kartinu": _zapisat_v_kartinu,
            "krayniye_tochki": _krayniye,      # KRAYNIYE_TOCHKI_V1
            "rastyanut_volnu": _rastyanut,      # RASTYAZHKA_V1
            "pokazat_etazh": _pokazat_etazh}
    itog.update(_ruka_mayaka_ruki(slot))   # RUKA_MAYAKA_V1
    return itog


# ── RUKA_MAYAKA_V1: одна дверь наружу на весь город ──────────
def _ruka_mayaka_shema() -> list:
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import ruka_mayaka
        return ruka_mayaka.shema()
    except Exception:
        return []          # Маяка нет — руки просто не будет


def _ruka_mayaka_ruki(kto: str) -> dict:
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _g not in _s.path:
            _s.path.insert(0, _g)
        import ruka_mayaka
        return ruka_mayaka.ruki(kto)
    except Exception:
        return {}


# RUKI_TREYDERA_V1 - marker

# RUKA_MAYAKA_V1 - marker

# RASTYAZHKA_V1 - marker

# KRAYNIYE_TOCHKI_V1 - marker

# DOSKA_V1 - marker

# KARTINA_SVOYA_V1 - marker

# UCHEBNIK_V_RUKE_V1 - marker

# UCHEBNIK_DISCIPLINY_V1 - marker
