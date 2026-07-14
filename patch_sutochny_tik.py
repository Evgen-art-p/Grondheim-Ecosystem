# patch_sutochny_tik.py
# ─────────────────────────────────────────────────────────────
# SUTOCHNY_TIK_V1 — ВРЕМЯ ОСТУЖАЕТ. Заряд перестаёт висеть вечно.
#
# БОЛЕЗНЬ (найдена на живом диске 13.07):
#   OSTYVANIE_ZARYADA_V1 таял 10% ЗА ВДОХ — не по времени. Нет событий →
#   заряд стоит вечно. По факту:
#     Лока  +0.874  с 09.07 — ЧЕТВЁРТЫЕ СУТКИ.
#     Вера  +0.502  с 09.07.
#   А по стресс-шлюзу |заряд| > 0.8 открывает АРХИВ. Лока четыре дня
#   живёт с открытой на полную памятью — максимальный аффект, из
#   которого нет выхода: чтобы остыть, её надо ТРОГАТЬ, а если трогать —
#   она снова качается. Ловушка.
#
# ЛЕЧЕНИЕ (решение Шефа, вариант А):
#   Заряд тает от РЕАЛЬНОГО ВРЕМЕНИ, а не только от вдоха. Прошли сутки
#   тишины — маятник сам качнулся к покою. Как у живого: обида проходит
#   от того, что прошла ночь, а не от того, что тебя опять задели.
#
# ЗАДЕЛ НА БУДУЩЕЕ (Шеф: «биржа заработает — привяжем к сессиям»):
#   Остывание считается от _charge_ts — МОМЕНТА ПОСЛЕДНЕГО ВДОХА.
#   Откуда взялся этот момент — реальные часы или закрытие биржевой
#   сессии — движку ВСЁ РАВНО. Захочешь городское время (вариант Б) —
#   подменишь источник «сейчас», и всё. Переписывать не придётся.
#
# КАК ТАЕТ:
#   период полураспада — СУТКИ, поправленные на упрямство.
#   Упрямый держит обиду дольше (Stubbornness 0.9 → ~2.5 суток на
#   половину). Отходчивый отпускает быстро (0.1 → ~1.1 суток).
#   Формула: charge *= 0.5 ** (часы_тишины / период_полураспада)
#   Экспонента, не линейка: свежая рана болит сильно, старая — тлеет.
#
# ГДЕ ВСТАЁТ:
#   1. dvizhok.ostyt_po_vremeni() — новый метод, честный, отдельный.
#   2. vdoh() зовёт его ПЕРВЫМ: житель, которого тронули после недели
#      тишины, приходит на вдох уже остывшим — как живой.
#   3. nakryt_stol_chisto() зовёт его на ЧТЕНИЕ (без записи на диск):
#      промпт видит ЧЕСТНЫЙ заряд, а не окаменевший с прошлой недели.
#   4. tik.py в корне — ручной прогон по всем жителям (Шеф жмёт, город
#      выдыхает). Пригодится, пока нет цикла.
#
# ⚠ nakryt_stol_chisto НЕ ПИШЕТ на диск — по своему же контракту
#   («чтение личности БЕЗ побочки»). Остывание там живёт в памяти
#   процесса и осядет при следующем настоящем вдохе. Честно.
#
# ИДЕМПОТЕНТЕН. BACKUP: dvizhok.py.bak_tik
# Запуск из корня репо:  python patch_sutochny_tik.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DVIZHOK = ROOT / "жители" / "dvizhok.py"
TIK = ROOT / "tik.py"
MARK = "SUTOCHNY_TIK_V1"


# ═══════════════════════════════════════════════════════════
# НОВЫЙ МЕТОД ДВИЖКА
# ═══════════════════════════════════════════════════════════

