# -*- coding: utf-8 -*-
"""
VYREZAT_KLICHKI_V1 — клички станций вон из канона и кода.

СЛОВО ШЕФА (04.09): «место не знает владельца — закон картриджа. У
нас не три места, а одно место, всего. Владельцы меняются, и все три
разных». Три стиля входа (пробой фрактала / ранний на конце C / откат
волны 2) — реальные и разные, но их называли именами бывших жителей
(Брут/Авантюрист/Консерватор). Отсюда: кто ни сядет на A06, читает
канон и добросовестно учит чужое имя как свой стиль.

ЧТО ДЕЛАЕТ ЭТОТ ПАТЧ:
  1) ЗНАНИЯ (учит любого трейдера): Брут → ПРОБОЙ, Авантюрист → РАННИЙ,
     Консерватор → ОТКАТ — во всех копиях КАНОН_ВХОДА.md и
     KOTIN_PHILOSOPHY.md (Академия/руда, три слота A06/A07/A08/знания,
     жители Нина/Синди/прочитано). Только текст стиля — техническое
     содержание (§, формулы, числа) не трогаем.
  2) КОД (комментарии, докстринги, строки логов в мозгах A06/A07/A08,
     hooks.py, tester_express.py, исполнитель): та же замена, плюс
     сам слот теперь не подписан именем — «трейдер», не «Брут».
  3) ИМЕНА ФАЙЛОВ ДАННЫХ: diary_brut.jsonl → diary_A06.jsonl (и так
     же A07/A08, brut_stats.json → stats_A06.json) — данные едут, имя
     файла больше не кличка. Место данных прежнее (данные/ слота),
     содержимое не трогается, только имя.

ЧТО ЭТОТ ПАТЧ НЕ ТРОГАЕТ:
  - жители/ковчег/Брут/ — отдельный житель, прошлый, не при делах.
    Слово Шефа: не трогать.
  - Личную память ЖИВЫХ жителей (archive.jsonl, resonance) — их
    собственная честная история, даже если там встречается старое
    слово «авантюристы» из конспекта старого канона. Это их прошлое,
    не редактируем чужие воспоминания.
  - Поля схемы ответа brut_action/brut_verdict/... (латиница,
    JSON-контракт, не кличка) — трогать НЕЛЬЗЯ, отдельная работа.

ИДЕМПОТЕНТНОСТЬ: маркер VYREZAT_KLICHKI_V1 в начале файла — повторный
запуск пропускает уже почищенные файлы. .bak рядом с каждым правленым
файлом. py_compile для .py после правки.
"""
from __future__ import annotations
import re, sys, shutil, py_compile
from pathlib import Path

MARKER = "VYREZAT_KLICHKI_V1"

ROOT = Path(__file__).resolve().parent

# ── 1. ЗНАНИЯ: замена стиля (не персоны) ────────────────────────
ZNANIYA_ZAMENA = [
    (r"\bБРУТА\b", "ПРОБОЯ"),
    (r"\bБРУТ\b", "ПРОБОЙ"),
    (r"\bБрута\b", "Пробоя"),
    (r"\bБруту\b", "Пробою"),
    (r"\bБрутом\b", "Пробоем"),
    (r"\bБрут\b", "Пробой"),
    (r"\bАвантюриста\b", "Раннего"),
    (r"\bАвантюристу\b", "Раннему"),
    (r"\bАвантюристом\b", "Ранним"),
    (r"\bАвантюрист\b", "Ранний"),
    (r"\bКонсерватора\b", "Отката"),
    (r"\bКонсерватору\b", "Откату"),
    (r"\bКонсерватором\b", "Откатом"),
    (r"\bКонсерватор\b", "Откат"),
]

ZNANIYA_FILES = [
    "GRONDHEIM_CITY/Академия/руда/тексты/КАНОН_ВХОДА.md",
    "КАНОН_ВХОДА.md",
    "GRONDHEIM_CITY/Академия/руда/тексты/KOTIN_PHILOSOPHY.md",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/знания/KOTIN_PHILOSOPHY.md",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/знания/KOTIN_PHILOSOPHY.md",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A08/знания/KOTIN_PHILOSOPHY.md",
    "GRONDHEIM_CITY/жители/ковчег/Нина/прочитано/KOTIN_PHILOSOPHY.md",
    "GRONDHEIM_CITY/жители/ковчег/Синди/прочитано/KOTIN_PHILOSOPHY.md",
]

# заголовок KOTIN_PHILOSOPHY.md прямо называет слоты кличками —
# отдельная точечная правка (снимает и станцию, и привязку к слоту)
ZAGOLOVOK_STARYY = ("## Общая база знаний для трейдеров Трибунала "
                     "(A06 Брут, A07 Авантюрист, A08 Консерватор)")
