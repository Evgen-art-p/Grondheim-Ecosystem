# -*- coding: utf-8 -*-
# AKADEMIA_KABINET_V1 — КАБИНЕТ АКАДЕМИИ (первый слой: экран)
"""
АКАДЕМИЯ · КАБИНЕТ · /akademia

СТИЛЬ — ВЕСЬ ОТ БИРЖИ (слово Шефа). Та же сетка (300 / центр / 260),
тот же хедер-пузырьки, та же левая колонка с загрузчиком, тот же стол
(тулбар + чат + отчёт-вьюер + плавающая консоль), та же правая колонка
(аватар + панели под ним). CSS снят с ui_torg.py один в один — Академия
самостоятельный модуль и не импортирует Биржу, поэтому копия, не ссылка
(Закон Двух Стандартов: внутри своё, на границе общее).

ЧТО ЭТО ЗА СЛОЙ (честно):
  Слой 1 — ЭКРАН. Пузырьки студентов, приёмка руды (текст + изображения),
  загрузчик библиотеки, навигация. Всё, что рисуется и живёт.
  Труба урока (просев -> вывод -> маяк -> метка) и разговор с учеником
  СЮДА НЕ ВШИТЫ. Их варим отдельным слоем, когда Шеф посмотрит экран.
  Пустая кнопка честнее вранья: где не построено — так и написано.

ПУЗЫРЬКИ = МЕСТА, до 10 (слово Шефа). Кто на месте — читается сканом
GRONDHEIM_CITY/Академия/ученики.json (Закон Картриджа: не держим реестр
в коде, спрашиваем данные). Пусто = честная вакансия, не ошибка.

`шесть·проверено·до·корня`
"""
import os
import sys
import json
import base64  # PATCH_AKADEMIA_VIZUAL_V1: кодируем картинку в data URL для мультимодального вызова
from pathlib import Path
from datetime import datetime, timezone

from nicegui import ui, app

# BELYY_SHRIFT_V1: читаемость на тёмном — см.
# postavit_belyy_shrift.py. Красим только то, что
# рисует Quasar своей светлой темой внутри наших
# тёмных карточек.
_BELYY_SHRIFT = r"""
/* BELYY_SHRIFT_V1 — читаемость на тёмном.
   Карточки диалогов рисуем мы (тёмные), а подписи внутри — Quasar по
   своей СВЕТЛОЙ теме. Отсюда тёмно-серые буквы на чёрном: в окне
   перевозки так пропадали имена жителей у галочек.
   Красим только то, что отдано Quasar'у. Кнопки и наши собственные
   раскрашенные надписи не трогаем — у них цвет задан руками. */
.q-dialog .q-card,
.q-dialog .q-card .q-item__label,
.q-dialog .q-card label,
.q-checkbox__label,
.q-radio__label,
.q-toggle__label,
.q-field__native,
.q-field__input,
.q-field__label,
.q-field__prefix,
.q-field__suffix,
.q-item__label,
.q-tab__label,
.q-select__dropdown-icon,
.q-menu .q-item,
.q-menu .q-item__label {
  color: rgba(255,255,255,0.92) !important;
}

/* Подсказка в пустом поле — белая, но приглушённая: она не должна
   спорить с тем, что человек уже вписал. */
.q-field__native::placeholder,
.q-field__input::placeholder,
.q-placeholder::placeholder {
  color: rgba(255,255,255,0.45) !important;
}

/* Выпадающий список Quasar рисует НЕ внутри нашей карточки, а
   отдельным слоем поверх страницы — своей темой. Без этого он
   оставался светлым пятном с белым текстом на белом. */
.q-menu {
  background: #0d1117 !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}
"""


# CHTENIE_KNIGI_V1: общая рука чтения города
try:
    import sys as _sys_ch
    from pathlib import Path as _Path_ch
    _gorod_ch = str(_Path_ch(__file__).resolve().parent.parent / "ГОРОД")
    if _gorod_ch not in _sys_ch.path:
        _sys_ch.path.insert(0, _gorod_ch)
    import chtenie as _chtenie
except Exception as _e_ch:  # пусть кабинет живёт и без неё
    _chtenie = None
    print(f"[ЧТЕНИЕ] рука чтения не подключилась: {_e_ch}")


# AKADEMIA_MODEL_SEL_V1: тот же каталог, что в кабинете Брата (ui_brat.py) —
# один список моделей на весь город, не плодим второй источник правды.
# bibliotekar.py уже принимает model=... в sprosit() — только UI не давал выбрать.
_OPENROUTER_MODEL_ENV = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
MODELS_CATALOG = [
    {"id": "google/gemini-2.5-flash",          "name": "Gemini 2.5 Flash",  "price": "$0.15/$0.60"},
    {"id": "anthropic/claude-haiku-4-5",       "name": "Claude Haiku 4.5",  "price": "$1/$5"},
    {"id": "deepseek/deepseek-chat",           "name": "DeepSeek V3",       "price": "$0.14/$0.28"},
    {"id": "openai/gpt-4o-mini-2024-07-18",              "name": "GPT-4o mini",      "price": "$0,15 / $0,60"},
    {"id": "meta-llama/llama-3.3-70b-instruct","name": "Llama 3.3 70B",     "price": "$0.10/$0.32"},
    {"id": "anthropic/claude-sonnet-4-5",      "name": "Claude Sonnet 4.5", "price": "$3/$15"},
]
DEFAULT_MODEL = _OPENROUTER_MODEL_ENV or MODELS_CATALOG[0]["id"]

# ═══════════════════════════════════════════════════════════
# PATCH_AKADEMIA_VIZUAL_V1 -- визуальный разбор изображения. НЕ
# редактирование -- только анализ: смотрим и описываем, файл не трогаем.
# Самодостаточная функция (свой os.getenv, не зависит от переменных
# другого кабинета) -- Закон Двух Стандартов, копия не ссылка.
# ═══════════════════════════════════════════════════════════
_KARTINKA_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".webp": "image/webp", ".gif": "image/gif"}


async def _analiz_kartinki(path: Path, model: str = "", vopros: str = "") -> str:
    """Мультимодальный вызов той же LLM: картинка вместо/вместе с текстом
    в content сообщения. Честно про ошибки -- не выдумывает разбор,
    если модель не отозвалась или ключа нет."""
    _key = os.getenv("OPENROUTER_API_KEY", "")
    if not _key:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    try:
        data = path.read_bytes()
    except Exception as e:
        return f"⚠ не прочитать файл: {e}"
    mime = _KARTINKA_MIME.get(path.suffix.lower(), "image/png")
    url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    vopros = vopros or "Опиши, что на изображении, коротко и по делу."
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": vopros},
            {"type": "image_url", "image_url": {"url": url}},
        ],
    }]
    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ разбор не удался: {e}"

_HERE = Path(__file__).resolve().parent           # Академия/
_REPO = _HERE.parent                              # корень репо
# PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: ГОРОД в пути — там rezidenty.py
for _p in (_REPO, _REPO / "ГОРОД", _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ── ДАННЫЕ АКАДЕМИИ (не код) ────────────────────────────────
KVARTAL = "Академия"
_DATA      = _REPO / "GRONDHEIM_CITY" / KVARTAL
_UCHENIKI  = _DATA / "ученики.json"
_RUDA      = _DATA / "руда"
_BIBLIO    = _DATA / "библиотека"
_KATALOG   = _BIBLIO / "каталог.json"

_KOVCHEG   = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
_LOKACII   = _REPO / "GRONDHEIM_CITY" / "локации"

ZDANIE = "0008_OWL_CASTLE"      # Замок Сов — дом Академии
MEST   = 10                     # мест за партами, слово Шефа

# полки библиотеки — как в старом городе
POLKI = ["психология", "ремесло", "грондхейм", "рынок", "техника", "прочее"]

# что принимает загрузчик руды
TEKST_EXT = {".txt", ".md", ".rtf"}
KARTINKA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

_STATIC = "akad-static"
_BG_MOUNTED = {"done": False}


# ═══════════════════════════════════════════════════════════
# ДИСК — читаем честно, пустое отдаём пустым
# ═══════════════════════════════════════════════════════════

def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ensure_dirs():
    """Академия заводит свой двор сама — не падаем на пустом городе."""
    for d in (_DATA, _RUDA, _RUDA / "тексты", _RUDA / "изображения", _BIBLIO):
        d.mkdir(parents=True, exist_ok=True)
    for polka in POLKI:
        (_BIBLIO / polka).mkdir(parents=True, exist_ok=True)
    if not _KATALOG.exists():
        _write_json(_KATALOG, {"книги": [], "полки": POLKI})
    if not _UCHENIKI.exists():
        _write_json(_UCHENIKI, {"места": []})


def _dom_zhitelya(imya: str) -> Path:
    return _KOVCHEG / imya


def _avatar_url(dom: Path) -> str:
    """Фото жителя — как в кабинете Биржи и жителя, один способ на город."""
    if not dom or not dom.exists():
        return ""
    p = _read_json(dom / "passport.json", {}) or {}
    av = p.get("avatar", "")
    if av and (dom / av).exists():
        return f"/{_STATIC}/{dom.name}/{av}"
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (dom / ("avatar" + ext)).exists():
            return f"/{_STATIC}/{dom.name}/avatar{ext}"
    return ""


def _bg_url() -> str:
    """Фон кабинета — картинка Замка Сов. Нет image.* — честно пусто."""
    dom = _LOKACII / ZDANIE
    if not dom.exists():
        return ""
    if not _BG_MOUNTED["done"]:
        try:
            app.add_static_files("/akad-bg", str(_LOKACII))
        except Exception:
            pass
        _BG_MOUNTED["done"] = True
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (dom / ("image" + ext)).exists():
            return f"/akad-bg/{ZDANIE}/image{ext}"
    return ""


def _build_mesta() -> list:
    """Десять мест за партами. Кто сидит — из ученики.json, не из кода.

    Формат записи: {"место": 1, "житель": "Илья", "курс": "..."}
    Место без записи — вакансия, это нормальное состояние новой школы.
    """
    zapisi = (_read_json(_UCHENIKI, {}) or {}).get("места", []) or []
    po_mestu = {}
    for z in zapisi:
        try:
            n = int(z.get("место", 0))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= MEST:
            po_mestu[n] = z

    out = []
    for n in range(1, MEST + 1):
        z = po_mestu.get(n)
        imya = (z or {}).get("житель", "")
        dom = _dom_zhitelya(imya) if imya else None
        est = bool(dom and dom.exists())
        if est:
            try:
                app.add_static_files(f"/{_STATIC}/{dom.name}", str(dom))
            except Exception:
                pass
        out.append({
            "место": n,
            "имя": imya if est else "",
            "дом": dom if est else None,
            "курс": (z or {}).get("курс", ""),
            "занято": est,
        })
    return out


def _mesto_row(mesta: list, n: int):
    for m in mesta:
        if m["место"] == n:
            return m
    return None


def _bar_html(charge: float) -> str:
    """Заряд/оптика — тот же вид, что в кабинете жителя и на Бирже."""
    mut = abs(charge)
    half = min(1.0, mut) * 50
    left = 50 if charge >= 0 else 50 - half
    znak = "+" if charge >= 0 else "\u2212"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    if mut < 0.25:
        optika, ocolor = "чисто", "rgba(80,250,123,0.9)"
    elif mut < 0.55:
        optika, ocolor = "ровно", "rgba(201,168,76,0.9)"
    elif mut < 0.8:
        optika, ocolor = "штырит", "rgba(255,160,60,0.9)"
    else:
        optika, ocolor = "колбасит", "rgba(255,80,80,0.9)"
    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar zpok-bar--zaryad"><div class="zpok-mid"></div>'
        f'<div class="zpok-fill" style="left:{left}%; width:{half}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" style="width:{int((1-mut)*100)}%; '
        f'background:{ocolor};"></div></div></div>'
        '</div>'
    )


