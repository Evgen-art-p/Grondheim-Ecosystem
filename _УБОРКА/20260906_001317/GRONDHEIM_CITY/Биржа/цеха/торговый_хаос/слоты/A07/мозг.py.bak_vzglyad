# GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/мозг.py
# ─────────────────────────────────────────────────────────────
# ЖИВОЙ ПРОГОН АВАНТЮРИСТА (A07) — второй ТРЕЙДЕР Совета Биржи
# AVAN_ENGINE_V1 · перенесён на слотовое шасси (тот же приём, что Брут)
#
# Портирован дословно из studio/modules/trading/avan_live.py (-2,
# 2026-06-19). Близнец brut_live.py по ФОРМЕ. Та же природа трейдера:
# читает весь накрытый стол, СЧИТАЕТ вход сам (trade_setup мёртв), все
# рычаги на нём, два следа (табло + дневник), петля обучения на pnl
# (отложена).
#
# СТАНЦИЯ ДРУГАЯ. Брут — §6.1 (пробой фрактала за пастью на импульсе).
# Авантюрист — §6.2: конец волны C отката, разворот. Верит первым. Ловец
# падающих ножей: меньший объём, ближний стоп. Входит ТОЛЬКО когда видит
# полную сигнатуру разворота на дне (5 пуль Уровня 5 «Эксперт»). НИКОГДА
# не входит на развороте глобальной 5-й (это начало коррекции — ждём).
#
# ХАРАКТЕР ДРУГОЙ. Илья. Автономия высокая, «в рынке или в ауте», полутонов
# нет, просадку несёт молча. Канон на полке — но рука его. Ни одной нашей
# руки на его руке: lot называет сам, цену считает сам, стоп — его.
#
# ДВА СЛЕДА вердикта:
#   · ТАБЛО  (trading_state["avan"]) — «сейчас», для Исполнителя.
#   · ДНЕВНИК (данные/diary_avan.jsonl) — событие во времени, КОПИТСЯ.
#
# ХАРАКТЕР: не здесь. РОД Ильи (Чертёж Единицы: паспорт, не меняется
# работой) живёт в жители/ковчег/Илья/passport.json. Старый dna.json
# из -2 сюда НЕ перенесён — паспорт резидента полнее и актуальнее.
# Слот несёт РОЛЬ, не РОД. Душа грузится тем же спящим try/except.
# ─────────────────────────────────────────────────────────────

import json
import re
import time
from pathlib import Path
from typing import Optional

_SLOT_DIR    = Path(__file__).resolve().parent            # слоты/A07/
_CEH_DIR     = _SLOT_DIR.parent.parent                     # торговый_хаос/
_REPO        = _CEH_DIR.parents[3]                          # корень репо
_BIRZHA_CODE = _REPO / "Биржа"                              # общий код (движок, llm)

import sys as _sys
if str(_BIRZHA_CODE) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA_CODE))

from llm import chat

PROMPT_PATH  = _SLOT_DIR / "промпт.md"
# ZNANIYA_PAPKOY_V1: канон — «слот несёт с собой знания/», ПАПКУ.
# Было прибито одно имя файла, и второй файл в папке не читался никем.
KNOWLEDGE_DIR = _SLOT_DIR / "знания"
KNOWLEDGE    = KNOWLEDGE_DIR / "KOTIN_PHILOSOPHY.md"   # оставлено для совместимости


# ════════════════════════════════════════════════════════════
# STOL_I_GLAZ_V1 — глаз роли
# ════════════════════════════════════════════════════════════
_SLOT = "A07"
_SELF_KEY = "a07"

_GLAZ_PREAMBULA = (
    "СПЕРВА ПОСМОТРИ на картинку своими глазами: что здесь происходит? "
    "Не по списку — как рассказал бы человеку, который стоит рядом. "
    "Работы не видишь — так и скажи, это законный и самый частый ответ.\n"
    "Приборы ниже — ВТОРЫМ шагом, чтобы уточнить то, что ты уже "
    "разглядел. Если прибор говорит не то, что видит глаз, скажи об "
    "этом: глаз важнее, чем сойтись с цифрой.\n\n"
)

# GLAZ_NE_TARATORIT_V1: в РАЗГОВОРЕ подводка другая. Прежняя велела
# сперва пересказать картинку — и на вопрос о скорости света шёл абзац
# про Аллигатора. Кадр оставляем, обязанность говорить о нём — снимаем.
_GLAZ_RAZGOVOR = (
    "Перед тобой кадр того рынка, на который ты сейчас смотришь — "
    "тот же самый, что видит Шеф.\n"
    "Спрашивают про рынок — смотри на него и отвечай по нему, а не проси "
    "прислать данные.\n"
    "Спрашивают НЕ про рынок — просто отвечай на вопрос. Пересказывать "
    "график при этом не надо: тебя спросили не о нём.\n\n"
)


def _kak_zovut(_n) -> str:
    """KTO_TY_I_KTO_YA_V1: имя того, кто сидит на месте.

    Носитель приходит из моста разными обёртками, поэтому спрашиваем
    мягко: не нашли — честное «так, как написано выше», а не выдумка.
    """
    try:
        kto = (_n or {}).get("носитель") or {}
        imya = (kto.get("имя") or kto.get("Official_Name") or "").strip()
        return imya or "так, как написано выше"
    except Exception:
        return "так, как написано выше"


