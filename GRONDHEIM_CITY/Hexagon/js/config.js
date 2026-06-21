/**
 * ХРАМ — Конфигурация
 * Все настройки в одном месте для удобного управления
 */

export const CONFIG = {

  // ── API ──────────────────────────────────────────
  api: {
    endpoint: 'https://openrouter.ai/api/v1/chat/completions',
    model: 'deepseek/deepseek-chat',
    apiKey: '', // Вставляй локально, не коммить ключ в Git
    maxTokens: 2000,
    temperature: 0.8,
  },

  // ── Состояния ────────────────────────────────────
  states: {
    SEEK:     'seek',
    DARKNESS: 'darkness',
    TEMPLE:   'temple',
    APPEAR:   'appear',
    LOOP:     'loop',
    INPUT:    'input',
    FIRE:     'fire',
    GUARDIAN: 'guardian',
    RELEASE:  'release',
    EXIT:     'exit',
  },

  // ── Тайминги (мс) ───────────────────────────────
  timing: {
    seekFadeIn:       800,
    seekToBlack:      2600,
    blackToTemple:    700,
    templeDelay:      400,
    videoFallback:    10000,
    loopToCapsule:    1800,
    capsuleFocus:     900,
    fadeTransition:   1400,
    fireThreshold:    90000,    // 90 сек до порога Костра
    edgeDistance:     50,        // px от края экрана
    typewriterSpeed:  45,        // мс между символами
    guardianSilence: 180000,    // 3 мин молчания → выпуск (резерв, пока не активен)
    releaseDelay:    2000,       // пауза перед запуском release видео
    exitToSeek:      8000,       // сек до появления «ищи» на экране выхода
  },

  // ── Ключевые слова → Хранители ──────────────────
  keywords: {
    'одиночество': 'lia',
    'одиноко':     'lia',
    'одинок':      'lia',
    'одинока':     'lia',
    'я один':      'lia',
    'я одна':      'lia',
    'никому':      'lia',
    'не нужен':    'lia',
    'благодарность':    'lia',
    'нежность':    'lia',
    'любовь':    'lia',
    'радость':    'lia',
    'покой':    'lia',
    'тишина':    'lia',
    'тащусь':    'lia',
    'секс':    'lia',

    'вина':        'yust',
    'виноват':     'yust',
    'виновата':    'yust',
    'справедливость': 'yust',
    'несправедливо':  'yust',
    'долг':  'yust',
    'камень':  'yust',
    'груз':  'yust',
    'ошибка':  'yust',
    'совестно':  'yust',
    'расплата':  'yust',
    'приговор':  'yust',
    'тяжесть':  'yust',

    'страх':       'key',
    'страшно':     'key',
    'боюсь':       'key',
    'потеря':      'key',
    'потерять':    'key',
    'потерял':     'key',
    'потеряла':    'key',
    'деньги':      'key',
    'дар':      'key',
    'победа':      'key',
    'удача':      'key',
    'нашел':      'key',
    'сокровища':      'key',
    'успех':      'key',
    'выигрыш':      'key',

    'ложь':        'victor',
    'вру':         'victor',
    'обманываю':   'victor',
    'притворяюсь': 'victor',
    'фальшь':      'victor',
    'маска':      'victor',
    'секрет':      'victor',
    'тайна':      'victor',
    'роль':      'victor',
    'чужое':      'victor',
    'тень':      'victor',
    'прячу':      'victor',
    'наебал':      'victor',
    'пиздешь':      'victor',
    'неправда':      'victor',

    'пустота':     'finch',
    'пусто':       'finch',
    'бессмысленно':'finch',
    'смысл':       'finch',
    'потерялся':   'finch',
    'потерялась':  'finch',
    'заблудился':  'finch',
    'надежда':  'finch',
    'зерно':  'finch',
    'шанс':  'finch',
    'вера':  'finch',
    'начало':  'finch',
    'мечта':  'finch',
    'предчувствие':  'finch',
  },

  // ── Фразы-триггеры для Костра ───────────────────
  fireTriggersExact: [
    'не знаю',
    'не уверен',
    'не уверена',
    'не могу ответить',
    'не понимаю',
    'не помню',
    'ни с чем',
    'просто',
    'случайно',
    'мимо',
    'неважно',
    'привет',
    '...',
    '',
  ],

  // ── Видео-сцены (intro → loop) ──────────────────
  // Каждая сцена: intro = появление, loop = жизнь, release = выпуск, releaseLoop = после выпуска
  scenes: {
    bezliky: {
      intro: '2_bezlikiy/appear.mp4',
      loop:  '2_bezlikiy_loop/loop.mp4',
    },
    fire: {
      intro: '3_koster/fire_appear.mp4',
      loop:  '3_koster/fire_loop.mp4',
    },
    lia: {
      intro:       '3_guardians/lia/appear.mp4',
      loop:        '3_guardians/lia/loop.mp4',
      release:     '3_guardians/lia/release.mp4',
      releaseLoop: '3_guardians/lia/release_loop.mp4',
    },
    yust: {
      intro:       '3_guardians/yust/appear.mp4',
      loop:        '3_guardians/yust/loop.mp4',
      release:     '3_guardians/yust/release.mp4',
      releaseLoop: '3_guardians/yust/release_loop.mp4',
    },
    key: {
      intro:       '3_guardians/key/appear.mp4',
      loop:        '3_guardians/key/loop.mp4',
      release:     '3_guardians/key/release.mp4',
      releaseLoop: '3_guardians/key/release_loop.mp4',
    },
    victor: {
      intro:       '3_guardians/victor/appear.mp4',
      loop:        '3_guardians/victor/loop.mp4',
      release:     '3_guardians/victor/release.mp4',
      releaseLoop: '3_guardians/victor/release_loop.mp4',
    },
    finch: {
      intro:       '3_guardians/finch/appear.mp4',
      loop:        '3_guardians/finch/loop.mp4',
      release:     '3_guardians/finch/release.mp4',
      releaseLoop: '3_guardians/finch/release_loop.mp4',
    },
  },

  // ── Хранители ───────────────────────────────────
  guardians: {
    lia:    { name: 'Лия',    phrase: 'Я здесь. Ты не один.',                  scene: 'lia',    prompt: '3_guardians/lia/prompt.txt' },
    yust:   { name: 'Юст',    phrase: 'Справедливость внутри. Ищи.',           scene: 'yust',   prompt: '3_guardians/yust/prompt.txt' },
    key:    { name: 'Кей',    phrase: 'Ценность не в деньгах. Смотри глубже.', scene: 'key',    prompt: '3_guardians/key/prompt.txt' },
    victor: { name: 'Виктор', phrase: 'Правда освободит. Если примешь.',       scene: 'victor', prompt: '3_guardians/victor/prompt.txt' },
    finch:  { name: 'Финч',   phrase: 'Посади семя. Я подожду.',              scene: 'finch',  prompt: '3_guardians/finch/prompt.txt' },
  },

  // ── Маркер конца беседы (хранитель вставляет в ответ) ──
  releaseMarker: '[ТЫ НЕ ОДИН]',

  // ── Слова прощания (человек говорит → выпуск) ──
  farewellWords: [
    'спасибо', 'благодарю', 'пора', 'ухожу', 'уйду',
    'прощай', 'до свидания', 'достаточно', 'хватит',
    'мне пора', 'я пойду', 'отпусти', 'выпусти',
  ],

  // ── Аудио (зарезервированные пути) ──────────────
  audio: {
    prosnis:    'audio/prosnis.mp3',
    fireCrackle:'audio/fire_first.mp3',
    lia:        'audio/lia.mp3',
    yust:       'audio/yust.mp3',
    key:        'audio/key.mp3',
    victor:     'audio/victor.mp3',
    finch:      'audio/finch.mp3',
    ambient:    'audio/ambient.mp3',
  },

  // ── Путь к промпту Костра ────────────────────────
  firePromptPath: '3_koster/fire_prompt.txt',

  // ── Фолбэк (если файл промпта не загрузился) ───
  fireSystemPrompt: 'Ты — Костёр. Огонь в центре Храма. Отвечай коротко, на русском. Отражай слова человека как эхо. Максимум 1-2 предложения. Когда чувствуешь что пора — скажи последние слова и добавь [ТЫ НЕ ОДИН].',
};
