# patch_razbor_pasportov.py
# ─────────────────────────────────────────────────────────────
# RAZBOR_PASPORTOV_V1 — РАЗВЕДКА ПЕРЕД МИГРАЦИЕЙ ЭТАЖЕЙ.
#
# НИЧЕГО НЕ ПИШЕТ. Только читает и показывает.
#
# Зачем: по закону ядра (Брат/README.md) три этажа —
#   1_якоря  = РОД, дно, зерно, НЕ МЕНЯЮТСЯ
#   2_метки  = НАЖИТОЕ, растёт
#   3_маяки  = МОМЕНТ, гаснет
# А на диске всё свалено в одно поле Anchor_Points: и род, и торговый
# опыт (это Брат дописывал 12.07 в Мосте — своя ошибка, разобрана в
# АКАДЕМИЯ_ГРОНДХЕЙМА.md §5.1).
#
# Решение Шефа (вариант Б): не код решает, что род, а что нажитое —
# РЕШАЕТ ШЕФ ГЛАЗАМИ. Этот скрипт печатает всё как есть + черновой
# разбор Брата (гипотеза, не приговор). Шеф правит и говорит, что куда.
#
# Запуск из корня репо:
#   python patch_razbor_pasportov.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CITY = ROOT / "GRONDHEIM_CITY"

YAKOR_LIT = "\\n"   # литерал: обратный слэш + n (как в dvizhok.py)

# Папки, куда не лезем при скане (мусор, кеш, архив)
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules",
             "_ARCHIVE", "_OLD", ".vscode"}


def _nayti_doma(koren: Path) -> list:
    """RAZBOR_PASPORTOV_V1 · живой скан (Закон Картриджа: город не ведёт
    списков — сканирует диск). Дом = любая папка с passport.json на ЛЮБОЙ
    глубине. Жёсткий путь не годится: у Шефа дома лежат под 'ковчег'.
    Локации тоже носят passport.json — их отсекаем: у жителя есть
    ID_Object + DNA_Static, у локации — нет."""
    naydeno = []
    for pp in koren.rglob("passport.json"):
        if any(part in SKIP_DIRS for part in pp.parts):
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(p, dict):
            continue
        # ЖИТЕЛЬ, а не локация: носит ID_Object и/или натуру
        if p.get("ID_Object") or p.get("DNA_Static") or p.get("Official_Name"):
            # у локации бывает Official_Name — но нет натуры и нет якорей
            if not (p.get("DNA_Static") or p.get("Anchor_Points")
                    or p.get("Core_Phrase") or p.get("Hidden_History")):
                continue
            naydeno.append(pp.parent)
    return sorted(set(naydeno))


# ── маркеры: чем нажитое пахнет иначе, чем род ──────────────────
# Род говорит КТО ОН ЕСТЬ. Нажитое говорит ЧТО С НИМ БЫЛО и ЧТО ОН ПОНЯЛ.
MARKERY_NAZHITOGO = [
    # торговая лексика — этого при рождении в паспорте быть не могло
    "стоп", "сделк", "позици", "лонг", "шорт", "профит", "убыт", "лосс",
    "тейк", "фрактал", "аллигатор", "ao", "бар", "свеч", "тренд",
    "пирамид", "риск", "просад", "депозит", "лот", "спред", "R:",
    # язык вывода — «я понял / я заметил / больше не»
    "понял", "усвоил", "заметил", "больше не", "теперь я", "научил",
    "оказалось", "вывод", "урок", "ошиб", "зря", "не стоит", "надо было",
    # рынок как субъект — язык опыта, не рода
    "рынок показал", "рынок наказал", "рынок научил",
]

MARKERY_RODA = [
    # род говорит про натуру и происхождение
    "я всегда", "с детств", "по природ", "меня растил", "родом",
    "не выношу", "не терплю", "верю", "боюсь", "люблю", "ненавиж",
    "для меня важн", "никогда не позволю",
]


def _razdelitel(raw: str) -> str:
    return YAKOR_LIT if YAKOR_LIT in (raw or "") else "\n"


