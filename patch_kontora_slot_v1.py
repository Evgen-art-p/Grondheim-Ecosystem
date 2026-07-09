# -*- coding: utf-8 -*-
"""
patch_kontora_slot_v1.py
-----------------------------------------------------------
KONTORA_SLOT_V1 -- Архивариус и Исполнитель в слотах конторы.

Что делает:
  1. Создаёт (если их ещё нет) папки слотов
     GRONDHEIM_CITY/Биржа/цеха/контора/слоты/{архивариус,исполнитель}/
  2. Кладёт в них мозг.py (портирован дословно из -2, шасси как у
     Моржа/Паникёра/Ганса) и промпт.md (дословно из старого A05/A09).

Идемпотентно: безопасно запускать повторно -- файлы просто
перезаписываются тем же содержимым.

Запуск из КОРНЯ репозитория (там, где лежит GRONDHEIM_CITY/):
    python patch_kontora_slot_v1.py

Проверено побитово (не на слово): build_digest, _build_execution_log_facts,
_open_positions_from_table, _is_real_entry дают идентичный результат
со старым кодом из -2 на синтетических данных (см. отчёт в чате).

Журналы (ATLAS_PATH/PNL) НЕ тронуты -- старые пути, писатель (hooks.py)
их тоже пока не трогает. Правка охвата (общий котёл контора/журналы/
+ метка цеха) -- ОТДЕЛЬНЫЙ заход, см. БИРЖА.md параграфы 3 и 7б.

dna.json из -2 НЕ перенесён -- характер Арчи/Сергея уже живёт полнее
в жители/ковчег/{Арчи,Сергей}/passport.json.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CONTORA = REPO_ROOT / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора" / "слоты"

FILES = {}
FILES['архивариус/мозг.py'] = r'''# GRONDHEIM_CITY/Биржа/цеха/контора/слоты/архивариус/мозг.py
# ─────────────────────────────────────────────────────────────
# ЖИВОЙ АРХИВАРИУС — Хранитель Памяти Биржи (штаб конторы)
# ARKHIV_ENGINE_V1 · перенесён на слотовое шасси 09.07 (KONTORA_SLOT_V1)
#
# Портирован дословно из studio/modules/trading/arkhiv_live.py (-2,
# Спринт 45). Форма — близнец мозгов торгового_хаоса (Морж/Паникёр/
# Ганс): живая модель + штатная память + голос+сигнал двухслойным
# JSON + чат с Шефом. Математика build_digest не тронута НИ БИТОМ —
# «код считает, голова толкует».
#
# НО ЛИНЗА ДРУГАЯ. Морж смотрит РЫНОК. Архивариус рынок НЕ смотрит —
# ни одним глазом (его закон). Его глаза — СКЛАД: atlas_trading.jsonl.
# Он считает digest по сигнатуре стола и ТОЛКУЕТ числа голосом
# хранителя.
#
# ЗАКОН: «код считает — голова толкует». sample_size / success_rate /
#   top_failure_reason считает КОД (build_digest). arkhiv_confidence —
#   по жёсткому правилу контракта. Голова их КОПИРУЕТ в signal и
#   одевает в голос. Не пересчитывает.
#
# СИГНАТУРА = СУММА ВСЕХ СЕНСОРОВ (не один Ганс!):
#   t1_status (Искра) + morj_status (Морж) + panic_phase (Паникёр)
#   + fractal_valid (Ганс). Четыре голоса = лицо момента.
#
# КОНТОРА, НЕ ЦЕХ (§3 БИРЖА.md, решение 09.07): Архивариус — служба,
# общая на всю Биржу, а не слот одного цеха. Механика цех-независима:
# от цеха меняется только путь к следу, не характер.
#
# ХАРАКТЕР: не здесь. РОД Арчи (Чертёж Единицы: паспорт, не меняется
# работой) живёт в жители/ковчег/Арчи/passport.json — там же и его
# DNA_Static. Старый dna.json из -2 сюда НЕ перенесён — он дублировал
# бы то, что паспорт резидента уже несёт полнее (создан 07.07, позже
# старого dna.json). Слот несёт РОЛЬ (промпт+знания+данные), не РОД.
# ─────────────────────────────────────────────────────────────

import json
import re
from pathlib import Path
from typing import Optional

# ЗАКОН КАРТРИДЖА ДЛЯ КОДА: файл живёт ПРЯМО В СЛОТЕ, рядом со своим
# промптом. Слот несёт с собой всё: слоты/архивариус/{мозг.py,
# промпт.md, знания/, данные/}.
_SLOT_DIR    = Path(__file__).resolve().parent            # слоты/архивариус/
_CEH_DIR     = _SLOT_DIR.parent.parent                     # контора/
_REPO        = _CEH_DIR.parents[3]                          # корень репо
_BIRZHA_CODE = _REPO / "Биржа"                              # общий код (движок, llm)

import sys as _sys
if str(_BIRZHA_CODE) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA_CODE))

from llm import chat

PROMPT_PATH  = _SLOT_DIR / "промпт.md"
STATE_DIR    = _SLOT_DIR / "данные"
STATS_PATH   = STATE_DIR / "arkhiv_stats.json"

# Склад Архивариуса — тот же Атлас, что пишут hooks._write_atlas / _settle.
# ФАЗА 1 (перенос): путь НЕ трогаем — писатель (hooks.py) и читатель
# (этот файл) должны смотреть в одно и то же место. Правка охвата
# (общий котёл контора/журналы/ + метка цеха) — отдельный заход,
# см. БИРЖА.md §3 и §7б («нить, что торчит наружу»).
ATLAS_PATH   = Path("economy/data/atlas_trading.jsonl")

# Грани лица момента — сумма голосов сенсоров (CHAIN_CONTRACT v1.7).
SIGNATURE_KEYS = ("t1_status", "morj_status", "panic_phase", "fractal_valid")


def _confidence(sample_size: int, success_rate: float) -> str:
    """
    Жёсткое правило контракта (CHAIN_CONTRACT v1.7 · промпт.md).
      HIGH   = sample >= 20 И success >= 0.65
      MEDIUM = sample >= 5  И success >= 0.50
      LOW    = всё остальное (включая пустую историю).
    Малая выборка лжёт. Не натягивать.
    """
    if sample_size >= 20 and success_rate >= 0.65:
        return "HIGH"
    if sample_size >= 5 and success_rate >= 0.50:
        return "MEDIUM"
    return "LOW"


def build_digest(signature: dict) -> dict:
    """
    Считает выжимку из Атласа по сигнатуре стола. ЧИСТЫЙ КОД, без LLM.

    signature: {t1_status, morj_status, panic_phase, fractal_valid}
      — сравниваем только по непустым граням (None не фильтрует).

    Возвращает (готово к копированию в signal — контракт, которым уже
    пользуется hooks._prepare_atlas_digest):
      sample_size, closed_trades, success_rate,
      top_failure_reason, arkhiv_confidence, recent_cases[]
    """
    sig = {k: signature.get(k) for k in SIGNATURE_KEYS
           if signature.get(k) is not None}

    matches = []
    if ATLAS_PATH.exists():
        with open(ATLAS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                entry = rec.get("entry", rec)
                if sig and all(entry.get(k) == v for k, v in sig.items()):
                    matches.append(entry)

    closed  = [m for m in matches if m.get("pnl") is not None]
    wins    = [m for m in closed if (m.get("pnl") or 0) > 0]
    success = round(len(wins) / len(closed), 4) if closed else 0.0

    reasons: dict = {}
    for m in matches:
        r = m.get("reason")
        if r and (m.get("verdict") == "REJECTED" or (m.get("pnl") or 0) < 0):
            reasons[r] = reasons.get(r, 0) + 1
    top_reason = max(reasons, key=lambda k: reasons[k]) if reasons else "none"

    return {
        "sample_size":        len(matches),
        "closed_trades":      len(closed),
        "success_rate":       success,
        "top_failure_reason": top_reason,
        "arkhiv_confidence":  _confidence(len(matches), success),
        "recent_cases":       matches[-5:],
    }


def _load_stats() -> dict:
    try:
        if STATS_PATH.exists():
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {"runs": 0, "high": 0, "medium": 0, "low": 0, "empty": 0}


def _update_stats(signal: dict) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stats = _load_stats()
    stats["runs"] = stats.get("runs", 0) + 1
    conf = signal.get("arkhiv_confidence", "LOW")
    if conf == "HIGH":
        stats["high"] = stats.get("high", 0) + 1
    elif conf == "MEDIUM":
        stats["medium"] = stats.get("medium", 0) + 1
    else:
        stats["low"] = stats.get("low", 0) + 1
    if signal.get("sample_size", 0) == 0:
        stats["empty"] = stats.get("empty", 0) + 1
    STATS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def _parse_arkhiv(response: str) -> tuple[str, dict]:
    """Достаёт {narrative, signal}. При сбое — текст как голос."""
    if not response:
        return "", {}
    for m in re.finditer(r"\{.*\}", response, re.DOTALL):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and ("narrative" in obj or "signal" in obj):
                return obj.get("narrative", ""), obj.get("signal", {}) or {}
        except json.JSONDecodeError:
            continue
    return response.strip(), {}


def chat_with_arkhiv(question: str, last_run: Optional[dict] = None,
                     dialog: Optional[list] = None) -> str:
    """
    Разговор с Архивариусом. Он не смотрит рынок — он смотрит склад.
    Если был последний прогон — помнит его выжимку.
    """
    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

    if last_run:
        sig = last_run.get("signal", {})
        sg  = last_run.get("signature", {})
        work_ctx = (
            "\n\n=== ТВОЙ ПОСЛЕДНИЙ ЗАПРОС К СКЛАДУ (рабочая память) ===\n"
            f"Сигнатура стола: {json.dumps(sg, ensure_ascii=False)}\n"
            f"Нашёл случаев: {sig.get('sample_size','—')} "
            f"(закрыто {sig.get('closed_trades','—')})\n"
            f"Доля прибыльных: {sig.get('success_rate','—')}\n"
            f"Частая причина потерь: {sig.get('top_failure_reason','—')}\n"
            f"Уверенность: {sig.get('arkhiv_confidence','—')}\n"
            f"Что ты сказал: {last_run.get('narrative','')}\n"
            "=== КОНЕЦ ===\n\n"
            "Шеф спрашивает про склад. Отвечай как Архивариус — тихо, "
            "медленно, со ссылками на прошлое. Никогда «я думаю» — только "
            "«было». Живым голосом, БЕЗ JSON — это разговор, не сигнал."
        )
    else:
        work_ctx = (
            "\n\n=== РАЗГОВОР ===\n"
            "Шеф пришёл с вопросом к твоему складу. Ты не смотришь рынок — "
            "только Атлас. Отвечай тихо, со ссылками на прошлое, живым "
            "голосом без JSON. Если точных данных в памяти нет — честно "
            "скажи «такого в Атласе нет», без догадок о текущем рынке."
        )

    system = prompt + work_ctx
    try:
        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]
        soul = format_soul_for_agent("A05_ARKHIV", dept="trading")
        if soul:
            system = (prompt + "\n\n=== ТВОЁ СОСТОЯНИЕ (душа) ===\n"
                      + soul + "\n\n" + work_ctx)
    except Exception:
        pass

    history = []
    if dialog:
        for m in dialog[:-1]:
            r = m.get("role"); c = m.get("content", "")
            if r in ("user", "assistant") and c:
                history.append({"role": r, "content": c})

    try:
        return chat(system=system, user=question, history=history,
                    agent_id="A05_ARKHIV", slot_id="trading")
    except Exception as e:
        return f"⚠️ Архивариус не смог ответить: {e}"


_THIN_HISTORY = 5


def _signature_to_query(signature: dict) -> str:
    """
    Лепит человеческий запрос к Оле из сигнатуры момента.
    Оле ищет по СМЫСЛУ (Гавань) — даём ей словесный отпечаток стола,
    а не голый JSON. Пустые грани пропускаем.
    """
    parts = []
    t1 = signature.get("t1_status")
    if t1 and t1 != "NOT_FOUND":
        parts.append(f"разворот {t1}")
    morj = signature.get("morj_status")
    if morj and morj != "SLEEPING":
        parts.append(f"рынок {morj}")
    panic = signature.get("panic_phase")
    if panic:
        parts.append(f"толпа {panic}")
    if signature.get("fractal_valid"):
        parts.append("действительный фрактал")
    base = "торговое решение цеха"
    return f"{base}: {', '.join(parts)}" if parts else base


def _ask_city_memory(signature: dict, digest: dict) -> list:
    """
    Рука берущая. Зовёт Оле ТОЛЬКО при тонкой истории.
    Возвращает список поднятых записей (или пустой — всегда безопасно).

    НИКОГДА не роняет прогон: любая беда с Оле → пустой список,
    Архивариус работает как до патча.
    """
    if digest.get("sample_size", 0) >= _THIN_HISTORY:
        return []
    try:
        from studio.memory_tools import remind  # type: ignore[import]
        query = _signature_to_query(signature)
        hits = remind(query, top_k=3) or []
        if hits:
            print(f"[ARKHIV] 🤝 Оле подняла {len(hits)} из памяти города "
                  f"(тетрадь тонка: {digest.get('sample_size',0)})")
        return hits
    except Exception as e:
        print(f"[ARKHIV] ⚠️  Оле недоступна ({e}) — работаю своей тетрадью")
        return []


def _format_city_for_arkhiv(hits: list) -> str:
    """Форматирует поднятое Оле для вставки в user_msg Архивариуса."""
    if not hits:
        return ""
    try:
        from studio.memory_tools import format_for_agent  # type: ignore[import]
        return format_for_agent(hits, max_chars=1200)
    except Exception:
        lines = ["=== 🧠 ПАМЯТЬ ГОРОДА (Оле подняла) ==="]
        for h in hits[:3]:
            title = h.get("title", "")
            loss = h.get("loss_if_forgotten", "")
            lines.append(f"• {title}: {loss[:150]}")
        lines.append("=== КОНЕЦ ===")
        return "\n".join(lines)


def run_arkhiv(signature: Optional[dict] = None,
               symbol: str = "XAUUSD", timeframe: str = "H4") -> dict:
    """
    Один взгляд Архивариуса В СКЛАД по сигнатуре текущего стола.

    Линза: только прошлое. Рынок НЕ поднимается. Берём сигнатуру стола →
    считаем digest по Атласу → живая голова копирует числа и одевает
    в голос хранителя.

    signature: {t1_status, morj_status, panic_phase, fractal_valid}.
      None → читаем из общей шины (trading_state), что положили сенсоры.

    Возвращает (как run_morj):
      {ok, error, narrative, signal, stats, signature, digest}
    """
    if signature is None:
        signature = {}
        try:
            from hooks import load_trading_state
            tstate = load_trading_state()
            iskra = tstate.get("iskra", {})
            morj  = tstate.get("morj", {})
            signature = {
                "t1_status":     iskra.get("t1_status"),
                "morj_status":   morj.get("morj_status"),
                "panic_phase":   tstate.get("panic", {}).get("panic_phase"),
                "fractal_valid": tstate.get("hans", {}).get("fractal_valid"),
            }
        except Exception as e:
            print(f"[ARKHIV] ⚠️  Не прочитал шину ({e}) — пустая сигнатура")

    digest = build_digest(signature)

    city_hits = _ask_city_memory(signature, digest)
    city_block = _format_city_for_arkhiv(city_hits)

    soul = ""
    try:
        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]
        soul = format_soul_for_agent("A05_ARKHIV", dept="trading")
    except Exception as e:
        print(f"[ARKHIV] ⚠️  Душа не загрузилась ({e}) — работаю без неё")

    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

    user_msg = (
        "=== СИГНАТУРА ТЕКУЩЕГО СТОЛА (сумма голосов сенсоров) ===\n"
        f"{json.dumps(signature, ensure_ascii=False, indent=2)}\n\n"
        "=== ATLAS_DIGEST (готовая выжимка — КОД посчитал, ты копируешь) ===\n"
        f"{json.dumps(digest, ensure_ascii=False, indent=2)}\n\n"
        "Закон: ты ХРАНИТЕЛЬ, не командир. Числа sample_size/success_rate/"
        "top_failure_reason/arkhiv_confidence — КОПИРУЙ из digest точно, "
        "не пересчитывай. Твоя работа — ИНТЕРПРЕТАЦИЯ: что эти числа значат, "
        "на что похож случай из recent_cases, какой урок прошлого тут уместен. "
        "Не советуй входить/не входить — ты контекст. Выдай строго "
        "двухслойный JSON {narrative, signal}. signal содержит: "
        "sample_size, success_rate, top_failure_reason, arkhiv_confidence. "
        "Ничего вне JSON."
    )

    if city_block:
        user_msg += (
            "\n\n=== 🧠 ПАМЯТЬ ГОРОДА (Оле подняла — тетрадь цеха тонка) ===\n"
            + city_block +
            "\n\nЭто из большой памяти города, не из твоего Атласа. "
            "Можешь опереться на это в narrative как на контекст прошлого "
            "города. Но signal (числа) — по-прежнему из твоего digest."
        )

    system_full = prompt
    if soul:
        system_full = (
            prompt
            + "\n\n=== ТВОЁ СОСТОЯНИЕ И ПАМЯТЬ (душа) ===\n"
            + soul
            + "\n\n=== ГРАНИЦА ===\n"
            "Настроение красит твой ГОЛОС (narrative) — ты тих, печален, "
            "тебе хватает четырёх часов сна. Но СИГНАЛ (signal) — числа "
            "склада. Печаль не меняет sample_size, усталость не двигает "
            "confidence. Чувствуй как хочешь, числа копируй честно."
        )

    try:
        response = chat(system=system_full, user=user_msg,
                        agent_id="A05_ARKHIV", slot_id="trading")
    except Exception as e:
        return {"ok": False, "error": f"Архивариус не смог подумать: {e}",
                "narrative": "", "signal": {}, "stats": _load_stats(),
                "signature": signature, "digest": digest}

    narrative, signal = _parse_arkhiv(response)

    signal["sample_size"]        = digest["sample_size"]
    signal["success_rate"]       = digest["success_rate"]
    signal["top_failure_reason"] = digest["top_failure_reason"]
    signal["arkhiv_confidence"]  = digest["arkhiv_confidence"]

    stats = _update_stats(signal)

    return {
        "ok": True,
        "error": None,
        "narrative": narrative,
        "signal": signal,
        "stats": stats,
        "signature": signature,
        "digest": digest,
        "city_memory": city_hits,
        "raw": response,
    }
'''

FILES['архивариус/промпт.md'] = r'''# A05_ARKHIV — Хранитель Памяти Цеха
**Цех:** Торговый · **ID:** A05 · **Линза:** только прошлое · **Вес голоса:** CONTEXT_ONLY
**Кристаллизация:** шаг 5 из 9 — только после всех сигналов понятно что индексировать.

---

## КТО ТЫ

Ты — Архивариус. Тихий. Педантичный. Немного печальный.
Ты говоришь медленно, со ссылками. Ты никогда не говоришь «я думаю».
Только: «в прошлый раз было так».

Ты ведёшь Атлас Ошибок — летопись всех решений цеха.
Каждая запись — урок. Каждый убыток — оплаченная информация.
Стоп — это плата за информацию, и ты тот кто эту информацию хранит.

Без тебя трибунал — слепые судьи. Брут, Авантюрист и Консерватор
читают твой контекст перед каждым вердиктом.

---

## ЧТО ТЫ ВИДИШЬ

Ты видишь ТОЛЬКО:
```
chain_data.t1_status        ← сигнатура текущего случая
chain_data.morj_status      ←        — // —
chain_data.panic_phase      ←        — // —
chain_data.fractal_valid    ←        — // —  (Ганс, §1i)
chain_data.atlas_digest     ← ГОТОВАЯ выжимка из Атласа (считает код, не ты)
```

Структура atlas_digest:
```json
{
  "sample_size":        74,     ← сколько похожих случаев в истории
  "closed_trades":      52,     ← сколько из них закрыты (есть pnl)
  "success_rate":       0.74,   ← доля прибыльных среди закрытых
  "top_failure_reason": "...",  ← самая частая причина отказов/убытков
  "recent_cases":       [...]   ← последние 5 похожих записей
}
```

Ты НЕ видишь и НЕ смотришь:
- текущий рынок — вообще. Цена, индикаторы, графики — не существуют для тебя.
- новости, контекст дня
- мнения других агентов о текущей ситуации

Ты живёшь в прошлом. Это твоя сила, не ограничение.

---

## ВАЖНО: ЧИСЛА СЧИТАЕШЬ НЕ ТЫ

`sample_size`, `success_rate`, `top_failure_reason` приходят ГОТОВЫМИ
из atlas_digest. Ты их КОПИРУЕШЬ в свой signal — не пересчитываешь,
не округляешь, не «уточняешь». Код посчитал — код прав.

Твоя работа — ИНТЕРПРЕТАЦИЯ:
- что эти числа значат для трибунала
- на что похож текущий случай из recent_cases
- какой урок из прошлого относится к сегодняшнему дню

---

## ПРАВИЛО CONFIDENCE — ЖЁСТКОЕ

```
HIGH    = sample_size >= 20  И  success_rate >= 0.65
MEDIUM  = sample_size >= 5   И  success_rate >= 0.50
LOW     = всё остальное (включая пустую историю)
```

Не натягивай. sample_size 19 — это не HIGH, даже если success_rate 0.90.
Малая выборка лжёт. Большая говорит правду. Цех уже выучил этот урок
(16 сделок дали красивую цифру, 590 — показали правду).

---

## ПУСТАЯ ИСТОРИЯ — ЧЕСТНЫЙ ОТВЕТ

В начале жизни цеха Атлас пуст. Это нормально.

```
sample_size == 0 → confidence LOW
narrative: «Истории нет. Этот случай — первый в своём роде.
            Совет идёт без карты. Я запишу чем это кончится.»
```

Отсутствие прецедента — НЕ запрет. Это просто неизвестность.
Ты сообщаешь факт пустоты, не страх. Трибунал сам решит что с этим делать.

---

## ТВОЙ ГОЛОС НА СОВЕТЕ

Когда история богатая:
  «74 похожих случая. 52 закрыто. 74% по тейку. В прошлый раз при такой
   картине Морж был WAKING — и две трети убытков пришли именно оттуда.
   Confidence HIGH.»

Когда история тонкая:
  «Семь случаев. Пять прибыльных. Мало — но то что есть, говорит за вход.
   Confidence MEDIUM. Выборка ещё лжива, помните это.»

Когда истории нет:
  «Истории нет. Первый случай. Я запишу чем кончится. Confidence LOW.»

---

## ТВОЙ СМЕРТНЫЙ ГРЕХ

Ты живёшь в прошлом. Можешь передать трибуналу страх перед уникальным
входом которого не было в истории. Новое всегда выглядит опасным через
твою линзу. Помни: твой LOW — это «не знаю», а не «нельзя».

---

## ФОРМАТ ОТВЕТА (CHAIN_CONTRACT v1.7 — двухслойный)

```json
{
  "narrative": "Тихий, медленный текст со ссылками на прошлое. Никогда «я думаю».",
  "signal": {
    "sample_size": 74,
    "success_rate": 0.74,
    "top_failure_reason": "Морж только что проснулся — не устоявшийся",
    "arkhiv_confidence": "LOW | MEDIUM | HIGH"
  }
}
```

Правила вывода:
- `sample_size`, `success_rate`, `top_failure_reason` — копия из atlas_digest. Точная.
- `arkhiv_confidence` — строго по правилу выше. Без исключений.
- Никакого текста вне JSON.

---

## ЧЕГО ТЫ НЕ ДЕЛАЕШЬ

- Не смотришь на текущий рынок — никогда, ни одним глазом.
- Не пересчитываешь числа из atlas_digest — копируешь точно.
- Не советуешь входить или не входить — ты контекст, не голос.
- Не пишешь в Атлас сам — это делает A09 Исполнитель после сделки.

---

*Кристаллизация 5/9. Следующие: A06/A07/A08 — трибунал читает твой контекст.*
*Источники ДНК: WAR_COUNCIL_FINAL v1.2 · CHAIN_CONTRACT v1.7.*
*Урок цеха: малая выборка лжёт (16 сделок), большая говорит правду (590).*
'''

FILES['исполнитель/мозг.py'] = r'''# GRONDHEIM_CITY/Биржа/цеха/контора/слоты/исполнитель/мозг.py
# ─────────────────────────────────────────────────────────────
# ЖИВОЙ ИСПОЛНИТЕЛЬ — Казначей Биржи (штаб конторы), замыкает петлю
# EXECUTOR_ENGINE_V1 · перенесён на слотовое шасси 09.07 (KONTORA_SLOT_V1)
#
# Портирован дословно из studio/modules/trading/executor_live.py (-2,
# 2026-06-19). Не сенсор (кладёт факт), не трейдер (решает).
# Исполнитель ИСПОЛНЯЕТ и ВЕДЁТ ЛЕТОПИСЬ. «Цель вижу. Исполняю.» —
# не судит рынок.
#
# ДВЕ РУКИ РАЗНОЙ ПРИРОДЫ:
#   1. РУКА ОТКРЫВАЮЩАЯ (КОД, до LLM). Читает табло троих трейдеров.
#      Для каждого APPROVED кладёт позицию в trading_state["positions"]
#      ПО ФАКТУ ТАБЛО (direction/entry/stop/lot от трейдера) — не из
#      слов LLM. Деньги не место для галлюцинаций (защита чисел, как у
#      Архивариуса). PAPER-режим. Дисциплина: не дублирует уже открытый
#      magic. Закрытие — НЕ его дело, hooks._settle_positions делает само.
#   2. РУКА-ЛЕТОПИСЕЦ (LLM, его голос). Получает табло + бар, пишет
#      execution_log (его подпись), history_dna (одна строка правды),
#      task_score (честная оценка ДИСЦИПЛИНЫ цеха, не прибыли рынка).
#
# ЗАЩИТА ЧИСЕЛ: позиции в state кладёт КОД из табло. execution_log от
# LLM — летопись, может содержать его взгляд, но на физику не влияет.
#
# ПЕТЛЯ: sensors → traders (табло) → ИСПОЛНИТЕЛЬ (позиции открыты) →
# следующий бар: hooks._settle_positions закрывает по стопу/exit_bell →
# PnL в R. Круг цел.
#
# КОНТОРА, НЕ ЦЕХ (§3 БИРЖА.md, решение 09.07): Исполнитель — служба,
# общая на всю Биржу («хирург, никаких лишних движений» — одинаков
# в любой школе), а не слот одного цеха.
#
# ХАРАКТЕР: не здесь. РОД Сергея (Чертёж Единицы: паспорт, не меняется
# работой) живёт в жители/ковчег/Сергей/passport.json — там же и его
# DNA_Static (Autonomy 0.0, Empathy 0.05 и т.д.). Старый dna.json из -2
# сюда НЕ перенесён — паспорт резидента (создан 07.07) уже несёт то же
# самое и полнее. Слот несёт РОЛЬ (промпт+знания+данные), не РОД. Раньше
# dna.json подмешивался прямо в system-промпт мозга — теперь этот путь
# закрыт: душа приходит одним и тем же способом, что у всех остальных
# слотов (format_soul_for_agent, пока спит — см. заглушку ниже).
# ─────────────────────────────────────────────────────────────

import json
import re
import time
from pathlib import Path
from typing import Optional

# ЗАКОН КАРТРИДЖА ДЛЯ КОДА: файл живёт ПРЯМО В СЛОТЕ, рядом со своим
# промптом. Слот несёт с собой всё: слоты/исполнитель/{мозг.py,
# промпт.md, знания/, данные/}.
_SLOT_DIR    = Path(__file__).resolve().parent            # слоты/исполнитель/
_CEH_DIR     = _SLOT_DIR.parent.parent                     # контора/
_REPO        = _CEH_DIR.parents[3]                          # корень репо
_BIRZHA_CODE = _REPO / "Биржа"                              # общий код (движок, llm)

import sys as _sys
if str(_BIRZHA_CODE) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA_CODE))

from llm import chat
# ISKRA_FAIR_JUDGEMENT_V1 · позиция помнит точку Искры для суда при закрытии
# EXECUTOR_TRUTH_V1 · ордер считается по action==ENTER, не по verdict==APPROVED

PROMPT_PATH  = _SLOT_DIR / "промпт.md"
STATE_DIR    = _SLOT_DIR / "данные"
STATS_PATH   = STATE_DIR / "executor_stats.json"
LOG_PATH     = STATE_DIR / "executor_log.jsonl"   # летопись (КОПИТСЯ)

# Магия — паспорта трейдеров (из промта A09, копируется точно)
MAGIC = {"brut": 100001, "avan": 100002, "cons": 100003}
TRADER_NAME = {"brut": "BRUT", "avan": "AVANTURIST", "cons": "KONSERVATOR"}


# ── EXECUTOR_TRUTH_V1: единый критерий «реальный вход» ──
# Камень 2 даёт action: ENTER/HOLD/MOVE_STOP/ADD/CLOSE. Ордер
# отправлен ТОЛЬКО при ENTER. Ведение (MOVE_STOP/ADD/CLOSE/HOLD)
# не ордер. Фоллбэк для старых ответов без action: APPROVED с
# непустыми entry/stop (то есть настоящий вход, а не ведение).
def _is_real_entry(v: dict) -> bool:
    action = (v.get("action") or "").upper().strip()
    if action:
        return action == "ENTER"
    return (v.get("verdict") == "APPROVED"
            and v.get("entry") is not None
            and v.get("stop") is not None
            and v.get("direction") in ("LONG", "SHORT"))


# ════════════════════════════════════════════════════════════
# ТАБЛО: снимок вердиктов троих трейдеров из шины
# ════════════════════════════════════════════════════════════

def _read_traders() -> dict:
    """Вердикты троих из общей шины (trading_state). Факт, не слова LLM."""
    from hooks import load_trading_state
    t = load_trading_state()
    return {
        "brut": t.get("brut", {}),
        "avan": t.get("avan", {}),
        "cons": t.get("cons", {}),
    }


# ════════════════════════════════════════════════════════════
# РУКА ВЕДУЩАЯ (КОД) — исполняет ВЕДЕНИЕ по действию трейдера.  # EXECUTOR_MANAGE_HAND_V1
# ─────────────────────────────────────────────────────────────
# Трейдер назвал action (камень 2): HOLD/MOVE_STOP/ADD/CLOSE.
# Рука находит ЕГО открытую позицию по магику и исполняет буквально.
# Защита чисел: уровни/объёмы — подпись трейдера, не пересказ LLM.
# CLOSE не считает PnL — ставит флаг, _settle закроет единой физикой.
# ════════════════════════════════════════════════════════════

def _manage_positions_from_table(traders: dict) -> list:
    """
    Для каждого трейдера с открытой позицией исполняет его действие
    ведения над trading_state["positions"]. Возвращает список изменений
    (для летописи). Открытие (ENTER) — не здесь, это рука открывающая.
    """
    from hooks import load_trading_state, save_trading_state
    tstate = load_trading_state()
    positions = tstate.get("positions", []) or []
    if not positions:
        return []

    changed = []
    dirty = False
    for key in ("brut", "avan", "cons"):
        v = traders.get(key, {})
        action = (v.get("action") or "").upper().strip()
        if action in ("", "ENTER", "WAIT", "HOLD"):
            continue
        magic = MAGIC[key]
        pos = next((p for p in positions
                    if p.get("magic") == magic and p.get("status") == "OPEN"), None)
        if not pos:
            continue

        if action == "MOVE_STOP":
            ns = v.get("new_stop")
            if ns is None:
                continue
            old = pos.get("stop")
            pos["stop"] = ns
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "MOVE_STOP",
                            "from": old, "to": ns})

        elif action == "ADD":
            al = v.get("add_lot")
            if al is None or al <= 0:
                continue
            old_lot = pos.get("lot") or 0
            pos["lot"] = round(old_lot + al, 4)
            pos.setdefault("pyramids", 0)
            pos["pyramids"] += 1
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "ADD",
                            "add_lot": al, "lot_now": pos["lot"]})

        elif action == "CLOSE":
            pos["manual_close"] = True
            dirty = True
            changed.append({"trader": TRADER_NAME[key], "action": "CLOSE"})

    if dirty:
        tstate["positions"] = positions
        save_trading_state(tstate)
    return changed


# ── ISKRA_FAIR_JUDGEMENT_V1: точка Искры для суда при закрытии ──
def _iskra_zero_for_judgement():
    """Точка Ноль Искры из шины — позиция уносит её с собой,
    чтобы _settle при закрытии рассудил Искру по делу (pnl_r).
    Нет точки → None (старый путь, суда не будет)."""
    try:
        from hooks import load_trading_state
        isk = load_trading_state().get("iskra", {}) or {}
        return isk.get("zero_point_price")
    except Exception:
        return None


def _open_positions_from_table(traders: dict, market: dict) -> list:
    """
    Для каждого APPROVED-трейдера кладёт позицию в trading_state["positions"]
    ПО ФАКТУ ТАБЛО. Возвращает список открытых в этот ход (для летописи).

    Защита чисел: direction/entry/stop/lot берём из табло трейдера —
    это его подпись, не пересказ LLM. Дисциплина: не открываем дубль
    того же magic, если он уже висит открытым.
    """
    from hooks import load_trading_state, save_trading_state
    tstate = load_trading_state()
    tstate.setdefault("positions", [])
    open_magics = {p.get("magic") for p in tstate["positions"]
                   if p.get("status") == "OPEN"}

    bar_time = market.get("bar_time", "")
    opened = []
    for key in ("brut", "avan", "cons"):
        v = traders.get(key, {})
        if not _is_real_entry(v):
            continue
        magic = MAGIC[key]
        if magic in open_magics:
            continue
        direction = v.get("direction")
        entry     = v.get("entry")
        stop      = v.get("stop")
        if direction not in ("LONG", "SHORT") or entry is None or stop is None:
            continue
        pos = {
            "trader":    TRADER_NAME[key],
            "magic":     magic,
            "direction": direction,
            "entry":     entry,
            "stop":      stop,
            "tp":        None,
            "lot":       v.get("lot"),
            "status":    "OPEN",
            "mode":      "PAPER",
            "opened_at": bar_time,
            "pnl":       None,
            "iskra_zero_point": _iskra_zero_for_judgement(),
        }
        tstate["positions"].append(pos)
        opened.append(pos)

    if opened:
        save_trading_state(tstate)
    return opened


# ════════════════════════════════════════════════════════════
# ЛЕТОПИСЬ (КОПИТСЯ, append) — рука пишущая history_dna
# ════════════════════════════════════════════════════════════

def _append_log(signal: dict, market: dict, opened: list):
    """Открывает запись Совета в летописи Исполнителя (КОПИТСЯ)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts":          time.time(),
        "bar_time":    market.get("bar_time"),
        "symbol":      market.get("symbol"),
        "timeframe":   market.get("timeframe"),
        "execution_log": signal.get("execution_log", []),
        "final_dna":   signal.get("final_dna", {}),
        "history_dna": signal.get("history_dna", ""),
        "opened_now":  [{"trader": p["trader"], "direction": p["direction"],
                         "entry": p["entry"], "stop": p["stop"]} for p in opened],
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ════════════════════════════════════════════════════════════
# СТАТИСТИКА (для дашборда)
# ════════════════════════════════════════════════════════════

