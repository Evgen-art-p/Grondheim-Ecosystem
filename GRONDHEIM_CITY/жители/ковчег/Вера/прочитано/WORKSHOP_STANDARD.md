# СТАНДАРТ ЦЕХА — ШАБЛОН
## studio/WORKSHOP_STANDARD.md
## Студия «Шесть Пальцев» · 2026
##
## Применяется ко всем 11 цехам.
## Для каждого нового цеха — скопировать этот файл,
## заполнить свои значения, удалить комментарии.

---

## 1. ОБЯЗАТЕЛЬНЫЕ ФАЙЛЫ ЦЕХА

Каждый цех живёт в `studio/modules/{цех_id}/` и содержит:

```
studio/modules/{цех_id}/
├── manifest.json        ← обязателен
├── CHAIN_CONTRACT.md    ← обязателен (таможня читает его)
├── hooks.py             ← если нужна кастомная логика
└── forge/               ← промты агентов
    ├── A01/prompt.md
    ├── A02/prompt.md
    └── ...
```

Если `CHAIN_CONTRACT.md` отсутствует — `contract_validator` падает на дефолт `video_shorts`.

---

## 2. MANIFEST.JSON — ОБЯЗАТЕЛЬНЫЕ ПОЛЯ

```json
{
  "id":           "цех_id",
  "label":        "Название для UI",
  "icon":         "🔧",
  "version":      "1.0",
  "description":  "Что делает цех и сколько режимов.",
  "run_type":     "цех_id",
  "phases": {
    "ФАЗА_1": ["A01", "A02"],
    "ФАЗА_2": ["A03", "A04"],
    "ФАЗА_N": ["A12"]
  },
  "qa_agent":         "A12",
  "checkpoint_after": [],
  "stop_after":       null,
  "conflict_mode":    "none",
  "interaction_log":  "economy/data/interaction_log_{цех_id}.jsonl",
  "memory_layers":    ["personal", "project", "runtime", "interaction"]
}
```

### Правила manifest.json

| Поле | Что писать |
|------|------------|
| `id` | строчные буквы + underscore, уникальный в студии |
| `run_type` | совпадает с `id` для дефолтного режима |
| `qa_agent` | всегда последний агент цеха (финализатор) |
| `conflict_mode` | `"none"` если не нужно — дорогой режим, включать осознанно |
| `hard_stop` | только если цех требует гейта. Без гейта — не писать поле |
| `interaction_log` | путь уникальный для каждого цеха — иначе логи мешаются |

---

## 3. CHAIN_CONTRACT.MD — МИНИМАЛЬНАЯ СТРУКТУРА

Контракт описывает что каждый агент **пишет** и **читает** в `chain_data`.
Это единственный источник правды для `contract_validator`.

```markdown
# КОНТРАКТ КЛЮЧЕЙ — {ЦЕХ} v1.0
## studio/modules/{цех_id}/CHAIN_CONTRACT.md

## СВОДНАЯ ТАБЛИЦА

| Агент | Пишет | Читает |
|-------|-------|--------|
| A01 Имя | `ключ_a01` | `master_brief`, `history_dna` |
| A02 Имя | `ключ_a02` | `ключ_a01`, `history_dna` |
| ...   | ...   | ... |
| A12 Имя | `ключ_a12`, `deliverables`, `final_dna`, `history_dna` | ВСЁ |

## СТРУКТУРЫ КЛЮЧЕЙ
(описать каждый ключ из колонки "Пишет")
```

### Правила CHAIN_CONTRACT

| Правило | Почему |
|---------|--------|
| Ключи в backtick-ах `` `ключ` `` через запятую в ячейке | contract_validator парсит именно backtick-и |
| Каждый ключ — отдельный backtick, не `ключ1 + ключ2` | Иначе validator видит `ключ1 + ключ2` как один ключ |
| `history_dna` в колонке "Пишет" у A01 и A12 | Иначе validator блокирует запись |
| `deliverables` и `final_dna` — отдельные backtick-и у A12 | Аналогично |

---

## 4. HOOKS.PY — ШАБЛОН

Если в цехе нужна кастомная логика (генерация, стоп, FAL):

```python
# studio/modules/{цех_id}/hooks.py

def on_before_agent(state: dict, worker_id: str, context: str) -> str:
    """Модифицирует контекст до вызова агента. Вернуть context."""
    return context


def on_after_agent(state: dict, worker_id: str, human_text: str, meta: dict) -> dict:
    """Пост-обработка после агента.

    Возвращает:
        {}                   — продолжить пайплайн
        {"action": "stop"}   — остановить пайплайн (работает ТОЛЬКО если
                               cartridge.py содержит проверку action == "stop")
        {"human_text": ...,
         "meta": ...}        — переопределить текст/мета агента
    """
    # Пример: стоп после A04 в PLAN-режиме
    run_type = state.get("run_type", "")
    if run_type == "content_plan" and worker_id == "A04":
        print(f"[HOOKS] PLAN: стоп после {worker_id}.")
        return {"action": "stop"}

    return {}
```

