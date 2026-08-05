# -*- coding: utf-8 -*-
# PAMYAT_RYNOK_SUDYA_V1
"""
ПАТЧ ПАМЯТИ: торговый вывод твердеет от РЫНКА, а не от повтора.

ЧТО БЫЛО СЛОМАНО
    dopisat_vyvod(pattern=...) поднимал маяк в метку по счётчику "раз":
    три раза встретился тот же ключ — маяк догорел, встала метка.
    Результата никто не спрашивал. Значит трейдер, трижды сказавший
    "здесь вход" и трижды сливший, получал ТВЁРДОЕ знание из своей
    ошибки. Дурная привычка закреплялась тем же механизмом, что и
    хорошая.

ЧТО СТАНОВИТСЯ
    Для выводов с откуда="рынок"/"сделка" счётчик повторов больше не
    поднимает. Поднимает ВЕРДИКТ: verdikt_rynka(pattern, plus=True/False),
    который зовётся при ЗАКРЫТИИ сделки, когда результат уже факт.

      подтверждений >= 3 и больше опровержений  -> маяк встаёт меткой
      опровержений  >= 3 и больше подтверждений -> маяк гаснет в архив
      метку рынок опроверг 3 раза               -> метка ПАДАЕТ обратно
                                                   в маяки (разучивание)

    Последнее — главное. Раньше метка была вечной: ошибку, однажды
    затвердевшую, снять было нечем. Теперь память умеет ошибаться и
    умеет отучаться.

ЧЕГО ПАТЧ НЕ ТРОГАЕТ
    Выводы с откуда="учёба"/"жизнь"/профессия работают ровно как
    работали — порог 3 по повтору. Академия, просев, кабинет жителя
    ничего не заметят. Это только про рынок.

ЗАПУСК из корня репо:
    python patch_pamyat_rynok_sudya.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "PAMYAT_RYNOK_SUDYA_V1"
TARGET = Path("жители") / "dvizhok.py"
BAK = Path("жители") / "dvizhok.py.bak_rynok_sudya"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — константы рядом с порогом повтора
# ═══════════════════════════════════════════════════════════
A1_OLD = """    PROMOTE_THRESHOLD = 3
    DRAFT_CAP = 6   # черновиков живёт не больше — тоже не резиновый склад
"""

A1_NEW = """    PROMOTE_THRESHOLD = 3
    DRAFT_CAP = 6   # черновиков живёт не больше — тоже не резиновый склад

    # PAMYAT_RYNOK_SUDYA_V1: у ТОРГОВОГО вывода судья не повтор, а рынок.
    # Повтор говорит "я это часто думаю" — и только. Рынок говорит "ты был
    # прав". Метка обязана расти из второго, иначе трейдер затвердевает
    # в собственной ошибке. Числа те же, что у Пути Зрелости (3), смысл
    # другой: не три упоминания, а три ЗАКРЫТЫЕ сделки.
    RYNOCHNYE_ISTOCHNIKI = ("рынок", "сделка")
    PODTVERZHDENIY_DO_METKI = 3      # закрытых в плюс — маяк встаёт меткой
    OPROVERZHENIY_DO_GASHENIYA = 3   # закрытых в минус — маяк гаснет
    OPROVERZHENIY_DO_PADENIYA = 3    # столько же — и МЕТКА падает обратно
"""

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — подъём по повтору теперь не для рыночных
# ═══════════════════════════════════════════════════════════
A2_OLD = """        promoted = False
        ushlo = []
        if raz >= self.PROMOTE_THRESHOLD:
            # маяк догорел — на его месте встаёт метка
            mayaki = [m for m in mayaki if m is not found]
            ushlo = _lech_metkoy(found["текст"], pattern, raz)
            promoted = True