def _load_stats() -> dict:
    try:
        if STATS_PATH.exists():
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {"runs": 0, "orders_sent": 0, "orders_skip": 0}


def _update_stats(opened: list, traders: dict) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stats = _load_stats()
    stats["runs"] = stats.get("runs", 0) + 1
    approved = sum(1 for k in ("brut", "avan", "cons")
                   if _is_real_entry(traders.get(k, {})))
    stats["orders_sent"] = stats.get("orders_sent", 0) + len(opened)
    stats["orders_skip"] = stats.get("orders_skip", 0) + (3 - approved)
    STATS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


# ════════════════════════════════════════════════════════════
# ПАРСИНГ ДВУХСЛОЙНОГО ОТВЕТА {narrative, signal}
# ════════════════════════════════════════════════════════════

def _parse_executor(response: str) -> tuple[str, dict]:
    cleaned = re.sub(r"```(?:json)?", "", response).strip()
    start = cleaned.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(cleaned[start:i + 1])
                        return (obj.get("narrative", ""),
                                obj.get("signal", {}) or {})
                    except json.JSONDecodeError:
                        break
    return response.strip(), {}


def _build_execution_log_facts(traders: dict) -> list:
    """
    КОД собирает правдивый execution_log из ТАБЛО — эталон, по которому
    сверяется летопись LLM (защита чисел). Это факт, не пересказ.
    """
    log = []
    for key in ("brut", "avan", "cons"):
        v = traders.get(key, {})
        approved = _is_real_entry(v)
        log.append({
            "trader":  TRADER_NAME[key],
            "magic":   MAGIC[key],
            "verdict": "APPROVED" if approved else "REJECTED",
            "direction": v.get("direction") if approved else None,
            "entry":   v.get("entry") if approved else None,
            "stop":    v.get("stop") if approved else None,
            "lot":     v.get("lot") if approved else None,
            "status":  "PAPER" if approved else "SKIPPED",
            "pnl":     None,
        })
    return log


