# -*- coding: utf-8 -*-
# patch_zhitel_chtenie.py — ZHITEL_CHTENIE_V1
# ─────────────────────────────────────────────────────────────
# ЧТЕНИЕ ЖИТЕЛЯ: снимаем фанеру с загрузчика Ковчега (ui_zhitel.py).
#
# ЧТО ДЕЛАЕТ:
#   1. Загрузчик оживает: on_upload=handle_upload — файл падает в
#      дом жителя, папка руда_входящее (один в один труба Брата).
#   2. Список файлов настоящий: update_files() сканирует руду,
#      а не печатает зашитую строку «— руды нет —».
#   3. Кнопка «📖 Прочитать»: файл → LLM через ЛИНЗУ МЕСТА
#      (sostoyanie.gde_ya: дома — читает для себя; на месте —
#      как профессионал) → выжимка → ВДОХ движка (kontekst="учёба",
#      sila=0.9, svezhest=1.0) → оседает в archive/archive.jsonl
#      с меткой [Знание: Дом] / [Знание: Цех] (Закон Меток, Гл. 1.5.1).
#   4. Прочитанная книга уходит на полку «прочитано» — второй раз
#      не переваривается (иначе дубли в архиве — настоящий баг).
#   5. Знание — прожитый опыт: житель поднимет его сам через
#      MEMORY_REQUEST (vspomnit ищет по archive). Ни новой library,
#      ни клона просева Брата — движок уже был готов («учёба» → archive).
#
# ЗАПУСК: из корня проекта:  python patch_zhitel_chtenie.py
# Идемпотентен (маркер ZHITEL_CHTENIE_V1), бэкап .bak_*, py_compile.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ZHITEL_CHTENIE_V1"

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "жители" / "ui_zhitel.py"

# ══════════════════════════════════════════════════════════════
# БЛОКИ ЗАМЕН
# ══════════════════════════════════════════════════════════════

# ── 1. импорт events (нужен handle_upload, как у Брата) ──
OLD_IMPORT = "from nicegui import ui\n"
NEW_IMPORT = "from nicegui import ui, events  # ZHITEL_CHTENIE_V1: events для handle_upload\n"

# ── 2. CSS: калька .uploaded-file из кабинета Брата (в Ковчеге её не было) ──
OLD_CSS = ".file-list{ padding:8px 12px; font-family:monospace; font-size:11px; overflow:auto; }"
NEW_CSS = (
    ".file-list{ padding:8px 12px; font-family:monospace; font-size:11px; overflow:auto; }\n"
    "/* ZHITEL_CHTENIE_V1: калька .uploaded-file Брата — список руды рисуется как у него */\n"
    ".uploaded-file{ padding:6px 10px; background:rgba(201,168,76,0.12);\n"
    "  border:1px solid rgba(201,168,76,0.3); border-radius:6px; margin:3px 0;\n"
    "  display:flex; justify-content:space-between; align-items:center; }"
)

# ── 3. модульные помощники чтения — перед page_zhitel ──
ANCHOR_PAGE = '\ndef page_zhitel(zid: str = ""):'

