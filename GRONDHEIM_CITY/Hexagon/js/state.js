/**
 * ХРАМ — State Machine
 * Управляет состояниями и переходами
 */

import { CONFIG } from './config.js';

class StateMachine {
  constructor() {
    this.current = CONFIG.states.SEEK;
    this.listeners = [];
    this.history = [];
  }

  /** Подписка на изменение состояния */
  on(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  /** Переход в новое состояние */
  transition(newState, data = {}) {
    const prev = this.current;
    this.history.push({ from: prev, to: newState, time: Date.now(), data });
    this.current = newState;
    console.log(`[Храм] ${prev} → ${newState}`, data);
    this.listeners.forEach(fn => fn(newState, prev, data));
  }

  /** Текущее состояние */
  get state() {
    return this.current;
  }

  /** Проверка состояния */
  is(state) {
    return this.current === state;
  }
}

// Синглтон
export const stateMachine = new StateMachine();