# ═══════════════════════════════════════════════════════════
# AKADEMIA_CHAT_SAVE_V1 -- сохранить/достать чат, как у Брата
# (Брат/чаты) -- своя полка на каждого СТУДЕНТА (не общий котёл
# кабинета Академии): дом/академия_чаты/, отдельно от личных чатов
# кабинета жителя (дом/чаты/).
# ═══════════════════════════════════════════════════════════

def _save_chat_akademii(dom: Path, chat: list) -> str:
    chats_dir = dom / "академия_чаты"
    chats_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fp = chats_dir / f"чат_{ts}.json"
    fp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp.name


def _list_chaty_akademii(dom: Path) -> list:
    chats_dir = dom / "академия_чаты"
    if not chats_dir.exists():
        return []
    return sorted(chats_dir.glob("чат_*.json"), reverse=True)


def _load_chat_akademii(fp: Path) -> list:
    return json.loads(fp.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
# PATCH_AKADEMIA_STOL_CHTENIE_V1 -- Стол Академии. Руда общая, не
# расходуется -- как Стол Трейдера в Бирже. Реестр "кто что прочитал"
# лежит рядом со столом, не трогая сам стол.
# ═══════════════════════════════════════════════════════════
_PROCHITANO_REESTR = _RUDA / "прочитано.json"
_KARTINKA_MIME_STOL = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                       ".webp": "image/webp", ".gif": "image/gif"}


# AKADEMIA_GLAZA_V_CHATE_V1 + AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1
def _kartinka_na_stole(ruda_sessii=None):
    """Что за картинка лежит на столе СЕЙЧАС: (путь, data-url) или
    (None, ""). Стол — это последняя картинка, которую положили в
    загрузчик за эту сессию.

    Нужно, чтобы про картинку можно было СПРОСИТЬ, а не только «дать
    прочитать». Раньше чат не нёс изображение вовсе, и ученик отвечал
    по имени файла — то есть выдумывал.

    AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1. Сначала здесь бралась самая
    свежая картинка ИЗ ПАПКИ руды — и это было неверно: руда общая и
    не расходуется, файлы лежат в ней всегда. Выходило, что на столе
    вечно что-то есть, даже когда сегодня ничего не клали, и убрать
    это можно было только вытащив файл руками. Стол — то, что
    положили; CLEAR в загрузчике его убирает.

    AKADEMIA_VSE_KARTINKI_STOLA_V1: отдаём ВСЕ картинки со стола, а не
    последнюю. Так сделано в старой студии (_collect_images_for_vision)
    и там работает. Одна картинка = сравнивать не с чем, а сравнение и
    есть учёба: здесь откат кончился, а здесь нет.

    Возвращает список пар (путь, data-url), в порядке укладки.
    """
    import base64 as _b64
    out = []
    for r in (ruda_sessii or []):
        if r.get("вид") != "изображение" or not r.get("путь"):
            continue
        fp = Path(r["путь"])
        if not fp.exists() or fp.suffix.lower() not in _KARTINKA_MIME_STOL:
            continue
        try:
            data = fp.read_bytes()
        except Exception:
            continue
        mime = _KARTINKA_MIME_STOL.get(fp.suffix.lower(), "image/png")
        out.append((fp, f"data:{mime};base64,{_b64.b64encode(data).decode('ascii')}"))
    return out


def _kto_chto_prochital() -> dict:
    return _read_json(_PROCHITANO_REESTR, {}) or {}


def _otmetit_prochitannym(imya: str, fajl: str):
    reg = _kto_chto_prochital()
    reg.setdefault(imya, [])
    if fajl not in reg[imya]:
        reg[imya].append(fajl)
    _write_json(_PROCHITANO_REESTR, reg)


# PROSEV_ZNANII_V1 — второй заход просева: за содержанием
_ZNANIE_MAX_TEM = 3   # больше трёх тем за просев не берём — это деньги


def _uchebnye_temy(momenty: list) -> dict:
    """Разбирает моменты просева на темы учёбы: {имя материала: [моменты]}.

    Учебные записи стол пишет в виде «[Академия] «имя»: выжимка» —
    по этой форме их и узнаём. Всё остальное — личная жизнь, её не
    трогаем, она уходит в первый заход как раньше.
    """
    import re as _re
    temy = {}
    for mm in momenty or []:
        fakt = str(mm.get("факт", ""))
        # PROSEV_ZNANII_DOMA_V1: житель читает и дома, а дом ставит свою
        # метку контекста. Ловим обе формы, иначе просев видит только
        # половину прочитанного — смотря где его запустили.
        if not (fakt.startswith("[Академия]") or fakt.startswith("[Знание:")):
            continue
        m = _re.search(r"«([^»]+)»", fakt)
        tema = (m.group(1) if m else "материал").strip()
        temy.setdefault(tema, []).append(mm)
    return temy


async def _prosev_znanii(dv, dusha: str, momenty: list, model: str = "") -> list:
    """Спрашивает у ученика, что он УЗНАЛ — отдельно от того, что
    почувствовал. Возвращает список (тема, этаж) для показа Шефу.

    Вопрос нарочно противоположен вопросу первого захода: там «не
    пересказывай», здесь — «перескажи точно». Без этого содержание
    из памяти выпадает целиком (проверено на Нине 06.08).
    """
    itogi = []
    for tema, gruppa in list(_uchebnye_temy(momenty).items())[:_ZNANIE_MAX_TEM]:
        spisok = "\n".join(f"— {str(g.get('факт',''))}" for g in gruppa)
        vopros = (
            f"Вот что ты читала по теме «{tema}»:\n{spisok}\n\n"
            f"Что ты УЗНАЛА? Своими словами, но ТОЧНО: определения, порядок "
            f"действий, названия и числа сохрани как есть, ничего не округляй "
            f"и не сглаживай. Это не про чувства — про содержание.\n"
            f"3–6 строк. Чего-то не поняла — так и напиши, это нормальный "
            f"ответ и он полезнее выдуманного."
        )
        try:
            vyvod = await _zvat_llm_akademii(
                [{"role": "system", "content": dusha},
                 {"role": "user", "content": vopros}], model)
        except Exception:
            continue
        if not vyvod or vyvod.startswith("⚠"):
            continue
        try:
            res = dv.dopisat_vyvod(vyvod.strip(),
                                   pattern=f"знание:{tema}", otkuda="учёба")
        except Exception:
            continue
        if res.get("дописано"):
            itogi.append((tema, res.get("этаж", "?")))
    return itogi


async def _zvat_llm_akademii(messages, model: str = "") -> str:
    """Общий вызов LLM -- тот же способ, что и весь кабинет.
    Самодостаточная функция (свой os.getenv) -- Закон Двух Стандартов."""
    _key = os.getenv("OPENROUTER_API_KEY", "")
    if not _key:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    import httpx
    # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
    # из некоторых регионов -- та же настройка, что и в остальном городе.
    _proxy = os.getenv("PROXY_URL", "") or None
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    messages = list(messages)

    # UCHEBNIK_UCHENIKU_V1: руки ученика. Картинки Академии были
    # доступны трейдерам на Бирже и НЕДОСТУПНЫ ученику в самой
    # Академии — там, где по ним и учат. Показывал Ректор, когда сочтёт
    # нужным; сам ученик заглянуть в учебник не мог.
    # Важно для учёбы: в память ложится не картинка, а его СОБСТВЕННЫЙ
    # текст о ней (наблюдение Шефа 05.08). Пока вернуться к рисунку
    # было нельзя, это был приговор: посмотрел раз, пересказал — и
    # живёшь с пересказом.
    ruki_shema, ruki = _ruki_uchenika()
    for _krug in range(5):
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        if ruki_shema and _krug < 4:
            payload["tools"] = ruki_shema
            payload["tool_choice"] = "auto"
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                msg = r.json()["choices"][0]["message"]
        except Exception as e:
            return f"⚠ не отозвался: {e}"

        if not msg.get("tool_calls"):
            return msg.get("content") or ""

        messages.append({"role": "assistant",
                         "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
        for tc in msg["tool_calls"]:
            imya = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except Exception:
                args = {}
            ruka = ruki.get(imya)
            otvet = ruka(args) if ruka else f"такой руки нет: {imya}"
            print(f"[УЧЕНИК] 🖐 {imya}({args})")
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": str(otvet)})
            # метка кадра — досылаем саму КАРТИНКУ, иначе ученик
            # получит путь к файлу вместо рисунка
            if isinstance(otvet, str) and otvet.startswith("[КАДР: "):
                try:
                    import base64 as _b64
                    _p = Path(otvet[7:otvet.index("]")])
                    if _p.exists():
                        _b = _b64.b64encode(_p.read_bytes()).decode("ascii")
                        _mime = ("image/png" if _p.suffix.lower() == ".png"
                                 else "image/jpeg")
                        messages.append({"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:{_mime};base64,{_b}"}},
                            {"type": "text",
                             "text": "Вот рисунок из учебника, который ты "
                                     "попросил(а). Смотри внимательно."}]})
                        print(f"[УЧЕНИК] 🖼 показан {_p.name}")
                except Exception as _e:
                    print(f"[УЧЕНИК] картинка не дошла: {_e}")
    return "⚠ разговор с руками не сошёлся"


