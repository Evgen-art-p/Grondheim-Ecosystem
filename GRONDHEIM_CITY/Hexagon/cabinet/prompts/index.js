/**
 * КАБИНЕТ — Реестр промптов
 * Добавляй новые промпты сюда, они появятся в панели автоматически
 *
 * knowledge — путь к .md файлу с базой знаний (необязательно)
 * Загружается автоматически и инжектится после system prompt
 */

export const PROMPTS = {

  // ── Папки с промптами ─────────────────────────
  folders: [
    {
      id: 'kostyor',
      name: '🔥 Костёр',
      prompts: [
        {
          id: 'fire_main',
          name: 'Костёр — основной',
          file: 'kostyor/fire_main.txt',
          knowledge: 'knowledge/kostyor.md',
        },
        {
          id: 'fire_soft',
          name: 'Костёр — мягкий',
          file: 'kostyor/fire_soft.txt',
          knowledge: 'knowledge/kostyor.md',
        },
      ],
    },
    {
      id: 'guardians',
      name: '🛡 Хранители',
      prompts: [
        {
          id: 'lia',
          name: 'Лия',
          file: 'guardians/lia.txt',
          knowledge: 'knowledge/lia.md',
        },
        {
          id: 'yust',
          name: 'Юст',
          file: 'guardians/yust.txt',
          knowledge: 'knowledge/yust.md',
        },
        {
          id: 'key',
          name: 'Кей',
          file: 'guardians/key.txt',
          knowledge: 'knowledge/key.md',
        },
        {
          id: 'victor',
          name: 'Виктор',
          file: 'guardians/victor.txt',
          knowledge: 'knowledge/victor.md',
        },
        {
          id: 'finch',
          name: 'Финч',
          file: 'guardians/finch.txt',
          knowledge: 'knowledge/finch.md',
        },
      ],
    },
    {
      id: 'test',
      name: '🧪 Тесты',
      prompts: [
        {
          id: 'finch_p',
          name: 'Финч-смыслы',
          file: 'test/finch.txt',
        },
        {
          id: 'echo',
          name: 'Лока',
          file: 'test/loka.txt',
        },
        {
          id: 'key_p',
          name: 'Кей-партнер',
          file: 'test/key.txt',
        },
        {
          id: 'yust_p',
          name: 'Юст-юрист',
          file: 'test/yust.txt',
        },
        {
          id: 'victor_p',
          name: 'Виктор-критик',
          file: 'test/victor.txt',
        },
      ],
    },
  ],
};