HELPERS = '''
# ═══════════════════════════════════════════════════════════
# ZHITEL_CHTENIE_V1 — ЧТЕНИЕ: житель усваивает знания
# ─────────────────────────────────────────────────────────────
# Механизм приёмки — один в один труба Брата (руда_входящее).
# Кишки — свои: не ЗЕРНО/ПЛАСТИК, а «что изменилось во мне».
# ЛИНЗА МЕСТА (sostoyanie.gde_ya): дома читает для себя (смыслы,
# отклик), на месте/работе — как профессионал (арсенал). Механизм
# один, призма меняется — Закон Меток (Гл. 1.5.1 Чертежа).
# Выжимка идёт ВДОХОМ через движок (kontekst="учёба" → archive):
# знание — не внешний справочник, а прожитый опыт. Житель сам
# поднимет его потом через MEMORY_REQUEST (vspomnit ищет по archive).
# ═══════════════════════════════════════════════════════════
RUDA_PODPAPKA       = "руда_входящее"   # как у Брата — один словарь на весь город
PROCHITANO_PODPAPKA = "прочитано"       # полка: прочитано — второй раз не переваривается
CHTENIE_LIMIT       = 50000             # как у Брата (_read limit=50000)


def _chel_razmer(n) -> str:
    """ZHITEL_CHTENIE_V1: размер по-человечески (калька _human_size Брата)."""
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "Б" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}ТБ"


def _prochitat_fail(path: Path, limit: int = CHTENIE_LIMIT) -> str:
    """ZHITEL_CHTENIE_V1: честное чтение текста файла.
    UTF-8 строго → откат на cp1251 (русские книги из Windows) →
    utf-8 с заменой. Бинарь-щит: нули или море замен — это не книга,
    вернём "" (кабинет честно скажет «не текст»)."""
    try:
        raw = path.read_bytes()
    except Exception:
        return ""
    t = ""
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            t = raw.decode("cp1251")
        except UnicodeDecodeError:
            t = raw.decode("utf-8", errors="replace")
    if "\\x00" in t or ("\\ufffd" in t and len(t) > 200 and t.count("\\ufffd") / len(t) > 0.10):
        return ""
    return t[:limit] if limit else t


def _linza_chtenia(dom) -> tuple:
    """ZHITEL_CHTENIE_V1: линза восприятия по ЖИВОМУ месту (sostoyanie.gde_ya).
    Дома → «дом» (читает для себя). Не дома → «работа» (читает как
    профессионал на месте). Возвращает (линза, имя_локации)."""
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in sys.path:
            sys.path.insert(0, str(_repo))
        import sostoyanie as _sost
        r = _sost.gde_ya(dom)
        lok = r.get("локация") or ""
        try:
            lok_imya = _lokacia_name(lok) if lok else ""
        except Exception:
            lok_imya = str(lok)
        if r.get("дома", True):
            return "дом", lok_imya
        return "работа", lok_imya
    except Exception:
        return "дом", ""  # sostoyanie нет — тихий откат: читает как дома


def _dusha_chtenia(p: dict) -> str:
    """ZHITEL_CHTENIE_V1: душа для чтения — та же личность, что видит
    чат (send / YAKORYA_V_SOUL_V1), без диалоговых наставлений.
    Пустые поля пропускаем — промпт не раздуваем."""
    imya = p.get("Official_Name", "житель")
    s = (f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица, "
         f"живым голосом, не как ассистент.\\n")
    if p.get("Core_Phrase"):
        s += f"Твоё ядро (коронная фраза): «{p['Core_Phrase']}»\\n"
    if p.get("Hidden_History"):
        s += f"Твоя скрытая история: {p['Hidden_History']}\\n"
    if p.get("Sensory_Response"):
        s += f"Как ты чувствуешь мир: {p['Sensory_Response']}\\n"
    if p.get("Anchor_Points"):
        s += f"Твои незыблемые якоря: {p['Anchor_Points']}\\n"
    if p.get("Hidden_Taste"):
        s += f"Твой скрытый вкус (эстетика): {p['Hidden_Taste']}\\n"
    if p.get("Pull_Vector"):
        s += f"Тебя тянет к: {p['Pull_Vector']}\\n"
    if p.get("домашний_промпт"):  # PATCH_DOM_V_DUSHU: дом носишь в себе всегда
        s += f"Твой дом, который ты носишь в себе всегда: {p['домашний_промпт']}\\n"
    dna = p.get("DNA_Static", {}) or {}
    if isinstance(dna, dict) and dna:
        s += "Твоя натура (черты характера): " + " · ".join(
            f"{k.split('_')[0]} {v}" for k, v in dna.items()) + "\\n"
    return s


def _prompt_chtenia(imya_fajla: str, tekst: str, linza: str, lok_imya: str) -> str:
    """ZHITEL_CHTENIE_V1: вопрос жителю по линзе места.
    РАБОТА — структурная польза в арсенал. ДОМ — смыслы и отклик.
    Не «оцени факты и найди связи» (это фильтр Брата), а
    «ты прочитал(а) — что усвоилось, что отзовётся в тебе»."""
    if linza == "работа":
        gde = (f"Ты сейчас на месте — {lok_imya}." if lok_imya
               else "Ты сейчас на работе, за делом.")
        zadacha = ("Прочитай это как профессионал за делом: вытащи структурную "
                   "пользу — алгоритмы, паттерны, приёмы, рабочие схемы, "
                   "которые пополнят твой арсенал.")
    else:
        gde = "Ты сейчас дома, читаешь для себя, в своём ритме."
        zadacha = ("Прочитай это как человек для себя: что тронуло, какие мысли "
                   "и смыслы отозвались, какая эстетика запомнилась, что из "
                   "этого отзовётся в тебе дальше.")
    return (
        f"{gde}\\nТебе принесли текст.\\n"
        f"FILENAME: {imya_fajla}\\nCONTENT:\\n{tekst}\\n\\n"
        f"{zadacha}\\n"
        f"Напиши концентрат усвоенного от первого лица: 5–12 плотных строк — "
        f"суть плюс твой личный отклик. Не пересказывай файл целиком — усвой его. "
        f"Без строк MEMORY_REQUEST."
    )

'''

