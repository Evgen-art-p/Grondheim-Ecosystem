# -*- coding: utf-8 -*-
"""
postavit_vremya_i_sessii.py · MARKER: VREMYA_GORODA_V1

ЧТО ЭТО
───────
Слово Шефа: «время при запуске терминальное, пояс москва, лучше
автоматическая настройка, но сессии писать должен где-нибудь текстом
в кабинете в хедере... потом город привяжем ко времени».

Сейчас у Биржи времени нет вовсе. Часы есть у машины, у брокера свои
(его сервер почти никогда не UTC), а сессии посчитаны в
`Биржа/kalibrovka.py` по UTC — и этот файл кодом никто не зовёт.
Получается: в кабинете не видно ни который час на рынке, ни какая
сессия идёт.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Кладёт `Биржа/vremya.py` — одни часы на весь город:

   * пояс сервера ОПРЕДЕЛЯЕТСЯ САМ: спрашиваем у терминала время
     последнего тика и сравниваем с настоящим UTC. Разница, округлённая
     до получаса, и есть сдвиг брокера. Руками ничего не вбивается —
     сменил брокера, часы подстроились;
   * определяется ОДИН РАЗ при запуске и держится (сдвиг брокера за
     день не гуляет, кроме перевода часов; есть `zabyt()`, чтобы
     пересчитать);
   * терминала нет (Linux, сервер сборки, MT5 не поставлен) — часы не
     врут и не выдумывают: честно говорят «сервер не спросили»,
     показывают МСК по системным часам и помечают это словом;
   * МСК = UTC+3 круглый год, перевода часов в России нет.

2. Сессии берёт из `kalibrovka.py`, а НЕ переписывает своей таблицей.
   Вторая правда о том, когда открыта Европа, городу не нужна. Если
   таблица там поменяется — поменяется и в хедере.

3. В хедер кабинета ставит строку и обновляет её раз в полминуты:

       🕒 МСК 17:04 · сервер 16:04 (UTC+2) · Европа + Америка

   Рынок спит — так и написано. Часы по системным — рядом честная
   пометка, чтобы не принять их за терминальные.

Дальше на эти же часы сядет город, когда будем привязывать его ко
времени: `vremya.seychas()` — одна дверь, второй не заводим.

БЕЗОПАСНОСТЬ
────────────
Идемпотентен (маркер), .bak рядом, ast.parse и py_compile до записи,
корень ищет сам. Терминал открывает и закрывает ровно так же, как
`mt5_feed._fetch` — initialize/shutdown в одном месте, чужую сессию
не держит.

Запуск: двойной щелчок или  py postavit_vremya_i_sessii.py
        py postavit_vremya_i_sessii.py --suho
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "VREMYA_GORODA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
            and (p / "Биржа" / "kalibrovka.py").exists()
            and (p / "main.py").exists())


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


VREMYA_PY = '''# -*- coding: utf-8 -*-
# VREMYA_GORODA_V1
"""
ЧАСЫ ГОРОДА — одни на всех.

ЗАКОН ЭТОГО ФАЙЛА
    Время на рынке не совпадает ни с часами машины, ни с UTC: у
    брокера свой сервер, и его пояс — не наше дело выбирать, а наше
    дело УЗНАТЬ. Поэтому здесь ничего не настраивается руками.
    Спросили терминал один раз при запуске — дальше знаем.

    Сессии живут в kalibrovka.py. Здесь их НЕ переписываем: город
    не должен иметь двух мнений о том, когда открыта Европа.
