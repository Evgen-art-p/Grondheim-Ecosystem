# -*- coding: utf-8 -*-
"""
magic_pri_meste.py   ·   MARKER: MAGIC_PRI_MESTE_V3

СЛОВО ШЕФА
----------
«Магик — свойство МЕСТА. Сел человек — работает под номером места;
ушёл — номер остался на месте, а человек уходит пустой. Магик делался
для Биржи, для других вакансий его не планировали.»

ЧТО ПОЛОМАЛОСЬ 24.08
--------------------
Сделку закрыла Нина (A07), а в лог ушло:

    [МОСТ] 🫁 Лока: -1.0R → заряд 0.265

Заряд от чужой сделки лёг Локе в паспорт. И не только заряд — тем же
путём идёт вывод судьи, значит и опыт ушёл бы туда же.

Виноват не пост и не ошибка найма. Номера СТОЛКНУЛИСЬ:

    treyder_proboy     A06   magic=100001      bibliotekar        100001
    treyder_ranniy     A07   magic=100002      khranitel_arkhiva  100002
    treyder_otkat      A08   magic=100003      mayak              100003

Номер 100002 законно принадлежит и месту A07, и хранителю архива —
это Лока. Две нумерации росли врозь: торговым местам номера раздаёт
жёсткая табличка A06→100001, а посты Академии и Города получали свои,
тоже с 100001. Скан по магику нашёл Локу не по ошибке — у неё этот
номер действительно есть.

Плюс магик копировался в маску жителя при найме. У Локи он там живой
до сих пор: снялась с места давно, а номер остался при ней.

ЧТО ДЕЛАЕМ
----------
  1. Магик — только у ТОРГОВЫХ мест. У библиотекаря, ректора, маяка и
     хранителя архива он убирается: сделок они не открывают, счёт в
     терминале им не нужен. Столкновение исчезает само.
  2. В масках жителей магик гасится. В человеке номера быть не
     должно — иначе он уносит его с собой, как унесла Лока.
  3. Поиск «магик → человек» разворачивается: сперва ищем МЕСТО с
     этим номером среди постов, потом спрашиваем пост, кто на нём
     сидит. Нашлось два места с одним номером — говорим вслух и не
     угадываем. Маски остаются последним запасным путём, чтобы уже
     сидящие не выпали из строя.
  4. Пост A07 пуст: Нина работает по старой маске, а в документе
     места её нет. Дописываем то, что и так есть по факту — имя и
     дату. Это не приём заново: метки, статистика и журнал места не
     трогаются. Заодно проверяем остальные места и называем все
     расхождения между маской и постом.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · заряд Локи от чужой сделки не откатываем — слово Шефа: пусть
    остаётся, Лока просилась на Биржу, метка ещё придётся к месту;
  · зашитую табличку номеров у Исполнителя и `ГОРОД/rabota.py` не
    трогаем — это второй заход;
  · никого не увольняем и не нанимаем.

Сначала ПОКАЗЫВАЕТ, что собирается сделать, и только потом делает.
Идемпотентен, кладёт `.bak_magicmesto_ГГГГММДД_ЧЧММСС`.

  py -3 magic_pri_meste.py           — сделать
  py -3 magic_pri_meste.py --suho    — только показать
"""

import ast
import json
import sys
import time
from pathlib import Path

MARKER = "MAGIC_PRI_MESTE_V3"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ────────────────── 3. разворот поиска в реестре ──────────────────

R_STAROE = '''def resolve_by_magic(magic):
    """ОБРАТНЫЙ мостик: magic закрытой позиции → носитель.
    Близнец resolve_para, тот же скан масок — magic живёт В МАСКЕ
    (Закон Пары), отдельного реестра магиков нет. Честный None:
    магик не найден ни в одной активной маске. Приводит к int, чтобы
    100002 и "100002" резолвились одинаково. # MAGIC_IN_MASK_V1
    """
    try:
        m = int(magic)
    except (TypeError, ValueError):
        return None
    for z in _scan_zhiteli_maski():
        zm = z.get("magic")
        if zm is None:
            continue
        try:
            if int(zm) == m:
                return z
        except (TypeError, ValueError):
            continue
    return None'''

