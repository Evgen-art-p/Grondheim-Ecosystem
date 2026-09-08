# -*- coding: utf-8 -*-
# ZHIVOY_KADR_V1
"""
ЖИВОЙ КАДР ТРЕЙДЕРА — чтобы Шеф видел тот этаж, который трейдер выбрал.

ДЫРА (найдена 06.09, подтверждена по коду 08.09). Когда трейдер зовёт
руку `pokazat_etazh` / `rastyanut_volnu`, та рисует PNG и возвращает
строку «[КАДР: путь] инструмент этаж». Дальше:

  · llm.chat_with_images_and_tools эту строку ЛОВИТ и дошлёт картинку
    в зрение модели — трейдер видит, что попросил. Это работает.
  · А в кабинете строку не разбирает НИКТО. Картинка лежит на диске
    (Биржа/кадры/), но на экран Шефа не попадает вообще.
  · Панель кадра и кнопка «👁 Взгляд» всегда рисуют НАЗНАЧЕННЫЙ этаж
    (_para_aktivnogo → рабочий этаж места), а не тот, что трейдер
    только что смотрел.

Итог: обещание «Шеф и трейдер смотрят на одну картинку» держится ровно
до того момента, как трейдер сходил руками дальше своего кадра. А
проверить «видит или придумывает» без этого нельзя в принципе — сверять
его слова не с чем.

ЧТО ДЕЛАЕТ ПАТЧ (крючок уже был готов, его просто никто не передавал):

  1. В трёх мозгах (A06/A07/A08), в `_glaz_s_rukami`, добавляется
     `on_tool_call` — параметр, который llm зовёт ПОСЛЕ КАЖДОЙ руки.
     Крючок ловит ответы, начинающиеся с «[КАДР: », и кладёт путь и
     подпись на общую площадь города (trading_state["zhivoy_kadr"]).
     Больше он не делает ничего: ни считает, ни решает, ни рисует.

  2. В кабинете (`Биржа/ui_torg.py`) встаёт таймер — тем же приёмом,
     что уже держит ленту чата живой (KABINET_ZHIVYOT_PRI_GORODE_V1).
     Раз в секунду смотрит, не появился ли новый живой кадр, и если
     появился — перерисовывает панель им, с подписью «рукой трейдера».

ПОВЕДЕНИЕ. Панель показывает последнее, на что трейдер смотрел, пока
он не посмотрит что-то ещё. Шеф жмёт «👁 Взгляд» или переключает
пузырёк — панель возвращается к назначенному этажу как раньше
(pokazat_kadr рисует поверх и сбрасывает метку живого кадра).

ЧЕГО ПАТЧ НЕ ТРОГАЕТ: ни решение трейдера, ни стол, ни промпт, ни
знания, ни зрение модели. Только показ картинки Шефу. Если крючок
сорвётся — он в try, разговор идёт как шёл.

Запускать из корня репозитория:
    python postavit_zhivoy_kadr.py

Идемпотентен (маркер ZHIVOY_KADR_V1 в каждом файле). Сверяет ВСЕ куски
заранее: либо ложится целиком во все четыре файла, либо не трогает
ничего. Рядом с каждым файлом кладёт .bak.
"""
from __future__ import annotations
from pathlib import Path

MARKER = "ZHIVOY_KADR_V1"

MOZGI = [
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/мозг.py",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/мозг.py",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A08/мозг.py",
]
KABINET = "Биржа/ui_torg.py"


# ══════════════════════════════════════════════════════════════
# 1) МОЗГИ — крючок после каждой руки
# ══════════════════════════════════════════════════════════════

MOZG_OLD = '''                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary,
                                       rabochiy_etazh=timeframe,
                                       imya_zhitelya=_kto_ya()),
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))'''

MOZG_NEW = '''                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary,
                                       rabochiy_etazh=timeframe,
                                       imya_zhitelya=_kto_ya()),
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    on_tool_call=_zhivoy_kadr_kryuchok,   # ZHIVOY_KADR_V1
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))'''

# крючок определяем внутри obertka, до вызова llm
# Крючок кладём ВНУТРЬ obertka функции _glaz_s_rukami. Просто искать
# "def obertka" нельзя: в файле их две (у _glaz и у _glaz_s_rukami), и
# начинаются они одинаково. Поэтому ищем от подписи _glaz_s_rukami —
# она в файле одна — и берём первую obertka после неё. Текст описания
# у A08 отличается от A06/A07, поэтому за него не цепляемся.

