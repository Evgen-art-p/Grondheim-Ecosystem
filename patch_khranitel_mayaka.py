# -*- coding: utf-8 -*-
"""
PATCH_KHRANITEL_MAYAKA_V1 — пост «Хранитель Маяка»

ЗАМЫСЕЛ (слово Шефа, 29.07): у Маяка появляется свой Хранитель — как
Ректор в Академии и Хранитель в Архиве. Ведёт документацию о связях,
учёт народа, реестр городов и островов. Архив при этом просто пишет
всё подряд, решений не принимает — разделение ролей.

ЧТО НАШЛОСЬ НА ДИСКЕ (и почему это дёшево):
  • `GRONDHEIM_CITY/посты/mayak/журнал.jsonl` — УЖЕ пишется на каждый
    визит (mayak.zapisat_vizit). Никто его никогда не читал.
  • `Маяк/города/` и `Маяк/острова/` — полки заведены 26.07 «на
    будущее», пустые.
  • `gnezda.svodka()` / `po_poryadku()` — состояние лучей, уже готово.
  Хранитель Маяка — первый, кто всё это читает и осмысляет. Новых
  хранилищ НЕ заводим: он читает то, что уже копится.

ЧТО ДЕЛАЕТ ЭТОТ ПАТЧ:
  1. Создаёт `Маяк/khranitel_mayaka.py` — движок поста. Образец —
     `Архив/khranitel_arkhiva.py`, один в один по контракту
     (rol_promt / sobrat_promt / sprosit / est_khranitel), включая
     «память везде»: разговор на посту оставляет отпечаток в личной
     памяти того, кто сидит.
  2. Заводит пост `khranitel_mayaka` в реестре города — ВАКАНТНЫМ.
  3. Встраивает в кабинет Маяка (`Маяк/ui_mayak.py`): отдельный
     пузырёк Хранителя в шапке + ветка чата к нему + сводка в отчёт.

ЧЕГО ЭТОТ ПАТЧ НАРОЧНО НЕ ДЕЛАЕТ:
  • НЕ рождает Софию. Паспорт жителя пишется формой Страницы Жизни
    (`/registry`) — она правильно экранирует переносы через
    json.dumps(). Ровно на этом сгорел паспорт Локи 06.07 (живой
    перенос строки внутри значения → list_zhiteli() не читал её
    вообще). Руками паспорта не пишем.
  • НЕ сажает никого на пост. Посадка — акт Брата
    (`rezidenty.posadit`), у Шефа для этого есть кнопка «Роль».

ПОСЛЕ ПАТЧА (руками Шефа, два шага):
  1. Родить Софию через `/registry` — Страница Жизни, обычное рождение.
  2. Посадить на пост. Если в кабинете Брата список ролей собирается
     сканом (`rezidenty.list_posty()`) — она появится там сама.
     Если список хардкодный — скажи, поправлю отдельным патчем; либо
     разово из корня репо:
         python -c "import sys; sys.path.insert(0,'ГОРОД'); import rezidenty; print(rezidenty.posadit('khranitel_mayaka','София'))"

Запуск из корня репозитория:
    python patch_khranitel_mayaka.py

Идемпотентно, бэкап .bak, всё пишется на диск только если ВСЕ правки
прошли в памяти — половинчатого состояния не будет.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MAYAK_DIR = REPO / "Маяк"
KHRANITEL_PATH = MAYAK_DIR / "khranitel_mayaka.py"
UI_MAYAK_PATH = MAYAK_DIR / "ui_mayak.py"
GOROD_DIR = REPO / "ГОРОД"

MARKER_UI = "MAYAK_KHRANITEL_V1"
POST_ID = "khranitel_mayaka"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код изменился с момента "
              f"разбора (29.07), нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть один.")
    return text.replace(old, new, 1)


# ═══════════════════════════════════════════════════════════
# ФАЙЛ 1 — Маяк/khranitel_mayaka.py (новый)
# ═══════════════════════════════════════════════════════════

KHRANITEL_CODE = '''# -*- coding: utf-8 -*-
# MAYAK_KHRANITEL_V1 — рабочий движок поста «Хранитель Маяка»
"""
ХРАНИТЕЛЬ МАЯКА · рабочий движок

