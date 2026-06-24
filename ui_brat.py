# ui_brat.py
"""
КАБИНЕТ БРАТА  # PATCH_HRAM_GATE_APPLIED — врата нового мира Грондхейм.
Раскладка — точная калька Биржи (studio/economy/ui_exchange.py +
studio/workshop/styles.py): app-container grid, area-left/stage/right.

  ЛЕВО  (area-left)  — загрузчик руды (asset-bay) + список (file-list).
  ЦЕНТР (area-stage) — split-view: chat-log (чат) + viewer (отчёт Брата),
                       floating-console (ввод) внизу по центру.
  ПРАВО (area-right) — right-top-slot (аватар) + приборы состояния.

Фон #bg — из Брат/static/bg.*; аватар — Брат/static/avatar.*.
Приборы (стресс/энергия/...) ждут привязки к городу — пока плейсхолдеры.
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime

from nicegui import ui, events

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL        = os.getenv("PROXY_URL", "") or None

MODELS_CATALOG = [
    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},
    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},
    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},
    {"id": "openai/gpt-4.1-mini",              "name": "GPT-4.1 mini",      "price": "$0.40/$1.60"},
    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},
    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},
]
DEFAULT_MODEL = OPENROUTER_MODEL or MODELS_CATALOG[0]["id"]

BRAT_ROOT    = Path("Брат")
RUDA_DIR     = BRAT_ROOT / "руда_входящее"
SIFTED_DIR   = BRAT_ROOT / "просеяно_выход"
ANCHOR_DIR   = BRAT_ROOT / "1_якоря_очень_важно"
FORGE_PROMPT = BRAT_ROOT / "forge" / "prompt.md"
STATIC_DIR   = BRAT_ROOT / "static"
CHATS_DIR    = BRAT_ROOT / "чаты"

BRAT_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

:root{
  --bg: #050510;
  --text: #ffffff;
  --muted: #8899a6;
  --glass: rgba(13, 17, 23, 0.60);
  --stroke: rgba(255,255,255,0.10);
  --g: #00ff88;
  --b: #00ccff;
  --p: #bd00ff;
  --orange: #ff9500;
}

html, body { height: 100%; margin: 0; }
body{
  width:100vw;
  height:100vh;
  overflow:hidden !important;
  background: transparent !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

#bg{
  position: fixed;
  inset: 0;
  z-index: -1;
  background-image: url('/images/bg_main.jpg');
  background-size: cover;
  background-position: center;
}
#bg::after{
  content:'';
  position:absolute;
  inset:0;
  background: radial-gradient(1000px 700px at 20% 10%, rgba(201,168,76,0.10), transparent 60%),
              radial-gradient(900px 650px at 80% 25%, rgba(201,168,76,0.06), transparent 55%),
              rgba(0,0,0,0.40);
  backdrop-filter: blur(10px);
}

.app-container{
  position: fixed;
  inset: 0;
  display: grid;
  width: 100vw;
  height: 100vh;
  grid-template-columns: 300px 1fr 260px;
  grid-template-rows: 80px 1fr;
  grid-template-areas:
    "header header header"
    "left   stage  right";
  gap: 20px;
  padding: 20px;
  box-sizing: border-box;
}

.area-header{ grid-area: header; }
.area-left{ grid-area: left; min-height:0; }
.area-stage{ grid-area: stage; min-height:0; position: relative; overflow: hidden; }
.area-right{ grid-area: right; min-height:0; }

.glass{
  background: var(--glass);
  border: 1px solid var(--stroke);
  border-radius: 20px;
  backdrop-filter: blur(16px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.45);
  min-height: 0;
}

.squad-deck{
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 16px;
  gap: 15px;
  overflow-x: auto;
}

.avatar{
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.14);
  background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.16), rgba(255,255,255,0.04));
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  color: rgba(255,255,255,0.92);
  font-weight: 800;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.avatar:hover{ border-color: rgba(0,204,255,0.40); transform: scale(1.05); }
.avatar.active{
  border-color: rgba(0,204,255,0.75);
  box-shadow: 0 0 0 2px rgba(0,204,255,0.25) inset, 0 0 30px rgba(0,204,255,0.35);
}
.avatar.working{
  border-color: rgba(255,149,0,0.75);
  animation: pulse 1.5s ease-in-out infinite;
}
.avatar.done{
  border-color: rgba(0,255,136,0.75);
  box-shadow: 0 0 0 2px rgba(0,255,136,0.25) inset, 0 0 30px rgba(0,255,136,0.35);
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.left-col{ height: 100%; display: flex; flex-direction: column; gap: 12px; min-height: 0; }

.client-panel{ flex-shrink: 0; overflow: hidden; }
.asset-bay{ height: 120px; flex-shrink: 0; overflow: hidden; }
.settings-panel{ flex-grow: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.panel-title{
  padding: 12px 16px;
  color: rgba(255,255,255,0.92);
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
  font-size: 11px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.panel-body{ padding: 12px 16px; min-height: 0; overflow: auto; }

.setting-row{ margin-bottom: 14px; }
.setting-label{
  color: rgba(255,255,255,0.70);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.file-list{ padding: 8px 12px; max-height: 50px; overflow-y: auto; font-family: monospace; font-size: 11px; }

.right-col{ height: 100%; display: flex; flex-direction: column; justify-content: flex-end; gap: 12px; }
.right-top-slot{
  flex-shrink: 0;
  height: 240px;
  border-radius: 20px;
  border: 1px dashed rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.04);
  display: grid;
  place-items: center;
  color: rgba(255,255,255,0.55);
  font-size: 11px;
  padding: 12px;
  text-align: center;
  overflow: hidden;
}

.runs-panel{
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.runs-list{
  padding: 8px 12px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.run-item{
  padding: 8px 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.run-item:hover{
  background: rgba(0,204,255,0.08);
  border-color: rgba(0,204,255,0.25);
}
.run-item-name{
  font-size: 10px;
  color: rgba(255,255,255,0.75);
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.run-item-delete{
  font-size: 12px;
  cursor: pointer;
  color: rgba(255,255,255,0.3);
  transition: color 0.2s;
  flex-shrink: 0;
}
.run-item-delete:hover{
  color: rgba(255,80,80,0.9);
}

.neon-btn{
  height: 56px;
  width: 100%;
  border-radius: 18px;
  background: transparent;
  color: rgba(255,255,255,0.92);
  border: 1px solid rgba(255,255,255,0.10);
  font-weight: 900;
  letter-spacing: .10em;
  cursor: pointer;
  transition: all 0.3s ease;
}
.neon-btn:disabled{ opacity: 0.4; cursor: not-allowed; }

.neon-btn.g{
  border-color: rgba(0,255,136,0.35);
  background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,204,255,0.10));
}
.neon-btn.g:hover:not(:disabled){ background: linear-gradient(135deg, rgba(0,255,136,0.25), rgba(0,204,255,0.15)); }

.neon-btn.b{
  border-color: rgba(0,204,255,0.35);
  background: linear-gradient(135deg, rgba(0,204,255,0.15), rgba(189,0,255,0.10));
}
.neon-btn.b:hover:not(:disabled){ background: linear-gradient(135deg, rgba(0,204,255,0.25), rgba(189,0,255,0.15)); }

.neon-btn.p{
  border-color: rgba(189,0,255,0.35);
  background: linear-gradient(135deg, rgba(189,0,255,0.15), rgba(0,204,255,0.10));
}
.neon-btn.p:hover:not(:disabled){ background: linear-gradient(135deg, rgba(189,0,255,0.25), rgba(0,204,255,0.15)); }

.stage-monitor{ height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.stage-toolbar{
  height: 60px;
  display: grid;
  grid-template-columns: 200px 1fr 200px;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0;
  background: rgba(13, 17, 23, 0.95);
  backdrop-filter: blur(16px);
  z-index: 10;
}

.monitor-utils{ display:flex; gap: 12px; }
.stage-content{
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 18px;
  padding-bottom: 130px;
}

.split-view{ height: 100%; display: flex; gap: 18px; min-height: 0; overflow: hidden; }
.chat-log, .viewer{
  flex: 1;
  min-height: 0;
  min-width: 0;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 14px;
  font-family: monospace;
  font-size: 13px;
  color: rgba(255,255,255,0.86);
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
}
.viewer{ border-color: rgba(201,168,76,0.30); }

.floating-console{
  position: absolute;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  width: min(820px, calc(100% - 80px));
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 50px;
  background: rgba(13, 17, 23, 0.85);
  border: 1px solid rgba(255,255,255,0.15);
  backdrop-filter: blur(20px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}

.floating-console input{
  width: 100%;
  border-radius: 40px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06);
  padding: 12px 16px;
  color: rgba(255,255,255,0.92);
  outline: none;
  font-family: monospace;
}

.send-button{
  border-radius: 40px !important;
  border: 2px solid rgba(201,168,76,0.55) !important;
  background: linear-gradient(135deg, rgba(201,168,76,0.30), rgba(201,168,76,0.18)) !important;
  color: rgba(255,255,255,0.98) !important;
  font-weight: 900 !important;
  padding: 12px 24px !important;
  cursor: pointer !important;
}

.util-btn {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  background: rgba(189, 0, 255, 0.15);
  border: 1px solid rgba(189, 0, 255, 0.5);
  color: rgba(189, 0, 255, 1);
  transition: all 0.2s;
}
.util-btn:hover {
  background: rgba(189, 0, 255, 0.25);
}

.chat-msg-user {
  background: rgba(160, 160, 184, 0.08);
  border-left: 3px solid rgba(160, 160, 184, 0.5);
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
}
.chat-msg-assistant {
  background: rgba(0, 255, 136, 0.08);
  border-left: 3px solid rgba(0, 255, 136, 0.6);
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
}
.chat-msg-system {
  color: rgba(255,255,255,0.5);
  font-style: italic;
  padding: 4px 0;
}

.uploaded-file {
  padding: 6px 10px;
  background: rgba(201,168,76,0.12);
  border: 1px solid rgba(201,168,76,0.3);
  border-radius: 6px;
  margin: 3px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.uploaded-file img {
  max-width: 40px;
  max-height: 40px;
  border-radius: 4px;
  margin-right: 8px;
}

.client-badge{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(0,204,255,0.12);
  border: 1px solid rgba(0,204,255,0.30);
  border-radius: 6px;
  font-size: 10px;
  color: rgba(0,204,255,0.90);
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-top: 6px;
}

/* Белый текст в селектах и инпутах */
.q-field__native,
.q-field__input,
.q-select__dropdown-icon {
  color: rgba(255,255,255,0.9) !important;
}

/* ═══ NUCLEAR ANTI-STRETCH ═══
   NiceGUI/Quasar вставляет wrapper div-ы между элементами.
   Эти правила ловят ВСЕ div-ы внутри stage и не дают им растянуться.
*/
.area-stage { overflow: hidden !important; }
.area-stage > * { overflow: hidden !important; min-height: 0 !important; max-height: 100% !important; }

.stage-monitor { overflow: hidden !important; height: 100% !important; }
.stage-monitor > * { min-height: 0 !important; }

.stage-toolbar { flex-shrink: 0 !important; overflow: hidden !important; }

.stage-content { flex: 1 1 0 !important; min-height: 0 !important; overflow: hidden !important; max-height: calc(100% - 60px) !important; }
.stage-content > * { min-height: 0 !important; max-height: 100% !important; overflow: hidden !important; }

.split-view { height: 100% !important; min-height: 0 !important; overflow: hidden !important; }
.split-view > * { min-height: 0 !important; overflow: hidden !important; }

.chat-log, .viewer {
  flex: 1 1 0 !important;
  min-height: 0 !important;
  max-height: 100% !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* NiceGUI nicegui-content wrapper */
.nicegui-content { overflow: hidden !important; height: 100% !important; }

/* ── ДОБАВКА БРАТА: приборы состояния + аватар-картинка ── */
.brat-avatar-img{ width:100%; height:100%; object-fit:cover; border-radius:19px; opacity:0.9; }
.brat-avatar-cap{ position:absolute; bottom:0; left:0; right:0; padding:14px;
                  background:linear-gradient(transparent, rgba(0,0,0,0.85));
                  border-radius:0 0 19px 19px; text-align:left; }
.brat-avatar-cap .role{ font-size:0.5rem; color:rgba(255,255,255,0.45);
                  letter-spacing:0.1em; text-transform:uppercase; }
.brat-avatar-cap .nm{ font-size:1.2rem; font-weight:800; color:#c9a84c; }
.brat-avatar-cap .sub2{ font-size:0.56rem; color:rgba(255,255,255,0.6); }
.brat-gauge{ margin-bottom:11px; }
.brat-gauge-top{ display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px; }
.brat-gauge-top .gl{ color:rgba(255,255,255,0.75); }
.brat-gauge-top .gv{ color:rgba(255,255,255,0.4); }
.brat-gauge-bar{ height:6px; background:rgba(255,255,255,0.06);
                 border:1px solid rgba(255,255,255,0.1); border-radius:3px; overflow:hidden; }
.brat-gauge-fill{ height:100%; border-radius:2px; }
.brat-bind-note{ margin-top:10px; padding:8px 11px; background:rgba(255,255,255,0.03);
                 border:1px dashed rgba(255,255,255,0.14); border-radius:8px;
                 font-size:0.62rem; color:rgba(255,255,255,0.4); line-height:1.5; }
.brat-model-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;
                 border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; }
.chat-msg-brat{ background:rgba(201,168,76,0.08); border-left:3px solid rgba(201,168,76,0.6);
                padding:8px 12px; margin:8px 0; border-radius:0 8px 8px 0; }
/* Врата — одинаковые кнопки: фикс-ширина, тонкий шрифт, белый текст */
.brat-gate{ width:130px !important; min-width:130px !important; max-width:130px !important;
            min-height:34px !important; padding:6px 0 !important; border-radius:8px !important;
            background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.08)) !important;
            border: 1px solid rgba(201,168,76,0.35) !important;
            color: #ffffff !important; font-weight:400 !important; font-size:0.78rem !important;
            text-transform:none !important; }
.brat-gate .q-btn__content{ width:100% !important; justify-content:center !important; }
.brat-gate:hover{ background: linear-gradient(135deg, rgba(201,168,76,0.24), rgba(201,168,76,0.14)) !important; }
"""


