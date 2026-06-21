/**
 * ХРАМ — Сессия
 * Единый контейнер данных пути: от первого слова до Свитка.
 * Заполняется в: main.js, fire.js, guardian.js
 * Читается в: ear-agent.js
 */

export const session = {
  initialKey:     '',   // первое сообщение у Безликого
  initialMood:    '',   // cold | hot | confused
  pathType:       '',   // direct | through_fire
  guardianId:     '',   // lia | yust | key | victor | finch
  fireDialogue:   [],   // [{role:'user'|'assistant', content}]
  keeperDialogue: [],   // [{role:'user'|'assistant', content}]
};

/** Сбросить сессию (новый проход) */
export function resetSession() {
  session.initialKey     = '';
  session.initialMood    = '';
  session.pathType       = '';
  session.guardianId     = '';
  session.fireDialogue   = [];
  session.keeperDialogue = [];
}

/** Определить настроение по тексту */
export function detectMood(text) {
  const t = text.toLowerCase();
  const cold = ['потерял','пусто','не знаю','зачем','устал','один','одна','никому','темно','бессмысл','нет смысла','потерялся'];
  const hot  = ['злюсь','злость','ненавижу','хочу','должен','срочно','надоело','ярость','бешусь','не могу больше'];
  const cs = cold.filter(w => t.includes(w)).length;
  const hs = hot.filter(w => t.includes(w)).length;
  if (cs > hs) return 'cold';
  if (hs > cs) return 'hot';
  return 'confused';
}