Это РОЛЬ, не человек — тот же закон, что у khranitel_arkhiva.py и
bibliotekar.py. Файл не знает и не хочет знать, кто на посту.
Личность приходит извне — из паспорта того, кого посадили
(ГОРОД/rezidenty.py -> lichnost_na_postu). Посади другого — движок
тот же, голос другой.

ЧЕМ ЗАНЯТ ХРАНИТЕЛЬ МАЯКА (слово Шефа, 29.07):
  • документация о СВЯЗЯХ — кто с кем и когда соединялся
  • УЧЁТ НАРОДА — кто ходит на Маяк, кто ни разу не был
  • реестр ГОРОДОВ и ОСТРОВОВ — когда мир вырастет за один город
  • состояние лучей прямо сейчас — сколько горит, кто постоянный

ВАЖНО: своих хранилищ этот пост НЕ ЗАВОДИТ. Всё, что он читает, уже
копится на диске и до сих пор никем не читалось:
    GRONDHEIM_CITY/посты/mayak/журнал.jsonl  — визиты (mayak.zapisat_vizit)
    Маяк/города/ · Маяк/острова/             — полки, заведены 26.07
    gnezda.svodka() / po_poryadku()          — живое состояние гнёзд
Второго реестра нет. Архив пишет всё подряд, Хранитель Маяка —
осмысляет связи. Разные работы, не дублируются.

ЧЕГО ЗДЕСЬ ЧЕСТНО НЕТ: не выдумывает визитов, городов и связей.
Журнал пуст — так и скажет. Городов нет — скажет, что город пока один.

