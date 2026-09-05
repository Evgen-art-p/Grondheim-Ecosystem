# -*- coding: utf-8 -*-
# MARKER: YARKOE_V1
"""
ЯРКОЕ — ЖИТЕЛЬ САМ РЕШАЕТ, ЧТО ДЕРЖИТСЯ ДОЛЬШЕ ОБЫЧНОГО.

СЛОВО ШЕФА (03.09)
    «Возможно, как-то жителю самому определить, что для него важно, а
    что нет?» — «Мне ближе первое» (в любой момент разговора, как
    MEMORY_REQUEST — сказал в моменте «это важно», и всё).

ЧТО БЫЛО НЕ ТАК
────────────────
В прошлое окно стола (METKI_V_STOL=4) попадали только САМЫЕ СВЕЖИЕ
метки — не самые важные. Через неделю по-настоящему сильный момент
вытеснялся тремя проходными, потому что окно смотрит на дату, а не на
вес. Спросишь дома «как поработала» — а вспоминать ей уже нечем,
только фантазия.

ЧТО ДЕЛАЕТСЯ
────────────
Тот же приём, что MEMORY_REQUEST, только не наружу (принести из
архива), а внутрь (сохранить крепче). Житель в любой момент разговора
пишет отдельной строкой:
    ЯРКОЕ: <что запомнить>
Это ложится в метки СРАЗУ — минуя и обычный порог повтора (Путь
Зрелости, 3 раза), и рыночного судью (verdikt_rynka) — с флагом
"ярко". Метка с этим флагом больше не вымывается свежестью: стол
всегда показывает её, сколько бы времени ни прошло. Решает сам
житель, не движок, не рынок, не счётчик.

Правится жители/dvizhok.py (сердце — новый метод + окно стола),
жители/ui_zhitel.py (дом), Биржа/nositel.py (мост) и три мозга
торгового_хаоса (A06/A07/A08 — оба конца: сказать И услышать).

Идемпотентен. .bak рядом с каждым правленым файлом.
"""
import ast
import shutil
import sys
from pathlib import Path

MARKER = "YARKOE_V1"


