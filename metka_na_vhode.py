# -*- coding: utf-8 -*-
# metka_na_vhode.py — на входе трейдер называет код с кадра.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python metka_na_vhode.py
#
# ═══ ЗАЧЕМ ═══
#
# Прогон 17.09, H4, 279 пробудов. Сторону хода трейдер читает верно —
# сверка полная: некрон BEAR → «цена росла» 23 из 23, некрон BULL →
# «цена падала» 31 из 31. Ни одной перепутанной. Канон в голове стоит.
#
# А стол рукой она взяла ТОЛЬКО 129 раз из 279. В остальных 150
# писала «дивергенция AO, приседающий бар» не посмотрев ни одной
# цифры. Слова верные, порядок верный, сторона верная — а под ними в
# половине случаев может не быть ничего.
#
# Проверить это нечем: кадр она вроде смотрит, но что именно на нём
# разглядела, никто не спрашивает.
#
# ═══ ЧЕМ ПРОВЕРЯЕМ ═══
#
# Контрольной меткой. Четыре знака в углу кадра, новые при каждой
# отрисовке. Их нет ни на столе, ни в задании, ни в памяти — ТОЛЬКО
# на картинке. Назвать можно, лишь посмотрев.
#
# До сих пор метка печаталась в лог и забывалась. Город её не помнил,
# сверять было не с чем, и вопрос трейдеру не задавался ни разу.
#
# ═══ ЧТО СТАВИМ ═══
#
# 1. ГРАФИКА ПОМНИТ. Последние коды по каждой паре и этажу остаются в
#    памяти (по 12 штук — за один взгляд кадр рисуется несколько раз,
#    и трейдер мог смотреть не самый последний).
#
# 2. РУКА СВЕРЯЕТ. У приказа появляется поле «метка». На ENTER рука
#    сравнивает названное с тем, что было на кадрах, и пишет в лог:
#        [МЕТКА] ✓ EURUSD H4: назвала LM42 — на кадре была
#        [МЕТКА] ✗ EURUSD H4: назвала AB12 — на кадрах: LM42, PS78
#        [МЕТКА] ∅ EURUSD H4: метка не названа
#
# 3. ЗАДАНИЕ ПРОСИТ. В последнем блоке, рядом с рукой, сказано: на
#    ENTER назови код из угла кадра.
#
# ВХОД НЕ БЛОКИРУЕТСЯ. Не назвала или назвала мимо — приказ всё равно
# принимается. Это замер, а не запрет: сперва узнаем, сколько входов
# сделано глазами, и только потом решим, что с этим делать.
#
# БЕЗОПАСНО. Правит три файла, готовит все и пишет, только если
# сошлись все. Рядом кладёт копии.
# Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER = "METKA_NA_VHODE_V1"

# ── 1. графика помнит коды ──
G_STAROE = (
    '        _chey = f"{symbol} {timeframe}".strip() or "?"\n'
    "        print(f'[КАДР] контрольная метка: {_kod} · {_chey}')\n"
)
G_NOVOE = (
    '        _chey = f"{symbol} {timeframe}".strip() or "?"\n'
    "        print(f'[КАДР] контрольная метка: {_kod} · {_chey}')\n"
    '        # METKA_NA_VHODE_V1: запоминаем код, иначе сверять ответ\n'
    '        # трейдера не с чем. Держим последние 12 на пару и этаж:\n'
    '        # за один взгляд кадр рисуется несколько раз, и смотреть\n'
    '        # он мог не самый последний.\n'
    '        _spisok = METKI_KADROV.setdefault(_chey, [])\n'
    '        _spisok.append(_kod)\n'
    '        del _spisok[:-12]\n'
)

G_TOP_STAROE = "BAROV_V_KADRE = 140\n"
G_TOP_NOVOE = (
    "BAROV_V_KADRE = 140\n"
    "\n"
    "# METKA_NA_VHODE_V1: контрольные метки последних кадров, по паре\n"
    "# и этажу. Метка есть ТОЛЬКО на картинке — ни на столе, ни в\n"
    "# знаниях. Назвал её трейдер — значит смотрел.\n"
    "METKI_KADROV: dict = {}\n"
    "\n"
    "\n"
    "def metki_kadrov(chey: str) -> list:\n"
    '    """Коды последних кадров для пары и этажа, например "EURUSD H4"."""\n'
    "    return list(METKI_KADROV.get(str(chey).strip(), []))\n"
)

# ── 2. поле метки в схеме руки ──
R_SHEMA_STAROE = (
    '                "лот": {"type": "number", "description": "объём, если знаешь"},\n'
)
R_SHEMA_NOVOE = (
    '                "лот": {"type": "number", "description": "объём, если знаешь"},\n'
    '                # METKA_NA_VHODE_V1: код из угла кадра. Проверка\n'
    '                # зрения: его нет ни на столе, ни в знаниях.\n'
    '                "метка": {"type": "string",\n'
    '                          "description": ("код из левого верхнего угла "\n'
    '                                          "кадра — две буквы и две цифры. "\n'
    '                                          "На ENTER назови обязательно: "\n'
    '                                          "это доказательство, что ты "\n'
    '                                          "смотрел картинку, а не "\n'
    '                                          "вспоминал правило")},\n'
)