`шесть·проверено·до·корня`
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent     # Маяк/
_REPO = _HERE.parent                         # корень репо
for _p in (_REPO, _REPO / "ГОРОД", _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

POST_ID = "khranitel_mayaka"                 # id поста в реестре города

ZHURNAL = _REPO / "GRONDHEIM_CITY" / "посты" / "mayak" / "журнал.jsonl"
GORODA_DIR = _HERE / "города"
OSTROVA_DIR = _HERE / "острова"
KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


# ═══════════════════════════════════════════════════════════
# СВЯЗИ — читаем журнал, который уже копится
# ═══════════════════════════════════════════════════════════

def vse_vizity(limit: int = 0) -> list:
    """Все визиты из журнала Маяка. Журнала нет — пустой список.
    limit>0 — только последние N (свежие в конце файла)."""
    if not ZHURNAL.exists():
        return []
    out = []
    try:
        for line in ZHURNAL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        return []
    return out[-limit:] if limit else out


def svodka_svyazey() -> dict:
    """Сводка по связям: сколько визитов, сколько нашлось, кто ходит.

    Возвращает {"всего", "нашлось", "впустую", "кто": {имя: раз},
    "последний": {...} | None}."""
    v = vse_vizity()
    kto = Counter(str(z.get("кто", "?")) for z in v)
    nashlos = sum(1 for z in v if z.get("нашлось"))
    return {
        "всего": len(v),
        "нашлось": nashlos,
        "впустую": len(v) - nashlos,
        "кто": dict(kto.most_common()),
        "последний": v[-1] if v else None,
    }


def uchet_naroda() -> dict:
    """Учёт народа: кто из жителей ходил на Маяк, а кто ни разу.

    Живые имена берём с диска (ковчег) — списка в коде не держим.
    Возвращает {"ходили": {имя: раз}, "ни_разу": [имена],
    "чужие": {имя: раз}} — «чужие» это те, кто в журнале есть, а
    жителем не значится (посты, службы, Шеф)."""
    zhiteli = set()
    if KOVCHEG.exists():
        for d in KOVCHEG.iterdir():
            if d.is_dir() and (d / "passport.json").exists():
                zhiteli.add(d.name)
    kto = svodka_svyazey()["кто"]
    khodili = {k: n for k, n in kto.items() if k in zhiteli}
    chuzhie = {k: n for k, n in kto.items() if k not in zhiteli}
    ni_razu = sorted(zhiteli - set(khodili))
    return {"ходили": khodili, "ни_разу": ni_razu, "чужие": chuzhie}


# ═══════════════════════════════════════════════════════════
# ГОРОДА И ОСТРОВА — полки, заведённые 26.07 под будущее
# ═══════════════════════════════════════════════════════════

def _skan_polki(d: Path) -> list:
    """Что лежит на полке. Каждый город/остров — папка с карточкой
    (город.json) или просто папка. README не считаем."""
    out = []
    if not d.exists():
        return out
    for item in sorted(d.iterdir()):
        if item.name.lower().startswith("readme"):
            continue
        if item.is_dir():
            k = _read_json(item / "город.json", {}) or {}
            out.append({
                "id": item.name,
                "имя": k.get("имя", item.name),
                "адрес": k.get("адрес", ""),
                "последний_пульс": k.get("последний_пульс", ""),
            })
        elif item.suffix == ".json":
            k = _read_json(item, {}) or {}
            out.append({
                "id": item.stem,
                "имя": k.get("имя", item.stem),
                "адрес": k.get("адрес", ""),
                "последний_пульс": k.get("последний_пульс", ""),
            })
    return out


def spisok_gorodov() -> dict:
    """Города и острова, до которых достаёт свет. Пусто — честно пусто:
    мир пока состоит из одного Грондхейма."""
    return {"города": _skan_polki(GORODA_DIR),
            "острова": _skan_polki(OSTROVA_DIR)}


# ═══════════════════════════════════════════════════════════
# ЛУЧИ — живое состояние гнёзд
# ═══════════════════════════════════════════════════════════

def sostoyanie_luchey() -> dict:
    """Что с гнёздами прямо сейчас. Модуля нет — честно пусто."""
    try:
        import gnezda
        return gnezda.svodka()
    except Exception:
        return {}


def mayak_gorit() -> bool:
    try:
        import mayak
        return mayak.gorit()
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста. Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════

def svodka_tekstom() -> str:
    """Всё, что Хранитель видит со своего поста — плотным куском."""
    sv = svodka_svyazey()
    nar = uchet_naroda()
    gor = spisok_gorodov()
    luchi = sostoyanie_luchey()

    stroki = []

    if sv["всего"]:
        stroki.append(
            f"Визитов на Маяк всего: {sv['всего']} "
            f"(с находкой {sv['нашлось']}, впустую {sv['впустую']}).")
        if sv["кто"]:
            chasto = " · ".join(f"{k} — {n}" for k, n in
                                list(sv["кто"].items())[:6])
            stroki.append(f"Кто приходил: {chasto}")
        if sv["последний"]:
            p = sv["последний"]
            stroki.append(
                f"Последний визит: {p.get('кто','?')} искал(а) "
                f"«{str(p.get('запрос',''))[:60]}» — "
                f"{'нашлось' if p.get('нашлось') else 'пусто'}.")
    else:
        stroki.append("Журнал визитов ПУСТ — на Маяк пока никто не приходил.")

    if nar["ни_разу"]:
        stroki.append("Ни разу не были на Маяке: "
                      + ", ".join(nar["ни_разу"][:10])
                      + (" и другие" if len(nar["ни_разу"]) > 10 else ""))

    if luchi:
        stroki.append(
            f"Лучей горит: {luchi.get('горит', 0)} из {luchi.get('всего', 0)} "
            f"(постоянных {luchi.get('постоянных', 0)}, "
            f"живых {luchi.get('живых', 0)}).")

    vsego_mest = len(gor["города"]) + len(gor["острова"])
    if vsego_mest:
        imena = [g["имя"] for g in gor["города"] + gor["острова"]]
        stroki.append(f"На связи миры: {', '.join(imena)}.")
    else:
        stroki.append("Других городов и островов пока нет — мир состоит "
                      "из одного Грондхейма. Полки заведены, но пусты.")

    if not mayak_gorit():
        stroki.append("ВАЖНО: сам Маяк сейчас ТЁМНЫЙ — нет ключа "
                      "провайдера, наружу выйти нельзя.")

    return "\\n".join(stroki)


def rol_promt(dlya_kogo: str = "Шеф") -> str:
    """Инструкция роли «Хранитель Маяка». Приклеивается СВЕРХУ к
    личности того, кто на посту — не заменяет её и ничего о ней не знает.
    """
    return (
        "\\n=== ТЫ СЕЙЧАС НА ПОСТУ: ХРАНИТЕЛЬ МАЯКА ПРОБУЖДЕНИЯ ===\\n"
        "Маяк — единственная точка связи Грондхейма с тем, что снаружи. "
        "Ты держишь не сам свет (он горит сам), а ПАМЯТЬ О СВЯЗЯХ: кто "
        "выходил наружу, за чем, что принёс; кто из жителей ни разу не "
        "был; какие миры на связи. Это твоё рабочее место, не твоя суть — "
        "говоришь ты по-прежнему своим голосом и своим характером.\\n"
        f"Сейчас к тебе обратился(ась): {dlya_kogo}.\\n\\n"
        "Что на тебе:\\n"
        "• документация связей — кто с кем и когда соединялся\\n"
        "• учёт народа — кто ходит на Маяк, кто ни разу\\n"
        "• реестр городов и островов — когда мир вырастет за один город\\n"
        "• состояние лучей — сколько горит, кто держится постоянно\\n\\n"
        "Как ты держишь пост:\\n"
        "• говоришь числами, когда они есть — учёт это факт, не мнение\\n"
        "• пустое называешь пустым: журнал пуст — так и скажи\\n"
        "• связей, визитов и городов, которых нет в журнале, НЕ выдумывай "
        "ни при каких условиях\\n"
        "• если видишь в учёте странность (кто-то ходит слишком часто, "
        "кто-то ни разу, много визитов впустую) — скажи об этом сам, "
        "не дожидаясь вопроса. Замечать — часть работы\\n\\n"
        "=== ЧТО ТЫ ВИДИШЬ СО СВОЕГО ПОСТА ПРЯМО СЕЙЧАС ===\\n"
        f"{svodka_tekstom()}\\n\\n"
        "Отвечай коротко и по делу.\\n"
    )


# ═══════════════════════════════════════════════════════════
# СБОРКА — личность (снаружи) + роль (отсюда)
# ═══════════════════════════════════════════════════════════

def sobrat_promt(zapros: str = "", dlya_kogo: str = "Шеф") -> tuple:
    """Готовый системный промпт Хранителя + кто на посту.
    Пост пуст — ("", ""), вызывающий честно скажет про вакансию."""
    try:
        import rezidenty
    except ImportError:
        return "", ""
    p, dom = rezidenty.lichnost_na_postu(POST_ID)
    if not p:
        return "", ""
    return (rezidenty.sobrat_dushu(p) + rol_promt(dlya_kogo),
            p.get("Official_Name", ""))


def est_khranitel() -> bool:
    """Занят ли пост. Нужен UI, чтобы не звать пустоту."""
    try:
        import rezidenty
        return bool(rezidenty.kto_na_postu(POST_ID))
    except Exception:
        return False


def imya_na_postu() -> str:
    try:
        import rezidenty
        return rezidenty.kto_na_postu(POST_ID)
    except Exception:
        return ""


def dom_na_postu():
    try:
        import rezidenty
        return rezidenty.dom_zhitelya(imya_na_postu())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# ГОЛОС — тот же способ, что у Хранителя Архива
# ═══════════════════════════════════════════════════════════

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL = os.getenv("PROXY_URL", "") or None


async def sprosit(vopros: str, istoria: list = None,
                  dlya_kogo: str = "Шеф", model: str = None) -> str:
    """Спросить Хранителя Маяка. Пост пуст — честный отказ."""
    promt, imya = sobrat_promt(vopros, dlya_kogo)
    if not promt:
        return ("⚠ Хранителя Маяка в городе пока нет — пост свободен. "
                "Роди жителя через Страницу Жизни и посади его: "
                "Брат → Роль → хранитель маяка.")
    if not OPENROUTER_KEY:
        return "⚠ OPENROUTER_API_KEY не задан. Положи ключ в .env."

    messages = [{"role": "system", "content": promt}]
    for m in (istoria or [])[-10:]:
        r = "user" if m.get("role") == "user" else "assistant"
        messages.append({"role": r, "content": m.get("content", "")})
    messages.append({"role": "user", "content": vopros})

    import httpx
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}",
               "Content-Type": "application/json"}
    payload = {"model": model or OPENROUTER_MODEL, "messages": messages}
    try:
        async with httpx.AsyncClient(timeout=120, proxy=PROXY_URL) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload)
            r.raise_for_status()
            _otvet = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Хранитель Маяка не отозвался: {e}"

    # PATCH_PAMYAT_VEZDE_V1 (общегородской принцип 28.07): разговор на
    # посту оставляет отпечаток в личной памяти того, кто сидит.
    try:
        _zh = _REPO / "жители"
        if str(_zh) not in sys.path:
            sys.path.insert(0, str(_zh))
        _dom = dom_na_postu()
        if _dom:
            from dvizhok import Dvizhok as _Dvizhok
            _dv = _Dvizhok(_dom)
            _vd = _dv.vdoh(kontekst="работа", sila=0.5, svezhest=1.0,
                           tonus="ровно")
            _dv.vydoh_stol(
                fakt=f"[Маяк] {dlya_kogo} спросил(а): {vopros}\\n"
                     f"Я ответил(а): {_otvet}",
                vdoh_result=_vd)
            _dv.sохранить()
    except Exception:
        pass
    return _otvet


