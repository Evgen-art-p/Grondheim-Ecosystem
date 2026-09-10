# -*- coding: utf-8 -*-
# METKA_KAK_KLYUCH_V1
"""
МЕТКА СТАНОВИТСЯ КЛЮЧОМ-ЗАКЛАДКОЙ.

Слово Шефа 08.09:

> Метки для этого и задумывались. Если метки будут играть роль
> меток-закладок, то легко и просто совсем получится — и дели до
> сраки: и по важности, и по времени, и по числу потерянных
> Локиных трусов.
>
> Давай придумаем ключ. У всего есть ключ, вот и метка это ключ, и
> куча меток в куче тоже ключ. Какие-то части идентичны у всех, а
> какие-то персональные. Все понимают, а разница есть.
>
> Знание одно, просто авторитет мой и авторитет Нины разный для него,
> а информация одинакова.

═══ ЧТО НАШЛОСЬ ПРИ РАЗБОРЕ ═══

**Половина ключа уже лежит в метке.** Она хранит: текст, паттерн,
откуда, когда, сколько раз повторилась и флаг «ярко» (важность, и
ставит её САМ ЖИТЕЛЬ — это уже правильно и не трогаем).

**А узкое место оказалось в поиске.** `vspomnit` считает, сколько слов
запроса ДОСЛОВНО встретилось в тексте записи. Спросишь «дивергенция» —
найдёт только там, где так и написано. Записал он когда-то «диверы» —
не найдёт никогда. Вот это настоящая беда, а не перегородка
работа/жизнь.

Закладка чинит именно это: у записи появляется имя, и спрашивают по
имени, а не по угаданному слову.

**И ГЛАВНОЕ — нашлась настоящая причина старого долга.** У меток и
маяков нет ни поля `контекст`, ни поля `слой` — только `откуда`. А
`kontekst_zapisi` смотрит первые два. Значит при ЛЮБОМ запросе с
фильтром метки и маяки отсеивались ЦЕЛИКОМ. А мост с Биржи всегда
спрашивает рабочее — то есть **весь торговый опыт трейдера был
невидим для его же рабочего поиска**. Он копил то, чего потом не мог
найти.

Чиним ЧТЕНИЕ, а не запись: голос «рынок» остаётся голосом «рынок» —
он нарочно отличает «что мне сказал рынок» от «что я вынес в
монтажной», и житель вправе их столкнуть. Просто при чтении этот
голос теперь понимается как рабочий.

**Чего не хватало — двух полей:**

1. `ярлыки` — свои слова жителя, список. Поле `паттерн` занять нельзя:
   оно служебное, на нём висит суд рынка (подтверждения/опровержения),
   трогать его — рисковать тем, что уже работает.
2. `от кого` — ИМЯ того, от кого знание. Сейчас `откуда` хранит
   контекст («работа», «рынок», «сам»), а не человека. Знание одно —
   а вес источника разный, и вес этот живёт в самом жителе, не в базе.
   Поэтому храним ИМЯ, а не оценку: сколько оно весит, он решает сам,
   когда достаёт.

═══ ЧТО ПАТЧ ДЕЛАЕТ (жители/dvizhok.py) ═══

1. `otmetit_yarkim(...)` принимает `yarlyki` и `ot_kogo` и пишет их в
   метку. Если метка уже была — ярлыки ДОБАВЛЯЮТСЯ к её ярлыкам, а не
   затирают их.
2. `dopisat_vyvod(...)` — то же самое для рабочих выводов и маяков.
3. `vspomnit(...)` — совпадение по ярлыку весит как ПЯТЬ слов. Значит
   спрос по закладке всегда бьёт словесную кашу. И в выдаче ярлыки и
   имя видны, чтобы житель понимал, откуда след.
4. Новый `yarlyki()` — его собственный словарь закладок с числом
   употреблений. Нужно затем, что свободный ярлык через месяц
   расплодится в двести вариантов вразнобой: перед тем как вешать
   новый, житель смотрит, что у него уже есть.

═══ ЧЕГО ПАТЧ НЕ ДЕЛАЕТ ═══

Не трогает: `паттерн` и суд рынка, флаг «ярко» и то, кто его ставит,
перегородку работа/жизнь, лимиты и вытеснение, три яруса прочности.
Старые метки не ломаются: нет поля — значит пусто, ищутся как раньше.

Руки жителю (повесить ярлык, посмотреть свой словарь, вспомнить по
закладке) — СЛЕДУЮЩИМ патчем. Сперва пусть механизм ляжет и
проверится, потом дадим ручку.

Запускать из корня репозитория:
    python postavit_metku_klyuchom.py

Идемпотентен (маркер METKA_KAK_KLYUCH_V1). Сверяет все куски заранее:
либо ложится целиком, либо не трогает ничего. Рядом .bak.
"""
from __future__ import annotations
from pathlib import Path

