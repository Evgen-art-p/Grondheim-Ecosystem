# -*- coding: utf-8 -*-
"""
postavit_obhod_etazhey.py · MARKER: OBHOD_ETAZHEY_V1

ТРЕБУЕТ: postavit_paru_mesta.py (лесенка и рабочая пара).

ЧТО ЭТО
───────
Сценарий Шефа 14.08, дословно по смыслу:

    зашёл в кабинет → ТЕРМИНАЛ (источник) → кликнул трейдера →
    кликнул слева ИНСТРУМЕНТ, и больше ничего не задаю →
    дальше он сам проходит по этажам, выбирает рабочий и встаёт
    на дежурство. Сигналы редкие: раз посмотрел — и ждёт.
    С утра или когда сам сочтёт нужным — прошёлся заново.

Этаж Шеф не задаёт вовсе. Его находит трейдер, и находит ГЛАЗОМ:
шагает по коридору масштабов и смотрит, на каком его структура
ложится в окно 100-140 баров целиком. Правило Вильямса: 100-140 —
это выбор таймфрейма для чтения картинки, а не фильтр сигналов.

КОРИДОР (слово Шефа): от D1 до M15.
    Ниже M15 не спускаемся: «бывает и до 10 минут спускаешься, и до
    5, но это ни разу своей эффективности мне лично не показало».
    Выше D1 рабочим не ставим: неделя и месяц нужны для тренда, а не
    для работы. Это не запрет навсегда — одна строка в masshtab.py.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. `Биржа/masshtab.py` — коридор рабочих этажей и опыт Шефа про
   мелкие масштабы, записанный прямо в файл, чтобы через месяц не
   выяснять это заново.

2. `Биржа/obhod.py` — рука обхода. Рисует кадры коридора (те же, что
   видит Шеф), отдаёт их ГЛАЗУ ТРЕЙДЕРА — через разговорную дверь его
   собственного мозга, не через чужую — и ловит ответ «ЭТАЖ: H1».
   Решает трейдер, рука только водит и записывает.
   Своей модели и своего промпта у руки нет: в слот она не лезет,
   параллельной дороги вдоль мозга не строит.

3. Обход не бесплатный (каждый этаж — картинка), поэтому он не на
   каждый бар: `nado_li_oboyti()` говорит «пора», если этажа ещё нет,
   если сменился инструмент или если с прошлого обхода прошли сутки.
   Позвать руками можно всегда.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает кабинет и вахту: кнопка обхода и дежурство по своей свече —
следующим шагом. Сейчас обход зовётся из консоли или кодом.

Запуск: py postavit_obhod_etazhey.py   (или --suho)
        py Биржа\\obhod.py A06          — прогнать обход руками
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "OBHOD_ETAZHEY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    # Приметы только ПОСТОЯННЫЕ. Раньше здесь стоял masshtab.py — а он
    # появляется лишь после предыдущего патча, и город без него
    # объявлялся «не тем городом». Примета не должна быть тем, что
    # патч сам и создаёт.
    return ((p / "Биржа" / "vybor.py").exists()
            and (p / "Биржа" / "ui_torg.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


# ── 1. коридор в лесенку ──
ST_OKNO = '''# Окно чтения картинки. Не фильтр — масштаб.
BAROV_V_KADRE = 140
OKNO = (100, 140)'''

NOV_OKNO = '''# Окно чтения картинки. Не фильтр — масштаб.
BAROV_V_KADRE = 140
OKNO = (100, 140)

# ── КОРИДОР РАБОЧИХ ЭТАЖЕЙ (OBHOD_ETAZHEY_V1, слово Шефа 14.08) ──
# Где трейдер ищет свой рабочий масштаб. Границы не выдуманы:
#
#   низ — M15. «Бывает и до 10 минут спускаешься, и до 5, но это ни
#   разу своей эффективности мне лично не показало» (Шеф). Не запрет,
#   а известное: пробовали, не показало. Захотим — сдвинем строкой.
#
#   верх — D1. Неделя и месяц остаются для ТРЕНДА (компас со старшего
#   этажа), рабочими их не делаем.
#
# Частота работы задаётся именно этим: час — сигналы чаще, четыре
# часа — реже, дневка — совсем редко, зато ждёт.
KORIDOR = ["D1", "H12", "H8", "H4", "H1", "M30", "M15"]


def v_koridore(tf: str) -> bool:
    return (tf or "").strip().upper() in KORIDOR


def koridor_ot(tf: str = "") -> list:
    """Этажи для обхода. Начинаем с рабочего, если он задан и в
    коридоре, — чтобы привычный шёл первым, а не последним."""
    tf = (tf or "").strip().upper()
    if tf in KORIDOR:
        i = KORIDOR.index(tf)
        return [tf] + [x for j, x in enumerate(KORIDOR) if j != i]
    return list(KORIDOR)'''

OBHOD_PY = '''# -*- coding: utf-8 -*-
# OBHOD_ETAZHEY_V1
"""
ОБХОД ЭТАЖЕЙ — как трейдер находит свой рабочий масштаб.