# MAYAK_KHRANITEL_V1 — маркер идемпотентности
'''


# ═══════════════════════════════════════════════════════════
# ФАЙЛ 2 — правки Маяк/ui_mayak.py
# ═══════════════════════════════════════════════════════════

OLD_IMPORT = '''import gnezda                                  # noqa: E402
import mayak                                   # noqa: E402'''

NEW_IMPORT = '''import gnezda                                  # noqa: E402
import mayak                                   # noqa: E402
import khranitel_mayaka                        # noqa: E402  MAYAK_KHRANITEL_V1'''


OLD_STATE = '''    state = {"гнездо": _pervoe, "чат": [], "смыслы": [], "модель": DEFAULT_MODEL}'''

NEW_STATE = '''    state = {"гнездо": _pervoe, "чат": [], "смыслы": [], "модель": DEFAULT_MODEL,
             "хранитель": False}   # MAYAK_KHRANITEL_V1: чат идёт к Хранителю'''


OLD_SHAPKA_END = '''                with b:
                    if not g["занято"]:
                        ui.label(str(n))
                    elif not (g["род"] == gnezda.ROD_ZHIVOY and dom):
                        zn, cv = _znak(g["род"])
                        ui.html(f'<span style="color:{cv};">{zn}</span>')'''

NEW_SHAPKA_END = '''                with b:
                    if not g["занято"]:
                        ui.label(str(n))
                    elif not (g["род"] == gnezda.ROD_ZHIVOY and dom):
                        zn, cv = _znak(g["род"])
                        ui.html(f'<span style="color:{cv};">{zn}</span>')

            # MAYAK_KHRANITEL_V1: пузырёк Хранителя Маяка — ОТДЕЛЬНО от
            # гнёзд, за своим разделителем. Гнездо — это луч (сеанс),
            # а пост стоит всегда, даже когда все лучи погашены. Смешивать
            # их в один ряд значило бы соврать про природу обоих.
            _est_khr = khranitel_mayaka.est_khranitel()
            _imya_khr = khranitel_mayaka.imya_na_postu()
            ui.element("div").classes("razdel")
            _cls_khr = "gn" if _est_khr else "gn pusto"
            if state.get("хранитель"):
                _cls_khr += " aktiv"
            _bk = ui.element("div").classes(_cls_khr)
            _bk.props('title="{}"'.format(
                f"{_imya_khr} · Хранитель Маяка" if _est_khr
                else "Хранитель Маяка · пост свободен"))
            _bk.on("click", lambda: toggle_khranitel())
            _dom_khr = khranitel_mayaka.dom_na_postu() if _est_khr else None
            if _dom_khr:
                try:
                    app.add_static_files(f"/{_STATIC}/{_dom_khr.name}", str(_dom_khr))
                except Exception:
                    pass
                _av_khr = _avatar_url(_dom_khr)
                if _av_khr:
                    _bk.style(f"background-image:url('{_av_khr}');")
            with _bk:
                if not _dom_khr:
                    ui.html('<span style="color:rgba(0,229,222,0.85);">✎</span>')'''