def _spisok(raw: str) -> list:
    s = (raw or "").replace(YAKOR_LIT, "\n")
    return [ln.strip() for ln in s.split("\n") if ln.strip()]


def _gipoteza(stroka: str) -> tuple:
    """Черновой разбор Брата: род или нажитое. ГИПОТЕЗА, не приговор.
    Возвращает (вердикт, причина). Шеф правит."""
    s = stroka.lower()
    hit_n = [m for m in MARKERY_NAZHITOGO if m in s]
    hit_r = [m for m in MARKERY_RODA if m in s]

    if hit_n and not hit_r:
        return "МЕТКА", f"нажитое: {', '.join(hit_n[:3])}"
    if hit_r and not hit_n:
        return "РОД", f"натура: {', '.join(hit_r[:3])}"
    if hit_n and hit_r:
        return "?СПОРНО", f"и то и то: род[{hit_r[0]}] / нажитое[{hit_n[0]}]"
    return "?НЕ ЗНАЮ", "маркеров нет — смотри глазами"


def razobrat_zhitelya(dom: Path):
    pp = dom / "passport.json"
    if not pp.exists():
        return None
    try:
        p = json.loads(pp.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"  ⚠ паспорт не читается: {ex}")
        return None

    imya = p.get("Official_Name") or dom.name
    zid = p.get("ID_Object", "—")

    print()
    print("═" * 70)
    print(f"  {imya}   (ID {zid})")
    try:
        print(f"  путь: {dom.relative_to(CITY)}")
    except Exception:
        print(f"  путь: {dom}")
    print("═" * 70)

    # ── СОСТОЯНИЕ ───────────────────────────────────────────────
    charge = p.get("_charge", None)
    charge_ts = p.get("_charge_ts", "—")
    if charge is None:
        print("  заряд:  НЕТ ПОЛЯ (_charge) — житель ещё не дышал")
    else:
        print(f"  заряд:  {charge:+.3f}   последний вдох: {charge_ts}")
        # хвост §7 Академии: заряд не остывает сам, только по вдоху
        if abs(charge) > 0.4:
            print(f"          ⚠ висит высоко — Суточного Тика нет, "
                  f"сам не остынет")

    # ── МАСКА (профессия — это РОЛЬ, не род) ────────────────────
    mp = dom / "маски" / "работа" / "mask.json"
    if mp.exists():
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
            aktivna = m.get("_активна")
            print(f"  маска:  {m.get('Turbo_Role') or m.get('Profession') or '—'}"
                  f"  цех={m.get('Workshop_ID', '—')}"
                  f"  magic={m.get('magic', '—')}"
                  f"  активна={aktivna}")
            cp = (m.get("Core_Phrase") or "").strip()
            if cp:
                print(f"  ядро:   «{cp}»   (из МАСКИ — так и должно быть)")
        except Exception:
            print("  маска:  ⚠ не читается")
    else:
        print("  маска:  НЕТ — житель без профессии (кандидат в Академию)")

    cp_pass = (p.get("Core_Phrase") or "").strip()
    if cp_pass:
        print(f"  ⚠ ядро ЕСТЬ И В ПАСПОРТЕ: «{cp_pass}» — по Чертежу §1.5 "
              f"ядро живёт в РОЛИ. Дубль.")

    # ── ЭТАЖ 1: ЯКОРЯ (по факту — свалка рода и нажитого) ────────
    raw = p.get("Anchor_Points", "") or ""
    sep = _razdelitel(raw)
    sep_imya = "ЛИТЕРАЛ \\n" if sep == YAKOR_LIT else "настоящий перевод строки"
    lines = _spisok(raw)

    print()
    print(f"  ── Anchor_Points ── ({len(lines)} строк, разделитель: {sep_imya})")
    if not lines:
        print("     пусто")
    for i, ln in enumerate(lines, 1):
        verdict, prichina = _gipoteza(ln)
        print()
        print(f"     [{i}] {ln}")
        print(f"         → Брат думает: {verdict}   ({prichina})")

    # ── ЭТАЖ 3: ЧЕРНОВИКИ (маяки) ───────────────────────────────
    drafts = p.get("Draft_Anchors") or []
    print()
    print(f"  ── Draft_Anchors ── ({len(drafts)} черновиков)")
    if not drafts:
        print("     пусто")
    for d in drafts:
        print(f"     • [{d.get('раз', 1)}/3] {d.get('текст', '')}")
        print(f"       паттерн: {d.get('паттерн', '—')}   "
              f"первый раз: {str(d.get('первый_раз', '—'))[:10]}")

    # ── ЭТАЖ 2: МЕТКИ (пока не существует) ──────────────────────
    mfile = dom / "2_метки" / "metki.json"
    print()
    if mfile.exists():
        try:
            mm = json.loads(mfile.read_text(encoding="utf-8"))
            print(f"  ── 2_метки/metki.json ── ({len(mm)} меток) — УЖЕ ЕСТЬ")
        except Exception:
            print("  ── 2_метки/metki.json ── ⚠ не читается")
    else:
        print("  ── 2_метки/metki.json ── НЕТ. Этаж не построен.")

    # ── СЛОИ ПАМЯТИ ─────────────────────────────────────────────
    print()
    print("  ── слои памяти ──")
    for sloy, fname in (("core", None),
                        ("sensory", "sensory_memory.json"),
                        ("resonance", "event_log.jsonl"),
                        ("archive", "archive.jsonl")):
        d = dom / sloy
        if not d.exists():
            print(f"     {sloy:10s} папки нет")
            continue
        if fname is None:
            n = len(list(d.iterdir()))
            print(f"     {sloy:10s} {n} файл(ов)")
            continue
        f = d / fname
        if not f.exists():
            print(f"     {sloy:10s} пусто")
            continue
        try:
            if fname.endswith(".jsonl"):
                n = sum(1 for l in f.read_text(encoding="utf-8").splitlines()
                        if l.strip())
            else:
                n = len(json.loads(f.read_text(encoding="utf-8"))
                        .get("entries", []))
            print(f"     {sloy:10s} {n} запис(ей)")
        except Exception:
            print(f"     {sloy:10s} ⚠ не читается")

    return {"имя": imya, "id": zid, "якорей": len(lines),
            "черновиков": len(drafts), "заряд": charge}