FAYL = "жители/dvizhok.py"
MARKER = "METKA_KAK_KLYUCH_V1"


# ── 1) общий помощник + разбор ярлыков ──────────────────────────────
POMOSH_OLD = '''    def metki(self) -> list:
        """Весь второй этаж — нажитое. Список объектов."""
        return self._chitat_etazh(self._metki_path())'''

POMOSH_NEW = '''    def metki(self) -> list:
        """Весь второй этаж — нажитое. Список объектов."""
        return self._chitat_etazh(self._metki_path())

    # ═══════════════════════════════════════════════════════
    # METKA_KAK_KLYUCH_V1 — МЕТКА КАК ЗАКЛАДКА
    # ═══════════════════════════════════════════════════════
    # Ключ собирается из двух половин. ОБЩАЯ у всех одинакова — когда,
    # откуда, от кого: по ней город может спросить поперёк жителей, и
    # слово будет значить одно и то же для всех. ЛИЧНАЯ — ярлыки его
    # словами и важность его глазами: тут все разные, и мы не лезем.
    #
    # Зачем вообще. Поиск в vspomnit буквальный, по словам: спросил
    # «дивергенция» — нашёл только там, где так и написано; записал
    # «диверы» — не нашёл никогда. Закладка чинит именно это: у записи
    # появляется ИМЯ, и спрашивают по имени, а не по угаданному слову.
    #
    # Почему не заняли «паттерн». Он служебный: на нём висит суд рынка
    # (подтверждений/опровержений). Трогать его — рисковать тем, что
    # уже работает.
    # ═══════════════════════════════════════════════════════

    YARLYK_VES = 5   # совпадение по закладке весит как пять слов запроса

    @staticmethod
    def _yarlyki_spisok(x) -> list:
        """Ярлыки в порядок: строка через запятую или список — в чистый
        список коротких слов нижним регистром, без повторов."""
        if not x:
            return []
        syrye = x.split(",") if isinstance(x, str) else list(x)
        out = []
        for y in syrye:
            y = str(y).strip().lower().strip("#")
            if y and y not in out:
                out.append(y[:40])
        return out[:8]

    def _prishit_klyuch(self, zapis: dict, yarlyki=None, ot_kogo: str = ""):
        """Дописать закладочную часть ключа в запись. ДОБАВЛЯЕТ ярлыки к
        тем, что были, а не затирает: житель мог повесить одно вчера и
        другое сегодня, и оба верны."""
        novye = self._yarlyki_spisok(yarlyki)
        if novye:
            bylo = self._yarlyki_spisok(zapis.get("ярлыки"))
            zapis["ярлыки"] = self._yarlyki_spisok(bylo + novye)
        if (ot_kogo or "").strip():
            zapis["от кого"] = str(ot_kogo).strip()[:40]
        return zapis

    def yarlyki(self) -> list:
        """Его собственный словарь закладок: [(ярлык, сколько раз), ...],
        частые первыми.

        Нужно затем, что свободный ярлык через месяц расплодится в
        двести вариантов вразнобой — «дивер», «диверы», «дивергенция».
        Перед тем как вешать новый, житель смотрит, что у него уже
        есть, и берёт оттуда."""
        schyot = {}
        for etazh in (self.metki(), self.mayaki()):
            for z in etazh:
                for y in self._yarlyki_spisok(z.get("ярлыки")):
                    schyot[y] = schyot.get(y, 0) + 1
        return sorted(schyot.items(), key=lambda kv: (-kv[1], kv[0]))'''


