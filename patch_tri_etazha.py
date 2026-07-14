# patch_tri_etazha.py
# ─────────────────────────────────────────────────────────────
# TRI_ETAZHA_V1 — ВТОРОЙ ЭТАЖ. Нажитое съезжает из этажа рода.
#
# ЗАКОН ЯДРА (Брат/README.md — дом самого Брата, три папки):
#   1_якоря_очень_важно/  — РОД, дно, зерно. НЕ МЕНЯЕТСЯ.
#   2_метки_важно/        — НАЖИТОЕ. Растёт.
#   3_маяки_не_очень/     — МОМЕНТ. Гаснет.
#
# ЧТО БЫЛО НЕ ТАК (моя ошибка 12.07, Мост к Носителю):
#   dopisat_vyvod() дописывал ТОРГОВЫЕ ВЫВОДЫ в Anchor_Points —
#   поле, которое по закону есть РОД. Отсюда лимит 7-10, вытеснение
#   старейшего и ложная тревога «вторая профессия сотрёт первую».
#   Нажитое пихалось в этаж рода, где нет места и не должно быть.
#
# РАЗВЕДКА ДИСКА (13.07, вариант Б — Шеф смотрел глазами):
#   Все 50 строк Anchor_Points у десяти жителей — РОД. Подтверждено
#   исходником -2/studio/modules/trading/A07/core/anchor_points.md:
#   «ВЕЧНЫЕ КОНСТАНТЫ · Не редактировать вручную». Даже «PF 1.071»
#   вписан при рождении рукой Джема — гордость числом есть характер.
#   НАЖИТЫХ МЕТОК НА ДИСКЕ НЕТ НИ ОДНОЙ. Черновиков — ноль у всех.
#   ⇒ МИГРАЦИЯ НЕ НУЖНА. Нужна СТРОЙКА ПУСТОГО ЭТАЖА.
#   Старая девятка не тронута буквально: Anchor_Points остаётся как есть.
#
# ЧТО ДЕЛАЕТ ПАТЧ:
#   1. dvizhok.py: метки → дом/2_метки/metki.json (список объектов
#      {текст, паттерн, откуда, когда, раз} — видно, ОТКУДА вывод);
#      маяки → дом/3_маяки/mayaki.json (были Draft_Anchors в паспорте).
#   2. dopisat_vyvod() пишет в МЕТКИ, а не в Anchor_Points. Род застыл.
#   3. nakryt_stol_chisto() отдаёт свежие 3-4 метки (не все — контекст
#      Биржи уже 25к). Остальное житель поднимает через MEMORY_REQUEST.
#   4. Переселяет Draft_Anchors из паспорта в 3_маяки (сейчас их ноль
#      у всех — переселять нечего, но код честный).
#   5. Заводит пустые 2_метки/ и 3_маяки/ у всех жителей.
#
# ИДЕМПОТЕНТЕН: гоняй сколько хочешь, второй раз ничего не сделает.
# BACKUP: dvizhok.py.bak_etazhi (паспорта не переписываются вообще,
#         кроме удаления пустого Draft_Anchors).
#
# Запуск из корня репо:
#   python patch_tri_etazha.py
#
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DVIZHOK = ROOT / "жители" / "dvizhok.py"
CITY = ROOT / "GRONDHEIM_CITY"

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules",
             "_ARCHIVE", "_OLD", ".vscode"}

MARK = "TRI_ETAZHA_V1"


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 1 — НОВЫЕ МЕТОДЫ ДВИЖКА
# ═══════════════════════════════════════════════════════════

