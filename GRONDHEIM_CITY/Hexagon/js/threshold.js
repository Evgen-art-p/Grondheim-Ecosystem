/**
 * ХРАМ — Порог
 * Таймер молчания + отслеживание курсора у края экрана
 */

import { CONFIG } from './config.js';

class Threshold {
  constructor() {
    this.timer = null;
    this.expired = false;       // Таймер истёк
    this.triggered = false;     // Порог уже сработал (однократно)
    this.mouseHandler = null;
    this.onTrigger = null;      // Колбэк при срабатывании
  }

  /** Запустить порог */
  start() {
    this.expired = false;
    this.triggered = false;
    this.startTimer();
    this.startMouseTracking();
  }

  /** Сбросить таймер (пользователь написал) */
  reset() {
    this.expired = false;
    this.clearTimer();
    this.startTimer();
  }

  /** Остановить всё */
  stop() {
    this.clearTimer();
    this.stopMouseTracking();
  }

  /** Внутренний: запуск таймера */
  startTimer() {
    this.clearTimer();
    this.timer = setTimeout(() => {
      this.expired = true;
      console.log('[Храм] Порог: таймер истёк');
    }, CONFIG.timing.fireThreshold);
  }

  clearTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  /** Внутренний: отслеживание мыши */
  startMouseTracking() {
    this.mouseHandler = (e) => {
      if (!this.expired || this.triggered) return;

      const edge = CONFIG.timing.edgeDistance;
      const nearEdge = (
        e.clientX < edge ||
        e.clientY < edge ||
        e.clientX > window.innerWidth - edge ||
        e.clientY > window.innerHeight - edge
      );

      if (nearEdge) {
        this.triggered = true;
        console.log('[Храм] Порог: сработал');
        if (this.onTrigger) this.onTrigger();
      }
    };

    document.addEventListener('mousemove', this.mouseHandler);
  }

  stopMouseTracking() {
    if (this.mouseHandler) {
      document.removeEventListener('mousemove', this.mouseHandler);
      this.mouseHandler = null;
    }
  }
}

export const threshold = new Threshold();