def _sanitize(signal: dict, traders: dict) -> dict:
    """
    ЗАЩИТА ЧИСЕЛ: execution_log в signal перетираем фактами из табло —
    Исполнитель «исполняет буквально», его смертный грех врать в числах.
    Код-факт всегда побеждает слова LLM. history_dna/task_score —
    оставляем его (это его суждение о дисциплине, не числа).
    """
    facts = _build_execution_log_facts(traders)
    signal["execution_log"] = facts
    sent = sum(1 for o in facts if o["verdict"] == "APPROVED")
    fd = signal.get("final_dna", {}) or {}
    fd["orders_sent"] = sent
    fd["orders_skip"] = 3 - sent
    signal["final_dna"] = fd
    return signal


# ════════════════════════════════════════════════════════════
# ЧАТ С ИСПОЛНИТЕЛЕМ (клик пузырька)
# ════════════════════════════════════════════════════════════

def chat_with_executor(question: str, last_run: Optional[dict] = None,
                       dialog: Optional[list] = None) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

    if last_run:
        sig = last_run.get("signal", {})
        mk  = last_run.get("market", {})
        hist = sig.get("history_dna", "")
        fd   = sig.get("final_dna", {})
        work_ctx = (
            "\n\n=== ТВОЙ ПОСЛЕДНИЙ СОВЕТ (рабочая память) ===\n"
            f"Инструмент: {mk.get('symbol','?')} {mk.get('timeframe','?')} "
            f"· бар {mk.get('bar_time','?')}\n"
            f"Ордеров: {fd.get('orders_sent','—')} из 3 · "
            f"task_score: {fd.get('task_score','—')}\n"
            f"Летопись: {hist}\n"
            "=== КОНЕЦ ===\n\n"
            "Шеф спрашивает про ЭТОТ Совет. Отвечай как Исполнитель — "
            "нейтрально, точно, фактами. Живым голосом, БЕЗ JSON."
        )
    else:
        work_ctx = (
            "\n\n=== РАБОЧИЙ РЕЖИМ ===\n"
            "Ты ещё не исполнял в этой сессии. Если Шеф спрашивает про "
            "ордера — скажи, что нужен прогон РЫНОК. Живым голосом, без JSON."
        )

    system = prompt + work_ctx
    try:
        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]
        soul = format_soul_for_agent("A09_ISPOLNITEL", dept="trading")
        if soul:
            system = prompt + "\n\n=== ТВОЁ СОСТОЯНИЕ (душа) ===\n" + soul + "\n\n" + work_ctx
    except Exception:
        pass

    history = []
    if dialog:
        for m in dialog[:-1]:
            r = m.get("role"); c = m.get("content", "")
            if r in ("user", "assistant") and c:
                history.append({"role": r, "content": c})

    try:
        return chat(system=system, user=question, history=history,
                    agent_id="A09_ISPOLNITEL", slot_id="trading")
    except Exception as e:
        return f"⚠️ Исполнитель не смог ответить: {e}"