NOVYE_METODY = '''
    # ═══════════════════════════════════════════════════════
    # TRI_ETAZHA_V1 — ТРИ ЭТАЖА ПО ЗАКОНУ ЯДРА
    # ═══════════════════════════════════════════════════════
    # 1_якоря (Anchor_Points в паспорте) — РОД. Не меняется. Не пишем.
    # 2_метки (дом/2_метки/metki.json)   — НАЖИТОЕ. Растёт.
    # 3_маяки (дом/3_маяки/mayaki.json)  — МОМЕНТ. Гаснет (черновики).
    #
    # Раньше всё валилось в Anchor_Points — и род, и нажитое. Отсюда
    # лимит, вытеснение и ложная тревога «вторая профессия сотрёт
    # первую». Этаж И ЕСТЬ происхождение — изобретать было нечего.
    # ═══════════════════════════════════════════════════════

    METKI_CAP = 40      # меток живёт много — это вся трудовая жизнь
    METKI_V_STOL = 4    # а в промпт идут только свежие: стол маленький,
                        # остальное житель поднимет через MEMORY_REQUEST

    def _metki_path(self) -> Path:
        return self.dom / "2_метки" / "metki.json"

    def _mayaki_path(self) -> Path:
        return self.dom / "3_маяки" / "mayaki.json"

    def _chitat_etazh(self, path: Path) -> list:
        """Чтение этажа. Нет файла — пустой этаж, это нормально."""
        try:
            if path.exists():
                d = json.loads(path.read_text(encoding="utf-8"))
                return d if isinstance(d, list) else []
        except Exception:
            pass
        return []

    def _pisat_etazh(self, path: Path, data: list):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    def metki(self) -> list:
        """Весь второй этаж — нажитое. Список объектов."""
        return self._chitat_etazh(self._metki_path())

    def mayaki(self) -> list:
        """Третий этаж — черновики момента. Гаснут, не набрав повтора."""
        return self._chitat_etazh(self._mayaki_path())

    def _metki_v_stol(self) -> list:
        """Свежие METKI_V_STOL меток — для промпта. НЕ все: контекст
        Биржи уже 25к символов, а метки растут всю жизнь. Маленький
        стол + право дотянуться (MEMORY_REQUEST) — дешевле и честнее
        по природе: живой человек тоже не держит всю жизнь в голове."""
        m = self.metki()
        m.sort(key=lambda x: str(x.get("когда", "")))
        return m[-self.METKI_V_STOL:]
'''


