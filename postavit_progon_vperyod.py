# -*- coding: utf-8 -*-
"""
postavit_progon_vperyod.py · MARKER: PROGON_VPERYOD_V1

СЛОВО ШЕФА (20.08)
──────────────────
«А в чём разница факта? Что на истории он есть, что на реале. Появилось,
наблюдает, дошло, вошла.»

Прав, и я это уже второй раз пропустил. Я сказал: наблюдение на истории
толком не проверить, потому что прогон прыгает через месяцы. Но прыгает
он не потому, что история такая — а потому, что я его таким сделал.
Факты в прошлом ровно те же, что и в живом городе: точка появилась,
трейдер наблюдает, картина дозрела, трейдер вошёл. Разницы нет никакой.

ЧТО БЫЛО
────────
Прогон вставал в кандидата, спрашивал трейдера один раз и прыгал к
следующему месту. Трейдер, которому родившаяся точка не его момент,
говорил «не мой вход» — и всё, что он увидел, пропадало. Тридцать мест
на двух инструментах, тридцать таких ответов.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Встав в место, прогон больше не прыгает сразу. Он спрашивает трейдера
и смотрит на его слово:

    трейдер не наблюдает  → идём к следующему месту, как раньше
    трейдер НАБЛЮДАЕТ     → шагаем ВПЕРЁД по одному бару и спрашиваем
                            снова, пока он наблюдает

Шаг — настоящий бар рабочего этажа (istoriya.shag), не календарный: в
выходные рынка нет. На каждом шаге курсор двигается, кадр
перерисовывается, стол пересобирается — трейдер видит, как картина
дозревает или рассыпается.

Наблюдение кончается словом самого трейдера: УХОЖУ или вход. Тогда
прогон идёт к следующему месту.

ГДЕ ГРАНИЦА
───────────
Шагаем, пока не упрёмся в дату СЛЕДУЮЩЕГО места (или в конец истории).
Это не выдуманное число баров, а естественный край: дальше начинается
следующая точка, и наблюдать старую уже не за чем.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не решает за трейдера, когда хватит наблюдать. Не гасит наблюдение при
сломе точки — по слову Шефа, трейдер увидит слом сам.

ПРО ДЕНЬГИ, ЧЕСТНО
──────────────────
Каждый шаг вперёд — это взгляд, то есть оплаченный вызов модели. Место,
за которым трейдер следит двадцать баров, стоит двадцать взглядов, а не
один. Ставь на первую пробу три-пять мест, а не пятнадцать.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Ставить ПОСЛЕ наблюдения — патч это проверит.
Запуск: py postavit_progon_vperyod.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_VPERYOD_V1"
NUZHEN = "NABLYUDENIE_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return (p / "Биржа" / "ui_torg.py").exists()


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


YAKOR = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()'''

NOV = '''                state["chat_history"].append({
                    "role": "assistant", "agent": _sl,
                    "content": skazal or "(без текста)"})
                update_chat_display()

                # ── PROGON_VPERYOD_V1 ────────────────────────
                # Слово Шефа: «в чём разница факта? что на истории он
                # есть, что на реале — появилось, наблюдает, дошло,
                # вошла». Прогон прыгал через месяцы не потому, что
                # история такая, а потому что я его таким сделал.
                # Теперь: трейдер взял на карандаш — шагаем ВПЕРЁД по
                # одному настоящему бару и спрашиваем снова, пока он
                # наблюдает. Граница — дата следующего места: дальше
                # начинается своя точка, старую наблюдать не за чем.
                _sled = None
                try:
                    _i_tek = mesta.index((data, _sl, _sym, _tf, k))
                    if _i_tek + 1 < len(mesta):
                        _sled = mesta[_i_tek + 1][0]
                except Exception:
                    _sled = None
                while True:
                    if state.get("stop_requested"):
                        break
                    try:
                        import hooks as _h
                        if not _h.nablyudenie(_sym, _tf, _sl):
                            break
                    except Exception as _en:
                        print(f"[ПРОГОН] наблюдение не прочлось: {_en}")
                        break
                    try:
                        _bylo = istoriya.gde_stoim()
                        _stalo = istoriya.shag(_tf, 1, _sym)
                    except Exception as _esh:
                        print(f"[ПРОГОН] шаг вперёд не вышел: {_esh}")
                        break
                    if not _stalo or _stalo == _bylo:
                        print("[ПРОГОН] история кончилась — иду дальше")
                        break
                    if _sled and _stalo >= _sled:
                        print("[ПРОГОН] дошёл до следующего места — "
                              "наблюдение закрываю")
                        try:
                            _h.snyat_nablyudenie(_sym, _tf, _sl,
                                                 "дошли до следующего места")
                        except Exception:
                            pass
                        break
                    state["chat_history"].append({
                        "role": "system",
                        "content": f"👁 {_stalo} · наблюдает {imya}"})
                    update_chat_display()
                    _kadr = None
                    try:
                        _kadr = await loop.run_in_executor(
                            None, lambda s=_sym, t=_tf: __import__(
                                "grafik").kadr(s, t))
                        pokazat_kadr(_kadr)
                    except Exception as _ek:
                        print(f"[ПРОГОН] кадр не нарисовался: {_ek}")
                    try:
                        itog = await loop.run_in_executor(None, _zvat)
                    except Exception as e:
                        print(f"[ПРОГОН] Совет сорвался на {_stalo}: {e}")
                        break
                    r = (itog.get("results") or {}).get(_sl) or {}
                    skazal = (r.get("narrative") or "").strip()
                    if not skazal and r.get("error"):
                        skazal = f"(промолчал: {r['error']})"
                    if _otchyot is not None:
                        try:
                            _otchyot.zapisat(k, _sl, imya, _sym, _tf, r,
                                             _kadr)
                        except Exception as _e:
                            print(f"[ОТЧЁТ] шаг не записался: {_e}")
                    state["chat_history"].append({
                        "role": "assistant", "agent": _sl,
                        "content": skazal or "(без текста)"})
                    update_chat_display()'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    if NUZHEN not in (koren / "Биржа" / "council.py").read_text(
            encoding="utf-8"):
        print("✗ Сперва накати postavit_nablyudenie.py — без третьего")
        print("  ответа трейдера шагать вперёд не за чем.")
        return 1
    if t.count(YAKOR) != 1:
        print(f"✗ якорь найден {t.count(YAKOR)} раз — жду ровно один")
        return 1

    novyy = t.replace(YAKOR, NOV, 1) + f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_vperyod_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ прогон умеет идти вперёд (копия: {bak.name})")
    print("\nВ ленте появится:")
    print("  👁 2025.11.19 08:00 · наблюдает Нина")
    print("  👁 2025.11.19 12:00 · наблюдает Нина")
    print("  ...пока она не скажет УХОЖУ или не войдёт")
    print("\nПРО ДЕНЬГИ: каждый шаг вперёд — оплаченный взгляд. Место,")
    print("за которым она следит двадцать баров, стоит двадцать взглядов.")
    print("На первую пробу ставь три-пять мест, не пятнадцать.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