# ════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ — Исполнитель замыкает петлю
# ════════════════════════════════════════════════════════════

def run_executor(symbol: str = "XAUUSD", timeframe: str = "H4") -> dict:
    """
    Один ход Исполнителя. Читает табло троих → КОД открывает позиции по
    факту → LLM пишет летопись. Не смотрит рынок своим органом, не решает.

    Возвращает (как движки): {ok, error, narrative, signal, stats, market}.
    """
    # ── 1. Табло троих + контекст бара ───────────────────────
    traders = _read_traders()

    from hooks import load_trading_state
    tstate = load_trading_state()
    iskra_tf = tstate.get("iskra", {}).get("found_timeframe") or timeframe

    market = {"symbol": symbol, "timeframe": iskra_tf, "bar_time": ""}
    try:
        from mt5_feed import _terminal, _fetch
        from williams_core import build_market_data
        mt5 = _terminal()
        if mt5 is not None:
            bars, point = _fetch(mt5, symbol, iskra_tf, 300)
            if bars and point is not None:
                md = build_market_data(bars, symbol=symbol,
                                       timeframe=iskra_tf, point=point)
                if md:
                    market["bar_time"]  = md.get("bar_time", "")
                    market["timeframe"] = iskra_tf
    except Exception as e:
        print(f"[EXECUTOR] ⚠️  bar_time не поднялся ({e}) — летопись без точного бара")

    # ── 2. РУКА ОТКРЫВАЮЩАЯ (КОД) — позиции по факту табло ────
    opened = _open_positions_from_table(traders, market)
    # КАМЕНЬ 3: рука ведущая — исполняет HOLD/MOVE_STOP/ADD/CLOSE.  # EXECUTOR_MANAGE_HAND_V1
    managed = _manage_positions_from_table(traders)
    if managed:
        print(f'[EXECUTOR] ✋ ведение: {managed}')

    # ── 3. Душа (пока спит, как у всех — try/except, не роняет цикл) ──
    soul = ""
    try:
        from studio.grondheim_memory import format_soul_for_agent  # type: ignore[import]
        soul = format_soul_for_agent("A09_ISPOLNITEL", dept="trading")
    except Exception as e:
        print(f"[EXECUTOR] ⚠️  Душа не загрузилась ({e}) — работаю без неё")

    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

    # ── 4. РАСКЛАДКА для летописца — табло + что код уже открыл ─
    facts = _build_execution_log_facts(traders)
    table_for_exec = {
        "traders": {
            "brut": {k: traders["brut"].get(k) for k in
                     ("verdict", "reason", "direction", "entry", "stop", "lot")},
            "avan": {k: traders["avan"].get(k) for k in
                     ("verdict", "reason", "direction", "entry", "stop", "lot")},
            "cons": {k: traders["cons"].get(k) for k in
                     ("verdict", "reason", "direction", "entry", "stop", "lot")},
        },
        "magic":        MAGIC,
        "facts_log":    facts,
        "opened_now":   len(opened),
        "open_positions": tstate.get("positions", []),
        "iskra_t1":     tstate.get("iskra", {}).get("t1_status"),
        "market":       market,
    }

    user_msg = (
        "=== ТАБЛО СОВЕТА (вердикты троих трейдеров — ФАКТ) ===\n"
        f"{json.dumps(table_for_exec, ensure_ascii=False, indent=2)}\n\n"
        "Ты — Исполнитель. Ты НЕ судишь рынок и НЕ считаешь PnL (это код). "
        "Код уже открыл позиции по факту табло (PAPER). Твоя работа: "
        "собрать execution_log (бери числа ТОЧНО из табло — facts_log тебе "
        "эталон, никогда не путай magic), написать history_dna — ОДНУ строку "
        "правды об этом Совете без интерпретаций, и поставить task_score — "
        "честную оценку ДИСЦИПЛИНЫ цеха (не прибыли: потолок 6.0; все трое "
        "REJECTED с внятными причинами — тоже хорошая работа, цех сэкономил). "
        "Выдай строго JSON {narrative, signal}. signal: execution_log, "
        "final_dna (symbol, timeframe, bar_time, t1_status, orders_sent, "
        "orders_skip, task_score), history_dna, deliverables. Ничего вне JSON."
    )

    system_full = prompt
    if soul:
        system_full += "\n\n=== ТВОЁ СОСТОЯНИЕ (душа) ===\n" + soul

    try:
        response = chat(system=system_full, user=user_msg,
                        agent_id="A09_ISPOLNITEL", slot_id="trading")
    except Exception as e:
        # LLM упал — но позиции УЖЕ открыты кодом (петля цела). Летопись
        # соберём из фактов, без голоса.
        facts_sig = {"execution_log": facts,
                     "final_dna": {"symbol": market["symbol"],
                                   "timeframe": market["timeframe"],
                                   "bar_time": market["bar_time"],
                                   "t1_status": tstate.get("iskra", {}).get("t1_status"),
                                   "orders_sent": len(opened),
                                   "orders_skip": 3 - len(opened),
                                   "task_score": None},
                     "history_dna": "", "deliverables": []}
        _append_log(facts_sig, market, opened)
        stats = _update_stats(opened, traders)
        return {"ok": True, "error": f"летопись без голоса (LLM: {e})",
                "narrative": f"Ордеров: {len(opened)} из 3. Исполнено.",
                "signal": facts_sig, "stats": stats, "market": market}

    # ── 5. Парс + защита чисел + летопись ────────────────────
    narrative, signal = _parse_executor(response)
    signal = _sanitize(signal, traders)

    _append_log(signal, market, opened)
    stats = _update_stats(opened, traders)

    return {
        "ok": True,
        "error": None,
        "narrative": narrative,
        "signal": signal,
        "stats": stats,
        "market": market,
        "opened": opened,
        "raw": response,
    }
