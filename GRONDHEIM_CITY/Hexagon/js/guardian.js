/**
 * ХРАМ — Хранитель
 * Диалог с хранителем через API
 * Определение конца беседы: маркер [ОТПУСТИ] от хранителя или слова прощания от человека
 */

import { CONFIG } from './config.js';
import { stateMachine } from './state.js';
import { session } from './session.js';
import { synthesizeScroll } from './ear-agent.js';

// DeepSeek и другие модели иногда пишут маркер без скобок:
// [ТЫ НЕ ОДИН] → ТЫ НЕ ОДИН
// Детектируем оба варианта
const MARKER_RE = /\[?ТЫ НЕ ОДИН\]?/;
const hasReleaseMarker  = text => MARKER_RE.test(text);
const cleanReleaseMarker = text => text.replace(MARKER_RE, '').trim();

class Guardian {
  constructor() {
    this.history = [];          // История диалога
    this.systemPrompt = '';     // Промпт хранителя
    this.guardianId = null;     // Текущий хранитель
    this.isWaiting = false;
    this.released = false;      // Уже отпущен
    this.outputEl = null;
    this.inputEl = null;
    this._promptCache = {};     // Кэш загруженных промптов
  }

  /** Инициализация DOM */
  init() {
    this.outputEl = document.getElementById('guardian-chat');
    this.inputEl = document.getElementById('guardian-input');

    if (this.inputEl) {
      // Убираем старый listener если был
      this.inputEl.replaceWith(this.inputEl.cloneNode(true));
      this.inputEl = document.getElementById('guardian-input');

      this.inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const text = this.inputEl.value.trim();
          if (text && !this.isWaiting && !this.released) {
            this.send(text);
            this.inputEl.value = '';
          }
        }
      });
    }
  }

  /** Войти в состояние хранителя */
  async enter(guardianId) {
    this.history = [];
    this.released = false;
    this.isWaiting = false;
    this.guardianId = guardianId;

    // Очистить чат
    if (this.outputEl) this.outputEl.innerHTML = '';

    // Загрузить промпт хранителя
    const guardianData = CONFIG.guardians[guardianId];
    if (guardianData?.prompt) {
      this.systemPrompt = await this._loadPrompt(guardianData.prompt);
    } else {
      this.systemPrompt = '';
    }

    console.log(`[Храм] Хранитель ${guardianData?.name}: диалог начат`);
  }

  /** Отправить сообщение хранителю */
  async send(text) {
    if (this.released) return;

    // Проверяем слова прощания ДО отправки
    if (this._isFarewell(text)) {
      this.appendMessage('user', text);
      this.history.push({ role: 'user', content: text });
      session.keeperDialogue.push({ role: 'user', content: text });

      // Даём хранителю ответить последний раз
      this.isWaiting = true;
      this.showTyping();

      try {
        // Добавляем подсказку что человек прощается
        const farewellHistory = [
          ...this.history,
          { role: 'system', content: 'Человек прощается. Скажи последние слова и добавь в конец: [ТЫ НЕ ОДИН]' },
        ];
        const response = await this._callAPI(farewellHistory);
        this.hideTyping();

        // Убираем маркер из видимого текста
        const cleanResponse = cleanReleaseMarker(response);
        if (cleanResponse) {
          await this.typeResponse(cleanResponse);
          this.history.push({ role: 'assistant', content: cleanResponse });
          session.keeperDialogue.push({ role: 'assistant', content: cleanResponse });
        }
      } catch {
        this.hideTyping();
      }

      this.isWaiting = false;
      this._triggerRelease();
      return;
    }

    // Обычное сообщение
    this.appendMessage('user', text);
    this.history.push({ role: 'user', content: text });
    session.keeperDialogue.push({ role: 'user', content: text });

    this.isWaiting = true;
    this.showTyping();

    try {
      const response = await this._callAPI();
      this.hideTyping();

      // Проверяем маркер выпуска в ответе хранителя
      if (hasReleaseMarker(response)) {
        const cleanResponse = cleanReleaseMarker(response);
        if (cleanResponse) {
          await this.typeResponse(cleanResponse);
          this.history.push({ role: 'assistant', content: cleanResponse });
          session.keeperDialogue.push({ role: 'assistant', content: cleanResponse });
        }
        this.isWaiting = false;
        this._triggerRelease();
        return;
      }

      // Обычный ответ
      if (response) {
        this.history.push({ role: 'assistant', content: response });
        session.keeperDialogue.push({ role: 'assistant', content: response });
        await this.typeResponse(response);
      }
    } catch (err) {
      this.hideTyping();
      console.error('[Храм] Guardian API error:', err);
      await this.typeResponse('...');
    }

    this.isWaiting = false;
  }

  // ── Приватные ──────────────────────────────────

  /** Вызов API */
  async _callAPI(customHistory) {
    const messages = [];
    if (this.systemPrompt) {
      messages.push({ role: 'system', content: this.systemPrompt });
    }
    messages.push(...(customHistory || this.history));

    const response = await fetch(CONFIG.api.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.api.apiKey}`,
        'HTTP-Referer': window.location.origin,
        'X-Title': 'temple',
      },
      body: JSON.stringify({
        model: CONFIG.api.model,
        messages,
        max_tokens: CONFIG.api.maxTokens,
        temperature: CONFIG.api.temperature,
      }),
    });

    if (!response.ok) {
      throw new Error(`API ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices?.[0]?.message?.content?.trim() || '...';
  }

  /** Загрузить промпт из файла */
  async _loadPrompt(path) {
    if (this._promptCache[path]) return this._promptCache[path];
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`${res.status}`);
      const text = await res.text();
      this._promptCache[path] = text;
      return text;
    } catch (err) {
      console.warn('[Храм] Промпт не загружен:', path, err);
      return '';
    }
  }

  /** Проверка слов прощания */
  _isFarewell(text) {
    const clean = text.toLowerCase().trim();
    return CONFIG.farewellWords.some(word => clean.includes(word));
  }

  /** Запуск выпуска */
  _triggerRelease() {
    if (this.released) return;
    this.released = true;
    console.log(`[Храм] Хранитель ${this.guardianId}: выпуск`);

    setTimeout(() => {
      this._launchScrollPhase();
    }, CONFIG.timing.releaseDelay);
  }

  /** ← ХРАМ SCROLL: стартуем синтез в фоне, передаём промис в RELEASE */
  _launchScrollPhase() {
    session.guardianId = this.guardianId;
    session.pathType   = session.fireDialogue.length > 0 ? 'through_fire' : 'direct';

    console.log('[Храм] Ухо-Агент: старт синтеза (фон)', session);

    // Запускаем синтез — НЕ ждём здесь, передаём промис дальше
    const scrollPromise = synthesizeScroll(session).catch(err => {
      console.error('[Храм] Ухо-Агент: ошибка', err);
      return null; // null = свиток не покажем, но путь продолжится
    });

    // Передаём промис в RELEASE — main.js сам покажет свиток в нужный момент
    stateMachine.transition(CONFIG.states.RELEASE, {
      guardianId:    this.guardianId,
      scrollPromise: scrollPromise,
    });
  }

  /** Добавить сообщение в чат */
  appendMessage(role, text) {
    if (!this.outputEl) return;
    const div = document.createElement('div');
    div.className = `guardian-msg guardian-msg--${role}`;
    div.textContent = text;
    this.outputEl.appendChild(div);
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  /** Typewriter эффект */
  async typeResponse(text) {
    if (!this.outputEl) return;
    const div = document.createElement('div');
    div.className = 'guardian-msg guardian-msg--guardian';
    this.outputEl.appendChild(div);

    for (let i = 0; i < text.length; i++) {
      div.textContent += text[i];
      this.outputEl.scrollTop = this.outputEl.scrollHeight;
      await new Promise(r => setTimeout(r, CONFIG.timing.typewriterSpeed));
    }
  }

  showTyping() {
    if (!this.outputEl) return;
    const el = document.createElement('div');
    el.className = 'guardian-msg guardian-msg--typing';
    el.id = 'guardian-typing';
    el.textContent = '···';
    this.outputEl.appendChild(el);
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  hideTyping() {
    const el = document.getElementById('guardian-typing');
    if (el) el.remove();
  }
}

export const guardian = new Guardian();