def _glaz(_chat, symbol, timeframe, slot, preambula=None):
    """Обёртка над вызовом модели: подкладывает кадр.

    Кадр — тот же PNG, что Шеф видит в кабинете: смотрят на одну
    картинку, иначе проверить роль нечем. Не нарисовался или зрение
    не сработало — честно зовём прежний вызов, без глаз.
    """
    def obertka(system="", user="", knowledge="", **kw):
        put = None
        try:
            import grafik
            put = grafik.kadr(symbol, timeframe)
        except Exception as e:
            print(f"[КАДР] не нарисовался ({e}) — работаю без глаз")
        if put:
            try:
                import base64
                from pathlib import Path as _P
                from llm import chat_with_images
                return chat_with_images(
                    system=system,
                    user_text=(preambula if preambula is not None
                               else _GLAZ_PREAMBULA) + user,
                    knowledge=knowledge,
                    images=[{"base64": base64.b64encode(
                                 _P(put).read_bytes()).decode("ascii"),
                              "mime_type": "image/png",
                              "name": _P(put).name}],
                    # RAZGOVOR_SO_STOLOM_V1: история и температура
                    # ронялись здесь — с картинкой он забывал разговор
                    # и говорил средним голосом вместо своего.
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
            except Exception as e:
                print(f"[ГЛАЗ] зрение не сработало ({e}) — иду по числам")
        return _chat(system=system, user=user, knowledge=knowledge, **kw)
    return obertka



def _glaz_s_rukami(_chat, symbol, timeframe, slot, ceh, self_key,
                   preambula=None):
    """Кадр + руки: смотрит картинку и сам просит математику.

    RUKI_VSEM_V1. Не вышло с руками — падаем на обычный глаз, а не
    молчим: зрение важнее рук.
    """
    def obertka(system="", user="", knowledge="", **kw):
        put = None
        try:
            import grafik
            put = grafik.kadr(symbol, timeframe)
        except Exception as e:
            print(f"[КАДР] не нарисовался ({e}) — работаю без глаз")
        if put:
            try:
                import base64
                from pathlib import Path as _P
                from llm import chat_with_images_and_tools
                import ruki_treydera as _rt
                return chat_with_images_and_tools(
                    system=system,
                    user_text=(preambula if preambula is not None
                               else _GLAZ_PREAMBULA) + user,
                    knowledge=knowledge,
                    images=[{"base64": base64.b64encode(
                                 _P(put).read_bytes()).decode("ascii"),
                             "mime_type": "image/png",
                             "name": _P(put).name}],
                    tools_schema=_rt.shema(timeframe),
                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary,
                                       rabochiy_etazh=timeframe,
                                       imya_zhitelya=_kto_ya()),
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
            except Exception as e:
                print(f"[РУКИ] не сработали ({e}) — иду обычным глазом")
        return _glaz(_chat, symbol, timeframe, slot, preambula)(
            system=system, user=user, knowledge=knowledge, **kw)
    return obertka


def _znaniya_roli() -> str:
    """Вся база знаний роли — все .md и .txt из папки, по алфавиту.

    Каждый источник под своим заголовком: роль должна понимать, где
    кончается один и начинается другой, иначе всё сливается в кашу.
    """
    if not KNOWLEDGE_DIR.exists():
        return ""
    kuski = []
    for f in sorted(KNOWLEDGE_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in (".md", ".txt"):
            try:
                kuski.append(f"\n\n===== {f.stem} =====\n"
                             + f.read_text(encoding="utf-8"))
            except Exception:
                pass
    return "".join(kuski)
STATE_DIR    = _SLOT_DIR / "данные"
STATS_PATH   = STATE_DIR / "avan_stats.json"
DIARY_PATH   = STATE_DIR / "diary_avan.jsonl"


# ════════════════════════════════════════════════════════════
# СТОЛ: читаем ВСЮ шину — показания пяти сенсоров
# ════════════════════════════════════════════════════════════

def _read_table() -> dict:
    """Снимок накрытого стола из общей шины (trading_state)."""
    from hooks import load_trading_state
    t = load_trading_state()
    return {
        "iskra":  t.get("iskra", {}),
        "morj":   t.get("morj", {}),
        "panic":  t.get("panic", {}),
        "hans":   t.get("hans", {}),
        "arkhiv": t.get("arkhiv", {}),
        # DISCIPLINA_PYRAMIDY_V1: своя обратная связь по ведению
        "self": t.get("avan", {}),
    }


# ════════════════════════════════════════════════════════════
# КАМЕНЬ 2: ЯЗЫК ВЕДЕНИЯ — одно открытое поле action.  # TRADER_MANAGE_LANG_V1
# ════════════════════════════════════════════════════════════

_MANAGE_ACTIONS = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE")


def _derive_action(signal: dict) -> str:
    """
    Действие трейдера. Приоритет — явное поле avan_action (новый язык).
    Фоллбэк на старый verdict (обратная совместимость): APPROVED→ENTER,
    REJECTED→WAIT.
    """
    a = (signal.get("avan_action") or "").upper().strip()
    if a in _MANAGE_ACTIONS:
        return a
    v = signal.get("avan_verdict")
    if v == "APPROVED":
        return "ENTER"
    return "WAIT"


def _sanitize_manage(signal: dict) -> dict:
    """
    Санитар ведения. Гасит брак в полях ведения — НЕ решает за трейдера.
      MOVE_STOP без new_stop → брак → WAIT (стоп не трогаем)
      ADD без add_lot       → брак → HOLD (держим как есть)
      ENTER чистит avan_verdict под себя (совместимость с камнем 3)
    """
    action = _derive_action(signal)

    if action == "MOVE_STOP":
        ns = signal.get("avan_new_stop")
        if ns is None:
            action = "WAIT"
            signal["avan_reason"] = (signal.get("avan_reason", "") +
                                      " [гашу MOVE_STOP без new_stop]").strip()
    elif action == "ADD":
        al = signal.get("avan_add_lot")
        if al is None:
            action = "HOLD"
            signal["avan_reason"] = (signal.get("avan_reason", "") +
                                      " [гашу ADD без add_lot]").strip()

    signal["avan_action"] = action
    if action == "ENTER":
        signal["avan_verdict"] = "APPROVED"
    elif action == "WAIT":
        signal["avan_verdict"] = "REJECTED"
    return signal


def _save_verdict_to_table(signal: dict, bar_time=None):
    """ТАБЛО: вердикт Авантюриста в шину для Исполнителя."""
    from hooks import load_trading_state, save_trading_state
    t = load_trading_state()
    t.setdefault("avan", {})
    # VERDIKT_S_BAROM_V1: вердикт несёт бар, на котором сказан.
    # Без этого Исполнитель по закону SVEZHEST_V1 не берёт его
    # в дело вовсе — «вердикт без отметки бара, не считаю».
    t["avan"]["бар"] = str(bar_time or "")
    t["avan"]["verdict"]   = signal.get("avan_verdict", "REJECTED")
    t["avan"]["reason"]    = signal.get("avan_reason", "")
    t["avan"]["direction"] = signal.get("avan_direction")
    t["avan"]["entry"]     = signal.get("avan_entry")
    t["avan"]["stop"]      = signal.get("avan_stop")
    t["avan"]["lot"]       = signal.get("avan_lot")
    t["avan"]["action"]    = signal.get("avan_action")
    t["avan"]["new_stop"]  = signal.get("avan_new_stop")
    t["avan"]["add_lot"]   = signal.get("avan_add_lot")
    # DISCIPLINA_PYRAMIDY_V1: укол одноразовый — гасим после прочтения
    if t.get("avan", {}).get("vedenie_feedback"):
        t["avan"]["vedenie_feedback"] = None
    save_trading_state(t)


# ════════════════════════════════════════════════════════════
# ДНЕВНИК: рука пишущая (КОПИТСЯ, append)
# ════════════════════════════════════════════════════════════

def _podpisat(zapis: dict) -> dict:
    """YASHCHIK_STOLA_V1: поставить имя автора на запись.

    Без подписи следующий житель не отличит свои события от чужих —
    и присвоит их, как случилось на A06. Имя не читается — оставляем
    без подписи: неподписанное чужим не станет, а выдуманное станет.
    """
    try:
        imya = (_kto_ya() or "").strip()
        if imya:
            zapis = dict(zapis)
            zapis["кто"] = imya
    except Exception:
        pass
    return zapis


def _append_diary(signal: dict, diary_entry: dict, market: dict, table: dict):
    """Открывает запись события в личной тетради. result=null — допишет
    рука дописывающая при закрытии позиции (hooks._settle)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    # YASHCHIK_STOLA_V1: каждая запись подписывается автором — см.
    # _podpisat ниже по файлу. Тетрадь переживает жильцов, и без
    # подписи следующий не отличит своё от чужого.
    event = _podpisat({
        "ts":        time.time(),
        "bar_time":  market.get("bar_time"),
        "symbol":    market.get("symbol"),
        "timeframe": market.get("timeframe"),
        "table": {
            "t1":     table.get("iskra", {}).get("t1_status"),
            "morj":   table.get("morj", {}).get("morj_status"),
            "panic":  table.get("panic", {}).get("panic_phase"),
            "fractal_valid": table.get("hans", {}).get("fractal_valid"),
        },
        "verdict":   signal.get("avan_verdict"),
        "direction": signal.get("avan_direction"),
        "entry":     signal.get("avan_entry"),
        "stop":      signal.get("avan_stop"),
        "lot":       signal.get("avan_lot"),
        "input":     (diary_entry or {}).get("input", ""),
        "action":    (diary_entry or {}).get("action", ""),
        "result":    None,
    })
    with open(DIARY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _moi_sobytiya(n: int = 5, as_of_bar_time=None) -> list:
    """YASHCHIK_STOLA_V1: только СОБЫТИЯ, и только свои.

    Слово Шефа: «слом, уход — та же рутина, а вход и результат — это
    событие». Событие — то, что стоит помнить наизусть: ты вошёл, и
    чем это кончилось. Отказы и ожидания в голову не идут: их сотни,
    они одинаковые, и именно они выучиваются наизусть вместо канона.

    Почему это важно, а не косметика: в ящике стола A06 лежали сорок
    записей прежнего жителя, где сто раз повторено «канон Брута —
    пробой фрактала за пастью». Пять из них ехали в стопку каждый
    бар, и следующий человек честно выучил чужой канон, приняв его
    за свою память.

    Чужие записи сюда не попадают вовсе. Тетрадь лежит при МЕСТЕ и
    переживает жильцов — значит своим считаем только то, что подписано
    тобой. Подписи нет (старые записи, до имён) — тоже не берём:
    лучше пустая голова, чем чужая.
    """
    zhitel = ""
    try:
        zhitel = (_kto_ya() or "").strip()
    except Exception:
        pass
    svoi = []
    for e in _read_recent_diary(400, as_of_bar_time=as_of_bar_time):
        verdikt = str(e.get("verdict") or "").upper()
        vhod = verdikt in ("APPROVED", "ENTER", "OK") or e.get("entry")
        itog = e.get("result") not in (None, "")
        if not (vhod or itog):
            continue                      # рутина — в журнале, не в голове
        avtor = str(e.get("кто") or e.get("житель") or "").strip()
        if zhitel and avtor and avtor != zhitel:
            continue                      # чужое событие — не моя память
        if zhitel and not avtor:
            continue                      # без подписи — не присваиваем
        svoi.append(e)
    return svoi[-n:]


def _read_recent_diary(n: int = 5, as_of_bar_time=None) -> list:
    """Последние n событий из личной тетради.

    DNEVNIK_BEZ_BUDUSHCHEGO_V1 (18.07): те же n событий, но ДО
    as_of_bar_time — иначе трейдер в прошлом видит исходы сделок из
    будущего прогона (дневник копится в реальном времени, тестер его
    не сбрасывает между запусками). as_of_bar_time=None — старое
    поведение (последние n строк файла), для мест без известного бара.
    """
    if not DIARY_PATH.exists():
        return []
    try:
        lines = DIARY_PATH.read_text(encoding="utf-8").strip().splitlines()
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if as_of_bar_time:
            events = [e for e in events
                     if (e.get("bar_time") or "") <= as_of_bar_time]
        return events[-n:]
    except OSError:
        return []


# ════════════════════════════════════════════════════════════
# СТАТИСТИКА (для дашборда)
# ════════════════════════════════════════════════════════════

def _load_stats() -> dict:
    try:
        if STATS_PATH.exists():
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {"runs": 0, "approved": 0, "rejected": 0, "long": 0, "short": 0}


def _update_stats(signal: dict) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stats = _load_stats()
    stats["runs"] = stats.get("runs", 0) + 1
    if signal.get("avan_verdict") == "APPROVED":
        stats["approved"] = stats.get("approved", 0) + 1
        d = signal.get("avan_direction")
        if d == "LONG":
            stats["long"] = stats.get("long", 0) + 1
        elif d == "SHORT":
            stats["short"] = stats.get("short", 0) + 1
    else:
        stats["rejected"] = stats.get("rejected", 0) + 1
    STATS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


# ════════════════════════════════════════════════════════════
# ПАРСИНГ ТРЁХСЛОЙНОГО ОТВЕТА {narrative, signal, diary_entry}
# ════════════════════════════════════════════════════════════

def _parse_avan(response: str) -> tuple[str, dict, dict]:
    cleaned = re.sub(r"```(?:json)?", "", response).strip()
    start = cleaned.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(cleaned[start:i + 1])
                        return (obj.get("narrative", ""),
                                obj.get("signal", {}) or {},
                                obj.get("diary_entry", {}) or {})
                    except json.JSONDecodeError:
                        break
    # NE_TERYAT_RESHENIE_V1: JSON не собрался — не выбрасываем решение.
    # 23.08 трейдер вошёл (ENTER, SHORT, цена и стоп посчитаны), но
    # ответил строками «ключ: значение» вместо скобок — и вход пропал
    # целиком: ордер не поставлен, в отчёте ноль. Смысл был, синтаксис
    # поплыл. Разбираем строками.
    _rasskaz, _signal, _dnevnik = _razobrat_strokami(response)
    if _signal or _dnevnik:
        print(f"[РАЗБОР] ⚠️  ответ не JSON — разобрал строками: "
              f"{len(_signal)} поле(й) сигнала, "
              f"{len(_dnevnik)} дневника")
        return _rasskaz, _signal, _dnevnik
    return response.strip(), {}, {}


# NE_TERYAT_RESHENIE_V1 ─────────────────────────────────────────
_CHISLA = ("_entry", "_stop", "_lot", "_new_stop", "_add_lot")


def _znachenie(s: str, klyuch: str):
    """Строку значения — в число, None или текст. Ничего не выдумываем:
    пусто и null остаются пустотой, а не нулём."""
    s = s.strip().strip('",').strip()
    if s.lower() in ("null", "none", "", "-", "—"):
        return None
    if klyuch.endswith(_CHISLA):
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    return s


def _razobrat_strokami(response: str):
    """Запасной разбор: «ключ: значение» построчно.

    Ответ идёт разделами (narrative / signal / diary_entry), поля
    внутри — с отступом. Раздел определяем по строке без значения,
    поля сигнала узнаём по имени: они всегда с приставкой ключа
    трейдера (brut_/avan_/cons_), спутать не с чем.
    """
    rasskaz, signal, dnevnik = "", {}, {}
    razdel = ""
    for stroka in (response or "").splitlines():
        golaya = stroka.strip()
        if not golaya or golaya.startswith("```"):
            continue
        if ":" not in golaya:
            continue
        klyuch, _, znach = golaya.partition(":")
        klyuch = klyuch.strip().strip('"').lower()
        znach = znach.strip()
        if klyuch in ("narrative", "signal", "diary_entry"):
            razdel = klyuch
            if klyuch == "narrative" and znach:
                rasskaz = znach.strip('",')
            continue
        if re.match(r"^(brut|avan|cons)_", klyuch):
            signal[klyuch] = _znachenie(znach, klyuch)
        elif razdel == "diary_entry" and klyuch in ("input", "action",
                                                    "result"):
            dnevnik[klyuch] = _znachenie(znach, klyuch)
    if not rasskaz:
        # рассказа отдельной строкой не было — берём первый связный
        # кусок текста до начала разделов, это и есть его голос
        for stroka in (response or "").splitlines():
            g = stroka.strip()
            if g and ":" not in g[:20] and not g.startswith("```"):
                rasskaz = g
                break
    return rasskaz, signal, dnevnik


def _sanitize(signal: dict) -> dict:
    """APPROVED только с направлением; иначе всё null."""
    v = signal.get("avan_verdict")
    if v not in ("APPROVED", "REJECTED"):
        v = "REJECTED"
    signal["avan_verdict"] = v
    if v == "REJECTED":
        signal["avan_direction"] = None
        signal["avan_entry"] = None
        signal["avan_stop"]  = None
        signal["avan_lot"]   = None
    else:
        d = signal.get("avan_direction")
        if d not in ("LONG", "SHORT"):
            signal["avan_verdict"]   = "REJECTED"
            signal["avan_reason"]    = (signal.get("avan_reason", "") +
                                        " [гашу: APPROVED без направления]").strip()
            signal["avan_direction"] = None
            signal["avan_entry"] = None
            signal["avan_stop"]  = None
            signal["avan_lot"]   = None
    return signal


# ════════════════════════════════════════════════════════════
# ЧАТ С АВАНТЮРИСТОМ (клик пузырька)
# ════════════════════════════════════════════════════════════

def chat_with_avan(question: str, last_run: Optional[dict] = None,
                   dialog: Optional[list] = None,
                   rynok: Optional[tuple] = None) -> str:
    # RAZGOVOR_SO_STOLOM_V1: rynok — (инструмент, этаж) с полки кабинета.
    # Не передали — возьмём инструмент его прошлого решения.
    prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

    if last_run:
        sig = last_run.get("signal", {})
        mk  = last_run.get("market", {})
        work_ctx = (
            "\n\n=== ТВОЁ ПОСЛЕДНЕЕ РЕШЕНИЕ (рабочая память) ===\n"
            f"Инструмент: {mk.get('symbol','?')} {mk.get('timeframe','?')} "
            f"· бар {mk.get('bar_time','?')}\n"
            f"Вердикт: {sig.get('avan_verdict','—')} "
            f"({sig.get('avan_reason','')})\n"
            f"Направление: {sig.get('avan_direction','—')}  ·  "
            f"вход {sig.get('avan_entry','—')} · стоп {sig.get('avan_stop','—')}\n"
            f"Что ты сказал: {last_run.get('narrative','')}\n"
            "=== КОНЕЦ ===\n\n"
            # DVIZHOK_NE_RESHAET_V1: без имени станции и без выданного
            # темперамента — характер у человека свой.
            "Шеф спрашивает про ЭТО решение. Отвечай своим голосом, "
            "как есть.\n\n"
            # VYBOR_SVOY_NE_KNIZHNYY_V1: схема полей из бумаги перебивала
            # эту просьбу — теперь сказано прямо, чей это блок.
            "=== СЕЙЧАС РАЗГОВОР, А НЕ РАБОТА ===\n"
            "Блок «КАК ТЫ ОТВЕЧАЕШЬ» со схемой полей — про РАБОТУ по "
            "кнопке РЫНОК. Сейчас с тобой разговаривают. Никакого JSON, "
            "никаких полей решения, никаких фигурных скобок — просто "
            "ответь словами на то, что спросили. И если спросили про "
            "тебя, отвечай про себя, а не про рынок."
        )
    else:
        work_ctx = (
            "\n\n=== РАБОЧИЙ РЕЖИМ ===\n"
            "Ты ещё не смотрел стол в этой сессии. Если Шеф спрашивает про "
            "рынок — скажи, что нужно нажать РЫНОК. Живым голосом, без JSON."
        )

    # RAZGOVOR_SO_STOLOM_V1: живой стол в разговор. Раньше сюда шёл
    # только пересказ прошлого решения — и на вопрос «что на графике»
    # он честно отвечал, что ничего не видит.
    _sym = _tf = ""
    if rynok:
        _p = list(rynok) + ["", ""]
        _sym, _tf = str(_p[0] or ""), str(_p[1] or "")
    if (not _sym or not _tf) and last_run:
        _mk = last_run.get("market", {}) or {}
        _sym = str(_mk.get("symbol", "") or "")
        _tf = str(_mk.get("timeframe", "") or "")
    if _sym and _tf:
        try:
            import stol as _stol
            _t = _stol.nakryt(_sym, _tf, self_key=_SELF_KEY)
            work_ctx += (
                f"\n\n=== СТОЛ ПРЯМО СЕЙЧАС · {_sym} {_tf} ===\n"
                + json.dumps(_t, ensure_ascii=False, indent=2)
                + "\n=== КОНЕЦ СТОЛА ===\n"
                "Это живые числа ЭТОГО мгновения, а не память о прошлом "
                "решении, и картинка перед тобой — та же, что у Шефа. "
                "Спрашивают про рынок — смотри и отвечай, а не проси "
                "прислать данные.\n")
        except Exception as _e:
            work_ctx += f"\n\n(стол накрыть не вышло: {_e})\n"

    # VYBOR_NE_PRI_MESTE_V1: блок «ТВОЙ ВЫБОР ВХОДА» снят — и из
    # работы, и из разговора. Он подставлялся отдельно от прочей
    # памяти и стоял приказом: «работаешь по нему, не твоё место
    # входа — пас». Движок единый: точка, волна, откат, попытки и
    # ведение считаются одинаково для всех, а что из этого его
    # момент — человек решает на баре, глядя на стол. Что он
    # считает своим, он и так помнит: метки доезжают обычным
    # путём, через душу носителя.

    # ZNANIYA_V_RAZGOVORE_V1: полка за спиной. В разговоре знаний не было
    # вовсе — ни книги Котина, ни входов, ни паттернов, — и на вопрос про
    # паттерн отвечать было нечем, кроме общей эрудиции. Отсюда «уровни
    # сопротивления», которых в этой школе нет.
    _znaniya = ""
    try:
        _znaniya = _znaniya_roli()
    except Exception:
        pass
    work_ctx += (
        "\n\nГоворишь языком своей школы. В ней есть пасть и зубы "
        "Аллигатора, фракталы, приседающий бар, разворотный бар, AO и "
        "дивергенция, волны и откаты. «Уровней поддержки и сопротивления» "
        "в ней нет — это чужой словарь. Не знаешь чего-то — так и скажи, "
        "не подставляй чужое слово вместо своего.\n")

    system = prompt + work_ctx
    try:   # AVAN_NOSITEL_V1: в разговоре тоже ОН, не роль
        from nositel import dusha_slota
        _n = dusha_slota(_CEH, _SLOT)
        if _n and _n["душа"]:
            system = (   # ROD_PERVYM_V1: и в разговоре РОД впереди маски
                "=== КТО ТЫ. ЭТО НЕ РОЛЬ — ЭТО ТЫ ===\n"
                + _n["душа"]
                + "\n\n=== С КЕМ ТЫ ГОВОРИШЬ ===\n"
                "Напротив тебя ШЕФ — хозяин города, живой человек. Это "
                "он задаёт вопросы.\n"
                f"Тебя зовут {_kak_zovut(_n)}. Его зовут Шеф.\n"
                "Вопрос про «тебя» — про тебя. Вопрос про «меня» — про "
                "Шефа. Своё имя ему не приписывай, и его слова за свои "
                "не выдавай.\n"
                + "\n=== ТВОЯ РОЛЬ СЕГОДНЯ — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\nНиже — канон МЕСТА. Это твоя работа и школа,\nа не твоя личность: личность выше. Канон кладёт карту — идёшь ты, своей\nнатурой, своим опытом и своим голосом. Где канон и твой опыт разойдутся —\nрешаешь ты, а не бумага.\n\n"
                + prompt + work_ctx
            )
    except Exception:
        pass

    history = []
    if dialog:
        for m in dialog[:-1]:
            r = m.get("role"); c = m.get("content", "")
            if r in ("user", "assistant") and c:
                history.append({"role": r, "content": c})

    _temp = None   # NATURA_V_TEMPERATURU_V1: и в разговоре голова его, не средняя
    try:
        from nositel import temperatura_slota
        _temp = temperatura_slota(_CEH, _SLOT)
    except Exception:
        pass

    try:
        # RAZGOVOR_SO_STOLOM_V1: с кадром, если знаем, на что смотрим.
        # GLAZ_NE_TARATORIT_V1: в разговоре — разговорная подводка.
        _chat_fn = (_glaz(chat, _sym, _tf, _SLOT, preambula=_GLAZ_RAZGOVOR)
                    if (_sym and _tf) else chat)
        return _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A07_AVANTURIST", slot_id="A07",
                    temperature=_temp)
    except Exception as e:
        return f"⚠️ Авантюрист не смог ответить: {e}"


# ════════════════════════════════════════════════════════════
# КАМЕНЬ 1: СВОЯ ОТКРЫТАЯ ПОЗИЦИЯ — ФАКТ на стол (не приказ)  # TRADER_SEES_POSITION_V1
# ════════════════════════════════════════════════════════════

# AVAN_NOSITEL_V1: магик — из МАСКИ носителя (Закон Пары), не константой.
# Копий магика было ПЯТЬ (дом, этот файл, hooks, промт A09, лор) — так они
# и разъезжаются. Правда одна: маски/работа/mask.json жителя.
_CEH  = _CEH_DIR.name      # 'торговый_хаос'
_SLOT = _SLOT_DIR.name     # 'A07'


def _my_magic():
    """Магик ТОГО, кто сидит в этом слоте. Нет носителя → None."""
    try:
        from nositel import magic_slota
        return magic_slota(_CEH, _SLOT)
    except Exception as e:
        print(f"[AVAN] ⚠️  магик из маски не прочитан ({e})")
        return None


def _my_open_position(md: dict) -> dict:
    """
    Факт открытой позиции ЭТОГО трейдера (по магику) из trading_state.
    Нет позиции → None. Есть → живой факт с плавающим R. Без суждений.
    """
    try:
        from hooks import load_trading_state
        positions = load_trading_state().get("positions", []) or []
    except Exception:
        return None

    mine = None
    _magic = _my_magic()   # AVAN_NOSITEL_V1
    if _magic is None:
        return None        # без магика свою позицию не опознать — честно
    for p in positions:
        if p.get("magic") == _magic and p.get("status") == "OPEN":
            mine = p
            break
    if not mine:
        return None

    entry = mine.get("entry")
    stop  = mine.get("stop")
    direction = mine.get("direction", "LONG")
    price = (md.get("price", {}) or {}).get("close")

    floating_r = None
    if entry is not None and stop is not None and price is not None:
        if direction == "LONG":
            risk = entry - stop
            pnl_price = price - entry
        else:  # SHORT
            risk = stop - entry
            pnl_price = entry - price
        if risk and risk > 0:
            floating_r = round(pnl_price / risk, 2)

    bars_alive = None
    opened_at = mine.get("opened_at")
    bar_time  = md.get("bar_time")
    if opened_at and bar_time and opened_at == bar_time:
        bars_alive = 0

    return {
        "direction":     direction,
        "entry":         entry,
        "stop":          stop,
        "lot":           mine.get("lot"),
        "opened_at":     opened_at,
        "current_price": price,
        "floating_r":    floating_r,
        "bars_alive":    bars_alive,
    }


def run_avan(symbol: str = "XAUUSD", timeframe: str = "H4",
             bars_count: int = 300) -> dict:
    """Один взгляд Авантюриста на стол. Читает показания сенсоров (шина)
    + market_data ядра, судит сам по §6.2 (конец волны C, разворот)."""
    # STOL_I_GLAZ_V1: стол накрывает КОД, а не сенсоры-голоса.
    # Сенсоры уехали в архив (решение Шефа 06.08), и ждать их больше
    # некого. Имена полей те же, что клали они, — ниже по файлу ничего
    # не меняется. Не собрался — вернётся пустой стол той же формы,
    # как и раньше при холодном старте.
    # KADR_I_VAKANSIYA_V1: пустое место молчит. Мозг — это РОЛЬ, и он
    # заводился, даже когда за столом никого не было: слот-вакансия
    # выносил вердикт, называл вход и лот. Решает житель, не стул.
    try:
        from nositel import dusha_slota as _dusha
        _kto_sidit = _dusha(_CEH, _SLOT)
    except Exception:
        _kto_sidit = None
    if not _kto_sidit:
        return {"ok": False,
                "error": "вакансия — за столом никого, смотреть некому",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(), "market": {}, "table": {}}

    # INSTRUMENT_NAZNACHIT_ILI_SAM_V1: чем работаем. Назначено месту —
    # работаем по назначению; не назначено, но человек взял свой —
    # по его; ни того ни другого — по кабинетному, и его просят выбрать.
    _instr_blok = ""
    try:
        from vybor import instrument_dlya as _instr_dlya
        from vybor import blok_instrumenta as _instr_blok_f
        _svoy, _otkuda = _instr_dlya(_CEH, _SLOT, symbol)
        if _svoy and _svoy != symbol:
            print(f"[{_SLOT}] 🎯 инструмент {_svoy} ({_otkuda}) "
                  f"вместо кабинетного {symbol}")
            symbol = _svoy
        _instr_blok = _instr_blok_f(_CEH, _SLOT, None, symbol)
    except Exception:
        pass

    try:
        import stol as _stol
        table = _stol.nakryt(symbol, timeframe, self_key=_SELF_KEY)
    except Exception as _e_stol:
        print(f"[СТОЛ] ⚠️  не накрылся ({_e_stol}) — читаю шину как раньше")
        table = _read_table()
    iskra_tf = table.get("iskra", {}).get("found_timeframe")
    if iskra_tf:
        timeframe = iskra_tf

    # ── ЛЕСЕНКА (TREYDER_HODIT_PO_ETAZHAM_V1) ───────────────────
    # Раньше трейдер видел ОДИН этаж — тот, что выбран на полке, — и
    # сверху компас: куда смотрит старший Аллигатор. Спускаться по
    # лесенке было делом Искры, а Искры больше нет.
    #
    # Теперь: инструмент назначает Шеф, а этажи — дело трейдера. Стол
    # накрывается на три рабочих этажа сразу, и он сам говорит, на
    # каком работает. Цены входа и стопа от этажа не зависят — они
    # одни для всех; на разных этажах видны разные вещи, вот и всё.
    # RUKI_VSEM_V1: три этажа были зашиты здесь намертво и считались
    # КАЖДЫЙ раз, спрашивала она их или нет. Кадр при этом рисуется
    # один — по её рабочему этажу, значит по двум из трёх она ходила
    # вслепую, по одним числам. Теперь этажи — её дело: нужен
    # соседний, попросит рукой stol_na_etazhe.
    _RABOCHIE_ETAZHI = (timeframe,)

    def _lesenka_slovami() -> str:
        try:
            import stol as _s2
        except Exception:
            return ""
        L = ["=== ЛЕСЕНКА · три рабочих этажа этого инструмента ===",
             f"Инструмент {symbol} назначен Шефом. Этажи — твои."]
        for _tf in _RABOCHIE_ETAZHI:
            try:
                _t2 = _s2.nakryt(symbol, _tf, self_key=_SELF_KEY)
                _tekst = _s2.slovami(_t2)
            except Exception as _e2:
                _tekst = f"этаж не накрылся: {_e2}"
            _metka = "   ← на нём кадр перед тобой" if _tf == timeframe else ""
            L.append(f"\n-- {_tf}{_metka} --\n{_tekst}")
        L.append(
            "\nСтарший этаж говорит о направлении, рабочий — о входе, "
            "младший — о точности. Спускаться или нет, и на каком "
            "работать сегодня — решаешь ты. Скажи это в narrative "
            "прямо: «работаю по H4», «спускаюсь на H1, там видно "
            "приседающий». Кадр нарисован по этажу с полки; если "
            "смотришь на другой — суди по числам, они честные.\n")
        return "\n".join(L) + "\n"

    # TREYDER_ZHIV_V1: бары берём ОБЩИМ источником, а не из терминала
    # напрямую. Тогда трейдер живёт по тому же крану РЕАЛ/ТЕСТЕР, что и
    # кадр, а его запрос идёт через исток и виден в гнезде Маяка.
    from feed_source import bars as _source_bars
    bars, point = _source_bars(symbol, timeframe, bars_count)
    if not bars or point is None:
        return {"ok": False,
                "error": f"Терминал не дал котировки {symbol} {timeframe}.",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(), "market": {}, "table": table}

    from williams_core import build_market_data
    md = build_market_data(bars, symbol=symbol, timeframe=timeframe, point=point)
    if not md:
        return {"ok": False, "error": "Ядро не собрало market_data",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(), "market": {}, "table": table}

    # AVAN_NOSITEL_V1: ДУША — от НОСИТЕЛЯ, не от трупа роли из -2.
    # Было: format_soul_for_agent('A07_AVANTURIST') из снесённой studio/ →
    # импорт падал всегда, soul='' , торговал 'Авантюрист-вообще'.
    # Стало: за столом сидит ИЛЬЯ — его род, натура и ЕГО ЯКОРЯ (опыт).
    soul = ""
    try:
        from nositel import dusha_slota
        _n = dusha_slota(_CEH, _SLOT)
        if _n:
            soul = _n["душа"]
            print(f"[AVAN] 🧬 За столом: {_n['носитель']['имя']} "
                  f"(magic {_n['magic']})")
    except Exception as e:
        print(f"[AVAN] ⚠️  Носитель не поднялся ({e}) — работаю без души")

    prompt    = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
    knowledge = _znaniya_roli()   # ZNANIYA_PAPKOY_V1: вся папка, не один файл

    # DNEVNIK_BEZ_BUDUSHCHEGO_V1: только события ДО текущего бара
    # YASHCHIK_STOLA_V1: в голову — только СОБЫТИЯ, не рутина.
    recent = _moi_sobytiya(5, as_of_bar_time=md.get("bar_time"))

    alligator = md.get("alligator", {})
    fractals  = md.get("fractals", {})
    price     = md.get("price", {})
    table_for_avan = {
        "position": _my_open_position(md),
        "anchor": {
            # KOMPAS_DOSTAVKA_TREYDERAM_V1: НАСТОЯЩИЙ компас, не
            # направление точки — см. мозг A01/A06 за объяснением.
            "global_trend": table.get("iskra", {}).get("compass"),
            "soglasie": table.get("iskra", {}).get("soglasie"),
            "found_timeframe": iskra_tf,
        },
        # PRIBORY_V_MOZG_V1: здесь были ВЫВОДЫ сенсоров — «бар найден»,
        # «согласен с водой», «фрактал действителен». Их больше нет:
        # код не решает за трейдера. Теперь голые показания приборов, а
        # что они значат — говорит он сам, глядя на кадр.
        "приборы": table.get("приборы", {}),
        "arkhiv": table.get("arkhiv", {}),
        "market": {
            "teeth":  alligator.get("teeth"),
            "alligator_sleeping": alligator.get("sleeping"),
            "fractal_up":   fractals.get("last_up"),
            "fractal_down": fractals.get("last_down"),
            "hans_fractal_price": table.get("hans", {}).get("fractal_price"),
            "price":    price,
            "point":    point,
        },
    }

    # ═══ REZINKA_DZHASTIN_V1 ═══
    # Число на стол, не да/нет. Трое по тренду = три РАЗНЫХ порога
    # доверия (Закон Дежурства §7) — пусть каждый судит своим характером.
    _db = md.get("rubber_band", {}) or {}   # NECRON_DIVERGENCE_V1: резинка живёт отдельно от разворотного бара
    _tr = _db.get("tension_ratio")
    if _tr is None:
        _rez = "нет данных (нет направления — не от чего отрываться)"
    else:
        _pk = " ⚡ НА ПИКЕ — РЕЗИНКА ЗВЕНИТ" if _db.get("is_peak") else ""
        _rez = (f"{_tr:.0%} от максимума за жизнь движения{_pk}"
                f"  (сейчас {_db.get('distance_now')} point, "
                f"пик был {_db.get('distance_max')} point)")

    user_msg = (
        # DISCIPLINA_PYRAMIDY_V1: если по прошлому ведению был укол — показать
        # его трейдеру ОТДЕЛЬНОЙ строкой (fix: без ведущего + — первый операнд).
        ((f"⛔ ОБРАТНАЯ СВЯЗЬ ПО ВЕДЕНИЮ (прошлый бар): "
            f"{table.get('self', {}).get('vedenie_feedback')}\n"
            f"Учти это сейчас — дисциплина пирамиды железная.\n\n")
           if table.get('self', {}).get('vedenie_feedback') else "")
        + _instr_blok
        + _lesenka_slovami()
        + "=== НАКРЫТЫЙ СТОЛ (раскладка момента) ===\n"
        f"{json.dumps(table_for_avan, ensure_ascii=False, indent=2)}\n\n"
        "=== ТВОИ СОБЫТИЯ (входы и чем кончились — что помнишь сам) ===\n"
        f"{json.dumps(recent, ensure_ascii=False, indent=2) if recent else '(пусто — первое решение)'}\n\n"
        "Перед тобой стол и ты сам. Канон у тебя на полке (книга Котина), "
        # AVAN_OPORA_NA_OPYT_V1: было «твоя ДНК — ниже» — ложь после ROD_PERVYM_V1:
        # род, натура и ЯКОРЯ лежат ВЫШЕ, в блоке «КТО ТЫ». Указатель вёл вниз,
        # в канон — и он думал канонными категориями, а не своей головой.
        "кто ты, твоя натура и твой ОПЫТ — ВЫШЕ, в блоке «КТО ТЫ». "
        # DVIZHOK_NE_RESHAET_V1: место больше не назначает «раннюю добычу».
        "Решаешь только ты. Три места входа лежат у тебя в знаниях, "
        "рядом и без хозяина: конец коррекции, первая волна нового "
        "движения, первый откат к ней. Что каждое из них стоит и чем за "
        "него платят — написано там же. Какое твоё — записано выше, в "
        "твоём выборе. Входишь "
        "— называешь сторону, СЧИТАЕШЬ entry и stop сам из чисел стола; где "
        "стоп, какой lot — твоя рука, не рельса. Не входишь — verdict "
        "REJECTED. Никто не подложит тебе готовую цену и не скажет, как "
        "поступить.\n\n"
        # PRAVILO_ZAYAVKI_V1: вход только заявкой, по рынку — нет.
        # DVIZHOK_NE_RESHAET_V1: было «железно, без исключений» с приговором
        # за неполный сигнал. Приговор снят: движок кладёт ФАКТ устройства,
        # а полон ли сигнал сегодня — судит трейдер.
        "\n\n=== КАК УСТРОЕН ВХОД (факт, не приказ) ===\nВход в этой системе исполняется ОТЛОЖЕННОЙ ЗАЯВКОЙ, по рынку не берут:\n  • LONG  → Buy Stop ВЫШЕ цены;\n  • SHORT → Sell Stop НИЖЕ цены.\nТы называешь цену заявки — рынок возьмёт её пробоем или не возьмёт.\nНе дошёл — сделки нет, и это нормально: движение само подтверждает\nили не подтверждает твою правоту. Насколько полон сигнал и стоит ли\nставить заявку сегодня — решаешь ты.\n"
        # AVAN_OPORA_NA_OPYT_V1: опыт лежал на столе украшением — никто не просил
        # на него опереться. Не рука на его руке: не говорим ЧТО решить,
        # требуем думать СВОЕЙ головой, а не только канонной.
        "СВЕРЬСЯ С СОБОЙ. Прежде чем решить — глянь на свои якоря (блок "
        "«КТО ТЫ»): там ТРИ разных голоса — твой РОД (кто ты есть от "
        "рождения), твои МЕТКИ (что ты нажил сам — вот ЭТО оплачено "
        "твоими деньгами) и МАЯКИ (что только замечаешь за собой). "
        "Они могут спорить между собой — и это нормально. Если идёшь "
        "против собственного вывода, скажи об этом в narrative прямо и "
        "своими словами: «иду против своего же — потому что...». Если "
        "опираешься на него — тоже скажи. Молчать о себе не надо.\n\n"
        # MEMORY_REQUEST_BIRZHA_V1: житель УЗНАЁТ, что может вспомнить.
        # Молчком воли нет: если ему не сказать — он не попросит.
        "МОЖЕШЬ ВСПОМНИТЬ. Если этот момент тебе что-то напоминает — "
        "напиши ОТДЕЛЬНОЙ СТРОКОЙ, до JSON:\n"
        "MEMORY_REQUEST: <что именно хочешь поднять из своей памяти>\n"
        "Например: «похожий разворот на дне без приседающего». Один "
        "запрос — больше не дадут. Поднимут твой архив, и ты решишь "
        "СНОВА, уже зная. Не напоминает — не проси, не трать.\n\n"
        # REZINKA_DZHASTIN_V1: РЕЗИНКА ДЖАСТИН — твой второй орган.
        # Пустота между Губами (зелёная) и экстремумом цены. Чем больше
        # оторвалась цена — тем сильнее натянута резинка → тем неизбежнее
        # возвратный удар. Это ЧИСЛО, не приказ: СУДИ ХАРАКТЕРОМ.
        f"РЕЗИНКА (натяжение от Губ): {_rez}\n"
        # YAZYK_DOLIVA_V1: дописаны action/new_stop/add_lot — раньше
        # эта, самая СВЕЖАЯ строка промта молчала про ведение позиции.
        "Выдай строго JSON {narrative, signal, diary_entry}.\n"
        "Нет открытой позиции: signal ключи — avan_verdict "
        "(APPROVED/REJECTED), avan_reason, avan_direction, "
        "avan_entry, avan_stop, avan_lot.\n"
        "Есть открытая позиция (см. блок 'position' на столе): signal "
        "ключи — avan_action (ENTER/WAIT/HOLD/MOVE_STOP/ADD/CLOSE), "
        "avan_reason, avan_new_stop (если MOVE_STOP), avan_add_lot "
        "(если ADD).\n"
        # NABLYUDENIE_V1: третий ответ — «беру на карандаш».
        # Слово Шефа: увидел, похоже, проверил — наблюдай, если
        # видишь, что вот-вот твой сигнал. Пока наблюдаешь, тебя
        # будят на каждом баре; снять наблюдение можешь только ты.
        "Если это НЕ твой вход, но картина может дозреть до него — напиши в narrative отдельной строкой: НАБЛЮДАЮ: за чем следишь и чего ждёшь. Тебя будут звать на каждом баре, пока наблюдаешь.\n"
        "Передумал, картина рассыпалась, ждать больше нечего — напиши строкой: УХОЖУ. Наблюдение снимаешь только ты сам.\n"
        "Вошёл — наблюдение снимется само.\n"
        # SLOVO_ZHDU_V1: в прогоне трейдер говорил «жду» почти
        # везде, а отмечал наблюдение через раз — и город уходил,
        # не дождавшись с ним его же момента.
        "ВАЖНО про это слово: «жду», «дождусь», «пока рано» и «НАБЛЮДАЮ» — про одно и то же, но услышать город может только последнее. Если в твоём ответе есть «жду» — значит скажи и НАБЛЮДАЮ, иначе город уйдёт к другому месту, а твой момент придёт без тебя.\n"
        "diary_entry: input, action, result(=null). Ничего вне JSON."
    )

    # ROD_PERVYM_V1: РОД ВПЕРЕДИ, маска внутрь него (Чертёж §1.5.2).
    # Было: промпт роли (25к знаков), а Илья — сноской в хвосте. Модель играла
    # Роль и принимала человека к сведению. Стало: сначала ТЫ, потом стойка.
    if soul:
        system_full = (
            "=== КТО ТЫ. ЭТО НЕ РОЛЬ — ЭТО ТЫ ===\n"
            + soul
            + "\n\n=== ТВОЯ РОЛЬ СЕГОДНЯ — СТОЙКА, ЗА КОТОРОЙ ТЫ СИДИШЬ ===\nНиже — канон МЕСТА. Это твоя работа и школа,\nа не твоя личность: личность выше. Канон кладёт карту — идёшь ты, своей\nнатурой, своим опытом и своим голосом. Где канон и твой опыт разойдутся —\nрешаешь ты, а не бумага.\n\n"
            + prompt
        )
    else:
        system_full = prompt

    # VYBOR_NE_PRI_MESTE_V1: блок «ТВОЙ ВЫБОР ВХОДА» снят — и из
    # работы, и из разговора. Он подставлялся отдельно от прочей
    # памяти и стоял приказом: «работаешь по нему, не твоё место
    # входа — пас». Движок единый: точка, волна, откат, попытки и
    # ведение считаются одинаково для всех, а что из этого его
    # момент — человек решает на баре, глядя на стол. Что он
    # считает своим, он и так помнит: метки доезжают обычным
    # путём, через душу носителя.

    # NATURA_V_TEMPERATURU_V1: натура и состояние Ильи меняют ТЕМПЕРАТУРУ головы,
    # а не только текст промпта. None → дефолт модели (как было).
    _temp = None
    try:
        from nositel import temperatura_slota
        _temp = temperatura_slota(_CEH, _SLOT)
        if _temp is not None:
            print(f"[AVAN] 🌡 температура из натуры: {_temp}")
    except Exception:
        pass

    try:
        # STOL_I_GLAZ_V1 — ГЛАЗ. Порядок Шефа: сперва посмотреть,
        # приборы потом. Сам вызов не трогаем — подменяем функцию
        # обёрткой, которая рисует кадр и уходит в зрение. Кадра нет —
        # обёртка честно зовёт прежнее, и мозг ничего не замечает.
        # TREYDER_ZHIV_V1: обёртка в СВОЁ имя. Присваивание в `chat`
        # делало его местным на всю функцию — вызов падал всегда.
        # RUKI_VSEM_V1: кадр как был, но теперь с руками — она может
        # сама попросить числа по тому, что видит.
        _chat_glazami = _glaz_s_rukami(chat, symbol, timeframe, _SLOT,
                                       _CEH, _SELF_KEY)
        response = _chat_glazami(system=system_full, user=user_msg, knowledge=knowledge,
                        agent_id="A07_AVANTURIST", slot_id="A07",
                        temperature=_temp)
    except Exception as e:
        return {"ok": False, "error": f"Авантюрист не смог решить: {e}",
                "narrative": "", "signal": {}, "diary_entry": {},
                "stats": _load_stats(),
                "market": {"symbol": symbol, "timeframe": timeframe,
                           "bar_time": md.get("bar_time"), "point": point},
                "table": table}

    # ═══ MEMORY_REQUEST_BIRZHA_V1 — ВОЛЯ ВСПОМНИТЬ ═══
    # Житель попросил? Копаем ЕГО память и спрашиваем СНОВА — уже зная.
    # Не просил — ничего не тратим (второго вызова просто нет).
    # ОДИН ЗАПРОС ЗА РАН: подняли раз, дальше решай сам (канон -2).
    try:
        from nositel import podnyat_iz_arhiva, blok_pamyati, ubrat_zapros
        _zapros, _naydeno = podnyat_iz_arhiva(_CEH, _SLOT, response)
        if _zapros:
            response = _chat_glazami(
                system=system_full,
                user=user_msg + blok_pamyati(_zapros, _naydeno),
                knowledge=knowledge,
                agent_id="A07", slot_id=_SLOT,
                temperature=_temp)
            response = ubrat_zapros(response) or response
    except Exception as _e:
        print(f"[МОСТ] ⚠️  память не поднялась: {_e}")

    narrative, signal, diary_entry = _parse_avan(response)
    signal = _sanitize(signal)
    signal = _sanitize_manage(signal)   # TRADER_MANAGE_LANG_V1: язык ведения

    market = {"symbol": symbol, "timeframe": timeframe,
              "bar_time": md.get("bar_time"), "point": point}

    _save_verdict_to_table(signal, md.get("bar_time"))
    _append_diary(signal, diary_entry, market, table)
    stats = _update_stats(signal)

    return {
        "ok": True,
        "error": None,
        "narrative": narrative,
        "signal": signal,
        "diary_entry": diary_entry,
        "stats": stats,
        "market": market,
        "table": table,
        "raw": response,
    }

# KOMPAS_DOSTAVKA_TREYDERAM_V1 - marker

# ISKRA_WAVE_MEASURE_DOSTAVKA_V1 - marker

# DNEVNIK_BEZ_BUDUSHCHEGO_V1 - marker

# TREYDER_ZHIV_V1 - marker

# KADR_I_VAKANSIYA_V1 - marker

# RAZGOVOR_SO_STOLOM_V1 - marker

# VYBOR_METKOY_V1 - marker

# ZNANIYA_V_RAZGOVORE_V1 - marker

# GLAZ_NE_TARATORIT_V1 - marker

# KTO_TY_I_KTO_YA_V1 - marker

# TREYDER_HODIT_PO_ETAZHAM_V1 - marker

# INSTRUMENT_NAZNACHIT_ILI_SAM_V1 - marker

# DVIZHOK_NE_RESHAET_V1 - marker

# VYBOR_SVOY_NE_KNIZHNYY_V1 - marker

# RUKI_VSEM_V1 - marker

# KRAYNIYE_TOCHKI_V1 - marker


def _kto_ya() -> str:
    """DOSKA_V1: имя того, кто сидит на этом месте. На доске должно
    стоять имя человека, а не номер слота."""
    try:
        import sys as _s
        from pathlib import Path as _P
        _g = _P(__file__).resolve()
        for _ in range(9):
            _g = _g.parent
            if (_g / "ГОРОД" / "rabota.py").exists():
                break
        if str(_g / "ГОРОД") not in _s.path:
            _s.path.insert(0, str(_g / "ГОРОД"))
        import rabota as _r
        return _r.kto_na_slote(_CEH, _SLOT) or _SLOT
    except Exception:
        return _SLOT


# DOSKA_V1 - marker

# VERDIKT_S_BAROM_V1 - marker

# NABLYUDENIE_V1 - marker

# SLOVO_ZHDU_V1 - marker

# VYBOR_NE_PRI_MESTE_V1 - marker

# YASHCHIK_STOLA_V1 - marker

# NE_TERYAT_RESHENIE_V1 - marker