# ── 2) otmetit_yarkim принимает ключ ────────────────────────────────
YARKOE_OLD = '''    def otmetit_yarkim(self, tekst: str, otkuda: str = "") -> dict:
        tekst = (tekst or "").strip()
        if not tekst:
            return {"дописано": False, "причина": "пустой текст"}
        metki = self.metki()
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for m in metki:
            if m.get("текст") == tekst:
                if m.get("ярко"):
                    return {"дописано": False, "причина": "уже отмечено ярким"}
                m["ярко"] = True
                self._pisat_etazh(self._metki_path(), metki)
                return {"дописано": True, "причина": "было меткой, стало яркой"}
        metki.append({"текст": tekst, "паттерн": None, "откуда": otkuda or "сам",
                      "когда": now_iso, "раз": 1, "ярко": True})'''

YARKOE_NEW = '''    def otmetit_yarkim(self, tekst: str, otkuda: str = "",
                       yarlyki=None, ot_kogo: str = "") -> dict:
        # METKA_KAK_KLYUCH_V1: сюда же вешается закладочная часть ключа.
        # Даже если метка уже была яркой — ярлык и имя дописываем: это
        # не повтор знания, это уточнение ключа к нему.
        tekst = (tekst or "").strip()
        if not tekst:
            return {"дописано": False, "причина": "пустой текст"}
        metki = self.metki()
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for m in metki:
            if m.get("текст") == tekst:
                _bylo_yarkim = bool(m.get("ярко"))
                self._prishit_klyuch(m, yarlyki, ot_kogo)
                if _bylo_yarkim:
                    if yarlyki or ot_kogo:
                        self._pisat_etazh(self._metki_path(), metki)
                        return {"дописано": True, "причина": "ключ уточнён"}
                    return {"дописано": False, "причина": "уже отмечено ярким"}
                m["ярко"] = True
                self._pisat_etazh(self._metki_path(), metki)
                return {"дописано": True, "причина": "было меткой, стало яркой"}
        _novaya = {"текст": tekst, "паттерн": None, "откуда": otkuda or "сам",
                   "когда": now_iso, "раз": 1, "ярко": True}
        self._prishit_klyuch(_novaya, yarlyki, ot_kogo)
        metki.append(_novaya)'''


# ── 3) dopisat_vyvod принимает ключ ─────────────────────────────────
VYVOD_OLD = '''    def dopisat_vyvod(self, vyvod: str, limit: int = 10,
                      pattern: Optional[str] = None,   # PYLANCE_GIGIENA_V1
                      otkuda: str = "рынок") -> dict:'''

VYVOD_NEW = '''    def dopisat_vyvod(self, vyvod: str, limit: int = 10,
                      pattern: Optional[str] = None,   # PYLANCE_GIGIENA_V1
                      otkuda: str = "рынок",
                      yarlyki=None, ot_kogo: str = "") -> dict:
        # METKA_KAK_KLYUCH_V1: yarlyki — свои слова жителя (закладка),
        # ot_kogo — ИМЯ того, от кого знание. Оба необязательны: не
        # передали — всё как было.'''

LECH_OLD = '''        def _lech_metkoy(txt, patt, raz):
            metki.append({"текст": txt, "паттерн": patt, "откуда": otkuda,
                          "когда": now_iso, "раз": raz})'''

LECH_NEW = '''        def _lech_metkoy(txt, patt, raz):
            _m = {"текст": txt, "паттерн": patt, "откуда": otkuda,
                  "когда": now_iso, "раз": raz}
            self._prishit_klyuch(_m, yarlyki, ot_kogo)   # METKA_KAK_KLYUCH_V1
            metki.append(_m)'''

MAYAK_OLD = '''        if found is not None:
            found["раз"] = found.get("раз", 1) + 1
            found["текст"] = vyvod
            found["последний_раз"] = now_iso
            found["откуда"] = otkuda
            raz = found["раз"]
        else:
            found = {"текст": vyvod, "паттерн": pattern, "откуда": otkuda,
                     "раз": 1, "первый_раз": now_iso, "последний_раз": now_iso}
            mayaki.append(found)
            raz = 1'''

