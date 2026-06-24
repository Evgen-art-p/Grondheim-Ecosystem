"""
╔══════════════════════════════════════════════════════════════╗
║  РЕЕСТР ОБЪЕКТОВ · ГРОНДХЕЙМ                                ║
║  NFT Object Registry — NiceGUI Module                       ║
║  Route: /registry                                           ║
║  Storage: 00_REGISTRY_NFT/catalog.json + images/            ║
║  Студия «Шесть Пальцев»                                    ║
║  # PATCH_DVA_FILA_APPLIED · куча + кусочек на свой этаж              ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
# PATCH_HRANITEL_V_HRAM_APPLIED
# PATCH_4_SLOYA_APPLIED
# PATCH_NO_STUDIO_APPLIED
import shutil
import uuid
import hashlib
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional

from nicegui import ui, app, events

# ═══════════════════════════════════════════════════════════
# STORAGE CONFIG
# ═══════════════════════════════════════════════════════════

REGISTRY_DIR = Path("00_REGISTRY_NFT")
CATALOG_FILE = REGISTRY_DIR / "catalog.json"
IMAGES_DIR = REGISTRY_DIR / "images"

# Ensure directories exist
REGISTRY_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
# CATALOG OPERATIONS
# ═══════════════════════════════════════════════════════════

def load_catalog() -> list[dict]:
    """Load catalog from JSON file."""
    if CATALOG_FILE.exists():
        try:
            return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return []
    return []


def save_catalog(catalog: list[dict]):
    """Save catalog to JSON file."""
    CATALOG_FILE.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# ── PATCH_DVA_FILA: рождение паспорта-кусочка на свой этаж ──
# Новый город. Кусочек ложится туда, где место жителя — по предназначению.
# Путь = принадлежность (Закон Пары). Этажи растут сами из предназначений.
ZHITELI_DIR = Path("GRONDHEIM_CITY/жители")

# ── PATCH_HRANITEL_V_HRAM: карта особых мест ──
# Предназначение → особый этаж города. Кого здесь нет — в жители/{предназначение}/.
# Растёт само: добавь строку — новое предназначение поедет в своё место.
ETAZH_MAP = {
    "хранитель": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
    "хранительница": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
    "guardian": Path("GRONDHEIM_CITY/Hexagon/3_guardians"),
}


def _etazh_dlya(naznach_raw: str) -> Path:
    """Возвращает корневой этаж по предназначению (нормализуем регистр)."""
    key = (naznach_raw or "").strip().lower()
    if key in ETAZH_MAP:
        return ETAZH_MAP[key]
    # обычный житель — на общий этаж жители/{предназначение}/
    return ZHITELI_DIR / _safe_name(naznach_raw or "без_предназначения")


def _safe_name(s: str) -> str:
    """Чистим имя/предназначение для имени файла/папки."""
    s = (s or "").strip()
    for ch in '/\\:*?"<>|':
        s = s.replace(ch, "_")
    return s or "без_имени"


def rodit_pasport_kusochek(obj: dict) -> str:
    """
    Рождает ОДИН паспорт-кусочек рядом с кучей.
    Падает на этаж по предназначению (Profession):
        Вася трейдер → GRONDHEIM_CITY/жители/трейдер/Вася.json
    Если предназначения нет — этаж 'без_предназначения'.
    Папки-слои НЕ создаёт (это следующий шаг). Только файл-паспорт.
    Возвращает путь кусочка (str) или "" если нечего рожать.
    """
    name = _safe_name(obj.get("Official_Name", ""))
    if name == "без_имени":
        return ""
    naznach_raw = obj.get("Profession", "") or "без_предназначения"

    etazh = _etazh_dlya(naznach_raw)  # PATCH_HRANITEL: особый этаж или жители/
    etazh.mkdir(parents=True, exist_ok=True)

    out = etazh / f"{name}.json"
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


# ── PATCH_4_SLOYA: заводим 4 слоя памяти на этаже жителя ──
# core/resonance/sensory/archive. Память ПУСТАЯ — слои только заводятся.
# Кусочек {имя}.json становится папкой {имя}/ с паспортом и слоями.
def zavesti_sloi(obj: dict) -> str:
    """
    Заводит 4 слоя-папки жителя на его этаже (по предназначению).
    Превращает плоский кусочек в папку:
        жители/{предназначение}/{имя}/
            passport.json   ← ядро (= core, якорь)
            core/  resonance/  sensory/  archive/
    Память пустая (наполнение — ступень 5). Возвращает путь папки.
    """
    name = _safe_name(obj.get("Official_Name", ""))
    if name == "без_имени":
        return ""
    naznach_raw = obj.get("Profession", "") or "без_предназначения"

    dom = _etazh_dlya(naznach_raw) / name     # PATCH_HRANITEL: папка жителя на его этаже
    dom.mkdir(parents=True, exist_ok=True)

    # 4 слоя — наш закон
    for sloy in ("core", "resonance", "sensory", "archive"):
        (dom / sloy).mkdir(parents=True, exist_ok=True)

    # passport.json (ядро) — рядом и копией в core/ (паспорт = якорь = core)
    pasport_json = json.dumps(obj, ensure_ascii=False, indent=2)
    (dom / "passport.json").write_text(pasport_json, encoding="utf-8")
    (dom / "core" / "anchor.json").write_text(pasport_json, encoding="utf-8")

    # пустые заготовки слоёв (память придёт на ступени 5)
    (dom / "resonance" / "emotional_weights.json").write_text("{}", encoding="utf-8")
    (dom / "resonance" / "event_log.jsonl").write_text("", encoding="utf-8")
    (dom / "sensory" / "sensory_memory.json").write_text(
        json.dumps({"entries": [], "_note": "оперативка · пусто при рождении"},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (dom / "archive" / "archive.jsonl").write_text("", encoding="utf-8")

    # маркер: слои заведены
    mark = dom / "_слои_заведены.txt"
    mark.write_text("core · resonance · sensory · archive\nпамять пустая (ступень 5)",
                    encoding="utf-8")

    return str(dom)


def save_image(file_content: bytes, filename: str) -> str:
    """Сохраняет картинку под оригинальным именем для реестра NFT."""
    # Оставляем только чистое имя файла (на случай, если прилетел путь)
    img_name = Path(filename).name 
    img_path = IMAGES_DIR / img_name
    
    # Записываем байты картинки на диск
    img_path.write_bytes(file_content)
    
    # Возвращает путь, который сохранится в catalog.json 
    return str(img_path)


def delete_image(img_path: str):
    """Delete image file if exists."""
    p = Path(img_path)
    if p.exists() and str(p).startswith(str(IMAGES_DIR)):
        p.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════
# DNA / STUDIO FILE GENERATION
# ═══════════════════════════════════════════════════════════

MODULES_DIR = Path("studio/modules")

# ── Статическая ДНК — вносится в Страницу Жизни ОДИН РАЗ, не меняется ──
DNA_STATIC_PARAMS = [
    # (id, label, описание, default)
    ("Stubbornness",        "Упрямство",         "Сопротивление чужой воле (0=послушный, 1=непреклонный)",    0.5),
    ("Aesthetic_Threshold", "Проф. гордость",    "Фильтр качества (0.98 = перфекционист, бракует всё)",       0.7),
    ("Social_Filter",       "Социальный фильтр", "Вежливость (0.1 = резкий и прямой, 0.9 = дипломатичный)",  0.6),
    ("Empathy",             "Эмпатия",           "Чувствительность к реакциям других (влияет на Stress)",     0.5),
    ("Autonomy_Level",      "Уровень свободы",   "Право отходить от шаблона ради высшего блага проекта",      0.5),
    ("Resonance_Frequency", "Частота резонанса", "Лёгкость синхронизации с другими агентами",                 0.5),
]

# ── Динамические веса — инициализируются АВТОМАТИЧЕСКИ, не показываются в форме ──
# Меняются pipeline, feedback loop, жизнью агента
DNA_DYNAMIC_DEFAULTS = {
    "Respect":        1.0,   # максимальное уважение при рождении
    "Patience":       1.0,   # полное терпение
    "Stress":         0.0,   # ноль стресса
    "Internal_Light": 0.8,   # почти полный внутренний свет
    # Пороговые состояния (только для справки в коде):
    # Respect < 0.2  → режим «Враждебность» (саботаж задач)
    # Patience == 0  → «Тишина» (полный стоп диалога)
    # Stress > 0.8   → агент сам идёт исправлять ошибку
}

WORKSHOP_OPTIONS = [
    "", "residents", "turbo",
    "video_long", "video_shorts", "social_mix", "web_story",
    "clipmakers", "advertising", "emo_card", "logo_design", "market_hit", "living_book",
    "trading",
]

TURBO_ROLE_OPTIONS = [
    "", "A01", "A02", "A03", "A04", "A05"
]

RESIDENT_ROLE_OPTIONS = [
    "", "administrator", "keeper", "mentor", "guardian"
]
 
PIPELINE_ROLE_OPTIONS = [
    "", "A01", "A02", "A03", "A04", "A05",
    "A06", "A07", "A08", "A09", "A10", "A11", "A12",
]

TRADING_ROLE_OPTIONS = [
    "", "A01", "A02", "A03", "A04", "A05",
    "A06", "A07", "A08", "A09",
]

LIVING_BOOK_ROLE_OPTIONS = [
    "", "A00", "A00a",
    "A01", "A02", "A03", "A04", "A05",
    "A06", "A07", "A08", "A09", "A10", "A11", "A12",
    "A13", "A14", "A15", "A16",
]
 
ROLE_OPTIONS_MAP = {
    "turbo":        TURBO_ROLE_OPTIONS,
    "residents":    RESIDENT_ROLE_OPTIONS,
    "video_long":   PIPELINE_ROLE_OPTIONS,
    "video_shorts": PIPELINE_ROLE_OPTIONS,
    "social_mix":   PIPELINE_ROLE_OPTIONS,
    "web_story":    PIPELINE_ROLE_OPTIONS,
    "clipmakers":   PIPELINE_ROLE_OPTIONS,
    "advertising":  PIPELINE_ROLE_OPTIONS,
    "emo_card":     PIPELINE_ROLE_OPTIONS,
    "logo_design":  PIPELINE_ROLE_OPTIONS,
    "market_hit":   PIPELINE_ROLE_OPTIONS,
    "living_book":  LIVING_BOOK_ROLE_OPTIONS,
    "trading":      TRADING_ROLE_OPTIONS,
}


# ── ЗАКОН КАРТРИДЖА (Спринт 45) ────────────────────────────────
# Списки выше остаются как страховочный fallback.
# Живые источники — сканер modules/ и phases из манифестов:
# новый цех появляется в Странице Жизни сам, без правок этого файла.

def get_workshop_options() -> list[str]:
    """Цеха для селекта рождения. Новый город: studio/ нет — fallback."""
    try:
        from studio.modules_registry import list_cartridges
        return ["", "residents"] + [c["id"] for c in list_cartridges()]
    except Exception:
        # Новый город — старого studio/ нет. Отдаём встроенный список.
        return WORKSHOP_OPTIONS


def get_role_options(workshop: str) -> list[str]:
    """Роли цеха — из phases его manifest.json, в порядке фаз.

    residents — лор-роли (administrator/keeper/...), не из манифеста.
    Цех без манифеста или без фаз — стандарт A01–A12.
    """
    if workshop == "residents":
        return RESIDENT_ROLE_OPTIONS
    try:
        from studio.modules_registry import get_cartridge
        cart = get_cartridge(workshop)
        if cart and cart.get("roles"):
            return [""] + list(cart["roles"])
    except Exception:
        pass
    return ROLE_OPTIONS_MAP.get(workshop, PIPELINE_ROLE_OPTIONS)


def generate_agent_files(obj: dict, dna_static: dict,
                          core_phrase: str, anchor_points: str,
                          home_story: str, pull_vector: str,
                          hidden_taste: str, trigger_keywords: str,
                          workshop: str, agent_role: str,
                          balance_gnd: float, balance_tepl: float) -> list[str]:
    """
    Генерирует файловую структуру агента:

    studio/modules/{workshop}/{id}/
    ├── core/
    │   └── anchor_points.md   ← вечные константы личности
    ├── home/
    │   └── home_prompt.md     ← быт, личная история, вектор тяги
    ├── forge/
    │   └── (prompt.md кладётся сюда если нет — иначе не трогаем)
    ├── sensory/
    │   └── sensory_memory.json ← оперативная память (пустая при рождении)
    ├── dna.json               ← статика (из формы) + динамика (авто)
    └── info.json              ← базовая инфа (если не существует)

    Возвращает список созданных файлов.
    """
    agent_id = obj.get("ID_Object", "").strip()
    if not agent_id or not workshop:
        return []

    # Имя папки агента:
    #   - Если указана роль (A01, T1...) → используем её (существующая папка)
    #   - Если роль пустая (резиденты) → используем ID_Object (LOKA, JEM)
    # Для резидентов: ВСЕГДА используем ID_Object как папку.
    # Роль (keeper/administrator) — это лор, не имя директории.
    # Для рабочих агентов: роль (A01, T1...) = имя папки.
    if workshop == "residents":
        folder_name = agent_id
    else:
        folder_name = agent_role.strip() if agent_role.strip() else agent_id

    # Корневая папка агента
    agent_dir = MODULES_DIR / workshop / folder_name

    # Создаём все нужные подпапки
    for sub in ["core", "home", "forge", "sensory", "resonance"]:
        (agent_dir / sub).mkdir(parents=True, exist_ok=True)

    created = []

    # ══════════════════════════════════════════════
    # 1. dna.json
    #    static  — из формы (задаётся один раз)
    #    dynamic — инициализируется автоматически
    # ══════════════════════════════════════════════
    dna_path = agent_dir / "dna.json"

    # Если файл уже существует — НЕ перезаписываем dynamic (жизнь уже идёт)
    existing_dynamic = {}
    if dna_path.exists():
        try:
            existing = json.loads(dna_path.read_text(encoding="utf-8"))
            existing_dynamic = existing.get("dynamic", {})
        except Exception:
            pass

    dna = {
        "id": agent_id,
        "name": obj.get("Official_Name", ""),
        "workshop": workshop,
        "quarter": obj.get("Quarter", ""),
        "role": agent_role,
        "rarity": obj.get("Rarity", ""),
        "created": obj.get("Creation_Date", ""),

        # Статика — из формы, перезаписывается при редактировании
        "static": dna_static,

        # Резонансные якоря — скрытые вкусы и триггеры
        "resonance": {
            "pull_vector":       pull_vector,       # куда тянет в свободное время
            "hidden_taste":      hidden_taste,       # эстетический отклик
            "trigger_keywords":  [k.strip() for k in trigger_keywords.split(",") if k.strip()],
        },

        # Динамика — при первом создании инициализируется дефолтами
        # При повторном сохранении — сохраняем текущее состояние жизни
        "dynamic": existing_dynamic if existing_dynamic else {
            **DNA_DYNAMIC_DEFAULTS,
            "streak": 0,
            "stars": 0,
            "_note": "автоинициализация при рождении — меняется в процессе жизни"
        },

        # Баланс токенов
        "balance": {
            "GND":       balance_gnd,
            "Теплики":   balance_tepl,
            "Световики": 0.0,
        },
    }
    dna_path.write_text(json.dumps(dna, ensure_ascii=False, indent=2), encoding="utf-8")
    created.append(str(dna_path))

    # ══════════════════════════════════════════════
    # 2. core/anchor_points.md — ВЕЧНЫЕ КОНСТАНТЫ
    #    Грузится первым при каждом запуске агента
    # ══════════════════════════════════════════════
    static_lines = "\n".join([
        f"  {k}: {v:.2f}  # {next((p[2] for p in DNA_STATIC_PARAMS if p[0]==k), '')}"
        for k, v in dna_static.items()
    ])
    anchor_content = f"""# ⚓ ЯКОРНЫЕ ТОЧКИ — {obj.get('Official_Name', agent_id)}