MOZG_PODPIS = "def _glaz_s_rukami(_chat, symbol, timeframe, slot, ceh, self_key,"
MOZG_OBERTKA = '''    def obertka(system="", user="", knowledge="", **kw):'''

MOZG_KRYUK = '''    # ZHIVOY_KADR_V1: крючок после каждой руки. Ловит только ответы
    # вида "[КАДР: путь] инструмент этаж" и кладёт их на общую площадь
    # города, чтобы кабинет показал Шефу ТОТ ЖЕ этаж, на который
    # трейдер сходил руками. Ничего не считает и не решает.
    def _zhivoy_kadr_kryuchok(_imya, _args, _otvet):
        try:
            s = str(_otvet or "")
            if not s.startswith("[КАДР: "):
                return
            _put = s[7:s.index("]")]
            _podpis = s[s.index("]") + 1:].strip()[:120]
            from hooks import load_trading_state, save_trading_state
            _t = load_trading_state()
            _t["zhivoy_kadr"] = {
                "put": _put,
                "podpis": _podpis,
                "chey": _kto_ya() or slot,
                "slot": slot,
                "ruka": str(_imya),
            }
            save_trading_state(_t)
            print(f"[ЖИВОЙ КАДР] {slot} посмотрел: {_podpis}")
        except Exception as _e_zk:
            print(f"[ЖИВОЙ КАДР] не запомнился ({_e_zk}) — не беда")

'''


def _pravka_mozga(text: str):
    """(новый текст, None) или (None, причина). Ничего не гадает."""
    if text.count(MOZG_PODPIS) != 1:
        return None, f"подпись _glaz_s_rukami найдена {text.count(MOZG_PODPIS)} раз (нужно 1)"
    i = text.index(MOZG_PODPIS)
    j = text.find(MOZG_OBERTKA, i)
    if j < 0:
        return None, "после подписи _glaz_s_rukami не найдена obertka"
    text = text[:j] + MOZG_KRYUK + text[j:]
    if text.count(MOZG_OLD) != 1:
        return None, f"вызов llm найден {text.count(MOZG_OLD)} раз (нужно 1)"
    text = text.replace(MOZG_OLD, MOZG_NEW, 1)
    return text, None


# ══════════════════════════════════════════════════════════════
# 2) КАБИНЕТ — таймер, показывающий живой кадр
# ══════════════════════════════════════════════════════════════

UI_OLD = '''    try:
        ui.timer(1.0, _dognat_lentu)
    except Exception as _e_tmr:
        print(f"[КАБИНЕТ] лента не догоняет ({_e_tmr}) — не беда")'''

UI_NEW = '''    try:
        ui.timer(1.0, _dognat_lentu)
    except Exception as _e_tmr:
        print(f"[КАБИНЕТ] лента не догоняет ({_e_tmr}) — не беда")

    # ZHIVOY_KADR_V1: панель показывает ТО, НА ЧТО СМОТРИТ ТРЕЙДЕР.
    # Раньше кадр всегда был про назначенный этаж места, а когда
    # трейдер уходил руками на другой — Шеф этого не видел вовсе, и
    # сверить его слова было не с чем. Тот же приём, что у ленты выше:
    # раз в секунду смотрим на площадь города, не появился ли новый.
    _zhivoy_vidno = {"put": None}

    def _dognat_zhivoy_kadr():
        try:
            if not kadr_ref["element"]:
                return
            from hooks import load_trading_state
            zk = (load_trading_state() or {}).get("zhivoy_kadr") or {}
            put = zk.get("put")
            if not put or put == _zhivoy_vidno["put"]:
                return
            p = Path(put)
            if not p.exists():
                return
            _zhivoy_vidno["put"] = put
            kadr_ref["element"].clear()
            with kadr_ref["element"]:
                ui.image(str(p)).style(
                    "width:100%; height:100%; object-fit:contain; "
                    "flex:1; min-height:0;")
                _chey = zk.get("chey") or zk.get("slot") or "трейдер"
                _pod = zk.get("podpis") or ""
                ui.label(f"🖐 {_chey} смотрит рукой · {_pod}").style(
                    "color:rgba(224,160,32,0.9); font-size:11px; "
                    "letter-spacing:0.06em; padding-top:6px; "
                    "flex-shrink:0; width:100%; text-align:center;")
        except Exception:
            pass

    try:
        ui.timer(1.0, _dognat_zhivoy_kadr)
    except Exception as _e_zk:
        print(f"[КАБИНЕТ] живой кадр не догоняет ({_e_zk}) — не беда")'''