def _ruki_uchenika():
    """(схема, руки) — учебник Академии. Не заводим второй: зовём тот
    же Биржа/uchebnik.py, что сканирует дисциплины. Положишь новую
    книгу — увидят и ученик, и трейдер, разом."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo / "Биржа") not in sys.path:
            sys.path.insert(0, str(_repo / "Биржа"))
        import uchebnik as _u
    except Exception as e:
        print(f"[УЧЕНИК] учебник не подключился: {e}")
        return None, {}

    shema = [
        {"type": "function", "function": {
            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ рисунок из учебника, по которому тебя учат. "
                "Скажи тему словами: «приседающий бар», «фрактал», «волны "
                "AO». Ты УВИДИШЬ сам рисунок и авторскую подпись. Проси, "
                "когда хочешь свериться с книгой, а не вспоминать."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string", "description": "тема словами"},
                "дисциплина": {"type": "string",
                               "description": "необязательно: сузить поиск"}},
                "required": ["о_чём"]}}},
        {"type": "function", "function": {
            "name": "chemu_uchili",
            "description": "Какие дисциплины и сколько рисунков есть.",
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},
    ]

    def _pokazat(args):
        o = str(args.get("о_чём", "")).strip()
        tema = str(args.get("дисциплина", "")).strip()
        try:
            nashlos = _u.nayti(o, skolko=1, tema=tema)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            return (f"по «{o}» рисунка не нашёл. Что есть:\n{_u.temy()}")
        p, t, glava, podpis = nashlos[0]
        hvost = f" · {glava}" if glava else ""
        podp = f"\nподпись автора: {podpis}" if podpis else ""
        return f"[КАДР: {p}] учебник · {t}{hvost} · {p.name}{podp}"

    return shema, {"uchebnik": _pokazat,
                   "chemu_uchili": lambda a: "=== ДИСЦИПЛИНЫ ===\n"
                                             + _u.temy()}


def _dvizhok_dlya(dom: Path):
    """Поднимает rezidenty + Dvizhok жителя из кабинета Академии --
    своя точка входа в sys.path, не трогаем общий список модуля
    (Закон Двух Стандартов: свой самодостаточный ход)."""
    _repo2 = Path(__file__).resolve().parent.parent
    for _pp in (_repo2, _repo2 / "ГОРОД", _repo2 / "жители"):
        if str(_pp) not in sys.path:
            sys.path.insert(0, str(_pp))
    import rezidenty
    from dvizhok import Dvizhok
    return rezidenty, Dvizhok


# ═══════════════════════════════════════════════════════════
# PATCH_AKADEMIA_UROKI_PANEL_V1 -- список дисциплин/уроков, живой
# скан диска. Ни одной дисциплины -- честный пустой список, не падаем.
# ═══════════════════════════════════════════════════════════
_DISTSIPLINY_DIR = _DATA / "дисциплины"


def _vse_distsipliny() -> list:
    """Все дисциплины по всем направлениям -- плоский список для UI.
    Дисциплин нет -- пустой список, честно."""
    out = []
    if not _DISTSIPLINY_DIR.exists():
        return out
    for napr_dir in sorted(_DISTSIPLINY_DIR.iterdir()):
        if not napr_dir.is_dir():
            continue
        for d in sorted(napr_dir.iterdir()):
            if not d.is_dir():
                continue
            man = _read_json(d / "manifest.json")
            if man:
                man["_путь"] = str(d)
                man.setdefault("направление", napr_dir.name)
                out.append(man)
    return out


def _urok_soderzhimoe(distsiplina_put: str, urok_rel: str) -> str:
    fp = Path(distsiplina_put) / urok_rel
    try:
        return fp.read_text(encoding="utf-8")
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
# СТИЛЬ — снят с Биржи один в один
# ═══════════════════════════════════════════════════════════

AKAD_CSS = r"""
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
  width:100vw; height:100vh; overflow:hidden !important;
  background: transparent !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
}

#bg{ position: fixed; inset: 0; z-index: -1; background-size: cover;
     background-position: center; background-color: #050510; }
#bg::after{ content:''; position:absolute; inset:0; background: rgba(5,5,16,0.88); }

.app-container{
  position: fixed; inset: 0; display: grid;
  width: 100vw; height: 100vh;
  grid-template-columns: 300px 1fr 260px;
  grid-template-rows: 80px 1fr;
  grid-template-areas:
    "header header header"
    "left   stage  right";
  gap: 20px; padding: 20px; box-sizing: border-box;
}

.area-header{ grid-area: header; }
.area-left{ grid-area: left; min-height:0; }
.area-stage{ grid-area: stage; min-height:0; position: relative; overflow: hidden; }
.area-right{ grid-area: right; min-height:0; }

.glass{
  background: var(--glass); border: 1px solid var(--stroke);
  border-radius: 20px; backdrop-filter: blur(16px);
  box-shadow: 0 20px 60px rgba(0,0,0,0.45); min-height: 0;
}

.squad-deck{
  height: 100%; display: flex; justify-content: center; align-items: center;
  padding: 10px 16px; gap: 15px; overflow-x: auto;
}

.avatar{
  width: 44px; height: 44px; border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.14);
  background-size: cover; background-position: center 18%;
  background-color: rgba(255,255,255,0.05);
  flex: 0 0 auto; display: grid; place-items: center;
  color: rgba(255,255,255,0.92); font-weight: 800; font-size: 11px;
  cursor: pointer; transition: all 0.3s ease; position: relative;
}
.avatar:hover{ border-color: rgba(0,204,255,0.40); transform: scale(1.05); }
.avatar.active{
  border-color: rgba(0,204,255,0.75);
  box-shadow: 0 0 0 2px rgba(0,204,255,0.25) inset, 0 0 30px rgba(0,204,255,0.35);
}
.avatar.vacant{ border-style: dashed; opacity: 0.4; cursor: default; }

