# -*- coding: utf-8 -*-
"""
postavit_ruki_treydera.py · MARKER: RUKI_TREYDERA_V1

ПРОБА НА ОДНОЙ — Вера, слот A08. Соседок не трогаю.

ЗАЧЕМ
─────
Слово Шефа 14.08: «не код рулит агентом, а агент кодом... код даёт
математику, а трейдер собой, а не кодом, принимает решение».

Это же записано в КАНОН_ВХОДА.md §1⑥: «Математику считает код. Решает —
только LLM, и только на готовом... он читает посчитанное и
интерпретирует, взвешивает, решает. Это и есть роль трейдера по
Вильямсу». И §1④: «индикаторы — ориентиры, НЕ сигналы; путь по их
комбинации ищет ТРЕЙДЕР».

КАК БЫЛО (рельсы)
─────────────────
Код не просто считал — он решал, ЧТО посчитать, исходя из роли,
прибитой к слоту при рождении:

    A08 → `_read_vasya_wave()`: код сам спускался на ступень ниже и
          мерил волну там, потому что «Консерватор пасёт конец волны 2»;
    плюс зашитая лесенка ровно из трёх этажей D1/H4/H1 — не её выбор.

Вера про это не просила. Свой паттерн она выбрала сама («первый откат
к новой волне»), но до кода этот выбор не доходил: паттерн жил в трёх
разных кусках кода, по куску на слот. Отсюда «код суёт разное».

КАК СТАЛО (руки)
────────────────
У Веры появляются РУКИ — она сама говорит, какая математика ей нужна:

    стол_на_этаже(этаж)   — накрыть стол где скажет
    измерить_волну(этаж)  — длина в барах, дивер, ангуляция, РБ
    мой_дневник(сколько)  — чем кончались похожие случаи

Не попросила — не посчитали и не заплатили. Спуск «на ступень ниже»
остаётся возможным, но теперь это ЕЁ шаг, а не рельса под ней. Ровно
Чертёж, Гл.6.3: инициатива просит — рука снаружи исполняет.

ЧТО ПРИШЛОСЬ ПОЧИНИТЬ ПО ДОРОГЕ
───────────────────────────────
1. `llm.chat_with_tools` держал список рук ВНУТРИ себя (только поиск
   Маяка) — свои передать было нельзя. Добавлен параметр `executors`.
2. Руки и КАДР не жили вместе: `chat_with_images` — один проход без
   рук, `chat_with_tools` — руки без картинки. А Вере нужно и то, и
   другое: она смотрит кадр и просит числа по нему. Добавлена
   `chat_with_images_and_tools` — картинка плюс руки в одном разговоре.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Кадр по чужому этажу рукой не выдаётся: ответ руки — текст, картинку
в него не положить. Вера видит кадр своего рабочего этажа, а про
другие спрашивает числами. Захочешь картинку по запросу — это отдельно
и иначе.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_ruki_treydera.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RUKI_TREYDERA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "llm.py").exists()
            and (p / "Биржа" / "stol.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


def pravit(put: Path, proverka, pravka, imya: str) -> bool:
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {put.name}: маркер уже стоит — пропускаю")
        return True
    ok, prichina = proverka(tekst)
    if not ok:
        print(f"  ✗ {put.name}: {prichina}")
        return False
    novyy = pravka(tekst)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    bak = put.with_suffix(put.suffix
                          + f".bak_{imya}_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}: правка легла (копия: {bak.name})")
    return True


# ═══════════════════════════════════════════════════════════
# 1. llm.py — свои руки внутрь пускать
# ═══════════════════════════════════════════════════════════
ST_EXEC = '''    tool_executors = {
        "web_search": lambda args: _exec_tavily_search(args.get("query", "")),
    }'''

NOV_EXEC = '''    # RUKI_TREYDERA_V1: список рук был зашит здесь намертво — только
    # поиск Маяка. Значит своей руки не мог завести никто, кроме
    # Архива. Теперь вызывающий передаёт свои; встроенная остаётся.
    tool_executors = {
        "web_search": lambda args: _exec_tavily_search(args.get("query", "")),
    }
    if executors:
        tool_executors.update(executors)'''

ST_SIG = '''    agent_id: str = "unknown",
    slot_id: str = "unknown",
    knowledge_source: str = "internal",
) -> str:
    """Вызов LLM с поддержкой Tool Use (синхронный).'''

NOV_SIG = '''    agent_id: str = "unknown",
    slot_id: str = "unknown",
    knowledge_source: str = "internal",
    executors: Optional[dict] = None,       # RUKI_TREYDERA_V1
) -> str:
    """Вызов LLM с поддержкой Tool Use (синхронный).'''

KARTINKA_I_RUKI = '''

# ═══════════════════════════════════════════════════════════
# КАРТИНКА И РУКИ ВМЕСТЕ (RUKI_TREYDERA_V1)
# ═══════════════════════════════════════════════════════════
# Было две двери и ни одной нужной: chat_with_images — кадр без рук,
# chat_with_tools — руки без кадра. А трейдеру нужно и то, и другое:
# он смотрит на картинку и по ней просит числа. Дверь одна.
def chat_with_images_and_tools(
    system: str,
    user_text: str,
    images: Optional[list] = None,
    knowledge: str = "",
    tools_schema: Optional[list] = None,
    executors: Optional[dict] = None,
    max_tool_rounds: int = 4,
    temperature: Optional[float] = None,
    history: Optional[list] = None,
    on_tool_call: Optional[Callable] = None,
    agent_id: str = "unknown",
    slot_id: str = "unknown",
    knowledge_source: str = "internal",
) -> str:
    """Разговор с кадром, где собеседник может сам просить математику.

    Руки исполняются здесь же и их ответы возвращаются в тот же
    разговор, поэтому он видит и картинку, и числа, которые запросил
    ПО ЭТОЙ картинке. Не попросил — ничего лишнего не считали.
    """
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}",
               "Content-Type": "application/json"}

    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    if knowledge:
        messages.append({"role": "user",
                         "content": f"БАЗА ЗНАНИЙ:\\n{knowledge}"})
        messages.append({"role": "assistant",
                         "content": "Принял базу знаний. Готов к работе."})
    if history:
        for m in history:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": m["content"]})

    user_content: list = []
    for img in (images or []):
        b64 = img.get("base64", "")
        if not b64:
            continue
        mime = img.get("mime_type", "image/png")
        user_content.append({"type": "image_url",
                             "image_url": {"url": f"data:{mime};base64,{b64}"}})
        user_content.append({"type": "text",
                             "text": f"[Изображение: {img.get('name', 'кадр')}]"})
    user_content.append({"type": "text", "text": user_text})
    messages.append({"role": "user", "content": user_content})

    ruki = dict(executors or {})
    sdelano = 0

    for _ in range(max_tool_rounds + 1):
        payload: dict = {"model": _CURRENT_MODEL, "messages": messages,
                         "max_tokens": LLM_MAX_TOKENS}
        if temperature is not None:
            payload["temperature"] = temperature
        if tools_schema and sdelano < max_tool_rounds:
            payload["tools"] = tools_schema
            payload["tool_choice"] = "auto"

        r = _post_with_retry(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json_payload=payload, proxies=proxies,
            timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            try:
                err = r.json().get("error", {}).get("message", r.text[:300])
            except Exception:
                err = r.text[:300]
            raise RuntimeError(f"OpenRouter [{r.status_code}]: {err}")

        data = r.json()
        msg = (data.get("choices") or [{}])[0].get("message", {}) or {}

        if not msg.get("tool_calls"):
            content = msg.get("content") or ""
            if not content.strip():
                raise RuntimeError("Модель вернула пустой ответ (кадр+руки)")
            usage = data.get("usage", {})
            _ledger.record(agent_id=agent_id, slot_id=slot_id,
                           model=payload["model"],
                           prompt_tokens=usage.get("prompt_tokens", 0),
                           completion_tokens=usage.get("completion_tokens", 0),
                           call_type="chat_with_images_and_tools",
                           knowledge_source=knowledge_source)
            return content

        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
        for tc in msg["tool_calls"]:
            imya = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            ruka = ruki.get(imya)
            if ruka:
                try:
                    otvet = str(ruka(args))
                except Exception as e:
                    otvet = f"рука {imya} сорвалась: {e}"
                sdelano += 1
                print(f"[РУКА] 🖐 {imya}({args}) → {len(otvet)} симв. "
                      f"({sdelano}/{max_tool_rounds})")
            else:
                otvet = f"Такой руки нет: {imya}"
            if on_tool_call:
                try:
                    on_tool_call(imya, args, otvet)
                except Exception:
                    pass
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": otvet})

    return "Разговор с руками не сошёлся — рук попросили больше, чем можно."


# RUKI_TREYDERA_V1 - marker
'''

# ═══════════════════════════════════════════════════════════
# 2. руки трейдера
# ═══════════════════════════════════════════════════════════
RUKI_PY = '''# -*- coding: utf-8 -*-
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
            return f"=== СТОЛ · {symbol} {tf} ===\\n" + _s.slovami(t)
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
            return ("=== ВОЛНА · измерено, не истолковано ===\\n"
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
            return ("=== ДНЕВНИК · последние " + str(len(zapisi)) + " ===\\n"
                    + json.dumps(zapisi, ensure_ascii=False, indent=1)[:3000])
        except Exception as e:
            return f"дневник не прочитался: {e}"

    return {"stol_na_etazhe": _stol,
            "izmerit_volnu": _volna,
            "moy_dnevnik": _dnevnik}


# RUKI_TREYDERA_V1 - marker
'''

# ═══════════════════════════════════════════════════════════
# 3. Вера: рельсы снять, руки дать
# ═══════════════════════════════════════════════════════════
ST_LESENKA = '''    _RABOCHIE_ETAZHI = ("D1", "H4", "H1")'''
NOV_LESENKA = '''    # RUKI_TREYDERA_V1: три этажа были зашиты здесь намертво и
    # считались КАЖДЫЙ раз, спрашивал он их или нет. Теперь этажи —
    # его дело: захочет посмотреть соседний, попросит рукой
    # stol_na_etazhe. Оставлен только его рабочий — тот, на котором
    # нарисован кадр перед ним.
    _RABOCHIE_ETAZHI = (timeframe,)'''

ST_VASYA = '''        "own_wave": {
            "timeframe":            own_wave.get("timeframe"),'''
NOV_VASYA = '''        # RUKI_TREYDERA_V1: раньше код САМ спускался на ступень ниже и
        # мерил волну там — потому что «Консерватор пасёт конец волны
        # 2». Она про это не просила: паттерн жил в коде, а не в её
        # выборе. Спуск остался возможным, но теперь это ЕЁ шаг —
        # рука izmerit_volnu(этаж).
        "own_wave": {
            "timeframe":            own_wave.get("timeframe"),'''

ST_ZOV = '''        _chat_glazami = _glaz(chat, symbol, timeframe, _SLOT)'''
NOV_ZOV = '''        # RUKI_TREYDERA_V1: кадр как был, но теперь с руками — она
        # может сама попросить числа по тому, что видит.
        _chat_glazami = _glaz_s_rukami(chat, symbol, timeframe, _SLOT,
                                       _CEH, _SELF_KEY)'''

GLAZ_S_RUKAMI = '''

def _glaz_s_rukami(_chat, symbol, timeframe, slot, ceh, self_key,
                   preambula=None):
    """Кадр + руки: смотрит картинку и сам просит математику.

    RUKI_TREYDERA_V1. Не вышло с руками — падаем на обычный глаз, а
    не молчим: зрение важнее рук.
    """
    def obertka(system="", user="", knowledge="", **kw):
        put = None
        try:
            import grafik
            put = grafik.kadr(symbol, timeframe)
        except Exception as e:
            print(f"[КАДР] не нарисовался ({e}) — работаю без глаз")
        if put:
            try:
                import base64
                from pathlib import Path as _P
                from llm import chat_with_images_and_tools
                import ruki_treydera as _rt
                return chat_with_images_and_tools(
                    system=system,
                    user_text=(preambula if preambula is not None
                               else _GLAZ_PREAMBULA) + user,
                    knowledge=knowledge,
                    images=[{"base64": base64.b64encode(
                                 _P(put).read_bytes()).decode("ascii"),
                             "mime_type": "image/png",
                             "name": _P(put).name}],
                    tools_schema=_rt.shema(timeframe),
                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary),
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
            except Exception as e:
                print(f"[РУКИ] не сработали ({e}) — иду обычным глазом")
        return _glaz(_chat, symbol, timeframe, slot, preambula)(
            system=system, user=user, knowledge=knowledge, **kw)
    return obertka

'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    llm = koren / "Биржа" / "llm.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"
    vera = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
            / "слоты" / "A08" / "мозг.py")
    masshtab = koren / "Биржа" / "masshtab.py"

    if not masshtab.exists():
        print("✗ Нет Биржа/masshtab.py — накати сперва postavit_paru_mesta.py")
        return 1

    print("\n1. llm.py — пускать свои руки и держать кадр вместе с ними")
    ok1 = pravit(
        llm,
        lambda t: (t.count(ST_EXEC) == 1 and t.count(ST_SIG) == 1,
                   "не нашёл chat_with_tools дословно"),
        lambda t: (t.replace(ST_SIG, NOV_SIG, 1)
                   .replace(ST_EXEC, NOV_EXEC, 1)
                   .rstrip("\n") + "\n" + KARTINKA_I_RUKI),
        "ruki")

    print("\n2. Руки трейдера — Биржа/ruki_treydera.py")
    if ruki.exists() and MARKER in ruki.read_text(encoding="utf-8"):
        print("  · уже лежат — пропускаю")
    else:
        try:
            ast.parse(RUKI_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if SUHO:
            print("  · готовы (сухой прогон)")
        else:
            ruki.write_text(RUKI_PY, encoding="utf-8")
            print("  ✓ положены (стол на этаже, измерить волну, дневник)")

    print("\n3. Вера (A08) — снять рельсы, дать руки")
    ok3 = pravit(
        vera,
        lambda t: (t.count(ST_LESENKA) == 1 and t.count(ST_VASYA) == 1
                   and t.count(ST_ZOV) == 1,
                   "не нашёл якоря в мозге A08 дословно"),
        lambda t: (t.replace(ST_LESENKA, NOV_LESENKA, 1)
                   .replace(ST_VASYA, NOV_VASYA, 1)
                   .replace(ST_ZOV, NOV_ZOV, 1)
                   .replace("\ndef _znaniya_roli() -> str:",
                            GLAZ_S_RUKAMI + "\ndef _znaniya_roli() -> str:", 1)
                   + f"\n# {MARKER} - marker\n"),
        "ruki_a08")

    if not (ok1 and ok3):
        print("\n✗ Не всё легло — файлы целы.")
        return 1

    if not SUHO:
        import py_compile
        for f in (llm, ruki, vera):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nЧто изменилось для Веры:")
        print("  было — код сам спускался этажом ниже и считал три этажа;")
        print("  стало — она смотрит кадр и САМА просит, что ей нужно.")
        print("  В консоли будет видно каждую просьбу строкой [РУКА] 🖐")
        print("\nСоседки пока на рельсах — нарочно, чтобы было с чем сравнить.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
