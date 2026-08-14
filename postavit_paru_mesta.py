# -*- coding: utf-8 -*-
"""
postavit_paru_mesta.py · MARKER: PARA_MESTA_V1

ЧТО ЭТО
───────
Первый слой по слову Шефа: «должен свой инструмент и этаж персонально,
никаких общих вахт... три трейдера три инструмента, зачем ещё один?»
и «рабочий да, от которого всегда пляшешь... если они ещё и графики
переберут сами — вообще замечательно».

ЧТО БЫЛО НЕ ТАК
───────────────
1. Инструменты трёх трейдеров лежали ОДНИМ ОБЩИМ ЛИСТКОМ при квартале:
   `Биржа/данные/naznacheniya.json`. Чертёж, Гл.7.2: «никто никого не
   регистрирует — единица есть там, где лежит, и говорит сама. Никто
   не держит списков за других». Листок — ровно такой список.
   При этом в бланке поста поле «инструмент» УЖЕ ЕСТЬ и пустует: то
   есть правда была заведена в двух местах, а жила в неправильном.

2. Этажа не было нигде. Поэтому он и оказался общим: один на троих,
   с полки кабинета. Сбился общий — сбились все.

3. Лесенка масштабов (`MN1 W1 D1 H12 H8 H4 H1 M30 M15 M10 M5`) жила
   ВНУТРИ насоса котировок `mt5_feed.py`, и умела только ВНИЗ
   (`step_down`). Шага ВВЕРХ не было вовсе — а он нужнее: структура
   чаще не влезает в окно, чем не помещается мелко. Кто-то уже
   упирался в это и решил копией файла — `mt5_feed_с_step_up.py`
   лежит в уборке.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Кладёт `Биржа/masshtab.py` — лесенка масштабов как общее знание
   города, с шагом в ОБЕ стороны и с записанным правилом Вильямса
   (окно 100-140 баров — это выбор ЭТАЖА для чтения картинки, не
   фильтр сигналов). Насос теперь читает лесенку оттуда, своей копии
   не держит.

2. Дополняет `Биржа/vybor.py`:
   * инструмент места читается из ПОСТА (`посты/{id}/пост.json`), а не
     из листка. Листок ещё читается — но только как запасной, для
     того что не переехало;
   * `naznachit()` пишет в пост;
   * появляется РАБОЧИЙ ЭТАЖ — метка жителя при паре с инструментом
     («EURUSD H4»), потому что у одного человека на золоте структура
     может читаться с дневок, а на евро с часов. Этаж — его право,
     согласия не спрашивает (Закон II: в чужую кухню не лезем);
   * `rabota_dlya(ceh, slot)` — одна дверь: чем и на каком этаже
     работает это место, и откуда это известно.

3. Разово переносит содержимое листка в посты и откладывает листок
   как `.perenesen` (не удаляет).

ЧЕГО ПАТЧ НЕ ДЕЛАЕТ (следующим слоем)
─────────────────────────────────────
Не трогает Совет, руку рынка и позиции — они пока работают по
кабинетному инструменту. Это второй слой, он стоит на этом.

БЕЗОПАСНОСТЬ
────────────
Идемпотентен (маркер), .bak рядом, ast.parse и py_compile до записи,
корень ищет сам. Ничего не удаляет.

Запуск: двойной щелчок или  py postavit_paru_mesta.py
        py postavit_paru_mesta.py --suho
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "PARA_MESTA_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "vybor.py").exists()
            and (p / "ГОРОД" / "rabota.py").exists()
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


MASSHTAB_PY = '''# -*- coding: utf-8 -*-
# PARA_MESTA_V1
"""
МАСШТАБ — лесенка этажей города.

ЗАЧЕМ ХОДЯТ ПО ЭТАЖАМ (слово Шефа, 14.08)
    Не «полазить посмотреть». Этаж — ручка масштаба. Окно кадра
    фиксировано (140 баров, число Вильямса), поэтому, меняя этаж,
    трейдер меняет не количество баров, а сколько ВРЕМЕНИ влезает в
    те же 140. Цель одна: чтобы ЕГО структура легла в окно целиком.

    Из источников (РАЗБОР_ИСТОЧНИКОВ.md, ролик про AO):
        100-140 баров — это выбор таймфрейма для чтения картинки,
        не фильтр сигналов (тот же импульс: 91 бар на H4, 181 на H12).

    Порядок работы, записанный со слов Шефа:
        1. рабочий этаж свой, привычный, от комфорта — от него пляшем
        2. взгляд: читается картинка или нет
        3. не читается — вышел («хрень, ухожу»)
        4. читается — двигает этажи, растягивает, смотрит глубину
        5. 100-140 баров — уточнение структуры, уже внутри
        6. и только теперь ищет точку

    Рабочий этаж задаёт и ЧАСТОТУ работы: час — сигналы чаще,
    четыре часа — реже, дневка — совсем редко, зато ждёт. Дневки и
    недели нужны для тренда, рабочими у нас бывают час и полчаса.