ZAGOLOVOK_NOVYY = ("## Общая база знаний для трейдеров Биржи "
                    "(A06/A07/A08 — место не диктует стиль, "
                    "стиль выбирает сам трейдер)")

# ── 2. КОД: снятие имени со СЛОТА (комментарии/логи, не логика) ──
KOD_ZAMENA = [
    (r"\bБРУТОМ\b", "ТРЕЙДЕРОМ"),
    (r"\bБРУТА\b", "ТРЕЙДЕРА"),
    (r"\bБРУТ\b", "ТРЕЙДЕР"),
    (r"\bБрута\b", "трейдера"),
    (r"\bБруту\b", "трейдеру"),
    (r"\bБрутом\b", "трейдером"),
    (r"\bБрут\b", "трейдер"),
    (r"\bАВАНТЮРИСТОМ\b", "ТРЕЙДЕРОМ"),
    (r"\bАВАНТЮРИСТА\b", "ТРЕЙДЕРА"),
    (r"\bАВАНТЮРИСТ\b", "ТРЕЙДЕР"),
    (r"\bАвантюриста\b", "трейдера"),
    (r"\bАвантюристу\b", "трейдеру"),
    (r"\bАвантюристом\b", "трейдером"),
    (r"\bАвантюрист\b", "трейдер"),
    (r"\bКОНСЕРВАТОРОМ\b", "ТРЕЙДЕРОМ"),
    (r"\bКОНСЕРВАТОРА\b", "ТРЕЙДЕРА"),
    (r"\bКОНСЕРВАТОР\b", "ТРЕЙДЕР"),
    (r"\bКонсерватора\b", "трейдера"),
    (r"\bКонсерватору\b", "трейдеру"),
    (r"\bКонсерватором\b", "трейдером"),
    (r"\bКонсерватор\b", "трейдер"),
]

KOD_FILES = [
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/мозг.py",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/мозг.py",
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A08/мозг.py",
    "GRONDHEIM_CITY/Биржа/hooks.py",
    "GRONDHEIM_CITY/Биржа/tester_express.py",
    "GRONDHEIM_CITY/Биржа/цеха/контора/слоты/исполнитель/мозг.py",
]

# ТОЧЕЧНЫЕ замены ДО общего прохода: эти строки СРАВНИВАЮТ два-три
# РАЗНЫХ стиля по номеру параграфа (§6.1/6.2/6.3) — тут нужны слова
# стиля (как в знаниях), а не «трейдер», иначе сравнение схлопнется
# в «трейдер — §6.1... трейдер — §6.3...» и потеряет смысл.
KOD_TOCHECHNO = {
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/мозг.py": [
        ("# СТАНЦИЯ ДРУГАЯ. Брут — §6.1 (пробой фрактала за пастью на импульсе).\n"
         "# Авантюрист — §6.2: конец волны C отката, разворот. Верит первым. Ловец",
         "# СТИЛЬ ДРУГОЙ. Пробой — §6.1 (пробой фрактала за пастью на импульсе).\n"
         "# Ранний — §6.2: конец волны C отката, разворот. Верит первым. Ловец"),
    ],
    "GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A08/мозг.py": [
        ("# СТАНЦИЯ ДРУГАЯ. Брут — §6.1 (пробой фрактала за пастью на импульсе).\n"
         "# Консерватор — §6.3: откат волны 2 после импульса. Ждёт разрядки AO и",
         "# СТИЛЬ ДРУГОЙ. Пробой — §6.1 (пробой фрактала за пастью на импульсе).\n"
         "# Откат — §6.3: откат волны 2 после импульса. Ждёт разрядки AO и"),
    ],
}

# ── 3. Имена файлов данных: кличка → номер слота ────────────────
# (путь мозга, старое имя в DIARY_PATH/STATS_PATH, новое имя)
FAYLY_DANNYKH = [
    ("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/мозг.py",
     "diary_brut.jsonl", "diary_A06.jsonl", "brut_stats.json", "stats_A06.json"),
    ("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A07/мозг.py",
     "diary_avan.jsonl", "diary_A07.jsonl", "avan_stats.json", "stats_A07.json"),
    ("GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A08/мозг.py",
     "diary_cons.jsonl", "diary_A08.jsonl", "cons_stats.json", "stats_A08.json"),
]


def _naiti(rel: str) -> Path | None:
    """Ищет файл по относительному пути от корня репо, где бы репо
    ни лежало — Шеф не прописывает пути руками (правило студии)."""
    p = ROOT / rel
    if p.exists():
        return p
    # репо может быть на этаж выше/ниже — ищем по имени файла в дереве
    for cand in ROOT.rglob(Path(rel).name):
        if str(cand).replace("\\", "/").endswith(rel.replace("\\", "/")):
            return cand
    return None


