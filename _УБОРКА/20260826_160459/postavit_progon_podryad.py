# -*- coding: utf-8 -*-
"""
postavit_progon_podryad.py · MARKER: PROGON_PODRYAD_V1

СЛОВО ШЕФА (21.08)
──────────────────
«Есть история — прогнал, посмотрел РЕАЛЬНО, потому что там реальная
история. А у нас хуета: задом наперёд, отсеивает ещё. Мы что вообще
тестируем?»

Он прав. Тестировали искателя, а не рынок.

ЧТО БЫЛО
────────
Прогон работал так: искатель находил «места», прыгал по ним от свежих к
старым, половину отсеивал по рамке и по тренду — и город видел не
историю, а выборку из неё, собранную нашими же правилами. Проверить на
такой выборке нельзя ничего: она проверяет саму себя.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Прогон идёт по истории ПОДРЯД, бар за баром, как жил бы в реальности.

    с даты пусто → последний год истории
    с даты задан → с неё и до конца данных

На каждом баре город считает сам, молча и бесплатно: ведёт точку,
ищет конец волны, откат, двигает стопы, закрывает позиции. Трейдера
зовут ТОЛЬКО когда открылся ключ — родилась точка, кончилась волна,
кончился откат, или у него есть своя позиция.

Никакого искателя. Никакой рамки 100-140. Никакого отсева. Просто
история, как она была.

В конце — счёт: сколько баров пройдено, сколько раз будили, сколько
входов, чем кончились.

ПРО ЦЕНУ, ЧЕСТНО
────────────────
Год H4 — это около полутора тысяч баров. Считает их город сам, это
быстро и даром. Платим только за пробуждения: по замеру их выходит
несколько десятков за год. Если ключ вдруг откроется чаще, чем ждём, —
жми СТОП, прогон остановится.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_progon_podryad.py   (или --suho)
"""
import ast
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PROGON_PODRYAD_V1"
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


YAKOR = '''        # 1. код ищет места — бесплатно, поэтому ищем сразу всем
        mesta = []
        for _sl, _sym, _tf in rabotniki:
            try:
                # PROGON_S_DATY_V1: пусто — от сегодня, как было.
                spisok = await loop.run_in_executor(
                    None, lambda s=_sym, t=_tf: (
                        _kd.iskat(s, t, skolko=skolko, govorit=print,
                                  s_momenta=_ot_daty)   # POISK_S_DATY_V1
                        if _ot_daty else
                        _kd.iskat(s, t, skolko=skolko, govorit=print)))
            except Exception as e:
                print(f"[ПРОГОН] {_sl}: искать не вышло — {e}")
                continue
            for k in spisok:
                mesta.append((k.get("момент") or k.get("дата", ""),
                              _sl, _sym, _tf, k))'''

NOV = '''        # 1. PROGON_PODRYAD_V1: идём по истории ПОДРЯД, бар за баром.
        # Слово Шефа: «есть история — прогнал, посмотрел реально».
        # Раньше здесь работал искатель: прыгал по своим «местам» от
        # свежих к старым и половину отсеивал рамкой и трендом. Город
        # видел не историю, а выборку, собранную нашими же правилами, —
        # такая проверка проверяет только саму себя.
        #
        # Теперь: с даты пусто — последний год; задана — с неё до конца
        # данных. Каждый бар город считает сам, молча и даром. Трейдера
        # зовут только на открытом ключе.
        mesta = []
        for _sl, _sym, _tf in rabotniki:
            try:
                _vse = await loop.run_in_executor(
                    None, lambda s=_sym, t=_tf: istoriya._vse_bary(s, t))
            except Exception as e:
                print(f"[ПРОГОН] {_sl}: история не открылась — {e}")
                continue
            if not _vse:
                continue
            _daty = [b.get("date", "") for b in _vse]
            if _ot_daty:
                _s = next((j for j, d in enumerate(_daty)
                           if d >= _ot_daty), None)
                if _s is None:
                    print(f"[ПРОГОН] {_sl}: после {_ot_daty} баров нет")
                    continue
            else:
                # год назад: на H4 это около 1500 баров, на D1 — 250.
                # Берём по числу баров, а не по календарю: файл может
                # кончаться раньше сегодняшнего дня.
                _v_godu = {"MN1": 12, "W1": 52, "D1": 252, "H12": 500,
                           "H8": 750, "H4": 1500, "H1": 6000}.get(
                               str(_tf).upper(), 1500)
                _s = max(0, len(_daty) - _v_godu)
            _s = max(_s, 300)          # ядру нужно окно на разгон
            for j in range(_s, len(_daty)):
                mesta.append((_daty[j], _sl, _sym, _tf,
                              {"дата": _daty[j], "подряд": True}))
            print(f"[ПРОГОН] {_sl}: {_sym} {_tf} — "
                  f"{len(_daty) - _s} баров, "
                  f"с {_daty[_s]} по {_daty[-1]}")'''

# на баре подряд трейдера зовут только по ключу
YAKOR2 = '''                istoriya.postavit(data)'''

NOV2 = '''                istoriya.postavit(data)
                # PROGON_PODRYAD_V1: на сплошном ходу считаем сами и
                # смотрим ключ. Закрыт — идём дальше молча и даром.
                if k.get("подряд"):
                    try:
                        def _tiho(s=_sym, t=_tf, sl=_sl):
                            import hooks as _h2
                            _h2.rynok_novyy_bar(s, t)
                            return __import__("council")._klyuch_probuzhdeniya(
                                s, t, sl)
                        _kk = await loop.run_in_executor(None, _tiho)
                    except Exception as _ek:
                        print(f"[ПРОГОН] ключ не прочёлся: {_ek}")
                        _kk = {"будим": False}
                    if not _kk.get("будим"):
                        continue
                    k = dict(k)
                    k["почему"] = _kk.get("почему", "")'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")
    f = koren / "Биржа" / "ui_torg.py"
    t = f.read_text(encoding="utf-8")

    if MARKER in t:
        print("· маркер уже стоит — пропускаю")
        return 0
    for yakor in (YAKOR, YAKOR2):
        if t.count(yakor) != 1:
            print(f"✗ якорь найден {t.count(yakor)} раз — жду ровно один")
            print(f"  {yakor.strip().splitlines()[0][:70]}")
            return 1

    novyy = t.replace(YAKOR, NOV, 1).replace(YAKOR2, NOV2, 1)
    novyy += f"\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ после правки не разбирается: {e}")
        return 1
    if SUHO:
        print("· правка готова (сухой прогон)")
        return 0

    bak = f.with_suffix(f".py.bak_podryad_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(f, bak)
    f.write_text(novyy, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
    except Exception as e:
        shutil.copy2(bak, f)
        print(f"✗ НЕ компилируется ({e}) — откатил из {bak.name}")
        return 1
    print(f"✓ прогон идёт по истории подряд (копия: {bak.name})")
    print("\nТеперь ТЕСТЕР + пустая дата = последний год бар за баром.")
    print("Дата задана — с неё и до конца данных.")
    print("\nВ начале город скажет, сколько баров взял и с какого по какой.")
    print("Дальше молчит и считает, а трейдера зовёт только на событиях.")
    print("\nПоле «ловить» на сплошном ходу больше ни на что не влияет.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
