/**
 * ХРАМ — Главный модуль
 * Инициализация и связка всех компонентов
 */

import { CONFIG } from './config.js';
import { stateMachine } from './state.js';
import { video } from './video.js';
import { keywords } from './keywords.js';
import { fire } from './fire.js';
import { guardian } from './guardian.js';
import { threshold } from './threshold.js';
import { memory } from './memory.js';
import { initCursor } from './cursor.js';
import { session, resetSession, detectMood } from './session.js'; // ← ХРАМ SCROLL
import { showScroll } from './scroll.js'; // ← ХРАМ SCROLL
import { audio } from './audio.js';

const $ = id => document.getElementById(id);
const delay = ms => new Promise(r => setTimeout(r, ms));

// ── Аудио: пути к файлам ─────────────────────────
audio.setSources({
  ambient:  'audio/ambient.mp3',   // Порог + Безликий
  guardian: 'audio/guardian.mp3',  // Хранители
  release:  'audio/release.mp3',   // Свиток + Выход
});

// Прелоад всех файлов сразу — чтобы play() был мгновенным
audio.preloadAll();

// ── Управление экранами ──────────────────────────

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  $(id)?.classList.add('active');
}

function addScreen(id) {
  $(id)?.classList.add('active');
}

function hideScreen(id) {
  $(id)?.classList.remove('active');
}

// ── Обработчик переходов состояний ───────────────

stateMachine.on(async (state, prev, data) => {
  switch (state) {

    // ── Вход ──────────────────────────────────────
    case CONFIG.states.DARKNESS:
      // Фиксируем визит
      memory.recordVisit();
      resetSession(); // ← ХРАМ SCROLL: новый проход — чистая сессия

      audio.play('ambient', 2000);

      showScreen('screen-seek');
      $('seek-word')?.classList.add('appeared');
      await delay(CONFIG.timing.seekToBlack);
      $('screen-seek').style.transition = `opacity ${CONFIG.timing.fadeTransition}ms ease`;
      hideScreen('screen-seek');
      await delay(CONFIG.timing.blackToTemple);
      stateMachine.transition(CONFIG.states.TEMPLE);
      break;

    case CONFIG.states.TEMPLE:
      showScreen('screen-video');
      await delay(CONFIG.timing.templeDelay);
      video.showSlot('slot-1', 'video-temple');
      await video.waitForEnd('video-temple', CONFIG.timing.videoFallback);
      stateMachine.transition(CONFIG.states.APPEAR);
      break;

    // ── Безликий: Появление → Жизнь ──────────────
    case CONFIG.states.APPEAR: {
      const scene = CONFIG.scenes.bezliky;
      await video.playSequence(scene.intro, scene.loop);
      await delay(CONFIG.timing.loopToCapsule);
      stateMachine.transition(CONFIG.states.INPUT);
      break;
    }

    case CONFIG.states.INPUT: {
      // Проверяем — был ли человек раньше
      const ctx = memory.getBezlikyContext();

      // Безликий задаёт один вопрос — первый или повторный визит
      const bezlikyMsg = $('bezliky-message');
      if (bezlikyMsg) {
        bezlikyMsg.textContent = ctx?.isReturn
          ? 'Ты снова здесь. Что теперь?'
          : 'С чем ты здесь?';
        bezlikyMsg.classList.add('visible');
        console.log(`[Храм] Безликий: ${ctx?.isReturn ? 'повторный визит #' + ctx?.visits : 'первый визит'}`);
      }

      addScreen('screen-input');
      await delay(CONFIG.timing.capsuleFocus);
      $('answer')?.focus();
      break;
    }

    // ── Костёр ────────────────────────────────────
    case CONFIG.states.FIRE: {
      hideScreen('screen-input');

      audio.fadeOut('ambient', 1500);

      // Запускаем видео костра (appear → loop) на video-слое
      const fireScene = CONFIG.scenes.fire;
      if (fireScene) {
        // Останавливаем предыдущую последовательность (Безликий)
        video.stopSequence();
        try {
          await video.playSequence(fireScene.intro, fireScene.loop, { muted: false });
        } catch (err) {
          console.warn('[Храм] Костёр: видео не загружено, продолжаем без него', err);
        }
      }

      // Показываем UI костра поверх видео
      addScreen('screen-fire');
      fire.init();
      fire.enter();
      await delay(500);
      $('fire-input')?.focus();
      break;
    }

    // ── Хранитель: видео + диалог ─────────────────
    case CONFIG.states.GUARDIAN: {
      hideScreen('screen-input');
      hideScreen('screen-fire');
      video.stopSequence();
      threshold.stop();

      const gId = data.guardianId;
      const gData = keywords.getGuardian(gId);
      if (!gData) break;

      // Фиксируем в памяти
      memory.recordGuardian(gId);

      // Имя и фраза
      const elName = $('guardian-name');
      const elPhrase = $('guardian-phrase');
      if (elName) elName.textContent = gData.name;
      if (elPhrase) elPhrase.textContent = gData.phrase;

      // Запускаем видео intro → loop
      const scene = CONFIG.scenes[gData.scene];
      if (scene) {
        showScreen('screen-video');
        try {
          await video.playSequence(scene.intro, scene.loop);
        } catch {
          console.log(`[Храм] ${gData.name}: видео не найдено, заглушка`);
        }
      }

      // Показываем UI хранителя поверх видео
      addScreen('screen-guardian');

      audio.crossfade('ambient', 'guardian', 2000);

      // Инициализируем диалог
      guardian.init();
      await guardian.enter(gId);
      await delay(500);
      $('guardian-input')?.focus();
      break;
    }

    // ── Выпуск: 15с тишины → release → release_loop → Свиток → уйти ──
    case CONFIG.states.RELEASE: {
      const rId           = data.guardianId;
      const scrollPromise = data.scrollPromise;
      const rData         = keywords.getGuardian(rId);
      const rScene        = CONFIG.scenes[rData?.scene];

      // Блокируем ввод — диалог завершён
      const guardianInput = document.getElementById('guardian-input');
      if (guardianInput) guardianInput.disabled = true;

      audio.crossfade('guardian', 'release', 3000);

      // ── 15 секунд тишины ───────────────────────
      // Текст Хранителя остаётся поверх его loop-видео
      // Человек сидит с последними словами перед собой
      if (rScene?.releaseLoop) {
        video.preloadVideo(rScene.releaseLoop);
      }
      await delay(15000);

      // Теперь скрываем — прямо перед стартом release-видео
      hideScreen('screen-guardian');

      // ── release.mp4 → release_loop.mp4 ─────────
      // Оба перехода с 1.5с crossfade (opacity 0→1)
      if (rScene?.release) {
        try {
          await video.playSequence(
            rScene.release,
            rScene.releaseLoop,
            { crossfadeMs: 1500 }
          );
        } catch {
          console.log(`[Храм] ${rData?.name}: release видео не найдено`);
        }
      }

      // ── release_loop крутится бесконечно ───────
      // Ждём Свиток (синтез шёл всё это время параллельно)
      let scrollData = null;
      try {
        scrollData = scrollPromise ? await scrollPromise : null;
      } catch {
        scrollData = null;
      }

      // ── Свиток поверх release_loop ──────────────
      if (scrollData) {
        showScroll(scrollData, () => {
          stateMachine.transition(CONFIG.states.EXIT);
        });
      } else {
        // Синтез упал — идём на выход без Свитка
        stateMachine.transition(CONFIG.states.EXIT);
      }
      break;
    }

    // ── Выход (фолбэк без release-видео) ──────────
    case CONFIG.states.EXIT: {
      video.stopSequence();
      audio.fadeOut('release', 3000);
      showScreen('screen-exit');
      // Конец — никакого возврата, экран остаётся
      break;
    }
  }
});

