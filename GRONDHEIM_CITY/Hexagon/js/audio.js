/**
 * ХРАМ — Аудио
 *
 * Три зацикленных слоя + оригинальная дорожка видео:
 *
 *  'ambient'   — Порог + Безликий  (loop)
 *  'guardian'  — Хранители         (loop)
 *  'release'   — Свиток + Выход    (loop)
 *  video       — Костёр            (оригинальная дорожка mp4, не здесь)
 *
 * Использование:
 *   audio.play('ambient')            // запустить слой
 *   audio.fadeOut('ambient', 2000)   // плавно убрать за 2с
 *   audio.crossfade('ambient', 'guardian', 2000) // плавный переход
 *   audio.stopAll()
 */

class AudioManager {
  constructor() {
    // Пути к файлам — задаются через audio.setSources()
    this._sources = {
      ambient:  null,   // mp3/ogg для Порога и Безликого
      guardian: null,   // mp3/ogg для Хранителей
      release:  null,   // mp3/ogg для Свитка и Выхода
    };

    // Активные AudioContext и узлы
    this._ctx     = null;
    this._layers  = {};   // name → { source, gainNode, buffer }
    this._volumes = {
      ambient:  0.6,
      guardian: 0.5,
      release:  0.4,
    };
  }

  // ── Настройка ───────────────────────────────────

  /**
   * Задать пути к аудиофайлам.
   * Вызвать один раз в начале, до play().
   *
   * audio.setSources({
   *   ambient:  'audio/ambient.mp3',
   *   guardian: 'audio/guardian.mp3',
   *   release:  'audio/release.mp3',
   * });
   */
  setSources(sources) {
    this._sources = { ...this._sources, ...sources };
  }

  /**
   * Загрузить и декодировать все файлы заранее.
   * Вызывать сразу после setSources — тогда play() будет мгновенным.
   */
  async preloadAll() {
    // AudioContext требует user gesture — создаём заранее но не играем
    // Файлы качаются и декодируются в кэш
    try {
      await this._ensureCtx();
      await Promise.all(
        Object.entries(this._sources)
          .filter(([, src]) => src)
          .map(([name, src]) =>
            this._load(src)
              .then(() => console.log('[Аудио] прелоад готов:', name))
              .catch(err => console.warn('[Аудио] прелоад ошибка:', name, err))
          )
      );
    } catch {
      // AudioContext может не создаться до user gesture — ничего страшного,
      // файлы загрузятся при первом play()
    }
  }

  // ── Публичное API ───────────────────────────────

  /**
   * Запустить слой с фейдом
   * @param {string} name      — 'ambient' | 'guardian' | 'release'
   * @param {number} fadeInMs  — длительность нарастания (default: 1500)
   */
  async play(name, fadeInMs = 1500) {
    await this._ensureCtx();
    if (this._layers[name]) return; // уже играет

    const src = this._sources[name];
    if (!src) { console.warn('[Аудио] нет источника для:', name); return; }

    try {
      const buffer = await this._load(src);
      if (this._layers[name]) return; // параллельный вызов успел раньше

      const gainNode = this._ctx.createGain();
      gainNode.gain.setValueAtTime(0, this._ctx.currentTime);
      gainNode.connect(this._ctx.destination);

      const source = this._ctx.createBufferSource();
      source.buffer = buffer;
      source.loop   = true;
      source.connect(gainNode);
      source.start();

      // Плавное нарастание
      gainNode.gain.linearRampToValueAtTime(
        this._volumes[name] ?? 0.5,
        this._ctx.currentTime + fadeInMs / 1000
      );

      this._layers[name] = { source, gainNode };
      console.log('[Аудио] play:', name);
    } catch (err) {
      console.warn('[Аудио] ошибка загрузки:', name, err);
    }
  }

  /**
   * Плавно убрать слой
   * @param {string} name
   * @param {number} fadeOutMs
   */
  fadeOut(name, fadeOutMs = 1500) {
    const layer = this._layers[name];
    if (!layer) return;

    const { source, gainNode } = layer;
    const now = this._ctx.currentTime;

    gainNode.gain.setValueAtTime(gainNode.gain.value, now);
    gainNode.gain.linearRampToValueAtTime(0, now + fadeOutMs / 1000);

    setTimeout(() => {
      try { source.stop(); } catch {}
      gainNode.disconnect();
      delete this._layers[name];
      console.log('[Аудио] fadeOut done:', name);
    }, fadeOutMs + 100);
  }

  /**
   * Плавный переход между двумя слоями
   * @param {string} fromName
   * @param {string} toName
   * @param {number} ms
   */
  async crossfade(fromName, toName, ms = 2000) {
    this.fadeOut(fromName, ms);
    await this.play(toName, ms);
  }

  /**
   * Установить громкость слоя
   * @param {string} name
   * @param {number} value  — 0..1
   * @param {number} rampMs — время изменения
   */
  setVolume(name, value, rampMs = 500) {
    const layer = this._layers[name];
    if (!layer) { this._volumes[name] = value; return; }
    const now = this._ctx.currentTime;
    layer.gainNode.gain.setValueAtTime(layer.gainNode.gain.value, now);
    layer.gainNode.gain.linearRampToValueAtTime(value, now + rampMs / 1000);
    this._volumes[name] = value;
  }

  /** Остановить всё мгновенно */
  stopAll() {
    Object.keys(this._layers).forEach(name => {
      const { source, gainNode } = this._layers[name];
      try { source.stop(); } catch {}
      gainNode.disconnect();
    });
    this._layers = {};
  }

  // ── Приватные ───────────────────────────────────

  async _ensureCtx() {
    if (this._ctx) return;
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();
    // Браузер требует user gesture — если suspended, resume при первом вызове
    if (this._ctx.state === 'suspended') {
      await this._ctx.resume();
    }
  }

  _cache = {};

  async _load(src) {
    if (this._cache[src]) return this._cache[src];
    const res    = await fetch(src);
    const arr    = await res.arrayBuffer();
    const buffer = await this._ctx.decodeAudioData(arr);
    this._cache[src] = buffer;
    return buffer;
  }
}

export const audio = new AudioManager();