R_NOVOE = '''def resolve_by_magic(magic):
    """ОБРАТНЫЙ мостик: magic закрытой позиции → носитель.

    MAGIC_PRI_MESTE_V3: ищем СНАЧАЛА МЕСТО, потом человека на нём.
    Магик — свойство места, а не человека: сел — работаешь под
    номером места, ушёл — номер остался на месте.

    Раньше сканировались маски жителей, и 24.08 это дало чужой заряд:
    номер 100002 носили и место A07, и хранитель архива, а в маске
    Локи он остался живым с давних пор. Скан честно нашёл первого.

    Нашлось два места с одним номером — НЕ УГАДЫВАЕМ: говорим вслух и
    возвращаем пусто. Лучше потерянный вдох, чем вдох не тому.
    """
    try:
        m = int(magic)
    except (TypeError, ValueError):
        return None

    mesta = []
    try:
        # посты читаем файлами: их формат — граница города, и она
        # не меняется, а чужое API может отдать не все поля
        for _f in sorted((CITY / "посты").glob("*/пост.json")):
            _p = _read_json(_f) or {}
            try:
                if _p.get("magic") is not None and int(_p["magic"]) == m:
                    mesta.append(_p)
            except (TypeError, ValueError):
                continue
    except Exception as _e:
        print(f"[РЕЕСТР] посты не прочлись ({_e}) — иду по маскам")

    if len(mesta) > 1:
        _kto = ", ".join(f"{p.get('цех') or '—'}/{p.get('слот') or '—'}"
                         for p in mesta)
        print(f"[РЕЕСТР] ⚠️  магик {m} у НЕСКОЛЬКИХ мест: {_kto}. "
              f"Не угадываю — разведи номера.")
        return None
    if len(mesta) == 1:
        _ceh = (mesta[0].get("цех") or "").strip()
        _slot = (mesta[0].get("слот") or "").strip()
        if _ceh and _slot:
            return resolve_para(_ceh, _slot)

    # запасной путь: старые маски, чтобы уже сидящие не выпали
    for z in _scan_zhiteli_maski():
        zm = z.get("magic")
        if zm is None:
            continue
        try:
            if int(zm) == m:
                print(f"[РЕЕСТР] магик {m} найден только в маске "
                      f"({z.get('имя')}) — место его не знает")
                return z
        except (TypeError, ValueError):
            continue
    return None'''


# ─────────────────────────── работа с данными ───────────────────────────

TORGOVYE_CEHA = ("торговый_хаос",)     # где вообще открывают сделки


