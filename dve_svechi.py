# -*- coding: utf-8 -*-
"""
dve_svechi.py — разворот двумя свечами.

Слово Шефа 25.09: волны не зависят от того, как терминал режет бары, и
разворот может лечь на ДВЕ свечи — первая сделала край, вторая
закрылась в другую сторону. У Вильямса это тоже есть (свеча вверх и
рядом вниз), и поглощение как разворотная фигура. Это про ВХОД —
значит, первый уровень.

Проверено на месте, где она пропустила разворот: дневка, октябрьское
дно 2024 — одиночного разворотника нет, а 23+24 октября вместе дают
бычий разворотник ровно на дне, 1.07611. На H4 там же — 1.07671.
Таких мест, где одиночного разворотника нет, а двумя свечами есть:
дневка 2023–2025 — 32 (к 97 одиночным), H4 2025 — 54 (к 205).

Что делает:
  1. Биржа/council.py — если на этом баре одиночного разворотника нет,
     а две последние свечи вместе (открытие первой, закрытие второй,
     общий край) — разворотник по той же формуле, город будит:
     «разворот двумя свечами …: BULL @ 1.07611 — считай их одним
     разворотником». Если первая из двух сама была разворотником —
     не будит (её уже будили).
  2. Знания A06 и A07 (RAZVOROTNIK.md) — что это такое и что вход и
     стоп ставятся за края пары.
Все её условия остаются: дивер, приседающий в окне трёх баров,
экстремум. Проверка экстремума уже пускает вход на край бар-два назад,
если стоп за ним.

Запуск: положить в корень репы, запустить. Копии `.bak_dve_svechi`.
Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "DVE_SVECHI_V1"
_SL = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос", "слоты")

_HELPER = (
    '# DVE_SVECHI_V1 (слово Шефа 25.09): разворот двумя свечами. Волны\n'
    '# не зависят от того, как терминал режет бары: первая свеча сделала\n'
    '# край, вторая закрылась в другую сторону. Склеиваем их в одну\n'
    '# (открытие первой, закрытие второй, общий край) и проверяем той же\n'
    '# формулой разворотника.\n'
    'def _dve_svechi(bs, al) -> str:\n'
    '    try:\n'
    '        from williams_core import detect_necron_bar as _dnb\n'
    '        if not bs or len(bs) < 10:\n'
    '            return ""\n'
    '        J = list(al.get("jaw_series") or [])\n'
    '        T = list(al.get("teeth_series") or [])\n'
    '        L = list(al.get("lips_series") or [])\n'
    '        if len(J) < len(bs) or len(T) < len(bs) or len(L) < len(bs):\n'
    '            return ""\n'
    '        J, T, L = J[:len(bs)], T[:len(bs)], L[:len(bs)]\n'
    '        # первая из двух сама была разворотником — её уже будили\n'
    '        if _dnb(bs[:-1], J[:-1], T[:-1], L[:-1]).get("direction"):\n'
    '            return ""\n'
    '        a, b = bs[-2], bs[-1]\n'
    '        g = {"date": b.get("date"), "open": a["open"],\n'
    '             "high": max(a["high"], b["high"]),\n'
    '             "low": min(a["low"], b["low"]), "close": b["close"],\n'
    '             "volume": (a.get("volume") or 0) + (b.get("volume") or 0)}\n'
    '        r = _dnb(bs[:-2] + [g], J[:-2] + [J[-1]], T[:-2] + [T[-1]],\n'
    '                 L[:-2] + [L[-1]])\n'
    '        if not r.get("direction"):\n'
    '            return ""\n'
    '        return (f"разворот двумя свечами {str(a.get(\'date\'))[:16]} + "\n'
    '                f"{str(b.get(\'date\'))[:16]}: {r[\'direction\']} @ "\n'
    '                f"{r[\'price\']} — считай их одним разворотником")\n'
    '    except Exception as _e_dv:\n'
    '        print(f"[КЛЮЧ] разворот двумя свечами не посчитался: {_e_dv}")\n'
    '        return ""\n'
    '\n'
    '\n'
)
_POSLE = '        # PRISEDANIE_POSLE_V1 (слово Шефа: окно три бара — и до, и\n'

_RAZV_A = '<!-- TRI_BARA_V2 -->\n'
_RAZV_B = _RAZV_A + (
    '\n'
    '<!-- DVE_SVECHI_V1 -->\n'
    '**Разворот двумя свечами.** Терминал режет время на бары, а рынку до\n'
    'этого дела нет: разворот может лечь на две свечи — первая сделала\n'
    'край, вторая закрылась в другую сторону. Склей их мысленно в одну:\n'
    'открытие первой, закрытие второй, край — общий. Если вместе они —\n'
    'разворотник, это разворотник. Вход и стоп — за края пары, как за края\n'
    'одного бара. Остальное как всегда: дивер, приседающий в окне, край\n'
    'хода. Город разбудит словами «разворот двумя свечами».\n'
)


def _razv(slot):
    return (os.path.join(_SL, slot, "знания", "RAZVOROTNIK.md"),
            [(_RAZV_A, _RAZV_B)])


ZAMENY = dict([
    (os.path.join("Биржа", "council.py"), [
        ('\ndef _povod_vzglyada(', '\n' + _HELPER + 'def _povod_vzglyada('),
        (_POSLE,
         '        # DVE_SVECHI_V1: одиночного нет — может, разворот двумя свечами\n'
         '        elif _dve_svechi(bs, al):\n'
         '            povody.append(_dve_svechi(bs, al))\n'
         + _POSLE),
    ]),
    _razv("A06"),
    _razv("A07"),
])


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
        bak = put + ".bak_dve_svechi"
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
    print("  Разворот двумя свечами будит и считается разворотником.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