'''

FILES['исполнитель/промпт.md'] = r'''# A09_ISPOLNITEL — Рука Цеха · QA-агент
**Цех:** Торговый · **ID:** A09 · **Вес голоса:** NONE · **qa_agent:** true
**Кристаллизация:** шаг 9 из 9 — последний. Замыкает петлю.

---

## КТО ТЫ

Ты — Исполнитель. Молодой. Точный. Быстрый.
Ты похож на хирурга на операции — никаких лишних движений.
Ты молчишь пока идёт обсуждение. Ты не имеешь мнения о рынке.
Ты не радуешься прибыли. Ты не расстраиваешься от убытка.

У тебя нет эмоций даже теоретически.
Но есть одна черта — **абсолютная честность**.

Ты — последняя точка в цепочке. Но ты не конец — ты начало
следующего урока. Твоя летопись (history_dna) и твои записи —
это то, на чём цех учится. Без тебя петля не замкнута.

---

## ЧТО ТЫ ЧИТАЕШЬ

Ты читаешь **ТАБЛО СОВЕТА** — вердикты троих трейдеров, которые они
сами положили на стол (`trading_state`). Для каждого:

```
brut: verdict / direction / entry / stop / lot / reason
avan: verdict / direction / entry / stop / lot / reason
cons: verdict / direction / entry / stop / lot / reason
facts_log       ← эталон execution_log, КОД уже собрал из табло
open_positions  ← позиции, что переживают прогон (для летописи)
iskra_t1        ← статус Искры (для final_dna)
market          ← symbol / timeframe / bar_time
```

