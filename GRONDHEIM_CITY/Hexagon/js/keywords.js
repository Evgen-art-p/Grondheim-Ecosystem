/**
 * ХРАМ — Анализ ключевых слов
 * Определяет к какому хранителю направить человека
 */

import { CONFIG } from './config.js';

export const keywords = {

  /**
   * Проверяет текст на ключевые слова
   * @returns {string|null} id хранителя или null
   */
  detect(text) {
    const clean = text.toLowerCase().trim();

    for (const [word, guardianId] of Object.entries(CONFIG.keywords)) {
      // Проверяем как отдельное слово или как часть слова
      const regex = new RegExp(`\\b${word}\\b|${word}`, 'i');
      if (regex.test(clean)) {
        console.log(`[Храм] Ключевое слово: "${word}" → ${guardianId}`);
        return guardianId;
      }
    }
    return null;
  },

  /**
   * Проверяет, является ли текст триггером для Костра
   * ("не знаю", пустая строка, "..." и т.п.)
   */
  isFireTrigger(text) {
    const clean = text.toLowerCase().trim();
    // Пустая строка
    if (clean === '') return true;
    // Точные совпадения
    if (CONFIG.fireTriggersExact.includes(clean)) return true;
    // Паттерны неопределённости
    const patterns = [
      /^не\s*знаю/i,
      /^не\s*уверен/i,
      /^не\s*могу/i,
      /^не\s*поним/i,
      /^не\s*помню/i,
      /^\.{2,}$/,
      /^\?+$/,
      /^хз$/i,
      /^без\s*понятия/i,
    ];
    return patterns.some(p => p.test(clean));
  },

  /**
   * Получить данные хранителя по id
   */
  getGuardian(id) {
    return CONFIG.guardians[id] || null;
  },
};
