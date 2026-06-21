import { CONFIG } from './config.js';
import { stateMachine } from './state.js';
import { keywords } from './keywords.js';
import { threshold } from './threshold.js';
import { memory } from './memory.js';
import { session } from './session.js';

const MARKER_RE = /\[?ТЫ НЕ ОДИН\]?/;
const hasReleaseMarker   = text => MARKER_RE.test(text);
const cleanReleaseMarker = text => text.replace(MARKER_RE, '').trim();

class Fire {
  constructor() {
    this.history = [];
    this.isWaiting = false;
    this.released = false;
    this.pendingGuardian = null;
    this.systemPrompt = '';
    this._promptCache = null;
    this.outputEl = null;
    this.inputEl = null;
    this._classifierRunning = false;
    this._userMsgCount = 0;
  }

  init() {
    this.outputEl = document.getElementById('fire-output');
    this.inputEl = document.getElementById('fire-input');

    if (this.inputEl) {
      this.inputEl.replaceWith(this.inputEl.cloneNode(true));
      this.inputEl = document.getElementById('fire-input');
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

  async enter() {
    // Сброс состояния для нового круга
    this.history = [];
    this.released = false;
    this.isWaiting = false;
    this.pendingGuardian = null;
    this._classifierRunning = false;
    this._userMsgCount = 0;
    
    if (this.outputEl) {
      this.outputEl.innerHTML = '';
      // Принудительно проверяем наличие подложки в стилях через JS
      this.outputEl.style.background = "rgba(255, 255, 255, 0.15)";
      this.outputEl.style.backdropFilter = "blur(12px)";
    }

    this.systemPrompt = await this._loadPrompt(CONFIG.firePromptPath);
    threshold.start();
    console.log('[Храм] Костёр: новый круг начат');
  }

  async _loadPrompt(path) {
    if (this._promptCache) return this._promptCache;
    try {
      const res = await fetch(path);
      const text = await res.text();
      this._promptCache = text.trim();
      return this._promptCache;
    } catch (err) {
      this._promptCache = CONFIG.fireSystemPrompt || 'Ты — Костёр.';
      return this._promptCache;
    }
  }

  async send(text) {
    if (this.released) return;
    threshold.reset();

    this.appendMessage('user', text);
    this.history.push({ role: 'user', content: text });
    session.fireDialogue.push({ role: 'user', content: text });
    this._userMsgCount++;

    const guardianId = keywords.detect(text);
    if (guardianId && !this.pendingGuardian) {
      this.pendingGuardian = guardianId;
    }

    this.isWaiting = true;
    this.showTyping();

    try {
      const response = await this.callAPI();
      this.hideTyping();

      if (hasReleaseMarker(response)) {
        const clean = cleanReleaseMarker(response);
        if (clean) {
          await this.typeResponse(clean);
          session.fireDialogue.push({ role: 'assistant', content: clean });
        }
        this._handleRelease();
      } else {
        session.fireDialogue.push({ role: 'assistant', content: response });
        await this.typeResponse(response);
      }
    } catch (err) {
      this.hideTyping();
      await this.typeResponse('...');
    }
    this.isWaiting = false;
  }

  async callAPI() {
    const messages = [
      { role: 'system', content: this._buildSystemPrompt() },
      ...this.history,
    ];

    const response = await fetch(CONFIG.api.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.api.apiKey}`
      },
      body: JSON.stringify({
        model: CONFIG.api.model,
        messages,
        temperature: CONFIG.api.temperature,
      }),
    });

    const data = await response.json();
    return data.choices?.[0]?.message?.content?.trim() || '...';
  }

  _buildSystemPrompt() {
    let prompt = this.systemPrompt || '';
	  
	// Если слово найдено — отпускаем после 3-й реплики
	// Если слово не найдено — держим до 6-й, чтобы классификатор успел сработать
	const canRelease = this.pendingGuardian ? (this._userMsgCount >= 3) : (this._userMsgCount >= 6);

	if (canRelease) {
      prompt += `\n\n[СИСТЕМА]: Скажи последнее прощание и добавь [ТЫ НЕ ОДИН].`;
    }
    return prompt;
  }

  _handleRelease() {
    this.released = true;
    threshold.stop();
    setTimeout(() => {
      stateMachine.transition(CONFIG.states.GUARDIAN, {
        guardianId: this.pendingGuardian || 'finch',
      });
    }, CONFIG.timing.releaseDelay);
  }

  appendMessage(role, text) {
    if (!this.outputEl) return;
    const div = document.createElement('div');
    div.className = `fire-msg fire-msg--${role}`;
    div.textContent = text;
    // Принудительный чёрный цвет для нового круга
    div.style.color = "#000000";
    this.outputEl.appendChild(div);
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  async typeResponse(text) {
    if (!this.outputEl) return;
    const div = document.createElement('div');
    div.className = 'fire-msg fire-msg--fire';
    div.style.color = "#000000";
    this.outputEl.appendChild(div);

    for (let i = 0; i < text.length; i++) {
      div.textContent += text[i];
      this.outputEl.scrollTop = this.outputEl.scrollHeight;
      await new Promise(r => setTimeout(r, CONFIG.timing.typewriterSpeed));
    }
  }

  showTyping() {
    const el = document.createElement('div');
    el.className = 'fire-msg fire-msg--typing';
    el.id = 'fire-typing';
    el.style.color = "#000000";
    el.textContent = '···';
    this.outputEl.appendChild(el);
  }

  hideTyping() {
    const el = document.getElementById('fire-typing');
    if (el) el.remove();
  }

  triggerThreshold() {
    // Вместо требования «скажи слово», просто напоминание о присутствии
	this.typeResponse('Я здесь.'); 
  }
}

export const fire = new Fire();