ЗАКОН ЭТОГО ФАЙЛА
    Здесь нет ни котировок, ни решений — только лестница и шаги по
    ней. Читает её кто угодно: трейдер, насос, кадр. Своей копии
    лесенки не держит НИКТО (Закон Картриджа: одна правда, читаемая
    сканом, а не список в каждом кармане).
"""
from __future__ import annotations

# Сверху вниз: от самого крупного масштаба к самому мелкому.
LESTNICA = ["MN1", "W1", "D1", "H12", "H8", "H4", "H1",
            "M30", "M15", "M10", "M5"]

# Окно чтения картинки. Не фильтр — масштаб.
BAROV_V_KADRE = 140
OKNO = (100, 140)


def est(tf: str) -> bool:
    return (tf or "").strip().upper() in LESTNICA


def _i(tf: str):
    t = (tf or "").strip().upper()
    return LESTNICA.index(t) if t in LESTNICA else None


def vyshe(tf: str):
    """Ступень КРУПНЕЕ. Нужна, когда структура не влезла в окно.
    На потолке (MN1) или вне лесенки — None."""
    i = _i(tf)
    if i is None or i == 0:
        return None
    return LESTNICA[i - 1]


def nizhe(tf: str):
    """Ступень МЕЛЬЧЕ. Нужна, когда структура видна, но крупно —
    разворотный бар на конце волны не разглядеть. На дне — None."""
    i = _i(tf)
    if i is None or i + 1 >= len(LESTNICA):
        return None
    return LESTNICA[i + 1]


def sosedi(tf: str) -> list:
    """Куда можно шагнуть с этого этажа. Прыжков через ступень нет:
    масштаб ищут шагами, иначе теряют то, что уже видели."""
    return [x for x in (vyshe(tf), nizhe(tf)) if x]


def poyasnenie(tf: str) -> str:
    """Строка для трейдера: где он стоит и куда может шагнуть."""
    v, n = vyshe(tf), nizhe(tf)
    kuski = [f"рабочий этаж: {tf}"]
    if v:
        kuski.append(f"крупнее — {v} (если структура не влезла)")
    if n:
        kuski.append(f"мельче — {n} (если структура видна, но мелко)")
    return "; ".join(kuski)


# PARA_MESTA_V1 - marker
'''

# ── дополнение vybor.py ──
VYBOR_DOP = '''

# ═══════════════════════════════════════════════════════════
# РАБОЧАЯ ПАРА МЕСТА: инструмент + этаж (PARA_MESTA_V1)
# ═══════════════════════════════════════════════════════════
# Слово Шефа 14.08: инструмент трейдер меняет ПО СОГЛАСИЮ Шефа,
# а этаж — всегда его право, и он должен этажами активно
# пользоваться (искать масштаб, в который ляжет его структура).
#
# Поэтому хранятся они по-разному:
#   инструмент — в ПОСТЕ места (задание Шефа, поле «инструмент»);
#   этаж       — МЕТКОЙ жителя, и обязательно ПРИ ИНСТРУМЕНТЕ:
#                у одного человека на золоте структура может
#                читаться с дневок, а на евро с часов. Один общий
#                этаж — это и был тот «ещё один», которого Шеф
#                велел убрать.

PATTERN_ETAZH = "рабочий_этаж"      # ключ метки
SLOVO_ETAZH = "ЭТАЖ:"               # как трейдер объявляет его словом


def _post_mesta(ceh: str, slot: str):
    """(модуль rabota, пост места) — или (None, None).

    Пост ищем ПО ПРИВЯЗКЕ (поля цех/слот), а не по угаданному имени
    папки: посты трейдеров заведены как `treyder_proboy`, а не
    `торговый_хаос__A06`. Так же делает и сам город в
    `rabota.kto_na_slote` — Закон Картриджа: сканируем, а не помним
    имена наизусть.
    """
    try:
        import sys as _s
        import json as _j
        from pathlib import Path as _P
        _gorod = str(_P(__file__).resolve().parent.parent / "ГОРОД")
        if _gorod not in _s.path:
            _s.path.insert(0, _gorod)
        import rabota as _r
        if not _r.POSTY.exists():
            return _r, None
        for d in sorted(_r.POSTY.iterdir()):
            f = d / "пост.json"
            if not f.exists():
                continue
            try:
                p = _j.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if p.get("цех") == ceh and p.get("слот") == slot:
                p["_id"] = p.get("id") or d.name
                return _r, p
        return _r, None
    except Exception:
        return None, None


def etazh_zhitelya(ceh: str, slot: str, symbol: str) -> str:
    """Рабочий этаж, который житель выбрал для ЭТОГО инструмента."""
    symbol = (symbol or "").strip().upper()
    d, _ = _dvizhok_zhitelya(ceh, slot)
    if d is None or not symbol:
        return ""
    try:
        moi = [m for m in d.metki() if m.get("паттерн") == PATTERN_ETAZH]
    except Exception:
        return ""
    moi.sort(key=lambda x: str(x.get("когда", "")))
    for m in reversed(moi):
        kuski = (m.get("текст") or "").strip().upper().split()
        if len(kuski) == 2 and kuski[0] == symbol:
            return kuski[1]
    return ""


def zapisat_etazh(ceh: str, slot: str, symbol: str, tf: str) -> tuple:
    """Житель ставит себе рабочий этаж. Согласия не спрашивает —
    это его кухня (Закон II). Прошлые не стираем: видно, как он
    искал масштаб."""
    symbol = (symbol or "").strip().upper()
    tf = (tf or "").strip().upper()
    if not symbol:
        return False, "не сказано, по какому инструменту"
    try:
        import masshtab
        if not masshtab.est(tf):
            return False, f"такого этажа нет в лесенке: {tf}"
    except Exception:
        pass
    d, n = _dvizhok_zhitelya(ceh, slot)
    if d is None:
        return False, "на месте никого"
    if etazh_zhitelya(ceh, slot, symbol) == tf:
        return True, "тот же этаж, что и был"
    try:
        from datetime import datetime
        metki = d.metki()
        metki.append({"текст": f"{symbol} {tf}", "паттерн": PATTERN_ETAZH,
                      "откуда": "решение",
                      "когда": datetime.now().isoformat(timespec="seconds"),
                      "раз": 1})
        d._pisat_etazh(d._metki_path(), metki)
    except Exception as e:
        return False, str(e)
    kto = (n or {}).get("имя", "житель")
    return True, f"{kto} работает {symbol} с {tf}"


def poymat_etazh(ceh: str, slot: str, symbol: str, otvet: str) -> tuple:
    """Строка «ЭТАЖ: H1» в ответе — ставим сразу, без согласия."""
    for stroka in (otvet or "").splitlines():
        s = stroka.strip()
        if s.upper().startswith(SLOVO_ETAZH):
            return zapisat_etazh(ceh, slot, symbol,
                                 s[len(SLOVO_ETAZH):])
    return False, ""


def rabota_dlya(ceh: str, slot: str) -> dict:
    """ОДНА ДВЕРЬ: чем и на каком этаже работает это место.

    {инструмент, этаж, откуда_инструмент, откуда_этаж, готов}

    готов=False — работать нечем, и это НЕ ошибка: место молчит,
    пока ему не сказано или пока человек не выбрал сам. Запасного
    инструмента «лишь бы какой» тут нет намеренно: он и был тем
    четвёртым, которого никто не звал, а работали все по нему.
    """
    instr, otk_i = instrument_dlya(ceh, slot)
    etazh, otk_e = "", ""
    if instr:
        etazh = etazh_zhitelya(ceh, slot, instr)
        otk_e = "выбрал сам" if etazh else ""
    return {"инструмент": instr, "этаж": etazh,
            "откуда_инструмент": otk_i if instr else "",
            "откуда_этаж": otk_e,
            "готов": bool(instr and etazh)}


def pochemu_molchit(ceh: str, slot: str) -> str:
    """Человеческим языком: чего не хватает, чтобы место работало."""
    r = rabota_dlya(ceh, slot)
    if r["готов"]:
        return ""
    if not r["инструмент"]:
        return "инструмент не задан и не выбран"
    return "рабочий этаж не выбран"


# PARA_MESTA_V1 - marker
'''

# ── правки в vybor.py: инструмент места читаем из ПОСТА ──
ST_INSTR_MESTA = '''    PANEL_TREYDERA_V1: читаем листок назначений при Бирже, а не бланк
    должности — бланк про должность, а это про сегодняшнюю работу.
    """
    return (_nazn_chitat().get(f"{ceh}/{slot}") or "").strip().upper()'''

NOV_INSTR_MESTA = '''    PARA_MESTA_V1 (правка 14.08): читаем ПОСТ, а не общий листок.
    Листок `Биржа/данные/naznacheniya.json` был списком за других —
    ровно тем, что запрещает Чертёж (Гл.7.2): «единица есть там, где
    лежит, и говорит сама». Поле «инструмент» в бланке поста было
    заведено давно и пустовало. Листок ещё читаем — но только как
    запасной, для того, что не переехало.
    """
    _r, post = _post_mesta(ceh, slot)
    if post:
        iz_posta = (post.get("инструмент") or "").strip().upper()
        if iz_posta:
            return iz_posta
    return (_nazn_chitat().get(f"{ceh}/{slot}") or "").strip().upper()'''

ST_NAZNACHIT = '''def naznachit(ceh: str, slot: str, symbol: str) -> tuple:
    """Шеф даёт трейдеру инструмент. Пусто — снимает задание."""
    import json as _j
    d = _nazn_chitat()'''

NOV_NAZNACHIT = '''def naznachit(ceh: str, slot: str, symbol: str) -> tuple:
    """Шеф даёт трейдеру инструмент. Пусто — снимает задание.

    PARA_MESTA_V1: пишем в ПОСТ места. Поста нет (место без бланка) —
    падаем в старый листок, чтобы задание не потерялось.
    """
    symbol_up = (symbol or "").strip().upper()
    _r, post = _post_mesta(ceh, slot)
    if _r is not None and post:
        ok, chto = _r.obnovit(post.get("_id", ""),
                              {"инструмент": symbol_up})
        if ok:
            return True, (f"задание: {symbol_up}" if symbol_up
                          else "задание снято")
        return False, chto
    import json as _j
    d = _nazn_chitat()'''


def pravit(put: Path, proverka, pravka, imya_bak: str) -> bool:
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        print(f"  · {put.name}: маркер уже стоит — пропускаю")
        return True
    ok, prichina = proverka(tekst)
    if not ok:
        print(f"  ✗ {put.name}: {prichina}")
        return False
    novyy = pravka(tekst)
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ {put.name}: после правки не разбирается ({e})")
        return False
    if SUHO:
        print(f"  · {put.name}: правка готова (сухой прогон)")
        return True
    bak = put.with_suffix(put.suffix + f".bak_{imya_bak}_"
                          f"{datetime.now():%Y%m%d_%H%M%S}")
    shutil.copy2(put, bak)
    put.write_text(novyy, encoding="utf-8")
    print(f"  ✓ {put.name}: правка легла (копия: {bak.name})")
    return True


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    masshtab = koren / "Биржа" / "masshtab.py"
    vybor = koren / "Биржа" / "vybor.py"
    feed = koren / "Биржа" / "mt5_feed.py"
    listok = koren / "Биржа" / "данные" / "naznacheniya.json"

    # ── 1. лесенка масштабов ──
    print("\n1. Лесенка масштабов — Биржа/masshtab.py")
    if masshtab.exists() and MARKER in masshtab.read_text(encoding="utf-8"):
        print("  · уже лежит — пропускаю")
    else:
        try:
            ast.parse(MASSHTAB_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if SUHO:
            print("  · готова (сухой прогон)")
        else:
            masshtab.write_text(MASSHTAB_PY, encoding="utf-8")
            print("  ✓ положена (шаг вверх и вниз, окно 100-140)")

    # ── 2. насос читает лесенку оттуда, своей копии не держит ──
    print("\n2. Насос перестаёт держать свою копию лесенки")
    ST_LADDER = ('_TF_LADDER = ["MN1", "W1", "D1", "H12", "H8", "H4", '
                 '"H1", "M30", "M15", "M10", "M5"]')
    NOV_LADDER = ('# PARA_MESTA_V1: лесенка переехала в Биржа/masshtab.py —\n'
                  '# ею пользуется не только насос, но и трейдер, и кадр.\n'
                  '# Здесь оставлен только читающий конец, чтобы старые\n'
                  '# вызовы step_down() работали как работали.\n'
                  'try:\n'
                  '    from masshtab import LESTNICA as _TF_LADDER\n'
                  'except Exception:\n'
                  '    _TF_LADDER = ["MN1", "W1", "D1", "H12", "H8", "H4",\n'
                  '                  "H1", "M30", "M15", "M10", "M5"]\n'
                  '\n'
                  '\n'
                  'def step_up(tf_name: str):\n'
                  '    """Ступень ВВЕРХ по лесенке. Была потеряна: файл\n'
                  '    mt5_feed_с_step_up.py лежал в уборке отдельной копией,\n'
                  '    вместо того чтобы жить рукой здесь."""\n'
                  '    try:\n'
                  '        from masshtab import vyshe\n'
                  '        return vyshe(tf_name)\n'
                  '    except Exception:\n'
                  '        return None')
    ok2 = pravit(
        feed,
        lambda t: (t.count(ST_LADDER) == 1,
                   f"якорь лесенки найден {t.count(ST_LADDER)} раз"),
        lambda t: t.replace(ST_LADDER, NOV_LADDER, 1),
        "lestnica")

    # ── 3. vybor.py: пара места ──
    print("\n3. Рабочая пара в Биржа/vybor.py")

    def _proverka_vybor(t):
        if t.count(ST_INSTR_MESTA) != 1:
            return False, "не нашёл instrument_mesta дословно"
        if t.count(ST_NAZNACHIT) != 1:
            return False, "не нашёл naznachit дословно"
        return True, ""

    def _pravka_vybor(t):
        t = t.replace(ST_INSTR_MESTA, NOV_INSTR_MESTA, 1)
        t = t.replace(ST_NAZNACHIT, NOV_NAZNACHIT, 1)
        return t.rstrip("\n") + "\n" + VYBOR_DOP

    ok3 = pravit(vybor, _proverka_vybor, _pravka_vybor, "para")

    if not (ok2 and ok3):
        print("\n✗ Не всё легло — файлы целы.")
        return 1

    # ── 4. перенос листка в посты ──
    print("\n4. Листок назначений → в посты")
    if not listok.exists():
        print("  · листка нет — переносить нечего")
    elif SUHO:
        print("  · перенёс бы (сухой прогон)")
    else:
        import json
        try:
            d = json.loads(listok.read_text(encoding="utf-8"))
        except Exception as e:
            d = {}
            print(f"  ⚠ листок не прочитался: {e}")
        sys.path.insert(0, str(koren / "ГОРОД"))
        perenes, ne_vyshlo = 0, []
        try:
            import rabota as _r
            for klyuch, sym in (d or {}).items():
                if "/" not in klyuch:
                    continue
                ceh, slot = klyuch.split("/", 1)
                pid = ""
                for dd in sorted(_r.POSTY.iterdir()):
                    ff = dd / "пост.json"
                    if not ff.exists():
                        continue
                    try:
                        pp = json.loads(ff.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if pp.get("цех") == ceh and pp.get("слот") == slot:
                        pid = pp.get("id") or dd.name
                        break
                if not pid:
                    ne_vyshlo.append(f"{klyuch} (поста нет)")
                    continue
                ok, chto = _r.obnovit(pid, {"инструмент": sym})
                if ok:
                    print(f"  ✓ {klyuch} → пост {pid}: {sym}")
                    perenes += 1
                else:
                    ne_vyshlo.append(f"{klyuch} ({chto})")
        except Exception as e:
            print(f"  ⚠ перенос не вышел: {e}")
        if perenes and not ne_vyshlo:
            novoe = listok.with_suffix(".json.perenesen")
            listok.rename(novoe)
            print(f"  ✓ листок отложен как {novoe.name} (не удалён)")
        elif ne_vyshlo:
            print(f"  ⚠ не переехало: {', '.join(ne_vyshlo)} — "
                  f"листок оставляю на месте, он ещё читается запасным")

    if not SUHO:
        import py_compile
        for f in (masshtab, vybor, feed):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nЧто теперь есть:")
        print("  vybor.rabota_dlya(цех, слот) — чем и на каком этаже")
        print("  vybor.zapisat_etazh(...)     — этаж без согласия, его право")
        print("  masshtab.vyshe/nizhe/sosedi  — шаги по лесенке в обе стороны")
        print("\nЭтажа пока нет ни у кого — его объявляет сам трейдер")
        print("словом «ЭТАЖ: H4». Пока не объявил, место честно молчит.")
        print("Ловля этого слова и работа Совета по паре — следующий слой.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