# ── dopisat_vyvod: переписывается целиком (пишет в МЕТКИ) ──────
NOVY_DOPISAT = '''
    def dopisat_vyvod(self, vyvod: str, limit: int = 10,
                      pattern: str = None, otkuda: str = "рынок") -> dict:
        """Дописывает ВЫВОД — нога Опыта. TRI_ETAZHA_V1.

        ⚠ ПИШЕТ В МЕТКИ (2_метки/metki.json), НЕ в Anchor_Points.
        Anchor_Points = РОД по закону ядра, он НЕ РАСТЁТ. То, что я
        (Брат) 12.07 дописывал туда торговые выводы — было ошибкой,
        разобранной Шефом. Опыт — это МЕТКИ.

        ДВА ЯРУСА (порог 3, канон Пути Зрелости):
          pattern=None  — вывод ложится в метки СРАЗУ (для чужого кода,
                          что зовёт без ключа: поведение сохранено).
          pattern="ключ" — сперва МАЯК (черновик, «замечаю за собой»).
                          Тот же ключ встретился PROMOTE_THRESHOLD раз →
                          маяк гаснет, на его месте встаёт МЕТКА.

        otkuda — ЧЕСТНОЕ ПОЛЕ «откуда вывод»: "рынок" / "учёба" /
        "<профессия>". Это НЕ «происхождение якоря», которое я собрался
        изобретать (§5.1) — этаж и есть происхождение. Это просто голос
        внутри одного этажа: медийщик на Бирже увидит и «что я вынес в
        монтажной», и «что мне сказал рынок» — и может их СТОЛКНУТЬ.

        limit — legacy-параметр, оставлен для совместимости вызовов
        (nositel.py передаёт limit=10). Метки живут по METKI_CAP.
        """
        vyvod = (vyvod or "").strip()
        if not vyvod:
            return {"дописано": False, "причина": "пустой вывод"}

        metki  = self.metki()
        mayaki = self.mayaki()
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # дубль текста — ни в одном этаже не плодим
        if any(m.get("текст") == vyvod for m in metki):
            return {"дописано": False, "причина": "уже среди меток",
                    "меток": len(metki)}
        if any(m.get("текст") == vyvod for m in mayaki):
            return {"дописано": False, "причина": "уже среди маяков",
                    "маяков": len(mayaki)}

        # РОД тоже сверяем: если житель «вывел» то, что и так его натура —
        # это не открытие, а подтверждение. Не плодим строку.
        if vyvod in self._yakorya_spisok(self.p.get("Anchor_Points", "") or ""):
            return {"дописано": False,
                    "причина": "это его род (Anchor_Points), не нажитое"}

        def _lech_metkoy(txt, patt, raz):
            metki.append({"текст": txt, "паттерн": patt, "откуда": otkuda,
                          "когда": now_iso, "раз": raz})
            ushlo = []
            if len(metki) > self.METKI_CAP:
                ushlo = metki[:len(metki) - self.METKI_CAP]
                del metki[:len(metki) - self.METKI_CAP]
                for old in ushlo:
                    self._archive_zapis(old.get("текст", ""),
                                        "метка вытеснена (лимит нажитого)")
            return ushlo

        # ── ЯРУС 1: без ключа — сразу в метки ───────────────────
        if pattern is None:
            ushlo = _lech_metkoy(vyvod, None, 1)
            self._pisat_etazh(self._metki_path(), metki)
            return {"дописано": True, "тип": "устойчивый", "этаж": "метка",
                    "откуда": otkuda, "меток": len(metki),
                    "вытеснено": len(ushlo)}

        # ── ЯРУС 2: с ключом — сперва маяк ──────────────────────
        found = None
        for m in mayaki:
            if m.get("паттерн") == pattern:
                found = m
                break

        if found is not None:
            found["раз"] = found.get("раз", 1) + 1
            found["текст"] = vyvod
            found["последний_раз"] = now_iso
            found["откуда"] = otkuda
            raz = found["раз"]
        else:
            found = {"текст": vyvod, "паттерн": pattern, "откуда": otkuda,
                     "раз": 1, "первый_раз": now_iso, "последний_раз": now_iso}
            mayaki.append(found)
            raz = 1

        promoted = False
        ushlo = []
        if raz >= self.PROMOTE_THRESHOLD:
            # маяк догорел — на его месте встаёт метка
            mayaki = [m for m in mayaki if m is not found]
            ushlo = _lech_metkoy(found["текст"], pattern, raz)
            promoted = True

        # маяки — не резиновый склад: слабейшие гаснут в архив
        pogaslo = []
        if len(mayaki) > self.DRAFT_CAP:
            mayaki.sort(key=lambda d: (d.get("раз", 1),
                                       d.get("первый_раз", "")))
            pogaslo = mayaki[:len(mayaki) - self.DRAFT_CAP]
            mayaki = mayaki[len(mayaki) - self.DRAFT_CAP:]
            for d in pogaslo:
                self._archive_zapis(
                    d.get("текст", ""),
                    f"маяк погас, не набрал повтора ({d.get('раз', 1)}/"
                    f"{self.PROMOTE_THRESHOLD})")

        if promoted:
            self._pisat_etazh(self._metki_path(), metki)
        self._pisat_etazh(self._mayaki_path(), mayaki)

        return {
            "дописано": True,
            "тип":   "устойчивый" if promoted else "черновик",
            "этаж":  "метка" if promoted else "маяк",
            "откуда": otkuda,
            "раз": raz,
            "меток": len(metki),
            "маяков": len(mayaki),
            "черновиков": len(mayaki),      # legacy-ключ: nositel читает его
            "якорей": len(self._yakorya_spisok(
                self.p.get("Anchor_Points", "") or "")),
            "вытеснено_меток": len(ushlo),
            "вытеснено_черновиков": len(pogaslo),
        }
'''