MAYAK_NEW = '''        if found is not None:
            found["раз"] = found.get("раз", 1) + 1
            found["текст"] = vyvod
            found["последний_раз"] = now_iso
            found["откуда"] = otkuda
            self._prishit_klyuch(found, yarlyki, ot_kogo)  # METKA_KAK_KLYUCH_V1
            raz = found["раз"]
        else:
            found = {"текст": vyvod, "паттерн": pattern, "откуда": otkuda,
                     "раз": 1, "первый_раз": now_iso, "последний_раз": now_iso}
            self._prishit_klyuch(found, yarlyki, ot_kogo)  # METKA_KAK_KLYUCH_V1
            mayaki.append(found)
            raz = 1'''


# ── 4) поиск: закладка бьёт словесную кашу ──────────────────────────
POISK_OLD = '''            fakt = str(z.get("текст") or z.get("факт") or "").lower()
            score = sum(1 for w in slova if w in fakt)
            if iskomyj_tonus and z.get("тонус") == iskomyj_tonus:
                score += 2   # PAMYAT_ISKRA_V1: тон совпал — весит как два слова'''

POISK_NEW = '''            fakt = str(z.get("текст") or z.get("факт") or "").lower()
            score = sum(1 for w in slova if w in fakt)
            # METKA_KAK_KLYUCH_V1: попадание по ЗАКЛАДКЕ весит как пять
            # слов. Поиск тут буквальный, по словам, и потому слепой к
            # синонимам: «дивергенция» не находит «диверы». Ярлык — это
            # имя, которое житель дал сам; спрос по имени должен бить
            # словесную кашу, иначе закладка бесполезна.
            _yarl = self._yarlyki_spisok(z.get("ярлыки"))
            if _yarl:
                for _y in _yarl:
                    if _y in low_zapros or any(_y == w for w in slova):
                        score += self.YARLYK_VES
                        break
            # и по ИМЕНИ источника: «что мне говорил Шеф» — законный
            # вопрос к своей памяти.
            _ot = str(z.get("от кого") or "").lower()
            if _ot and _ot in low_zapros:
                score += self.YARLYK_VES
            if iskomyj_tonus and z.get("тонус") == iskomyj_tonus:
                score += 2   # PAMYAT_ISKRA_V1: тон совпал — весит как два слова'''


# ── 5) выдача: показать закладку и имя ──────────────────────────────
VYDACHA_OLD = '''            stroki.append(f"— [{ts}{otkuda}] {z.get('текст') or z.get('факт') or ''}")'''

VYDACHA_NEW = '''            # METKA_KAK_KLYUCH_V1: закладка и имя — в выдачу. Знание
            # одно, а вес источника разный, и решает этот вес сам
            # житель. Значит он должен ВИДЕТЬ, от кого след.
            _yarl = self._yarlyki_spisok(z.get("ярлыки"))
            _hvost = ""
            if _yarl:
                _hvost += " ⟨" + ", ".join(_yarl) + "⟩"
            _ot = str(z.get("от кого") or "").strip()
            if _ot:
                _hvost += f" · от: {_ot}"
            stroki.append(
                f"— [{ts}{otkuda}] "
                f"{z.get('текст') or z.get('факт') or ''}{_hvost}")'''


# ── 6) ГЛАВНАЯ ПОЧИНКА: метки и маяки были невидимы рабочему поиску ──
KONTEKST_OLD = '''def kontekst_zapisi(z: dict) -> str:
    """Откуда след. Нет пометки — берём по слою; sensory неизвестен."""
    k = str(z.get("контекст") or "").strip()
    if k:
        return k
    return SLOY_KONTEKST.get(str(z.get("слой") or ""), "")'''

