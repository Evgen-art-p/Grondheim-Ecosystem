# -*- coding: utf-8 -*-
"""
odna_yama_i_stol.py — две правки после прогона 24.09 (осень 2024).

1. ВХОД ПО ОДНОЙ ЯМЕ. 08.10 Синди вошла LONG: цена 1.1008 → 1.09581,
   AO −0.0078 → −0.0072. Но на AO с 1 по 7 октября — одна сплошная яма,
   без горки между. Обе её точки — внутри этой одной ямы: дно и место,
   где яма начала выкарабкиваться. Город сказал: «после отката AO
   просто ползёт — второй ямки нет». Проверки края и экстремума
   промолчали — они срабатывают, только когда город нашёл пару.
   Теперь: если город не нашёл вообще никакой пары, потому что второй
   ямки (горки) нет, — вход не принимается. Синди получает: «между
   твоими точками AO не было отката — это одна яма, сравнивать нечего».
   Про номера волн — ни слова (слово Шефа: ей сейчас не до волн).
   Где пара есть — решает она, как раньше; толстая и тонкая линии
   не тронуты.

2. СТОЛ ЧИТАЛСЯ НЕДОПИСАННЫМ. «Повреждён trading_state.json — дефолт»:
   страница кабинета прочла стол в тот миг, когда прогон его писал, и
   увидела пустоту — стол сбросился, кнопка спряталась. Если бы в этот
   миг висела заявка или стояла позиция — она бы исчезла.
   Теперь стол пишется сперва во временный файл и подменяется одним
   махом — недописанным его не увидит никто. А если чтение всё же
   споткнулось, город пробует ещё пару раз, прежде чем сдаться.

Что правит: Биржа/ruki_treydera.py и Биржа/hooks.py.

Запуск: положить в корень репы, запустить. Копии `.bak_odna_yama`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "ODNA_YAMA_I_STOL_V1"
_EKS = '            # EKSTREMUM_NA_VHODE_V1 (слово Шефа 24.09: «цена не\n'
_ZAP_STAROE = (
    '    p.write_text(\n'
    '        json.dumps(tstate, ensure_ascii=False, indent=2), encoding="utf-8")\n'
    '    print(f"[STATE] 💾 стол сохранён'
)
_ZAP_NOVOE = (
    '    # ODNA_YAMA_I_STOL_V1: пишем во временный файл и подменяем одним\n'
    '    # махом — недописанного стола не увидит ни страница, ни прогон.\n'
    '    _tekst_st = json.dumps(tstate, ensure_ascii=False, indent=2)\n'
    '    _tmp_st = p.with_name(p.name + ".tmp")\n'
    '    try:\n'
    '        import os as _os_st, time as _time_st\n'
    '        _tmp_st.write_text(_tekst_st, encoding="utf-8")\n'
    '        for _k_st in range(10):\n'
    '            try:\n'
    '                _os_st.replace(_tmp_st, p)\n'
    '                break\n'
    '            except PermissionError:\n'
    '                _time_st.sleep(0.05)\n'
    '        else:\n'
    '            p.write_text(_tekst_st, encoding="utf-8")\n'
    '    except Exception:\n'
    '        p.write_text(_tekst_st, encoding="utf-8")\n'
    '    print(f"[STATE] 💾 стол сохранён'
)
_CHT_STAROE = (
    '    try:\n'
    '        return json.loads(p.read_text(encoding="utf-8"))\n'
    '    except (json.JSONDecodeError, OSError) as e:\n'
    '        print(f"[STATE] ⚠️  Повреждён {p.name} ({e}) — дефолт")\n'
)
_CHT_NOVOE = (
    '    # ODNA_YAMA_I_STOL_V1: споткнулись о недописанный — пробуем ещё.\n'
    '    import time as _time_ch\n'
    '    for _k_ch in range(3):\n'
    '        try:\n'
    '            return json.loads(p.read_text(encoding="utf-8"))\n'
    '        except (json.JSONDecodeError, OSError):\n'
    '            _time_ch.sleep(0.1)\n'
    '    try:\n'
    '        return json.loads(p.read_text(encoding="utf-8"))\n'
    '    except (json.JSONDecodeError, OSError) as e:\n'
    '        print(f"[STATE] ⚠️  Повреждён {p.name} ({e}) — дефолт")\n'
)
_YAMA = (
    '            # ODNA_YAMA_I_STOL_V1: город не нашёл вообще никакой пары,\n'
    '            # потому что второй ямки (горки) нет — AO после отката просто\n'
    '            # ползёт. Обе точки Синди тогда лежат в ОДНОЙ яме: дно и место,\n'
    '            # где яма выкарабкивается. Это не дивер — сравнивать нечего.\n'
    '            try:\n'
    '                _dd_y = locals().get("_d") or {}\n'
    '                _sl_y = str(_dd_y.get("slovami") or "")\n'
    '                _net_par = not (_dd_y.get("пары") or [])\n'
    '            except Exception:\n'
    '                _sl_y, _net_par = "", False\n'
    '            if _net_par and any(_s in _sl_y for _s in (\n'
    '                    "второй ямки нет", "второй горки нет",\n'
    '                    "второй ещё нет")):\n'
    '                _short_y = str(napravlenie).upper() == "SHORT"\n'
    '                _odna = "одна горка" if _short_y else "одна яма"\n'
    '                _dve = ("две горки с ямкой между ними" if _short_y\n'
    '                        else "две ямки с горкой между ними")\n'
    '                print(f"[ОДНА ЯМА] ✗ {symbol} {rabochiy_etazh} "\n'
    '                      f"{napravlenie}: второй ямки нет — вход не принят")\n'
    '                return ("Приказ НЕ отдан: между твоими точками AO не было "\n'
    '                        f"отката — это {_odna}, сравнивать нечего. Город: «"\n'
    '                        + _sl_y.strip() + "». Дивер — это " + _dve +\n'
    '                        ". Жди, когда AO откатится и появится вторая.")\n'
)
ZAMENY = {
    os.path.join("Биржа", "ruki_treydera.py"): [(_EKS, _YAMA + _EKS)],
    os.path.join("Биржа", "hooks.py"): [(_ZAP_STAROE, _ZAP_NOVOE),
                                        (_CHT_STAROE, _CHT_NOVOE)],
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
        bak = put + ".bak_odna_yama"
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
    print("  Вход по одной яме не принимается; стол пишется так, что недописанным его не прочесть.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