---

## 5. BILLING И MINISTRY — ПРАВИЛА ДЛЯ FAL-ВЫЗОВОВ

Если цех генерирует изображения/видео через fal.ai:

```python
# В hooks.py — slot_id для FAL-вызовов
# НЕ писать slot_id=f"img_{attempt}" — ministry распылит статистику

# ПРАВИЛЬНО:
slot_id = f"{state.get('active_dept', 'unknown')}_fal"
# Пример: "social_mix_fal", "turbo_fal", "video_long_fal"

generate_image(
    prompt,
    agent_id="A06",
    slot_id=slot_id,   # ← единый ключ для всех попыток
    ...
)
```

Почему это важно: `ministry.py` агрегирует историю по `(agent_id, slot_id)`.
Минимум 3 рана нужно чтобы ministry начал давать подсказки агентам.
Если slot_id разный каждый раз — ministry никогда не наберёт статистику.

---

## 6. МОДЕЛИ — АКТУАЛЬНЫЙ СПИСОК

Используй только модели из `billing_ledger.MODEL_PRICES`.
Имя модели в коде должно **точно** совпадать с ключом в `MODEL_PRICES` — иначе биллинг идёт по `_default` (переоценка).

```python
# Текущие поддерживаемые LLM-модели:
"google/gemini-2.5-flash"       # рекомендуется для QA-проверок (дёшево + мультимодально)
"google/gemini-2.0-flash"
"anthropic/claude-sonnet-4-5"   # для сложных агентов
"anthropic/claude-3-haiku"      # для простых/быстрых агентов
"openai/gpt-4o-mini"
"openai/gpt-4o"

# FAL-модели (фиксированная цена $0.04):
"fal/Nano Banana Pro"
"fal/Seedream 4.5"
```

⚠️ `google/gemini-1.5-flash` — устарела, больше не используется.
⚠️ Добавляя новую модель — сначала добавь её в `billing_ledger.MODEL_PRICES`.

---

## 7. MINISTRY — ИНТЕГРАЦИЯ В ФИНАЛИЗАТОРЕ

Чтобы economy_rating агентов рос и ministry давал подсказки,
финализатор (A12) должен вызывать `record_outcome` после получения QA-оценки.

```python
# В hooks.py, on_after_agent для финализатора:
if worker_id == "A12":
    chain_data = state.get("chain_data", {})
    viral_score = (
        chain_data.get("tim_analytics", {}).get("viral_score", 0)
        or chain_data.get("final_dna", {}).get("viral_score", 0)
    )
    if viral_score:
        slot_id = state.get("active_dept", "unknown")
        try:
            from studio.economy import ministry
            # Записываем для генератора изображений (A06)
            ministry.record_outcome("A06", f"{slot_id}_fal", viral_score, cost_usd=0.0)
            # Записываем для всего пайплайна
            ministry.record_outcome("pipeline", slot_id, viral_score, cost_usd=0.0)
        except Exception as e:
            print(f"[HOOKS] ministry.record_outcome: {e}")
```

---

## 8. ЧЕКЛИСТ НОВОГО ЦЕХА

Перед запуском пайплайна убедиться:

```
□ manifest.json создан и содержит все обязательные поля (раздел 2)
□ CHAIN_CONTRACT.md создан (раздел 3)
□ В CHAIN_CONTRACT: все ключи в backtick-ах, A01 и A12 имеют history_dna
□ hooks.py: {"action": "stop"} используется только если cartridge.py поддерживает
□ hooks.py: slot_id для FAL = "{dept}_fal", не f"img_{attempt}"
□ hooks.py: модель для LLM-вызовов — из актуального списка (раздел 6)
□ hooks.py: ministry.record_outcome вызывается в A12
□ interaction_log в manifest.json — уникальный путь для этого цеха
□ conflict_mode = "none" если конфликты не нужны
```

---

## 9. ИЗВЕСТНЫЕ СИСТЕМНЫЕ ПРОБЛЕМЫ (общие для всех цехов)

| # | Проблема | Статус | Фикс |
|---|---------|--------|------|
| 1 | cartridge.py не обрабатывает `{"action": "stop"}` | 🔴 Открыт | Добавить `if hook_result.get("action") == "stop": break` в строку 396 |
| 2 | A05 JSON→Markdown порядок ломает парсер | 🟡 Открыт | Привести к Markdown→JSON |
| 3 | fal_client.py стр. 43 — `_current_client_slug` = Path вместо None | 🟠 Открыт | Разбить на две строки |

Эти баги влияют на все цеха одинаково.
Баг #1 — самый критичный, один цикл любого цеха с PLAN-режимом сломан.

---

*WORKSHOP_STANDARD v1.0 · Студия «Шесть Пальцев» · 2026*
*Синхронизирован с: cartridge.py, contract_validator.py, billing_ledger.py, ministry.py, hooks.py*