"""

A2_NEW = """        promoted = False
        ushlo = []
        # PAMYAT_RYNOK_SUDYA_V1: рыночный маяк ЖДЁТ вердикта, повтор его
        # не поднимает. Заводим счётчики сразу, чтобы verdikt_rynka()
        # писал в готовые поля, а не создавал их на лету.
        _sudit_rynok = otkuda in self.RYNOCHNYE_ISTOCHNIKI
        if _sudit_rynok:
            found.setdefault("подтверждений", 0)
            found.setdefault("опровержений", 0)
        if (not _sudit_rynok) and raz >= self.PROMOTE_THRESHOLD:
            # маяк догорел — на его месте встаёт метка
            mayaki = [m for m in mayaki if m is not found]
            ushlo = _lech_metkoy(found["текст"], pattern, raz)
            promoted = True
"""

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 3 — вытеснение маяков: рыночный не должен гаснуть,
# не дождавшись вердикта
# ═══════════════════════════════════════════════════════════
A3_OLD = """            mayaki.sort(key=lambda d: (d.get("раз", 1),
                                       d.get("первый_раз", "")))
"""

A3_NEW = """            # PAMYAT_RYNOK_SUDYA_V1: рыночные — в хвост сортировки, значит
            # вытесняются последними. Сделка может закрыться через неделю,
            # обидно погасить маяк за день до ответа рынка.
            mayaki.sort(key=lambda d: (
                1 if d.get("откуда") in self.RYNOCHNYE_ISTOCHNIKI else 0,
                d.get("раз", 1),
                d.get("первый_раз", "")))