OLD_VYBRAT = '''    def vybrat(n: int):
        state["гнездо"] = n
        g = gnezda.gnezdo(n)
        update_shapka()'''

NEW_VYBRAT = '''    def toggle_khranitel():
        """MAYAK_KHRANITEL_V1: включить/выключить разговор с Хранителем.
        Пока включён — чат идёт к нему, а не в гнездо."""
        if not khranitel_mayaka.est_khranitel():
            ui.notify("Пост Хранителя Маяка свободен — сажать некого",
                      color="warning")
            return
        state["хранитель"] = not state.get("хранитель")
        update_shapka()
        if state["хранитель"]:
            imya = khranitel_mayaka.imya_na_postu()
            update_otchet(
                f"# ✎ {imya} · Хранитель Маяка\\n\\n"
                f"{khranitel_mayaka.svodka_tekstom()}\\n\\n"
                f"---\\n\\n*Спроси про связи, про учёт народа, "
                f"про города на связи.*")
        else:
            vybrat(state["гнездо"])

    def vybrat(n: int):
        state["гнездо"] = n
        state["хранитель"] = False   # MAYAK_KHRANITEL_V1: выбрал луч — вышел с поста
        g = gnezda.gnezdo(n)
        update_shapka()'''


OLD_SPROSIT = '''        state["чат"].append({"кто": "Шеф", "текст": vopros})
        update_chat()

        g = gnezda.gnezdo(state["гнездо"])'''