# «Взгляд» и переключение трейдера возвращают панель к назначенному
# этажу: сбрасываем метку живого кадра, иначе таймер тут же нарисует
# поверх свою картинку и Шеф не увидит того, что просил.
UI_SBROS_OLD = '''        kadr_ref["element"].clear()
        with kadr_ref["element"]:
            # KADR_NA_VES_KVADRAT_V1: тянемся на всю клетку, но БЕЗ
            # плющенья — contain держит пропорции свечей. Плющеная
            # свеча врёт глазу, а глаз у нас важнее цифры.'''

UI_SBROS_NEW = '''        # ZHIVOY_KADR_V1: Шеф смотрит сам — значит живой кадр трейдера
        # больше не показываем поверх, пока трейдер не сходит рукой
        # заново. Иначе таймер перерисует панель через секунду.
        try:
            from hooks import load_trading_state, save_trading_state
            _t_zk = load_trading_state()
            if _t_zk.get("zhivoy_kadr"):
                _t_zk["zhivoy_kadr"] = {}
                save_trading_state(_t_zk)
            _zhivoy_vidno["put"] = None
        except Exception:
            pass
        kadr_ref["element"].clear()
        with kadr_ref["element"]:
            # KADR_NA_VES_KVADRAT_V1: тянемся на всю клетку, но БЕЗ
            # плющенья — contain держит пропорции свечей. Плющеная
            # свеча врёт глазу, а глаз у нас важнее цифры.'''


def _pravki_ui(text: str):
    """(новый текст, None) или (None, причина)."""
    for nomer, (old, new) in enumerate(((UI_OLD, UI_NEW),
                                        (UI_SBROS_OLD, UI_SBROS_NEW)), start=1):
        if text.count(old) != 1:
            return None, f"кусок {nomer} найден {text.count(old)} раз (нужно 1)"
        text = text.replace(old, new, 1)
    return text, None


def main() -> None:
    root = Path(__file__).resolve().parent
    fayly = [(root / f, _pravka_mozga) for f in MOZGI]
    fayly.append((root / KABINET, _pravki_ui))

    net = [f for f, _ in fayly if not f.exists()]
    if net:
        print("НЕ НАШЁЛ файлы (запускать из корня репозитория):")
        for f in net:
            print("   ", f)
        return

    # ── сверка ВСЕГО заранее: либо всё, либо ничего ──────────────
    plan, uzhe, bracket = [], [], []
    for f, pravka in fayly:
        text = f.read_text(encoding="utf-8")
        if MARKER in text:
            uzhe.append(f.parent.name + "/" + f.name)
            continue
        novyy, prichina = pravka(text)
        if prichina:
            bracket.append((f.parent.name + "/" + f.name, prichina))
            continue
        novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
        try:
            import ast
            ast.parse(novyy)
        except SyntaxError as e:
            bracket.append((f.parent.name + "/" + f.name,
                            f"после правки синтаксис ломается: {e}"))
            continue
        plan.append((f, text, novyy))

    if uzhe and not plan and not bracket:
        print("уже накачен во всех файлах — ничего не трогаю")
        return

    if bracket:
        print("⚠ Файлы на диске отличаются от ожидаемого — НИЧЕГО не меняю:")
        for imya, prichina in bracket:
            print(f"   {imya}: {prichina}")
        print("\nПришли Брату эти файлы — доведу под них.")
        return

    for f, staroe, novoe in plan:
        bak = f.with_suffix(f.suffix + ".bak_zhivoy_kadr")
        if not bak.exists():
            bak.write_text(staroe, encoding="utf-8")
        f.write_text(novoe, encoding="utf-8")
        print(f"✔ {f.parent.name}/{f.name} — правки легли, синтаксис цел")

    if uzhe:
        print("(пропущены, уже накачены: " + ", ".join(uzhe) + ")")

    print("\nГотово. Как проверить:")
    print("  1. Спроси трейдера в чате: «а что на 15-минутке?»")
    print("  2. В консоли появится [РУКА] и следом [ЖИВОЙ КАДР] …")
    print("  3. Панель кадра справа сменится на тот этаж, с подписью")
    print("     «🖐 <имя> смотрит рукой».")
    print("  4. Жмёшь «👁 Взгляд» — панель возвращается к своему этажу.")


if __name__ == "__main__":
    main()