.left-col{ height: 100%; display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.asset-bay{ height: auto; max-height: 360px; flex-shrink: 0; overflow: visible; }

.panel-title{
  padding: 12px 16px; color: rgba(255,255,255,0.92); font-weight: 900;
  letter-spacing: .12em; text-transform: uppercase; font-size: 11px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.file-list{ padding: 8px 12px; max-height: 300px; overflow-y: auto;
            font-family: monospace; font-size: 11px; }

.right-col{ height: 100%; display: flex; flex-direction: column;
            justify-content: flex-start; gap: 12px; }
.right-top-slot{
  flex-shrink: 0; height: 240px; border-radius: 20px;
  border: 1px dashed rgba(255,255,255,0.14); background: rgba(255,255,255,0.04);
  display: grid; place-items: center; color: rgba(255,255,255,0.55);
  font-size: 11px; padding: 12px; text-align: center; overflow: hidden;
}

.stage-monitor{ height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.stage-toolbar{
  height: 60px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 12px; border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0; background: rgba(13, 17, 23, 0.95);
  backdrop-filter: blur(16px); z-index: 10;
}
.stage-content{ flex: 1; min-height: 0; overflow: hidden; padding: 18px; padding-bottom: 130px; }

.split-view{ height: 100%; display: flex; gap: 18px; min-height: 0; overflow: hidden; }
.chat-log, .viewer{
  flex: 1; min-height: 0; min-width: 0; border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03);
  overflow-y: auto; overflow-x: hidden; padding: 14px;
  font-family: monospace; font-size: 13px; color: rgba(255,255,255,0.86);
  white-space: pre-wrap; word-wrap: break-word; word-break: break-word;
}
.viewer{ border-color: rgba(0,204,255,0.30); }

.floating-console{
  position: absolute; left: 50%; bottom: 20px; transform: translateX(-50%);
  width: min(820px, calc(100% - 80px)); z-index: 50;
  display: flex; align-items: center; gap: 8px; padding: 10px 12px;
  border-radius: 50px; background: rgba(13, 17, 23, 0.85);
  border: 1px solid rgba(255,255,255,0.15); backdrop-filter: blur(20px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}
.floating-console input{
  width: 100%; border-radius: 40px; border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06); padding: 12px 16px;
  color: rgba(255,255,255,0.92); outline: none; font-family: monospace;
}
.send-button{
  border-radius: 40px !important; border: 2px solid rgba(0,204,255,0.55) !important;
  background: linear-gradient(135deg, rgba(0,204,255,0.30), rgba(189,0,255,0.25)) !important;
  color: rgba(255,255,255,0.98) !important; font-weight: 900 !important;
  padding: 12px 24px !important; cursor: pointer !important;
}

.chat-msg-user{ background: rgba(0, 204, 255, 0.1);
  border-left: 3px solid rgba(0, 204, 255, 0.6); padding: 8px 12px;
  margin: 8px 0; border-radius: 0 8px 8px 0; }
.chat-msg-assistant{ background: rgba(0, 255, 136, 0.08);
  border-left: 3px solid rgba(0, 255, 136, 0.6); padding: 8px 12px;
  margin: 8px 0; border-radius: 0 8px 8px 0; }
.chat-msg-system{ color: rgba(255,255,255,0.5); font-style: italic; padding: 4px 0; }

.zpok{ padding:10px 16px; display:flex; flex-direction:column; gap:9px; }
.zpok-row{ display:flex; flex-direction:column; gap:3px; }
.zpok-lab{ display:flex; justify-content:space-between; font-size:0.56rem;
  text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.5); }
.zpok-lab b{ color:rgba(255,255,255,0.85); font-weight:700; }
.zpok-bar{ height:6px; border-radius:4px; background:rgba(255,255,255,0.08);
  overflow:hidden; position:relative; }
.zpok-bar--zaryad .zpok-fill{ position:absolute; top:0; bottom:0; }
.zpok-mid{ position:absolute; left:50%; top:-2px; bottom:-2px; width:1px;
  background:rgba(255,255,255,0.4); z-index:2; }
.zpok-fill{ height:100%; border-radius:4px; }

.akad-btn{
  padding:6px 14px; border-radius:7px; font-size:12px; font-weight:700;
  cursor:pointer; display:flex; align-items:center;
  background:rgba(255,255,255,0.03); color:rgba(255,255,255,0.55);
  border:1px solid rgba(255,255,255,0.10);
}

/* AKADEMIA_MODEL_SEL_V1 — калька .brat-model-sel из ui_brat.py */
.amodel-sel .q-field__control{ background:rgba(255,255,255,0.06)!important;
  border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; }

.nicegui-content { overflow: hidden !important; height: 100% !important; }
.area-stage { overflow: hidden !important; }
.area-stage > * { overflow: hidden !important; min-height: 0 !important; max-height: 100% !important; }
.stage-monitor { overflow: hidden !important; height: 100% !important; }
.stage-monitor > * { min-height: 0 !important; }
.stage-toolbar { flex-shrink: 0 !important; overflow: hidden !important; }
.stage-content { flex: 1 1 0 !important; min-height: 0 !important; overflow: hidden !important;
                 max-height: calc(100% - 60px) !important; }
.stage-content > * { min-height: 0 !important; max-height: 100% !important; overflow: hidden !important; }
.split-view { height: 100% !important; min-height: 0 !important; overflow: hidden !important; }
.split-view > * { min-height: 0 !important; overflow: hidden !important; }
.chat-log, .viewer { flex: 1 1 0 !important; min-height: 0 !important; max-height: 100% !important;
                     overflow-y: auto !important; overflow-x: hidden !important; }
"""


# ═══════════════════════════════════════════════════════════
# СТРАНИЦА
# ═══════════════════════════════════════════════════════════

def page_akademia() -> None:
    """Кабинет Академии — Замок Сов изнутри."""

    _ensure_dirs()
    mesta = _build_mesta()

    # первое занятое место — активное; нет никого — первое место
    _first = next((m["место"] for m in mesta if m["занято"]), 1)

    state = {
        "активное_место": _first,
        "чат": [],
        "руда": [],          # что принял загрузчик за эту сессию
        "отчёт": "",
        "model": DEFAULT_MODEL,
    }

    def on_model_change(e):
        state["model"] = e.value

    chat_ref   = {"element": None}
    viewer_ref = {"element": None}
    ruda_ref   = {"element": None, "uploader": None}
    uroki_ref  = {"element": None}  # PATCH_AKADEMIA_UROKI_PANEL_V1
    knigi_ref  = {"uploader": None, "полка": None}
    avatar_ref = {"element": None}
    vitals_ref = {"element": None}
    biblio_ref = {"element": None}
    input_ref  = {"element": None}
    bubbles    = {"elements": {}}

    ui.add_head_html(f"<style>{AKAD_CSS}</style>")
    ui.add_head_html("<style>" + _BELYY_SHRIFT + "</style>")   # BELYY_SHRIFT_V1
    _bg = _bg_url()
    ui.html(f'<div id="bg"{f" style=\"background-image:url(\'{_bg}\');\"" if _bg else ""}></div>')

    # ── чат ────────────────────────────────────────────────
    def update_chat():
        if not chat_ref["element"]:
            return
        chat_ref["element"].clear()
        with chat_ref["element"]:
            if not state["чат"]:
                ui.html('<div class="chat-msg-system">SYSTEM: Замок Сов открыт. '
                        'Всегда тих. Ждёт тех, кто задаёт вопросы.</div>')
                return
            for m in state["чат"]:
                if m.get("role") == "user":
                    ui.html(f'<div class="chat-msg-user"><b>ШЕФ:</b> {m.get("content","")}</div>')
                else:
                    who = m.get("кто", "СИСТЕМА")
                    ui.html(f'<div class="chat-msg-assistant"><b>{who}:</b> {m.get("content","")}</div>')

    def update_viewer(md: str):
        if not viewer_ref["element"]:
            return
        state["отчёт"] = md
        viewer_ref["element"].clear()
        with viewer_ref["element"]:
            ui.markdown(md)

    # ── аватар студента (правая колонка) ───────────────────
    def update_avatar():
        if not avatar_ref["element"]:
            return
        m = _mesto_row(mesta, state["активное_место"])
        avatar_ref["element"].clear()
        with avatar_ref["element"]:
            # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: аватар — ЧИСТОЕ ЛИЦО.
            # Ни имени, ни места, ни курса поверх фото (так в кабинете
            # Брата: "аватар — чистое лицо, без подписи"). Всё словами
            # уехало в панель ПОД аватаром — update_vitals().
            av = _avatar_url(m["дом"]) if (m and m["занято"]) else ""
            if av:
                ui.html(f'<img src="{av}" style="width:100%;height:100%;'
                        f'object-fit:cover;border-radius:19px;opacity:0.9;" '
                        f'onerror="this.style.display=\'none\'">')
            else:
                ui.html('<div style="font-size:3rem; color:rgba(0,255,136,0.35);">⬡</div>')

    def update_vitals():
        if not vitals_ref["element"]:
            return
        vitals_ref["element"].clear()
        m = _mesto_row(mesta, state["активное_место"])
        with vitals_ref["element"]:
            # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: подпись студента живёт
            # ЗДЕСЬ, под аватаром — не поверх лица.
            if m and m["занято"]:
                p = _read_json(m["дом"] / "passport.json", {}) or {}
                kurs = (m.get("курс", "") or "курс не назначен")
                ui.html(
                    f'<div style="padding:12px 16px 4px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">'
                    f'студент · место {m["место"]}</div>'
                    f'<div style="font-size:1.15rem;font-weight:800;color:#00ff88;'
                    f'line-height:1.3;">{m["имя"]}</div>'
                    f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.6);">'
                    f'{kurs}</div></div>')
                ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))
            else:
                ui.html(
                    f'<div style="padding:12px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">'
                    f'место {m["место"] if m else "—"}</div>'
                    f'<div style="font-size:0.8rem;color:rgba(255,80,80,0.55);'
                    f'margin-top:2px;">свободно</div></div>')

    def update_bubbles():
        for n, el in bubbles["elements"].items():
            m = _mesto_row(mesta, n)
            base = "avatar" if (m and m["занято"]) else "avatar vacant"
            el.classes(replace=base)
            if n == state["активное_место"]:
                el.classes(add="active")

    def switch_mesto(n: int):
        m = _mesto_row(mesta, n)
        state["активное_место"] = n
        update_avatar()
        update_vitals()
        update_bubbles()
        if m and m["занято"]:
            p = _read_json(m["дом"] / "passport.json", {}) or {}
            dna = p.get("DNA_Static", {}) or {}
            ruchki = " · ".join(f"{k}: {v}" for k, v in dna.items()) or "—"
            update_viewer(
                f"# {m['имя']} · место {n}\n\n"
                f"**Курс:** {m['курс'] or '*не назначен*'}\n\n"
                f"**Натура:** {ruchki}\n\n"
                f"**Род:** {p.get('Hidden_History','—')}\n\n"
                f"---\n\n*Учёба ещё не подключена — это первый слой, экран.*"
            )
        else:
            ui.notify(f"Место {n} свободно — сюда ещё никого не записали", type="warning")
            update_viewer(f"# Место {n}\n\n*Свободно. Запись студента — отдельная дверь, "
                          f"её ещё нет.*")

    # ── ЗАГРУЗЧИК РУДЫ (левая колонка): текст + изображения ─
    def update_ruda_list():
        if not ruda_ref["element"]:
            return
        ruda_ref["element"].clear()
        with ruda_ref["element"]:
            if not state["руда"]:
                ui.label("Руда пуста").style("color: rgba(255,255,255,0.4); font-size:11px;")
                return
            for r in state["руда"]:
                ikona = "🖼" if r["вид"] == "изображение" else "📄"
                cvet = "rgba(189,0,255,0.9)" if r["вид"] == "изображение" else "rgba(0,204,255,0.9)"
                ui.html(f'''
                  <div style="padding:7px 10px;margin:3px 0;border-radius:7px;
                              background:rgba(255,255,255,0.02);
                              border:1px solid rgba(255,255,255,0.07);
                              font-family:'JetBrains Mono',monospace;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                      <span style="color:{cvet};font-size:11px;font-weight:700;">{ikona} {r["вид"]}</span>
                      <span style="color:rgba(255,255,255,0.4);font-size:9px;">{r["размер"]}</span>
                    </div>
                    <div style="color:rgba(255,255,255,0.6);font-size:9px;margin-top:2px;
                                word-break:break-all;">{r["имя"]}</div>
                  </div>''')

    async def handle_ruda(e):
        """Приёмка руды. Текст — на просев. Изображение — на разбор.

        РАЗБОР НЕ ВШИТ (первый слой): файл честно ложится на диск и
        показывается в списке. Чтобы читать график глазами, нужен голос,
        который видит картинки — это отдельный слой и отдельное решение
        Шефа. Пустого «проанализировано» здесь не будет.
        """
        imya = e.name
        ext = Path(imya).suffix.lower()
        if ext in TEKST_EXT:
            vid, papka = "текст", _RUDA / "тексты"
        elif ext in KARTINKA_EXT:
            vid, papka = "изображение", _RUDA / "изображения"
        else:
            ui.notify(f"{imya}: не текст и не изображение — не приму", type="warning")
            return
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать файл: {ce}", type="negative")
            return
        papka.mkdir(parents=True, exist_ok=True)
        dest = papka / imya
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не сохранить: {we}", type="negative")
            return

        kb = len(data) / 1024
        state["руда"].append({
            "имя": imya, "вид": vid, "путь": str(dest),
            "размер": f"{kb:.0f} КБ",
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        update_ruda_list()

        if vid == "текст":
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"📄 Принял «{imya}» — лёг в руду на просев."})
            ui.notify(f"📄 Принято на просев: {imya}", type="positive")
        else:
            # PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1: разбор при загрузке убран
            # -- жил один ход чата и дублировал то, что уже делает и
            # СОХРАНЯЕТ "📖 Прочитать" (личная память активного студента).
            # Стол только принимает, как и для текста.
            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",
                                 "content": f"🖼 Принял «{imya}» — лежит на столе, "
                                           f"разберёт тот, кто сядет читать."})
            ui.notify(f"🖼 Принято: {imya}", type="info")
        update_chat()

        up = ruda_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass

    def clear_ruda():
        state["руда"] = []
        update_ruda_list()
        ui.notify("Список очищен (файлы на диске остались)", type="info")

    # ── PATCH_AKADEMIA_UROKI_PANEL_V1 ────────────────────────
    state["текущий_урок"] = {"текст": "", "название": ""}

    def pokazat_urok(dist: dict, urok_rel: str, label: str):
        text = _urok_soderzhimoe(dist["_путь"], urok_rel)
        if not text.strip():
            ui.notify(f"«{label}» пуст или не читается", type="warning")
            return
        title = f'{dist.get("название", dist.get("id",""))} — {label}'
        state["текущий_урок"] = {"текст": text, "название": title}
        update_viewer(f"# {dist.get('название', dist.get('id',''))}\n\n"
                     f"## {label}\n\n{text}")

    def update_uroki_panel():
        if not uroki_ref["element"]:
            return
        uroki_ref["element"].clear()
        with uroki_ref["element"]:
            distsipliny = _vse_distsipliny()
            if not distsipliny:
                ui.html('<div style="color:rgba(255,255,255,0.35);font-size:10px;'
                        'padding:8px 12px;">Дисциплин пока нет</div>')
                return
            for dist in distsipliny:
                nazv = dist.get("название", dist.get("id", "?"))
                napr = dist.get("направление", "")
                ui.html(f'<div style="padding:6px 10px 2px 10px;font-size:10px;'
                        f'font-weight:800;color:rgba(0,204,255,0.85);'
                        f'text-transform:uppercase;letter-spacing:.06em;">'
                        f'{nazv} <span style="color:rgba(255,255,255,0.35);'
                        f'font-weight:400;">· {napr}</span></div>')
                uroki = dist.get("уроки", []) or []
                if not uroki:
                    ui.html('<div style="color:rgba(255,255,255,0.3);font-size:9px;'
                            'padding:2px 14px 6px 14px;">— уроков нет —</div>')
                    continue
                for urok_rel in uroki:
                    label = Path(urok_rel).stem
                    def _click(d=dist, u=urok_rel, lbl=label):
                        pokazat_urok(d, u, lbl)
                    ui.button(label, on_click=_click).props("flat no-caps dense").style(
                        "width:calc(100% - 8px); margin:1px 4px; text-align:left; "
                        "font-size:10px; color:rgba(255,255,255,0.7); "
                        "padding:4px 10px; border-radius:6px; "
                        "background:rgba(255,255,255,0.02);")

    async def do_chtenie_uroka():
        """Активный студент читает ПОКАЗАННЫЙ урок своей натурой.
        Впечатление сохраняется в его личную память (dvizhok,
        kontekst="учёба") -- через уже существующие _dvizhok_dlya()/
        _zvat_llm_akademii() (patch_akademia_stol_chtenie.py)."""
        urok = state.get("текущий_урок") or {}
        text = (urok.get("текст") or "").strip()
        if not text:
            ui.notify("Сначала выбери урок слева", type="warning")
            return
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — читать некому", type="warning")
            return
        imya, dom = m["имя"], m["дом"]
        try:
            rezidenty, Dvizhok = _dvizhok_dlya(dom)
            dv = Dvizhok(dom)
        except Exception as e:
            ui.notify(f"⚠ движок не дышит: {e}", type="negative")
            return
        p = _read_json(dom / "passport.json", {}) or {}
        try:
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица.\n"

        state["чат"].append({"role": "assistant", "кто": "УРОК",
                             "content": f"📖 {imya} читает «{urok['название']}»…"})
        update_chat()

        vopros = (f"Ты сейчас в Академии, изучаешь урок.\n\n"
                 f"{text}\n\n"
                 f"Прочитай своей натурой, вынеси концентрат — 5-8 строк, "
                 f"суть плюс твой личный отклик через свою натуру.")
        messages = [{"role": "system", "content": dusha},
                   {"role": "user", "content": vopros}]
        vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
        if not vyzhimka or vyzhimka.startswith("⚠"):
            ui.notify(f"⚠ {(vyzhimka or 'пустой ответ')[:90]}", type="negative")
            return

        try:
            vdoh_res = dv.vdoh(kontekst="учёба", sila=0.8, svezhest=1.0, tonus="плюс")
            dv.vydoh_stol(fakt=f"[Академия] «{urok['название']}»: {vyzhimka.strip()}",
                          vdoh_result=vdoh_res)
            dv.sохранить()
        except Exception:
            pass

        state["чат"].append({"role": "assistant", "кто": imya,
                             "content": f"📖 «{urok['название']}» — {vyzhimka.strip()}"})
        ui.notify(f"✦ {imya} прочитал(а): {urok['название']}", type="positive")
        update_chat()

    # ── ЗАГРУЗЧИК БИБЛИОТЕКИ (правая колонка, под аватаром) ─
    def update_biblio_info():
        if not biblio_ref["element"]:
            return
        kat = _read_json(_KATALOG, {"книги": []}) or {"книги": []}
        knigi = kat.get("книги", [])
        po_polkam = {}
        for k in knigi:
            po_polkam[k.get("полка", "прочее")] = po_polkam.get(k.get("полка", "прочее"), 0) + 1
        biblio_ref["element"].clear()
        with biblio_ref["element"]:
            if not knigi:
                ui.html('<div style="color:rgba(255,255,255,0.35);font-size:10px;'
                        'padding:8px 16px;">Полки пусты — ни одной книги</div>')
                return
            stroki = " · ".join(f"{p}: {n}" for p, n in po_polkam.items())
            ui.html(f'<div style="color:rgba(255,255,255,0.5);font-size:9px;'
                    f'padding:8px 16px;line-height:1.6;font-family:\'JetBrains Mono\',monospace;">'
                    f'книг всего: <b style="color:rgba(0,204,255,0.9);">{len(knigi)}</b><br>{stroki}</div>')

    async def handle_kniga(e):
        """Книга на полку + запись в каталог. Обложку (о чём, глубина)
        Шеф правит в каталоге руками — код за него не сочиняет."""
        imya = e.name
        polka = (knigi_ref["полка"].value if knigi_ref["полка"] else "прочее") or "прочее"
        try:
            data = e.content.read() if hasattr(e.content, "read") else e.content
        except Exception as ce:
            ui.notify(f"Не прочитать книгу: {ce}", type="negative")
            return
        dest_dir = _BIBLIO / polka
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / imya
        try:
            dest.write_bytes(data)
        except Exception as we:
            ui.notify(f"Не положить на полку: {we}", type="negative")
            return

        kat = _read_json(_KATALOG, {"книги": [], "полки": POLKI}) or {"книги": [], "полки": POLKI}
        knigi = kat.setdefault("книги", [])
        rel = f"{polka}/{imya}"
        book_id = Path(imya).stem.lower().replace(" ", "_")[:40]
        zapis = {
            "id": book_id,
            "название": Path(imya).stem,
            "полка": polka,
            "файл": rel,
            "глубина": "basic",      # обложку уточняет Шеф руками
            "теги": [],
            "когда": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        est = next((i for i, b in enumerate(knigi) if b.get("файл") == rel), None)
        if est is not None:
            knigi[est] = zapis
        else:
            knigi.append(zapis)
        kat["полки"] = POLKI
        _write_json(_KATALOG, kat)

        update_biblio_info()
        state["чат"].append({
            "role": "assistant", "кто": "БИБЛИОТЕКА",
            "content": (f"📚 «{zapis['название']}» встала на полку «{polka}». "
                        f"Глубина пока basic — поправь в каталоге, если книга тяжёлая.")})
        update_chat()
        ui.notify(f"📚 На полку «{polka}»: {zapis['название']}", type="positive")
        up = knigi_ref.get("uploader")
        if up:
            try:
                up.reset()
            except Exception:
                pass

    # ── навигация ──────────────────────────────────────────
    def idti_v_biblioteku():
        ui.notify("Отдельная Библиотека ещё не построена — заглушка", type="info")

    def idti_domoy():
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — некого вести домой", type="warning")
            return
        p = _read_json(m["дом"] / "passport.json", {}) or {}
        zid = p.get("ID_Object", "")
        ui.navigate.to(f"/zhitel/{zid}" if zid else "/zhitel")

    def idti_v_gorod():
        ui.navigate.to("/grondheim")

    # ── чат с учеником: активируется по клику на пузырёк ───
    # PATCH_AKADEMIA_UCHENIK_CHAT_V1: раньше чат ВСЕГДА говорил
    # библиотекарем, кто бы ни был выбран пузырьком — место просто
    # красилось активным, но с ним никто не разговаривал. Теперь
    # активное место и есть собеседник: клик по пузырьку меняет
    # switch_mesto() -> state["активное_место"], и чат обращается
    # именно к этому жителю (его личность — rezidenty.sobrat_dushu,
    # та же развязка личность/роль, что у библиотекаря). Маяк
    # подключён тем же способом: если горит — собеседник получает
    # свежий кусок из внешнего мира.

    async def _mayak_kusok(zapros: str, kto: str = "академия-ученик") -> str:
        """PATCH_AKADEMIA_MAYAK_VOLYA_V1: сходить на Маяк по КОНКРЕТНОМУ
        запросу (MAYAK_REQUEST извлечён из ответа ученика — воля, не
        автомат на каждую реплику; тот же закон, что у обычного жителя
        в ui_zhitel.py). `kto` — настоящее имя ученика для учёта
        Хранителя Маяка, не жёсткая строка. Пустая строка — Маяк не
        нужен или не отозвался, вызывающий просто ничего не добавит."""
        try:
            import mayak
        except ImportError:
            return ""
        try:
            if not mayak.gorit():
                return ""
            rez = await mayak.poisk(zapros, 4)
            try:
                mayak.zapisat_vizit(kto, zapros, rez.get("ok", False))
            except Exception:
                pass
            return mayak.dlya_promta(rez, 4)
        except Exception:
            return ""

    def _izvlech_mayak_request(text: str) -> str:
        """PATCH_AKADEMIA_MAYAK_VOLYA_V1: та же функция, что в
        ui_zhitel.py — не дублируем логику, дублируем только код
        (файлы самодостаточны, Закон Двух Стандартов)."""
        for line in (text or "").splitlines():
            if "MAYAK_REQUEST:" in line:
                return line.split("MAYAK_REQUEST:", 1)[1].strip()
        return ""

    def _ubrat_mayak_request(text: str) -> str:
        lines = [l for l in (text or "").splitlines() if "MAYAK_REQUEST:" not in l]
        return "\n".join(lines).strip()

    async def _sprosit_uchenika(dom, vopros: str, istoria: list, model: str) -> str:
        p = _read_json(dom / "passport.json", {}) or {}
        if not p:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка — иначе
            # вызывающий падает на распаковке и прячет эту причину.
            return "⚠ паспорт не читается — не могу собрать личность.", ""
        try:
            import rezidenty
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {p.get('Official_Name','житель')}, житель Грондхейма.\n"

        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: движок сигналит доступность
        # просева — тот же порог (≥3), что у кнопки «Осмыслить» и у
        # обычного жителя. Ученик сам решает, писать ли PROSEV_REQUEST.
        _prosev_dv = None
        _prosev_dostupno = False
        try:
            _rz, _Dv = _dvizhok_dlya(dom)
            _prosev_dv = _Dv(dom)
            _prosev_dostupno = len(_prosev_dv.sobrat_dlya_proseva(limit=8)) >= 3
        except Exception:
            _prosev_dv = None
            _prosev_dostupno = False

        # PAMYAT_V_PROMT_VEZDE_V1: ученик приходит на урок со ВСЕМ, что
        # уже нажил. Без этого он адекватен, только пока материал лежит
        # на столе прямо в этой сессии, а вышел — не знает ничего.
        try:
            if _prosev_dv is not None:
                dusha += _prosev_dv.pamyat_v_promt()
        except Exception:
            pass

        rol = ("\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\n"
               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "
               "голосом и характером, не как ассистент.\n")
        # PATCH_AKADEMIA_MAYAK_VOLYA_V1: тот же закон, что у обычного
        # жителя — Маяк не звонит на каждую реплику, ученик сам решает.
        # Работает и когда Шеф прямо просит что-то найти: он это просто
        # увидит в разговоре и сам напишет маркер, воля не отменяется,
        # только не автоматична.
        rol += (
            "\nЕсли для ответа не хватает свежих фактов из внешнего мира "
            "(то, чего ты сам знать не можешь — новости, текущие события, "
            "актуальные данные, или Шеф прямо попросил что-то найти) — "
            "напиши отдельной строкой MAYAK_REQUEST: <что узнать> и Маяк "
            "Пробуждения принесёт ответ."
        )
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: строка появляется, только если
        # движок реально насчитал накопленное — сигнал от движка,
        # согласие остаётся за учеником.
        if _prosev_dostupno:
            rol += (
                "\nЕсли чувствуешь, что многое накопилось (уроки, разговоры) "
                "и хочется остановиться, оглянуться и понять, чем ты стал(а) "
                "немного другим(ой) — можешь написать отдельной строкой "
                "PROSEV_REQUEST, и получится осмыслить это."
            )

        promt = dusha + rol
        _key = os.getenv("OPENROUTER_API_KEY", "")
        if not _key:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка.
            return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env.", ""

        messages = [{"role": "system", "content": promt}]
        for m in (istoria or [])[-10:]:
            r = "user" if m.get("role") == "user" else "assistant"
            messages.append({"role": r, "content": m.get("content", "")})
        # AKADEMIA_GLAZA_V_CHATE_V1: к вопросу прикрепляем то, что лежит
        # на столе. Раньше чат нёс один текст, и на вопрос «что на
        # картинке?» ученик отвечал по имени файла из переписки — то
        # есть сочинял. Картинки нет — всё как раньше.
        # AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1: стол — список загрузчика этой
        # сессии, а не всё, что накопилось в папке руды.
        # AKADEMIA_VSE_KARTINKI_STOLA_V1: кладём ВСЕ, чтобы можно было
        # сравнивать страницы между собой.
        _stol = _kartinka_na_stole(state.get("руда"))
        _url_stol = _stol[0][1] if _stol else ""
        if _stol:
            _skolko = ("На столе перед тобой лежит изображение."
                       if len(_stol) == 1 else
                       f"На столе перед тобой {len(_stol)} изображени"
                       f"{'я' if len(_stol) < 5 else 'й'}, по порядку.")
            _content = [{"type": "text", "text": (
                f"({_skolko} Если речь о них — смотри на сами изображения, "
                f"а не на названия. Не разглядела — так и скажи.)\n\n" + vopros)}]
            for _fp_i, _url_i in _stol:
                _content.append({"type": "image_url",
                                 "image_url": {"url": _url_i}})
            messages.append({"role": "user", "content": _content})
        else:
            messages.append({"role": "user", "content": vopros})

        import httpx
        # PATCH_PROXY_VEZDE_V1: без прокси OpenRouter честно отвечает 403
        # из некоторых регионов -- та же настройка, что и в остальном городе.
        _proxy = os.getenv("PROXY_URL", "") or None
        headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
        payload = {"model": model or DEFAULT_MODEL, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload)
                r.raise_for_status()
                reply = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # AKADEMIA_CHESTNAYA_OSHIBKA_V1: пара, а не строка. И текст
            # ошибки укорачиваем — иначе JSON-простыня распирает чат.
            _tekst = str(e)
            _telo = getattr(getattr(e, "response", None), "text", "")
            if _telo:
                _tekst = f"{_tekst} | ответ сервера: {_telo}"
            return f"⚠ не отозвался(лась): {_tekst[:400]}", ""

        # PATCH_AKADEMIA_MAYAK_VOLYA_V1: MAYAK_REQUEST извлекаем ПОСЛЕ
        # первого ответа — только теперь, если сам написал маркер, идём
        # на Маяк с ЧИСТЫМ запросом (не сырым текстом реплики Шефа) и
        # с НАСТОЯЩИМ именем ученика для учёта Хранителя Маяка.
        _mayak_q = _izvlech_mayak_request(reply)
        if _mayak_q:
            _kto = p.get("Official_Name", "академия-ученик")
            snaruzhi = await _mayak_kusok(_mayak_q, _kto)
            if snaruzhi:
                _vtoroy = list(messages)
                _vtoroy.append({"role": "assistant", "content": reply})
                _vtoroy.append({"role": "user", "content": (
                    f"(С Маяка Пробуждения принесли по запросу «{_mayak_q}»:\n"
                    f"{snaruzhi}\n"
                    f"Пропусти через себя и ответь заново своими словами, "
                    f"живым голосом — не пересказывай источники. Маяк не "
                    f"упоминай.)")})
                try:
                    async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                        r = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json={"model": model or DEFAULT_MODEL, "messages": _vtoroy})
                        r.raise_for_status()
                        reply = r.json()["choices"][0]["message"]["content"]
                except Exception:
                    pass  # остаётся первый ответ — не роняем разговор
            reply = _ubrat_mayak_request(reply) or reply

        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: та же труба, что кнопка
        # «Осмыслить» (do_prosev_akademii) — только вызвана волей
        # ученика, не рукой Шефа. Тихо, если не сложилось: воля не
        # всегда сбывается, это не ошибка разговора.
        _prosev_note = ""
        if _prosev_dostupno and _prosev_dv is not None:
            _prosev_q = False
            for _line in (reply or "").splitlines():
                if _line.strip().upper().startswith("PROSEV_REQUEST"):
                    _prosev_q = True
                    break
            if _prosev_q:
                reply = "\n".join(
                    l for l in (reply or "").splitlines()
                    if not l.strip().upper().startswith("PROSEV_REQUEST")
                ).strip() or reply
                try:
                    _momenty_p = _prosev_dv.sobrat_dlya_proseva(limit=8)
                    if len(_momenty_p) >= 3:
                        _spisok_p = "\n".join(
                            f"— [{mm['тонус']}] {mm['факт']}" for mm in _momenty_p)
                        _vopros_p = (
                            f"Вот моменты из твоей жизни, которые тебя тронули:\n"
                            f"{_spisok_p}\n\nЧто это говорит о тебе? Ответь от "
                            f"первого лица, 1–3 фразы, не пересказ моментов.")
                        _msg_p = [{"role": "system", "content": dusha},
                                 {"role": "user", "content": _vopros_p}]
                        _vyvod_p = await _zvat_llm_akademii(_msg_p, model)
                        if _vyvod_p and not _vyvod_p.startswith("⚠"):
                            _vyvod_p = _vyvod_p.strip()
                            _res_p = _prosev_dv.dopisat_vyvod(
                                _vyvod_p, pattern=None, otkuda="жизнь")
                            # PROSEV_ZNANII_V1: второй заход — за
                            # содержанием, отдельной строкой от чувств.
                            try:
                                _zn = await _prosev_znanii(
                                    _prosev_dv, dusha, _momenty_p, model)
                                if _zn:
                                    _prosev_note = (
                                        (_prosev_note + "  ") if _prosev_note else ""
                                    ) + "📚 узнала: " + ", ".join(t for t, _ in _zn)
                            except Exception:
                                pass
                            if _res_p.get("дописано"):
                                try:
                                    _prosev_dv.otmetit_prosejannym(
                                        [mm.get("id") for mm in _momenty_p
                                        if mm.get("id")])
                                    _prosev_dv.sохранить()
                                except Exception:
                                    pass
                                _prosev_note = f"🪞 {_vyvod_p}"
                except Exception:
                    pass
        return reply, _prosev_note

    async def send_message():
        if not input_ref["element"]:
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""

        # POPRAVKA_UCHITELYA_V1: сообщение с восклицательного знака —
        # это не реплика, а ПОПРАВКА. Ляжет ученику сразу меткой.
        # Сам знак ученику не показываем: он видит обычную фразу
        # учителя и отвечает на неё как всегда.
        _eto_popravka = msg.startswith("!")
        if _eto_popravka:
            msg = msg[1:].strip()
            if not msg:
                return

        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            state["чат"].append({"role": "user", "content": msg})
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": "Это место свободно — здесь некому ответить. "
                          "Кликни на занятый пузырёк."})
            update_chat()
            return

        state["чат"].append({"role": "user", "content": msg})
        update_chat()

        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": "…думает"})
        update_chat()
        _prosev_note = ""
        try:
            _otvet, _prosev_note = await _sprosit_uchenika(
                m["дом"], msg, state["чат"][:-2], state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ не отозвался(лась): {_e}"

        # PATCH_PAMYAT_VEZDE_V1: разговор со студентом -- отпечаток в
        # его личной памяти (сырой опыт, не готовый вывод). Свой
        # sys.path -- на случай, если жители/ ещё не подключены (если
        # "Прочитать"/"Осмыслить" ни разу не нажимались в этой сессии).
        if m["дом"] and not _otvet.startswith("⚠"):
            try:
                _repo_pm = Path(__file__).resolve().parent.parent
                _zh_pm = _repo_pm / "жители"
                if str(_zh_pm) not in sys.path:
                    sys.path.insert(0, str(_zh_pm))
                from dvizhok import Dvizhok as _Dvizhok_pm
                _dv_pm = _Dvizhok_pm(m["дом"])
                _vdoh_pm = _dv_pm.vdoh(kontekst="общение", sila=0.5, svezhest=1.0, tonus="ровно")
                _dv_pm.vydoh_stol(
                    fakt=f"[Академия] Шеф спросил: {msg}\nЯ ответил(а): {_otvet}",
                    vdoh_result=_vdoh_pm)
                _dv_pm.sохранить()
                # POPRAVKA_UCHITELYA_V1: поправка ложится ОТДЕЛЬНО и
                # сразу меткой — твёрдым знанием. Разговор остаётся
                # сырым моментом рядом, ничего не стирая.
                if _eto_popravka:
                    try:
                        _res_p = _dv_pm.popravka_uchitelya(msg)
                        if _res_p.get("легло"):
                            ui.notify("✎ поправка легла в знание",
                                      type="positive")
                        else:
                            ui.notify(f"⚠ поправка не легла: "
                                      f"{_res_p.get('причина','?')}",
                                      type="warning")
                    except AttributeError:
                        ui.notify("⚠ движок без popravka_uchitelya — "
                                  "накати патч на dvizhok.py",
                                  type="negative")
            except Exception:
                pass

        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: осмысление — отдельным
        # сообщением следом, как у кнопки «Осмыслить».
        if _prosev_note:
            state["чат"].append({"role": "assistant", "кто": m["имя"],
                                 "content": _prosev_note})
            update_chat()

    # PATCH_AKADEMIA_STOL_CHTENIE_V1
    async def do_chtenie_akademii():
        """Активный студент читает СО СТОЛА (руда, общая на класс)
        своей натурой. Стол не расходуется -- файл остаётся для
        остальных студентов, читавших его иначе или ещё не читавших."""
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — читать некому", type="warning")
            return
        imya, dom = m["имя"], m["дом"]
        # STOL_TOLKO_POLOZHENNOE_V1: берём ТОЛЬКО то, что положили в
        # загрузчик за эту сессию. Раньше здесь читалась вся папка руды
        # целиком — а руда общая и не расходуется, там копится всё за
        # месяц, и ученику вываливалось пачкой чужое и случайное.
        fajly = []
        for _r in (state.get("руда") or []):
            _p = _r.get("путь")
            if not _p:
                continue
            fp = Path(_p)
            if fp.is_file():
                fajly.append((fp, _r.get("вид") or "текст"))
        if not fajly:
            ui.notify("Стол пуст — положи материал в загрузчик",
                      type="warning")
            return
        uzhe = set(_kto_chto_prochital().get(imya, []))
        novye = [(fp, vid) for fp, vid in fajly if fp.name not in uzhe]
        if not novye:
            ui.notify(f"{imya} уже прочитал(а) всё, что на столе", type="info")
            return
        try:
            rezidenty, Dvizhok = _dvizhok_dlya(dom)
            dv = Dvizhok(dom)
        except Exception as e:
            ui.notify(f"⚠ движок не дышит: {e}", type="negative")
            return
        p = _read_json(dom / "passport.json", {}) or {}
        try:
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица.\n"
        rol = ("\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\nНа столе лежит материал "
               "для изучения — тот же, что видят другие студенты. Читай своей "
               "натурой, не чужой.\n")

        state["чат"].append({"role": "assistant", "кто": "СТОЛ",
                             "content": f"📖 {imya} садится читать {len(novye)} материал(ов) со стола…"})
        update_chat()

        for fp, vid in novye:
            if vid == "текст":
                # CHTENIE_KNIGI_V1: читаем честно и ЦЕЛИКОМ. Раньше
                # ученику доставались первые 20 000 знаков — вдвое
                # меньше, чем жителю дома, и молча.
                tekst = _chtenie.prochitat(fp)
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто — пропускаю", type="warning")
                    continue
                _chasti = _chtenie.narezat(tekst)
                state["чат"].append({"role": "system", "content":
                                     "📖 " + _chtenie.skazat_o_razmere(
                                         fp.name, tekst, len(_chasti))})
                update_chat()
                _hvost = ("" if len(_chasti) == 1 else
                          f" Это часть 1 из {len(_chasti)}, продолжение "
                          f"будет дальше.")
                vopros = (f"Материал: {fp.name}\n{_chasti[0]}\n\n"
                         f"Прочитай и вынеси концентрат — 5-8 строк, суть плюс твой "
                         f"личный отклик через свою натуру.{_hvost}")
                messages = [{"role": "system", "content": dusha + rol},
                           {"role": "user", "content": vopros}]
            else:
                import base64
                try:
                    data = fp.read_bytes()
                except Exception:
                    continue
                mime = _KARTINKA_MIME_STOL.get(fp.suffix.lower(), "image/png")
                url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
                # AKADEMIA_GLAZA_V_CHATE_V1: наблюдение и натура разведены
                # по времени. Раньше они стояли в одном вопросе, и натура
                # побеждала: реставратор икон видел слои копоти вместо
                # баров. Имя файла убрано из запроса — оно и было той
                # соломинкой, за которую хваталась выдумка.
                vopros = (
                    "Перед тобой изображение. Ответь двумя частями.\n\n"
                    "ЧТО ВИЖУ — только то, что действительно нарисовано. "
                    "Буквально, без толкований и сравнений. Есть чертёж, "
                    "схема или график — назови, что именно на нём начерчено. "
                    "Есть текст — о чём он. Не разглядела или мелко — так и "
                    "напиши, это нормальный ответ, догадываться не нужно.\n\n"
                    "ЧТО ЭТО ВО МНЕ — и только теперь твой отклик своей "
                    "натурой, 2-3 фразы.\n\n"
                    "Суди по самой картинке. Её название ничего не значит.")
                messages = [{"role": "system", "content": dusha + rol},
                           {"role": "user", "content": [
                               {"type": "text", "text": vopros},
                               {"type": "image_url", "image_url": {"url": url}},
                           ]}]
            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
            # CHTENIE_KNIGI_V1: остальные части — по очереди, с памятью
            # о прочитанном, и общий свод в конце.
            if vid == "текст" and len(_chasti) > 1 and vyzhimka \
                    and not vyzhimka.startswith("⚠"):
                _vyvody = [vyzhimka]
                for _n, _ch in enumerate(_chasti[1:], 2):
                    state["чат"].append({"role": "system", "content":
                                         f"… часть {_n} из {len(_chasti)}"})
                    update_chat()
                    _m = [{"role": "system", "content": dusha + rol},
                          {"role": "user", "content": (
                              f"Продолжаешь «{fp.name}», часть {_n} из "
                              f"{len(_chasti)}.\n\nЧто вынес(ла) раньше:\n"
                              + "\n".join(f"— {x.strip()[:600]}"
                                          for x in _vyvody)
                              + f"\n\nДальше:\n{_ch}\n\nКонцентрат ЭТОЙ "
                              f"части — 5-8 строк, без повтора прежнего.")}]
                    _v = await _zvat_llm_akademii(_m, state.get("model"))
                    if _v and not _v.startswith("⚠"):
                        _vyvody.append(_v)
                _m2 = [{"role": "system", "content": dusha + rol},
                       {"role": "user", "content": (
                           f"Ты дочитал(а) «{fp.name}» целиком. По ходу "
                           f"выносил(а):\n\n"
                           + "\n\n".join(f"Часть {i}: {x.strip()}"
                                          for i, x in enumerate(_vyvody, 1))
                           + "\n\nСкажи одним куском, что вынес(ла) из "
                           "материала В ЦЕЛОМ. Это и останется в памяти.")}]
                _itog = await _zvat_llm_akademii(_m2, state.get("model"))
                if _itog and not _itog.startswith("⚠"):
                    vyzhimka = _itog
            if not vyzhimka or vyzhimka.startswith("⚠"):
                ui.notify(f"⚠ {fp.name}: {(vyzhimka or 'пустой ответ')[:90]}", type="negative")
                continue
            try:
                vdoh_res = dv.vdoh(kontekst="учёба", sila=0.8, svezhest=1.0, tonus="плюс")
                dv.vydoh_stol(fakt=f"[Академия] «{fp.name}»: {vyzhimka.strip()}", vdoh_result=vdoh_res)
                dv.sохранить()
            except Exception:
                pass
            _otmetit_prochitannym(imya, fp.name)
            state["чат"].append({"role": "assistant", "кто": imya,
                                 "content": f"📖 «{fp.name}» — {vyzhimka.strip()}"})
            ui.notify(f"✦ {imya} прочитал(а): {fp.name}", type="positive")
            update_chat()
        update_vitals()

    async def do_prosev_akademii():
        """Тот же просев, что у жителя (dvizhok.sobrat_dlya_proseva +
        dopisat_vyvod уже существуют и работают) -- здесь просто зовём
        его для активного студента, без похода в кабинет жителя."""
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — осмыслять некому", type="warning")
            return
        imya, dom = m["имя"], m["дом"]
        try:
            rezidenty, Dvizhok = _dvizhok_dlya(dom)
            dv = Dvizhok(dom)
        except Exception as e:
            ui.notify(f"⚠ движок не дышит: {e}", type="negative")
            return
        momenty = dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify(f"{imya}: пока накопилось мало — рано осмыслять", type="warning")
            return
        p = _read_json(dom / "passport.json", {}) or {}
        try:
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {imya}, житель Грондхейма.\n"
        spisok = "\n".join(f"— [{mm['тонус']}] {mm['факт']}" for mm in momenty)
        vopros = (f"Вот моменты из твоей жизни, которые тебя тронули:\n{spisok}\n\n"
                 f"Что это говорит о тебе? Ответь от первого лица, 1–3 фразы, "
                 f"не пересказ моментов.")
        messages = [{"role": "system", "content": dusha},
                   {"role": "user", "content": vopros}]
        vyvod = await _zvat_llm_akademii(messages, state.get("model"))
        if not vyvod or vyvod.startswith("⚠"):
            ui.notify(f"⚠ просев не удался: {(vyvod or '')[:90]}", type="negative")
            return
        vyvod = vyvod.strip()
        res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        # PROSEV_ZNANII_V1: второй заход — за содержанием.
        try:
            _zn = await _prosev_znanii(dv, dusha, momenty, state.get("model"))
            if _zn:
                ui.notify("📚 " + imya + " узнала: "
                          + ", ".join(f"{t} → {e}" for t, e in _zn),
                          type="positive")
        except Exception as _e_zn:
            ui.notify(f"⚠ знание не осело: {_e_zn}", type="warning")
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: НАЙДЕННЫЙ ПОПУТНО БАГ — эта
        # кнопка ни разу не отмечала моменты просеянными. Общий фикс
        # дедупликации (PROSEV_DEDUP_V1, dvizhok.py) без этого вызова
        # бессилен: просев Академии жевал одни и те же топ-моменты по
        # кругу даже после того фикса.
        if res.get("дописано"):
            try:
                dv.otmetit_prosejannym([mm.get("id") for mm in momenty if mm.get("id")])
            except Exception:
                pass
        try:
            dv.sохранить()
        except Exception:
            pass
        if res.get("дописано"):
            state["чат"].append({"role": "assistant", "кто": imya, "content": f"🪞 {vyvod}"})
            ui.notify("✦ вывод дописан в метки", type="positive")
        else:
            ui.notify(f"— {res.get('причина', 'уже было')}", type="info")
        update_chat()

    # AKADEMIA_CHAT_SAVE_V1
    def do_save_chat_akad():
        """Сохраняет чат в дом ТЕКУЩЕГО студента (активное место) --
        своя полка, не общий котёл кабинета Академии."""
        if not state["чат"]:
            ui.notify("Чат пустой — нечего сохранять", type="warning")
            return
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — сохранять некуда", type="warning")
            return
        name = _save_chat_akademii(m["дом"], state["чат"])
        ui.notify(f"💾 сохранено: {name}", type="positive")

    async def do_load_chat_akad():
        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            ui.notify("Место свободно — читать некому", type="warning")
            return
        chats = _list_chaty_akademii(m["дом"])
        if not chats:
            ui.notify("Сохранённых чатов нет", type="warning")
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
                    state["чат"] = _load_chat_akademii(f)
                    update_chat()
                    dlg.close()
                    ui.notify(f"📂 загружен: {f.name}", type="positive")
                ui.button(label, on_click=_load).props("flat no-caps").style(
                    "width:100%; text-align:left; font-family:monospace; "
                    "font-size:0.78rem; color:rgba(255,255,255,0.75); "
                    "padding:8px 12px; border-radius:8px; "
                    "background:rgba(255,255,255,0.04); margin-bottom:4px;")
            ui.button("отмена", on_click=dlg.close).props("flat").style(
                "margin-top:10px; color:rgba(255,255,255,0.4); font-size:0.75rem;")
        dlg.open()

    # ═══ LAYOUT — калька Биржи ═══════════════════════════════
    with ui.element("div").classes("app-container"):

        # ── ШАПКА: пузырьки студентов + кнопки ──
        with ui.element("div").classes("area-header"):
            with ui.element("div").classes("glass squad-deck").style(
                "display:flex; align-items:center; width:100%; gap:8px; padding:0 12px;"
            ):
                with ui.element("div").style(
                    "display:flex; align-items:center; gap:6px; flex-wrap:wrap; "
                    "justify-content:center; flex:1;"
                ):
                    for m in mesta:
                        n = m["место"]
                        cls = f'avatar {"active" if n == state["активное_место"] else ""} ' \
                              f'{"" if m["занято"] else "vacant"}'
                        b = ui.element("div").classes(cls)
                        if m["занято"]:
                            av = _avatar_url(m["дом"])
                            if av:
                                b.style(f"background-image:url('{av}');")
                        b.on("click", lambda e, k=n: switch_mesto(k))
                        with b:
                            if not m["занято"]:
                                ui.label(str(n)).style("font-size: 9px")
                        bubbles["elements"][n] = b

                with ui.row().style("gap:6px; align-items:center;"):
                    with ui.element("div").classes("amodel-sel").style("margin-right:6px;"):
                        _opts = {m["id"]: f'{m["name"]} ({m["price"]})' for m in MODELS_CATALOG}
                        ui.select(_opts, value=state["model"], on_change=on_model_change) \
                            .props('dense borderless dark options-dense').style("min-width:180px;")
                    _b1 = ui.element("div").classes("akad-btn")
                    _b1.on("click", lambda: idti_v_biblioteku())
                    with _b1:
                        ui.html("📚 БИБЛИОТЕКА")
                    _b2 = ui.element("div").classes("akad-btn")
                    _b2.on("click", lambda: idti_domoy())
                    with _b2:
                        ui.html("🏠 ДОМОЙ")
                    _b3 = ui.element("div").classes("akad-btn")
                    _b3.on("click", lambda: idti_v_gorod())
                    with _b3:
                        ui.html("🏙 ГОРОД")

        # ── ЛЕВАЯ: загрузчик руды ──
        with ui.element("div").classes("area-left"):
            with ui.element("div").classes("left-col"):
                with ui.element("div").classes("glass asset-bay"):
                    with ui.row().style(
                        "width:100%; justify-content:space-between; align-items:center; "
                        "padding:8px 16px 6px 16px; border-bottom:1px solid rgba(255,255,255,0.08);"
                    ):
                        ui.label("ЗАГРУЗЧИК").style(
                            "color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em; "
                            "text-transform:uppercase; font-size:11px;")
                        ui.button("CLEAR", on_click=clear_ruda).props("flat dense size=xs").style(
                            "color:rgba(255,80,80,0.5); font-size:9px;")
                    ui.html('<div style="padding:4px 16px 6px 16px;color:rgba(255,255,255,0.35);'
                            'font-size:9px;line-height:1.5;">текст → на просев · '
                            'изображение → на разбор</div>')
                    ruda_ref["uploader"] = ui.upload(
                        on_upload=handle_ruda, multiple=True, auto_upload=True,
                    ).props("flat color=cyan").style("margin: 0 8px 8px 8px;")
                    ruda_ref["element"] = ui.element("div").classes("file-list").style(
                        "max-height:300px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")
                    update_ruda_list()
                    # PATCH_AKADEMIA_STOL_CHTENIE_V1
                    ui.button("📖 Прочитать", on_click=do_chtenie_akademii).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(0,204,255,0.15) !important; "
                        "border:1px solid rgba(0,204,255,0.45) !important; color:#8adfff !important;")
                    ui.button("🪞 Осмыслить", on_click=do_prosev_akademii).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(160,160,220,0.12) !important; "
                        "border:1px solid rgba(160,160,220,0.35) !important; color:#c8c8ec !important;")

                # PATCH_AKADEMIA_UROKI_PANEL_V1
                with ui.element("div").classes("glass").style(
                        "flex:1; min-height:0; overflow:hidden; display:flex; flex-direction:column;"):
                    ui.label("УРОКИ").style(
                        "color:rgba(255,255,255,0.92); font-weight:900; letter-spacing:.12em; "
                        "text-transform:uppercase; font-size:11px; padding:12px 16px 6px 16px;")
                    uroki_ref["element"] = ui.element("div").style(
                        "flex:1; min-height:0; overflow-y:auto; padding-bottom:6px;")
                    update_uroki_panel()
                    ui.button("📖 Дать читать (активный студент)", on_click=do_chtenie_uroka) \
                        .props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:6px 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.78rem; letter-spacing:0.04em; "
                        "background:rgba(0,204,255,0.15) !important; "
                        "border:1px solid rgba(0,204,255,0.45) !important; color:#8adfff !important;")

        # ── ЦЕНТР: тулбар + чат/отчёт + консоль ──
        with ui.element("div").classes("area-stage"):
            with ui.element("div").classes("glass stage-monitor").style("height:100%; overflow:hidden;"):
                with ui.element("div").classes("stage-toolbar"):
                    with ui.element("div").style("display:flex; gap:6px; align-items:center;"):
                        ui.html('<div style="color:rgba(255,255,255,0.55);font-size:11px;'
                                'letter-spacing:.14em;font-weight:900;">АКАДЕМИЯ · ЗАМОК СОВ</div>')
                    with ui.row().style("gap:8px; justify-content:flex-end;"):
                        ui.button("← Брат", on_click=lambda: ui.navigate.to("/brat")).props("flat").style(
                            "padding:6px 14px; border-radius:8px; font-size:12px; "
                            "background:rgba(99,130,255,0.08); border:1px solid rgba(99,130,255,0.25); "
                            "color:rgba(180,190,220,0.8);")

                with ui.element("div").classes("stage-content"):
                    with ui.element("div").classes("split-view"):
                        chat_ref["element"] = ui.element("div").classes("chat-log")
                        with chat_ref["element"]:
                            ui.html('<div class="chat-msg-system">SYSTEM: Замок Сов открыт.</div>')
                        viewer_ref["element"] = ui.element("div").classes("viewer")
                        with viewer_ref["element"]:
                            ui.label("Карточка студента появится здесь")

                with ui.element("div").classes("floating-console"):
                    input_ref["element"] = ui.input(placeholder="Сообщение ученику...").props(
                        "borderless").style("flex:1")
                    input_ref["element"].on("keydown.enter", send_message)
                    # AKADEMIA_CHAT_SAVE_V1
                    ui.button("💾", on_click=do_save_chat_akad).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(0,204,255,0.9); background:rgba(0,204,255,0.10); "
                        "border:1px solid rgba(0,204,255,0.35);")
                    ui.button("📂", on_click=do_load_chat_akad).props("flat").style(
                        "font-size:1.2rem; padding:6px 10px; border-radius:10px; "
                        "color:rgba(189,0,255,0.9); background:rgba(189,0,255,0.10); "
                        "border:1px solid rgba(189,0,255,0.35);")
                    ui.button("SEND", on_click=send_message).classes("send-button")

        # ── ПРАВАЯ: аватар + загрузчик библиотеки ──
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                avatar_ref["element"] = ui.element("div").classes("right-top-slot")
                update_avatar()

                with ui.element("div").classes("glass").style(
                        "margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    vitals_ref["element"] = ui.element("div")
                    update_vitals()

                with ui.element("div").classes("glass").style(
                        "margin-top:12px; flex-shrink:0; overflow:hidden;"):
                    ui.html('<div class="panel-title">БИБЛИОТЕКА</div>')
                    knigi_ref["полка"] = ui.select(
                        POLKI, value="психология", label="полка"
                    ).props("dense outlined dark").style(
                        "margin:8px 16px 4px 16px; font-size:11px;")
                    knigi_ref["uploader"] = ui.upload(
                        on_upload=handle_kniga, multiple=True, auto_upload=True,
                    ).props("flat color=purple").style("margin: 0 8px 6px 8px;")
                    biblio_ref["element"] = ui.element("div")
                    update_biblio_info()

    # первичная отрисовка
    update_chat()
    update_bubbles()
    switch_mesto(state["активное_место"])


if __name__ in {"__main__", "__mp_main__"}:
    @ui.page("/akademia")
    def _akad_page():
        page_akademia()
    ui.run(title="Академия · Грондхейм", port=8105, reload=False)

# AKADEMIA_KABINET_V1 — маркер идемпотентности

# CHTENIE_KNIGI_V1 - marker

# UCHEBNIK_UCHENIKU_V1 - marker