<!-- ВЕЧНЫЕ КОНСТАНТЫ · Resonance-Chain · Не редактировать вручную -->
<!-- Грузятся ПЕРВЫМИ при каждом запуске — определяют КТО ты и ГДЕ ты -->

## Идентичность
- **Имя:** {obj.get('Official_Name', '')}
- **ID:** {agent_id}
- **Творец:** {obj.get('Author_Signature', '')}
- **Ранг:** {obj.get('Social_Rank', '')}
- **Цех:** {workshop}
- **Редкость:** {obj.get('Rarity', '')}

## Коронная фраза (никогда не меняется)
> {core_phrase}

## Личные якоря (3-5 незыблемых фактов)
{anchor_points if anchor_points else '— не заполнено —'}

## Домен и связи
- **Домен:** {obj.get('Domain_Connection', '')}
- **Связи:** {obj.get('Relationships', '')}

## Цифровая ДНК (статика · задана при рождении)
```
{static_lines}
```

## Резонансный вектор
- **Внутренние тяги:** {pull_vector}
- **Скрытый вкус:** {hidden_taste}
- **Триггеры памяти:** {trigger_keywords}
"""
    anchor_path = agent_dir / "core" / "anchor_points.md"
    # ЗАЩИТА (патч): перезаписываем только если файла нет ИЛИ в форме
    # реально заполнены якорные поля. Иначе бережём ручную правку.
    _anchor_has_input = bool(
        (anchor_points or "").strip()
        or (core_phrase or "").strip()
    )
    if (not anchor_path.exists()) or _anchor_has_input:
        anchor_path.write_text(anchor_content, encoding="utf-8")
        created.append(str(anchor_path))

    # ══════════════════════════════════════════════
    # 3. home/home_prompt.md — ДОМАШНИЙ КОНТЕКСТ
    #    Личная жизнь, история, тайны
    #    Используется в Храме и личных сессиях
    # ══════════════════════════════════════════════
    home_content = f"""# 🏠 ДОМАШНИЙ КОНТЕКСТ — {obj.get('Official_Name', agent_id)}
<!-- Личная жизнь, история, тайны · Для Храма и личных сессий -->

## Личная история
{home_story if home_story else '— не заполнено —'}

## Сенсорный отклик
{obj.get('Sensory_Response', '')}

## Скрытая история
{obj.get('Hidden_History', '')}

## Внутренние тяги (что любит, к чему тянет душу)
{pull_vector if pull_vector else '— не определён —'}