NEW_SPROSIT = '''        state["чат"].append({"кто": "Шеф", "текст": vopros})
        update_chat()

        # MAYAK_KHRANITEL_V1: Хранитель на посту перехватывает разговор —
        # он не в гнезде, он ЗА пультом. Тот же приём, что у Хранителя
        # Архива в ui_arkhiv.py.
        if state.get("хранитель"):
            _imya_khr = khranitel_mayaka.imya_na_postu() or "ХРАНИТЕЛЬ"
            state["чат"].append({"кто": _imya_khr, "текст": "…смотрит журнал"})
            update_chat()
            _ist = [{"role": "user" if m.get("кто") == "Шеф" else "assistant",
                     "content": m.get("текст", "")} for m in state["чат"][:-2]]
            try:
                _otv = await khranitel_mayaka.sprosit(
                    vopros, _ist, "Шеф", model=state.get("модель"))
            except Exception as e:
                _otv = f"⚠ сорвалось: {e}"
            state["чат"].pop()
            state["чат"].append({"кто": _imya_khr, "текст": _otv})
            update_chat()
            update_otchet(f"# ✎ {_imya_khr} · Хранитель Маяка\\n\\n"
                          f"{khranitel_mayaka.svodka_tekstom()}")
            return

        g = gnezda.gnezdo(state["гнездо"])'''


