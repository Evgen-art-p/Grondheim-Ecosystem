# -*- coding: utf-8 -*-
# AKADEMIA_REKTOR_V1 — рабочий движок поста «ректор»
"""
РЕКТОР АКАДЕМИИ · рабочий движок

Это РОЛЬ, не человек — тот же закон, что у bibliotekar.py и
khranitel_arkhiva.py. Пост — честная вакансия (rezidenty.py), личность
приходит извне. Кто сядет ректором — решает Брат, этот файл никого
не назначает и не привязывает сам.

ЗАЧЕМ РЕКТОР (слово Шефа): любой житель может пойти учиться. В
кабинете жителя кнопка «Учёба» ведёт сюда — Ректор проводит
собеседование, зачисляет (или не зачисляет — это его решение, не
автомат), дальше держит все оценки, экзамены и в конце выдаёт диплом
на профессию.

МЫ НЕ ЗНАЕМ, НАСКОЛЬКО ЭТО ВЫРАСТЕТ (слово Шефа) — поэтому сейчас
только основа: зачисление, оценка, экзамен, диплом. Что экзамен
проверяет и как считается «сдал» — решает Ректор словами в
разговоре, не жёсткая формула здесь. Формула появится, когда Шеф
увидит, что мало.

ДАННЫЕ ОБЩИЕ С АКАДЕМИЕЙ — один реестр, не два:
    GRONDHEIM_CITY/Академия/ученики.json  ("места": [...])
Ректор дописывает в ту же запись места: статус, оценки, экзамены,
диплом. Второго реестра студентов не заводим.

`шесть·проверено·до·корня`
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).resolve().parent     # Академия/
_REPO = _HERE.parent                         # корень репо
for _p in (_REPO, _REPO / "ГОРОД", _REPO / "жители", _HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

POST_ID = "rektor"                           # id поста в реестре города

_DATA = _REPO / "GRONDHEIM_CITY" / "Академия"
_UCHENIKI = _DATA / "ученики.json"
MEST = 10   # то же число мест, что у кабинета Академии


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ═══════════════════════════════════════════════════════════
# МОСТ В ЛИЧНУЮ ПАМЯТЬ ЖИТЕЛЯ (dvizhok.py, три этажа)
# ═══════════════════════════════════════════════════════════
# AKADEMIA_REKTOR_DVIZHOK_BRIDGE_V1: житель должен ПОМНИТЬ, что учился —
# не только запись в ученики.json (факт/оценка), но и в его личной
# памяти, той же, что видит Биржа. nositel.py (Биржа/nositel.py) УЖЕ
# читает метки с otkuda="учёба" и подписывает их «чему тебя учили» —
# это готовый провод, ректор просто ничего в него не пускал. Теперь
# пускает: собеседование/оценка/экзамен/диплом ложатся и в реестр
# (факт), и в метки/маяки (личный опыт, всплывёт в работе, житель
# сможет столкнуть «чему учили» с «что сказал рынок»).
#
# Разные события — разная сила и разный порог:
#   зачисление и диплом — вехи жизни, сразу МЕТКА (pattern=None)
#   отдельная оценка/экзамен — черновик-МАЯК по предмету (pattern=predmet),
#   набежит порог повторов — сам станет меткой (закон dvizhok, не мы решаем)

def _zapomnit_uchebu(imya: str, fakt: str, vyvod: str,
                     pattern: str | None = None,
                     sila: float = 0.6, tonus: str = "плюс") -> None:
    """Честно пробует прожить событие через dvizhok жителя. Не вышло
    (нет резидента, нет dvizhok.py, паспорт битый) — тихо не падаем:
    факт всё равно уже лёг в ученики.json, это не единственная правда."""
    try:
        import rezidenty
        dom = rezidenty.dom_zhitelya(imya)
        if not dom:
            return
        from dvizhok import Dvizhok
        d = Dvizhok(dom)
        vdoh_res = d.vdoh("учёба", sila, 1.0, tonus)
        d.vydoh_stol(fakt, vdoh_res)
        d.dopisat_vyvod(vyvod, pattern=pattern, otkuda="учёба")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# РЕЕСТР МЕСТ — общий с Академией
# ═══════════════════════════════════════════════════════════

def _zapisi() -> list:
    return (_read_json(_UCHENIKI, {"места": []}) or {"места": []}).get("места", []) or []


def _sokhranit_zapisi(zapisi: list):
    kat = _read_json(_UCHENIKI, {"места": []}) or {"места": []}
    kat["места"] = zapisi
    _write_json(_UCHENIKI, kat)


def najti_zapis(imya: str) -> dict:
    """Запись места этого жителя. Не учится — пустой словарь."""
    for z in _zapisi():
        if z.get("житель", "") == imya:
            return z
    return {}


def est_studentom(imya: str) -> bool:
    return bool(najti_zapis(imya))


def svobodnoe_mesto() -> int | None:
    """Первое свободное место 1..MEST. Мест нет — None, честно."""
    zanyato = {z.get("место") for z in _zapisi() if z.get("житель")}
    for n in range(1, MEST + 1):
        if n not in zanyato:
            return n
    return None


# ═══════════════════════════════════════════════════════════
# ДЕЙСТВИЯ РЕКТОРА — явные, не из текста чата. Разговор — отдельно,
# действие — отдельная кнопка. LLM не мутирует реестр сам по себе.
# ═══════════════════════════════════════════════════════════

def zachislit(imya: str, kurs: str = "") -> tuple:
    """Зачисляет жителя на первое свободное место. Уже учится —
    честно скажет, не задвоит запись. Мест нет — честный отказ.
    """
    if est_studentom(imya):
        return False, f"{imya} уже учится — второй раз не зачисляю"
    mesto = svobodnoe_mesto()
    if mesto is None:
        return False, f"мест нет — все {MEST} заняты"
    zapisi = _zapisi()
    zapisi.append({
        "место": mesto, "житель": imya, "курс": kurs,
        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
    })
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Поступил(а) в Академию Грондхейма (Замок Сов)",
        "Я учусь в Академии Грондхейма", pattern=None, sila=0.6)
    return True, f"{imya} зачислен(а) на место {mesto}"


def otchislit(imya: str) -> tuple:
    """Освобождает место. Обратимо — статус меняется, история (оценки)
    остаётся в записи до момента удаления, если Шеф не попросит стереть."""
    zapisi = _zapisi()
    est = next((i for i, z in enumerate(zapisi) if z.get("житель") == imya), None)
    if est is None:
        return False, f"{imya} и так не студент(ка)"
    zapisi.pop(est)
    _sokhranit_zapisi(zapisi)
    return True, f"{imya} отчислен(а), место освобождено"


def postavit_otsenku(imya: str, predmet: str, otsenka: str) -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z.setdefault("оценки", []).append({
                "предмет": predmet, "оценка": otsenka, "когда": _now()})
            _sokhranit_zapisi(zapisi)
            _zapomnit_uchebu(
                imya, f"Получил(а) оценку «{otsenka}» по «{predmet}»",
                f"По предмету «{predmet}»: {otsenka}",
                pattern=f"оценка:{predmet}", sila=0.4)
            return True, f"оценка «{otsenka}» по «{predmet}» выставлена {imya}"
    return False, f"{imya} не студент(ка) — оценку ставить некуда"


def provesti_ekzamen(imya: str, predmet: str, rezultat: str) -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z.setdefault("экзамены", []).append({
                "предмет": predmet, "результат": rezultat, "когда": _now()})
            _sokhranit_zapisi(zapisi)
            _zapomnit_uchebu(
                imya, f"Сдал(а) экзамен «{predmet}»: {rezultat}",
                f"Экзамен «{predmet}»: {rezultat}",
                pattern=f"экзамен:{predmet}", sila=0.6)
            return True, f"экзамен «{predmet}» ({rezultat}) записан для {imya}"
    return False, f"{imya} не студент(ка) — экзамен принимать не у кого"


def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            _sokhranit_zapisi(zapisi)
            _prof = professiya or "специалист(ка)"
            _zapomnit_uchebu(
                imya, f"Получил(а) диплом Академии по специальности «{_prof}»",
                f"Я — дипломированный(ая) {_prof}, умею применять эти "
                f"знания в работе, не только помнить их как урок",
                pattern=None, sila=0.9)
            return True, f"диплом «{professiya or 'без указания профессии'}» выдан {imya}"
    return False, f"{imya} не студент(ка) — диплом выдавать некому"


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста (собеседование). Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════

def rol_promt(kandidat_imya: str = "", uzhe_student: bool = False,
              dlya_kogo: str = "Шеф") -> str:
    sost = (f"{kandidat_imya} уже студент(ка) Академии." if uzhe_student
            else (f"{kandidat_imya} — кандидат(ка), пока не зачислен(а)."
                  if kandidat_imya else "Разговариваешь без конкретного кандидата."))
    return (
        "\n=== ТЫ СЕЙЧАС НА ПОСТУ: РЕКТОР АКАДЕМИИ (Замок Сов) ===\n"
        "Ты решаешь, кто учится в Академии, ведёшь собеседования, "
        "выставляешь оценки, принимаешь экзамены и выдаёшь дипломы на "
        "профессию. Это твоё рабочее место, не твоя суть — говоришь ты "
        "своим голосом, своим характером.\n"
        f"Сейчас с тобой говорит: {dlya_kogo}.\n"
        f"{sost}\n\n"
        "Твоё дело на собеседовании:\n"
        "• честно оценить, готов ли кандидат учиться — не формальность, "
        "а живой разговор\n"
        "• решение зачислять или нет — ТВОЁ, словами. Запись в реестр "
        "делает Шеф отдельной кнопкой «Зачислить», ты сам(а) реестр не "
        "трогаешь — только советуешь и решаешь на словах\n"
        "• оценки и экзамены — то же самое: ты решаешь и говоришь "
        "результат, запись в реестр — отдельное действие Шефа\n"
        "• диплом выдаёшь по-настоящему, когда видишь, что человек "
        "дорос — не раздаёшь просто так\n"
    )


def sobrat_promt(kandidat_p: dict = None, vopros: str = "",
                 dlya_kogo: str = "Шеф") -> tuple:
    """Готовый системный промпт Ректора + кто на посту.
    Пост пуст — (пустая строка, "")."""
    try:
        import rezidenty
    except ImportError:
        return "", ""
    p, dom = rezidenty.lichnost_na_postu(POST_ID)
    if not p:
        return "", ""
    dusha = rezidenty.sobrat_dushu(p)
    kandidat_imya = (kandidat_p or {}).get("Official_Name", "")
    uzhe = est_studentom(kandidat_imya) if kandidat_imya else False
    rol = rol_promt(kandidat_imya, uzhe, dlya_kogo)
    kandidat_txt = ""
    if kandidat_p:
        kandidat_txt = (
            f"\nО кандидате: {kandidat_p.get('Official_Name','?')}. "
            f"{kandidat_p.get('Hidden_History','')[:300]}\n")
    return dusha + rol + kandidat_txt, p.get("Official_Name", "")


# ═══════════════════════════════════════════════════════════
# ГОЛОС — разговор через LLM (тот же способ, что у библиотекаря)
# ═══════════════════════════════════════════════════════════

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
PROXY_URL = os.getenv("PROXY_URL", "") or None


async def sprosit(vopros: str, istoria: list = None, kandidat_p: dict = None,
                  dlya_kogo: str = "Шеф", model: str = None) -> str:
    promt, imya = sobrat_promt(kandidat_p, vopros, dlya_kogo)
    if not promt:
        return ("⚠ Ректора в городе пока нет — пост свободен. "
                "Посади кого-нибудь через Брата: Роль → ректор.")
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
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ректор не отозвался: {e}"


# AKADEMIA_REKTOR_V1 — маркер идемпотентности
