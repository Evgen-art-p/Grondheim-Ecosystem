# -*- coding: utf-8 -*-
"""
kray_i_shapka.py — две правки после прогона 24.09 14:08.

1. БОЛЬШОЙ КРАЙ НА ВХОДЕ (слово Шефа: «делай»). Два LONG на спуске
   09.07 и 14.07 — оба −1R. Приседающий был, а город оба раза сказал:
   «цена прежний край не взяла — откат ещё идёт» (июньское дно 1.14516
   далеко внизу). Правило она читает при каждом входе и всё равно
   обходит. Взяла ли цена прежний край — факт цены, не толкование AO.
   Теперь при ENTER: если сверка по большому ходу говорит «цена прежний
   край не взяла», вход не принимается, и Синди получает этот факт в
   ответ. Дивер по AO город по-прежнему только пишет в лог.

2. ШАПКА ОТЧЁТА СЧИТАЛА МЕСТА, А НЕ СДЕЛКИ. Цена входа стоит и на
   каждом месте ведения — одна сделка засчитывалась столько раз, сколько
   Синди её смотрела (SHORT +2.14R — шесть раз), и выходило +8.83R вместо
   +0.14R. И результат искался по цене входа во всём журнале за все
   прогоны — мог подхватиться чужой.
   Теперь каждая сделка — один раз, и только закрытия ЭТОГО прогона
   (по времени: от начала прогона до начала следующего).

Что правит: Биржа/ruki_treydera.py и Биржа/ui_otchyot.py.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет оба, потом пишет. Копии `.bak_kray_shapka`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "KRAY_I_SHAPKA_V1"

_SVERKA_KONEC = (
    '            except Exception as _e_sd:\n'
    '                print(f"[ДИВЕР] посчитать не вышло ({_e_sd}) — не беда")\n'
)
_ZHURNAL = '_ZHURNAL: dict = {}\n'
_VH = '                vh = z.get("entry")\n'
_STRANICA = '        mesta = _mesta(p)\n        _shapka(ceh, p, mesta)\n'
_RY = (
    '        _ry = []\n'
    '        for _m in mesta:\n'
    '            _r, _ = _itog_mesta(_m)\n'
    '            if _r is not None:\n'
    '                _ry.append(_r)\n'
)

ZAMENY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(
        _SVERKA_KONEC,
        _SVERKA_KONEC +
        '            # KRAY_I_SHAPKA_V1 (слово Шефа 24.09): большой край — факт\n'
        '            # цены. Пока цена не взяла прежний край большого хода, это\n'
        '            # откат внутри хода, и мелкий дивер в нём — не вход.\n'
        '            try:\n'
        '                _sl_k = str((locals().get("_d") or {}).get("slovami")\n'
        '                            or "")\n'
        '            except Exception:\n'
        '                _sl_k = ""\n'
        '            _bolshoy_k = _sl_k.split("||")[0]\n'
        '            if "цена прежний край не взяла" in _bolshoy_k:\n'
        '                print(f"[КРАЙ] ✗ {symbol} {rabochiy_etazh} "\n'
        '                      f"{napravlenie}: большой край не взят — вход не "\n'
        '                      f"принят")\n'
        '                return ("Приказ НЕ отдан: цена прежний край большого "\n'
        '                        "хода не взяла — откат ещё идёт. Город: «"\n'
        '                        + _bolshoy_k.strip() + "». Пока цена не взяла "\n'
        '                        "большой край, это откат внутри хода, и мелкий "\n'
        '                        "дивер в нём — не вход. Жди, когда цена возьмёт "\n'
        '                        "край, или реши снова.")\n',
    )],
    os.path.join("Биржа", "ui_otchyot.py"): [
        (_ZHURNAL,
         _ZHURNAL +
         '# KRAY_I_SHAPKA_V1: окно времени открытого прогона — [с, по).\n'
         '# Закрытия берём только из него, чтобы не подхватить чужой прогон.\n'
         '_OKNO: list = [None, None]\n'),
        (_VH,
         '                # KRAY_I_SHAPKA_V1: только закрытия этого прогона\n'
         '                if _OKNO[0] is not None:\n'
         '                    try:\n'
         '                        from datetime import datetime as _dtz\n'
         '                        _tsz = _dtz.fromisoformat(\n'
         '                            str(z.get("ts") or "")[:19])\n'
         '                    except Exception:\n'
         '                        continue\n'
         '                    if _tsz < _OKNO[0] or (_OKNO[1] is not None\n'
         '                                           and _tsz >= _OKNO[1]):\n'
         '                        continue\n'
         + _VH),
        (_STRANICA,
         '        mesta = _mesta(p)\n'
         '        # KRAY_I_SHAPKA_V1: окно прогона — от его начала до начала\n'
         '        # следующего (имена папок — время старта).\n'
         '        try:\n'
         '            from datetime import datetime as _dtk\n'
         '            _ik = vse.index(p)\n'
         '            _OKNO[0] = _dtk.strptime(p.name[:15], "%Y%m%d_%H%M%S")\n'
         '            _OKNO[1] = (_dtk.strptime(vse[_ik - 1].name[:15],\n'
         '                                      "%Y%m%d_%H%M%S")\n'
         '                        if _ik > 0 else None)\n'
         '        except Exception:\n'
         '            _OKNO[0] = _OKNO[1] = None\n'
         '        _ZHURNAL.clear()\n'
         '        _shapka(ceh, p, mesta)\n'),
        (_RY,
         '        # KRAY_I_SHAPKA_V1: каждая СДЕЛКА один раз. Цена входа стоит\n'
         '        # и на местах ведения — раньше одна сделка шла в счёт столько\n'
         '        # раз, сколько её смотрели.\n'
         '        _ry = []\n'
         '        _uzhe = set()\n'
         '        for _m in mesta:\n'
         '            _c = _m.get("цена_входа")\n'
         '            if not isinstance(_c, (int, float)):\n'
         '                continue\n'
         '            _k = round(float(_c), 5)\n'
         '            if _k in _uzhe:\n'
         '                continue\n'
         '            _r, _ = _itog_mesta(_m)\n'
         '            if _r is not None:\n'
         '                _uzhe.add(_k)\n'
         '                _ry.append(_r)\n'),
    ],
}


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if all(os.path.isfile(os.path.join(papka, p))
                        for p in ZAMENY) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass
    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]
    otv = input("Не нашёл репу. Перетащи сюда папку репы и нажми Enter: ")
    otv = otv.strip().strip('"').strip("'")
    return godnyy(otv) if otv else None


def main():
    repa = nayti()
    if not repa:
        print("✗ Репу не нашёл. Ничего не менял.")
        return
    gotovo = []
    for otn, zameny in ZAMENY.items():
        put = os.path.join(repa, otn)
        with open(put, "rb") as f:
            syroe = f.read()
        crlf = b"\r\n" in syroe
        tekst = syroe.decode("utf-8").replace("\r\n", "\n")
        if METKA in tekst:
            print(f"· {otn}: уже стоит")
            continue
        novyy = tekst
        for staroe, novoe in zameny:
            if novyy.count(staroe) != 1:
                print(f"✗ {otn}: не нашлось место правки — пришли Брату "
                      f"этот файл.\n  Ничего не менял.")
                return
            novyy = novyy.replace(staroe, novoe)
        if otn.endswith(".py"):
            ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_kray_shapka"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            if put.endswith(".py"):
                py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Вход без взятого большого края не принимается; шапка отчёта считает каждую сделку один раз.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