def main():
    if not CITY.exists():
        print(f"⚠ не нашёл {CITY}")
        print("  запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  РАЗБОР ПАСПОРТОВ — разведка перед миграцией этажей" + " " * 16 + "║")
    print("║  RAZBOR_PASPORTOV_V1 · НИЧЕГО НЕ ПИШЕТ, только смотрит" + " " * 13 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"  скан: {CITY}  (живой rglob, не жёсткий путь)")

    doma = _nayti_doma(CITY)

    if not doma:
        print(f"\n⚠ жителей не нашёл нигде в {CITY}")
        print("  passport.json есть? скажи, где — поправлю фильтр")
        sys.exit(1)

    print(f"  найдено домов: {len(doma)}")

    itog = []
    for dom in doma:
        r = razobrat_zhitelya(dom)
        if r:
            itog.append(r)

    # ── СВОДКА ──────────────────────────────────────────────────
    print()
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  СВОДКА" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"  {'житель':22s} {'якорей':>7s} {'черновиков':>11s} {'заряд':>8s}")
    print("  " + "─" * 52)
    for r in itog:
        z = f"{r['заряд']:+.3f}" if r["заряд"] is not None else "—"
        print(f"  {str(r['имя'])[:22]:22s} {r['якорей']:>7d} "
              f"{r['черновиков']:>11d} {z:>8s}")
    print()
    print(f"  всего жителей: {len(itog)}")
    print()
    print("  ── ЧТО ДАЛЬШЕ ──")
    print("  Смотри разбор глазами. Где Брат ошибся — скажи.")
    print("  Слово Шефа по каждой строке (род / метка) → патч миграции.")
    print("  Код не решает. Решаешь ты. (вариант Б)")
    print()


if __name__ == "__main__":
    main()