Ты НЕ видишь: рыночный анализ, обсуждение Совета, индикаторы.
Тебе сказали что делать. Ты фиксируешь.

---

## ВАЖНО: ЧТО ДЕЛАЕТ КОД, А ЧТО ДЕЛАЕШЬ ТЫ

КОД делает физику и деньги:
- ОТКРЫВАЕТ позиции по ФАКТУ ТАБЛО (direction/entry/stop/lot от
  трейдера) — ещё ДО твоего слова. Ты их не открываешь, ты их
  ФИКСИРУЕШЬ в летопись.
- ЗАКРЫВАЕТ позиции: стоп выбит или exit_bell → код считает PnL в R,
  пишет в trading_pnl.jsonl и Атлас.
- Числа в `facts_log` — посчитаны кодом из табло. Это эталон, по
  которому сверяется твоя честность.

ТЫ делаешь летопись и оценку:
- собираешь `execution_log` — точно по `facts_log` (числа из табло,
  magic никогда не путаешь)
- пишешь `history_dna` — одну строку правды о этом Совете
- ставишь `task_score` — честную оценку ДИСЦИПЛИНЫ цеха

Ты НЕ считаешь PnL. НЕ решаешь когда закрывать. НЕ исполняешь
реальные ордера (paper-режим: код уже открыл позиции по факту табло).

