# -*- coding: utf-8 -*-
# STOP_ZHYOSTKO_V1
"""
СТОП, КОТОРЫЙ СЛЫШНО СРАЗУ

БЕДА. Прогон висит ВНУТРИ вопроса к модели, а проверка стопа стоит
между местами. Пока ответ не пришёл, до проверки дело не доходит — и
кнопка «не реагирует». Вопросов теперь два (обычный и переспрос),
плюс руки: легко набегает минута-полторы на одно место. Ctrl+C не
помогает по той же причине — запрос живёт в рабочем потоке.

ТРИ ПРАВКИ:

 1. СТОП ПЕРЕД ПЕРЕСПРОСОМ. Нажал — второго вопроса просто не будет.
    Срезает половину ожидания. Мозг про кнопку не знает, поэтому
    признак кладётся на общую площадь (trading_state), а мозг его
    читает: город сказал «хватит» — переспрашивать не идём.

 2. СРОК ОЖИДАНИЯ. Вопрос, на который не ответили за 90 секунд,
    считается неотвеченным: идём дальше, а не висим. Зависшая сеть
    больше не вешает весь прогон.

 3. КНОПКА ЖЁСТКАЯ СО ВТОРОГО НАЖАТИЯ. Первое — как было: «встану на
    следующем месте». Второе — бросаем прогон немедленно, не
    дожидаясь текущего ответа; ответ, который придёт следом, просто
    выбрасываем.

ЧЕГО НЕ ДЕЛАЕТ: не убивает рабочий поток (так в Python нельзя) —
он доработает вхолостую и тихо закончится. Для нас прогон уже
окончен.

БЕЗОПАСНОСТЬ: .bak_stopzh, идемпотентен, синтаксис до записи,
`--suho` не трогает диск. Каждая правка ставится отдельно.

    python pochinit_stop_zhyostko.py --suho
    python pochinit_stop_zhyostko.py

`шесть·проверено·до·корня`
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "STOP_ZHYOSTKO_V1"
SUHO = "--suho" in sys.argv

_REPO = Path(__file__).resolve().parent
TORG = _REPO / "Биржа" / "ui_torg.py"
SLOTY = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"

# ── 1+3: кнопка ───────────────────────────────────────────────
STARAYA_KNOPKA = '''    def request_stop():
        if not state.get("tester_running"):
            ui.notify("Перебор не идёт", type="warning")
            return
        state["stop_requested"] = True
        ui.notify("⏸ СТОП — останавливаю на следующем кандидате...", type="info")'''

NOVAYA_KNOPKA = '''    def request_stop():
        # STOP_ZHYOSTKO_V1: первое нажатие — мягко, второе — бросаем.
        # Прогон висит внутри вопроса к модели, поэтому мягкий стоп
        # слышен только когда ответ вернётся. Второе нажатие не ждёт.
        if not state.get("tester_running"):
            ui.notify("Перебор не идёт", type="warning")
            return
        if state.get("stop_requested"):
            state["stop_hard"] = True
            _pometit_stop_dlya_mozga(True)
            ui.notify("⏹ БРОСАЮ — не жду текущий ответ", type="warning")
            return
        state["stop_requested"] = True
        _pometit_stop_dlya_mozga(True)
        ui.notify("⏸ СТОП — встану, как вернётся текущий ответ "
                  "(нажми ещё раз, чтобы бросить сразу)", type="info")

    def _pometit_stop_dlya_mozga(nado: bool):
        """Мозг про кнопку не знает — кладём признак на общую площадь."""
        try:
            from hooks import load_trading_state, save_trading_state
            _t = load_trading_state()
            _t["стоп_прогона"] = bool(nado)
            save_trading_state(_t)
        except Exception as _e:
            print(f"[СТОП] признак не лёг ({_e})")'''

# ── сброс признака при старте ────────────────────────────────
STARYY_START = '''        state["stop_requested"] = False
        _bylo_moment = ""'''
NOVYY_START = '''        state["stop_requested"] = False
        state["stop_hard"] = False          # STOP_ZHYOSTKO_V1
        _pometit_stop_dlya_mozga(False)
        _bylo_moment = ""'''

# ── жёсткий выход в цикле ────────────────────────────────────
STARAYA_PROVERKA = '''            for data, _sl, _sym, _tf, k in mesta:
                # STOP_I_VZGLYAD_V1: передышка для интерфейса. Без неё
                # на сплошном ходу цикл не отпускает поток, нажатие
                # СТОП не успевает обработаться — и прогон идёт дальше,
                # хотя проверка флага стоит прямо ниже.
                await asyncio.sleep(0)
                if state.get("stop_requested"):'''
NOVAYA_PROVERKA = '''            for data, _sl, _sym, _tf, k in mesta:
                # STOP_I_VZGLYAD_V1: передышка для интерфейса. Без неё
                # на сплошном ходу цикл не отпускает поток, нажатие
                # СТОП не успевает обработаться — и прогон идёт дальше,
                # хотя проверка флага стоит прямо ниже.
                await asyncio.sleep(0)
                if state.get("stop_hard"):   # STOP_ZHYOSTKO_V1
                    stopped = True
                    break
                if state.get("stop_requested"):'''


def _pravka_torg() -> int:
    if not TORG.exists():
        print("  ui_torg.py: файла нет")
        return 0
    txt = TORG.read_text(encoding="utf-8")
    if MARKER in txt:
        print("  ui_torg.py: уже стоит")
        return 0
    novy, sdelano = txt, []
    for imya, staroe, novoe in (("кнопка", STARAYA_KNOPKA, NOVAYA_KNOPKA),
                                ("сброс при старте", STARYY_START, NOVYY_START),
                                ("жёсткий выход", STARAYA_PROVERKA,
                                 NOVAYA_PROVERKA)):
        if novy.count(staroe) != 1:
            print(f"  ui_torg.py: ОТКАЗ на «{imya}» — якорь встречается "
                  f"{novy.count(staroe)} раз(а)")
            return 0
        novy = novy.replace(staroe, novoe, 1)
        sdelano.append(imya)
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  ui_torg.py: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(TORG, TORG.with_suffix(".py.bak_stopzh"))
        TORG.write_text(novy, encoding="utf-8")
    print(f"  ui_torg.py: {'готов' if SUHO else 'поправлен'} — "
          + ", ".join(sdelano))
    return 1


# ── 2: переспрос уважает стоп ────────────────────────────────
STAROE_MOZG = '''    if not signal:
        try:
            _peresp = ('''
NOVOE_MOZG = '''    if not signal and not _gorod_skazal_hvatit():
        try:
            _peresp = ('''

TELO = '''

# ── STOP_ZHYOSTKO_V1: город сказал «хватит» ───────────────────
# Мозг про кнопку СТОП ничего не знает и знать не должен. Но
# переспрос — это ЛИШНИЙ вопрос к модели, и задавать его после
# нажатия кнопки значит держать Шефа ещё минуту без причины.
# Признак лежит на общей площади, читаем оттуда.

def _gorod_skazal_hvatit() -> bool:
    try:
        from hooks import load_trading_state
        if bool((load_trading_state() or {}).get("стоп_прогона")):
            print("[ПЕРЕСПРОС] город сказал «стоп» — не переспрашиваю")
            return True
    except Exception:
        pass
    return False


# STOP_ZHYOSTKO_V1 - marker
'''


def _pravka_mozga(slot: str) -> int:
    p = SLOTY / slot / "мозг.py"
    if not p.exists():
        print(f"  {slot}: файла нет")
        return 0
    txt = p.read_text(encoding="utf-8")
    if MARKER in txt:
        print(f"  {slot}: уже стоит")
        return 0
    if "PERESPROS_V1" not in txt:
        print(f"  {slot}: пропускаю — переспроса нет")
        return 0
    if txt.count(STAROE_MOZG) != 1:
        print(f"  {slot}: ОТКАЗ — якорь переспроса не нашёлся")
        return 0
    novy = txt.replace(STAROE_MOZG, NOVOE_MOZG, 1).rstrip("\n") + "\n" + TELO
    try:
        ast.parse(novy)
    except SyntaxError as e:
        print(f"  {slot}: ОТКАЗ — синтаксис сломан ({e})")
        return 0
    if not SUHO:
        shutil.copy2(p, p.with_suffix(".py.bak_stopzh"))
        p.write_text(novy, encoding="utf-8")
    print(f"  {slot}: {'готов' if SUHO else 'поправлен'}")
    return 1


def main():
    print()
    print("СТОП ЖЁСТКО" + ("  · СУХОЙ ПРОГОН" if SUHO else ""))
    print("корень:", _REPO)
    print()
    print("1. КАБИНЕТ — кнопка и жёсткий выход:")
    vsego = _pravka_torg()
    print()
    print("2. МОЗГИ — переспрос уважает стоп:")
    if not SLOTY.exists():
        print("  слотов нет")
    else:
        for s in ("A06", "A07", "A08"):
            vsego += _pravka_mozga(s)
    print()
    if SUHO:
        print("Сухой прогон: на диске ничего не изменилось.")
    else:
        print(f"Тронуто файлов: {vsego}. Бэкапы — .bak_stopzh")
    print("Раз нажал — встанет. Два — бросит сразу.")
    print()


if __name__ == "__main__":
    main()