def _nayti_koren() -> Path:
    """Корень репо — ищем по трём приметам разом: dvizhok.py, ui_zhitel.py,
    nositel.py и папка слотов торгового_хаоса."""
    for koren in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        if (koren / "жители" / "dvizhok.py").exists() and \
           (koren / "Биржа" / "nositel.py").exists():
            return koren
    print("Не нашёл корень репо (нужны жители/dvizhok.py и Биржа/nositel.py рядом).")
    s = input("Перетащи сюда корень репозитория и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if (p / "жители" / "dvizhok.py").exists():
        return p
    raise SystemExit("не та папка")


def _primenit(f: Path, zameny: list, opisanie: str) -> str:
    """zameny — список (STAR, NOV). Все должны найтись ровно по разу."""
    src = f.read_text(encoding="utf-8")
    if MARKER in src:
        return "уже накачено"
    novyy = src
    for i, (star, nov) in enumerate(zameny, 1):
        if star not in novyy:
            return f"! кусок {i}/{len(zameny)} не нашёлся дословно — файл правили, не трогаю ({opisanie})"
        if novyy.count(star) != 1:
            return f"! кусок {i}/{len(zameny)} встретился не один раз — не трогаю ({opisanie})"
        novyy = novyy.replace(star, nov)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    ast.parse(novyy)
    shutil.copy2(f, f.with_suffix(".py.bak_yarkoe"))
    f.write_text(novyy, encoding="utf-8")
    return f"накачено ({opisanie}, .bak_yarkoe рядом)"


# ═══════════════════ 1. жители/dvizhok.py — сердце ═══════════════════

DVIZHOK_STAR = '''    def _metki_v_stol(self) -> list:
        """Свежие METKI_V_STOL меток — для промпта. НЕ все: контекст
        Биржи уже 25к символов, а метки растут всю жизнь. Маленький
        стол + право дотянуться (MEMORY_REQUEST) — дешевле и честнее
        по природе: живой человек тоже не держит всю жизнь в голове."""
        m = self.metki()
        m.sort(key=lambda x: str(x.get("когда", "")))
        return m[-self.METKI_V_STOL:]'''

DVIZHOK_NOV = '''    YARKOE_V_STOL = 6   # ярких меток в столе — тоже не резиновый склад

    def _metki_v_stol(self) -> list:
        """Свежие METKI_V_STOL меток + ЯРКИЕ (YARKOE_V1) — для промпта.
        НЕ все: контекст Биржи уже 25к символов, а метки растут всю
        жизнь. Маленький стол + право дотянуться (MEMORY_REQUEST) —
        дешевле и честнее по природе: живой человек тоже не держит всю
        жизнь в голове. Но яркое (сам житель так решил, отдельной
        строкой в разговоре) не вымывается свежестью — держится своим
        флагом, а не местом в очереди."""
        m = self.metki()
        m.sort(key=lambda x: str(x.get("когда", "")))
        yarkie = [x for x in m if x.get("ярко")][-self.YARKOE_V_STOL:]
        svezhie = [x for x in m if not x.get("ярко")][-self.METKI_V_STOL:]
        return yarkie + svezhie

    # ═══════════════════════════════════════════════════════
    # YARKOE_V1 — ЖИТЕЛЬ САМ РЕШАЕТ, ЧТО ДЕРЖИТСЯ ДОЛЬШЕ
    # ═══════════════════════════════════════════════════════
    # Тот же приём, что MEMORY_REQUEST, только не наружу (принести), а
    # внутрь (сохранить). Не судья повтора (Путь Зрелости, 3 раза), не
    # рынок (verdikt_rynka) — воля жителя, в моменте разговора. Ложится
    # в метки СРАЗУ, минуя оба обычных порога, с флагом "ярко".
    # ═══════════════════════════════════════════════════════

    def otmetit_yarkim(self, tekst: str, otkuda: str = "") -> dict:
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
                      "когда": now_iso, "раз": 1, "ярко": True})
        ushlo = []
        # яркие не подставляем под обычное вытеснение по лимиту —
        # выселяем только НЕ-яркие, старейшие сначала
        if len(metki) > self.METKI_CAP:
            ne_yarkie_idx = [i for i, x in enumerate(metki) if not x.get("ярко")]
            izbytok = len(metki) - self.METKI_CAP
            vyselit = {id(metki[i]) for i in ne_yarkie_idx[:izbytok]}
            if vyselit:
                ushlo = [x for x in metki if id(x) in vyselit]
                metki = [x for x in metki if id(x) not in vyselit]
                for old in ushlo:
                    self._archive_zapis(old.get("текст", ""),
                                        "метка вытеснена (лимит нажитого)")
        self._pisat_etazh(self._metki_path(), metki)
        return {"дописано": True, "меток": len(metki), "вытеснено": len(ushlo)}'''


# ═══════════════════ 2. жители/ui_zhitel.py — дом ═══════════════════

UI_ZHITEL_HELPERS_STAR = '''def _ubrat_memory_request(text: str) -> str:
    """PATCH_ZHITEL_VSPOMINAET: технические строки MEMORY_REQUEST вычищаются из видимого ответа."""
    lines = [l for l in (text or "").splitlines() if "MEMORY_REQUEST:" not in l]
    return "\\n".join(lines).strip()'''

UI_ZHITEL_HELPERS_NOV = UI_ZHITEL_HELPERS_STAR + '''


# YARKOE_V1: тот же приём, что MEMORY_REQUEST/MAYAK_REQUEST — только
# внутрь, не наружу. Житель сам решает, что держится дольше обычного.
def _izvlech_yarkoe(text: str) -> str:
    for line in (text or "").splitlines():
        if "ЯРКОЕ:" in line:
            return line.split("ЯРКОЕ:", 1)[1].strip()
    return ""


def _ubrat_yarkoe(text: str) -> str:
    lines = [l for l in (text or "").splitlines() if "ЯРКОЕ:" not in l]
    return "\\n".join(lines).strip()'''

UI_ZHITEL_PROMPT_STAR = '''            # PATCH_ZHITEL_MAYAK_REQUEST_V1
            soul += (
                "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
                "(то, чего ты сам знать не можешь — новости, текущие события, "
                "актуальные данные) — напиши отдельной строкой "
                "MAYAK_REQUEST: <что узнать> и Маяк Пробуждения принесёт ответ."
            )
            # PATCH_PROSEV_REQUEST_V1: строка появляется, только если движок'''

UI_ZHITEL_PROMPT_NOV = '''            # PATCH_ZHITEL_MAYAK_REQUEST_V1
            soul += (
                "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
                "(то, чего ты сам знать не можешь — новости, текущие события, "
                "актуальные данные) — напиши отдельной строкой "
                "MAYAK_REQUEST: <что узнать> и Маяк Пробуждения принесёт ответ."
            )
            # YARKOE_V1: житель сам решает, что держится дольше обычного окна
            soul += (
                "\\nЕсли что-то из разговора кажется тебе важным настолько, что "
                "должно остаться с тобой надолго — напиши отдельной строкой "
                "ЯРКОЕ: <что запомнить>, и это ляжет в твою память крепче "
                "обычного, не сотрётся со временем само."
            )
            # PATCH_PROSEV_REQUEST_V1: строка появляется, только если движок'''

UI_ZHITEL_EXTRACT_STAR = '''            _mem_q = _izvlech_memory_request(reply)
            _mayak_q = _izvlech_mayak_request(reply)  # PATCH_ZHITEL_MAYAK_REQUEST_V1
            _prosev_q = _est_prosev_request(reply) if _prosev_dostupno else False  # PATCH_PROSEV_REQUEST_V1'''

UI_ZHITEL_EXTRACT_NOV = UI_ZHITEL_EXTRACT_STAR + '''
            _yark_q = _izvlech_yarkoe(reply)   # YARKOE_V1
            if _yark_q and dvizhok is not None:
                try:
                    dvizhok.otmetit_yarkim(_yark_q, otkuda="жизнь")
                except Exception:
                    pass'''

UI_ZHITEL_STRIP_STAR = (
    '            reply = _ubrat_prosev_request(_ubrat_mayak_request'
    '(_ubrat_memory_request(reply))) or reply')
UI_ZHITEL_STRIP_NOV = (
    '            reply = _ubrat_prosev_request(_ubrat_mayak_request'
    '(_ubrat_memory_request(_ubrat_yarkoe(reply)))) or reply')


# ═══════════════════ 3. Биржа/nositel.py — мост ═══════════════════

NOSITEL_STAR = "# PAMYAT_RABOTA_ZHIZN_V1 - marker"

NOSITEL_NOV = '''# PAMYAT_RABOTA_ZHIZN_V1 - marker


# ═══════════════════════════════════════════════════════════
# YARKOE_BIRZHA_V1 — тот же приём, что MEMORY_REQUEST, только внутрь
# ═══════════════════════════════════════════════════════════
YARKOE_MARKER = "ЯРКОЕ:"


def izvlech_yarkoe(text: str) -> str:
    for line in (text or "").splitlines():
        if YARKOE_MARKER in line:
            return line.split(YARKOE_MARKER, 1)[1].strip()
    return ""


def ubrat_yarkoe(text: str) -> str:
    lines = [l for l in (text or "").splitlines() if YARKOE_MARKER not in l]
    return "\\n".join(lines).strip()


def otmetit_yarkim_slotom(ceh: str, slot: str, tekst: str, otkuda: str = "работа") -> dict:
    """Житель, сидящий в слоте, сам решил — это держится дольше обычного."""
    try:
        n = dusha_slota(ceh, slot)
        if not n:
            return {"дописано": False, "причина": "вакансия"}
        d = _dvizhok(n["носитель"]["папка"])
        if d is None:
            return {"дописано": False, "причина": "движок недоступен"}
        return d.otmetit_yarkim(tekst, otkuda=otkuda)
    except Exception as e:
        print(f"[МОСТ] ⚠️  ярким не отметилось ({ceh}/{slot}): {e}")
        return {"дописано": False, "причина": str(e)}'''


# ═══════════════════ 4. три мозга — сказать И услышать ═══════════════════

SHKOLA_STAR = '''        "\\n\\nГоворишь языком своей школы. В ней есть пасть и зубы "
        "Аллигатора, фракталы, приседающий бар, разворотный бар, AO и "
        "дивергенция, волны и откаты. «Уровней поддержки и сопротивления» "
        "в ней нет — это чужой словарь. Не знаешь чего-то — так и скажи, "
        "не подставляй чужое слово вместо своего.\\n")'''

SHKOLA_NOV = '''        "\\n\\nГоворишь языком своей школы. В ней есть пасть и зубы "
        "Аллигатора, фракталы, приседающий бар, разворотный бар, AO и "
        "дивергенция, волны и откаты. «Уровней поддержки и сопротивления» "
        "в ней нет — это чужой словарь. Не знаешь чего-то — так и скажи, "
        "не подставляй чужое слово вместо своего.\\n"
        # YARKOE_V1: сам решаешь, что держится дольше обычного окна.
        "\\nЕсли что-то из разговора кажется тебе важным настолько, что "
        "должно остаться с тобой надолго — напиши отдельной строкой:\\n"
        "ЯРКОЕ: <что запомнить>\\n"
        "Это ляжет в твою память крепче обычного и не сотрётся со временем "
        "само.\\n")'''

# per-slot: свой STAR/NOV для return _chat_fn(...) / except — тексты
# в трёх мозгах отличаются именами агента и способом температуры

VOZVRAT = {
    "A06": (
        '''        return _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A06_BRUT", slot_id="trading", temperature=_my_temp())
    except Exception as e:
        return f"⚠️ Брут не смог ответить: {e}"''',
        '''        _otvet = _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A06_BRUT", slot_id="trading", temperature=_my_temp())
    except Exception as e:
        return f"⚠️ Брут не смог ответить: {e}"

    # YARKOE_V1: сам решил в разговоре — держится дольше обычного окна.
    try:
        from nositel import izvlech_yarkoe, ubrat_yarkoe, otmetit_yarkim_slotom
        _yark = izvlech_yarkoe(_otvet)
        if _yark:
            otmetit_yarkim_slotom(_CEH, _SLOT, _yark, otkuda="работа")
            _otvet = ubrat_yarkoe(_otvet) or _otvet
    except Exception:
        pass
    return _otvet''',
    ),
    "A07": (
        '''        return _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A07_AVANTURIST", slot_id="A07",
                    temperature=_temp)
    except Exception as e:
        return f"⚠️ Авантюрист не смог ответить: {e}"''',
        '''        _otvet = _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A07_AVANTURIST", slot_id="A07",
                    temperature=_temp)
    except Exception as e:
        return f"⚠️ Авантюрист не смог ответить: {e}"

    # YARKOE_V1: сам решил в разговоре — держится дольше обычного окна.
    try:
        from nositel import izvlech_yarkoe, ubrat_yarkoe, otmetit_yarkim_slotom
        _yark = izvlech_yarkoe(_otvet)
        if _yark:
            otmetit_yarkim_slotom(_CEH, _SLOT, _yark, otkuda="работа")
            _otvet = ubrat_yarkoe(_otvet) or _otvet
    except Exception:
        pass
    return _otvet''',
    ),
    "A08": (
        '''        return _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A08_KONSERVATOR", slot_id="trading", temperature=_my_temp())
    except Exception as e:
        return f"⚠️ Консерватор не смог ответить: {e}"''',
        '''        _otvet = _chat_fn(system=system, user=question, history=history,
                        knowledge=_znaniya,
                    agent_id="A08_KONSERVATOR", slot_id="trading", temperature=_my_temp())
    except Exception as e:
        return f"⚠️ Консерватор не смог ответить: {e}"

    # YARKOE_V1: сам решил в разговоре — держится дольше обычного окна.
    try:
        from nositel import izvlech_yarkoe, ubrat_yarkoe, otmetit_yarkim_slotom
        _yark = izvlech_yarkoe(_otvet)
        if _yark:
            otmetit_yarkim_slotom(_CEH, _SLOT, _yark, otkuda="работа")
            _otvet = ubrat_yarkoe(_otvet) or _otvet
    except Exception:
        pass
    return _otvet''',
    ),
}


def main():
    koren = _nayti_koren()
    print(f"\nКорень: {koren}\n")

    itog1 = _primenit(koren / "жители" / "dvizhok.py",
                      [(DVIZHOK_STAR, DVIZHOK_NOV)], "сердце")
    print(f"  жители/dvizhok.py: {itog1}")

    itog2 = _primenit(koren / "жители" / "ui_zhitel.py",
                      [(UI_ZHITEL_HELPERS_STAR, UI_ZHITEL_HELPERS_NOV),
                       (UI_ZHITEL_PROMPT_STAR, UI_ZHITEL_PROMPT_NOV),
                       (UI_ZHITEL_EXTRACT_STAR, UI_ZHITEL_EXTRACT_NOV),
                       (UI_ZHITEL_STRIP_STAR, UI_ZHITEL_STRIP_NOV)], "дом")
    print(f"  жители/ui_zhitel.py: {itog2}")

    itog3 = _primenit(koren / "Биржа" / "nositel.py",
                      [(NOSITEL_STAR, NOSITEL_NOV)], "мост")
    print(f"  Биржа/nositel.py: {itog3}")

    sloty_dir = koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос" / "слоты"
    if not sloty_dir.exists():
        sloty_dir = koren  # на случай другого расположения — main найдёт ниже

    for slot in ("A06", "A07", "A08"):
        f = sloty_dir / slot / "мозг.py"
        if not f.exists():
            print(f"  {slot}: ! мозг.py не найден по пути {f}")
            continue
        try:
            itog = _primenit(f, [(SHKOLA_STAR, SHKOLA_NOV), VOZVRAT[slot]],
                             f"мозг {slot}")
        except SyntaxError as e:
            itog = f"! после правки не разбирается ({e}) — файл НЕ тронут"
        print(f"  {slot}/мозг.py: {itog}")

    print("\nГотово. ЯРКОЕ можно сказать и дома, и на Бирже — оседает")
    print("в личных метках жителя с флагом 'ярко' и больше не вымывается")
    print("свежестью из стола.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