ЗАЧЕМ
    Шеф задаёт трейдеру ТОЛЬКО инструмент. Этаж — его дело: он
    проходит по коридору масштабов, смотрит картинку на каждом и
    выбирает тот, где ЕГО структура ложится в окно целиком.
    Окно фиксировано (140 баров), меняется этаж — меняется, сколько
    времени в это окно влезает.

ЗАКОН ЭТОГО ФАЙЛА
    Рука ВОДИТ и ЗАПИСЫВАЕТ. Она не решает и не имеет своего мнения
    о рынке. Смотрит глаз трейдера — через разговорную дверь его
    СОБСТВЕННОГО мозга. Своей модели, своего промпта и своих знаний
    у руки нет: параллельной дороги вдоль слота мы больше не строим
    (урок vzglyad.py, 06.08).

ЦЕНА
    Каждый этаж — картинка, картинка — деньги. Поэтому обход не на
    каждый бар: при назначении инструмента, дальше раз в сутки или
    когда позвали руками.
"""
from __future__ import annotations

import json
import sys as _sys
from datetime import datetime, timedelta
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
_KOREN = _BIRZHA.parent
for _p in (str(_BIRZHA), str(_KOREN / "ГОРОД"), str(_KOREN / "жители")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

CEH_PO_UMOLCHANIYU = "торговый_хаос"
SUTKI = timedelta(hours=24)

# где помним, когда и по чему ходили — при слоте, а не общим листком
def _sled_put(ceh: str, slot: str) -> Path:
    return (_KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh / "слоты"
            / slot / "данные" / "obhod.json")


def _sled(ceh: str, slot: str) -> dict:
    try:
        return json.loads(_sled_put(ceh, slot).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _zapisat_sled(ceh: str, slot: str, d: dict):
    p = _sled_put(ceh, slot)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    except Exception as e:
        print(f"[ОБХОД] ⚠️  след не записался: {e}")


def nado_li_oboyti(ceh: str, slot: str) -> tuple:
    """(надо ли, почему). Обход платный — зовём по делу, не каждый бар."""
    import vybor
    r = vybor.rabota_dlya(ceh, slot)
    if not r.get("инструмент"):
        return False, "инструмент не задан — обходить нечего"
    sled = _sled(ceh, slot)
    if not r.get("этаж"):
        return True, "рабочего этажа ещё нет"
    if (sled.get("инструмент") or "").upper() != r["инструмент"].upper():
        return True, "инструмент сменился"
    kogda = sled.get("когда") or ""
    try:
        if datetime.fromisoformat(kogda) < datetime.now() - SUTKI:
            return True, "прошли сутки с прошлого обхода"
    except Exception:
        return True, "неизвестно, когда ходили"
    return False, "ходили недавно, этаж есть"


def _dver_razgovora(ceh: str, slot: str):
    """Разговорная дверь мозга ЭТОГО слота. Своей не заводим."""
    import importlib.util
    put = (_KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / ceh / "слоты"
           / slot / "мозг.py")
    if not put.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"_mozg_{ceh}_{slot}", put)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for imya in dir(mod):
        if imya.startswith("chat_with_"):
            return getattr(mod, imya)
    return None


VOPROS = """Тебе назначен инструмент {symbol}. Рабочий этаж выбираешь ты сам.

Сейчас ты смотришь {tf}. На картинке — {barov} баров этого этажа.

Вопрос один: ложится ли на этом масштабе ТВОЯ структура целиком —
та, по которой ты работаешь? Тебе нужно видеть и импульс, и коррекцию
после него, и место, где ты входишь. Не «есть ли сигнал прямо сейчас»,
а «читается ли здесь картина».

Если структура не влезла — масштаб мелкий, надо крупнее.
Если она сжата в несколько баров и разворотный бар не разглядеть —
масштаб крупный, надо мельче.

