/**
 * ХРАМ — Управление видео
 *
 * Главный принцип: старое видео убирается ТОЛЬКО когда
 * первый кадр нового уже нарисован на экране.
 * Никакого чёрного промежутка.
 */

class VideoManager {
  constructor() {
    this._prev     = null;  // предыдущий loop — живёт пока новый не готов
    this._v1       = null;
    this._v2       = null;
    this._preloads = {};
  }

  // ── Базовые ────────────────────────────────────

  showSlot(slotId, videoId) {
    document.querySelectorAll('.video-slot').forEach(s => s.classList.remove('visible'));
    document.getElementById(slotId)?.classList.add('visible');
    const vid = document.getElementById(videoId);
    if (vid) { vid.currentTime = 0; vid.play().catch(() => {}); }
  }

  waitForEnd(videoId, fallbackMs = 10000) {
    return new Promise(resolve => {
      const vid = document.getElementById(videoId);
      if (!vid) return resolve();
      vid.addEventListener('ended', resolve, { once: true });
      setTimeout(resolve, fallbackMs);
    });
  }

  stopAll() { this.stopSequence(); }

  // ── Прелоад ────────────────────────────────────

  preloadVideo(src) {
    if (this._preloads[src]) return;
    const v = this._makeEl(src, false);
    v.style.cssText = 'position:fixed;width:0;height:0;opacity:0;pointer-events:none;';
    document.body.appendChild(v);
    v.load();
    this._preloads[src] = v;
    console.log('[Видео] preload:', src);
  }

  // ── playSequence ───────────────────────────────

  playSequence(introSrc, loopSrc, opts = {}) {
    const crossfadeMs = opts.crossfadeMs ?? 1500;
    const muted = opts.muted ?? true; // false для костра — своя дорожка
    const container   = document.querySelector('.video-container');
    if (!container) return Promise.reject(new Error('[Видео] .video-container не найден'));

    // Сохраняем текущий loop как prev — он останется видим пока не придёт замена
    const prevEl = this._v2 || this._v1 || null;
    if (prevEl && prevEl.parentNode !== container) {
      // prev уже не в контейнере — игнорируем
    }

    // Убираем старый v1 если был (intro уже не нужен)
    if (this._v1 && this._v1 !== prevEl) {
      this._v1.pause();
      if (this._v1.parentNode) this._v1.parentNode.removeChild(this._v1);
    }
    this._v1 = null;
    this._v2 = null;

    return new Promise((resolve, reject) => {

      const v1 = this._take(introSrc, false, muted);
      const v2 = this._take(loopSrc,  true,  muted);

      // Стили: оба поверх prevEl, v1 пока невидим
      const baseStyle = `position:absolute;inset:0;width:100%;height:100%;object-fit:cover;`;
      v1.style.cssText = baseStyle + 'z-index:3;opacity:0;';
      v2.style.cssText = baseStyle + 'z-index:4;opacity:0;';

      // prev остаётся на z-index:2 (или как был)
      if (prevEl) prevEl.style.zIndex = '2';

      container.appendChild(v1);
      container.appendChild(v2);
      this._v1 = v1;

      // ── Ждём первый кадр v1 ─────────────────────
      const INTRO_FADE = 800; // мс — плавный вход release поверх guardian loop

      const onV1Ready = () => {
        // v1 готов — плавно проявляем его поверх prevEl
        v1.play().catch(err => { console.warn('[Видео] v1 play failed:', err); reject(err); });

        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            v1.style.transition = `opacity ${INTRO_FADE}ms ease`;
            v1.style.opacity    = '1';

            // Убираем prevEl после завершения fade
            setTimeout(() => {
              if (prevEl && prevEl.parentNode) {
                prevEl.pause();
                prevEl.parentNode.removeChild(prevEl);
              }
            }, INTRO_FADE + 50);

            // ── Следим за концом v1 → crossfade ───
            let crossfadeStarted = false;
            const PREROLL = crossfadeMs / 1000 + 0.05;

            const startCrossfade = () => {
              if (crossfadeStarted) return;
              crossfadeStarted = true;
              this._crossfade(v1, v2, crossfadeMs, () => {
                this._v1 = null;
                this._v2 = v2;
                resolve();
              });
            };

            const onTime = () => {
              if (v1.duration > 0 && (v1.duration - v1.currentTime) <= PREROLL) {
                v1.removeEventListener('timeupdate', onTime);
                startCrossfade();
              }
            };
            v1.addEventListener('timeupdate', onTime);
            v1.addEventListener('ended', () => {
              v1.removeEventListener('timeupdate', onTime);
              startCrossfade();
            }, { once: true });
            setTimeout(() => { v1.removeEventListener('timeupdate', onTime); startCrossfade(); }, 60000);
          });
        });
      };

      if (v1.readyState >= 3) {
        onV1Ready();
      } else {
        const onReady = () => { clearTimeout(fb); onV1Ready(); };
        v1.addEventListener('canplay', onReady, { once: true });
        const fb = setTimeout(() => { v1.removeEventListener('canplay', onReady); onV1Ready(); }, 2000);
        v1.load();
      }
    });
  }

  stopSequence() {
    [this._v1, this._v2].forEach(v => {
      if (!v) return;
      v.pause();
      if (v.parentNode) v.parentNode.removeChild(v);
    });
    this._v1 = null;
    this._v2 = null;
  }

  // ── Приватные ──────────────────────────────────

  _crossfade(v1, v2, ms, callback) {
    v2.currentTime = 0;
    v2.play().catch(() => {});

    const doFade = () => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          v2.style.transition = `opacity ${ms}ms ease`;
          v2.style.opacity    = '1';
        });
      });
      setTimeout(() => {
        v1.pause();
        if (v1.parentNode) v1.parentNode.removeChild(v1);
        if (callback) callback();
      }, ms + 100);
    };

    if (v2.readyState >= 3) {
      doFade();
    } else {
      v2.addEventListener('canplay', doFade, { once: true });
      setTimeout(doFade, 400);
    }
  }

  _makeEl(src, loop, muted = true) {
    const v = document.createElement('video');
    v.src         = src;
    v.preload     = 'auto';
    v.muted       = muted;
    v.playsInline = true;
    v.loop        = loop;
    return v;
  }

  _take(src, loop, muted = true) {
    if (this._preloads[src]) {
      const v = this._preloads[src];
      delete this._preloads[src];
      v.loop  = loop;
      v.muted = muted;
      v.style.cssText = '';
      console.log('[Видео] из кэша:', src);
      return v;
    }
    console.log('[Видео] новый:', src);
    return this._makeEl(src, loop, muted);
  }
}

export const video = new VideoManager();