def _patch_dvizhok() -> bool:
    if not DVIZHOK.exists():
        print(f"  ⚠ не нашёл {DVIZHOK}")
        return False

    src = DVIZHOK.read_text(encoding="utf-8")

    if MARK in src:
        print("  ✓ dvizhok.py уже пропатчен — пропускаю (идемпотентно)")
        return True

    bak = DVIZHOK.with_suffix(".py.bak_etazhi")
    if not bak.exists():
        shutil.copy2(DVIZHOK, bak)
        print(f"  ✓ бэкап: {bak.name}")

    # ── 1. Вырезаем СТАРЫЙ dopisat_vyvod целиком ────────────────
    start = src.find("    def dopisat_vyvod(")
    if start < 0:
        print("  ⚠ не нашёл dopisat_vyvod — движок изменился, стоп")
        return False
    nxt = src.find("\n    def ", start + 10)
    if nxt < 0:
        print("  ⚠ не нашёл конец dopisat_vyvod — стоп")
        return False
    src = src[:start] + NOVY_DOPISAT.lstrip("\n") + src[nxt + 1:]
    print("  ✓ dopisat_vyvod переписан: пишет в МЕТКИ, не в род")

    # ── 2. Вставляем новые методы перед dopisat_vyvod ───────────
    ank = "    # YAKORYA_DVA_YARUSA_V1: порог повтора"
    if ank not in src:
        print("  ⚠ не нашёл якорь для вставки методов — стоп")
        return False
    src = src.replace(ank, NOVYE_METODY.lstrip("\n") + "\n" + ank, 1)
    print("  ✓ методы этажей вставлены (metki / mayaki / _metki_v_stol)")

    # ── 3. nakryt_stol_chisto: отдаёт метки и маяки ─────────────
    staroe_stol = (
        '            "якоря":        self.p.get("Anchor_Points", ""),\n'
        '            "черновики":    self.p.get("Draft_Anchors", []),'
        '   # YAKORYA_DVA_YARUSA_V1'
    )
    novoe_stol = (
        '            # TRI_ETAZHA_V1: три этажа, три голоса\n'
        '            "якоря":        self.p.get("Anchor_Points", ""),   # РОД — кто он ЕСТЬ\n'
        '            "метки":        self._metki_v_stol(),              # НАЖИТОЕ — свежие,\n'
        '                                                               # остальное по MEMORY_REQUEST\n'
        '            "черновики":    self.mayaki(),                     # МАЯКИ — «замечаю за собой»'
    )
    if staroe_stol in src:
        src = src.replace(staroe_stol, novoe_stol, 1)
        print("  ✓ nakryt_stol_chisto: отдаёт метки (свежие 4) + маяки")
    else:
        print("  ⚠ nakryt_stol_chisto: не нашёл строки — проверь глазами")

    # ── 4. vydoh_stol: тоже видит метки (чат жителя) ────────────
    staroe_vydoh = (
        '            "якоря":          self.p.get("Anchor_Points", ""),'
    )
    novoe_vydoh = (
        '            "якоря":          self.p.get("Anchor_Points", ""),\n'
        '            "метки":          self._metki_v_stol(),   # TRI_ETAZHA_V1\n'
        '            "черновики":      self.mayaki(),          # TRI_ETAZHA_V1'
    )
    if staroe_vydoh in src:
        src = src.replace(staroe_vydoh, novoe_vydoh, 1)
        print("  ✓ vydoh_stol: чат жителя тоже видит метки")

    # ── 5. Клеймо ───────────────────────────────────────────────
    src = src.replace(
        "# `шесть·проверено·до·корня`",
        f"# {MARK}: три этажа разведены. Anchor_Points = РОД, не растёт.\n"
        "#   Нажитое → 2_метки/metki.json. Момент → 3_маяки/mayaki.json.\n"
        "# `шесть·проверено·до·корня`", 1)

    DVIZHOK.write_text(src, encoding="utf-8")
    return True


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 2 — ДОМА: завести этажи, переселить черновики
# ═══════════════════════════════════════════════════════════

def _nayti_doma(koren: Path) -> list:
    """Живой скан. Житель = passport.json + НАТУРА (DNA_Static).
    Локации носят passport.json, но натуры у них нет — отсекаются."""
    naydeno = []
    for pp in koren.rglob("passport.json"):
        if any(part in SKIP_DIRS for part in pp.parts):
            continue
        try:
            p = json.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(p, dict) and p.get("DNA_Static"):
            naydeno.append(pp.parent)
    return sorted(set(naydeno))