Ответь коротко, своими словами. Если этот этаж тебе подходит как
РАБОЧИЙ — закончи ответ отдельной строкой:
ЭТАЖ: {tf}
Если не подходит — просто скажи почему, строку не пиши."""


def oboyti(ceh: str = CEH_PO_UMOLCHANIYU, slot: str = "",
           predel: int = 0, govorit=print) -> dict:
    """Провести трейдера по коридору. Решение — его, запись — наша.

    predel — сколько этажей показать максимум (0 = весь коридор).
    Возвращает {этаж, шагов, почему, ошибка}.
    """
    import vybor
    import masshtab

    itog = {"этаж": "", "шагов": 0, "почему": "", "ошибка": ""}
    r = vybor.rabota_dlya(ceh, slot)
    symbol = r.get("инструмент") or ""
    if not symbol:
        itog["ошибка"] = "инструмент не задан — водить не по чему"
        return itog

    dver = _dver_razgovora(ceh, slot)
    if dver is None:
        itog["ошибка"] = "у слота нет разговорной двери (мозг не найден)"
        return itog

    etazhi = masshtab.koridor_ot(r.get("этаж") or "")
    if predel > 0:
        etazhi = etazhi[:predel]

    govorit(f"[ОБХОД] 🧭 {slot} · {symbol} · коридор: {', '.join(etazhi)}")
    for tf in etazhi:
        itog["шагов"] += 1
        vopros = VOPROS.format(symbol=symbol, tf=tf,
                               barov=masshtab.BAROV_V_KADRE)
        try:
            # rynok=(инструмент, этаж) — кадр этого этажа подложит
            # сам мозг, своим глазом. Мы картинку не рисуем.
            otvet = dver(vopros, None, None, (symbol, tf))
        except Exception as e:
            govorit(f"[ОБХОД] ⚠️  {tf}: не ответил ({e})")
            continue
        vzyal, chto = vybor.poymat_etazh(ceh, slot, symbol, otvet or "")
        korotko = " ".join((otvet or "").split())[:110]
        if vzyal:
            govorit(f"[ОБХОД] ✓ {tf} — берёт: {chto}")
            govorit(f"[ОБХОД]   его словами: {korotko}")
            itog["этаж"] = tf
            itog["почему"] = korotko
            break
        govorit(f"[ОБХОД] · {tf} — не тот: {korotko}")

    _zapisat_sled(ceh, slot, {
        "инструмент": symbol,
        "этаж": itog["этаж"],
        "шагов": itog["шагов"],
        "когда": datetime.now().isoformat(timespec="seconds"),
        "почему": itog["почему"],
    })
    if not itog["этаж"]:
        itog["ошибка"] = ("прошёл коридор и не выбрал ни одного этажа — "
                          "картинка не читается ни на одном масштабе")
        govorit(f"[ОБХОД] 🤐 {slot}: {itog['ошибка']}")
    return itog


if __name__ == "__main__":
    _slot = _sys.argv[1] if len(_sys.argv) > 1 else ""
    if not _slot:
        print("Скажи, кого вести: py obhod.py A06")
        raise SystemExit(1)
    _ceh = _sys.argv[2] if len(_sys.argv) > 2 else CEH_PO_UMOLCHANIYU
    nado, pochemu = nado_li_oboyti(_ceh, _slot)
    print(f"[ОБХОД] надо ли: {'да' if nado else 'нет'} — {pochemu}")
    print(oboyti(_ceh, _slot))

# OBHOD_ETAZHEY_V1 - marker
'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    masshtab = koren / "Биржа" / "masshtab.py"
    obhod = koren / "Биржа" / "obhod.py"

    if not masshtab.exists():
        print("\n✗ Нет файла Биржа/masshtab.py — значит не накачен")
        print("  предыдущий патч. Порядок такой:")
        print("     1. postavit_ruku_rynka.py")
        print("     2. postavit_paru_mesta.py   ← вот этого не хватает")
        print("     3. postavit_rabotu_po_pare.py")
        print("     4. postavit_obhod_etazhey.py (этот)")
        return 1
    if "PARA_MESTA_V1" not in masshtab.read_text(encoding="utf-8"):
        print("✗ Биржа/masshtab.py есть, но без маркера PARA_MESTA_V1 —")
        print("  накати сперва postavit_paru_mesta.py")
        return 1

    print("\n1. Коридор рабочих этажей (D1 … M15)")
    t = masshtab.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · уже стоит — пропускаю")
    elif t.count(ST_OKNO) != 1:
        print("  ✗ не нашёл якорь окна дословно")
        return 1
    else:
        novyy = t.replace(ST_OKNO, NOV_OKNO, 1) + f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(masshtab, masshtab.with_suffix(
                f".py.bak_koridor_{datetime.now():%Y%m%d_%H%M%S}"))
            masshtab.write_text(novyy, encoding="utf-8")
            print("  ✓ коридор встал (7 этажей, опыт про 10 и 5 минут записан)")

    print("\n2. Рука обхода — Биржа/obhod.py")
    if obhod.exists() and MARKER in obhod.read_text(encoding="utf-8"):
        print("  · уже лежит — пропускаю")
    else:
        try:
            ast.parse(OBHOD_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if SUHO:
            print("  · готова (сухой прогон)")
        else:
            obhod.write_text(OBHOD_PY, encoding="utf-8")
            print("  ✓ положена")

    if not SUHO:
        import py_compile
        for f in (masshtab, obhod):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nКак теперь выглядит день трейдера:")
        print("  ты дал инструмент → он прошёл коридор глазом →")
        print("  сказал «ЭТАЖ: …» → работает на нём;")
        print("  заново пойдёт, если сменишь инструмент или пройдут сутки.")
        print("\nПрогнать руками (модель платная, один слот за раз):")
        print("   py Биржа\\obhod.py A06")
        print("\nКнопка в кабинете и дежурство по своей свече — следующий шаг.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
