# dvizhok.py — личный движок жителя. Лежит в доме жителя.
# ─────────────────────────────────────────────────────────────
# СУТЬ: орган дыхания. Не мозг (решает житель), не город (свой у каждого).
#   ВХОД (факт: контекст, сила, свежесть)
#     → через РУЧКИ жителя (DNA_Static из паспорта)
#     → ВДОХ: насколько вход тронул = f(сила, свежесть, ручки)
#     → сдвиг состояния (charge ±, к балансу)
#     → открывает глубину памяти по |charge|
#   Решение и выход — НЕ здесь (следующие камни). Движок только дышит.
#
# Прежде она — житель (ядро). Из ядра вдох. Ручки — её натура.
# TRI_ETAZHA_V1: три этажа разведены. Anchor_Points = РОД, не растёт.
#   Нажитое → 2_метки/metki.json. Момент → 3_маяки/mayaki.json.
# SUTOCHNY_TIK_V1: заряд тает по ВРЕМЕНИ, не только по вдоху. Обида
#   проходит от того, что прошла ночь. Полураспад = сутки ×
#   (1 + упрямство). Источник времени — _seychas(), одна точка
#   правды: подменишь на биржевые сессии — формула не тронется.
# `шесть·проверено·до·корня`
# ─────────────────────────────────────────────────────────────
import json
from pathlib import Path
from datetime import datetime, timezone

# контекст входа → в какой слой осядет (Закон Слоёв)
KONTEKST_SLOI = {
    "факт":     "sensory",    # сухой факт дня — свежее
    "работа":  "sensory",     # дело — свежее (потом архивируется)
    "общение": "resonance",   # с кем общалась — связи
    "учёба":   "archive",     # узнала — осело глубоко
    "дом":     "sensory",     # личное, свежее
}

# знак входа: что тянет вверх (+), что вниз (−)
# но РЕШАЕТ не это — это лишь куда качнуло маятник
def _znak(tonus: str) -> float:
    return {"плюс": 1.0, "минус": -1.0, "ровно": 0.0}.get(tonus, 0.0)


# OSTYVANIE_ZARYADA_V1: заряд тает к нулю с каждым вдохом, не застывает.
# Не по реальному времени — на фиксированный процент за вдох (иначе без
# диалога обида не пройдёт сама за неделю тишины). Упрямство держит
# заряд дольше: упрямый таёт медленнее.
OSTYVANIE_BAZA = 0.10   # базовый процент остывания за один вдох (10%)