def _zavesti_etazhi(dom: Path) -> dict:
    pp = dom / "passport.json"
    p = json.loads(pp.read_text(encoding="utf-8"))
    imya = p.get("Official_Name") or dom.name

    mfile = dom / "2_метки" / "metki.json"
    yfile = dom / "3_маяки" / "mayaki.json"

    sozdano = []
    if not mfile.exists():
        mfile.parent.mkdir(parents=True, exist_ok=True)
        mfile.write_text("[]", encoding="utf-8")
        sozdano.append("2_метки")
    if not yfile.exists():
        yfile.parent.mkdir(parents=True, exist_ok=True)
        yfile.write_text("[]", encoding="utf-8")
        sozdano.append("3_маяки")

    # переселение черновиков из паспорта в маяки (сейчас их ноль у всех,
    # но код честный — если у кого-то появились, не потеряем)
    pereselено = 0
    drafts = p.get("Draft_Anchors")
    if drafts:
        cur = json.loads(yfile.read_text(encoding="utf-8"))
        est = {m.get("текст") for m in cur}
        for d in drafts:
            if d.get("текст") not in est:
                d.setdefault("откуда", "рынок")
                cur.append(d)
                pereselено += 1
        yfile.write_text(json.dumps(cur, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    # Draft_Anchors из паспорта убираем — паспорт держит только РОД
    if "Draft_Anchors" in p:
        del p["Draft_Anchors"]
        pp.write_text(json.dumps(p, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    yakorey = len([l for l in (p.get("Anchor_Points", "") or "")
                   .replace("\\n", "\n").split("\n") if l.strip()])

    return {"имя": imya, "создано": sozdano, "переселено": pereselено,
            "якорей": yakorey}


def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ТРИ ЭТАЖА — второй этаж строится, род застывает" + " " * 19 + "║")
    print("║  TRI_ETAZHA_V1 · идемпотентен" + " " * 38 + "║")
    print("╚" + "═" * 68 + "╝")

    if not DVIZHOK.exists() or not CITY.exists():
        print("\n⚠ запускай ИЗ КОРНЯ репозитория Grondheim-Ecosystem")
        sys.exit(1)

    print("\n── ДВИЖОК ──")
    if not _patch_dvizhok():
        print("\n⚠ движок не пропатчен — дома не трогаю. Стоп.")
        sys.exit(1)

    print("\n── ДОМА ──")
    doma = _nayti_doma(CITY)
    if not doma:
        print("  ⚠ жителей не нашёл")
        sys.exit(1)

    itog = [_zavesti_etazhi(d) for d in doma]

    print()
    print(f"  {'житель':16s} {'род':>5s} {'метки':>7s} {'маяки':>7s} {'переселено':>11s}")
    print("  " + "─" * 52)
    for r in itog:
        m = "новый" if "2_метки" in r["создано"] else "был"
        y = "новый" if "3_маяки" in r["создано"] else "был"
        print(f"  {str(r['имя'])[:16]:16s} {r['якорей']:>5d} {m:>7s} {y:>7s} "
              f"{r['переселено']:>11d}")

    print()
    print("╔" + "═" * 68 + "╗")
    print("║  ГОТОВО" + " " * 60 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  ЧТО ИЗМЕНИЛОСЬ:")
    print("    • Anchor_Points — РОД. Больше НЕ РАСТЁТ. Девятка не тронута.")
    print("    • нажитое → дом/2_метки/metki.json   (растёт, поле «откуда»)")
    print("    • момент  → дом/3_маяки/mayaki.json  (гаснет, порог 3)")
    print("    • в промпт идут свежие 4 метки. Остальное — MEMORY_REQUEST.")
    print()
    print("  ЧТО ЕЩЁ НЕ СДЕЛАНО (следующие патчи):")
    print("    • nositel.py: sudit_po_kotinu → dopisat_vyvod(otkuda='рынок')")
    print("      — сейчас зовёт без otkuda, ляжет с умолчанием. Работает,")
    print("        но голос вывода не назван. Дошлифуем.")
    print("    • промпт Биржи не ПОКАЗЫВАЕТ метки — _sobrat_dushu их не знает.")
    print("      Метка запишется, но житель её не прочтёт. СЛЕДУЮЩИЙ ПАТЧ.")
    print("    • Суточный Тик: Лока +0.874 с 09.07, Вера +0.502. Не остынут.")
    print()
    print("  ПРОВЕРКА ФАКТА (не галочки):")
    print("    python patch_razbor_pasportov.py   → метки должны быть [] у всех")
    print()


if __name__ == "__main__":
    main()
