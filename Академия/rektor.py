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

# PATCH_REKTOR_DISTSIPLINY_V1: направления вместо одного "курса".
# Список открыт -- четвёртое направление родится той же папкой на
# диске, код его не хардкодит нигде, кроме этого стартового списка
# (три полки, которые Шеф назвал 27.07).
_DISTSIPLINY_DIR = _DATA / "дисциплины"
NAPRAVLENIA = ["финансы", "искусство", "общие_дисциплины"]
CHASTI_DISTSIPLINY = ("теория", "практика")


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
    # VYPUSK_V1: выпускник поступает снова как все — место он больше
    # не занимает. Считаем, какая это по счёту учёба, чтобы Ректор
    # видел человека целиком, а не с чистого листа.
    _proshlye = diplomy(imya)
    mesto = svobodnoe_mesto()
    if mesto is None:
        return False, f"мест нет — все {MEST} заняты"
    zapisi = _zapisi()
    zapisi.append({
        "место": mesto, "житель": imya, "курс": kurs,
        # PATCH_REKTOR_DISTSIPLINY_V1: "курс" оставлен для обратной
        # совместимости (ui_akademia.py его читает), но новый багаж --
        # список дисциплин, не одна строка. Несколько дисциплин разом.
        "дисциплины": [],
        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
        "учёба_по_счёту": len(_proshlye) + 1,          # VYPUSK_V1
        "прошлые_дипломы": [d.get("диплом", {}).get("профессия", "")
                            for d in _proshlye],
    })
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Поступил(а) в Академию Грондхейма (Замок Сов)",
        "Я учусь в Академии Грондхейма", pattern=None, sila=0.6)
    if _proshlye:
        _bylo = ", ".join(x for x in
                          (d.get("диплом", {}).get("профессия", "")
                           for d in _proshlye) if x)
        return True, (f"{imya} зачислен(а) на место {mesto} · "
                      f"учёба {len(_proshlye) + 1}-я, уже есть диплом: "
                      f"{_bylo or 'без профессии'}")
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


# ── VYPUSK_V1: выпускники и повторное поступление ────────────
VYPUSKNIKI = _UCHENIKI.parent / "выпускники.json"


def vypuskniki() -> list:
    """Все, кого Академия выпустила. Парт не занимают."""
    return (_read_json(VYPUSKNIKI, {"выпуски": []}) or {}).get("выпуски", [])


def diplomy(imya: str) -> list:
    """Дипломы этого человека — сколько раз учился и на кого выучился."""
    return [v for v in vypuskniki() if v.get("житель") == imya]


def _zapisat_vypusk(zapis: dict):
    d = _read_json(VYPUSKNIKI, {"выпуски": []}) or {"выпуски": []}
    d.setdefault("выпуски", []).append(zapis)
    _write_json(VYPUSKNIKI, d)


def _otmetit_diplom_v_pasporte(imya: str, professiya: str) -> bool:
    """Диплом — то, что человек НОСИТ С СОБОЙ. В реестре парт ему не
    место: парта про то, кто учится сейчас."""
    try:
        import sys as _s
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in _s.path:
            _s.path.insert(0, str(_repo))
        import rabota as _r
    except Exception:
        try:
            import sys as _s
            _repo = Path(__file__).resolve().parent.parent
            _g = str(_repo / "ГОРОД")
            if _g not in _s.path:
                _s.path.insert(0, _g)
            import rabota as _r
        except Exception:
            return False
    dom = _r.dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _read_json(pp)
    if p is None:
        return False
    spisok = p.get("Дипломы") or []
    spisok.append({"профессия": professiya or "специалист",
                   "выдан": _now(), "кем": "Академия Грондхейма"})
    p["Дипломы"] = spisok
    return bool(_write_json(pp, p))


def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    """VYPUSK_V1: диплом — это ВЫПУСК, а не отметка поверх парты.

    Раньше здесь ставился статус «выпускник», и место оставалось за
    человеком навсегда: Академия забивалась теми, кто давно отучился,
    и зачислить нового было некуда. Теперь место освобождается, а
    запись со всей историей учёбы уезжает в выпускники.
    """
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            z["выпущен"] = _now()
            _zapisat_vypusk(dict(z))
            _otmetit_diplom_v_pasporte(imya, professiya)
            zapisi = [x for x in zapisi if x.get("житель") != imya]
            _sokhranit_zapisi(zapisi)
            _prof = professiya or "специалист(ка)"
            _zapomnit_uchebu(
                imya, f"Получил(а) диплом Академии по специальности «{_prof}»",
                f"Я — дипломированный(ая) {_prof}, умею применять эти "
                f"знания в работе, не только помнить их как урок",
                pattern=None, sila=0.9)
            _mesto = z.get("место")
            return True, (f"диплом «{professiya or 'без указания профессии'}» "
                          f"выдан {imya} · место {_mesto} свободно · "
                          f"запись ушла в выпускники")
    return False, f"{imya} не студент(ка) — диплом выдавать некому"


# ═══════════════════════════════════════════════════════════
# ДИСЦИПЛИНЫ (PATCH_REKTOR_DISTSIPLINY_V1) -- направления, теория и
# практика раздельно, несколько дисциплин разом. АКАДЕМИЯ_ГРОНДХЕЙМА.md
# §12: дисциплина -- книга на полке направления, студент не выбирает
# одну и ждёт диплома, а записывается на сколько угодно сразу.
# ═══════════════════════════════════════════════════════════