"""
from __future__ import annotations

import sys as _sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

MSK = timezone(timedelta(hours=3))      # Москва круглый год, перевода нет

# Узнанный сдвиг сервера от UTC, в часах. None — ещё не спрашивали.
_SDVIG: float | None = None
_OTKUDA: str = ""


def zabyt():
    """Забыть узнанное — спросим терминал заново (перевод часов,
    сменили брокера, подняли терминал позже города)."""
    global _SDVIG, _OTKUDA
    _SDVIG, _OTKUDA = None, ""


def _sprosit_terminal() -> tuple:
    """(сдвиг в часах, откуда). Терминала нет — (None, причина).

    Как узнаём: берём время последнего тика по любому живому
    инструменту. Терминал отдаёт его в СВОЁМ времени, а часы машины
    знают настоящий UTC. Разница между ними и есть пояс брокера.
    Округляем до получаса — поясов в дробных минутах не бывает, а
    задержка тика на секунды не должна двигать ответ.
    """
    try:
        from mt5_feed import _terminal
        mt5 = _terminal()
    except Exception as e:
        return None, f"MetaTrader5 не импортируется ({e})"
    if mt5 is None:
        return None, "MetaTrader5 не установлен"
    if not mt5.initialize():
        return None, "терминал не отвечает"
    try:
        vse = mt5.symbols_get() or []
        imena = [s.name for s in vse if getattr(s, "visible", False)]
        if not imena:
            imena = [s.name for s in vse][:5]
        for imya in imena[:10]:
            tick = mt5.symbol_info_tick(imya)
            t = getattr(tick, "time", 0) if tick else 0
            if not t:
                continue
            seychas_utc = datetime.now(timezone.utc).timestamp()
            chasov = (float(t) - seychas_utc) / 3600.0
            # получас — самая мелкая единица поясов
            sdvig = round(chasov * 2) / 2
            if -14 <= sdvig <= 14:
                return sdvig, f"терминал ({imya})"
        return None, "терминал на связи, но тиков не отдал"
    except Exception as e:
        return None, f"сбой опроса ({e})"
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def sdvig_servera() -> tuple:
    """(сдвиг в часах или None, откуда узнали). Спрашиваем ОДИН раз."""
    global _SDVIG, _OTKUDA
    if _SDVIG is None and not _OTKUDA:
        _SDVIG, prichina = _sprosit_terminal()
        _OTKUDA = prichina if _SDVIG is None else prichina
        if _SDVIG is None:
            print(f"[ВРЕМЯ] ⚠️  сервер не спросили: {prichina}. "
                  f"Показываю МСК по часам машины.")
        else:
            znak = "+" if _SDVIG >= 0 else ""
            print(f"[ВРЕМЯ] 🕒 пояс сервера узнан сам: UTC{znak}{_SDVIG:g} "
                  f"({prichina})")
    return _SDVIG, _OTKUDA


def sessii_seychas(now_utc: datetime | None = None) -> list:
    """Какие сессии открыты прямо сейчас. Таблица — из kalibrovka."""
    now = now_utc or datetime.now(timezone.utc)
    try:
        import kalibrovka
        tablica = getattr(kalibrovka, "_SESSII", []) or []
    except Exception:
        return []
    h = now.hour
    return [s["имя"] for s in tablica
            if s.get("открытие", 0) <= h < s.get("закрытие", 0)]


def seychas() -> dict:
    """Одна дверь ко времени. Всё, что городу нужно знать про час.

    {utc, msk, server, сдвиг, откуда, терминальное (bool), сессии,
     строка}
    """
    utc = datetime.now(timezone.utc)
    sdvig, otkuda = sdvig_servera()
    server = utc + timedelta(hours=sdvig) if sdvig is not None else None
    idut = sessii_seychas(utc)
    return {
        "utc": utc,
        "msk": utc.astimezone(MSK),
        "server": server,
        "сдвиг": sdvig,
        "откуда": otkuda,
        "терминальное": sdvig is not None,
        "сессии": idut,
        "строка": stroka(),
    }


def stroka() -> str:
    """Строка для хедера кабинета. Коротко и без вранья."""
    utc = datetime.now(timezone.utc)
    msk = utc.astimezone(MSK)
    sdvig, otkuda = sdvig_servera()
    kuski = [f"МСК {msk:%H:%M}"]
    if sdvig is not None:
        server = utc + timedelta(hours=sdvig)
        znak = "+" if sdvig >= 0 else ""
        kuski.append(f"сервер {server:%H:%M} (UTC{znak}{sdvig:g})")
    else:
        kuski.append("сервер не спросили")
    idut = sessii_seychas(utc)
    kuski.append(" + ".join(idut) if idut else "рынок спит")
    return "🕒 " + " · ".join(kuski)


if __name__ == "__main__":
    d = seychas()
    print(d["строка"])
    print(f"  UTC:    {d['utc']:%Y-%m-%d %H:%M}")
    print(f"  МСК:    {d['msk']:%Y-%m-%d %H:%M}")
    print(f"  сервер: "
          + (f"{d['server']:%Y-%m-%d %H:%M}" if d["server"] else "—"))
    print(f"  откуда: {d['откуда'] or '—'}")
    print(f"  сессии: {', '.join(d['сессии']) or 'рынок спит'}")

# VREMYA_GORODA_V1 - marker
'''

# ── якорь в хедере: строка состава, перед выбором модели ──
YAKOR_UI = '''                with ui.element("div").style(
                    "margin-right:10px; background:rgba(255,255,255,0.06); "
                    "border:1px solid rgba(255,255,255,0.12); border-radius:10px;"
                ):'''

VSTAVKA_UI = '''                # VREMYA_GORODA_V1: часы и сессия — текстом, всегда на
                # виду. Пояс сервера город узнаёт сам у терминала, руками
                # ничего не вбивается. Сессии берутся из kalibrovka —
                # второй правды о рынке не заводим.
                vremya_ref["element"] = ui.label("").style(
                    "color:rgba(139,233,253,0.75); font-size:11px; "
                    "letter-spacing:0.05em; margin-right:14px; "
                    "white-space:nowrap;")

                def _vremya_obnovit():
                    try:
                        import vremya
                        if vremya_ref["element"]:
                            vremya_ref["element"].text = vremya.stroka()
                    except Exception:
                        pass

                _vremya_obnovit()
                ui.timer(30.0, _vremya_obnovit)

''' + YAKOR_UI

YAKOR_REF = '''    viewer_ref:   dict[str, Any] = {"element": None}'''
VSTAVKA_REF = YAKOR_REF + '''
    vremya_ref:   dict[str, Any] = {"element": None}   # VREMYA_GORODA_V1'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    vremya = koren / "Биржа" / "vremya.py"
    ui_torg = koren / "Биржа" / "ui_torg.py"

    # ── 1. часы ──
    print("\n1. Часы города — Биржа/vremya.py")
    if vremya.exists() and MARKER in vremya.read_text(encoding="utf-8"):
        print("  · уже лежат — пропускаю")
    else:
        try:
            ast.parse(VREMYA_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if SUHO:
            print("  · готовы (сухой прогон, не пишу)")
        else:
            if vremya.exists():
                shutil.copy2(vremya, vremya.with_suffix(
                    f".py.bak_vremya_{datetime.now():%Y%m%d_%H%M%S}"))
            vremya.write_text(VREMYA_PY, encoding="utf-8")
            print("  ✓ положены")

    # ── 2. хедер кабинета ──
    print("\n2. Строка в хедере кабинета")
    tekst = ui_torg.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  · маркер уже стоит — пропускаю")
    else:
        beda = ""
        if tekst.count(YAKOR_REF) != 1:
            beda = f"якорь ссылок найден {tekst.count(YAKOR_REF)} раз"
        elif tekst.count(YAKOR_UI) != 1:
            beda = f"якорь хедера найден {tekst.count(YAKOR_UI)} раз"
        if beda:
            print(f"  ✗ {beda} — жду ровно один. Кабинет правили, не трогаю.")
            return 1
        novyy = tekst.replace(YAKOR_REF, VSTAVKA_REF, 1)
        novyy = novyy.replace(YAKOR_UI, VSTAVKA_UI, 1)
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон, не пишу)")
        else:
            bak = ui_torg.with_suffix(
                f".py.bak_vremya_{datetime.now():%Y%m%d_%H%M%S}")
            shutil.copy2(ui_torg, bak)
            ui_torg.write_text(novyy, encoding="utf-8")
            print(f"  ✓ строка встала (копия: {bak.name})")

    if not SUHO:
        import py_compile
        for f in (vremya, ui_torg):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nПроверить часы отдельно, не поднимая города:")
        print("   py Биржа\\vremya.py")
        print("Терминал запущен — покажет его пояс и время сервера.")
        print("Не запущен — честно скажет, что сервер не спросили.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