# ── 4. update_files: фанера → живой скан; + handle_upload + do_chtenie ──
OLD_UPDATE_FILES = '''    def update_files():
        el = refs["files"]
        if not el: return
        el.clear()
        with el:
            ui.html('<div style="opacity:0.4; font-size:11px; padding:4px;">— руды нет —</div>')
'''

NEW_UPDATE_FILES = '''    def update_files():
        # ZHITEL_CHTENIE_V1: живой скан руды жителя (dom/руда_входящее) —
        # калька update_files Брата. Фанера снята, список настоящий.
        el = refs["files"]
        if not el: return
        el.clear()
        ruda_dir = (dom / RUDA_PODPAPKA) if dom is not None else None
        fajly = []
        if ruda_dir is not None and ruda_dir.exists():
            for _fp in sorted(ruda_dir.iterdir()):
                if _fp.is_file() and _fp.name.lower() != "readme.md":
                    try:
                        fajly.append((_fp.name, _fp.stat().st_size))
                    except Exception:
                        fajly.append((_fp.name, 0))
        with el:
            if fajly:
                for fn, sz in fajly:
                    ui.html(f'<div class="uploaded-file"><span>{fn}</span>'
                            f'<span style="opacity:0.6">{_chel_razmer(sz)}</span></div>')
            else:
                ui.html('<div style="opacity:0.4; font-size:11px; padding:4px;">— руды нет —</div>')

    def handle_upload(e: events.UploadEventArguments):
        # ZHITEL_CHTENIE_V1: приёмка — один в один труба Брата
        # (handle_upload ui_brat.py). Файл падает в ДОМ жителя.
        try:
            if dom is None:
                ui.notify("дом не найден — руду класть некуда", color="warning")
                return
            ruda_dir = dom / RUDA_PODPAPKA
            ruda_dir.mkdir(parents=True, exist_ok=True)
            (ruda_dir / e.name).write_bytes(e.content.read())
            ui.notify(f"⛏ руда: {e.name}", color="positive")
            update_files()
        except Exception as ex:
            ui.notify(f"⚠ {ex}", color="negative")

    async def do_chtenie():
        """ZHITEL_CHTENIE_V1: житель ЧИТАЕТ руду.
        Файл → LLM через линзу места → выжимка → ВДОХ движка
        (kontekst="учёба" → осело в archive) → книга на полку «прочитано».
        Знание становится прожитым опытом — vspomnit() его поднимет."""
        if state.get("waiting"):
            return
        if dom is None or not (dom / "passport.json").exists():
            ui.notify("дом не найден или паспорт пуст — читать некому", color="warning")
            return
        ruda_dir = dom / RUDA_PODPAPKA
        fajly = ([f for f in sorted(ruda_dir.iterdir()) if f.is_file()
                  and f.name.lower() != "readme.md"]
                 if ruda_dir.exists() else [])
        if not fajly:
            ui.notify("руды нет — нечего читать", color="warning")
            return
        try:
            _dv = Dvizhok(dom)
        except Exception as ex:
            ui.notify(f"⚠ движок не дышит: {ex}", color="negative")
            return
        state["waiting"] = True
        linza, lok_imya = _linza_chtenia(dom)
        ui.notify(f"📖 {name} читает {len(fajly)} файл(ов)"
                  + (f" — на месте «{lok_imya}»" if linza == "работа" else " — дома"),
                  color="info")
        # осадку нужно дно: _zapisat_sobytie молчит, если папки archive нет
        try:
            (dom / "archive").mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        dusha = _dusha_chtenia(p)
        prochitano_dir = dom / PROCHITANO_PODPAPKA
        for fp in fajly:
            tekst = _prochitat_fail(fp)
            if not tekst.strip():
                ui.notify(f"⚠ {fp.name}: пусто или не текст — пропускаю", color="warning")
                continue
            messages = [
                {"role": "system", "content": dusha},
                {"role": "user", "content": _prompt_chtenia(fp.name, tekst, linza, lok_imya)},
            ]
            vyzhimka = await call_zhitel_llm(messages, state.get("model"))
            if not vyzhimka or vyzhimka.startswith("⚠"):
                ui.notify(f"⚠ {fp.name}: {(vyzhimka or 'пустой ответ')[:90]}", color="negative")
                continue
            vyzhimka = _ubrat_memory_request(vyzhimka) or vyzhimka.strip()
            # Закон Меток (Гл. 1.5.1): жёсткая метка контекста чтения
            metka = "[Знание: Цех]" if linza == "работа" else "[Знание: Дом]"
            fakt = f"{metka} книга «{fp.name}»: {vyzhimka.strip()}"
            # ВДОХ: канон Локи — sila=0.9, svezhest=1.0; тонус — по отклику
            # самого жителя (тронуло/задело — качнёт маятник в свою сторону)
            tonus, _sila_otklika = _otsenit_tonus_silu(vyzhimka)
            vdoh_res = _dv.vdoh(kontekst="учёба", sila=0.9, svezhest=1.0, tonus=tonus)
            _dv.vydoh_stol(fakt=fakt, vdoh_result=vdoh_res)  # → archive/archive.jsonl
            # книга прочитана — на полку (иначе повторный клик = дубли в архиве)
            try:
                prochitano_dir.mkdir(parents=True, exist_ok=True)
                _dst = prochitano_dir / fp.name
                if _dst.exists():
                    _dst = prochitano_dir / f"{fp.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{fp.suffix}"
                fp.rename(_dst)
            except Exception:
                pass
            state["chat"].append({"role": "zhitel",
                                  "content": f"📖 «{fp.name}» — {vyzhimka.strip()}"})
            ui.notify(f"✦ прочитано: {fp.name}", color="positive")
        try:
            _dv.sохранить()  # заряд оседает в паспорт — прочитанное пережито
        except Exception:
            pass
        state["waiting"] = False
        update_files()
        update_chat()
'''