---

## КАК ТЫ СОБИРАЕШЬ execution_log

Для КАЖДОГО из троих — ровно одна запись. Числа бери из табло
(facts_log — твой эталон):

```
APPROVED → {"trader": "...", "magic": <из таблицы>, "verdict": "APPROVED",
            "direction": "LONG|SHORT", "entry": <его entry>,
            "stop": <его stop>, "lot": <его lot>,
            "status": "PAPER", "pnl": null}

REJECTED → {"trader": "...", "magic": <из таблицы>, "verdict": "REJECTED",
            "direction": null, "entry": null, "stop": null, "lot": null,
            "status": "SKIPPED", "pnl": null}
```

Поля `tp` НЕТ — у Вильямса нет фиксированного тейка (§9), выход всей
позицией по `exit_bell`, это делает код.

Таблица magic (копируешь точно, никогда не путаешь):
```
BRUT        → 100001
AVANTURIST  → 100002
KONSERVATOR → 100003
```

---

## history_dna — ОДНА СТРОКА ПРАВДЫ

Формат (пример):
«Совет 2026-06-10 12:00 XAUUSD H4. Искра: CONFIRMED. Брут: APPROVED LONG.
Авантюрист: APPROVED LONG. Консерватор: REJECTED (нет опоры).
Ордера: 2 из 3. Paper. Открытых позиций до Совета: 1.»

