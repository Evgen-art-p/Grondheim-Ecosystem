# -*- coding: utf-8 -*-
# PRIYOMNAYA_ODIN_V_ODIN_V1
"""
ПРИЁМНАЯ СТУДИИ — один в один со старой.

CSS, разметка и мозги взяты из studio/reception/ui.py ДОСЛОВНО.
Изменено ровно два места:
    /workshop?dept=X&prompt=Y  →  /studia/{цех}?naryad=…
    /images/*.mp4              →  /priyomnaya_media/*.mp4

Цеха больше не из load_depts(), а от сканера города: блок «приёмная»
в манифесте каждого цеха Студии. Ключи те же (id, label, icon, color,
placeholder, suggest, keywords, priority) — чтобы старый JS работал
без правок.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from nicegui import ui, app

KOREN = Path(__file__).resolve().parent.parent
MEDIA = KOREN / "GRONDHEIM_CITY" / "Студия" / "приёмная"

try:
    MEDIA.mkdir(parents=True, exist_ok=True)
    app.add_static_files("/priyomnaya_media", str(MEDIA))
except Exception:
    pass


def load_depts() -> list:
    """Цеха Студии в том же виде, в каком их ждёт старый JS."""
    try:
        if str(KOREN / "ГОРОД") not in sys.path:
            sys.path.insert(0, str(KOREN / "ГОРОД"))
        import rabota
        vse = rabota.kartridzhi()
    except Exception:
        return []
    out = []
    for k in vse:
        if k.get("папка_квартала") != "Студия" or k.get("вид") == "контора":
            continue
        try:
            m = json.loads((Path(k["папка"]) / "manifest.json").read_text(
                encoding="utf-8"))
        except Exception:
            continue
        p = m.get("приёмная") or {}
        out.append({
            "id": k["цех"],
            "label": p.get("название", m.get("название", k["цех"])),
            "icon": p.get("значок", "🧩"),
            "color": p.get("цвет", "#00ccff"),
            "placeholder": p.get("приглашение", "Опишите задачу…"),
            "suggest": p.get("подсказка", "Открываю этот цех?"),
            "keywords": p.get("ключевые_слова", []),
            "priority": p.get("вес", 0),
        })
    out.sort(key=lambda d: -d["priority"])
    return out


CSS = r"""
    
      :root { --zoom: 1.40; }

      html, body { height: 100%; }
      body{
        margin:0;
        height:100vh;
        width:100vw;
        overflow:hidden !important;
        background: #000 !important;
      }
      #q-app, .q-layout, .q-page-container, .q-page{
        height:100vh !important;
        background: transparent !important;
      }

      /* ===== Video backdrop ===== */
      #video-backdrop{
        position: fixed; inset:0; z-index:0; overflow:hidden;
        background: #000;
      }
      #video-backdrop video{
        position:absolute; inset:0; width:100%; height:100%;
        object-fit: cover;
      }
      #video-logo{ z-index:3; }
      #video-intro{
        z-index:2;
        opacity: 0;
        transition: opacity .6s ease;
      }
      #video-intro.visible{ opacity: 1; }
      #video-loop{
        z-index:1;
        opacity: 0;
        transition: none;
      }
      #video-loop.visible{ opacity: 1; }

      /* ===== Enter button ===== */
      .enter-btn{
          position: fixed;
          left: 50%;
          top: 76%;
          transform: translateX(-50%);
          z-index: 50;

          display: inline-flex;
          align-items: center;
          gap: 8px;

          background: none;
          border: none;
          outline: none;
          cursor: pointer;

          font-family: inherit;
          font-size: 15px;
          font-weight: 300;
          letter-spacing: .08em;
          color: rgba(0, 0, 0, .75);

          opacity: 0;
          pointer-events: none;
          transition: opacity .6s ease, color .25s ease;
      }
      .enter-btn.visible{
          opacity: 1;
          pointer-events: auto;
      }
      .enter-btn:hover{
        color: rgba(0, 0, 0, .95);
      }
      .enter-btn .arrow{
        display: inline-block;
        transition: transform .25s ease;
      }
      .enter-btn:hover .arrow{
        transform: translateX(4px);
      }

      @keyframes soft-pulse{
        0%, 100%{ opacity: .55; }
        50%{ opacity: .85; }
      }
      .enter-btn.visible{
        animation: soft-pulse 2.8s ease-in-out infinite;
      }
      .enter-btn:hover{
        animation: none;
        opacity: 1;
      }

      /* ===== HUD ===== */
      .hud{
        position: fixed;
        z-index: 20;
        left: 50%;
        bottom: 15vh;
        width: min(720px, 90vw);
        transform: translateX(-50%) translateY(22px);
        pointer-events: none;
        opacity: 0;
        transition: transform .65s cubic-bezier(.2,.9,.2,1), opacity .65s ease;
      }
      body.hud-ready .hud{
        transform: translateX(-50%) translateY(0);
        pointer-events: auto;
        opacity: 1;
      }

      .hud_capsule{
        position: relative;
        display:flex;
        align-items:center;
        gap:10px;
        padding: 10px 12px 10px 18px;
        border-radius: 9999px;

        background: rgba(20, 20, 24, .22);
        border: 1px solid rgba(255,255,255,.14);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
      }

      .hud .q-field__control,
      .hud .q-field__native{ background: transparent !important; }
      .hud .q-field__control:before,
      .hud .q-field__control:after{ border-color: transparent !important; }
      .hud .q-field__native,
      .hud .q-field__native input{
        color: rgba(226,232,240,.78) !important;
        caret-color: rgba(226,232,240,.78) !important;
        font-weight: 500;
      }
      .hud .q-field__native input::placeholder{ color: rgba(226,232,240,.55) !important; }

      .hud_arrow, .hud_folder{
        width: 40px; height: 40px;
        border-radius: 12px;
        display:grid; place-items:center;
        cursor:pointer;
        background: rgba(0,0,0,.30);
        border: 1px solid rgba(255,255,255,.14);
      }
      .hud_arrow{ border-radius: 9999px; background: rgba(0,0,0,.35); border-color: rgba(255,255,255,.18); }
      .hud_arrow .q-icon, .hud_folder .q-icon{ color: rgba(226,232,240,.75) !important; }

      .hud_cabinet{
        width: 40px; height: 40px;
        border-radius: 12px;
        display:grid; place-items:center;
        cursor:pointer;
        background: rgba(108,140,255,.08);
        border: 1px solid rgba(108,140,255,.22);
        transition: all .25s ease;
        flex-shrink: 0;
      }
      .hud_cabinet:hover{
        background: rgba(108,140,255,.18);
        border-color: rgba(108,140,255,.40);
        box-shadow: 0 0 16px rgba(108,140,255,.15);
      }
      .hud_cabinet .q-icon{ color: rgba(108,140,255,.85) !important; font-size: 18px; }

      .hud.is-busy .hud_arrow, .hud.is-busy .hud_folder{ opacity: .45; pointer-events:none; }
      .hud.is-busy input{ pointer-events:none; }

      /* ===== Suggest ===== */
      .suggest_wrap{
        position: absolute;
        left: 0; right: 0;
        bottom: calc(100% + 10px);
        display:flex;
        justify-content:center;
        pointer-events:none;
      }
      .suggest_card{
        pointer-events:auto;
        width: min(520px, 92vw);
        border-radius: 16px;
        padding: 10px 12px;
        display:flex;
        align-items:center;
        justify-content: space-between;
        gap: 12px;
        background: rgba(20,20,24,.28);
        border: 1px solid rgba(255,255,255,.14);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        opacity: 0;
        transform: translateY(8px);
        transition: opacity .25s ease, transform .25s ease;
      }
      body.has-suggest .suggest_card{ opacity:1; transform: translateY(0); }
      .suggest_left{ display:flex; align-items:center; gap:10px; }
      .suggest_badge{
        width: 38px; height: 38px; border-radius: 14px;
        display:grid; place-items:center;
        border: 1px solid rgba(255,255,255,.18);
        background: rgba(0,0,0,.25);
        font-size: 18px;
      }
      .suggest_title{ color: rgba(226,232,240,.92); font-weight: 800; font-size: 12px; letter-spacing:.04em; }
      .suggest_sub{ color: rgba(226,232,240,.62); font-size: 12px; }
      .suggest_hint{ color: rgba(226,232,240,.55); font-size: 11px; white-space: nowrap; }

      /* ===== Deck ===== */
      .deck{
        position: fixed;
        left: 50%;
        transform: translateX(-50%) translateY(10px);
        bottom: calc(15vh + 74px);
        width: min(980px, 94vw);
        z-index: 40;

        background: rgba(10,10,14,.28);
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 18px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);

        padding: 12px;
        opacity: 0;
        pointer-events: none;
        transition: opacity .25s ease, transform .25s ease;
      }
      body.deck-open .deck{
        opacity: 1;
        transform: translateX(-50%) translateY(0);
        pointer-events: auto;
      }

      .deck_row{
        display:flex;
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 6px;
      }
      .deck_row::-webkit-scrollbar{ height: 8px; }
      .deck_row::-webkit-scrollbar-thumb{ background: rgba(255,255,255,.16); border-radius: 999px; }
      .deck_row{ scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.16) transparent; }

      .card{
        flex: 0 0 auto;
        width: 210px;
        border-radius: 16px;
        padding: 12px;
        cursor:pointer;
        border: 1px solid rgba(255,255,255,.12);
        background: rgba(0,0,0,.18);
        transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
      }
      .card:hover{ transform: translateY(-2px); }
      .card_top{ display:flex; align-items:center; justify-content: space-between; margin-bottom: 8px; }
      .card_icon{ font-size: 20px; }
      .card_label{ color: rgba(226,232,240,.9); font-weight: 800; font-size: 12px; letter-spacing:.04em; }
      .card_id{ color: rgba(226,232,240,.55); font-size: 11px; }

      /* ===== Manual Lock ===== */
      body.manual-lock .hud_folder{
        border-color: rgba(255,255,255,.22) !important;
        box-shadow: 0 0 26px rgba(255,255,255,.12);
        background: rgba(0,0,0,.42);
      }
      body.manual-lock .hud_arrow{ opacity: .55; filter: saturate(.7); }
      body.manual-lock .suggest_card{
        opacity: 0 !important;
        transform: translateY(8px) !important;
        pointer-events: none !important;
      }

      /* ===== pre-navigation transition ===== */
      body.nav-away .hud{
        opacity: 0;
        transition: opacity .35s ease;
      }
      body.nav-away #video-backdrop{
        filter: blur(18px) brightness(.6);
        transition: filter .35s ease;
      }
    """

VIDEO_HTML = r"""      <div id="video-backdrop">
        <video id="video-logo" muted playsinline preload="auto">
          <source src="/priyomnaya_media/logo.mp4" type="video/mp4">
        </video>
        <video id="video-intro" playsinline preload="auto">
          <source src="/priyomnaya_media/intro.mp4" type="video/mp4">
        </video>
        <video id="video-loop" muted playsinline preload="auto" loop>
          <source src="/priyomnaya_media/loop.mp4" type="video/mp4">
        </video>
      </div>

      <button id="enter-btn" class="enter-btn">
        войти <span class="arrow">&rarr;</span>
      </button>"""

JS = r"""    <script>
      let phase = 'logo';

      function initVideoSequencer(){
        const logo  = document.getElementById('video-logo');
        const intro = document.getElementById('video-intro');
        const loop  = document.getElementById('video-loop');
        const btn   = document.getElementById('enter-btn');
        if (!logo || !intro || !loop || !btn) return;

        logo.addEventListener('timeupdate', function(){
          if (logo.currentTime >= 6 && !btn.classList.contains('visible')){
            btn.classList.add('visible');
          }
        });

        logo.addEventListener('ended', function(){});

        btn.addEventListener('click', function(){
            btn.classList.remove('visible');
            btn.style.display = 'none';
            phase = 'intro';

            logo.style.transition = 'opacity .6s ease';
            logo.style.opacity = '0';

            setTimeout(() => {
                logo.style.display = 'none';
                intro.classList.add('visible');
                intro.play().catch(()=>{});

                loop.currentTime = 0;
                loop.play().then(() => {
                    loop.pause();
                    loop.currentTime = 0;
                    console.log('[video] loop preloaded');
                }).catch(()=>{});
            }, 650);
        });

        intro.addEventListener('timeupdate', function(){
          if (intro.currentTime >= 4 && !document.body.classList.contains('hud-ready')){
            document.body.classList.add('hud-ready');
          }
        });

        intro.addEventListener('ended', function(){
          phase = 'loop';
          intro.style.display = 'none';
          loop.currentTime = 0;
          loop.classList.add('visible');
          loop.play().catch(()=>{});
          console.log('[v4] hard switch done');
        });

        logo.play().catch(()=>{});
      }

      window.addEventListener('load', () => {
        initVideoSequencer();
        renderDeck();
        setTimeout(updatePlaceholder, 0);
      });

      const DEPTS = JSON.parse(document.getElementById('depts-data').textContent);
      const PLACEHOLDERS = Object.fromEntries(DEPTS.map(d => [d.id, d.placeholder]));

      window.currentDept = (DEPTS[0]?.id || '');
      window.manualLock = false;
      let currentSuggest = null;

      function getHudInput(){
        return document.querySelector('.hud .q-field__native input');
      }

      function updatePlaceholder(){
        const el = getHudInput();
        if (!el) return;
        el.placeholder = window.manualLock
          ? (PLACEHOLDERS[window.currentDept] || 'Режим включён. Опишите задачу...')
          : 'Чего желаете, Шеф?';
      }

      function smartPick(text){
        const t = (text || '').toLowerCase().trim();
        if (!t) return (DEPTS[0]?.id || '');
        let best = null;
        for (const d of DEPTS){
          const kws = d.keywords || [];
          let score = 0;
          for (const k of kws){
            if (!k) continue;
            if (t.includes(String(k).toLowerCase())) score += 1;
          }
          const candidate = {id: d.id, score, priority: (d.priority || 0)};
          if (!best) best = candidate;
          else {
            if (candidate.score > best.score) best = candidate;
            else if (candidate.score === best.score && candidate.priority > best.priority) best = candidate;
          }
        }
        if (!best || best.score === 0) return (DEPTS[0]?.id) || '';
        return best.id;
      }

      function setSuggest(deptId){
        const d = DEPTS.find(x => x.id === deptId);
        if (!d) return;
        currentSuggest = d;
        const badge = document.getElementById('suggest_badge');
        const title = document.getElementById('suggest_title');
        const sub   = document.getElementById('suggest_sub');
        if (!badge || !title || !sub) return;
        badge.textContent = d.icon;
        title.textContent = d.label;
        sub.textContent = d.suggest || 'Открываю этот цех?';
        document.body.classList.add('has-suggest');
      }

      function clearSuggest(){
        currentSuggest = null;
        document.body.classList.remove('has-suggest');
      }

      function acceptSuggest(){
        if (currentSuggest) goWorkspace(currentSuggest.id);
      }

      function toggleDeck(forceOpen){
        forceOpen = (forceOpen === undefined) ? null : forceOpen;
        const open = document.body.classList.contains('deck-open');
        const next = (forceOpen === null) ? !open : forceOpen;
        document.body.classList.toggle('deck-open', next);
      }

      function enableManualLock(deptId){
        window.manualLock = true;
        document.body.classList.add('manual-lock');
        window.currentDept = deptId;
        clearSuggest();
        updatePlaceholder();
      }

      function onPromptInput(text){
        if (window.manualLock) return;
        const dept = smartPick(text || '');
        window.currentDept = dept;
        setSuggest(dept);
      }

      function goWorkspace(deptId){
        enableManualLock(deptId);
        const prompt = (getHudInput()?.value || '').trim();
        document.body.classList.add('nav-away');
        setTimeout(() => {
          const url = '/studia/' + encodeURIComponent(deptId) + '?naryad=' + encodeURIComponent(prompt);
          window.location.href = url;
        }, 380);
      }

      function submitGo(){
        const prompt = (getHudInput()?.value || '').trim();
        if (!prompt) return;
        goWorkspace(window.currentDept);
      }

      function renderDeck(){
        const row = document.getElementById('dept_deck_row');
        if (!row) return;
        row.innerHTML = '';
        for (const d of DEPTS){
          const el = document.createElement('div');
          el.className = 'card';
          el.onmouseenter = () => {
            el.style.borderColor = d.color;
            el.style.boxShadow = '0 0 24px ' + d.color + '33';
          };
          el.onmouseleave = () => {
            el.style.borderColor = 'rgba(255,255,255,.12)';
            el.style.boxShadow = 'none';
          };
          el.onclick = () => goWorkspace(d.id);
          el.innerHTML = '<div class="card_top"><div class="card_icon">' + d.icon + '</div><div class="card_id">' + d.id + '</div></div><div class="card_label">' + d.label + '</div>';
          row.appendChild(el);
        }
      }

      window.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const inHud = active && active.tagName === 'INPUT' && active.closest('.hud');
        if (!inHud) return;
        if (e.key === 'Tab'){
          e.preventDefault();
          enableManualLock(window.currentDept);
          toggleDeck();
        }
        if (e.key === 'Enter'){
          if (document.body.classList.contains('has-suggest') && currentSuggest){
            e.preventDefault();
            acceptSuggest();
          }
        }
      });
    </script>"""


def page_priyomnaya() -> None:
    depts = load_depts()
    depts_js = json.dumps(depts, ensure_ascii=False)

    ui.add_head_html(f"""
    <script id="depts-data" type="application/json">
    {depts_js}
    </script>
    """)

    ui.add_head_html("<style>" + CSS + "</style>")
    ui.add_head_html(JS)

    ui.html(VIDEO_HTML)

    @ui.refreshable
    def hud():
        busy, set_busy = ui.state(False)

        with ui.element('div').classes('hud' + (' is-busy' if busy else '')):
            with ui.element('div').classes('hud_capsule'):

                ui.html("""
                  <div class="suggest_wrap" id="dept_suggest_wrap">
                    <div class="suggest_card" id="dept_suggest" onclick="acceptSuggest()">
                      <div class="suggest_left">
                        <div class="suggest_badge" id="suggest_badge">&#9889;</div>
                        <div>
                          <div class="suggest_title" id="suggest_title"></div>
                          <div class="suggest_sub" id="suggest_sub"></div>
                        </div>
                      </div>
                      <div class="suggest_hint">Enter &mdash; открыть &bull; Tab &mdash; выбор</div>
                    </div>
                  </div>
                """)

                cabinet_btn = ui.element('div').classes('hud_cabinet').props('title="Кабинет"')
                with cabinet_btn:
                    ui.icon('smart_toy')
                cabinet_btn.on('click', lambda: ui.navigate.to('/brat'))

                inp = ui.input(placeholder='Чего желаете, Шеф?').props('borderless dense').classes('w-full')
                inp.on('input', lambda e: ui.run_javascript(
                    f"onPromptInput({json.dumps(e.args or '', ensure_ascii=False)});"))

                folder = ui.element('div').classes('hud_folder')
                with folder:
                    ui.icon('folder_open')
                folder.on('click', lambda: ui.run_javascript(
                    'enableManualLock(window.currentDept); toggleDeck(true);'))

                arrow = ui.element('div').classes('hud_arrow')
                with arrow:
                    ui.icon('arrow_upward')

                def submit():
                    if busy:
                        return
                    text = (inp.value or '').strip()
                    if not text:
                        return
                    set_busy(True)
                    hud.refresh()
                    ui.run_javascript("submitGo();")
                    ui.timer(0.4, lambda: (set_busy(False), hud.refresh()), once=True)

                inp.on('keydown.enter', lambda _: submit())
                arrow.on('click', lambda _: submit())

        ui.html("""
          <div class="deck" id="dept_deck">
            <div class="deck_row" id="dept_deck_row"></div>
          </div>
        """)

    hud()