# ── 3. сверка при входе ──
R_STAROE = (
    '            if net:\n'
    '                return ("Приказ НЕ отдан: не хватает " + ", ".join(net) +\n'
    '                        ". Войти вслепую нельзя — назови и позови снова.")\n'
)
R_NOVOE = (
    '            if net:\n'
    '                return ("Приказ НЕ отдан: не хватает " + ", ".join(net) +\n'
    '                        ". Войти вслепую нельзя — назови и позови снова.")\n'
    '            # METKA_NA_VHODE_V1: сверяем код с кадра. Вход НЕ\n'
    '            # блокируем — это замер, а не запрет: сперва узнаем,\n'
    '            # сколько входов сделано глазами, потом решим.\n'
    '            try:\n'
    '                import grafik as _gr\n'
    '                _chey = f"{symbol} {timeframe}".strip()\n'
    '                _byli = _gr.metki_kadrov(_chey)\n'
    '                _skazala = str(args.get("метка") or "").strip().upper()\n'
    '                if not _skazala:\n'
    '                    print(f"[МЕТКА] ∅ {_chey}: метка не названа")\n'
    '                elif _skazala in _byli:\n'
    '                    print(f"[МЕТКА] ✓ {_chey}: назвала {_skazala} — "\n'
    '                          f"на кадре была")\n'
    '                else:\n'
    '                    print(f"[МЕТКА] ✗ {_chey}: назвала {_skazala} — "\n'
    '                          f"на кадрах: {\', \'.join(_byli[-4:]) or \'—\'}")\n'
    '            except Exception as _e_mk:\n'
    '                print(f"[МЕТКА] сверить не вышло ({_e_mk}) — не беда")\n'
)

# ── 4. задание просит назвать ──
M_STAROE = (
    '        "Рассказ этим JSON, решение — рукой. Оба, каждый раз."\n'
)
M_NOVOE = (
    '        "Рассказ этим JSON, решение — рукой. Оба, каждый раз.\\n"\n'
    '        # METKA_NA_VHODE_V1: проверка зрения. Кода нет ни на\n'
    '        # столе, ни в знаниях — только на картинке.\n'
    '        "\\nИ НА ВХОДЕ — МЕТКА. В левом верхнем углу кадра стоит "\n'
    '        "код: две буквы и две цифры. Отдавая ENTER, положи его в "\n'
    '        "поле «метка». Это не формальность: кода нет ни на столе, "\n'
    '        "ни в твоих знаниях — назвать его можно, только посмотрев "\n'
    '        "на картинку. Не разглядел — так и скажи, но не выдумывай."\n'
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti(pryamo, imya, primeta=None):
    if pryamo.exists():
        return pryamo
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nashlos = [p for p in KOREN.rglob(imya)
               if not any(m in str(p) for m in musor)
               and (primeta is None or primeta in str(p))]
    if len(nashlos) == 1:
        return nashlos[0]
    if len(nashlos) > 1:
        print(f"Нашёл несколько {imya}:")
        for nomer, p in enumerate(nashlos, 1):
            print(f"  {nomer}. {p}")
        otvet = input("Какой правим? номер: ").strip()
        if otvet.isdigit() and 1 <= int(otvet) <= len(nashlos):
            return nashlos[int(otvet) - 1]
    return None


def podgotovit(put, pravki):
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        return None, "уже сделано"
    for nomer, (staroe, _) in enumerate(pravki, 1):
        if tekst.count(staroe) != 1:
            return None, (f"правка {nomer}: нашёл {tekst.count(staroe)} "
                          f"мест вместо одного")
    novyy = tekst
    for staroe, novoe in pravki:
        novyy = novyy.replace(staroe, novoe, 1)
    try:
        ast.parse(novyy)
    except SyntaxError as beda:
        return None, f"после правки файл поломался (строка {beda.lineno})"
    return novyy, ""


def main():
    grafik = nayti(KOREN / "Биржа" / "grafik.py", "grafik.py")
    ruki = nayti(KOREN / "Биржа" / "ruki_treydera.py", "ruki_treydera.py")
    mozg = nayti(KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха"
                 / "торговый_хаос" / "слоты" / "A06" / "мозг.py",
                 "мозг.py", "A06")
    if not (grafik and ruki and mozg):
        print("✗ не нашёл grafik.py, ruki_treydera.py или мозг A06 —")
        print("  запускай из корня репозитория")
        return 1

    g, gb = podgotovit(grafik, [(G_TOP_STAROE, G_TOP_NOVOE),
                                (G_STAROE, G_NOVOE)])
    r, rb = podgotovit(ruki, [(R_SHEMA_STAROE, R_SHEMA_NOVOE),
                              (R_STAROE, R_NOVOE)])
    m, mb = podgotovit(mozg, [(M_STAROE, M_NOVOE)])

    if gb == rb == mb == "уже сделано":
        print("· уже сделано")
        return 0
    for imya, beda in (("grafik.py", gb), ("ruki_treydera.py", rb),
                       ("мозг A06", mb)):
        if beda and beda != "уже сделано":
            print(f"✗ {imya}: {beda}")
            print("  Ничего не тронул ни в одном файле.")
            return 1

    for put, novyy in ((grafik, g), (ruki, r), (mozg, m)):
        if novyy is None:
            continue
        kopiya = put.with_suffix(put.suffix + ".bak_metka_vhod")
        if not kopiya.exists():
            shutil.copy2(put, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        put.write_text(novyy, encoding="utf-8")

    print("✓ метка спрашивается на входе:")
    print("    · графика помнит последние 12 кодов на пару и этаж")
    print("    · у приказа появилось поле «метка»")
    print("    · рука сверяет и пишет [МЕТКА] ✓ / ✗ / ∅")
    print("    · вход НЕ блокируется — это замер, не запрет")
    print()
    print("Перезапусти Кабинет (main.py) и запусти прогон.")
    print("Потом посчитай в логе строчки [МЕТКА]: сколько ✓, сколько ✗")
    print("и сколько ∅. Это и будет ответ, сколько входов сделано глазами.")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