KONTEKST_NEW = '''# METKA_KAK_KLYUCH_V1: голос «откуда» → контекст.
# У МЕТОК И МАЯКОВ НЕТ НИ «контекста», НИ «слоя» — только «откуда»
# («рынок», «сделка», «учёба», «работа», профессия). Значит при любом
# запросе с фильтром они давали пустой контекст и отсеивались ЦЕЛИКОМ.
# А мост с Биржи всегда спрашивает рабочее — то есть ВЕСЬ торговый
# опыт жителя был невидим для его же рабочего поиска. Он копил то,
# чего потом не мог найти.
# Чиним ЧТЕНИЕ, а не запись: голос «рынок» остаётся голосом «рынок» —
# он нарочно отличает «что мне сказал рынок» от «что я вынес в
# монтажной», и житель вправе их столкнуть.
OTKUDA_KONTEKST = {
    "рынок": "работа", "сделка": "работа", "работа": "работа",
    "факт": "факт",
    "учёба": "учёба", "учеба": "учёба",
    "общение": "общение", "дом": "дом", "жизнь": "дом",
}


def kontekst_zapisi(z: dict) -> str:
    """Откуда след. Нет пометки — берём по слою; потом по голосу
    «откуда» (метки и маяки живут только им); sensory неизвестен."""
    k = str(z.get("контекст") or "").strip()
    if k:
        return k
    k = SLOY_KONTEKST.get(str(z.get("слой") or ""), "")
    if k:
        return k
    # METKA_KAK_KLYUCH_V1: последняя опора — голос вывода. Незнакомый
    # голос (профессия, «сам») оставляем пустым, как было: гадать не
    # будем, лучше честное «следа нет».
    return OTKUDA_KONTEKST.get(str(z.get("откуда") or "").strip().lower(), "")'''


PRAVKI = [
    ("контекст метки по голосу «откуда»", KONTEKST_OLD, KONTEKST_NEW),
    ("помощники ключа и словарь", POMOSH_OLD, POMOSH_NEW),
    ("otmetit_yarkim", YARKOE_OLD, YARKOE_NEW),
    ("подпись dopisat_vyvod", VYVOD_OLD, VYVOD_NEW),
    ("метка в dopisat_vyvod", LECH_OLD, LECH_NEW),
    ("маяк в dopisat_vyvod", MAYAK_OLD, MAYAK_NEW),
    ("поиск по закладке", POISK_OLD, POISK_NEW),
    ("выдача с закладкой", VYDACHA_OLD, VYDACHA_NEW),
]


def main() -> None:
    root = Path(__file__).resolve().parent
    path = root / FAYL
    if not path.exists():
        print(f"НЕ НАШЁЛ: {path}")
        print("Запускать из корня репозитория (там, где лежит main.py).")
        return

    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("уже накачен — маркер на месте, ничего не трогаю")
        return

    bracket = []
    for imya, old, _new in PRAVKI:
        if text.count(old) != 1:
            bracket.append((imya, text.count(old)))

    if bracket:
        print("⚠ Файл на диске отличается от ожидаемого — НИЧЕГО не меняю:")
        for imya, cnt in bracket:
            print(f"   «{imya}»: совпадений {cnt} (нужно ровно 1)")
        print("Пришли Брату свой жители/dvizhok.py — доведу под него.")
        return

    for imya, old, new in PRAVKI:
        text = text.replace(old, new, 1)
        print(f"✔ {imya}")

    text = text.rstrip("\n") + f"\n\n# {MARKER} - marker\n"

    try:
        import ast
        ast.parse(text)
    except SyntaxError as e:
        print(f"\n⚠ СИНТАКСИС СЛОМАН: {e} — НЕ сохраняю")
        return

    bak = path.with_suffix(path.suffix + ".bak_metka_klyuch")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")

    print("\nсинтаксис цел, файл сохранён. Бэкап рядом:", bak.name)
    print("\nЧто теперь умеет метка:")
    print("  ОБЩЕЕ (у всех одинаково): когда · откуда · от кого")
    print("  ЛИЧНОЕ (у каждого своё):  ярлыки · ярко")
    print("\nИ куча меток вместе работает пересечением: один ярлык")
    print("достаёт широко, два сужают, три бьют в точку.")
    print("\nСледующим патчем — руки жителю: повесить ярлык,")
    print("посмотреть свой словарь закладок, вспомнить по закладке.")


if __name__ == "__main__":
    main()
