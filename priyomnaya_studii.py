# -*- coding: utf-8 -*-
# PRIYOMNAYA_STUDII_V1
"""
ПАТЧ · Приёмная Студии — как в старой, только по-новому.

ЧТО КЛАДЁТ
    ГОРОД/ui_priyomnaya.py                    страница приёмной
    main.py                                   роут /priyomnaya
    ui_grondheim.py                           карта: Студия → приёмная
    Студия/цеха/турбо/manifest.json           блок «приёмная»
    Студия/приёмная/                          папка под видео

КАК В СТАРОЙ
    Видео-фон тремя слоями: логотип → заставка → петля. Кнопка «войти».
    Капсула «Чего желаете, Шеф?». Приёмная САМА угадывает цех по
    ключевым словам и предлагает карточкой: Enter — открыть. Папка —
    дека всех цехов, выбрать руками.

ЧТО ПО-НОВОМУ
    Список цехов не зашит. Приёмная спрашивает сканер города и берёт
    блок «приёмная» из манифеста каждого цеха: значок, название,
    подсказку, ключевые слова, вес. Появится второй цех — встанет в
    деку сам, кода не трогаем.

    В старой это лежало в studio/modules/{цех}/info.json и читалось
    через load_depts(). Тот же смысл, только теперь в манифесте, где
    и остальное про цех.

ПОЧЕМУ ПРИЁМНАЯ, А НЕ СРАЗУ ЦЕХ
    С карты Шеф входит в ЗДАНИЕ, а не за станок. В здании его встречает
    приёмщик — тот самый слот конторы, который берёт заказ и выдаёт
    наряд. Приёмная и есть его лицо наружу.

ВИДЕО
    Файлов в репо нет — они лежали локально. Кладёшь в
    GRONDHEIM_CITY/Студия/приёмная/ файлы logo.mp4, intro.mp4, loop.mp4 —
    оживёт. Нет файлов — тёмный фон, всё работает.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PRIYOMNAYA_STUDII_V1"

PRIYOMNAYA_MANIFEST = {
    "значок": "⚡",
    "название": "ТУРБО Шортсы",
    "цвет": "#ffb300",
    "подсказка": "Похоже на короткое вертикальное видео. Открываю ТУРБО?",
    "приглашение": "Опишите идею шортса…",
    "примеры": ["тренд для TikTok", "Reels для бизнеса",
                "вирусный YouTube Shorts"],
    "ключевые_слова": ["turbo", "турбо", "shorts", "шортс", "шорт",
                       "вертикал", "быстр", "рилс", "reels", "тикток",
                       "tiktok", "ролик", "видео"],
    "вес": 10,
}

STRANICA = r'''# -*- coding: utf-8 -*-
# PRIYOMNAYA_STUDII_V1
"""
ПРИЁМНАЯ СТУДИИ.

Вход в здание. Шеф говорит, чего хочет, — приёмная угадывает цех и
отправляет туда вместе со сказанным.

Списка цехов не держит: спрашивает сканер города, берёт из манифеста
блок «приёмная». Новый цех встаёт в деку сам.

    /priyomnaya

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


def ceha_studii() -> list:
    """Цеха Студии с их приёмными данными. Списка не держим."""
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
            "значок": p.get("значок", "🧩"),
            "цвет": p.get("цвет", "#8be9fd"),
            "название": p.get("название", m.get("название", k["цех"])),
            "подсказка": p.get("подсказка", "Открываю этот цех?"),
            "приглашение": p.get("приглашение", "Чего желаете, Шеф?"),
            "примеры": p.get("примеры", []),
            "слова": [str(x).lower() for x in p.get("ключевые_слова", [])],
            "вес": p.get("вес", 0),
        })
    out.sort(key=lambda d: -d["вес"])
    return out


def _est(imya: str) -> bool:
    return (MEDIA / imya).exists()