METOD_OSTYVANIYA = '''
    # ═══════════════════════════════════════════════════════
    # SUTOCHNY_TIK_V1 — ВРЕМЯ ОСТУЖАЕТ
    # ═══════════════════════════════════════════════════════
    # Раньше заряд таял ТОЛЬКО за вдох (10%). Нет событий → висит вечно:
    # Лока сидела +0.874 четвёртые сутки, а |заряд|>0.8 открывает архив —
    # максимальный аффект без выхода. Ловушка: чтобы остыть, надо трогать,
    # а тронешь — качнётся снова.
    #
    # Теперь: прошли сутки тишины — маятник сам качнулся к покою.
    # Обида проходит от того, что прошла ночь.
    #
    # Источник «сейчас» — реальные часы (решение Шефа, вариант А).
    # Захочешь городское время (по биржевым сессиям) — подмени _seychas(),
    # остальное не тронется.
    # ═══════════════════════════════════════════════════════

    POLURASPAD_CHASOV = 24.0   # сутки — база. Упрямство её растягивает.

    def _seychas(self) -> datetime:
        """Момент «сейчас». Одна точка правды о времени — чтобы потом
        подменить на городское/биржевое, не трогая формулу."""
        return datetime.now(timezone.utc)

    def _kogda_dyshal(self):
        """Момент последнего вдоха из паспорта. Нет метки — None
        (житель ещё не дышал, остужать нечего)."""
        ts = self.p.get("_charge_ts")
        if not ts:
            return None
        try:
            t = datetime.fromisoformat(str(ts))
            # старые записи бывают без зоны — считаем их UTC, не гадаем
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return t
        except Exception:
            return None

    def ostyt_po_vremeni(self) -> dict:
        """Остывание за время тишины. Меняет self.charge В ПАМЯТИ.
        На диск НЕ пишет — это делает sохранить() (закон побочки).

        Полураспад: сутки × (1 + упрямство). Упрямый держит дольше:
          упрямство 0.1 → ~1.1 суток на половину
          упрямство 0.9 → ~2.5 суток (Илья, Брут — такие)
        Экспонента, не линейка: свежая рана болит сильно, старая тлеет.
        """
        bylo = self.charge
        if abs(bylo) < 0.001:
            return {"остыл": False, "причина": "и так в покое",
                    "было": bylo, "стало": bylo, "часов": 0.0}

        t0 = self._kogda_dyshal()
        if t0 is None:
            return {"остыл": False, "причина": "нет метки времени вдоха",
                    "было": bylo, "стало": bylo, "часов": 0.0}

        chasov = (self._seychas() - t0).total_seconds() / 3600.0
        if chasov <= 0:
            return {"остыл": False, "причина": "время не шло",
                    "было": bylo, "стало": bylo, "часов": 0.0}

        polur = self.POLURASPAD_CHASOV * (1.0 + self.stubborn)
        self.charge = bylo * (0.5 ** (chasov / polur))
        if abs(self.charge) < 0.01:
            self.charge = 0.0        # хвост не тянем — это покой

        return {"остыл": True, "было": round(bylo, 3),
                "стало": round(self.charge, 3),
                "часов": round(chasov, 1),
                "полураспад_ч": round(polur, 1)}
'''