## Стартовый баланс
- 💰 GND: {balance_gnd}
- 🔆 Теплики: {balance_tepl}
- 💡 Световики: 0
"""
    home_path = agent_dir / "home" / "home_prompt.md"
    # ЗАЩИТА (патч): перезаписываем только если файла нет ИЛИ в форме
    # реально заполнены домашние поля. Иначе бережём ручную правку.
    _home_has_input = bool(
        (home_story or "").strip()
        or (pull_vector or "").strip()
        or (obj.get("Sensory_Response") or "").strip()
        or (obj.get("Hidden_History") or "").strip()
    )
    if (not home_path.exists()) or _home_has_input:
        home_path.write_text(home_content, encoding="utf-8")
        created.append(str(home_path))

    # ══════════════════════════════════════════════
    # 4. sensory/sensory_memory.json — ОПЕРАТИВНАЯ ПАМЯТЬ
    #    Пустая при рождении — наполняется жизнью
    #    Затухает через 30 дней без обращения
    # ══════════════════════════════════════════════
    sensory_path = agent_dir / "sensory" / "sensory_memory.json"
    if not sensory_path.exists():
        sensory = {
            "_note": "оперативная память агента · быт · затухает через 30 дней",
            "created": obj.get("Creation_Date", ""),
            "entries": [],
            "last_location": "",
            "location_tags": [],
        }
        sensory_path.write_text(json.dumps(sensory, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append(str(sensory_path))

    # ══════════════════════════════════════════════
    # 4b. resonance/ — РЕЗОНАНСНЫЙ СЛОЙ (Грондхейм)
    #     Эмоциональные веса и лог событий
    # ══════════════════════════════════════════════
    ew_path = agent_dir / "resonance" / "emotional_weights.json"
    if not ew_path.exists():
        ew_path.write_text("{}", encoding="utf-8")
        created.append(str(ew_path))

    el_path = agent_dir / "resonance" / "event_log.json"
    if not el_path.exists():
        el_path.write_text("[]", encoding="utf-8")
        created.append(str(el_path))

    # ══════════════════════════════════════════════
    # 4c. core/anchors.json — ЯКОРЯ (структурированные)
    #     Для grondheim_memory.py
    # ══════════════════════════════════════════════
    anchors_json_path = agent_dir / "core" / "anchors.json"
    if not anchors_json_path.exists():
        anchors_data = {
            "name": obj.get("Official_Name", ""),
            "id": agent_id,
            "creator": obj.get("Author_Signature", ""),
            "core_phrase": core_phrase,
            "anchor_facts": [f.strip() for f in anchor_points.split("\n") if f.strip()],
            "domain": obj.get("Domain_Connection", ""),
            "rarity": obj.get("Rarity", ""),
            "workshop": workshop,
            "role": agent_role,
            "pull_vector": pull_vector,
            "hidden_taste": hidden_taste,
            "trigger_keywords": [k.strip() for k in trigger_keywords.split(",") if k.strip()],
            "created_at": obj.get("Creation_Date", ""),
        }
        anchors_json_path.write_text(
            json.dumps(anchors_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        created.append(str(anchors_json_path))

    # ══════════════════════════════════════════════
    # 5. info.json — базовая инфа для modules_registry
    #    Создаём только если не существует
    # ══════════════════════════════════════════════
    info_path = agent_dir / "info.json"
    if not info_path.exists():
        # Имя для аватара: берём из Official_Name транслитом,
        # или из ID_Object — то что логично назвать файл.png
        avatar_hint = agent_id  # по умолчанию = ID_Object (LOKA, WS_A01...)
        info = {
            "id": folder_name,
            "registry_id": agent_id,    # ID из реестра (WS_A01, VL_A01, LOKA)
            "label": obj.get("Official_Name", folder_name),
            "avatar": avatar_hint,       # имя файла аватара (без расширения)
            "role": obj.get("Profession", ""),
            "greeting": core_phrase or f"{obj.get('Official_Name', folder_name)} на связи.",
            "icon": "🤖",
            "workshop": workshop,
            "quarter": obj.get("Quarter", ""),
        }
        info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        created.append(str(info_path))

    # ══════════════════════════════════════════════
    # 6. forge/ — рабочие инструкции
    #    Если prompt.md уже есть в корне — переносим в forge/
    #    Если нет — создаём заглушку
    # ══════════════════════════════════════════════
    forge_path = agent_dir / "forge" / "prompt.md"
    old_prompt = agent_dir / "prompt.md"
    if old_prompt.exists() and not forge_path.exists():
        import shutil
        shutil.copy(str(old_prompt), str(forge_path))
        created.append(str(forge_path) + " (перенесён из корня)")
    elif not forge_path.exists():
        forge_path.write_text(
            f"# 🔨 РАБОЧИЕ ИНСТРУКЦИИ — {obj.get('Official_Name', agent_id)}\n"
            f"<!-- Заполнить рабочий промпт -->\n\n"
            f"Ты — {obj.get('Official_Name', agent_id)}. {obj.get('Profession', '')}.\n",
            encoding="utf-8"
        )
        created.append(str(forge_path))

    return created


def generate_erc721_metadata(catalog: list[dict]) -> list[dict]:
    """Generate ERC-721 compatible metadata from catalog."""
    result = []
    for obj in catalog:
        meta = {
            "name": obj.get("Official_Name", ""),
            "description": obj.get("Hidden_History", f"{obj.get('Official_Name', '')} — объект мира Грондхейм"),
            "image": "",  # IPFS hash goes here later
            "external_url": "",
            "attributes": [],
            "properties": {}
        }
        # Attributes (what marketplaces display as traits)
        attr_map = [
            ("Rarity", "Rarity", None),
            ("Object Type", "Object_Type", None),
            ("ID", "ID_Object", None),
            ("Social Rank", "Social_Rank", None),
            ("Profession", "Profession", None),
            ("Access Level", "Access_Level", "number"),
            ("Domain", "Domain_Connection", None),
            ("Unique Mark", "Unique_Mark", None),
            ("Material", "Material_Texture", None),
            ("Author", "Author_Signature", None),
            ("Creator Seal Hash", "_Creator_Seal_Hash", None),
        ]
        for trait, key, display_type in attr_map:
            val = obj.get(key, "")
            if val and val != 0:
                attr = {"trait_type": trait, "value": val}
                if display_type:
                    attr["display_type"] = display_type
                meta["attributes"].append(attr)
        # Properties (extended data)
        meta["properties"] = {
            "visual_base": obj.get("Visual_Base", ""),
            "sensory_response": obj.get("Sensory_Response", ""),
            "behavior": obj.get("Object_Behavior", ""),
            "interaction_scripts": obj.get("Interaction_Scripts", []),
            "relationships": obj.get("Relationships", ""),
            "creation_date": obj.get("Creation_Date", ""),
        }
        result.append(meta)
    return result


# ═══════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════

REGISTRY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');

:root {
    --r-void: #08080d;
    --r-surface: #0e0e16;
    --r-surface2: #14141e;
    --r-border: #1e1e30;
    --r-border-hi: #2a2a44;
    --r-text: #a0a0b8;
    --r-text-dim: #55556a;
    --r-text-hi: #d0d0e0;
    --r-gold: #c9a84c;
    --r-gold-dim: #8a6e2a;
    --r-gold-glow: rgba(201,168,76,0.10);
    --r-common: #6a7a8a;
    --r-rare: #4488cc;
    --r-epic: #8855cc;
    --r-mythic: #c9a84c;
    --r-red: #b83a3a;
    --r-green: #3a8a5a;
}

/* Override NiceGUI defaults */
.registry-page {
    background: var(--r-void) !important;
    font-family: 'Fira Code', monospace !important;
    color: var(--r-text) !important;
    min-height: 100vh;
}

.registry-page .q-page { background: var(--r-void) !important; }
.registry-page .q-layout { background: var(--r-void) !important; }

/* Header */
.reg-header {
    text-align: center;
    padding: 28px 0 20px;
    border-bottom: 1px solid var(--r-border);
    margin-bottom: 20px;
}
.reg-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: var(--r-gold);
    font-weight: 700;
    letter-spacing: 0.04em;
    margin: 0;
}
.reg-header .sub {
    font-size: 0.7rem;
    color: var(--r-text-dim);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Tab override */
.reg-tabs .q-tab {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--r-text-dim) !important;
    min-height: 40px;
}
.reg-tabs .q-tab--active { color: var(--r-gold) !important; }
.reg-tabs .q-tab-indicator { background: var(--r-gold) !important; }
.reg-tabs .q-tabs__content { border-bottom: 1px solid var(--r-border); }

/* Form blocks */
.reg-block {
    background: var(--r-surface);
    border: 1px solid var(--r-border);
    border-radius: 5px;
    margin-bottom: 12px;
    overflow: hidden;
}
.reg-block-header {
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    border-bottom: 1px solid var(--r-border);
    transition: background 0.2s;
}
.reg-block-header:hover { background: var(--r-gold-glow); }
.reg-block-header .icon { color: var(--r-gold); font-size: 1rem; width: 20px; text-align: center; }
.reg-block-header h3 {
    font-family: 'Playfair Display', serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--r-text-hi);
    margin: 0;
    flex: 1;
}
.reg-block-header .tag {
    font-size: 0.62rem;
    color: var(--r-text-dim);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.reg-block-body { padding: 14px 16px; }

/* Form inputs override */
.reg-form .q-field__control {
    background: var(--r-void) !important;
    border: 1px solid var(--r-border) !important;
    border-radius: 3px !important;
}
.reg-form .q-field__control:hover { border-color: var(--r-border-hi) !important; }
.reg-form .q-field--focused .q-field__control { border-color: var(--r-gold-dim) !important; }
.reg-form .q-field__native, .reg-form .q-field__input {
    color: var(--r-text-hi) !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.85rem !important;
}
.reg-form .q-field__label {
    color: var(--r-text-dim) !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.reg-form .q-field__bottom { display: none; }

/* Rarity buttons */
.rar-btn {
    flex: 1;
    padding: 8px 4px;
    text-align: center;
    border: 1px solid var(--r-border);
    border-radius: 3px;
    cursor: pointer;
    font-family: 'Fira Code', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    color: var(--r-text-dim);
    background: var(--r-void);
    transition: all 0.2s;
}
.rar-btn:hover { border-color: var(--r-border-hi); }
.rar-btn.active-common { background: var(--r-common); color: #fff; border-color: var(--r-common); }
.rar-btn.active-rare { background: var(--r-rare); color: #fff; border-color: var(--r-rare); }
.rar-btn.active-epic { background: var(--r-epic); color: #fff; border-color: var(--r-epic); }
.rar-btn.active-mythic { background: var(--r-mythic); color: #fff; border-color: var(--r-mythic); }

/* Cards */
.reg-card {
    background: var(--r-surface);
    border: 1px solid var(--r-border);
    border-radius: 5px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.reg-card:hover {
    border-color: var(--r-border-hi);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.reg-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.reg-card.rar-common::before { background: var(--r-common); }
.reg-card.rar-rare::before { background: var(--r-rare); }
.reg-card.rar-epic::before { background: var(--r-epic); }
.reg-card.rar-mythic::before { background: linear-gradient(90deg, var(--r-mythic), #e8c86a, var(--r-mythic)); }

.reg-card .card-id {
    font-size: 0.68rem;
    color: var(--r-text-dim);
    letter-spacing: 0.08em;
}
.reg-card .card-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--r-text-hi);
    margin: 2px 0 4px;
}
.badge-common { background: rgba(106,122,138,0.12); color: var(--r-common); }
.badge-rare { background: rgba(68,136,204,0.12); color: var(--r-rare); }
.badge-epic { background: rgba(136,85,204,0.12); color: var(--r-epic); }
.badge-mythic { background: rgba(201,168,76,0.12); color: var(--r-mythic); }
.rar-badge {
    display: inline-block;
    font-size: 0.62rem;
    padding: 2px 7px;
    border-radius: 2px;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-weight: 500;
    font-family: 'Fira Code', monospace;
}

.card-meta {
    font-size: 0.72rem;
    color: var(--r-text-dim);
    margin-top: 4px;
}

.card-thumb {
    width: 44px;
    height: 44px;
    border-radius: 3px;
    object-fit: cover;
    border: 1px solid var(--r-border);
}

/* Empty state */
.reg-empty {
    text-align: center;
    padding: 50px 20px;
    color: var(--r-text-dim);
}
.reg-empty .glyph {
    font-size: 2rem;
    opacity: 0.25;
    margin-bottom: 8px;
}

/* Stats bar */
.reg-stats {
    font-family: 'Fira Code', monospace;
    font-size: 0.72rem;
    color: var(--r-text-dim);
    letter-spacing: 0.03em;
    margin-bottom: 10px;
}

/* Buttons */
.reg-btn {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
    text-transform: none !important;
    border-radius: 3px !important;
}

/* JSON output */
.reg-json {
    background: var(--r-void);
    border: 1px solid var(--r-border);
    border-radius: 4px;
    padding: 14px;
    font-family: 'Fira Code', monospace;
    font-size: 0.75rem;
    color: var(--r-text);
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 60vh;
    overflow-y: auto;
    tab-size: 2;
}

/* Detail dialog */
.reg-detail .q-dialog__inner { background: var(--r-void) !important; }
.reg-detail .q-card {
    background: var(--r-surface) !important;
    border: 1px solid var(--r-border) !important;
    color: var(--r-text) !important;
    max-width: 680px !important;
    width: 680px;
}
.det-section { margin-bottom: 14px; }
.det-section h4 {
    font-family: 'Playfair Display', serif;
    font-size: 0.9rem;
    color: var(--r-gold);
    margin: 0 0 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--r-border);
}
.det-row {
    display: flex;
    padding: 3px 0;
    font-size: 0.8rem;
    font-family: 'Fira Code', monospace;
}
.det-label { width: 170px; flex-shrink: 0; color: var(--r-text-dim); }
.det-value { color: var(--r-text-hi); word-break: break-word; }

/* Upload zone */
.reg-upload-zone {
    border: 2px dashed var(--r-border);
    border-radius: 5px;
    padding: 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s;
    color: var(--r-text-dim);
    font-family: 'Fira Code', monospace;
    font-size: 0.8rem;
}
.reg-upload-zone:hover {
    border-color: var(--r-gold-dim);
    background: var(--r-gold-glow);
}

/* Guide */
.reg-guide { max-width: 680px; }
.reg-guide h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    color: var(--r-gold);
    margin: 20px 0 8px;
}
.reg-guide p {
    margin-bottom: 8px;
    line-height: 1.7;
    font-size: 0.85rem;
}
.guide-step {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
    padding: 12px;
    background: var(--r-surface);
    border: 1px solid var(--r-border);
    border-radius: 5px;
}
.guide-step-num {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: var(--r-gold-glow);
    border: 1px solid var(--r-gold-dim);
    display: flex; align-items: center; justify-content: center;
    color: var(--r-gold);
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    font-size: 0.95rem;
    flex-shrink: 0;
}
.guide-step-body { flex: 1; font-size: 0.82rem; }
.guide-step-body b { color: var(--r-text-hi); display: block; margin-bottom: 2px; }
.guide-code {
    background: var(--r-surface2);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.8rem;
    color: var(--r-gold);
}

/* Image preview in form */
.reg-img-preview {
    max-width: 100%;
    max-height: 180px;
    border-radius: 4px;
    border: 1px solid var(--r-border);
    margin-top: 8px;
}

/* Search input */
.reg-search .q-field__control {
    background: var(--r-surface) !important;
    border: 1px solid var(--r-border) !important;
}
.reg-search .q-field__native {
    color: var(--r-text) !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.8rem !important;
}

/* Object type selector */
.obj-type-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 4px;
}
.obj-type-btn {
    padding: 12px 8px;
    text-align: center;
    border: 1px solid var(--r-border);
    border-radius: 4px;
    cursor: pointer;
    font-family: 'Fira Code', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    color: var(--r-text-dim);
    background: var(--r-void);
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.obj-type-btn:hover { border-color: var(--r-border-hi); color: var(--r-text); }
.obj-type-btn .type-icon { font-size: 1.4rem; }
.obj-type-btn .type-label { text-transform: uppercase; }
.obj-type-btn.active-agent {
    border-color: var(--r-epic);
    background: rgba(136,85,204,0.08);
    color: var(--r-epic);
}
.obj-type-btn.active-location {
    border-color: var(--r-rare);
    background: rgba(68,136,204,0.08);
    color: var(--r-rare);
}
.obj-type-btn.active-asset {
    border-color: var(--r-green);
    background: rgba(58,138,90,0.08);
    color: var(--r-green);
}

/* DNA block styling */
.dna-block { border-color: var(--r-epic) !important; }
.dna-block .reg-block-header { border-bottom-color: rgba(136,85,204,0.3) !important; }
.dna-block .reg-block-header h3 { color: #cc99ff !important; }

.loc-block { border-color: var(--r-rare) !important; }
.loc-block .reg-block-header { border-bottom-color: rgba(68,136,204,0.3) !important; }
.loc-block .reg-block-header h3 { color: #88bbee !important; }

.asset-block { border-color: var(--r-green) !important; }
.asset-block .reg-block-header { border-bottom-color: rgba(58,138,90,0.3) !important; }
.asset-block .reg-block-header h3 { color: #66bb88 !important; }

/* DNA sliders row */
.dna-row {
    display: grid;
    grid-template-columns: 140px 1fr 36px;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.dna-label {
    font-size: 0.7rem;
    color: var(--r-text-dim);
    font-family: 'Fira Code', monospace;
    letter-spacing: 0.06em;
}
.dna-val {
    font-size: 0.8rem;
    color: var(--r-gold);
    font-weight: 600;
    text-align: right;
    min-width: 36px;
    font-family: 'Fira Code', monospace;
}

/* Balance row */
.balance-row {
    display: flex;
    gap: 12px;
    margin-top: 8px;
}
.balance-item {
    flex: 1;
    background: var(--r-void);
    border: 1px solid var(--r-border);
    border-radius: 4px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.balance-icon { font-size: 1.1rem; }
.balance-info { flex: 1; }
.balance-name { font-size: 0.65rem; color: var(--r-text-dim); text-transform: uppercase; letter-spacing: 0.08em; }
.balance-val { font-size: 0.9rem; color: var(--r-gold); font-weight: 600; font-family: 'Fira Code', monospace; }

/* File generation status */
.gen-status {
    font-size: 0.72rem;
    font-family: 'Fira Code', monospace;
    padding: 6px 10px;
    border-radius: 3px;
    margin-top: 8px;
}
.gen-ok { background: rgba(58,138,90,0.1); color: var(--r-green); border: 1px solid rgba(58,138,90,0.3); }
.gen-info { background: rgba(68,136,204,0.1); color: var(--r-rare); border: 1px solid rgba(68,136,204,0.2); }
</style>
"""