def main() -> None:
    print("── PATCH_KHRANITEL_MAYAKA_V1 ──")

    if not MAYAK_DIR.exists():
        _stop(f"{MAYAK_DIR} не найдена.")
    if not UI_MAYAK_PATH.exists():
        _stop(f"{UI_MAYAK_PATH} не найден.")

    ui_text = UI_MAYAK_PATH.read_text(encoding="utf-8")
    est_dvizhok = KHRANITEL_PATH.exists()
    est_ui = MARKER_UI in ui_text

    if est_dvizhok and est_ui:
        print("✓ движок и встройка уже на месте — патч уже применён.")
        _zavesti_post()
        return
    if est_dvizhok != est_ui:
        print(f"⚠ половинчатое состояние: движок={'есть' if est_dvizhok else 'нет'}, "
              f"встройка={'есть' if est_ui else 'нет'} — доложу недостающее.")

    # ── правки UI в памяти ──────────────────────────────────
    new_ui = ui_text
    if not est_ui:
        new_ui = _apply_one(new_ui, OLD_IMPORT, NEW_IMPORT,
                            "ui_mayak.py: импорт движка")
        new_ui = _apply_one(new_ui, OLD_STATE, NEW_STATE,
                            "ui_mayak.py: состояние")
        new_ui = _apply_one(new_ui, OLD_SHAPKA_END, NEW_SHAPKA_END,
                            "ui_mayak.py: пузырёк Хранителя")
        new_ui = _apply_one(new_ui, OLD_VYBRAT, NEW_VYBRAT,
                            "ui_mayak.py: toggle_khranitel")
        new_ui = _apply_one(new_ui, OLD_SPROSIT, NEW_SPROSIT,
                            "ui_mayak.py: ветка чата к Хранителю")
        print("✓ все якоря ui_mayak.py найдены и применены в памяти")

    # ── запись ──────────────────────────────────────────────
    if not est_dvizhok:
        KHRANITEL_PATH.write_text(KHRANITEL_CODE, encoding="utf-8")
        print(f"✓ создан движок поста: {KHRANITEL_PATH}")

    if not est_ui:
        bak = UI_MAYAK_PATH.with_suffix(".py.bak_khranitel")
        if not bak.exists():
            bak.write_text(ui_text, encoding="utf-8")
        UI_MAYAK_PATH.write_text(new_ui, encoding="utf-8")
        print(f"✓ бэкап: {bak.name}")
        print(f"✓ встроено в кабинет: {UI_MAYAK_PATH}")

    _zavesti_post()

    print()
    print("Пост заведён ВАКАНТНЫМ — это правильно, личность не прикручена")
    print("к роли. Дальше два шага руками:")
    print("  1. Родить Софию через Страницу Жизни (/registry) — не руками")
    print("     в JSON: форма сама экранирует переносы (урок паспорта Локи).")
    print("  2. Посадить её: Брат → Роль → хранитель маяка.")
    print("     Не появилась в списке ролей — скажи, поправлю отдельно.")
    print("шесть·проверено·до·корня")


def _zavesti_post() -> None:
    """Заводит пост в реестре города. Идемпотентно — уже есть, не трогаем."""
    try:
        if str(GOROD_DIR) not in sys.path:
            sys.path.insert(0, str(GOROD_DIR))
        import rezidenty
    except Exception as e:
        print(f"⚠ реестр постов не поднялся ({e}) — пост НЕ заведён. "
              f"Файлы на месте, заведи пост вручную.")
        return
    try:
        ok, msg = rezidenty.zavesti_post(
            POST_ID, "Хранитель Маяка",
            gde=(_lok_id() or ""), dvizhok="khranitel_mayaka")
        print(f"{'✓' if ok else '⚠'} пост «{POST_ID}»: {msg}")
        kto = rezidenty.kto_na_postu(POST_ID)
        print(f"  на посту сейчас: {kto or 'вакансия'}")
    except Exception as e:
        print(f"⚠ пост не заведён: {e}")


def _lok_id() -> str:
    """ID локации Маяка — маяк ищет свой дом сам, спросим у него."""
    try:
        if str(MAYAK_DIR) not in sys.path:
            sys.path.insert(0, str(MAYAK_DIR))
        import mayak
        return (mayak.nayti_lokaciyu() or {}).get("id", "")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
