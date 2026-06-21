// ═══════════════════════════════════════
// СВИТОК СМЫСЛА — Отображение и Capture
// ═══════════════════════════════════════

// ───────────────────────────────────────
// Иконки алтарей
// ───────────────────────────────────────
const ALTAR_ICONS = {
  fire:  '🔥',
  earth: '🌍',
  air:   '💨',
  water: '💧',
  void:  '🌑'
};

const ALTAR_COLORS = {
  fire:  { hue: 20,  saturation: 1.3, brightness: 1.1 },
  earth: { hue: 40,  saturation: 1.0, brightness: 0.9 },
  air:   { hue: 200, saturation: 0.8, brightness: 1.2 },
  water: { hue: 220, saturation: 1.2, brightness: 1.0 },
  void:  { hue: 270, saturation: 0.6, brightness: 0.7 }
};

// ───────────────────────────────────────
// Применить атмосферу к фону
// ───────────────────────────────────────
function applyAtmosphere(warmth, intensity) {
  const hue = Math.round(200 - warmth * 200);
  const brightness = (0.7 + intensity * 0.5).toFixed(2);
  const saturation = (0.8 + warmth * 0.4).toFixed(2);
  const filter = `hue-rotate(${hue}deg) brightness(${brightness}) saturate(${saturation})`;

  // Ищем фоновое видео по классу (адаптируй под реальный id/class своего проекта)
  const bg = document.querySelector('.temple-bg-video') 
          || document.querySelector('#video-temple')
          || document.querySelector('video');
  if (bg) {
    bg.style.transition = 'filter 3s ease';
    bg.style.filter = filter;
  }
}

// ───────────────────────────────────────
// Показать Свиток
// ───────────────────────────────────────

/**
 * @param {Object} scrollData - результат ear-agent.synthesizeScroll()
 * @param {Function} onExit - вызывается когда человек уходит из Свитка
 */
export function showScroll(scrollData, onExit) {
  const { scroll, visual_tuning, meta } = scrollData;
  const altar = meta.chosen_altar;
  const icon = ALTAR_ICONS[altar] || '✦';
  const scrollType = meta.scroll_type; // chalice | sword

  // Применяем атмосферу
  applyAtmosphere(visual_tuning.warmth, visual_tuning.intensity);

  // Создаём оверлей
  const overlay = document.createElement('div');
  overlay.id = 'scroll-overlay';
  overlay.className = `scroll-overlay scroll-type-${scrollType} scroll-altar-${altar}`;

  overlay.innerHTML = `
    <div class="scroll-container" id="scroll-capture-zone">

      <!-- Печать алтаря -->
      <div class="scroll-seal">
        <span class="scroll-seal-icon">${icon}</span>
        <span class="scroll-seal-name">${scroll.gift.altar_name}</span>
      </div>

      <!-- Суть -->
      <div class="scroll-block scroll-essence">
        <p>${scroll.essence}</p>
      </div>

      <!-- Дар Алтаря -->
      <div class="scroll-block scroll-gift">
        <div class="scroll-gift-label">дар алтаря</div>
        <div class="scroll-gift-tool">${scroll.gift.target_tool}</div>
        <div class="scroll-prompt-wrapper">
          <pre class="scroll-prompt" id="scroll-prompt-text">${scroll.gift.prompt}</pre>
          <button class="scroll-copy-btn" id="scroll-copy-btn" title="Скопировать">
            <span id="scroll-copy-label">скопировать</span>
          </button>
        </div>
        <div class="scroll-lia-word">«${scroll.gift.lia_word}»</div>
      </div>

      <!-- Связь -->
      <div class="scroll-block scroll-bridge">
        <p>${scroll.bridge}</p>
      </div>

      <!-- Эхо -->
      <div class="scroll-block scroll-echo">
        <p>${scroll.echo}</p>
      </div>

    </div>

    <!-- Действия -->
    <div class="scroll-actions">
      <button class="scroll-btn scroll-btn-capture" id="scroll-capture-btn">
        забрать в мир
      </button>
      <button class="scroll-btn scroll-btn-exit" id="scroll-exit-btn">
        уйти
      </button>
    </div>
  `;

  document.body.appendChild(overlay);

  // Анимация появления
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      overlay.classList.add('scroll-visible');
    });
  });

  // Скопировать промпт
  document.getElementById('scroll-copy-btn').addEventListener('click', () => {
    const text = scroll.gift.prompt;
    navigator.clipboard.writeText(text).then(() => {
      const label = document.getElementById('scroll-copy-label');
      label.textContent = 'скопировано ✓';
      setTimeout(() => { label.textContent = 'скопировать'; }, 2000);
    });
  });

  // Забрать в мир — скачать PNG
  document.getElementById('scroll-capture-btn').addEventListener('click', () => {
    captureScroll();
  });

  // Уйти
  document.getElementById('scroll-exit-btn').addEventListener('click', () => {
    overlay.classList.remove('scroll-visible');
    overlay.classList.add('scroll-hiding');
    setTimeout(() => {
      overlay.remove();
      if (typeof onExit === 'function') onExit();
    }, 800);
  });
}

// ───────────────────────────────────────
// Capture — скачать Свиток как PNG
// ───────────────────────────────────────
async function captureScroll() {
  const captureBtn = document.getElementById('scroll-capture-btn');
  captureBtn.textContent = 'создаём...';
  captureBtn.disabled = true;

  try {
    // Загружаем html2canvas если не подключён
    if (typeof html2canvas === 'undefined') {
      await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
    }

    const zone = document.getElementById('scroll-capture-zone');
    const canvas = await html2canvas(zone, {
      backgroundColor: '#0a0a0a',
      scale: 2,
      useCORS: true,
      logging: false
    });

    const link = document.createElement('a');
    link.download = `scroll_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();

    captureBtn.textContent = 'сохранено ✓';
    setTimeout(() => {
      captureBtn.textContent = 'забрать в мир';
      captureBtn.disabled = false;
    }, 2000);

  } catch (e) {
    console.error('[СВИТОК] Ошибка capture:', e);
    captureBtn.textContent = 'ошибка, попробуй снова';
    captureBtn.disabled = false;
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

// ───────────────────────────────────────
// Показать заглушку пока Ухо-Агент думает
// ───────────────────────────────────────
export function showScrollLoading() {
  const overlay = document.createElement('div');
  overlay.id = 'scroll-loading';
  overlay.className = 'scroll-loading-overlay';
  overlay.innerHTML = `
    <div class="scroll-loading-inner">
      <div class="scroll-loading-orb"></div>
      <p class="scroll-loading-text">Храм ткёт твой Свиток...</p>
    </div>
  `;
  document.body.appendChild(overlay);
  requestAnimationFrame(() => requestAnimationFrame(() => overlay.classList.add('visible')));
}

export function hideScrollLoading() {
  const overlay = document.getElementById('scroll-loading');
  if (overlay) {
    overlay.classList.remove('visible');
    setTimeout(() => overlay.remove(), 600);
  }
}
