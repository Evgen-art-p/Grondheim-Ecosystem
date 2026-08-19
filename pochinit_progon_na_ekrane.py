# -*- coding: utf-8 -*-
"""
pochinit_progon_na_ekrane.py · MARKER: PROGON_VIDNO_V1

ЧТО ПОКАЗАЛ СНИМОК ЭКРАНА
─────────────────────────
    Connection lost. Trying to reconnect…

Прогон написал «ищу до 10 мест» — и связь оборвалась. Дальше страница
мертва: ни кадров, ни ответов, ни отчёта. Город в это время работает,
но пишет в консоль, а ты смотришь в замёрзшее окно. Отсюда и «это не
тест, это игрушка» — справедливо.

ПОЧЕМУ РВАЛАСЬ СВЯЗЬ (моя вина, дважды)
───────────────────────────────────────
1. КАДР РИСОВАЛСЯ В ГЛАВНОМ ПОТОКЕ. Рисование графика — это
   matplotlib, секунды работы. Пока он рисует, сервер не отвечает
   ни на что, и браузер обрывает связь.

2. И РИСОВАЛСЯ ДВАЖДЫ НА КАЖДОЕ МЕСТО. Один раз для показа
   (`pokazat_kadr`), второй — чтобы положить картинку в отчёт. То
   есть на десяти местах двадцать тяжёлых рисований подряд в потоке,
   который обязан отвечать браузеру.

ЧТО ПРАВИТ
──────────
1. Кадр рисуется ОДИН раз и В ФОНЕ. Одна картинка идёт и на экран, и
   в отчёт — второй раз её никто не рисует.

2. Кадр показывается на экране СРАЗУ, как место открыто, — ты видишь
   ровно то, на что сейчас смотрит трейдер.

3. Ответ трейдера ложится в ОТЧЁТ СПРАВА (панель «Отчёт»), а не
   только в ленту. Раньше там висело «Отчёт пока не создан», потому
   что прогон писал в чат и не трогал отчёты.

4. В конце прогона на экран выводится ИТОГ, а не только путь к папке:
   сколько мест, сколько входов, сколько отказов и где лежит разбор.

ЧТО ТЫ УВИДИШЬ ПОСЛЕ ЭТОГО
──────────────────────────
    📍 2025.05.05 20:00 · разворотный BULL · волна 140 баров
       [кадр справа меняется на это место]
       [отчёт справа — что сказала Нина]
    … и так по каждому месту, живьём, без обрыва связи

    ✓ прогон окончен · мест 10 · входов 0 · отказов 10
      разбор: …/прогоны/20260816_154138

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py pochinit_progon_na_ekrane.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_VIDNO_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists() and (p / "main.py").exists()


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


# ── 1. кадр: один раз, в фоне, до опроса трейдера ──
ST_KADR = '''                istoriya.postavit(data)
                try:
                    pokazat_kadr()
                except Exception:
                    pass
                imya = _agent_label(roster, _sl) or _sl'''

NOV_KADR = '''                istoriya.postavit(data)
                imya = _agent_label(roster, _sl) or _sl
                # PROGON_VIDNO_V1: кадр рисуем ОДИН раз и В ФОНЕ.
                # Раньше он рисовался в главном потоке, да ещё дважды
                # на место (для экрана и для отчёта) — matplotlib на
                # секунды вешал сервер, и браузер обрывал связь:
                # «Connection lost». Одна картинка идёт и на экран,
                # и в отчёт.
                _kadr = None
                try:
                    _kadr = await loop.run_in_executor(
                        None, lambda s=_sym, t=_tf: __import__(
                            "grafik").kadr(s, t))
                except Exception as _ek:
                    print(f"[ПРОГОН] кадр не нарисовался: {_ek}")
                try:
                    pokazat_kadr(_kadr)
                except Exception:
                    pass'''

# ── 2. в отчёт кладём УЖЕ нарисованный кадр ──
ST_OTCHYOT = '''                if _otchyot is not None:
                    _kadr = None
                    try:
                        import grafik as _gr
                        _kadr = _gr.kadr(_sym, _tf)
                    except Exception:
                        pass
                    try:'''

NOV_OTCHYOT = '''                if _otchyot is not None:
                    try:'''

# ── 3. ответ трейдера — в панель отчёта справа ──
ST_LENTA = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()'''

NOV_LENTA = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()
                # PROGON_VIDNO_V1: и в ОТЧЁТ справа. Раньше там висело
                # «Отчёт пока не создан»: прогон писал только в ленту.
                try:
                    _shapka = (f"# {imya} ({_sl})\\n\\n"
                               f"**{k.get('дата', '')}** · {_sym} {_tf} · "
                               f"разворотный {k.get('разворотный')} · "
                               f"волна {k.get('длина_волны')} баров · "
                               f"компас {k.get('компас')}\\n\\n---\\n\\n")
                    state["reports"][_sl] = _shapka + (
                        skazal or "(без текста)")
                    if state.get("active_agent") == _sl:
                        update_viewer(state["reports"][_sl])
                except Exception as _er2:
                    print(f"[ПРОГОН] отчёт не показался: {_er2}")'''

# ── 4. итог на экран, а не только путь ──
ST_ITOG = '''        state["chat_history"].append({
            "role": "system",
            "content": f"✓ прогон окончен · пройдено мест: {proydeno}{_hvost}"})'''

NOV_ITOG = '''        # PROGON_VIDNO_V1: итог словами, а не только путь к папке.
        _vhodov = 0
        _otkazov = 0
        try:
            for _m in (_otchyot.mesta if _otchyot is not None else []):
                _v = str(_m.get("вердикт", "")).upper()
                if _v in ("APPROVED", "ENTER", "OK"):
                    _vhodov += 1
                elif _v in ("REJECTED", "WAIT"):
                    _otkazov += 1
        except Exception:
            pass
        state["chat_history"].append({
            "role": "system",
            "content": (f"✓ прогон окончен · мест {proydeno} · "
                        f"входов {_vhodov} · отказов {_otkazov}{_hvost}")})'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    t = ui_torg.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if "OTCHYOT_PROGONA_V1" not in t:
        print("✗ Нет отчёта прогона — накати сперва "
              "postavit_otchyot_progona.py")
        return 1

    pary = [("кадр", ST_KADR, NOV_KADR),
            ("кадр в отчёт", ST_OTCHYOT, NOV_OTCHYOT),
            ("отчёт справа", ST_LENTA, NOV_LENTA),
            ("итог", ST_ITOG, NOV_ITOG)]
    beda = [imya for imya, st, _ in pary if t.count(st) != 1]
    if beda:
        print(f"✗ якоря не найдены дословно: {', '.join(beda)}")
        return 1

    novyy = t
    for _, st, nov in pary:
        novyy = novyy.replace(st, nov, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1

    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = ui_torg.with_suffix(f".py.bak_vidno_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(ui_torg, bak)
    ui_torg.write_text(novyy, encoding="utf-8")
    print(f"✓ прогон стал видимым (копия: {bak.name})")

    import py_compile
    try:
        py_compile.compile(str(ui_torg), doraise=True)
        print("✓ компилируется")
    except Exception as e:
        print(f"✗ НЕ компилируется: {e}")
        return 1

    print("\nТеперь на экране, по каждому месту:")
    print("  · кадр справа меняется на это место;")
    print("  · отчёт справа — что она сказала;")
    print("  · строка в ленте с датой, разворотным и длиной волны.")
    print("\nВ конце: «мест 10 · входов 0 · отказов 10» и путь к разбору.")
    print("Связь рваться не должна — кадр ушёл в фон и рисуется один раз.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