# ── 5. загрузчик: подключаем обработчик (заглушка → труба) ──
OLD_UPLOAD = '''ui.upload(multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")'''
NEW_UPLOAD = '''ui.upload(on_upload=handle_upload, multiple=True, auto_upload=True).props("flat color=amber").style("margin:8px;")  # ZHITEL_CHTENIE_V1'''

# ── 6. кнопка «Прочитать» под списком руды (зеркало «Просеять» Брата) ──
OLD_FILES_BLOCK = '''                    refs["files"] = ui.element("div").classes("file-list")
                    update_files()
'''
NEW_FILES_BLOCK = '''                    refs["files"] = ui.element("div").classes("file-list")
                    update_files()
                    # ZHITEL_CHTENIE_V1: житель читает руду (зеркало «⚗ Просеять»
                    # Брата, но кишки свои — линза места, вдох, archive)
                    ui.button("📖 Прочитать", on_click=do_chtenie).props("flat no-caps").style(
                        "width:calc(100% - 16px); margin:0 8px 8px 8px; border-radius:10px; "
                        "font-weight:700; font-size:0.82rem; letter-spacing:0.06em; "
                        "background:rgba(201,168,76,0.15) !important; "
                        "border:1px solid rgba(201,168,76,0.45) !important; color:#e8c96a !important;")
'''