def _chitat(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pisat(p: Path, d: dict) -> bool:
    if SUHO:
        return True
    try:
        p.with_name(p.name + f".bak_magicmesto_{SHTAMP}").write_text(
            p.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass
    try:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception as e:
        print(f"      не записалось: {e}")
        return False


def posty(koren: Path):
    d = koren / "GRONDHEIM_CITY" / "посты"
    return sorted(d.glob("*/пост.json")) if d.exists() else []


def shag_1_neторговые(koren: Path):
    """Магик убираем у всех, кто не торгует."""
    print("\n1. МАГИК ТОЛЬКО У ТОРГОВЫХ МЕСТ")
    tronuto = 0
    for f in posty(koren):
        d = _chitat(f)
        if not d or d.get("magic") is None:
            continue
        ceh = (d.get("цех") or "").strip()
        if ceh in TORGOVYE_CEHA:
            print(f"   оставляю  {f.parent.name:<24} magic={d['magic']} "
                  f"({ceh}/{d.get('слот')})")
            continue
        print(f"   УБИРАЮ    {f.parent.name:<24} magic={d['magic']} "
              f"— сделок не открывает")
        d["magic"] = None
        if _pisat(f, d):
            tronuto += 1
    print(f"   → снято номеров: {tronuto}")


def shag_2_maski(koren: Path):
    """Магик из масок жителей — вон. В человеке номера быть не должно."""
    print("\n2. МАГИК В МАСКАХ ЖИТЕЛЕЙ")
    tronuto = 0
    root = koren / "GRONDHEIM_CITY" / "жители"
    for f in sorted(root.glob("*/*/маски/работа/mask.json")):
        d = _chitat(f)
        if not d or d.get("magic") is None:
            continue
        imya = f.parents[2].name
        print(f"   гашу      {imya:<12} magic={d['magic']}")
        d["magic"] = None
        if _pisat(f, d):
            tronuto += 1
    print(f"   → погашено: {tronuto}")


def shag_4_posty_i_maski(koren: Path):
    """Кто работает по маске, но не записан в пост."""
    print("\n4. МАСКА ПРОТИВ ПОСТА")
    root = koren / "GRONDHEIM_CITY" / "жители"
    po_maske = {}
    for f in sorted(root.glob("*/*/маски/работа/mask.json")):
        d = _chitat(f) or {}
        if not d.get("_активна"):
            continue
        ceh = (d.get("Workshop_ID") or "").strip()
        slot = (d.get("Turbo_Role") or "").strip()
        if ceh and slot:
            po_maske[(ceh, slot)] = f.parents[2].name

    for f in posty(koren):
        d = _chitat(f) or {}
        ceh = (d.get("цех") or "").strip()
        slot = (d.get("слот") or "").strip()
        if not (ceh and slot):
            continue
        kto = d.get("кто_сидит")
        imya_posta = (kto or {}).get("имя") if isinstance(kto, dict) else kto
        imya_maski = po_maske.get((ceh, slot))
        if imya_posta and imya_maski and imya_posta != imya_maski:
            print(f"   ⚠️  {ceh}/{slot}: пост говорит {imya_posta}, "
                  f"маска — {imya_maski}. Решать Шефу, не трогаю.")
            continue
        if imya_posta or not imya_maski:
            continue
        # маска есть, поста нет — дописываем факт
        print(f"   дописываю {ceh}/{slot}: {imya_maski} "
              f"(работает по маске, в посту пусто)")
        d["кто_сидит"] = {"имя": imya_maski,
                          "с": time.strftime("%Y-%m-%d %H:%M"),
                          "запись": "MAGIC_PRI_MESTE_V3: факт по маске"}
        _pisat(f, d)


# ─────────────────────────── механика ───────────────────────────

def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — только показываю, ничего не пишу.")

    # 3. код реестра
    print("\n3. РЕЕСТР: магик → место → человек")
    put = koren / "Биржа" / "cartridge_registry.py"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        print("   уже стояло")
    elif text.count(R_STAROE) != 1:
        print("   мимо: якорь не найден — код НЕ тронут")
    else:
        novyy = text.replace(R_STAROE, R_NOVOE, 1)
        novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
            if not SUHO:
                put.with_name(put.name + f".bak_magicmesto_{SHTAMP}"
                              ).write_text(text, encoding="utf-8")
                put.write_text(novyy, encoding="utf-8")
            print("   сделано   Биржа/cartridge_registry.py")
        except SyntaxError as e:
            print(f"   мимо: правка ломает синтаксис ({e.lineno}: {e.msg})")

    shag_1_neторговые(koren)
    shag_2_maski(koren)
    shag_4_posty_i_maski(koren)

    print("""
────────────────────────────────────────────────────────────────
ЧТО ПРОВЕРИТЬ ПОСЛЕ ПРОГОНА
  При закрытии сделки Нины в логе должно стоять ЕЁ имя:
      [МОСТ] 🫁 Нина: -1.0R → заряд …
  Если увидишь «магик … у НЕСКОЛЬКИХ мест» — значит номера где-то
  ещё пересекаются, скинь строку.
  Если «найден только в маске» — место этого номера не знает, и
  туда надо смотреть отдельно.

ОСТАЛОСЬ НА ВТОРОЙ ЗАХОД
  · зашитая табличка номеров в мозге Исполнителя (третья копия
    правды о номерах);
  · ГОРОД/rabota.py — чтобы новые посты вне Биржи номера не
    получали вовсе.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