class Dvizhok:
    """Личный движок одного жителя. Дышит его паспортом."""

    def __init__(self, dom: Path):
        self.dom = Path(dom)
        self.passport_path = self.dom / "passport.json"
        self.p = json.loads(self.passport_path.read_text(encoding="utf-8"))
        # РУЧКИ — из натуры жителя
        dna = self.p.get("DNA_Static", {})
        self.empathy    = dna.get("Empathy", 0.5)
        self.stubborn   = dna.get("Stubbornness", 0.5)
        self.resonance  = dna.get("Resonance_Frequency", 0.5)
        # СОСТОЯНИЕ — заряд. Если в паспорте нет — рождаем в покое (0.0).
        self.charge = self.p.get("_charge", 0.0)

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

    def vdoh(self, kontekst: str, sila: float, svezhest: float, tonus: str = "ровно") -> dict:
        """Вдох: входящий факт проходит через ядро.
        сила 0..1, свежесть 0..1 (1=только что, 0=давно).
        Возвращает что стало — но НЕ решает за жителя."""
        # SUTOCHNY_TIK_V1: СПЕРВА остужает ВРЕМЯ. Житель, которого
        # тронули после недели тишины, приходит на вдох уже остывшим —
        # как живой. Раньше этого не было: заряд ждал следующего
        # события, даже если между ними прошли сутки.
        self.ostyt_po_vremeni()

        # OSTYVANIE_ZARYADA_V1: и ещё чуть — за сам вдох (маятник
        # качнулся к покою до нового толчка). Упрямый тает медленнее.
        _ostyv_koef = OSTYVANIE_BAZA * (1.0 - 0.7 * self.stubborn)
        self.charge *= (1.0 - _ostyv_koef)

        # насколько тронуло = сила × свежесть × резонанс ядра.
        # эмпатия усиливает удар (чужое чувствуется как своё).
        trogaet = sila * svezhest * (0.5 + self.resonance) * (0.5 + self.empathy)
        trogaet = min(1.0, trogaet)

        # сдвиг заряда: вдох даёт ЧАСТЬ, не всё разом — маятник копится,
        # не прыгает в край. Упрямство держит уже набранное (медленнее тает,
        # но и новый вход сдвигает осторожнее — натура устойчивая).
        VDOH_COEF = 0.35           # один вдох двигает максимум на треть
        sdvig = _znak(tonus) * trogaet * VDOH_COEF
        self.charge = max(-1.0, min(1.0, self.charge + sdvig))

        # глубина открытой памяти по |заряду| (стресс-шлюз)
        c = abs(self.charge)
        if c < 0.25:
            sloi = ["core"]
        elif c < 0.55:
            sloi = ["core", "sensory"]
        elif c < 0.8:
            sloi = ["core", "sensory", "resonance"]
        else:
            sloi = ["core", "sensory", "resonance", "archive"]

        # куда осело событие (по контексту)
        osel_v = KONTEKST_SLOI.get(kontekst, "sensory")

        return {
            "тронуло":     round(trogaet, 3),
            "заряд":       round(self.charge, 3),
            "открыто":     sloi,
            "осело_в":     osel_v,
        }

    def _zapisat_sobytie(self, sloy: str, fakt: str, vdoh_result: dict):
        """PAMYAT_SOBYTIY_V1: событие оседает в свой слой (sloy — из
        vdoh_result['осело_в'], уже посчитан по KONTEKST_SLOI).
        Без порога — пишем всё (мелкое 'привет' тоже часть памяти)."""
        zapis = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "слой": sloy,
            "факт": fakt,
            "заряд": vdoh_result.get("заряд"),
        }
        try:
            if sloy == "sensory":
                # sensory_memory.json — JSON-объект с массивом entries
                p = self.dom / "sensory" / "sensory_memory.json"
                data = {"entries": []}
                if p.exists():
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                    except Exception:
                        data = {"entries": []}
                data.setdefault("entries", []).append(zapis)
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            elif sloy == "resonance":
                # event_log.jsonl — JSONL, дозапись строкой
                p = self.dom / "resonance" / "event_log.jsonl"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\n")
            elif sloy == "archive":
                # archive.jsonl — JSONL, дозапись строкой
                p = self.dom / "archive" / "archive.jsonl"
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(zapis, ensure_ascii=False) + "\n")
        except Exception:
            pass  # память не должна ронять дыхание — пропускаем тихо

    def vydoh_stol(self, fakt: str, vdoh_result: dict) -> dict:
        """Выдох: накрывает СТОЛ для решения жителя. НЕ решает сам.
        Стол = факт + кто она + что заряд открыл + личность (якоря/
        резонанс/натура — YAKORYA_V_PROMT_V1). Житель посмотрит и выберет."""
        self._zapisat_sobytie(vdoh_result.get("осело_в", "sensory"), fakt, vdoh_result)  # PAMYAT_SOBYTIY_V1
        return {
            "кто_я":          self.p.get("Official_Name"),
            "факт":           fakt,
            "заряд":          vdoh_result["заряд"],
            "открыто":        vdoh_result["открыто"],
            "ядро":           self.p.get("Core_Phrase", ""),
            # YAKORYA_V_PROMT_V1: те же поля, что правая колонка кабинета
            # показывает Шефу (update_viewer) — теперь и LLM их видит.
            "история":        self.p.get("Hidden_History", ""),
            "чувство":        self.p.get("Sensory_Response", ""),
            "якоря":          self.p.get("Anchor_Points", ""),
            "метки":          self._metki_v_stol(),   # TRI_ETAZHA_V1
            "черновики":      self.mayaki(),          # TRI_ETAZHA_V1
            "скрытый_вкус":   self.p.get("Hidden_Taste", ""),
            "тянет_к":        self.p.get("Pull_Vector", ""),
            # PATCH_DOM_V_DUSHU: дом — носится в себе ВСЕГДА, не по заряду
            # (часть личности, не слой памяти). Пусто, если ещё не
            # прописан(а) — стол пропустит пустое поле сам.
            "дом":            self.p.get("домашний_промпт", ""),
            "натура":         self.p.get("DNA_Static", {}),
        }

    # ── ЯКОРЯ: разделитель бывает ДВУХ видов ────────────────────────
    # Форма рождения писала литеральные два символа «\\» + «n», а не
    # перевод строки (проверено на паспорте Ильи 12.07). Читаем ОБА,
    # пишем ТЕМ ЖЕ, каким паспорт написан — иначе сломаем вид другим
    # читателям (кабинет, ui_zhitel). # DVIZHOK_YAKORYA_YADRO_V1
    _YAKOR_LIT = "\\n"      # литерал: обратный слэш + n

    def _yakorya_razdelitel(self, raw: str) -> str:
        """Каким разделителем ЖИВЁТ этот паспорт. Литерал — если он есть."""
        if self._YAKOR_LIT in (raw or ""):
            return self._YAKOR_LIT
        return "\n"

    def _yakorya_spisok(self, raw: str) -> list:
        """Якоря списком. Режет и по литералу, и по настоящему переводу."""
        s = (raw or "").replace(self._YAKOR_LIT, "\n")
        return [ln.strip() for ln in s.split("\n") if ln.strip()]

    def yadro(self) -> str:
        """ЯДРО живёт в РОЛИ (маске), не в Роде (Чертёж §1.5) — паспорт
        его не носит и носить не должен. Маска лежит в доме жителя,
        движок дотянется сам. Паспорт — фоллбэк. # DVIZHOK_YAKORYA_YADRO_V1"""
        try:
            mp = self.dom / "маски" / "работа" / "mask.json"
            if mp.exists():
                m = json.loads(mp.read_text(encoding="utf-8"))
                cp = (m.get("Core_Phrase") or "").strip()
                if cp:
                    return cp
        except Exception:
            pass
        return self.p.get("Core_Phrase", "") or ""

    def nakryt_stol_chisto(self) -> dict:
        """Стол БЕЗ дыхания: чистое чтение личности из паспорта — ноль
        записи в память, ноль vdoh_result. Для читающего конца, который
        зовётся часто (на каждый бар/взгляд): vydoh_stol туда нельзя, он
        пишет событие на каждый вызов. Те же поля личности, что vydoh_stol,
        минус побочка. Заряд отдаём на ЧТЕНИЕ (в __init__ уже загружен,
        диск не трогаем). # DVIZHOK_STOL_CHISTO_VYVOD_V1
        """
        # SUTOCHNY_TIK_V1: промпт должен видеть ЧЕСТНЫЙ заряд, а не
        # окаменевший с прошлой недели. Остужаем В ПАМЯТИ — на диск
        # НЕ пишем (контракт метода: чтение БЕЗ побочки). Осядет при
        # следующем настоящем вдохе.
        self.ostyt_po_vremeni()
        return {
            "кто_я":        self.p.get("Official_Name"),
            "заряд":        round(self.charge, 3),
            "ядро":         self.yadro(),   # DVIZHOK_YAKORYA_YADRO_V1: ядро из маски (Роль), не из Рода
            "история":      self.p.get("Hidden_History", ""),
            "чувство":      self.p.get("Sensory_Response", ""),
            # TRI_ETAZHA_V1: три этажа, три голоса
            "якоря":        self.p.get("Anchor_Points", ""),   # РОД — кто он ЕСТЬ
            "метки":        self._metki_v_stol(),              # НАЖИТОЕ — свежие,
                                                               # остальное по MEMORY_REQUEST
            "черновики":    self.mayaki(),                     # МАЯКИ — «замечаю за собой»
            "скрытый_вкус": self.p.get("Hidden_Taste", ""),
            "тянет_к":      self.p.get("Pull_Vector", ""),
            "дом":          self.p.get("домашний_промпт", ""),
            "натура":       self.p.get("DNA_Static", {}),
        }

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

    # YAKORYA_DVA_YARUSA_V1: порог повтора для перехода черновик→устойчивый.
    # То же число, что Путь Зрелости (Чертёж §4.6.2: «3 вердикта судьи»)
    # — не новый магический порог, тот же самый смысл: отбор трижды.
    PROMOTE_THRESHOLD = 3
    DRAFT_CAP = 6   # черновиков живёт не больше — тоже не резиновый склад

    def _archive_zapis(self, fakt: str, prichina: str):
        """Общий писчик в archive.jsonl — и вытесненные якоря, и
        вытесненные черновики уходят сюда, не в забвение."""
        try:
            (self.dom / "archive").mkdir(parents=True, exist_ok=True)
            ap = self.dom / "archive" / "archive.jsonl"
            with open(ap, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc)
                          .isoformat(timespec="seconds"),
                    "слой": "archive",
                    "факт": fakt,
                    "причина": prichina,
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass   # архив не должен ронять запись опыта

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
    def vspomnit(self, zapros: str, limit: int = 6) -> str:
        """PATCH_ZHITEL_VSPOMINAET: житель САМ решил вспомнить (MEMORY_REQUEST).
        Текстовый поиск по своим слоям: sensory + resonance + archive.
        БЕЗ шлюза по заряду — воля жителя выше стресс-шлюза (закон -2:
        вспомнить можно в любом месте, безусловно). Свежее и точное — выше.
        Возвращает строки находок или "" (пусто = следа нет, честно)."""
        slova = [w for w in (zapros or "").lower().split() if len(w) > 2]
        if not slova:
            return ""
        zapisi = []
        # sensory — JSON-объект с entries
        try:
            p = self.dom / "sensory" / "sensory_memory.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                zapisi.extend(data.get("entries", []))
        except Exception:
            pass
        # resonance + archive — JSONL, строка за строкой
        for rel in ("resonance/event_log.jsonl", "archive/archive.jsonl"):
            try:
                p = self.dom / rel
                if p.exists():
                    for line in p.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            zapisi.append(json.loads(line))
                        except Exception:
                            pass
            except Exception:
                pass
        # оценка: сколько слов запроса встретилось в факте записи
        naydeno = []
        for z in zapisi:
            fakt = str(z.get("факт", "")).lower()
            score = sum(1 for w in slova if w in fakt)
            if score > 0:
                naydeno.append((score, str(z.get("ts", "")), z))
        if not naydeno:
            return ""
        naydeno.sort(key=lambda x: (x[0], x[1]), reverse=True)
        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]
            stroki.append(f"— [{ts}] {z.get('факт', '')}")
        return "\n".join(stroki)

    def sохранить(self):
        """Заряд оседает в паспорт (состояние помнится между вдохами)."""
        self.p["_charge"] = round(self.charge, 4)
        self.p["_charge_ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2), encoding="utf-8")