// ── Обработка ввода Безликого ────────────────────

function handleBezlikyInput(text) {
  const clean = text.toLowerCase().trim();
  if (!clean) return;

  // ← ХРАМ SCROLL: фиксируем первое слово и настроение
  session.initialKey  = text;
  session.initialMood = detectMood(text);
  console.log(`[Храм] Сессия: initialKey="${text}", mood=${session.initialMood}`);

  // Скрываем сообщение Безликого если было
  const bezlikyMsg = $('bezliky-message');
  if (bezlikyMsg) bezlikyMsg.classList.remove('visible');

  // 1. Ключевые слова → сразу к хранителю
  const guardianId = keywords.detect(clean);
  if (guardianId) {
    stateMachine.transition(CONFIG.states.GUARDIAN, { guardianId });
    return;
  }

  // 2. Триггеры Костра
  if (keywords.isFireTrigger(clean)) {
    stateMachine.transition(CONFIG.states.FIRE);
    return;
  }

  // 3. Не распознано — к Костру, пусть поможет найти слово
  console.log('[Храм] Безликий: не распознано, направляю к Костру:', clean);
  stateMachine.transition(CONFIG.states.FIRE);
}

// ── Связка порога с Костром ──────────────────────

threshold.onTrigger = () => {
  fire.triggerThreshold();
};

// ── Инициализация ────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  initCursor();

  // Экран «ищи»
  setTimeout(() => $('seek-word')?.classList.add('appeared'), CONFIG.timing.seekFadeIn);

  // Клик → старт
  $('screen-seek')?.addEventListener('click', () => {
    stateMachine.transition(CONFIG.states.DARKNESS);
  }, { once: true });

  // Enter в поле Безликого
  $('answer')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const val = e.target.value.trim();
      e.target.value = '';
      if (val !== undefined) handleBezlikyInput(val);
    }
  });
});