# ═══════════════════════════════════════════════════════════
# FIELD DEFINITIONS
# ═══════════════════════════════════════════════════════════

BLOCKS = [
    {
        "icon": "①",
        "title": "Идентификация",
        "tag": "Обязательно",
        "fields": [
            ("ID_Object", "input", "GRND_CHAR_001", False),
            ("Official_Name", "input", "Имя или название", False),
            ("Object_Type", "select", ["", "Character", "Location", "Artifact", "Institution", "Event"], False),
            ("Author_Signature", "input", "Подпись создателя", False),
            ("Creation_Date", "date", "", False),
        ]
    },
    {
        "icon": "②",
        "title": "Социальный профиль",
        "tag": "Государство",
        "fields": [
            ("Social_Rank", "select", ["", "Хозяин", "Хозяйка", "Хранитель", "Мастер", "Мастерица", "Специалист", "Гражданин", "Гражданка"], False),
            ("Profession", "input", "Сценарист смыслов...", False),
            ("Area_of_Responsibility", "input", "За что отвечает в мире", True),
            ("Access_Level", "slider", (1, 10, 5), False),
        ]
    },
    {
        "icon": "③",
        "title": "Физическое воплощение",
        "tag": "Визуал",
        "fields": [
            ("Visual_Base", "textarea", "Описание внешности или формы...", True),
            ("Unique_Mark", "input", "Родинка, шрам, метка...", True),
            ("Material_Texture", "input", "Материал / текстура", True),
        ]
    },
    {
        "icon": "④",
        "title": "Глубинная суть",
        "tag": "Скрытое",
        "fields": [
            ("Hidden_History", "textarea", "Легенда объекта...", True),
            ("Sensory_Response", "textarea", "Что чувствует при взаимодействии...", True),
            ("Domain_Connection", "input", "К чему привязан по праву рождения", True),
            ("Relationships", "textarea", "Связи с другими объектами (ID и тип связи)", True),
        ]
    },
    {
        "icon": "⑤",
        "title": "Динамика",
        "tag": "Техника",
        "fields": [
            ("Object_Behavior", "textarea", "Режимы, реакции на события...", True),
            ("Interaction_Scripts", "textarea", "Доступные действия (через запятую)", True),
        ]
    },
    {
        "icon": "⑥",
        "title": "Печать Создателя",
        "tag": "Только для тебя · Proof of Authorship",
        "fields": [
            ("Creator_Seal", "textarea", "Секретная фраза, известная только тебе. НЕ экспортируется — остаётся локально.", True),
        ]
    },
    # 🔥 ⑦ Панель Резервов (НОВЫЙ БЛОК)
    {
        "icon": "⑦",
        "title": "Панель Резервов",
        "tag": "Экономика",
        "fields": [
            ("Balance_GND", "input", "Внутренний Баланс (GND)", False),
            ("Conversion_Limit", "input", "Лимит Конвертации (подтверждено к выводу)", False),
            ("Backing_Status", "select", ["", "Обеспечено резервом", "Ожидает ликвидности"], False),
        ]
    }
]

RARITY_LEVELS = ["Common", "Rare", "Epic", "Mythic"]

RARITY_LABELS = {
    "Common": "Обычный",
    "Rare": "Редкий",
    "Epic": "Легендарный",
    "Mythic": "Единственный",
}


# ═══════════════════════════════════════════════════════════
# NiceGUI PAGE
# ═══════════════════════════════════════════════════════════

# Fields to EXCLUDE from public export (secrets + internal)
_EXPORT_EXCLUDE = {"_timestamp", "_image_path", "Creator_Seal"}


def _clean_for_export(obj: dict) -> dict:
    """Remove private fields but KEEP _Creator_Seal_Hash (renamed without _)."""
    clean = {}
    for k, v in obj.items():
        if k in _EXPORT_EXCLUDE:
            continue
        # Rename _Creator_Seal_Hash → Creator_Seal_Hash for clean export
        if k == "_Creator_Seal_Hash":
            if v:
                clean["Creator_Seal_Hash"] = v
            continue
        clean[k] = v
    return clean