CSS = r"""
<style>
html,body{height:100%;}
body{margin:0; overflow:hidden !important; background:#05070a !important;}
#q-app,.q-layout,.q-page-container,.q-page{height:100vh !important;
  background:transparent !important;}
#p-fon{position:fixed; inset:0; z-index:0; overflow:hidden; background:#05070a;}
#p-fon video{position:absolute; inset:0; width:100%; height:100%;
  object-fit:cover;}
#p-logo{z-index:3;} 
#p-intro{z-index:2; opacity:0; transition:opacity .6s ease;}
#p-intro.vidno{opacity:1;}
#p-loop{z-index:1; opacity:0;}
#p-loop.vidno{opacity:1;}
#p-gradient{position:fixed; inset:0; z-index:4; pointer-events:none;
  background:radial-gradient(60% 50% at 50% 40%,
    rgba(0,0,0,0) 0%, rgba(0,0,0,0.55) 100%);}
.p-vhod{position:fixed; left:50%; top:74%; transform:translateX(-50%);
  z-index:50; background:none; border:none; cursor:pointer;
  color:rgba(255,255,255,0.9); font-size:1.05rem; letter-spacing:0.28em;
  text-transform:uppercase; font-weight:300;
  display:inline-flex; align-items:center; gap:10px;
  transition:all .3s;}
.p-vhod:hover{color:#8be9fd; gap:16px;}
body.p-voshli .p-vhod{opacity:0; pointer-events:none;}
.p-hud{position:fixed; left:50%; bottom:8%; transform:translateX(-50%);
  z-index:60; width:min(760px,92vw); opacity:0; pointer-events:none;
  transition:opacity .5s ease .2s;}
body.p-voshli .p-hud{opacity:1; pointer-events:auto;}
.p-caps{display:flex; align-items:center; gap:10px; padding:10px 14px;
  border-radius:18px; background:rgba(12,16,22,0.82);
  border:1px solid rgba(255,255,255,0.12);
  backdrop-filter:blur(14px); color:#e6edf3;}
.p-ico{width:34px; height:34px; border-radius:10px; flex-shrink:0;
  display:flex; align-items:center; justify-content:center; cursor:pointer;
  background:rgba(255,255,255,0.05);
  border:1px solid rgba(255,255,255,0.1); transition:all .2s;}
.p-ico:hover{border-color:rgba(139,233,253,0.6); color:#8be9fd;}
.p-sovet{position:absolute; left:0; right:0; bottom:64px;
  border-radius:16px; padding:12px 16px; cursor:pointer;
  background:rgba(12,16,22,0.9); border:1px solid rgba(139,233,253,0.35);
  backdrop-filter:blur(14px);
  display:none; align-items:center; gap:14px;}
body.p-sovet-est .p-sovet{display:flex;}
.p-sovet:hover{border-color:rgba(139,233,253,0.8);}
.p-sovet .z{font-size:1.5rem;}
.p-sovet .t{font-weight:700; font-size:0.92rem; color:#fff;}
.p-sovet .s{font-size:0.76rem; color:rgba(255,255,255,0.55);}
.p-sovet .h{margin-left:auto; font-size:0.66rem;
  color:rgba(255,255,255,0.3); white-space:nowrap;}
/* дека — ЛЕНТА карточек с прокруткой, как в старой */
.p-deka{position:absolute; left:0; right:0; bottom:64px;
  border-radius:18px; padding:12px;
  background:rgba(10,10,14,0.55);
  border:1px solid rgba(255,255,255,0.12); backdrop-filter:blur(14px);
  opacity:0; pointer-events:none; transform:translateY(10px);
  transition:opacity .25s ease, transform .25s ease;}
body.p-deka-est .p-deka{opacity:1; transform:translateY(0);
  pointer-events:auto;}
body.p-deka-est .p-sovet{display:none !important;}
.p-lenta{display:flex; gap:10px; overflow-x:auto; padding-bottom:6px;
  scrollbar-width:thin;
  scrollbar-color:rgba(255,255,255,.16) transparent;}
.p-lenta::-webkit-scrollbar{height:8px;}
.p-lenta::-webkit-scrollbar-thumb{background:rgba(255,255,255,.16);
  border-radius:999px;}
.p-karta{flex:0 0 auto; width:210px; border-radius:16px; padding:12px;
  cursor:pointer; border:1px solid rgba(255,255,255,.12);
  background:rgba(0,0,0,.24);
  transition:transform .15s ease, border-color .15s ease,
             box-shadow .15s ease;}
.p-karta:hover{transform:translateY(-2px);}
.p-karta .verh{display:flex; align-items:center;
  justify-content:space-between; margin-bottom:8px;}
.p-karta .z{font-size:20px;}
.p-karta .id{color:rgba(226,232,240,.55); font-size:11px;
  font-family:monospace;}
.p-karta .t{color:rgba(226,232,240,.9); font-weight:800; font-size:12px;
  letter-spacing:.04em;}
/* ручной выбор: угадывание молчит, папка горит, стрелка тускнеет */
body.p-ruchnoy .p-sovet{opacity:0 !important; pointer-events:none
  !important;}
body.p-ruchnoy .p-papka{border-color:rgba(255,255,255,.28) !important;
  box-shadow:0 0 22px rgba(255,255,255,.10);
  background:rgba(0,0,0,.42);}
body.p-ruchnoy .p-strelka{opacity:.55; filter:saturate(.7);}
/* уход со страницы */
body.p-uhodim .p-hud{opacity:0; transform:translateX(-50%)
  translateY(12px);}
body.p-uhodim #p-fon{filter:brightness(.5); transition:filter .35s ease;}
.p-nazv{position:fixed; left:50%; top:12%; transform:translateX(-50%);
  z-index:50; text-align:center; color:rgba(255,255,255,0.85);}
.p-nazv .b{font-size:1.5rem; font-weight:200; letter-spacing:0.42em;
  text-transform:uppercase;}
.p-nazv .m{font-size:0.68rem; letter-spacing:0.22em;
  color:rgba(139,233,253,0.6); margin-top:6px;}
</style>
"""