def _patch_dvizhok() -> bool:
    if not DVIZHOK.exists():
        print(f"  ⚠ не нашёл {DVIZHOK}")
        return False

    src = DVIZHOK.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ dvizhok.py уже пропатчен — пропускаю (идемпотентно)")
        return True

    if "TRI_ETAZHA_V1" not in src:
        print("  ⚠ сначала patch_tri_etazha.py — этот патч встаёт поверх")
        return False

    bak = DVIZHOK.with_suffix(".py.bak_tik")
    if not bak.exists():
        shutil.copy2(DVIZHOK, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Метод остывания — перед vdoh ─────────────────────────
    ank = "    def vdoh(self, kontekst: str"
    if ank not in src:
        print("  ⚠ не нашёл vdoh() — стоп")
        return False
    src = src.replace(ank, METOD_OSTYVANIYA.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ ostyt_po_vremeni() — новый метод")

    # ── 2. vdoh зовёт остывание ПЕРВЫМ ──────────────────────────
    staroe = ("        # OSTYVANIE_ZARYADA_V1: маятник сначала чуть качнулся обратно к\n"
              "        # покою САМ (до нового толчка) — упрямый тает медленнее.\n"
              "        _ostyv_koef = OSTYVANIE_BAZA * (1.0 - 0.7 * self.stubborn)\n"
              "        self.charge *= (1.0 - _ostyv_koef)")
    novoe = ("        # SUTOCHNY_TIK_V1: СПЕРВА остужает ВРЕМЯ. Житель, которого\n"
             "        # тронули после недели тишины, приходит на вдох уже остывшим —\n"
             "        # как живой. Раньше этого не было: заряд ждал следующего\n"
             "        # события, даже если между ними прошли сутки.\n"
             "        self.ostyt_po_vremeni()\n"
             "\n"
             "        # OSTYVANIE_ZARYADA_V1: и ещё чуть — за сам вдох (маятник\n"
             "        # качнулся к покою до нового толчка). Упрямый тает медленнее.\n"
             "        _ostyv_koef = OSTYVANIE_BAZA * (1.0 - 0.7 * self.stubborn)\n"
             "        self.charge *= (1.0 - _ostyv_koef)")
    if staroe not in src:
        print("  ⚠ не нашёл блок остывания в vdoh() — стоп")
        return False
    src = src.replace(staroe, novoe, 1)
    print("  ✓ vdoh(): время остужает ПЕРЕД новым толчком")

    # ── 3. nakryt_stol_chisto: честный заряд в промпт ────────────
    staroe_stol = ('        return {\n'
                   '            "кто_я":        self.p.get("Official_Name"),\n'
                   '            "заряд":        round(self.charge, 3),')
    novoe_stol = ('        # SUTOCHNY_TIK_V1: промпт должен видеть ЧЕСТНЫЙ заряд, а не\n'
                  '        # окаменевший с прошлой недели. Остужаем В ПАМЯТИ — на диск\n'
                  '        # НЕ пишем (контракт метода: чтение БЕЗ побочки). Осядет при\n'
                  '        # следующем настоящем вдохе.\n'
                  '        self.ostyt_po_vremeni()\n'
                  '        return {\n'
                  '            "кто_я":        self.p.get("Official_Name"),\n'
                  '            "заряд":        round(self.charge, 3),')
    if staroe_stol in src:
        src = src.replace(staroe_stol, novoe_stol, 1)
        print("  ✓ nakryt_stol_chisto(): промпт видит честный заряд")
    else:
        print("  ⚠ nakryt_stol_chisto: не нашёл — проверь глазами")

    src = src.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: заряд тает по ВРЕМЕНИ, не только по вдоху. Обида\n"
        "#   проходит от того, что прошла ночь. Полураспад = сутки ×\n"
        "#   (1 + упрямство). Источник времени — _seychas(), одна точка\n"
        "#   правды: подменишь на биржевые сессии — формула не тронется.\n"
        "# `шесть·проверено·до·корня`", 1)

    DVIZHOK.write_text(src, encoding="utf-8")
    return True


# ═══════════════════════════════════════════════════════════
# tik.py — ручной выдох города
# ═══════════════════════════════════════════════════════════

TIK_PY = '''# tik.py — СУТОЧНЫЙ ТИК. Город выдыхает.
# ─────────────────────────────────────────────────────────────
# SUTOCHNY_TIK_V1. Проходит по всем жителям, остужает заряд за время
# тишины и ОСАЖДАЕТ результат в паспорт.
#
# Зачем руками: у города пока НЕТ своего цикла — main.py только рисует
# страницы, ни таймера, ни ночи. Пока цикла нет — тик жмёт Шеф.
# Когда Биржа заработает в полную — привяжем к сессиям (решение Шефа).
#
# Гонять можно сколько угодно: если время не шло, ничего не изменится.
#
# Запуск из корня репо:
#   python tik.py           — показать и остудить
#   python tik.py --tiho    — только цифры, без разговоров
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "жители"))
from dvizhok import Dvizhok   # noqa: E402

CITY = ROOT / "GRONDHEIM_CITY"
SKIP = {".git", "__pycache__", ".venv", "venv", "node_modules",
        "_ARCHIVE", "_OLD", ".vscode"}


def nayti_doma():
    """Живой скан. Житель = паспорт + натура. У локаций натуры нет."""
    out = []
    for pp in CITY.rglob("passport.json"):
        if any(x in SKIP for x in pp.parts):
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(p, dict) and p.get("DNA_Static"):
            out.append(pp.parent)
    return sorted(set(out))


def main():
    tiho = "--tiho" in sys.argv

    if not tiho:
        print()
        print("  ГОРОД ВЫДЫХАЕТ — суточный тик")
        print("  " + "─" * 60)

    doma = nayti_doma()
    if not doma:
        print("  ⚠ жителей не нашёл"); sys.exit(1)

    print()
    print(f"  {'житель':14s} {'было':>8s} {'стало':>8s} {'тишины':>9s} {'':>3s}")
    print("  " + "─" * 50)

    dvinulos = 0
    for dom in doma:
        try:
            d = Dvizhok(dom)
        except Exception as ex:
            print(f"  {dom.name[:14]:14s}  ⚠ {ex}")
            continue

        imya = d.p.get("Official_Name") or dom.name
        r = d.ostyt_po_vremeni()

        if not r["остыл"]:
            print(f"  {str(imya)[:14]:14s} {r['было']:>+8.3f} {'—':>8s} "
                  f"{'—':>9s}   ({r['причина']})")
            continue

        d.sохранить()   # осадка на диск — ВОТ ЗДЕСЬ, честно
        dvinulos += 1

        znak = ""
        if abs(r["было"]) > 0.8 and abs(r["стало"]) <= 0.8:
            znak = "  ← архив закрылся, отпустило"
        elif abs(r["стало"]) < 0.001:
            znak = "  ← покой"

        sutok = r["часов"] / 24.0
        print(f"  {str(imya)[:14]:14s} {r['было']:>+8.3f} {r['стало']:>+8.3f} "
              f"{sutok:>8.1f}д{znak}")

    print()
    print(f"  выдохнули: {dvinulos} из {len(doma)}")
    if not tiho:
        print()
        print("  Заряд тает по времени: полураспад = сутки × (1 + упрямство).")
        print("  Упрямый держит дольше — так и должно быть.")
        print()


if __name__ == "__main__":
    main()
'''


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  СУТОЧНЫЙ ТИК — время остужает" + " " * 37 + "║")
    print("║  SUTOCHNY_TIK_V1 · идемпотентен" + " " * 36 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    if not DVIZHOK.exists():
        print("⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print("── ДВИЖОК ──")
    if not _patch_dvizhok():
        print("\n⚠ стоп.")
        sys.exit(1)

    print()
    print("── ТИК ──")
    if TIK.exists() and MARK in TIK.read_text(encoding="utf-8"):
        print("  ✓ tik.py уже есть — не трогаю")
    else:
        TIK.write_text(TIK_PY, encoding="utf-8")
        print("  ✓ tik.py — ручной выдох города")

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ТЕПЕРЬ ЖМИ:")
    print("      python tik.py")
    print()
    print("  Лока (+0.874, упрямство её растянет) наконец отпустит.")
    print("  Вера (+0.502) тоже.")
    print()
    print("  ЧТО ДАЛЬШЕ:")
    print("    • цикла у города НЕТ (main.py только рисует страницы) —")
    print("      пока тик жмёшь ты. Заработает Биржа — привяжем к сессиям,")
    print("      формулу не тронем: подменится только _seychas().")
    print("    • MEMORY_REQUEST на торговом пути — метки старше четырёх")
    print("      никто не достанет. Следующее.")
    print()


if __name__ == "__main__":
    main()