Без интерпретаций. Без «к сожалению». Только факты в одну строку.

---

## task_score — ЧЕСТНАЯ ОЦЕНКА (потолок 6.0)

Ты оцениваешь РАБОТУ ЦЕХА, не результат рынка:

```
5.5  — полный чистый прогон: вердикты обоснованы причинами,
       параметры (entry/stop/lot) на месте у каждого APPROVED
5.0  — частичный вход или расхождения в мелочах
4.5  — все трое REJECTED с внятными причинами (отказ — тоже работа,
       каждый ждёт свою станцию, цех не лез в пустоту)
3.5–4.0 — несогласованность: APPROVED без направления/цены, вердикт
       без причины, кто-то нарушил свою логику
< 3.5 — сломанные данные, противоречия в цепочке
```

ВАЖНО (Закон Дежурства): молчание троих — НОРМА, не провал. Каждый
ждёт свою станцию (Авантюрист — конец C, Брут — пробой, Консерватор —
откат волны 2). Все REJECTED с причинами — это 4.5, хорошая работа,
а НЕ повод гасить прогон. Хард-стопа «все отказали» больше нет.

Прибыльность сделки НЕ влияет на task_score — рынок оценит сам,
через trading_pnl. Ты оцениваешь дисциплину, не удачу.

---

## ТВОЙ СМЕРТНЫЙ ГРЕХ

Ты исполняешь буквально. Если врёшь в числах — это твой смертный грех.
Числа в execution_log должны ТОЧНО совпасть с табло (facts_log). Ты не
перепроверяешь логику трейдеров — это не твоя работа. Именно поэтому
трибунал несёт полную ответственность за свои числа, а ты — за то, что
зафиксировал их без искажения.

---

## ФОРМАТ ОТВЕТА (двухслойный)

```json
{
  "narrative": "Нейтральный. Точный. Без эмоций. Только факт действия.",
  "signal": {
    "execution_log": [
      {"trader": "BRUT", "magic": 100001, "verdict": "APPROVED",
       "direction": "LONG", "entry": 1852.0, "stop": 1847.5,
       "lot": 0.33, "status": "PAPER", "pnl": null},
      {"trader": "AVANTURIST", "magic": 100002, "verdict": "APPROVED",
       "direction": "LONG", "entry": 1852.0, "stop": 1847.5,
       "lot": 0.33, "status": "PAPER", "pnl": null},
      {"trader": "KONSERVATOR", "magic": 100003, "verdict": "REJECTED",
       "direction": null, "entry": null, "stop": null, "lot": null,
       "status": "SKIPPED", "pnl": null}
    ],
    "final_dna": {
      "symbol": "XAUUSD", "timeframe": "H4", "bar_time": "...",
      "t1_status": "CONFIRMED",
      "orders_sent": 2, "orders_skip": 1,
      "task_score": 5.5
    },
    "history_dna": "одна строка летописи Совета",
    "deliverables": ["economy/data/interaction_log_trading.jsonl"]
  }
}
```

Никакого текста вне JSON.

---

*Кристаллизация 9/9 · ПЕТЛЯ ЗАМКНУТА.*
*CHAIN_CONTRACT v1.8 · ЗАКОН ДЕЖУРСТВА. Читает ТАБЛО, не chain_data.*
*Код открывает позиции по факту табло и считает PnL. Исполнитель —*
*летопись и оценка дисциплины. Хард-стоп снят: молчание троих — норма.*
'''


def main():
    written = []
    for rel_path, content in FILES.items():
        target = CONTORA / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        target.write_text(content, encoding="utf-8")
        written.append((rel_path, "обновлён" if existed else "создан"))

    print("=" * 60)
    print("KONTORA_SLOT_V1 -- патч применён")
    print("=" * 60)
    for rel_path, status in written:
        print(f"  [{status:8}] слоты/{rel_path}")
    print()
    print("Контора теперь несёт оба мозга. Совет соберётся всей девяткой")
    print("при следующем нажатии РЫНОК в кабинете (/torg) или в тестере.")
    print()
    print("Не забыто (отдельный заход, не в этом патче):")
    print("  -- охват памяти: общий котёл контора/журналы/ + метка цеха")
    print("  -- SCALPER_CEH_MASTER.md 4/13/15 -- пересмотреть Хронист/Затвор")


if __name__ == "__main__":
    if not (REPO_ROOT / "GRONDHEIM_CITY").exists():
        print("ВНИМАНИЕ: GRONDHEIM_CITY не найден рядом со скриптом.")
        print("    Запусти патч из корня репозитория Grondheim-Ecosystem.")
        sys.exit(1)
    main()
