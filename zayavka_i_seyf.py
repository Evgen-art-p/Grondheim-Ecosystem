# -*- coding: utf-8 -*-
"""
zayavka_i_seyf.py — руки для висящей заявки и сейф только когда линии
в ряд.

Решения Шефа 23.09:

1. «Пусть она переставляет.» Пока заявка висит, у Синди не было рук:
   ENTER город отбивал («второй раз не входят»), MOVE_STOP и прочие —
   только для открытой позиции, WAIT заявку не трогает. 17.07 она
   написала «заявку не подтверждаю», а снять не могла — заявка дожила
   до 18.07 и сработала против её же мнения.
   Теперь две новые руки:
     MOVE_ORDER — переставить заявку (новые цена и стоп) на новый
                  разворотный бар;
     CANCEL     — снять заявку, передумала.
   Правило «второй раз в то же место не входят» остаётся: вторую
   заявку рядом не повесить, свою — двигать или убирать. Городской
   автопереезд по полному сигналу тоже остаётся.

2. «В болтанке почему стоп двигается?» Сейф тянул стоп за Зубы на
   ЛЮБОМ баре, где цена закрылась по нужную сторону линии, даже когда
   Аллигатор спал или смотрел в другую сторону. В болтанке Зубы идут
   посреди цены — стоп садился вплотную и его снимало следующим
   шевелением (07.07, 03.07, 18.07). Канон Котина: сейф работает, когда
   пасть открыта и линии в ряд.
   Теперь: стоп тянется за Зубами, только когда линии выстроились в
   сторону сделки и цена за ними (LONG: Губы > Зубы > Челюсть, цена
   выше Губ; SHORT — зеркально). Иначе стоп стоит, где его поставила
   Синди; двигать его в болтанке может только она сама (MOVE_STOP).

Что правит (все три файла вместе или ни одного):
  Биржа/ruki_treydera.py — руки MOVE_ORDER и CANCEL;
  GRONDHEIM_CITY/Биржа/цеха/контора/слоты/исполнитель/мозг.py —
      исполнитель переставляет или снимает висящую заявку;
  Биржа/hooks.py — сейф за Зубами только при линиях в ряд.

Запуск: положить в корень репы, запустить. Сам находит файлы, сперва
проверяет все три, потом пишет. Копии `.bak_zayavka_seyf`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ZAYAVKA_I_SEYF_V1"
RUKI = os.path.join("Биржа", "ruki_treydera.py")
ISPOLNITEL = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "контора",
                          "слоты", "исполнитель", "мозг.py")
HOOKS = os.path.join("Биржа", "hooks.py")

ZAMENY = {
    RUKI: [
        # 1. два новых слова
        ('_PRIKAZY = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE")\n',
         '# ZAYAVKA_I_SEYF_V1: MOVE_ORDER и CANCEL — руки для висящей заявки.\n'
         '_PRIKAZY = ("ENTER", "WAIT", "HOLD", "MOVE_STOP", "ADD", "CLOSE",\n'
         '            "MOVE_ORDER", "CANCEL")\n'),
        # 2. описание слова «что»
        ('                                        "MOVE_STOP, ADD и CLOSE сказать не "\n'
         '                                        "о чем.")},\n',
         '                                        "MOVE_STOP, ADD и CLOSE сказать не "\n'
         '                                        "о чем. "\n'
         '                                        "Висит ЗАЯВКА (ещё не сработала): "\n'
         '                                        "MOVE_ORDER — переставить её на "\n'
         '                                        "новый разворотный бар (новые цена "\n'
         '                                        "и стоп) · CANCEL — снять, "\n'
         '                                        "передумала · WAIT — оставить "\n'
         '                                        "висеть как есть. WAIT заявку НЕ "\n'
         '                                        "снимает.")},\n'),
        # 3. отказ второго ENTER — подсказать новые руки
        ('                        "стоп, ADD — долить к этой же позиции, "\n'
         '                        "CLOSE — закрыть.")\n',
         '                        "стоп, ADD — долить к этой же позиции, "\n'
         '                        "CLOSE — закрыть. Если это висящая заявка: "\n'
         '                        "MOVE_ORDER — переставить (новые цена и "\n'
         '                        "стоп), CANCEL — снять.")\n'),
        # 4. проверки новых рук
        ('        if chto == "MOVE_STOP" and not isinstance(args.get("новый_стоп"),\n',
         '        # ZAYAVKA_I_SEYF_V1: переставить или снять можно только\n'
         '        # свою висящую заявку.\n'
         '        if chto in ("MOVE_ORDER", "CANCEL"):\n'
         '            _moyo = _chto_u_menya_est()\n'
         '            if not _moyo.startswith("висящая заявка"):\n'
         '                return ("Приказ НЕ отдан: висящей заявки у тебя нет"\n'
         '                        + (f" (есть {_moyo})" if _moyo else "") +\n'
         '                        ". " + chto + " — только для заявки, которая "\n'
         '                        "ещё не сработала.")\n'
         '            if chto == "MOVE_ORDER":\n'
         '                _net = [p for p, z in (("цена", cena), ("стоп", stop))\n'
         '                        if not isinstance(z, (int, float))]\n'
         '                if _net:\n'
         '                    return ("Приказ НЕ отдан: MOVE_ORDER без "\n'
         '                            + ", ".join(_net) + ". Назови новые цену "\n'
         '                            "и стоп заявки и позови снова.")\n'
         '        if chto == "MOVE_STOP" and not isinstance(args.get("новый_стоп"),\n'),
        # 5. табло
        ('        if chto == "MOVE_STOP":\n'
         '            v["new_stop"] = args.get("новый_стоп")\n',
         '        if chto == "MOVE_STOP":\n'
         '            v["new_stop"] = args.get("новый_стоп")\n'
         '        if chto == "MOVE_ORDER":\n'
         '            v["entry"] = cena\n'
         '            v["stop"] = stop\n'),
        # 6. ответ руки
        ('        if chto == "WAIT":\n'
         '            return f"Принято: не работаешь на этом баре{\', \' + bar if bar else \'\'}."\n',
         '        if chto == "MOVE_ORDER":\n'
         '            return (f"Приказ отдан: {adresat} переставит заявку на "\n'
         '                    f"{cena}, стоп {stop}"\n'
         '                    + (f", бар {bar}" if bar else "") + ".")\n'
         '        if chto == "CANCEL":\n'
         '            return (f"Приказ отдан: {adresat} снимет заявку"\n'
         '                    + (f", бар {bar}" if bar else "") + ".")\n'
         '        if chto == "WAIT":\n'
         '            return f"Принято: не работаешь на этом баре{\', \' + bar if bar else \'\'}."\n'),
    ],
    ISPOLNITEL: [
        ('        magic = MAGIC[key]\n'
         '        pos = next((p for p in positions\n',
         '        magic = MAGIC[key]\n'
         '        # ZAYAVKA_I_SEYF_V1: рука для ВИСЯЩЕЙ заявки — переставить\n'
         '        # на новый разворотный бар или снять. Решает трейдер.\n'
         '        if action in ("MOVE_ORDER", "CANCEL"):\n'
         '            zv = next((p for p in positions\n'
         '                       if p.get("magic") == magic\n'
         '                       and p.get("status") == "PENDING"), None)\n'
         '            if not zv:\n'
         '                changed.append({"trader": TRADER_NAME[key],\n'
         '                                "action": action + "_REJECTED",\n'
         '                                "why": "висящей заявки нет"})\n'
         '                continue\n'
         '            if action == "CANCEL":\n'
         '                positions = [p for p in positions if p is not zv]\n'
         '                dirty = True\n'
         '                print(f"[ОРДЕР] 🚫 {zv.get(\'trader\')} "\n'
         '                      f"{zv.get(\'direction\')} @ {zv.get(\'entry\')} "\n'
         '                      f"СНЯТ — трейдер передумал")\n'
         '                changed.append({"trader": TRADER_NAME[key],\n'
         '                                "action": "CANCEL",\n'
         '                                "entry": zv.get("entry")})\n'
         '                continue\n'
         '            ne, ns = v.get("entry"), v.get("stop")\n'
         '            dz = (zv.get("direction") or "").upper()\n'
         '            if (not isinstance(ne, (int, float))\n'
         '                    or not isinstance(ns, (int, float))\n'
         '                    or (dz == "LONG" and not ns < ne)\n'
         '                    or (dz == "SHORT" and not ns > ne)):\n'
         '                print(f"[ОРДЕР] ✗ {zv.get(\'trader\')} {dz}: "\n'
         '                      f"переставить нельзя — вход {ne}, стоп {ns}")\n'
         '                changed.append({"trader": TRADER_NAME[key],\n'
         '                                "action": "MOVE_ORDER_REJECTED",\n'
         '                                "attempted": [ne, ns],\n'
         '                                "why": "нет цены/стопа или стоп не "\n'
         '                                       "по ту сторону от входа"})\n'
         '                continue\n'
         '            _bylo = (zv.get("entry"), zv.get("stop"))\n'
         '            zv["entry"] = ne\n'
         '            zv["stop"] = ns\n'
         '            zv["stop_initial"] = ns\n'
         '            if "entry_avg" in zv:\n'
         '                zv["entry_avg"] = ne\n'
         '            # опора для городского переезда и снятия — новый бар\n'
         '            zv["signal_start"] = ns\n'
         '            zv["entry_fractal_price"] = ns\n'
         '            zv["_ждёт_баров"] = 0\n'
         '            # на баре перестановки не срабатывает — как при рождении\n'
         '            zv["_ждёт_с"] = _tekushchiy_bar(tstate)\n'
         '            dirty = True\n'
         '            print(f"[ОРДЕР] 🔄 {zv.get(\'trader\')} {dz} ПЕРЕСТАВЛЕН "\n'
         '                  f"рукой: вход {_bylo[0]} → {ne}, стоп {_bylo[1]} → {ns}")\n'
         '            changed.append({"trader": TRADER_NAME[key],\n'
         '                            "action": "MOVE_ORDER",\n'
         '                            "from": list(_bylo), "to": [ne, ns]})\n'
         '            continue\n'
         '        pos = next((p for p in positions\n'),
    ],
    HOOKS: [
        ('    teeth = allig.get("teeth")\n',
         '    teeth = allig.get("teeth")\n'
         '    # ZAYAVKA_I_SEYF_V1: сейф — когда пасть открыта и линии в ряд.\n'
         '    _jaw = allig.get("jaw")\n'
         '    _lips = allig.get("lips")\n'),
        ('            if close < teeth:\n'
         '                continue\n',
         '            if close < teeth:\n'
         '                continue\n'
         '            # ZAYAVKA_I_SEYF_V1 (слово Шефа 23.09): в болтанке сейфа\n'
         '            # нет. Тянем, только когда линии в ряд вверх и цена\n'
         '            # над ними: Губы > Зубы > Челюсть, цена выше Губ.\n'
         '            if not (_lips is not None and _jaw is not None\n'
         '                    and _lips > teeth > _jaw and close > _lips):\n'
         '                if teeth > old:\n'
         '                    print(f"[ТРЕЙЛ] ⏸ {pos.get(\'trader\')} LONG: линии "\n'
         '                          f"не в ряд — болтанка, стоп стоит {old}")\n'
         '                continue\n'),
        ('            if close > teeth:\n'
         '                continue\n',
         '            if close > teeth:\n'
         '                continue\n'
         '            # ZAYAVKA_I_SEYF_V1: зеркально — Губы < Зубы < Челюсть,\n'
         '            # цена ниже Губ.\n'
         '            if not (_lips is not None and _jaw is not None\n'
         '                    and _lips < teeth < _jaw and close < _lips):\n'
         '                if teeth < old:\n'
         '                    print(f"[ТРЕЙЛ] ⏸ {pos.get(\'trader\')} SHORT: линии "\n'
         '                          f"не в ряд — болтанка, стоп стоит {old}")\n'
         '                continue\n'),
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
        ast.parse(novyy)
        gotovo.append((put, novyy, crlf))
    if not gotovo:
        print("✓ Всё уже стоит. Ничего не менял.")
        return
    for put, novyy, crlf in gotovo:
        bak = put + ".bak_zayavka_seyf"
        if not os.path.exists(bak):
            shutil.copy2(put, bak)
        with open(put, "wb") as f:
            f.write((novyy.replace("\n", "\r\n") if crlf else novyy)
                    .encode("utf-8"))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, put)
            print(f"✗ {put} не скомпилировался, вернул как было: {e}")
            return
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Заявку можно переставить (MOVE_ORDER) и снять (CANCEL); сейф "
          "за Зубами — только когда линии в ряд.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