def _uzhe_pochishcheno(text: str) -> bool:
    return MARKER in text


def _pravit_tekst(path: Path, zameny, extra=None, is_py=False) -> bool:
    if not path.exists():
        print(f"  ⏭  нет файла: {path.name}")
        return False
    text = path.read_text(encoding="utf-8")
    if _uzhe_pochishcheno(text):
        print(f"  ✓  уже чисто: {path.name}")
        return False

    novyy = text
    if extra:
        for stary, novy in extra:
            novyy = novyy.replace(stary, novy)
    for patt, zamena in zameny:
        novyy = re.sub(patt, zamena, novyy)

    if novyy == text:
        print(f"  ·  нечего менять: {path.name}")
        return False

    bak = path.with_suffix(path.suffix + ".bak_klichki")
    shutil.copy2(path, bak)

    # маркер — в первую строку-комментарий (py) или после заголовка (md)
    if is_py:
        novyy = f"# {MARKER}\n" + novyy
    else:
        novyy = novyy + f"\n\n<!-- {MARKER} -->\n"

    path.write_text(novyy, encoding="utf-8")

    if is_py:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, path)
            print(f"  ✗ ОТКАТ (не компилируется): {path.name}\n     {e}")
            return False

    print(f"  ✔  почищен: {path.name}  (бэкап: {bak.name})")
    return True


def pravit_faily_dannykh(rel_mozg: str, star_diary, nov_diary, star_stats, nov_stats):
    mozg = _naiti(rel_mozg)
    if not mozg:
        return
    text = mozg.read_text(encoding="utf-8")
    if star_diary not in text and star_stats not in text:
        return  # уже переименовано выше по тексту-патчу мозга

    # физически переносим существующие файлы данных, если они есть
    data_dir = mozg.parent / "данные"
    for star, nov in ((star_diary, nov_diary), (star_stats, nov_stats)):
        stary_f = data_dir / star
        novy_f = data_dir / nov
        if stary_f.exists() and not novy_f.exists():
            shutil.move(str(stary_f), str(novy_f))
            print(f"  📦 файл данных переехал: {star} → {nov}")
        elif stary_f.exists() and novy_f.exists():
            print(f"  ⚠️  и старый, и новый файл данных существуют — "
                  f"{star} НЕ тронут, разбираться руками: {data_dir}")


def main():
    print("=== ЗНАНИЯ (стиль, не персона) ===")
    for rel in ZNANIYA_FILES:
        p = _naiti(rel)
        if p is None:
            print(f"  ⏭  не найден: {rel}")
            continue
        _pravit_tekst(p, ZNANIYA_ZAMENA,
                       extra=[(ZAGOLOVOK_STARYY, ZAGOLOVOK_NOVYY)],
                       is_py=False)

    print("\n=== КОД (слот без имени владельца) ===")
    for rel in KOD_FILES:
        p = _naiti(rel)
        if p is None:
            print(f"  ⏭  не найден: {rel}")
            continue
        _pravit_tekst(p, KOD_ZAMENA, extra=KOD_TOCHECHNO.get(rel), is_py=True)

    print("\n=== ФАЙЛЫ ДАННЫХ (имя без клички) ===")
    for rel_mozg, sd, nd, ss, ns in FAYLY_DANNYKH:
        pravit_faily_dannykh(rel_mozg, sd, nd, ss, ns)
        p = _naiti(rel_mozg)
        if p:
            # переименование ПУТИ в самом коде — отдельно от текстовой
            # чистки выше (DIARY_PATH/STATS_PATH это код, не проза)
            text = p.read_text(encoding="utf-8")
            if sd in text or ss in text:
                text2 = text.replace(f'"{sd}"', f'"{nd}"').replace(f'"{ss}"', f'"{ns}"')
                if text2 != text:
                    bak = p.with_suffix(p.suffix + ".bak_fayly_dannykh")
                    shutil.copy2(p, bak)
                    p.write_text(text2, encoding="utf-8")
                    try:
                        py_compile.compile(str(p), doraise=True)
                        print(f"  ✔  переименованы пути в коде: {p.name}")
                    except py_compile.PyCompileError as e:
                        shutil.copy2(bak, p)
                        print(f"  ✗ ОТКАТ путей данных: {p.name}\n     {e}")

    print("\nГотово. Житель Брут (жители/ковчег/Брут/) и личная память "
          "живых жителей не тронуты — как договорились.")


if __name__ == "__main__":
    main()

# VYREZAT_KLICHKI_V1 - marker