def page_priyomnaya():
    ui.add_head_html(CSS)
    ceha = ceha_studii()
    dannye = json.dumps(ceha, ensure_ascii=False)

    est_logo, est_intro, est_loop = (_est("logo.mp4"), _est("intro.mp4"),
                                     _est("loop.mp4"))

    video = '<div id="p-fon">'
    if est_logo:
        video += ('<video id="p-logo" muted playsinline preload="auto">'
                  '<source src="/priyomnaya_media/logo.mp4" '
                  'type="video/mp4"></video>')
    if est_intro:
        video += ('<video id="p-intro" playsinline preload="auto">'
                  '<source src="/priyomnaya_media/intro.mp4" '
                  'type="video/mp4"></video>')
    if est_loop:
        video += ('<video id="p-loop" muted playsinline preload="auto" loop>'
                  '<source src="/priyomnaya_media/loop.mp4" '
                  'type="video/mp4"></video>')
    video += '</div><div id="p-gradient"></div>'
    ui.html(video)

    ui.html('<div class="p-nazv"><div class="b">Шесть Пальцев</div>'
            '<div class="m">приёмная студии</div></div>')

    ui.html('<button class="p-vhod" onclick="voyti()">'
            'войти <span>&rarr;</span></button>')

    # ── капсула ──────────────────────────────────────────────
    with ui.element("div").classes("p-hud"):
        ui.html("""
          <div class="p-sovet" onclick="prinyat()">
            <div class="z" id="s-z">⚡</div>
            <div>
              <div class="t" id="s-t"></div>
              <div class="s" id="s-s"></div>
            </div>
            <div class="h">Enter — открыть · Tab — выбрать</div>
          </div>
          <div class="p-deka"><div class="p-lenta" id="p-lenta"></div></div>
        """)
        with ui.element("div").classes("p-caps"):
            kab = ui.element("div").classes("p-ico").tooltip("Кабинет Брата")
            with kab:
                ui.icon("smart_toy")
            kab.on("click", lambda: ui.navigate.to("/brat"))

            pole = ui.input(placeholder="Чего желаете, Шеф?").props(
                "borderless dense dark").classes("w-full").style(
                "font-size:0.92rem;")
            pole.on("input", lambda e: ui.run_javascript(
                f"nabral({json.dumps(e.args or '', ensure_ascii=False)});"))
            pole.on("keydown.tab", lambda: ui.run_javascript(
                "ruchnoy(vybran && vybran.id); deka();"))

            papka = ui.element("div").classes("p-ico p-papka").tooltip(
                "Все цеха · Tab")
            with papka:
                ui.icon("folder_open")
            papka.on("click", lambda: ui.run_javascript(
                "ruchnoy(vybran && vybran.id); deka();"))

            strelka = ui.element("div").classes("p-ico p-strelka").tooltip(
                "Открыть")
            with strelka:
                ui.icon("arrow_upward")
            strelka.on("click", lambda: ui.run_javascript("prinyat();"))

            pole.on("keydown.enter", lambda: ui.run_javascript("prinyat();"))

    # ── мозги приёмной ───────────────────────────────────────
    ui.add_body_html(f"""
    <script>
    const CEHA = {dannye};
    const PRIGLASHENIYA = Object.fromEntries(
        CEHA.map(c => [c.id, c.приглашение]));
    let vybran = CEHA.length ? CEHA[0] : null;
    let ruchnoyRezhim = false;

    function pole(){{
      return document.querySelector('.p-caps input');
    }}

    function priglashenie(){{
      const el = pole();
      if (!el) return;
      el.placeholder = ruchnoyRezhim
        ? (PRIGLASHENIYA[vybran && vybran.id] || 'Режим включён. Опишите задачу…')
        : 'Чего желаете, Шеф?';
    }}

    /* ЛЕНТА рисуется СРАЗУ при загрузке, а не по первому открытию */
    function narisovatDeku(){{
      const lenta = document.getElementById('p-lenta');
      if (!lenta) return;
      lenta.innerHTML = '';
      for (const c of CEHA){{
        const el = document.createElement('div');
        el.className = 'p-karta';
        el.onmouseenter = () => {{
          el.style.borderColor = c.цвет;
          el.style.boxShadow = '0 0 24px ' + c.цвет + '33';
        }};
        el.onmouseleave = () => {{
          el.style.borderColor = 'rgba(255,255,255,.12)';
          el.style.boxShadow = 'none';
        }};
        el.onclick = () => otkryt(c);
        el.innerHTML = '<div class="verh"><div class="z">' + c.значок
          + '</div><div class="id">' + c.id + '</div></div>'
          + '<div class="t">' + c.название + '</div>';
        lenta.appendChild(el);
      }}
    }}

    function voyti(){{
      document.body.classList.add('p-voshli');
      const intro = document.getElementById('p-intro');
      const loop  = document.getElementById('p-loop');
      if (intro) {{
        intro.classList.add('vidno');
        intro.play().catch(()=>{{}});
        intro.onended = () => {{
          if (loop) {{ loop.classList.add('vidno');
                       loop.play().catch(()=>{{}}); }}
        }};
      }} else if (loop) {{
        loop.classList.add('vidno'); loop.play().catch(()=>{{}});
      }}
      setTimeout(()=>{{ const i = pole(); if (i) i.focus(); }}, 400);
      pokazat(vybran);
    }}

    function ugadat(t){{
      t = (t || '').toLowerCase().trim();
      if (!t) return CEHA[0] || null;
      let luchshiy = null;
      for (const c of CEHA){{
        let ochki = 0;
        for (const k of (c.слова || [])) if (k && t.includes(k)) ochki += 1;
        const kand = {{c: c, ochki: ochki, ves: c.вес || 0}};
        if (!luchshiy) luchshiy = kand;
        else if (kand.ochki > luchshiy.ochki) luchshiy = kand;
        else if (kand.ochki === luchshiy.ochki && kand.ves > luchshiy.ves)
          luchshiy = kand;
      }}
      if (!luchshiy || luchshiy.ochki === 0) return CEHA[0] || null;
      return luchshiy.c;
    }}

    function pokazat(c){{
      if (!c || ruchnoyRezhim) {{
        document.body.classList.remove('p-sovet-est'); return;
      }}
      vybran = c;
      document.getElementById('s-z').textContent = c.значок;
      document.getElementById('s-t').textContent = c.название;
      document.getElementById('s-s').textContent = c.подсказка;
      document.body.classList.add('p-sovet-est');
    }}

    /* ручной выбор: угадывание молчит, приглашение — цеховое */
    function ruchnoy(id){{
      ruchnoyRezhim = true;
      document.body.classList.add('p-ruchnoy');
      const c = CEHA.find(x => x.id === id);
      if (c) vybran = c;
      document.body.classList.remove('p-sovet-est');
      priglashenie();
    }}

    function nabral(t){{
      if (ruchnoyRezhim) return;
      pokazat(ugadat(t || ''));
    }}

    function deka(prinuditelno){{
      const est = document.body.classList.contains('p-deka-est');
      const nado = (prinuditelno === undefined) ? !est : !!prinuditelno;
      document.body.classList.toggle('p-deka-est', nado);
    }}

    /* уходим плавно, как в старой: 380 мс и переход */
    function otkryt(c){{
      if (!c) return;
      ruchnoy(c.id);
      const i = pole();
      const skazano = ((i && i.value) || '').trim();
      document.body.classList.add('p-uhodim');
      setTimeout(() => {{
        window.location.href = '/studia/' + encodeURIComponent(c.id)
          + (skazano ? ('?naryad=' + encodeURIComponent(skazano)) : '');
      }}, 380);
    }}

    function prinyat(){{
      const i = pole();
      const skazano = ((i && i.value) || '').trim();
      if (!skazano && !ruchnoyRezhim) return;
      otkryt(vybran || ugadat(skazano));
    }}

    document.addEventListener('keydown', (e) => {{
      const a = document.activeElement;
      const v_kapsule = a && a.tagName === 'INPUT' && a.closest('.p-hud');
      if (e.key === 'Escape') {{ deka(false); return; }}
      if (!v_kapsule) return;
      if (e.key === 'Tab'){{
        e.preventDefault();
        ruchnoy(vybran && vybran.id);
        deka();
      }}
      if (e.key === 'Enter'){{
        if (document.body.classList.contains('p-sovet-est') && vybran){{
          e.preventDefault(); otkryt(vybran);
        }}
      }}
    }});

    window.addEventListener('load', () => {{
      narisovatDeku();
      setTimeout(priglashenie, 0);
      const logo = document.getElementById('p-logo');
      if (logo) logo.play().catch(()=>{{}});
    }});
    </script>
    """)