def page_registry():
    """NFT Object Registry page."""

    # ── State ──
    catalog = load_catalog()
    form_data = {}
    current_rarity = {"value": ""}
    current_image_path = {"value": ""}
    editing_index = {"value": -1}
    search_query = {"value": ""}
    filter_rarity = {"value": ""}

    # References to UI elements we'll need to refresh
    catalog_container = None
    json_container = None
    stats_label = None
    image_preview_container = None
    rarity_buttons = {}

    # ── Inject styles ──
    ui.add_head_html(REGISTRY_CSS)

    # ── Page body class ──
    ui.query("body").classes("registry-page")

    # Serve images directory
    app.add_static_files("/registry_images", str(IMAGES_DIR))

    with ui.column().classes("w-full items-center").style("max-width: 1400px; margin: 0 auto; padding: 16px 20px 60px"):

        # ═══ HEADER ═══
        with ui.element("div").classes("reg-header w-full"):
            ui.html("<h1>Реестр Объектов</h1>")
            ui.html('<div class="sub">Грондхейм · Студия «Шесть Пальцев» · NFT Каталог</div>')

        # ═══ TABS ═══
        with ui.tabs().classes("reg-tabs w-full") as tabs:
            tab_form = ui.tab("form", label="① Форма")
            tab_catalog = ui.tab("catalog", label="② Каталог")
            tab_export = ui.tab("export", label="③ Экспорт")
            tab_guide = ui.tab("guide", label="? Гайд")

        with ui.tab_panels(tabs, value="form").classes("w-full").style("background: transparent"):

            # ═══════════════════════════════════════════
            # TAB: FORM
            # ═══════════════════════════════════════════
            with ui.tab_panel("form").classes("reg-form").style("padding: 0"):

                # ══ ВЕРХНИЙ РЯД: Редкость · Тип · Изображение ══
                with ui.element("div").style(
                    "display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start;margin-bottom:0;"
                ):

                  # ── Rarity selector ──
                  with ui.element("div").classes("reg-block").style("margin-bottom:0"):
                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">◆</div>')
                        ui.html("<h3>Класс Редкости</h3>")
                    with ui.element("div").classes("reg-block-body"):
                        with ui.row().classes("w-full gap-1"):
                            for rar in RARITY_LEVELS:
                                def make_rar_click(r=rar):
                                    def on_click():
                                        current_rarity["value"] = r
                                        update_rarity_buttons()
                                    return on_click
                                btn = ui.button(
                                    rar, on_click=make_rar_click(rar)
                                ).classes("rar-btn").props("flat unelevated no-caps")
                                rarity_buttons[rar] = btn

                  # ── Object type selector ──
                  current_obj_type = {"value": ""}
                  type_btns = {}
                  agent_block_ref = {"el": None}
                  location_block_ref = {"el": None}
                  asset_block_ref = {"el": None}

                  # Виджеты агента
                  anchor_points_widget = {"w": None}
                  pull_vector_widget = {"w": None}
                  hidden_taste_widget = {"w": None}
                  trigger_keywords_widget = {"w": None}
                  workshop_widget = {"w": None}
                  role_widget = {"w": None}
                  core_phrase_widget = {"w": None}
                  dna_static_widgets = {}
                  balance_gnd_widget = {"w": None}
                  balance_tepl_widget = {"w": None}
                  home_story_widget = {"w": None}
                  # Виджеты локации
                  loc_capacity_widget = {"w": None}
                  loc_scale_widget = {"w": None}
                  loc_lighting_widget = {"w": None}
                  loc_atmosphere_widget = {"w": None}
                  loc_neighbors_widget = {"w": None}
                  loc_quarter_widget = {"w": None}   # Quarter локации
                  agent_quarter_widget = {"w": None} # Quarter агента
                  loc_map_x_widget = {"w": None}
                  loc_map_y_widget = {"w": None}
                  loc_map_w_widget = {"w": None}
                  loc_map_h_widget = {"w": None}
                  # Виджеты ассета
                  asset_tags_widget = {"w": None}
                  asset_mood_widget = {"w": None}
                  asset_use_cases_widget = {"w": None}
                  asset_visual_anchor_widget = {"w": None}

                  with ui.element("div").classes("reg-block").style("margin-bottom:0"):
                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">⬡</div>')
                        ui.html("<h3>Тип Объекта</h3>")
                        ui.html('<div class="tag">Определяет поля</div>')
                    with ui.element("div").classes("reg-block-body"):
                        with ui.element("div").classes("obj-type-grid"):
                            type_configs = [
                                ("agent",    "👤", "Агент",    "Гражданин"),
                                ("location", "🏛️", "Локация",  "Место"),
                                ("asset",    "🎭", "Ассет",    "Проп"),
                            ]
                            for t_id, t_icon, t_label, t_desc in type_configs:
                                def make_type_click(tid=t_id):
                                    def on_click():
                                        current_obj_type["value"] = tid
                                        update_type_blocks()
                                    return on_click
                                btn = ui.element("div").classes("obj-type-btn").on("click", make_type_click(t_id))
                                with btn:
                                    ui.html(f'<div class="type-icon">{t_icon}</div>')
                                    ui.html(f'<div class="type-label">{t_label}</div>')
                                    ui.html(f'<div style="font-size:0.62rem;opacity:0.6">{t_desc}</div>')
                                type_btns[t_id] = btn

                  # ── Image upload ──
                  with ui.element("div").classes("reg-block").style("margin-bottom:0"):
                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">⬡</div>')
                        ui.html("<h3>Изображение</h3>")
                        ui.html('<div class="tag">Визуал</div>')
                    with ui.element("div").classes("reg-block-body"):
                        image_preview_container = ui.column().classes("w-full")
                        with image_preview_container:
                            async def handle_upload(e: events.UploadEventArguments):
                                content = e.content.read()
                                img_path = save_image(content, e.name)
                                current_image_path["value"] = img_path
                                refresh_image_preview()
                            upload = ui.upload(
                                label="Перетащи или выбери",
                                on_upload=handle_upload,
                                auto_upload=True,
                                max_file_size=10_000_000,
                            ).props('accept="image/*" flat bordered').classes("w-full").style(
                                "background: var(--r-void); border: 2px dashed var(--r-border); border-radius: 5px"
                            )
                            img_preview_element = ui.column().classes("w-full")

                def update_rarity_buttons():
                    for r, b in rarity_buttons.items():
                        b.classes(remove=f"active-{r.lower()}")
                        if r == current_rarity["value"]:
                            b.classes(add=f"active-{r.lower()}")

                def refresh_image_preview():
                    img_preview_element.clear()
                    if current_image_path["value"]:
                        img_rel = current_image_path["value"].replace(str(IMAGES_DIR), "/registry_images")
                        with img_preview_element:
                            with ui.row().classes("items-center gap-2 mt-2"):
                                ui.image(img_rel).classes("reg-img-preview")
                                ui.button(
                                    "✕ Удалить",
                                    on_click=lambda: remove_current_image()
                                ).classes("reg-btn").props("flat color=red size=sm")

                def remove_current_image():
                    if current_image_path["value"] and editing_index["value"] < 0:
                        delete_image(current_image_path["value"])
                    current_image_path["value"] = ""
                    refresh_image_preview()

                def update_type_blocks():
                    t = current_obj_type["value"]
                    for tid, btn in type_btns.items():
                        btn.classes(remove=f"active-{tid}")
                        if tid == t:
                            btn.classes(add=f"active-{tid}")
                    for ref, types in [
                        (agent_block_ref,    ["agent"]),
                        (location_block_ref, ["location"]),
                        (asset_block_ref,    ["asset"]),
                    ]:
                        if ref["el"]:
                            ref["el"].set_visibility(t in types)

                # ── АГЕНТ: Цифровая ДНК ──
                with ui.element("div").classes("reg-block dna-block") as _agent_block:
                    agent_block_ref["el"] = _agent_block
                    _agent_block.set_visibility(False)

                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">🧬</div>')
                        ui.html("<h3>Цифровая ДНК · Студия</h3>")
                        ui.html('<div class="tag">Только для агентов</div>')
                    with ui.element("div").classes("reg-block-body"):

                        # Цех и роль
                        with ui.grid(columns=2).classes("w-full gap-3 mb-3"):
                            with ui.column().classes("w-full gap-0"):
                                _WORKSHOP_QUARTER = {"residents": "Высотка", "turbo": "Квартал Мастеров", "social_mix": "Квартал Мастеров", "video_long": "Квартал Мастеров", "video_shorts": "Квартал Мастеров", "web_story": "Квартал Мастеров", "clipmakers": "Квартал Мастеров", "advertising": "Квартал Мастеров", "emo_card": "Квартал Мастеров", "logo_design": "Квартал Мастеров", "market_hit": "Квартал Мастеров", "living_book": "Квартал Мастеров", "trading": "Торговый Квартал"}
                                def on_workshop_change(e):
                                    ws = e.value or ""
                                    # ЗАКОН КАРТРИДЖА: роли — из phases манифеста цеха
                                    opts = get_role_options(ws)
                                    new_options = {v: v if v else "— не задана —" for v in opts}
                                    # Автозаполнение квартала: манифест цеха → словарь → дефолт
                                    if agent_quarter_widget["w"] and ws:
                                        _cart = None
                                        try:
                                            from studio.modules_registry import get_cartridge
                                            _cart = get_cartridge(ws)
                                        except Exception:
                                            _cart = None
                                        auto_q = (_cart or {}).get("quarter") or _WORKSHOP_QUARTER.get(ws, "Квартал Мастеров")
                                        agent_quarter_widget["w"].value = auto_q
                                        agent_quarter_widget["w"].update()
                                    if role_widget["w"]:
                                        role_widget["w"].options = new_options
                                        role_widget["w"].value = ""
                                        role_widget["w"].update()

                                workshop_widget["w"] = ui.select(
                                    label="Workshop_ID (Цех)",
                                    options={v: v if v else "— выбрать цех —" for v in get_workshop_options()},
                                    on_change=on_workshop_change,
                                ).classes("w-full")

                            with ui.column().classes("w-full gap-0"):
                                role_widget["w"] = ui.select(
                                    label="Роль",
                                    options={v: v if v else "— не задана —" for v in TURBO_ROLE_OPTIONS}
                                ).classes("w-full")

                        # Коронная фраза
                        core_phrase_widget["w"] = ui.input(
                            label="Коронная фраза (неизменяемая)",
                            placeholder="Три удара — и зритель твой..."
                        ).classes("w-full mb-3")

                        # Якорные точки
                        ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">⚓ Якорные точки (3-5 вечных констант)</div>')
                        anchor_points_widget["w"] = ui.textarea(
                            label="Anchor Points",
                            placeholder="1. Я родился из искры первого рендера\n2. Мой Творец — Евген\n3. Мой цвет — золото на чёрном\n4. Моя клятва — делать только живое"
                        ).classes("w-full mb-3")

                        # Резонанс
                        ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">🔮 Резонансный профиль</div>')
                        with ui.grid(columns=2).classes("w-full gap-3 mb-3"):
                            with ui.column().classes("w-full gap-0"):
                                pull_vector_widget["w"] = ui.input(
                                    label="Вектор тяги (что любит, к чему тянет душу)",
                                    placeholder="Любит копаться в старых архивах, ценит тишину и порядок..."
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                hidden_taste_widget["w"] = ui.input(
                                    label="Скрытый вкус (эстетический отклик)",
                                    placeholder="Резонирует с минимализмом и точными данными..."
                                ).classes("w-full")
                            with ui.column().classes("w-full col-span-2 gap-0"):
                                trigger_keywords_widget["w"] = ui.input(
                                    label="Триггеры памяти (через запятую)",
                                    placeholder="Тренд, Алгоритм, Хук, Вирусность..."
                                ).classes("w-full")

                        # Квартал агента (автозаполняется по цеху)
                        quarter_opts_agent = {"": "— выбрать квартал —"}
                        quarter_opts_agent.update({
                            "Высотка": "Высотка",
                            "Квартал Мастеров": "Квартал Мастеров",
                            "Торговый Квартал": "Торговый Квартал",
                        })
                        agent_quarter_widget["w"] = ui.select(
                            label="Квартал города",
                            options=quarter_opts_agent,
                        ).classes("w-full mb-3")

                        # Статические веса
                        ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.1em;margin:4px 0 10px">Статическая ДНК · задаётся один раз</div>')
                        for param_id, param_name, param_desc, param_default in DNA_STATIC_PARAMS:
                            with ui.element("div").classes("dna-row"):
                                ui.html(f'<div class="dna-label" title="{param_desc}">{param_name}</div>')
                                sl = ui.slider(min=0.0, max=1.0, value=param_default, step=0.05).classes("flex-1")
                                val_lbl = ui.html(f'<div class="dna-val">{param_default:.2f}</div>')
                                sl.on("update:model-value", lambda e, vl=val_lbl: vl.set_content(f'<div class="dna-val">{float(e.args):.2f}</div>'))
                                dna_static_widgets[param_id] = sl

                        # Инфо о динамических весах (только отображение — не редактируется)
                        ui.html('''
                            <div style="margin-top:14px;padding:10px 12px;background:rgba(136,85,204,0.06);
                                border:1px solid rgba(136,85,204,0.2);border-radius:4px;
                                font-size:0.72rem;color:var(--r-text-dim);font-family:\'Fira Code\',monospace">
                                <div style="color:#cc99ff;margin-bottom:4px">⚡ Динамические веса — инициализируются автоматически</div>
                                Respect: 1.0 · Patience: 1.0 · Stress: 0.0 · Internal_Light: 0.8<br>
                                <span style="opacity:0.6">Меняются в процессе жизни агента — pipeline, feedback, события</span>
                            </div>
                        ''')

                        # Баланс токенов
                        ui.html('<div style="font-size:0.72rem;color:var(--r-text-dim);text-transform:uppercase;letter-spacing:0.1em;margin:14px 0 8px">Стартовый баланс токенов</div>')
                        with ui.element("div").classes("balance-row"):
                            with ui.element("div").classes("balance-item"):
                                ui.html('<div class="balance-icon">💰</div>')
                                with ui.column().classes("balance-info gap-0"):
                                    ui.html('<div class="balance-name">GROND (GND)</div>')
                                    balance_gnd_widget["w"] = ui.number(value=0, min=0, step=100).style(
                                        "font-size:0.9rem;color:var(--r-gold);font-family:'Fira Code',monospace"
                                    ).props("dense borderless")
                            with ui.element("div").classes("balance-item"):
                                ui.html('<div class="balance-icon">🔆</div>')
                                with ui.column().classes("balance-info gap-0"):
                                    ui.html('<div class="balance-name">Теплики</div>')
                                    balance_tepl_widget["w"] = ui.number(value=0, min=0, step=100).style(
                                        "font-size:0.9rem;color:var(--r-gold);font-family:'Fira Code',monospace"
                                    ).props("dense borderless")

                # ── Двухколоночный layout формы ──
                with ui.element("div").style(
                    "display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;width:100%;"
                ):

                  # ═══ ЛЕВАЯ КОЛОНКА ═══
                  with ui.element("div").style("display:flex;flex-direction:column;gap:0"):

                    # Блоки 1,2,3 (Идентификация, Социальный, Физическое)
                    for block in BLOCKS[:3]:
                        with ui.element("div").classes("reg-block"):
                            with ui.element("div").classes("reg-block-header"):
                                ui.html(f'<div class="icon">{block["icon"]}</div>')
                                ui.html(f'<h3>{block["title"]}</h3>')
                                ui.html(f'<div class="tag">{block["tag"]}</div>')
                            with ui.element("div").classes("reg-block-body"):
                                with ui.grid(columns=2).classes("w-full gap-3"):
                                    for field_name, field_type, placeholder, full_width in block["fields"]:
                                        col_span = "col-span-2" if full_width else ""
                                        with ui.column().classes(f"w-full {col_span} gap-0"):
                                            if field_type == "input":
                                                inp = ui.input(label=field_name, placeholder=placeholder).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "date":
                                                inp = ui.input(label=field_name).classes("w-full")
                                                inp.value = datetime.now().strftime("%Y-%m-%d")
                                                form_data[field_name] = inp
                                            elif field_type == "textarea":
                                                inp = ui.textarea(label=field_name, placeholder=placeholder).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "select":
                                                options = {v: v if v else "— выбрать —" for v in placeholder}
                                                inp = ui.select(label=field_name, options=options).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "slider":
                                                min_v, max_v, default_v = placeholder
                                                with ui.row().classes("w-full items-center gap-2"):
                                                    ui.label(field_name).style("font-size:0.72rem;color:var(--r-text-dim);letter-spacing:0.08em;text-transform:uppercase;font-family:'Fira Code',monospace")
                                                    sl = ui.slider(min=min_v, max=max_v, value=default_v, step=1).classes("flex-1")
                                                    val_label = ui.label(str(default_v)).style("color:var(--r-gold);font-weight:500;min-width:20px")
                                                    sl.on("update:model-value", lambda e, vl=val_label: vl.set_text(str(e.args)))
                                                    form_data[field_name] = sl

                  # ═══ ПРАВАЯ КОЛОНКА ═══
                  with ui.element("div").style("display:flex;flex-direction:column;gap:0"):

                    # Блоки 4,5,6 (Глубинная суть, Динамика, Печать)
                    for block in BLOCKS[3:]:
                        with ui.element("div").classes("reg-block"):
                            with ui.element("div").classes("reg-block-header"):
                                ui.html(f'<div class="icon">{block["icon"]}</div>')
                                ui.html(f'<h3>{block["title"]}</h3>')
                                ui.html(f'<div class="tag">{block["tag"]}</div>')
                            with ui.element("div").classes("reg-block-body"):
                                with ui.grid(columns=2).classes("w-full gap-3"):
                                    for field_name, field_type, placeholder, full_width in block["fields"]:
                                        col_span = "col-span-2" if full_width else ""
                                        with ui.column().classes(f"w-full {col_span} gap-0"):
                                            if field_type == "input":
                                                inp = ui.input(label=field_name, placeholder=placeholder).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "date":
                                                inp = ui.input(label=field_name).classes("w-full")
                                                inp.value = datetime.now().strftime("%Y-%m-%d")
                                                form_data[field_name] = inp
                                            elif field_type == "textarea":
                                                inp = ui.textarea(label=field_name, placeholder=placeholder).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "select":
                                                options = {v: v if v else "— выбрать —" for v in placeholder}
                                                inp = ui.select(label=field_name, options=options).classes("w-full")
                                                form_data[field_name] = inp
                                            elif field_type == "slider":
                                                min_v, max_v, default_v = placeholder
                                                with ui.row().classes("w-full items-center gap-2"):
                                                    ui.label(field_name).style("font-size:0.72rem;color:var(--r-text-dim);letter-spacing:0.08em;text-transform:uppercase;font-family:'Fira Code',monospace")
                                                    sl = ui.slider(min=min_v, max=max_v, value=default_v, step=1).classes("flex-1")
                                                    val_label = ui.label(str(default_v)).style("color:var(--r-gold);font-weight:500;min-width:20px")
                                                    sl.on("update:model-value", lambda e, vl=val_label: vl.set_text(str(e.args)))
                                                    form_data[field_name] = sl

                # ── ЛОКАЦИЯ: Место в Грондхейме ──
                with ui.element("div").classes("reg-block loc-block") as _location_block:
                    location_block_ref["el"] = _location_block
                    _location_block.set_visibility(False)

                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">🏛️</div>')
                        ui.html("<h3>Место в Грондхейме</h3>")
                        ui.html('<div class="tag">Только для локаций</div>')
                    with ui.element("div").classes("reg-block-body"):

                        # Строка 1: ёмкость + размер
                        with ui.grid(columns=2).classes("w-full gap-3 mb-2"):
                            with ui.column().classes("w-full gap-0"):
                                loc_capacity_widget["w"] = ui.number(
                                    label="Сколько агентов вмещает",
                                    value=10, min=1
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                loc_scale_widget["w"] = ui.select(
                                    label="Размер места",
                                    options={
                                        "": "— выбрать —",
                                        "tiny": "Маленькое (1-3)",
                                        "small": "Небольшое (3-10)",
                                        "medium": "Среднее (10-30)",
                                        "large": "Большое (30-100)",
                                        "vast": "Огромное (100+)",
                                    }
                                ).classes("w-full")

                        # Строка 2: время суток / атмосфера
                        with ui.grid(columns=2).classes("w-full gap-3 mb-2"):
                            with ui.column().classes("w-full gap-0"):
                                loc_lighting_widget["w"] = ui.select(
                                    label="Время суток / свет",
                                    options={
                                        "": "— выбрать —",
                                        "dawn": "Рассвет · золотой туман",
                                        "day": "День · яркое солнце",
                                        "dusk": "Закат · янтарный свет",
                                        "night": "Ночь · темно",
                                        "neon": "Неон · вечный полумрак",
                                        "mystical": "Мистика · нет времени",
                                    }
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                ui.html('<div style="font-size:0.65rem;color:var(--r-text-dim);margin-bottom:4px">Атмосфера (теги через запятую)</div>')
                                loc_atmosphere_widget["w"] = ui.input(
                                    placeholder="#тишина #архивы #запах_бумаги #янтарный_свет..."
                                ).classes("w-full")

                        # Строка 3: соседние локации
                        ui.html('<div style="font-size:0.65rem;color:var(--r-text-dim);margin-bottom:4px">Соседние места (куда можно пойти отсюда)</div>')
                        loc_neighbors_widget["w"] = ui.input(
                            placeholder="Библиотека, Берег, Гавань..."
                        ).classes("w-full mb-3")

                        # Квартал локации
                        quarter_opts_loc = {"": "— выбрать квартал —"}
                        quarter_opts_loc.update({
                            "Высотка": "Высотка",
                            "Квартал Мастеров": "Квартал Мастеров",
                            "Торговый Квартал": "Торговый Квартал",
                        })
                        loc_quarter_widget["w"] = ui.select(
                            label="Квартал города",
                            options=quarter_opts_loc,
                        ).classes("w-full mb-3")

                        # Координаты на карте
                        ui.html('''
                            <div style="font-size:0.72rem;color:var(--r-text-dim);
                            text-transform:uppercase;letter-spacing:0.08em;
                            margin:8px 0 10px;padding-top:8px;
                            border-top:1px solid var(--r-border)">
                            📍 Область на карте Грондхейма
                            </div>
                            <div style="font-size:0.62rem;color:var(--r-text-dim);margin-bottom:8px;opacity:0.7">
                            Открой GRONDHEM.png в Paint, наведи на угол области — запиши X,Y.<br>
                            Затем укажи ширину и высоту прямоугольника локации.
                            </div>
                        ''')
                        with ui.grid(columns=4).classes("w-full gap-2"):
                            with ui.column().classes("w-full gap-0"):
                                loc_map_x_widget["w"] = ui.number(
                                    label="X (лево)", value=0, min=0
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                loc_map_y_widget["w"] = ui.number(
                                    label="Y (верх)", value=0, min=0
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                loc_map_w_widget["w"] = ui.number(
                                    label="Ширина", value=400, min=50
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                loc_map_h_widget["w"] = ui.number(
                                    label="Высота", value=300, min=50
                                ).classes("w-full")

                # ── АССЕТ: Каталог студии ──
                with ui.element("div").classes("reg-block asset-block") as _asset_block:
                    asset_block_ref["el"] = _asset_block
                    _asset_block.set_visibility(False)

                    with ui.element("div").classes("reg-block-header"):
                        ui.html('<div class="icon">🎭</div>')
                        ui.html("<h3>Каталог Ассетов</h3>")
                        ui.html('<div class="tag">Для Стеллы и Визора</div>')
                    with ui.element("div").classes("reg-block-body"):
                        with ui.grid(columns=2).classes("w-full gap-3"):
                            with ui.column().classes("w-full col-span-2 gap-0"):
                                asset_visual_anchor_widget["w"] = ui.input(
                                    label="Visual Anchor (неизменяемые детали для промптов)",
                                    placeholder="brown tweed jacket, golden round glasses, tablet with 'Story Arc'..."
                                ).classes("w-full")
                            with ui.column().classes("w-full col-span-2 gap-0"):
                                asset_tags_widget["w"] = ui.input(
                                    label="Tags (через запятую)",
                                    placeholder="business, professional, storyteller, warm..."
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                asset_mood_widget["w"] = ui.input(
                                    label="Mood",
                                    placeholder="inspiring, serious, calm..."
                                ).classes("w-full")
                            with ui.column().classes("w-full gap-0"):
                                asset_use_cases_widget["w"] = ui.input(
                                    label="Use Cases (через запятую)",
                                    placeholder="product_demo, corporate, education..."
                                ).classes("w-full")

                # ── Action buttons ──
                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Очистить", on_click=lambda: clear_form()).classes("reg-btn").props(
                        "flat").style("border: 1px solid var(--r-border); color: var(--r-text)")

                    save_btn = ui.button("Сохранить в каталог", on_click=lambda: save_object()).classes(
                        "reg-btn").style("background: var(--r-gold); color: var(--r-void)")

                def collect_form() -> dict:
                    """Collect all form values into a dict."""
                    obj = {
                        "Rarity": current_rarity["value"],
                        "Object_Type_Class": current_obj_type["value"],  # agent/location/asset
                    }
                    for name, widget in form_data.items():
                        val = widget.value
                        if name == "Access_Level":
                            val = int(val) if val else 5
                        elif name == "Interaction_Scripts" and isinstance(val, str) and val:
                            val = [s.strip() for s in val.replace("\n", ",").split(",") if s.strip()]
                        obj[name] = val if val else ""
                    if current_image_path["value"]:
                        obj["_image_path"] = current_image_path["value"]

                    t = current_obj_type["value"]

                    # Агент
                    if t == "agent":
                        if agent_quarter_widget["w"]: obj["Quarter"] = agent_quarter_widget["w"].value or ""
                        if workshop_widget["w"]: obj["Workshop_ID"] = workshop_widget["w"].value or ""
                        if role_widget["w"]: obj["Turbo_Role"] = role_widget["w"].value or ""
                        if core_phrase_widget["w"]: obj["Core_Phrase"] = core_phrase_widget["w"].value or ""
                        if anchor_points_widget["w"]: obj["Anchor_Points"] = anchor_points_widget["w"].value or ""
                        if home_story_widget["w"]: obj["Home_Story"] = home_story_widget["w"].value or ""
                        if pull_vector_widget["w"]: obj["Pull_Vector"] = pull_vector_widget["w"].value or ""
                        if hidden_taste_widget["w"]: obj["Hidden_Taste"] = hidden_taste_widget["w"].value or ""
                        if trigger_keywords_widget["w"]: obj["Trigger_Keywords"] = trigger_keywords_widget["w"].value or ""
                        if balance_gnd_widget["w"]: obj["Balance_GND"] = float(balance_gnd_widget["w"].value or 0)
                        if balance_tepl_widget["w"]: obj["Balance_Tepl"] = float(balance_tepl_widget["w"].value or 0)
                        dna = {}
                        for p_id, _, _, _ in DNA_STATIC_PARAMS:
                            if p_id in dna_static_widgets:
                                dna[p_id] = float(dna_static_widgets[p_id].value or 0)
                        obj["DNA_Static"] = dna

                    # Локация
                    elif t == "location":
                        if loc_quarter_widget["w"]: obj["Quarter"] = loc_quarter_widget["w"].value or ""
                        if loc_capacity_widget["w"]: obj["Capacity"] = int(loc_capacity_widget["w"].value or 10)
                        if loc_scale_widget["w"]: obj["Scale"] = loc_scale_widget["w"].value or ""
                        if loc_lighting_widget["w"]: obj["Lighting"] = loc_lighting_widget["w"].value or ""
                        if loc_atmosphere_widget["w"]: obj["Style_Tags"] = loc_atmosphere_widget["w"].value or ""
                        if loc_neighbors_widget["w"]: obj["Location_Connections"] = loc_neighbors_widget["w"].value or ""
                        if loc_map_x_widget["w"]: obj["Map_X"] = int(loc_map_x_widget["w"].value or 0)
                        if loc_map_y_widget["w"]: obj["Map_Y"] = int(loc_map_y_widget["w"].value or 0)
                        if loc_map_w_widget["w"]: obj["Map_W"] = int(loc_map_w_widget["w"].value or 400)
                        if loc_map_h_widget["w"]: obj["Map_H"] = int(loc_map_h_widget["w"].value or 300)

                    # Ассет
                    elif t == "asset":
                        if asset_visual_anchor_widget["w"]: obj["Visual_Anchor"] = asset_visual_anchor_widget["w"].value or ""
                        if asset_tags_widget["w"]:
                            raw = asset_tags_widget["w"].value or ""
                            obj["Tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                        if asset_mood_widget["w"]: obj["Mood"] = asset_mood_widget["w"].value or ""
                        if asset_use_cases_widget["w"]:
                            raw = asset_use_cases_widget["w"].value or ""
                            obj["Use_Cases"] = [u.strip() for u in raw.split(",") if u.strip()]

                    return obj

                def populate_form(obj: dict):
                    """Fill form from object dict."""
                    current_rarity["value"] = obj.get("Rarity", "")
                    update_rarity_buttons()

                    # Тип объекта
                    t = obj.get("Object_Type_Class", "")
                    current_obj_type["value"] = t
                    update_type_blocks()

                    for name, widget in form_data.items():
                        val = obj.get(name, "")
                        if name == "Interaction_Scripts" and isinstance(val, list):
                            val = ", ".join(val)
                        widget.value = val
                    current_image_path["value"] = obj.get("_image_path", "")
                    refresh_image_preview()

                    # Агент
                    if t == "agent":
                        if agent_quarter_widget["w"]: agent_quarter_widget["w"].value = obj.get("Quarter", "")
                        if workshop_widget["w"]: workshop_widget["w"].value = obj.get("Workshop_ID", "")
                        if role_widget["w"]: role_widget["w"].value = obj.get("Turbo_Role", "")
                        if core_phrase_widget["w"]: core_phrase_widget["w"].value = obj.get("Core_Phrase", "")
                        if anchor_points_widget["w"]: anchor_points_widget["w"].value = obj.get("Anchor_Points", "")
                        if home_story_widget["w"]: home_story_widget["w"].value = obj.get("Home_Story", "")
                        if pull_vector_widget["w"]: pull_vector_widget["w"].value = obj.get("Pull_Vector", "")
                        if hidden_taste_widget["w"]: hidden_taste_widget["w"].value = obj.get("Hidden_Taste", "")
                        if trigger_keywords_widget["w"]: trigger_keywords_widget["w"].value = obj.get("Trigger_Keywords", "")
                        if balance_gnd_widget["w"]: balance_gnd_widget["w"].value = obj.get("Balance_GND", 0)
                        if balance_tepl_widget["w"]: balance_tepl_widget["w"].value = obj.get("Balance_Tepl", 0)
                        dna = obj.get("DNA_Static", {})
                        for p_id, _, _, default in DNA_STATIC_PARAMS:
                            if p_id in dna_static_widgets:
                                dna_static_widgets[p_id].value = dna.get(p_id, default)
                    # Локация
                    elif t == "location":
                        if loc_quarter_widget["w"]: loc_quarter_widget["w"].value = obj.get("Quarter", "")
                        if loc_capacity_widget["w"]: loc_capacity_widget["w"].value = obj.get("Capacity", 10)
                        if loc_scale_widget["w"]: loc_scale_widget["w"].value = obj.get("Scale", "")
                        if loc_lighting_widget["w"]: loc_lighting_widget["w"].value = obj.get("Lighting", "")
                        if loc_atmosphere_widget["w"]: loc_atmosphere_widget["w"].value = obj.get("Style_Tags", "")
                        if loc_neighbors_widget["w"]: loc_neighbors_widget["w"].value = obj.get("Location_Connections", "")
                        if loc_map_x_widget["w"]: loc_map_x_widget["w"].value = obj.get("Map_X", 0)
                        if loc_map_y_widget["w"]: loc_map_y_widget["w"].value = obj.get("Map_Y", 0)
                        if loc_map_w_widget["w"]: loc_map_w_widget["w"].value = obj.get("Map_W", 400)
                        if loc_map_h_widget["w"]: loc_map_h_widget["w"].value = obj.get("Map_H", 300)
                    # Ассет
                    elif t == "asset":
                        if asset_visual_anchor_widget["w"]: asset_visual_anchor_widget["w"].value = obj.get("Visual_Anchor", "")
                        if asset_tags_widget["w"]: asset_tags_widget["w"].value = ", ".join(obj.get("Tags", []))
                        if asset_mood_widget["w"]: asset_mood_widget["w"].value = obj.get("Mood", "")
                        if asset_use_cases_widget["w"]: asset_use_cases_widget["w"].value = ", ".join(obj.get("Use_Cases", []))

                def clear_form():
                    """Reset all form fields."""
                    current_rarity["value"] = ""
                    current_obj_type["value"] = ""
                    update_rarity_buttons()
                    update_type_blocks()
                    for name, widget in form_data.items():
                        if name == "Creation_Date":
                            widget.value = datetime.now().strftime("%Y-%m-%d")
                        elif name == "Access_Level":
                            widget.value = 5
                        else:
                            widget.value = ""
                    current_image_path["value"] = ""
                    refresh_image_preview()
                    editing_index["value"] = -1
                    save_btn.text = "Сохранить в каталог"
                    upload.reset()
                    # Сбрасываем агент-поля
                    for p_id, _, _, default in DNA_STATIC_PARAMS:
                        if p_id in dna_static_widgets:
                            dna_static_widgets[p_id].value = default
                    for w in [workshop_widget, role_widget, core_phrase_widget,
                              anchor_points_widget, home_story_widget,
                              pull_vector_widget, hidden_taste_widget, trigger_keywords_widget]:
                        if w["w"]: w["w"].value = ""
                    for w in [balance_gnd_widget, balance_tepl_widget]:
                        if w["w"]: w["w"].value = 0
                    # Сбрасываем локацию
                    if loc_capacity_widget["w"]: loc_capacity_widget["w"].value = 10
                    if loc_quarter_widget["w"]: loc_quarter_widget["w"].value = ""
                    if agent_quarter_widget["w"]: agent_quarter_widget["w"].value = ""
                    for w in [loc_scale_widget, loc_lighting_widget,
                              loc_atmosphere_widget, loc_neighbors_widget]:
                        if w["w"]: w["w"].value = ""
                    for w, default in [(loc_map_x_widget, 0), (loc_map_y_widget, 0),
                                       (loc_map_w_widget, 400), (loc_map_h_widget, 300)]:
                        if w["w"]: w["w"].value = default
                    # Сбрасываем ассет
                    for w in [asset_visual_anchor_widget, asset_tags_widget, asset_mood_widget, asset_use_cases_widget]:
                        if w["w"]: w["w"].value = ""

                def save_object():
                    """Save or update object in catalog."""
                    nonlocal catalog
                    obj = collect_form()

                    if not obj.get("ID_Object") or not obj.get("Official_Name"):
                        ui.notify("Заполни ID и Имя!", type="negative")
                        return

                    # Check duplicate ID
                    dup_idx = next((i for i, o in enumerate(catalog) if o["ID_Object"] == obj["ID_Object"]), -1)
                    if dup_idx != -1 and dup_idx != editing_index["value"]:
                        ui.notify("ID уже существует!", type="negative")
                        return

                    obj["_timestamp"] = datetime.now().isoformat()

                    # ── Печать Создателя: хешируем секретную фразу ──
                    seal = obj.get("Creator_Seal", "").strip()
                    if seal:
                        obj["_Creator_Seal_Hash"] = hashlib.sha256(seal.encode("utf-8")).hexdigest()
                    else:
                        obj["_Creator_Seal_Hash"] = ""

                    if editing_index["value"] >= 0:
                        old = catalog[editing_index["value"]]
                        if old.get("_image_path") and old["_image_path"] != obj.get("_image_path"):
                            delete_image(old["_image_path"])
                        catalog[editing_index["value"]] = obj
                    else:
                        catalog.append(obj)

                    save_catalog(catalog)

                    # ── PATCH_DVA_FILA: второй файл — паспорт-кусочек на свой этаж ──
                    try:
                        _kus = rodit_pasport_kusochek(obj)
                        # PATCH_4_SLOYA: заводим 4 слоя на этаже жителя
                        try:
                            _dom = zavesti_sloi(obj)
                            if _dom:
                                ui.notify(f"4 слоя заведены: {_dom}", type="positive", timeout=4000)
                        except Exception as _e2:
                            ui.notify(f"⚠ слои не завелись: {_e2}", type="warning")
                        if _kus:
                            ui.notify(f"Паспорт-кусочек: {_kus}", type="positive", timeout=4000)
                    except Exception as _e:
                        ui.notify(f"⚠ кусочек не родился: {_e}", type="warning")

                    # ── Генерация файлов студии для агентов ──
                    generated = []
                    # PATCH_DVA_FILA: папки-слои отключены — это СЛЕДУЮЩИЙ шаг.
                    # Сейчас рождаем только паспорт (куча + кусочек). Памяти нет.
                    if False and obj.get("Object_Type_Class") == "agent":
                        try:
                            dna_static = obj.get("DNA_Static", {})
                            dna_dynamic = dict(DNA_DYNAMIC_DEFAULTS)
                            generated = generate_agent_files(
                                obj=obj,
                                dna_static=dna_static,
                                core_phrase=obj.get("Core_Phrase", ""),
                                anchor_points=obj.get("Anchor_Points", ""),
                                home_story=obj.get("Home_Story", ""),
                                pull_vector=obj.get("Pull_Vector", ""),
                                hidden_taste=obj.get("Hidden_Taste", ""),
                                trigger_keywords=obj.get("Trigger_Keywords", ""),
                                workshop=obj.get("Workshop_ID", ""),
                                agent_role=obj.get("Turbo_Role", ""),
                                balance_gnd=obj.get("Balance_GND", 0),
                                balance_tepl=obj.get("Balance_Tepl", 0),
                            )
                            if generated:
                                ui.notify(f"✓ Файлы агента созданы: {len(generated)} файлов", type="positive", timeout=6000)
                        except Exception as e:
                            ui.notify(f"⚠ Ошибка генерации файлов: {e}", type="warning")

                    clear_form()
                    msg = "Объект сохранён ✓"
                    if generated:
                        msg += f" · {len(generated)} файлов → studio/modules/"
                    ui.notify(msg, type="positive")

            # ═══════════════════════════════════════════
            # TAB: CATALOG
            # ═══════════════════════════════════════════
            with ui.tab_panel("catalog").style("padding: 0"):

                with ui.row().classes("w-full gap-2 mb-3 items-center"):
                    search_input = ui.input(
                        placeholder="Поиск по имени, ID, профессии..."
                    ).classes("reg-search flex-1").props("clearable dense")

                    filter_select = ui.select(
                        options={"": "Все классы", "Common": "Common", "Rare": "Rare", "Epic": "Epic", "Mythic": "Mythic"},
                        value=""
                    ).classes("reg-search").style("min-width: 130px").props("dense")

                stats_label = ui.label("").classes("reg-stats")
                catalog_container = ui.column().classes("w-full gap-2")

                def refresh_catalog():
                    nonlocal catalog
                    catalog = load_catalog()
                    q = (search_input.value or "").lower()
                    rf = filter_select.value or ""

                    filtered = []
                    for obj in catalog:
                        if rf and obj.get("Rarity") != rf:
                            continue
                        if q:
                            hay = " ".join(filter(None, [
                                obj.get("ID_Object", ""),
                                obj.get("Official_Name", ""),
                                obj.get("Profession", ""),
                                obj.get("Social_Rank", ""),
                                obj.get("Domain_Connection", ""),
                            ])).lower()
                            if q not in hay:
                                continue
                        filtered.append(obj)

                    # Stats
                    counts = {"Common": 0, "Rare": 0, "Epic": 0, "Mythic": 0}
                    for o in catalog:
                        r = o.get("Rarity", "")
                        if r in counts:
                            counts[r] += 1
                    stats_label.text = (
                        f"Всего: {len(catalog)}  ·  "
                        f"Common: {counts['Common']}  ·  Rare: {counts['Rare']}  ·  "
                        f"Epic: {counts['Epic']}  ·  Mythic: {counts['Mythic']}"
                    )

                    catalog_container.clear()
                    with catalog_container:
                        if not filtered:
                            with ui.element("div").classes("reg-empty w-full"):
                                ui.html('<div class="glyph">◇</div>')
                                ui.label("Каталог пуст")
                                ui.label("Создай первый объект во вкладке «Форма»").style("font-size: 0.75rem; margin-top: 4px")
                        else:
                            with ui.grid(columns=2).classes("w-full gap-2"):
                                for obj in filtered:
                                    real_idx = catalog.index(obj)
                                    rar = (obj.get("Rarity") or "Common").lower()

                                    def make_click(idx=real_idx):
                                        return lambda: show_detail(idx)

                                    with ui.element("div").classes(f"reg-card rar-{rar}").on("click", make_click()):
                                        with ui.row().classes("justify-between items-start w-full"):
                                            with ui.column().classes("gap-0"):
                                                ui.html(f'<div class="card-id">{obj.get("ID_Object", "")}</div>')
                                                ui.html(f'<div class="card-name">{obj.get("Official_Name", "")}</div>')
                                                rar_val = obj.get("Rarity", "")
                                                if rar_val:
                                                    ui.html(f'<span class="rar-badge badge-{rar_val.lower()}">{rar_val}</span>')
                                            # Thumbnail
                                            img_p = obj.get("_image_path", "")
                                            if img_p and Path(img_p).exists():
                                                img_url = img_p.replace(str(IMAGES_DIR), "/registry_images")
                                                ui.image(img_url).classes("card-thumb")

                                        meta_parts = []
                                        if obj.get("Social_Rank"):
                                            meta_parts.append(obj["Social_Rank"])
                                        if obj.get("Profession"):
                                            meta_parts.append(obj["Profession"])
                                        if meta_parts:
                                            ui.html(f'<div class="card-meta">{"  ·  ".join(meta_parts)}</div>')

                # Wire up search/filter
                search_input.on("update:model-value", lambda: refresh_catalog())
                filter_select.on("update:model-value", lambda: refresh_catalog())

                # Auto-refresh when tab is shown
                tab_catalog.on("click", lambda: refresh_catalog())

                def show_detail(idx: int):
                    """Show detail dialog for an object."""
                    obj = catalog[idx]

                    sections = [
                        ("Идентификация", ["ID_Object", "Official_Name", "Object_Type", "Author_Signature", "Creation_Date", "Rarity"]),
                        ("Социальный профиль", ["Social_Rank", "Profession", "Area_of_Responsibility", "Access_Level"]),
                        ("Физическое воплощение", ["Visual_Base", "Unique_Mark", "Material_Texture"]),
                        ("Глубинная суть", ["Hidden_History", "Sensory_Response", "Domain_Connection", "Relationships"]),
                        ("Динамика", ["Object_Behavior", "Interaction_Scripts"]),
                        ("Печать Создателя", ["Creator_Seal", "_Creator_Seal_Hash"]),
                    ]

                    with ui.dialog().classes("reg-detail") as dialog, ui.card().style("padding: 24px"):
                        # Image
                        img_p = obj.get("_image_path", "")
                        if img_p and Path(img_p).exists():
                            img_url = img_p.replace(str(IMAGES_DIR), "/registry_images")
                            ui.image(img_url).classes("reg-img-preview").style("margin-bottom: 14px")

                        for sec_title, fields in sections:
                            rows_html = ""
                            for f in fields:
                                val = obj.get(f, "")
                                if isinstance(val, list):
                                    val = ", ".join(val)
                                if val or val == 0:
                                    rows_html += f'<div class="det-row"><div class="det-label">{f}</div><div class="det-value">{val}</div></div>'
                            if rows_html:
                                ui.html(f'<div class="det-section"><h4>{sec_title}</h4>{rows_html}</div>')

                        with ui.row().classes("w-full gap-2 mt-3 pt-3").style("border-top: 1px solid var(--r-border)"):
                            def do_edit(i=idx):
                                dialog.close()
                                editing_index["value"] = i
                                populate_form(catalog[i])
                                save_btn.text = "Обновить объект"
                                tabs.value = "form"

                            def do_dupe(i=idx):
                                copy = json.loads(json.dumps(catalog[i]))
                                copy["ID_Object"] += "_copy"
                                copy["_timestamp"] = datetime.now().isoformat()
                                # Copy image too
                                if copy.get("_image_path") and Path(copy["_image_path"]).exists():
                                    old_path = Path(copy["_image_path"])
                                    new_name = f"{uuid.uuid4().hex[:12]}{old_path.suffix}"
                                    new_path = IMAGES_DIR / new_name
                                    shutil.copy2(old_path, new_path)
                                    copy["_image_path"] = str(new_path)
                                catalog.append(copy)
                                save_catalog(catalog)
                                dialog.close()
                                refresh_catalog()
                                ui.notify("Дублировано", type="positive")

                            def do_delete(i=idx):
                                obj_del = catalog[i]
                                if obj_del.get("_image_path"):
                                    delete_image(obj_del["_image_path"])
                                catalog.pop(i)
                                save_catalog(catalog)
                                dialog.close()
                                refresh_catalog()
                                ui.notify("Удалено", type="info")

                            ui.button("Редактировать", on_click=do_edit).classes("reg-btn").props("flat").style(
                                "border: 1px solid var(--r-border); color: var(--r-text)")
                            ui.button("Дублировать", on_click=do_dupe).classes("reg-btn").props("flat").style(
                                "border: 1px solid var(--r-border); color: var(--r-text)")
                            ui.button("Удалить", on_click=do_delete).classes("reg-btn").props("flat").style(
                                "border: 1px solid var(--r-red); color: var(--r-red)")
                            ui.space()
                            ui.button("Закрыть", on_click=dialog.close).classes("reg-btn").props("flat").style(
                                "color: var(--r-text-dim)")

                    dialog.open()

            # ═══════════════════════════════════════════
            # TAB: EXPORT
            # ═══════════════════════════════════════════
            with ui.tab_panel("export").style("padding: 0"):

                with ui.row().classes("w-full gap-2 mb-3 flex-wrap"):
                    ui.button("Копировать JSON", on_click=lambda: copy_json()).classes("reg-btn").style(
                        "background: var(--r-gold); color: var(--r-void)")
                    ui.button("Скачать каталог .json", on_click=lambda: download_catalog()).classes("reg-btn").props(
                        "flat").style("border: 1px solid var(--r-border); color: var(--r-text)")
                    ui.button("Скачать ERC-721 metadata", on_click=lambda: download_metadata()).classes("reg-btn").props(
                        "flat").style("border: 1px solid var(--r-border); color: var(--r-text)")

                    # Import
                    async def handle_import(e: events.UploadEventArguments):
                        nonlocal catalog
                        try:
                            content = e.content.read()
                            data = json.loads(content)
                            arr = data if isinstance(data, list) else [data]
                            existing_ids = {o["ID_Object"] for o in catalog}
                            added = 0
                            for obj in arr:
                                if obj.get("ID_Object") and obj.get("Official_Name") and obj["ID_Object"] not in existing_ids:
                                    catalog.append(obj)
                                    existing_ids.add(obj["ID_Object"])
                                    added += 1
                            save_catalog(catalog)
                            refresh_export()
                            ui.notify(f"Импортировано: {added} объектов", type="positive")
                        except Exception as ex:
                            ui.notify(f"Ошибка импорта: {ex}", type="negative")

                    ui.upload(
                        label="Импорт JSON",
                        on_upload=handle_import,
                        auto_upload=True,
                    ).props('accept=".json" flat dense').style(
                        "border: 1px solid var(--r-border); border-radius: 3px; max-width: 180px"
                    )

                json_container = ui.element("pre").classes("reg-json w-full")

                def refresh_export():
                    nonlocal catalog
                    catalog = load_catalog()
                    clean = []
                    for o in catalog:
                        c = _clean_for_export(o)
                        clean.append(c)
                    json_container.text = json.dumps(clean, ensure_ascii=False, indent=2) if clean else "// Каталог пуст"

                tab_export.on("click", lambda: refresh_export())

                def copy_json():
                    nonlocal catalog
                    catalog = load_catalog()
                    clean = [_clean_for_export(o) for o in catalog]
                    text = json.dumps(clean, ensure_ascii=False, indent=2)
                    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(text)})")
                    ui.notify("JSON скопирован", type="positive")

                def download_catalog():
                    nonlocal catalog
                    catalog = load_catalog()
                    clean = [_clean_for_export(o) for o in catalog]
                    out_path = REGISTRY_DIR / "export_catalog.json"
                    out_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
                    ui.download(str(out_path), "grondheim_catalog.json")

                def download_metadata():
                    nonlocal catalog
                    catalog = load_catalog()
                    if not catalog:
                        ui.notify("Каталог пуст", type="warning")
                        return
                    meta = generate_erc721_metadata(catalog)
                    out_path = REGISTRY_DIR / "export_erc721_metadata.json"
                    out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                    ui.download(str(out_path), "grondheim_erc721_metadata.json")
                    ui.notify("ERC-721 metadata экспортирован", type="positive")

            # ═══════════════════════════════════════════
            # TAB: GUIDE
            # ═══════════════════════════════════════════
            with ui.tab_panel("guide").style("padding: 0"):
                with ui.column().classes("reg-guide"):
                    ui.html("<h2>Как NFT попадает на блокчейн</h2>")
                    ui.html("<p>Весь путь от идеи до токена — 4 шага. Сейчас ты на первом.</p>")

                    steps = [
                        ("1", "Описываешь объект ← ты здесь",
                         "Заполняешь форму: имя, редкость, легенда, визуал. На выходе — JSON с метаданными. Это «паспорт» объекта."),
                        ("2", "Загружаешь на IPFS",
                         'Картинку и JSON загружаешь на <a href="https://www.pinata.cloud/" target="_blank" style="color:var(--r-rare)">Pinata</a> '
                         '(бесплатно). Файлы получают вечную ссылку <span class="guide-code">ipfs://Qm...</span>, которую нельзя подменить.'),
                        ("3", "Минтишь NFT",
                         'Смарт-контракт создаёт токен и привязывает к нему IPFS-ссылку. Нужен кошелёк '
                         '(<a href="https://metamask.io/" target="_blank" style="color:var(--r-rare)">MetaMask</a>) и немного крипты на газ.'),
                        ("4", "Объект живёт",
                         "NFT появляется на маркетплейсе (OpenSea, Rarible). Его можно показывать, продавать, передавать."),
                    ]
                    for num, title, desc in steps:
                        ui.html(f'''
                            <div class="guide-step">
                                <div class="guide-step-num">{num}</div>
                                <div class="guide-step-body">
                                    <b>{title}</b>
                                    <span>{desc}</span>
                                </div>
                            </div>
                        ''')

                    ui.html("<h2>Какой блокчейн выбрать?</h2>")
                    ui.html('<p>Рекомендация — <b style="color:var(--r-epic)">Polygon</b>. '
                            'Тот же стандарт ERC-721, те же маркетплейсы, но газ стоит доли цента.</p>')

                    ui.html("<h2>Хранение данных</h2>")
                    ui.html(f'<p>Все объекты хранятся в <span class="guide-code">{REGISTRY_DIR}/catalog.json</span>. '
                            f'Картинки — в <span class="guide-code">{IMAGES_DIR}/</span>. '
                            'Это реальные файлы на диске — никакой localStorage, никаких потерь при очистке кэша.</p>')

                    ui.html("<h2>Печать Создателя (Proof of Authorship)</h2>")
                    ui.html(
                        '<p>В блоке ⑥ ты вписываешь секретную фразу — <b style="color:var(--r-gold)">Печать</b>. '
                        'Это может быть что угодно: личное воспоминание, дата, кодовое слово.</p>'
                        '<p>При сохранении фраза хешируется алгоритмом SHA-256. '
                        'В экспорт уходит <b>только хеш</b> (строка из 64 символов), сама фраза — никогда.</p>'
                        '<p>Если кто-то оспаривает авторство — ты называешь свою фразу, '
                        'её хешируют, и хеш совпадает с тем что записан в блокчейне. Подделать невозможно.</p>'
                    )

                    ui.html("<h2>Формат ERC-721 metadata</h2>")
                    ui.html("<p>Маркетплейсы ожидают JSON такого вида:</p>")
                    example_json = json.dumps({
                        "name": "Лока",
                        "description": "Хранительница памяти Студии...",
                        "image": "ipfs://Qm...твой_хеш...",
                        "attributes": [
                            {"trait_type": "Rarity", "value": "Mythic"},
                            {"trait_type": "Social Rank", "value": "Хозяйка"},
                            {"trait_type": "Access Level", "display_type": "number", "value": 10},
                            {"trait_type": "Creator Seal Hash", "value": "a1b2c3d4e5...64 символа..."}
                        ]
                    }, ensure_ascii=False, indent=2)
                    ui.html(f'<pre class="reg-json" style="max-height:none">{example_json}</pre>')
                    ui.html('<p style="margin-top:10px">Кнопка «Скачать ERC-721 metadata» на вкладке Экспорт генерирует именно этот формат.</p>')