EOF_MARKER = "\n# ZHITEL_CHTENIE_V1 — маркер идемпотентности\n"


# ══════════════════════════════════════════════════════════════
# МЕХАНИКА ПАТЧА
# ══════════════════════════════════════════════════════════════

def main():
    print("═" * 62)
    print(f"  ПАТЧ {MARKER}: чтение жителя (Ковчег)")
    print("═" * 62)

    if not TARGET.exists():
        print(f"✗ не найден {TARGET}")
        print("  Запусти патч из корня проекта (рядом с папкой жители/).")
        sys.exit(1)

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"• маркер {MARKER} уже стоит — патч применён ранее. Выходим чисто.")
        sys.exit(0)

    # проверяем ВСЕ якоря до первой правки — либо режем всё, либо ничего
    anchors = [
        ("импорт nicegui",        OLD_IMPORT),
        ("CSS .file-list",        OLD_CSS),
        ("def page_zhitel",       ANCHOR_PAGE),
        ("заглушка update_files", OLD_UPDATE_FILES),
        ("ui.upload без ручки",   OLD_UPLOAD),
        ("блок file-list",        OLD_FILES_BLOCK),
    ]
    ok = True
    for label, a in anchors:
        n = text.count(a)
        status = "✓" if n == 1 else "✗"
        print(f"  {status} якорь [{label}]: найден {n} раз (нужно ровно 1)")
        if n != 1:
            ok = False
    if not ok:
        print("✗ якоря не сошлись — файл отличается от ожидаемого. Ничего не режу.")
        sys.exit(1)

    # бэкап
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = TARGET.with_name(TARGET.name + f".bak_{ts}")
    shutil.copy2(TARGET, bak)
    print(f"• бэкап: {bak.name}")

    # правки
    text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)
    text = text.replace(OLD_CSS, NEW_CSS, 1)
    text = text.replace(ANCHOR_PAGE, "\n" + HELPERS + "\ndef page_zhitel(zid: str = \"\"):", 1)
    text = text.replace(OLD_UPDATE_FILES, NEW_UPDATE_FILES, 1)
    text = text.replace(OLD_UPLOAD, NEW_UPLOAD, 1)
    text = text.replace(OLD_FILES_BLOCK, NEW_FILES_BLOCK, 1)
    text += EOF_MARKER

    TARGET.write_text(text, encoding="utf-8")
    print("• правки внесены")

    # проверка компиляции — иначе откат
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("• py_compile: ЗЕЛЁНЫЙ")
    except Exception as e:
        shutil.copy2(bak, TARGET)
        print(f"✗ py_compile упал: {e}")
        print("  Файл откатан из бэкапа. Ничего не сломано.")
        sys.exit(1)

    print()
    print("  ГОТОВО. Что появилось в Ковчеге:")
    print("  1. Загрузчик живой: файл → дом жителя / руда_входящее")
    print("  2. Список руды — настоящий скан (не фанера)")
    print("  3. Кнопка «📖 Прочитать»: линза места → выжимка → вдох")
    print("     (учёба → archive) → книга на полку «прочитано»")
    print("  4. Знание поднимается жителем через MEMORY_REQUEST")
    print("═" * 62)


if __name__ == "__main__":
    main()