def list_napravlenia() -> list:
    """Три полки, заведённые Шефом 27.07. Список открыт на будущее --
    новое направление появится той же папкой, здесь просто стартовые."""
    return list(NAPRAVLENIA)


def list_distsipliny(napravlenie: str = "") -> list:
    """Дисциплины на диске. Пусто направление -- по всем сразу. Честно:
    ни одной дисциплины ещё нет, пока вернёт пустой список -- не
    выдумываем то, чего на диске нет."""
    out = []
    if not _DISTSIPLINY_DIR.exists():
        return out
    papki = ([_DISTSIPLINY_DIR / napravlenie] if napravlenie
             else [_DISTSIPLINY_DIR / n for n in NAPRAVLENIA])
    for napr_dir in papki:
        if not napr_dir.exists():
            continue
        for d in sorted(napr_dir.iterdir()):
            if not d.is_dir():
                continue
            man = _read_json(d / "manifest.json")
            if man:
                out.append(man)
    return out


def _najti_mesto(imya: str):
    """Индекс места студента в списке или None. Внутренний помощник --
    дисциплины живут внутри записи места, не отдельным реестром."""
    zapisi = _zapisi()
    for i, z in enumerate(zapisi):
        if z.get("житель") == imya:
            return zapisi, i
    return zapisi, None


def zapisat_na_distsiplinu(imya: str, distsiplina_id: str,
                          napravlenie: str) -> tuple:
    """Записывает студента на дисциплину. НЕ блокирует, если он уже
    учит другие -- несколько дисциплин разом это норма (§12), не
    исключение. Повторная запись на ТУ ЖЕ дисциплину -- честный отказ,
    не дублируем строку."""
    zapisi, idx = _najti_mesto(imya)
    if idx is None:
        return False, f"{imya} не студент(ка) — сперва зачислить в Академию"
    z = zapisi[idx]
    distsipliny = z.setdefault("дисциплины", [])
    if any(d.get("дисциплина") == distsiplina_id for d in distsipliny):
        return False, f"{imya} уже записан(а) на «{distsiplina_id}»"
    distsipliny.append({
        "дисциплина": distsiplina_id,
        "направление": napravlenie,
        "записан": _now(),
        "теория": {"оценки": []},
        "практика": {"оценки": []},
    })
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Начал(а) изучать «{distsiplina_id}» ({napravlenie})",
        f"Я изучаю «{distsiplina_id}»", pattern=None, sila=0.4)
    return True, f"{imya} записан(а) на «{distsiplina_id}» ({napravlenie})"


def postavit_otsenku_distsipliny(imya: str, distsiplina_id: str,
                                 chast: str, otsenka: str) -> tuple:
    """Оценка ЗА ЧАСТЬ дисциплины -- теория и практика раздельно
    (§12), не смешиваются в один список, как было у postavit_otsenku()
    для курса целиком. Каждая часть -- свой ключ в личной памяти
    студента (dopisat_vyvod), свой порог 3, друг другу не мешают."""
    if chast not in CHASTI_DISTSIPLINY:
        return False, f"часть должна быть 'теория' или 'практика', не «{chast}»"
    zapisi, idx = _najti_mesto(imya)
    if idx is None:
        return False, f"{imya} не студент(ка) — оценку ставить некуда"
    z = zapisi[idx]
    distsipliny = z.get("дисциплины", [])
    d = next((d for d in distsipliny if d.get("дисциплина") == distsiplina_id), None)
    if d is None:
        return False, f"{imya} не записан(а) на «{distsiplina_id}»"
    d.setdefault(chast, {"оценки": []}).setdefault("оценки", []).append({
        "оценка": otsenka, "когда": _now()})
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Оценка по «{distsiplina_id}» ({chast}): {otsenka}",
        f"По «{distsiplina_id}» ({chast}): {otsenka}",
        pattern=f"{distsiplina_id}:{chast}", sila=0.5)
    return True, f"оценка «{otsenka}» ({chast}, «{distsiplina_id}») выставлена {imya}"


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
            _otvet = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ректор не отозвался: {e}"

    # PATCH_PAMYAT_VEZDE_V1: разговор на посту -- отпечаток в личной
    # памяти того, кто сейчас сидит Ректором.
    try:
        import rezidenty as _rez_pm
        _dom_pm = _rez_pm.dom_zhitelya(imya)
        if _dom_pm:
            from dvizhok import Dvizhok as _Dvizhok_pm
            _dv_pm = _Dvizhok_pm(_dom_pm)
            _vdoh_pm = _dv_pm.vdoh(kontekst="работа", sila=0.5, svezhest=1.0, tonus="ровно")
            _dv_pm.vydoh_stol(
                fakt=f"[Ректорская] {dlya_kogo} спросил(а): {vopros}\nЯ ответил(а): {_otvet}",
                vdoh_result=_vdoh_pm)
            _dv_pm.sохранить()
    except Exception:
        pass
    return _otvet


# AKADEMIA_REKTOR_V1 — маркер идемпотентности

# VYPUSK_V1 - marker