"""

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 4 — новый метод перед блоком PAMYAT_ISKRA_V1
# ═══════════════════════════════════════════════════════════
A4_OLD = """    # PAMYAT_ISKRA_V1: запрос вида «найди тёплое» / «что царапнуло» ищет
"""

A4_NEW = '''    # ═══════════════════════════════════════════════════════
    # PAMYAT_RYNOK_SUDYA_V1 — ВЕРДИКТ РЫНКА
    # ═══════════════════════════════════════════════════════

    def verdikt_rynka(self, pattern: str, plus: bool,
                      fakt: str = "") -> dict:
        """Рынок ответил по СВЕРШИВШЕЙСЯ сделке. Зовётся при ЗАКРЫТИИ,
        не при входе — до закрытия судить нечем.

        pattern — тот же ключ, под которым вывод лёг маяком
                  (например "вход:откат-в-тренд:H4").
        plus    — True, если сделка закрыта в плюс.
        fakt    — необязательная строка для архива (тикет, R, инструмент).

        Четыре исхода:
          маяк набрал подтверждений  -> встаёт МЕТКОЙ (нажитое знание)
          маяк набрал опровержений   -> ГАСНЕТ в архив, честно
          метку рынок опроверг       -> метка ПАДАЕТ обратно в маяки
          ключа нигде нет            -> честное "не нашёл", не выдумываем
        """
        pattern = (pattern or "").strip()
        if not pattern:
            return {"учтено": False, "причина": "пустой ключ"}

        mayaki = self.mayaki()
        metki = self.metki()
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        pole = "подтверждений" if plus else "опровержений"

        # ── случай 1: ключ ещё в маяках (черновик ждёт суда) ──
        m = next((x for x in mayaki if x.get("паттерн") == pattern), None)
        if m is not None:
            m[pole] = int(m.get(pole, 0)) + 1
            m["последний_вердикт"] = now_iso
            za = int(m.get("подтверждений", 0))
            protiv = int(m.get("опровержений", 0))

            if za >= self.PODTVERZHDENIY_DO_METKI and za > protiv:
                mayaki = [x for x in mayaki if x is not m]
                metki.append({
                    "текст": m.get("текст", ""), "паттерн": pattern,
                    "откуда": m.get("откуда", "рынок"), "когда": now_iso,
                    "раз": m.get("раз", 1),
                    "подтверждений": za, "опровержений": protiv,
                })
                if len(metki) > self.METKI_CAP:
                    for old in metki[:len(metki) - self.METKI_CAP]:
                        self._archive_zapis(old.get("текст", ""),
                                            "метка вытеснена (лимит нажитого)")
                    del metki[:len(metki) - self.METKI_CAP]
                self._pisat_etazh(self._metki_path(), metki)
                self._pisat_etazh(self._mayaki_path(), mayaki)
                return {"учтено": True, "исход": "маяк стал меткой",
                        "паттерн": pattern, "за": za, "против": protiv}

            if protiv >= self.OPROVERZHENIY_DO_GASHENIYA and protiv > za:
                mayaki = [x for x in mayaki if x is not m]
                self._archive_zapis(
                    m.get("текст", ""),
                    f"рынок опроверг маяк ({protiv} против {za}) {fakt}".strip())
                self._pisat_etazh(self._mayaki_path(), mayaki)
                return {"учтено": True, "исход": "маяк погашен рынком",
                        "паттерн": pattern, "за": za, "против": protiv}

            self._pisat_etazh(self._mayaki_path(), mayaki)
            return {"учтено": True, "исход": "маяк ждёт дальше",
                    "паттерн": pattern, "за": za, "против": protiv}

        # ── случай 2: ключ уже метка — она тоже под судом ──
        mt = next((x for x in metki if x.get("паттерн") == pattern), None)
        if mt is not None:
            mt[pole] = int(mt.get(pole, 0)) + 1
            mt["последний_вердикт"] = now_iso
            za = int(mt.get("подтверждений", 0))
            protiv = int(mt.get("опровержений", 0))

            # РАЗУЧИВАНИЕ. Раньше метка была вечной: ошибку, однажды
            # затвердевшую, снять было нечем. Рынок передумал — память
            # обязана уметь передумать вслед за ним.
            if protiv >= self.OPROVERZHENIY_DO_PADENIYA and protiv > za:
                metki = [x for x in metki if x is not mt]
                mayaki.append({
                    "текст": mt.get("текст", ""), "паттерн": pattern,
                    "откуда": mt.get("откуда", "рынок"), "раз": 1,
                    "первый_раз": now_iso, "последний_раз": now_iso,
                    "подтверждений": 0, "опровержений": 0,
                    "падала": True,
                })
                self._archive_zapis(
                    mt.get("текст", ""),
                    f"метка упала обратно в маяки: рынок опроверг "
                    f"({protiv} против {za}) {fakt}".strip())
                self._pisat_etazh(self._metki_path(), metki)
                self._pisat_etazh(self._mayaki_path(), mayaki)
                return {"учтено": True, "исход": "метка упала в маяки",
                        "паттерн": pattern, "за": za, "против": protiv}

            self._pisat_etazh(self._metki_path(), metki)
            return {"учтено": True, "исход": "метка устояла",
                    "паттерн": pattern, "за": za, "против": protiv}

        # ── случай 3: ключа нет нигде ──
        return {"учтено": False, "причина": "такого ключа нет ни в маяках, "
                                           "ни в метках", "паттерн": pattern}

    def zhdut_verdikta(self) -> list:
        """Рыночные маяки, по которым рынок ещё не ответил. Для кабинета:
        видно, что висит незакрытым и что вот-вот затвердеет."""
        return [m for m in self.mayaki()
                if m.get("откуда") in self.RYNOCHNYE_ISTOCHNIKI]

    # PAMYAT_ISKRA_V1: запрос вида «найди тёплое» / «что царапнуло» ищет
'''

PRAVKI = [
    ("константы вердикта", A1_OLD, A1_NEW),
    ("подъём по повтору — не для рыночных", A2_OLD, A2_NEW),
    ("вытеснение маяков — рыночные последними", A3_OLD, A3_NEW),
    ("метод verdikt_rynka + zhdut_verdikta", A4_OLD, A4_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    novyy = src
    for imya, old, new in PRAVKI:
        n = novyy.count(old)
        if n != 1:
            print(f"✗ якорь «{imya}»: найден {n} раз (нужно 1). "
                  f"Файл изменился — патч НЕ применён, оригинал цел.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print(f"  {len(src)} → {len(novyy)} символов")
    return 0


if __name__ == "__main__":
    sys.exit(main())
