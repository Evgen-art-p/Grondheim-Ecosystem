/**
 * ХРАМ — Память
 *
 * Два слоя:
 *   localStorage  → история между визитами (человек вернулся через день — Храм помнит)
 *   sessionStorage → текущая сессия (детали текущего прохода)
 *
 * Что храним:
 *   - Был ли человек раньше
 *   - Сколько раз приходил
 *   - К каким хранителям ходил
 *   - О чём говорил с Костром (темы/ключевые слова)
 *   - Последний визит (дата)
 */

const KEYS = {
  // localStorage (между визитами)
  visited:       'temple_visited',        // boolean
  visits:        'temple_visits',         // number
  lastVisit:     'temple_last_visit',     // ISO date
  guardianLog:   'temple_guardian_log',   // [{id, date}]
  fireTopics:    'temple_fire_topics',    // ["страх", "потеря"]

  // sessionStorage (текущая сессия)
  currentGuardian: 'temple_current_guardian',  // "lia"
  returnedToFire:  'temple_returned_to_fire',  // boolean
  fireHistory:     'temple_fire_history',      // краткая история Костра
};

class Memory {

  // ══════════════════════════════════════════════
  // Чтение
  // ══════════════════════════════════════════════

  /** Был ли человек в Храме раньше */
  get hasVisited() {
    return localStorage.getItem(KEYS.visited) === 'true';
  }

  /** Сколько раз приходил */
  get visitCount() {
    return parseInt(localStorage.getItem(KEYS.visits) || '0', 10);
  }

  /** Список хранителей, к которым ходил [{id, date}] */
  get guardianLog() {
    try {
      return JSON.parse(localStorage.getItem(KEYS.guardianLog) || '[]');
    } catch { return []; }
  }

  /** Темы разговоров с Костром */
  get fireTopics() {
    try {
      return JSON.parse(localStorage.getItem(KEYS.fireTopics) || '[]');
    } catch { return []; }
  }

  /** Последний хранитель (из лога) */
  get lastGuardian() {
    const log = this.guardianLog;
    return log.length > 0 ? log[log.length - 1].id : null;
  }

  /** Текущий хранитель (в этой сессии) */
  get currentGuardian() {
    return sessionStorage.getItem(KEYS.currentGuardian) || null;
  }

  /** Человек вернулся к Костру в этой сессии */
  get hasReturnedToFire() {
    return sessionStorage.getItem(KEYS.returnedToFire) === 'true';
  }

  /** Краткая история Костра из текущей сессии */
  get fireHistory() {
    try {
      return JSON.parse(sessionStorage.getItem(KEYS.fireHistory) || '[]');
    } catch { return []; }
  }

  // ══════════════════════════════════════════════
  // Запись
  // ══════════════════════════════════════════════

  /** Зафиксировать новый визит в Храм */
  recordVisit() {
    localStorage.setItem(KEYS.visited, 'true');
    const count = this.visitCount + 1;
    localStorage.setItem(KEYS.visits, String(count));
    localStorage.setItem(KEYS.lastVisit, new Date().toISOString());
    console.log(`[Храм] Память: визит #${count}`);
  }

  /** Зафиксировать посещение хранителя */
  recordGuardian(guardianId) {
    // В localStorage — лог
    const log = this.guardianLog;
    log.push({ id: guardianId, date: new Date().toISOString() });
    localStorage.setItem(KEYS.guardianLog, JSON.stringify(log));

    // В sessionStorage — текущий
    sessionStorage.setItem(KEYS.currentGuardian, guardianId);

    console.log(`[Храм] Память: хранитель ${guardianId}`);
  }

  /** Добавить тему Костра */
  recordFireTopic(topic) {
    const topics = this.fireTopics;
    if (!topics.includes(topic)) {
      topics.push(topic);
      localStorage.setItem(KEYS.fireTopics, JSON.stringify(topics));
      console.log(`[Храм] Память: тема Костра "${topic}"`);
    }
  }

  /** Сохранить краткую историю Костра (для возврата) */
  saveFireHistory(history) {
    // Храним только последние 10 реплик, без системных
    const brief = history
      .filter(m => m.role !== 'system')
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content.substring(0, 200) }));
    sessionStorage.setItem(KEYS.fireHistory, JSON.stringify(brief));
  }

  /** Отметить возврат к Костру */
  markReturnToFire() {
    sessionStorage.setItem(KEYS.returnedToFire, 'true');
  }

  // ══════════════════════════════════════════════
  // Контекст для промптов
  // ══════════════════════════════════════════════

  /** Контекст для Безликого: знает ли он человека */
  getBezlikyContext() {
    if (!this.hasVisited) return null;

    const lastG = this.lastGuardian;
    const visits = this.visitCount;

    return {
      isReturn: true,
      visits,
      lastGuardian: lastG,
      message: 'Ты уже был здесь. Что теперь?',
    };
  }

  /** Контекст для Костра: о чём уже говорили */
  getFireContext() {
    const topics = this.fireTopics;
    const history = this.fireHistory;

    if (topics.length === 0 && history.length === 0) return null;

    let context = '';

    if (topics.length > 0) {
      context += `В прошлый раз человек говорил о: ${topics.join(', ')}. `;
      context += 'Ты помнишь это. Не повторяй, но можешь мягко упомянуть если уместно. ';
    }

    if (history.length > 0) {
      context += 'Краткий контекст прошлого разговора: ';
      history.forEach(m => {
        const who = m.role === 'user' ? 'Человек' : 'Ты';
        context += `${who}: "${m.content}" `;
      });
    }

    return context.trim();
  }

  // ══════════════════════════════════════════════
  // Очистка (для тестов)
  // ══════════════════════════════════════════════

  /** Полный сброс памяти */
  clear() {
    Object.values(KEYS).forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    console.log('[Храм] Память: очищена');
  }
}

export const memory = new Memory();
