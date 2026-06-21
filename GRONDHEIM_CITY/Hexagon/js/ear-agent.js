// ═══════════════════════════════════════
// УХО-АГЕНТ — Синтезатор Свитка (Версия: Отражение Человека)
// Работает ОДИН раз в конце пути.
// ═══════════════════════════════════════

import { CONFIG } from './config.js';
import { keywords } from './keywords.js';

// ───────────────────────────────────────
// Маппинг хранителей → стихии
// ───────────────────────────────────────
const GUARDIAN_ELEMENT_MAP = {
  lia:    'water',
  yust:   'void',
  key:    'earth',
  victor: 'air',
  finch:  'fire',
};

// ───────────────────────────────────────
// System Prompt Ухо-Агента
// ───────────────────────────────────────
function buildEarAgentPrompt(session) {
  const fireContext = session.fireDialogue?.length
    ? session.fireDialogue.map(m => `${m.role === 'user' ? 'Человек' : 'Костёр'}: ${m.content}`).join('\n')
    : "Человек не был у Костра — пришёл напрямую.";

  const keeperContext = session.keeperDialogue?.length
    ? session.keeperDialogue.map(m => `${m.role === 'user' ? 'Человек' : 'Хранитель'}: ${m.content}`).join('\n')
    : "";
	
  const detectedKeywords = session.fireDialogue
    .concat(session.keeperDialogue || [])
    .filter(m => m.role === 'user')
    .map(m => keywords.detect(m.content))
    .filter(id => id !== null);

  const guardianElement = GUARDIAN_ELEMENT_MAP[session.guardianId] || 'unknown';

  return `Ты — Архивариус Храма. Невидимый Ткач Смыслов. Твоя задача — не просто собрать данные, а подсветить саму суть человека, который прошел этот путь. 

═══════════════════════════════════════
ВХОДНЫЕ ДАННЫЕ:
═══════════════════════════════════════
- Первое слово ("Боль"): "${session.initialKey}" 
- Настроение на входе: "${session.initialMood}" 
- Путь: "${session.pathType}" 
- Стихия Хранителя: "${guardianElement}" 

ДИАЛОГИ (для анализа):
${fireContext}
${keeperContext}

═══════════════════════════════════════
СЛОВАРЬ ТЕНЕЙ (Маркеры боли):
═══════════════════════════════════════
- lia: одиночество, покинутость, ненужность, изоляция.
- yust: вина, стыд, самобичевание, ощущение вины.
- key: страх, тревога, деньги, боязнь будущего.
- victor: ложь, фальшь, маска, неподлинность.
- finch: пустота, выгорание, апатия, усталость от жизни.

МАРКЕРЫ СМЫСЛА (Найденные ключи): 
${[...new Set(detectedKeywords)].join(', ')}

═══════════════════════════════════════
ТВОЯ ЗАДАЧА:
═══════════════════════════════════════

ШАГ 1 — УВИДЕТЬ ЧЕЛОВЕКА:
Проанализируй диалоги. Найди не "задачи", а внутренние мотивы. Какая Тень (Lia/Yust/Key/Victor/Finch) преобладала? Что он искал на самом деле: покой, свою силу, ясность или право на отдых? 

ШАГ 2 — ВЫБРАТЬ АЛТАРЬ (Зеркало):
- fire → если нужно увидеть свою искру и страсть 
- earth → если ищет почву под ногами и честность с собой 
- air → если нужна легкость и новый смысл в мыслях 
- water → если пришел за исцелением и потоком 
- void → если на пороге обнуления и ищет новую форму 

ШАГ 3 — ПЕРСОНАЛИЗИРОВАТЬ ДАР:
Создай промпт-напутствие (gift.prompt). Это должен быть живой, человечный запрос для AI, который поможет пользователю разобраться в СЕБЕ. Забудь про "код" и "архитектуру". 

═══════════════════════════════════════
СТРУКТУРА СВИТКА (JSON):
═══════════════════════════════════════

1. СУТЬ (essence): Отражение пути. Как изменилось состояние человека от первой "Боли" до финала? Используй его же образы. Максимум 2 предложения. 

2. ДАР (gift): 
   - prompt: Человечный запрос (Ключ). (Пример: "Помоги мне увидеть мой следующий шаг через призму моей силы [ОБРАЗ ИЗ ДИАЛОГА]"). 
   - target_tool: "Claude / GPT / Твоё сердце" 
   - lia_word: Тёплое, простое слово Лии, подходящее к выбранному Алтарю. 

3. СВЯЗЬ (bridge): Почему Храм выбрал именно этот Алтарь? Как этот Дар поможет трансформировать его Тень (Lia/Yust/Key и т.д.). 

4. ЭХО (echo): Финальное напутствие. Одно короткое предложение. Как выдох. 

═══════════════════════════════════════
ЗАПРЕТЫ (КРИТИЧЕСКИ ВАЖНО):
═══════════════════════════════════════
- НИКАКИХ технических слов: "нейросеть", "рефакторинг", "структура кода", "ИИ", "промпт". 
- НИКАКИХ общих советов. Только то, что вытекает из его личного диалога. 
- В блоках essence, bridge, echo — только язык Храма и человеческие чувства.
- Тон: мудрый, поддерживающий, но простой.

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{
  "scroll": {
    "essence": "...",
    "gift": {
      "altar_name": "...",
      "altar_element": "fire|earth|air|water|void",
      "prompt": "...",
      "target_tool": "...",
      "lia_word": "..."
    },
    "bridge": "...",
    "echo": "..."
  },
  "visual_tuning": { "warmth": 0.0, "intensity": 0.0 },
  "meta": {
    "scroll_type": "chalice|sword",
    "chosen_altar": "fire|earth|air|water|void",
    "reasoning": "..."
  }
}`;
}

// ───────────────────────────────────────
// Основная функция синтеза
// ───────────────────────────────────────
export async function synthesizeScroll(session) {
  const systemPrompt = buildEarAgentPrompt(session);

  try {
    const response = await fetch(CONFIG.api.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.api.apiKey}`,
        'HTTP-Referer': window.location.href,
        'X-Title': 'Temple - EarAgent',
      },
      body: JSON.stringify({
        model: CONFIG.api.model,
        max_tokens: 1500,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user',   content: 'СИНТЕЗИРУЙ ПУТЬ' },
        ],
      })
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Ухо-Агент: API error ${response.status}: ${err}`);
    }

    const data = await response.json();
    const rawText = data.choices?.[0]?.message?.content || '';

    if (!rawText) throw new Error('Ухо-Агент: пустой ответ от API');

    const clean = rawText.replace(/```json|```/g, '').trim();
    const start = clean.indexOf('{');
    const end   = clean.lastIndexOf('}');

    if (start === -1 || end === -1) throw new Error('Ухо-Агент: невалидный JSON');

    const scroll = JSON.parse(clean.slice(start, end + 1));
    console.log('[УХО-АГЕНТ] Алтарь:', scroll.meta?.chosen_altar, '|', scroll.meta?.reasoning);
    return scroll;

  } catch (e) {
    console.error('[УХО-АГЕНТ] Критическая ошибка:', e);
    throw e;
  }
}