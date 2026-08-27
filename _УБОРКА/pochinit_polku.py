# -*- coding: utf-8 -*-
# MARKER: POLKA_NE_DUSHIT_SVYAZ_V1
"""
СВЯЗЬ ПЕРЕСТАЁТ РВАТЬСЯ ПРИ ОТКРЫТИИ КАБИНЕТА.

ЧТО БЫЛО СЛОМАНО
────────────────
Кабинет при постройке страницы собирает полку — список файлов из
test_data. Чтобы показать строчку «EURUSD H4 · 50110 баров · с … по …»,
он ЦЕЛИКОМ разбирал каждый файл: тридцать три файла, около полутора
миллионов баров, в главной нитке.

Видно прямо в логе Шефа при запуске:
    EURUSDH1.csv: 100012 баров
    GBPUSDM5.csv: 100000 баров
    XAUUSDM30.csv: 100000 баров
    ... и так тридцать три раза

Пока сервер это грыз, он не отвечал браузеру ни на что. Браузер ждёт
пару секунд и объявляет «Connection lost · Trying to reconnect». А
после переподключения страница строится ЗАНОВО — и всё по кругу.

Отсюда все три беды разом:
    · пустой экран (сервер молчит, ленту рисовать некому)
    · пузыри «не жмутся» — нажатие уходит на сервер (в логе видно
      «[ПУЗЫРЬ] нажали: A07»), но ответить некому, экран не отвечает
    · страница сама перезагружается

Терминал MT5 тут ни при чём — он ругался по своей причине, это
чинилось отдельно.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
Полке не нужны сами бары — ей нужны три числа: сколько баров, первая
дата, последняя. Теперь они берутся БЫСТРО, без разбора всего файла:
    · строки считаются кусками по мегабайту, без разбора цифр
    · первая дата — из первой строки
    · последняя — из хвоста файла (читаем последний кусок с конца)

Разбор миллиона чисел не делается вовсе. Открытие кабинета из
секунд превращается в мгновение, и связь не рвётся.

Если файл почему-то не поддаётся быстрому чтению — падаем на старый
полный разбор, чтобы полка не потеряла файл.

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ
───────────────────
Не трогает механику: точку, волну, откат, воду. Не трогает то, как
читаются бары для СЧЁТА — там по-прежнему полный честный разбор,
просто он делается для одного нужного файла, а не для всех сразу.

Идемпотентен. .bak рядом. Путь ищет сам.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "POLKA_NE_DUSHIT_SVYAZ_V1"


def _nayti_birzhu() -> Path:
    primety = ("ui_torg.py",)
    nashli = []
    korni = []
    for k in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if k not in korni:
            korni.append(k)
    for koren in korni:
        mesta = [koren]
        try:
            mesta += [x for x in koren.iterdir() if x.is_dir()]
        except OSError:
            pass
        for p in mesta:
            if all((p / f).exists() for f in primety) and p not in nashli:
                nashli.append(p)
    if len(nashli) == 1:
        return nashli[0]
    if not nashli:
        print("Не нашёл папку Биржа рядом со скриптом.")
        s = input("Перетащи сюда папку Биржа и нажми Enter:\n> ")
        p = Path(s.strip().strip('"').strip("'"))
        if (p / "ui_torg.py").exists():
            return p
        raise SystemExit("не та папка — там нет ui_torg.py")
    print("Нашёл несколько:")
    for i, p in enumerate(nashli, 1):
        print(f"  {i}. {p}")
    return nashli[int((input("которая? ").strip() or "1")) - 1]


BYSTRO_ST = 'def page_torg(tseh_id: str = "торговый_хаос") -> None:\n'
BYSTRO_NO = '\ndef _bystryy_pasport(p) -> dict:\n    """Три числа о файле БЕЗ разбора баров: сколько строк, первая\n    дата, последняя.\n\n    POLKA_NE_DUSHIT_SVYAZ_V1. Формат тот же, что читает read_mt5_csv:\n    MT5-выгруз в utf-16-le, поля через запятую, дата первым полем.\n\n    Строки считаем кусками по мегабайту — это чтение с диска и ничего\n    больше. Последнюю строку берём с ХВОСТА файла, не проходя его\n    целиком. Не вышло — возвращаем None, и зовущий разберёт файл\n    по-старому.\n    """\n    try:\n        razmer = p.stat().st_size\n        if razmer <= 0:\n            return None\n\n        KUSOK = 1 << 20          # мегабайт за раз\n        perevodov = 0\n        pervaya = b""\n        with open(p, "rb") as f:\n            kusok = f.read(KUSOK)\n            if not kusok:\n                return None\n            pervaya = kusok.split(b"\\n", 1)[0]\n            while kusok:\n                perevodov += kusok.count(b"\\n")\n                kusok = f.read(KUSOK)\n\n            # Хвост: последняя непустая строка. Кодировка utf-16-le —\n            # два байта на букву, поэтому и начало куска, и разбор\n            # должны идти по буквам, а не по байтам, иначе последняя\n            # дата читается мусором.\n            hvost_dlina = min(8192, razmer)\n            nachalo = razmer - hvost_dlina\n            if nachalo % 2:            # встать на границу буквы\n                nachalo += 1\n            f.seek(nachalo)\n            hvost = f.read(razmer - nachalo)\n\n        def _stroka_v_datu(syrye: bytes):\n            try:\n                s = syrye.decode("utf-16-le", errors="ignore")\n            except Exception:\n                return None\n            s = s.strip().lstrip("\\ufeff").strip("\\x00").strip()\n            if not s:\n                return None\n            chasti = s.split(",")\n            if len(chasti) < 6:\n                return None\n            data = chasti[0].strip()\n            # у настоящего бара дальше идут числа — проверяем одно\n            try:\n                float(chasti[1])\n            except (ValueError, IndexError):\n                return None\n            return data or None\n\n        do_konca = _stroka_v_datu(pervaya)\n\n        posle = None\n        try:\n            hvost_tekst = hvost.decode("utf-16-le", errors="ignore")\n        except Exception:\n            hvost_tekst = ""\n        for stroka in reversed(hvost_tekst.split("\\n")):\n            stroka = stroka.strip().lstrip("\\ufeff").strip("\\x00").strip()\n            if not stroka:\n                continue\n            chasti = stroka.split(",")\n            if len(chasti) < 6:\n                continue\n            try:\n                float(chasti[1])\n            except (ValueError, IndexError):\n                continue\n            posle = chasti[0].strip()\n            if posle:\n                break\n\n        if not do_konca or not posle:\n            return None\n\n        # строк с данными: переводы строк минус возможная пустая\n        # последняя. Точность до одной строки полке не важна, но\n        # заниженным числом пугать тоже не будем.\n        barov = max(1, perevodov)\n        return {"bars": barov, "date_from": do_konca, "date_to": posle}\n    except Exception as e:\n        print(f"[ПОЛКА] быстро не прочитал {getattr(p, \'name\', p)} ({e}) — "\n              f"разберу полностью")\n        return None\n\n\ndef page_torg(tseh_id: str = "торговый_хаос") -> None:\n'
YAKOR = '        if klyuch is not None and klyuch in _PASPORTA_KESH:\n            return dict(_PASPORTA_KESH[klyuch])\n        bars = read_mt5_csv(str(p))\n        if not bars:\n            return None\n        symbol, tf = _parse_symbol_tf(p.name)\n        _pasport = {\n            "name": p.name, "path": str(p), "symbol": symbol, "timeframe": tf,\n            "bars": len(bars), "date_from": bars[0].get("date", "?"), "date_to": bars[-1].get("date", "?"),\n        }\n'
NOVOE = '        if klyuch is not None and klyuch in _PASPORTA_KESH:\n            return dict(_PASPORTA_KESH[klyuch])\n\n        # POLKA_NE_DUSHIT_SVYAZ_V1: полке нужны ТРИ числа — сколько\n        # баров, первая дата, последняя. Раньше ради них разбирался\n        # ВЕСЬ файл, и на тридцати трёх файлах это было около полутора\n        # миллионов баров в главной нитке. Пока сервер их грыз, он не\n        # отвечал браузеру — тот рвал связь («Connection lost»), после\n        # переподключения страница строилась заново, и всё по кругу.\n        # Отсюда же пустой экран и «пузыри не жмутся»: нажатие до\n        # сервера доходит, а ответить некому.\n        #\n        # Считаем строки кусками, даты берём с двух концов файла.\n        # Ни одно число не разбирается. Не получилось — падаем на\n        # прежний полный разбор, чтобы файл не пропал с полки.\n        _bystro = _bystryy_pasport(p)\n        if _bystro is not None:\n            symbol, tf = _parse_symbol_tf(p.name)\n            _pasport = dict(_bystro)\n            _pasport.update({"name": p.name, "path": str(p),\n                             "symbol": symbol, "timeframe": tf})\n            if klyuch is not None:\n                _PASPORTA_KESH[klyuch] = dict(_pasport)\n            return _pasport\n\n        bars = read_mt5_csv(str(p))\n        if not bars:\n            return None\n        symbol, tf = _parse_symbol_tf(p.name)\n        _pasport = {\n            "name": p.name, "path": str(p), "symbol": symbol, "timeframe": tf,\n            "bars": len(bars), "date_from": bars[0].get("date", "?"), "date_to": bars[-1].get("date", "?"),\n        }\n'

PARY = [
    ("быстрый паспорт", BYSTRO_ST, BYSTRO_NO),
    ("разбор файла для полки", YAKOR, NOVOE),
]



def main():
    b = _nayti_birzhu()
    print(f"\nБиржа: {b}\n")
    p = b / "ui_torg.py"
    text = p.read_text(encoding="utf-8")

    if MARKER in text:
        print("  . ui_torg.py: уже накачен, пропускаю")
    else:
        novyy = text
        for nazv, staroe, novoe in PARY:
            if novyy.count(staroe) != 1:
                raise SystemExit(
                    f"  X ui_torg.py: якорь «{nazv}» не найден или не один "
                    f"({novyy.count(staroe)}). Файл НЕ ТРОНУТ.")
            novyy = novyy.replace(staroe, novoe)
        novyy = novyy.rstrip() + "\n\n# " + MARKER + " - marker\n"
        ast.parse(novyy)
        shutil.copy2(p, p.with_suffix(".py.bak_polka"))
        p.write_text(novyy, encoding="utf-8")
        print("  + ui_torg.py: полка больше не грызёт все файлы (.bak_polka рядом)")

    print("\nГотово. Перезапусти город (закрой окно python и запусти main.py).")
    print("При открытии кабинета в логе больше НЕ должно быть строк")
    print("«[CORE] 📂 ... баров» на все файлы подряд — только на тот,")
    print("по которому реально считают.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
