# PATCH_AKADEMIA_STOL_CHTENIE_V1
"""
PATCH_AKADEMIA_STOL_CHTENIE_V1 -- «Стол Академии» (слово Шефа, 27.07):
руда в Академии общая на весь класс, не своя у каждого студента, как
у жителя — значит устроена она должна быть как Стол Трейдера в Бирже,
не как руда_входящее жителя.

МОДЕЛЬ:
  - материал (руда/тексты, руда/изображения) НЕ расходуется и НЕ
    двигается никуда после прочтения -- лежит на столе постоянно,
    как факт, который видят все;
  - АКТИВНЫЙ студент (выбранный пузырёк) читает материал СВОЕЙ
    натурой (rezidenty.sobrat_dushu) -- один и тот же файл разные
    студенты прочтут по-разному;
  - что каждый студент уже прочитал -- отдельный реестр рядом со
    столом (руда/прочитано.json: {студент: [файлы]}), чтобы один и
    тот же клик не заставлял читать по кругу; но ДРУГИЕ студенты
    видят файл как непрочитанный и могут прочитать его по-своему;
  - вывод идёт личной памятью студента (dvizhok.vdoh/vydoh_stol,
    kontekst="учёба") -- та же труба, что уже использует Ректор;
  - «Осмыслить» -- тот же механизм просева, что уже есть у жителя
    (dvizhok.sobrat_dlya_proseva + dopisat_vyvod), просто вызван для
    активного студента прямо из кабинета Академии, без похода в
    кабинет жителя.

Идемпотентно: если маркер PATCH_AKADEMIA_STOL_CHTENIE_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении. Не зависит от порядка
относительно patch_akademia_vizual.py -- трогает другие места файла.

Запуск из корня репо:  python patch_akademia_stol_chtenie.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/ui_akademia.py')
MARKER = 'PATCH_AKADEMIA_STOL_CHTENIE_V1'

OLD_MODULE_ANCHOR = '''def _load_chat_akademii(fp: Path) -> list:
    return json.loads(fp.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
# СТИЛЬ — снят с Биржи один в один
# ═══════════════════════════════════════════════════════════'''

NOVYI_MODULE_ANCHOR = '''def _load_chat_akademii(fp: Path) -> list:
    return json.loads(fp.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
# PATCH_AKADEMIA_STOL_CHTENIE_V1 -- Стол Академии. Руда общая, не
# расходуется -- как Стол Трейдера в Бирже. Реестр "кто что прочитал"
# лежит рядом со столом, не трогая сам стол.
# ═══════════════════════════════════════════════════════════
_PROCHITANO_REESTR = _RUDA / "прочитано.json"
_KARTINKA_MIME_STOL = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                       ".webp": "image/webp", ".gif": "image/gif"}


def _kto_chto_prochital() -> dict:
    return _read_json(_PROCHITANO_REESTR, {}) or {}


def _otmetit_prochitannym(imya: str, fajl: str):
    reg = _kto_chto_prochital()
    reg.setdefault(imya, [])
    if fajl not in reg[imya]:
        reg[imya].append(fajl)
    _write_json(_PROCHITANO_REESTR, reg)


async def _zvat_llm_akademii(messages, model: str = "") -> str:
    """Общий вызов LLM -- тот же способ, что и весь кабинет.
    Самодостаточная функция (свой os.getenv) -- Закон Двух Стандартов."""
    _key = os.getenv("OPENROUTER_API_KEY", "")
    if not _key:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."
    import httpx
    headers = {"Authorization": f"Bearer {_key}", "Content-Type": "application/json"}
    payload = {"model": model or DEFAULT_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ не отозвался: {e}"


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
# СТИЛЬ — снят с Биржи один в один
# ═══════════════════════════════════════════════════════════'''

OLD_NESTED_ANCHOR = '''        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()

    # AKADEMIA_CHAT_SAVE_V1
    def do_save_chat_akad():'''

NOVYI_NESTED_ANCHOR = '''        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
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
        fajly = []
        for papka, vid in ((_RUDA / "тексты", "текст"), (_RUDA / "изображения", "изображение")):
            if papka.exists():
                for fp in sorted(papka.iterdir()):
                    if fp.is_file():
                        fajly.append((fp, vid))
        if not fajly:
            ui.notify("Стол пуст — нечего читать", type="warning")
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
            dusha = f"Ты — {imya}, житель Грондхейма. Говоришь от первого лица.\\n"
        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\nНа столе лежит материал "
               "для изучения — тот же, что видят другие студенты. Читай своей "
               "натурой, не чужой.\\n")

        state["чат"].append({"role": "assistant", "кто": "СТОЛ",
                             "content": f"📖 {imya} садится читать {len(novye)} материал(ов) со стола…"})
        update_chat()

        for fp, vid in novye:
            if vid == "текст":
                try:
                    tekst = fp.read_bytes().decode("utf-8", errors="replace")
                except Exception:
                    tekst = ""
                if not tekst.strip():
                    ui.notify(f"⚠ {fp.name}: пусто — пропускаю", type="warning")
                    continue
                vopros = (f"Материал: {fp.name}\\n{tekst[:20000]}\\n\\n"
                         f"Прочитай и вынеси концентрат — 5-8 строк, суть плюс твой "
                         f"личный отклик через свою натуру.")
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
                vopros = (f"На столе изображение: {fp.name}. Посмотри своей натурой, "
                         f"вынеси концентрат — 5-8 строк, суть плюс личный отклик.")
                messages = [{"role": "system", "content": dusha + rol},
                           {"role": "user", "content": [
                               {"type": "text", "text": vopros},
                               {"type": "image_url", "image_url": {"url": url}},
                           ]}]
            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
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
            dusha = f"Ты — {imya}, житель Грондхейма.\\n"
        spisok = "\\n".join(f"— [{mm['тонус']}] {mm['факт']}" for mm in momenty)
        vopros = (f"Вот моменты из твоей жизни, которые тебя тронули:\\n{spisok}\\n\\n"
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
    def do_save_chat_akad():'''

OLD_KNOPKI_ANCHOR = '''                    ruda_ref["uploader"] = ui.upload(
                        on_upload=handle_ruda, multiple=True, auto_upload=True,
                    ).props("flat color=cyan").style("margin: 0 8px 8px 8px;")
                    ruda_ref["element"] = ui.element("div").classes("file-list").style(
                        "max-height:300px; overflow-y:auto; overflow-x:hidden; padding:4px 8px;")
                    update_ruda_list()'''

NOVYI_KNOPKI_ANCHOR = '''                    ruda_ref["uploader"] = ui.upload(
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
                        "border:1px solid rgba(160,160,220,0.35) !important; color:#c8c8ec !important;")'''

REPLACEMENTS = [
    (OLD_MODULE_ANCHOR, NOVYI_MODULE_ANCHOR),
    (OLD_NESTED_ANCHOR, NOVYI_NESTED_ANCHOR),
    (OLD_KNOPKI_ANCHOR, NOVYI_KNOPKI_ANCHOR),
]

REPLACE_ALL = [
]


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_stol_chtenie")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