'''


def _teper() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def naiti_koren() -> Path:
    starty = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starty:
        for kand in [start, *start.parents]:
            if (kand / "GRONDHEIM_CITY" / "локации").is_dir() \
                    and (kand / "ГОРОД" / "rabota.py").is_file():
                return kand
    raise SystemExit("Не нашёл корень репо. Запусти из корня "
                     "Grondheim-Ecosystem.")


M_STAR = '''from ui_studia import page_studia

@ui.page("/studia/{ceh}")'''

M_NOV = '''# ── ПРИЁМНАЯ СТУДИИ (PRIYOMNAYA_STUDII_V1) ──
# Вход в здание с карты. Угадывает цех по сказанному и отправляет туда.
from ui_priyomnaya import page_priyomnaya

@ui.page("/priyomnaya")
def _priyomnaya():
    page_priyomnaya()

from ui_studia import page_studia

@ui.page("/studia/{ceh}")'''

G_STAR = '''    "0015_GRONDHEIM_ARCHIVE": "/arkhiv",  # Архив -> кабинет Хранителя (ui_arkhiv.py)
}'''

G_NOV = '''    "0015_GRONDHEIM_ARCHIVE": "/arkhiv",  # Архив -> кабинет Хранителя (ui_arkhiv.py)
    # PRIYOMNAYA_STUDII_V1: с карты входим в ЗДАНИЕ, а не за станок.
    # В здании встречает приёмщик — он и решит, в какой цех.
    "0001_STUDIO_SIX_FINGERS": "/priyomnaya",
}'''


def patchit(put: Path, star: str, nov: str) -> str:
    if not put.exists():
        return f"нет {put.name}"
    t = put.read_text(encoding="utf-8")
    if MARKER in t:
        return "уже пропатчен, не трогал"
    if t.count(star) != 1:
        return f"якорь встречается {t.count(star)} раз — не рискую"
    shutil.copyfile(put, put.with_suffix(put.suffix + f".bak_{_teper()}"))
    put.write_text(t.replace(star, nov, 1), encoding="utf-8")
    return "пропатчен, .bak рядом"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")

    # страница
    put = koren / "ГОРОД" / "ui_priyomnaya.py"
    if put.exists() and put.read_text(encoding="utf-8") == STRANICA:
        print("Приёмная: уже стоит")
    else:
        if put.exists():
            shutil.copyfile(put, put.with_suffix(f".py.bak_{_teper()}"))
        put.write_text(STRANICA, encoding="utf-8")
        print(f"Приёмная: положена ({len(STRANICA.splitlines())} строк)")

    import py_compile
    try:
        py_compile.compile(str(put), doraise=True)
        print("Компилируется: да")
    except Exception as e:
        print(f"НЕ КОМПИЛИРУЕТСЯ: {e}")
        return

    print("main.py:  " + patchit(koren / "main.py", M_STAR, M_NOV))
    print("карта:    " + patchit(koren / "ГОРОД" / "ui_grondheim.py",
                                 G_STAR, G_NOV))

    # блок «приёмная» в манифест цеха
    mf = koren / "GRONDHEIM_CITY" / "Студия" / "цеха" / "турбо" / "manifest.json"
    if mf.exists():
        m = json.loads(mf.read_text(encoding="utf-8"))
        if "приёмная" in m:
            print("манифест: блок «приёмная» уже есть")
        else:
            m["приёмная"] = PRIYOMNAYA_MANIFEST
            m["_note_приёмная"] = (
                "чем цех представляется в приёмной: значок, название, "
                "подсказка, ключевые слова для угадывания, вес при "
                "равном счёте. В старой студии это лежало в info.json "
                "цеха и читалось через load_depts()."
            )
            shutil.copyfile(mf, mf.with_suffix(f".json.bak_{_teper()}"))
            mf.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
            print("манифест: блок «приёмная» вписан")

    # папка под видео
    media = koren / "GRONDHEIM_CITY" / "Студия" / "приёмная"
    media.mkdir(parents=True, exist_ok=True)
    est = [f for f in ("logo.mp4", "intro.mp4", "loop.mp4")
           if (media / f).exists()]
    print(f"\nВидео в {media.relative_to(koren)}: "
          + (", ".join(est) if est else "нет — фон будет тёмный"))

    # что увидит приёмная
    sys.path.insert(0, str(koren / "ГОРОД"))
    spec_put = koren / "ГОРОД" / "ui_priyomnaya.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("_pr", spec_put)
    try:
        import types
        fake = types.ModuleType("nicegui")

        class _E:
            def __init__(s, *a, **k): pass
            def __getattr__(s, n): return s
            def __call__(s, *a, **k): return s
            def __enter__(s): return s
            def __exit__(s, *a): return False
        fake.ui = _E(); fake.app = _E()
        sys.modules["nicegui"] = fake
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        ceha = mod.ceha_studii()
        print("\nЦеха, которые увидит приёмная:")
        for c in ceha:
            print(f"  {c['значок']} {c['название']:<16} слов "
                  f"{len(c['слова'])}, вес {c['вес']}  → /studia/{c['id']}")
        if not ceha:
            print("  — ни одного")
    except Exception as e:
        print(f"\nне проверил список цехов: {e}")

    print("\nГотово. Перезапусти приложение.\n"
          "  Брат → ГРОНДХЕЙМ (карта) → клик по Студии → приёмная\n"
          "  скажи, чего хочешь → Enter. Tab — все цеха.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