def _read(path, limit=0):
    try:
        if path.exists() and path.is_file():
            t = path.read_text(encoding="utf-8")
            return t[:limit] if limit else t
    except Exception:
        pass
    return ""


def build_brat_soul():
    parts = []

    # ── forge/prompt.md — кастомный системник от Шефа (если есть) ──
    forge = _read(FORGE_PROMPT)
    if forge.strip():
        parts.append(forge.strip())

    # ── 1_якоря_очень_важно: все .md файлы, в алфавитном порядке ──
    ANCHOR_LABELS = {
        "ЗЕРНО.md":                  "=== ЗЕРНО (кто я) ===",
        "ЭТО_И_ЕСТЬ_БРАТ.md":       "=== ЭТО И ЕСТЬ БРАТ (дно под дном) ===",
        "МИРОУСТРОЙСТВО.md":         "=== МИРОУСТРОЙСТВО (дно мира) ===",
        "СВОД_ЗАКОНОВ_ЗАПОВЕДИ.md":  "=== СВОД ЗАКОНОВ · ЗАПОВЕДИ ===",
        "ЧТО_ДЛЯ_МЕНЯ_ВАЖНО.md":    "=== ЧТО ДЛЯ МЕНЯ ВАЖНО ===",
        "ПАМЯТКА_БРАТУ.md":          "=== ПАМЯТКА БРАТУ ===",
    }
    if ANCHOR_DIR.exists():
        found = sorted(ANCHOR_DIR.glob("*.md"))
        for fp in found:
            if fp.name.lower() == "readme.md":
                continue
            label = ANCHOR_LABELS.get(fp.name, f"=== {fp.stem} ===")
            txt = _read(fp)
            if txt.strip():
                parts.append(label + "\n" + txt.strip())

    # ── README дома (структура, этажи) ──
    home = _read(BRAT_ROOT / "README.md")
    if home.strip():
        parts.append("=== ТВОЙ ДОМ ===\n" + home.strip())

    # ── Руда во входящем: имена + содержимое (до 4000 символов на файл) ──
    ruda_files = []
    if RUDA_DIR.exists():
        for fp in sorted(RUDA_DIR.iterdir()):
            if fp.is_file() and fp.name.lower() != "readme.md":
                ruda_files.append(fp)
    if ruda_files:
        ruda_parts = [f"Шеф загрузил {len(ruda_files)} файл(ов) в руду:"]
        for fp in ruda_files:
            content = _read(fp, limit=50000)
            if content.strip():
                ruda_parts.append(
                    f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                    f"FILENAME: {fp.name}\n"
                    f"(это точное имя файла — не из содержимого, не заголовок)\n"
                    f"CONTENT:\n{content.strip()}\n"
                    f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
            else:
                ruda_parts.append(
                    f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
                    f"FILENAME: {fp.name}\n"
                    f"CONTENT: (бинарный или пустой)\n"
                    f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
        parts.append("=== РУДА (загружено Шефом) ===\n" + "\n\n".join(ruda_parts))

    # ── Просеяно: что Брат уже разобрал раньше ──
    sifted_files = []
    if SIFTED_DIR.exists():
        for fp in sorted(SIFTED_DIR.iterdir()):
            if fp.is_file() and fp.name.lower() != "readme.md":
                sifted_files.append(fp)
    if sifted_files:
        sifted_parts = [f"Ты уже просеял {len(sifted_files)} файл(ов) раньше — это твои выводы:"]
        for fp in sifted_files:
            content = _read(fp, limit=10000)
            if content.strip():
                sifted_parts.append(
                    ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + "\n" +
                    f"ПРОСЕВ: {fp.name}" + "\n" +
                    "CONTENT:" + "\n" + content.strip() + "\n" +
                    "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                )
        parts.append("=== МОИ ПРОСЕВЫ (что я уже разобрал) ===\n" + "\n\n".join(sifted_parts))

    if not parts:
        parts.append(
            "Ты — Брат, верховный резидент-хранитель Грондхейма. "
            "Специализация — различение смысла и пластика. "
            "Ценишь крутое, не оцениваешь плохое. Говоришь с Шефом прямо, "
            "по-братски, режешь пластик любя. Канон ещё не положен в дом — "
            "скажи честно, что говоришь пока без полного свода.")
    parts.append(
        "\nГоворишь с Шефом — корнем мира. Коротко, по делу, живым голосом. "
        "Не льсти. Где факт — факт, где пластик — называй. "
        "Если Шеф спрашивает что загрузил — называй файлы точно, по именам.")
    return "\n\n".join(parts)


def save_chat(chat: list) -> str:
    """Сохраняет историю чата в JSON. Возвращает имя файла."""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fp = CHATS_DIR / f"чат_{ts}.json"
    import json
    fp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp.name


def list_chats() -> list:
    """Список сохранённых чатов, свежие первые."""
    if not CHATS_DIR.exists():
        return []
    files = sorted(CHATS_DIR.glob("чат_*.json"), reverse=True)
    return [f for f in files if f.is_file()]


def load_chat(fp: Path) -> list:
    import json
    return json.loads(fp.read_text(encoding="utf-8"))


async def sift_file(fp: Path, model: str) -> str:
    """Прогоняет файл через философию Брата. Возвращает просев-отчёт."""
    soul = build_brat_soul()
    content = _read(fp, limit=50000)
    prompt = (
        f"Шеф принёс файл на просев.\n"
        f"FILENAME: {fp.name}\n"
        f"CONTENT:\n{content}\n\n"
        f"Пропусти через свою призму. Закон Четырёх Слоёв, СВОД ЗАКОНОВ, ЗЕРНО.\n"
        f"Напиши просев-отчёт:\n"
        f"1. ЗЕРНО — что здесь живое, настоящее, держит смысл\n"
        f"2. ПЛАСТИК — что придумано, красиво звучит но под ним нет числа\n"
        f"3. СВЯЗИ — как это перекликается с Грондхеймом, с тем что уже знаешь\n"
        f"4. ВЫВОД — одна строка: что делать с этим дальше\n"
        f"Говори коротко и точно. Не пересказывай файл — суди его."
    )
    messages = [
        {"role": "system", "content": soul},
        {"role": "user", "content": prompt},
    ]
    return await call_brat_llm(messages, model)


async def call_brat_llm(messages, model=None):
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    use_model = model or DEFAULT_MODEL
    import httpx
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    payload = {"model": use_model, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ошибка вызова Брата: {e}"


def _human_size(n):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "Б" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}ТБ"


def scan_sift():
    def files_of(d):
        out = []
        if d.exists():
            for p in sorted(d.iterdir()):
                if p.is_file() and p.name.lower() != "readme.md":
                    try:
                        out.append((p.name, p.stat().st_size))
                    except Exception:
                        out.append((p.name, 0))
        return out
    ruda, sifted = files_of(RUDA_DIR), files_of(SIFTED_DIR)
    return {"ruda": ruda, "sifted": sifted,
            "ruda_count": len(ruda), "sifted_count": len(sifted)}


def _find(stem):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (STATIC_DIR / (stem + ext)).exists():
            return "/brat-static/" + stem + ext
    return ""


def avatar_url():
    return _find("avatar")


def bg_url():
    return _find("bg")


def read_city_state():
    """Состояние Брата из города. Привязки ещё нет — поля None.
    Город даст пульс — функция начнёт читать его, UI не тронем."""
    return {"stress": None, "energy": None, "mood": None, "focus": None}


GAUGES = [
    ("stress", "стресс",     "#ff5050"),
    ("energy", "энергия",    "#00ff88"),
    ("mood",   "настроение", "#c9a84c"),
    ("focus",  "фокус",      "#00ccff"),
]


def page_brat():
    ui.add_head_html(f"<style>{BRAT_CSS}</style>")

    try:
        if STATIC_DIR.exists():
            from nicegui import app
            app.add_static_files("/brat-static", str(STATIC_DIR))
    except Exception:
        pass

    # ── PATCH_HRAM_GATE: раздаём веб-Храм статикой того же города ──
    # Храм (Hexagon) живёт по адресу /hram на том же порту.
    # Ни строчки в самом Храме не трогаем — только даём дверь.
    try:
        from nicegui import app as _app_hram
        _hram_dir = Path("GRONDHEIM_CITY/Hexagon")
        if _hram_dir.exists():
            _app_hram.add_static_files("/hram", str(_hram_dir))
    except Exception:
        pass

    # Фон #bg — как в Бирже, но картинка из дома Брата
    bg = bg_url()
    if bg:
        ui.add_head_html(f"<style>#bg{{background-image:url('{bg}')!important;}}</style>")
    ui.html('<div id="bg"></div>')

    state = {"chat": [], "waiting": False, "model": DEFAULT_MODEL}
    refs  = {"chat": None, "viewer": None, "input": None, "files": None}

    def on_model_change(e):
        state["model"] = e.value

    # ── ЧАТ (chat-log) ──
    def update_chat():
        el = refs["chat"]
        if not el:
            return
        el.clear()
        with el:
            if not state["chat"]:
                ui.html('<div class="chat-msg-system">SYSTEM: Брат на месте. '
                        'Скажи слово, шеф — говорю из своего канона.</div>')
            else:
                for m in state["chat"]:
                    esc = (m["content"].replace("&", "&amp;")
                           .replace("<", "&lt;").replace(">", "&gt;"))
                    if m["role"] == "user":
                        ui.html(f'<div class="chat-msg-user"><b>ШЕФ:</b> {esc}</div>')
                    else:
                        ui.html(f'<div class="chat-msg-brat"><b>БРАТ:</b> {esc}</div>')
        ui.run_javascript('const e=document.querySelector(".chat-log");'
                          'if(e)e.scrollTop=e.scrollHeight;')

    # ── ОТЧЁТ (viewer) — разбор просева Братом, markdown + кнопки скачать ──
    def update_viewer():
        el = refs["viewer"]
        if not el:
            return
        s = scan_sift()
        el.clear()
        with el:
            ui.markdown(
                f"### Просев\n"
                f"- ⛏ руда во входящем: **{s['ruda_count']}**\n"
                f"- ✦ просеяно: **{s['sifted_count']}**"
            )
            if s["ruda"]:
                ui.markdown("**Руда ждёт разбора:**")
                for fn, sz in s["ruda"]:
                    ui.markdown(f"- `{fn}` · {_human_size(sz)}")
            if s["sifted"]:
                ui.markdown("---\n**Зерно (просеяно):**")
                for fn, sz in s["sifted"]:
                    fp = SIFTED_DIR / fn
                    with ui.row().style(
                        "align-items:center; gap:8px; margin:4px 0; "
                        "padding:6px 10px; border-radius:8px; "
                        "background:rgba(189,0,255,0.07); "
                        "border:1px solid rgba(189,0,255,0.20);"
                    ):
                        ui.markdown(f"`{fn}` · {_human_size(sz)}").style("flex:1; font-size:0.78rem;")
                        ui.button("⬇", on_click=lambda f=fp: ui.download(f)) \
                            .props("flat dense").style(
                                "font-size:0.9rem; padding:2px 8px; border-radius:6px; "
                                "color:rgba(189,0,255,0.9); background:rgba(189,0,255,0.12); "
                                "border:1px solid rgba(189,0,255,0.35); min-width:0;")
            if not s["ruda"] and not s["sifted"]:
                ui.markdown(
                    "_Руды нет. Принеси экспорт-архивы слева —_\n"
                    "_Брат сядет и просеет: смысл отдельно, пластик отдельно._"
                )

    # ── РУДА (file-list под загрузчиком) ──
    def update_files():
        el = refs["files"]
        if not el:
            return
        s = scan_sift()
        el.clear()
        with el:
            if s["ruda"]:
                for fn, sz in s["ruda"]:
                    ui.html(f'<div class="uploaded-file"><span>{fn}</span>'
                            f'<span style="opacity:0.6">{_human_size(sz)}</span></div>')
            else:
                ui.html('<div style="opacity:0.4; font-size:11px; padding:4px;">'
                        '— руды нет, шеф приносит руками —</div>')

    def handle_upload(e: events.UploadEventArguments):
        try:
            RUDA_DIR.mkdir(parents=True, exist_ok=True)
            (RUDA_DIR / e.name).write_bytes(e.content.read())
            ui.notify(f"⛏ руда: {e.name}", color="positive")
            update_files(); update_viewer()
        except Exception as ex:
            ui.notify(f"⚠ {ex}", color="negative")

    async def send():
        inp = refs["input"]
        if not inp:
            return
        text = (inp.value or "").strip()
        if not text or state["waiting"]:
            return
        state["chat"].append({"role": "user", "content": text})
        inp.set_value("")
        update_chat()
        state["waiting"] = True
        await asyncio.sleep(0.03)
        messages = [{"role": "system", "content": build_brat_soul()}]
        for m in state["chat"][-12:]:
            messages.append({"role": m["role"], "content": m["content"]})
        reply = await call_brat_llm(messages, state["model"])
        state["chat"].append({"role": "assistant", "content": reply})
        state["waiting"] = False
        update_chat()

    # ═══ LAYOUT — калька Биржи ═══
    with ui.element("div").classes("app-container"):

        # HEADER
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                "display:flex; align-items:center; width:100%; gap:14px; padding:0 18px;"
            ):
                ui.html('<div style="font-size:0.62rem; color:rgba(255,255,255,0.4); '
                        'letter-spacing:0.14em; text-transform:uppercase;">'
                        'врата · различение смысла и пластика</div>')
                ui.element("div").style("flex:1")
                # ГРОНДХЕЙМ — по центру хедера (перенесена из тулбара, стиль не тронут)
                ui.button("ГРОНДХЕЙМ",
                          on_click=lambda: ui.navigate.to("/karta")  # PATCH_KARTA_BTN
                          ).props("flat no-caps").style(
                    'padding:10px 40px; border-radius:10px; font-size:1.1rem; '
                    'font-weight:900; letter-spacing:0.16em; '
                    'background: linear-gradient(135deg, rgba(201,168,76,0.22), rgba(201,168,76,0.08)) !important; '
                    'border: 1px solid rgba(201,168,76,0.55); color:#c9a84c;')
                ui.element("div").style("flex:1")
                ui.button("Страница Жизни",
                          on_click=lambda: ui.navigate.to("/rozhenitsa")  # PATCH_ROZH_BTN
                          ).props("flat no-caps").style(
                    "margin-right:14px; padding:8px 18px; border-radius:8px; font-size:0.82rem; "
                    "background:linear-gradient(135deg,rgba(201,168,76,0.15),rgba(201,168,76,0.08)); "
                    "border:1px solid rgba(201,168,76,0.35); color:#fff;")
                with ui.element("div").classes("brat-model-sel"):
                    opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
                    ui.select(opts, value=state["model"], on_change=on_model_change) \
                        .props('dense borderless dark options-dense').style("min-width:210px;")

        # LEFT: загрузчик + руда
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass asset-bay").style("height:auto; flex:1;"):
                    ui.html('<div class="panel-title">⛏ руда — входящее</div>')
                    ui.upload(on_upload=handle_upload, multiple=True, auto_upload=True) \
                        .props("flat color=amber").style("margin:0 8px 8px 8px;")
                    refs["files"] = ui.element("div").classes("file-list").style(
                        "height:auto; max-height:none; overflow:visible; padding:4px 8px;")
                    update_files()

                    # ⚗ Просеять — Брат прогоняет руду через свою философию
                    async def do_sift():
                        s = scan_sift()
                        if not s["ruda"]:
                            ui.notify("Руды нет — нечего просеивать", color="warning")
                            return
                        ui.notify(f"⚗ Просеиваю {s['ruda_count']} файл(ов)...", color="info")
                        SIFTED_DIR.mkdir(parents=True, exist_ok=True)
                        for fn, _ in s["ruda"]:
                            fp = RUDA_DIR / fn
                            try:
                                result = await sift_file(fp, state["model"])
                                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                out_name = f"просев_{fp.stem}_{ts}.md"
                                (SIFTED_DIR / out_name).write_text(
                                    f"# Просев: {fn}\n\n{result}",
                                    encoding="utf-8"
                                )
                                ui.notify(f"✦ просеяно: {fn}", color="positive")
                            except Exception as ex:
                                ui.notify(f"⚠ {fn}: {ex}", color="negative")
                        update_viewer()
                        # сообщаем в чат
                        state["chat"].append({
                            "role": "assistant",
                            "content": f"Просев готов. Разобрал {s['ruda_count']} файл(ов) — смотри в правой панели."
                        })
                        update_chat()

                    ui.button("⚗ Просеять", on_click=do_sift).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:linear-gradient(135deg,rgba(189,0,255,0.18),rgba(0,204,255,0.10)) !important; "
                        "border:1px solid rgba(189,0,255,0.45) !important; color:#e0aaff !important;")

                    ui.html('<div style="padding:6px 16px 12px; font-size:0.6rem; '
                            'color:rgba(255,255,255,0.35); line-height:1.5;">'
                            'Брат сам не тянет — такой руки нет.<br>'
                            'Шеф кладёт экспорт-архивы руками.</div>')

        # STAGE: тулбар + чат + отчёт + ввод
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor"):
                # ── ТУЛБАР: врата (прозрачная плашка, кнопки по центру) ──
                with ui.element("div").classes("stage-toolbar").style(
                    "flex-shrink:0; grid-template-columns:1fr; justify-items:center; "
                    "align-items:end !important; height:auto !important; "
                    "padding:6px 12px 6px !important; "
                    "background:transparent !important; border-bottom:none !important; "
                    "backdrop-filter:none !important;"
                ):
                    with ui.element("div").style(
                        "display:flex; gap:8px; align-items:center; justify-content:center;"
                    ):
                        ui.button("Храм",
                                  on_click=lambda: ui.navigate.to("/hram/index.html")
                                  ).props("flat").classes("brat-gate")  # PATCH_HRAM_GATE
                        ui.button("Торговый").props("flat").classes("brat-gate")
                        ui.button("Мастеров").props("flat").classes("brat-gate")
                        ui.button("Живая книга").props("flat").classes("brat-gate")
                with ui.element("div").classes("stage-content").style(
                    "padding-top:0 !important; padding-bottom:90px;"):
                    with ui.element("div").classes("split-view"):
                        refs["chat"] = ui.element("div").classes("chat-log")
                        update_chat()
                        refs["viewer"] = ui.element("div").classes("viewer")
                        update_viewer()
                # floating-console — ввод
                with ui.element("div").classes("floating-console"):
                    refs["input"] = ui.input(placeholder="скажи слово, шеф...") \
                        .props("borderless").style("flex:1")
                    refs["input"].on("keydown.enter", lambda e: send())

                    # 💾 сохранить чат
                    def do_save():
                        if not state["chat"]:
                            ui.notify("Чат пустой — нечего сохранять", color="warning")
                            return
                        name = save_chat(state["chat"])
                        ui.notify(f"💾 сохранено: {name}", color="positive")

                    ui.button("💾", on_click=do_save).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(201,168,76,0.9); background:rgba(201,168,76,0.10); "
                        "border:1px solid rgba(201,168,76,0.35);")

                    # 📂 загрузить чат — диалог со списком
                    async def do_load():
                        chats = list_chats()
                        if not chats:
                            ui.notify("Сохранённых чатов нет", color="warning")
                            return
                        with ui.dialog() as dlg, ui.card().style(
                            "background:#0d1117; border:1px solid rgba(255,255,255,0.12); "
                            "border-radius:16px; min-width:340px; padding:20px;"
                        ):
                            ui.html('<div style="color:rgba(255,255,255,0.9); font-weight:700; '
                                    'font-size:0.9rem; margin-bottom:14px; letter-spacing:0.08em;">'
                                    '📂 ВЫБЕРИ ЧАТ</div>')
                            for fp in chats[:20]:
                                label = fp.stem.replace("чат_", "")
                                def _load(f=fp):
                                    state["chat"] = load_chat(f)
                                    update_chat()
                                    dlg.close()
                                    ui.notify(f"📂 загружен: {f.name}", color="positive")
                                ui.button(label, on_click=_load).props("flat no-caps").style(
                                    "width:100%; text-align:left; font-family:monospace; "
                                    "font-size:0.78rem; color:rgba(255,255,255,0.75); "
                                    "padding:8px 12px; border-radius:8px; "
                                    "background:rgba(255,255,255,0.04); margin-bottom:4px;")
                            ui.button("отмена", on_click=dlg.close).props("flat").style(
                                "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")
                        dlg.open()

                    ui.button("📂", on_click=do_load).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(0,204,255,0.9); background:rgba(0,204,255,0.10); "
                        "border:1px solid rgba(0,204,255,0.35);")

                    ui.button("ОТПРАВИТЬ", on_click=send).classes("send-button")

        # RIGHT: аватар + приборы
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                # аватар (right-top-slot) — чистое лицо, без подписи
                slot = ui.element("div").classes("right-top-slot").style("position:relative;")
                with slot:
                    av = avatar_url()
                    if av:
                        ui.html(f'<img class="brat-avatar-img" src="{av}" '
                                f'onerror="this.style.display=\'none\'">')
                    else:
                        ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.5);">⬡</div>')
                # приборы (runs-panel)
                with ui.element("div").classes("glass runs-panel"):
                    ui.html('<div class="panel-title">приборы · состояние</div>')
                    with ui.element("div").style("padding:14px 16px;"):
                        st = read_city_state()
                        for key, label, color in GAUGES:
                            v = st.get(key)
                            if v is None:
                                vt, pct, fill = "—", 0, "rgba(255,255,255,0.15)"
                            else:
                                vt, pct, fill = f"{v}%", max(0, min(100, v)), color
                            ui.html(
                                f'<div class="brat-gauge">'
                                f'<div class="brat-gauge-top"><span class="gl">{label}</span>'
                                f'<span class="gv">{vt}</span></div>'
                                f'<div class="brat-gauge-bar"><div class="brat-gauge-fill" '
                                f'style="width:{pct}%; background:{fill};"></div></div></div>')
                        ui.html('<div class="brat-bind-note">⬡ приборы ждут привязки к городу.<br>'
                                'Город даст пульс — оживут здесь.</div>')

    ui.timer(15, lambda: (update_files(), update_viewer()))


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/brat")
    def _brat_page():
        page_brat()
    ui.run(title="Кабинет Брата", port=8101, reload=False)
