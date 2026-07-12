# -*- coding: utf-8 -*-
"""
patch_yakorya_dva_yarusa_v1.py
────────────────────────────────────────────────────────────────────
ДВА ЯРУСА ЯКОРЕЙ — черновик и устойчивый. Решение Шефа (12.07),
на размышление о Гл.4.4 Чертежа: «Один вывод — не опыт. Опыт зреет
из накопленного… Единичное событие меняет заряд, не фильтр (защита
от дребезга)».

ПРОБЛЕМА, КОТОРУЮ ЧИНИМ: dopisat_vyvod писал ЛЮБОЙ значимый вывод
СРАЗУ в Anchor_Points — один стоп Ильи против ветра становился
постоянным якорем с первого раза. Канон явно требует другого:
единичное событие — это ЗАРЯД (уже есть, vdoh() качается всегда),
а в ФИЛЬТР (Anchor_Points) должно ложиться только НАКОПЛЕННОЕ.

РЕШЕНИЕ ШЕФА: не строить новый механизм — надстроить сортировку
по значимости поверх готового (лимит 7-10 + архив уже есть).

КАК УСТРОЕНО:

  ЯРУС 1 — ЧЕРНОВИК (Draft_Anchors, JSON-список в паспорте).
    Новый вывод с ключом паттерна → либо создаёт черновик (раз=1),
    либо усиливает существующий той же природы (раз+=1, текст
    обновляется свежей формулировкой). Черновик читается столом,
    но с ПОНИЖЕННЫМ голосом: «замечаю за собой, пока не подтвердилось».

  ЯРУС 2 — УСТОЙЧИВЫЙ (Anchor_Points, как было).
    Черновик, набравший ПОРОГ повторов (3 — тот же порог, что
    Путь Зрелости, Чертёж §4.6.2: «3 вердикта судьи», не новое
    число с потолка), ПОВЫШАЕТСЯ: уходит из черновиков, ложится
    постоянной строкой в Anchor_Points (тот же лимит 7-10, то же
    вытеснение старейшего в архив, что было).

  ГРАНИЦА МЕХАНИЗМА (Закон Фрактала — один механизм, разные источники):
    dvizhok.dopisat_vyvod остаётся ОБЩИМ движком, не знает слова
    «трейдер» или «против ветра». Ключ паттерна ЕМУ ПЕРЕДАЮТ —
    dopisat_vyvod(vyvod, pattern=...). pattern=None (умолчание) —
    старое поведение без ярусов, для любого другого вызывающего
    кода, который об этом ещё не знает. Классификатор паттернов
    (какой текст к какому ключу) живёт в nositel.py — он знает
    свои же шаблоны (sudit_po_kotinu / sudit_sensora), sниффинг
    безопасен: это НАШ код генерирует текст, не LLM.

  ЧТЕНИЕ (стол): черновики показываются отдельным блоком, с
  пометкой числа повторов — «дважды, похоже на закономерность» —
  честно, без притворства, что один раз уже есть вывод.

  ЗАЩИТА ОТ ЛОЖНОГО СЧЁТА: идемпотентность закрытия сделки (не
  повторно засчитать ОДНУ И ТУ ЖЕ сделку как второй повтор паттерна)
  расширена — ищет дубликат бара и среди черновиков тоже, не только
  среди устойчивых якорей.

Требует: patch_dvizhok_yakorya_yadro_v1, patch_etalon_avana_v1,
patch_sud_sensorov_v2. Идемпотентно. .bak рядом.
Из КОРНЯ репы:  python patch_yakorya_dva_yarusa_v1.py
"""
from __future__ import annotations
import io
import sys
from pathlib import Path

MARKER = "YAKORYA_DVA_YARUSA_V1"

DVIZHOK = Path("жители") / "dvizhok.py"
NOSITEL = Path("Биржа") / "nositel.py"

# ══════════════════════════════════════════════════════════════
# 1. dvizhok.py: генерический механизм два-яруса
# ══════════════════════════════════════════════════════════════

OLD_DOPISAT = '''    def dopisat_vyvod(self, vyvod: str, limit: int = 10) -> dict:
        """Дописывает ВЫВОД из сделки в Anchor_Points — нога Опыта
        (Чертёж §5.2/4.6.4). Опыт живёт рядом с Родом, рукой самого
        жителя (в паспорт пишет только его движок). Лимит якорей — limit
        (Чертёж: 7-10); переполнение — старейшее в archive, не в
        забвение. Дубликат вывода строку не плодит. Возвращает что стало.
        # DVIZHOK_STOL_CHISTO_VYVOD_V1
        """
        vyvod = (vyvod or "").strip()
        if not vyvod:
            return {"дописано": False, "причина": "пустой вывод"}
        raw = self.p.get("Anchor_Points", "") or ""
        sep = self._yakorya_razdelitel(raw)   # DVIZHOK_YAKORYA_YADRO_V1
        lines = self._yakorya_spisok(raw)
        if vyvod in lines:
            return {"дописано": False, "причина": "уже среди якорей",
                    "всего": len(lines)}
        lines.append(vyvod)
        ushlo = []
        if len(lines) > limit:
            ushlo = lines[:len(lines) - limit]
            lines = lines[len(lines) - limit:]
            # старейшие якоря не в забвение — в архив жителя
            try:
                (self.dom / "archive").mkdir(parents=True, exist_ok=True)
                ap = self.dom / "archive" / "archive.jsonl"
                with open(ap, "a", encoding="utf-8") as f:
                    for old in ushlo:
                        f.write(json.dumps({
                            "ts": datetime.now(timezone.utc)
                                  .isoformat(timespec="seconds"),
                            "слой": "archive",
                            "факт": old,
                            "причина": "якорь вытеснен (лимит опыта)",
                        }, ensure_ascii=False) + "\\n")
            except Exception:
                pass   # архив не должен ронять запись опыта
        self.p["Anchor_Points"] = sep.join(lines)   # DVIZHOK_YAKORYA_YADRO_V1: пишем ТЕМ ЖЕ разделителем
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2),
            encoding="utf-8")
        return {"дописано": True, "всего": len(lines), "вытеснено": len(ushlo)}
'''

NEW_DOPISAT = '''    # ''' + MARKER + ''': порог повтора для перехода черновик→устойчивый.
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
                }, ensure_ascii=False) + "\\n")
        except Exception:
            pass   # архив не должен ронять запись опыта

    def dopisat_vyvod(self, vyvod: str, limit: int = 10,
                      pattern: str = None) -> dict:
        """Дописывает ВЫВОД из сделки — нога Опыта (Чертёж §5.2/4.6.4).

        ДВА ЯРУСА (Чертёж §4.4, «единичное событие меняет заряд, не
        фильтр» — защита от дребезга, решение Шефа 12.07):

          pattern=None (умолчание, старое поведение для любого чужого
            вызывающего кода) — пишет СРАЗУ в устойчивые якоря, как было.

          pattern="ключ_природы_вывода" — ДВУХЪЯРУСНЫЙ путь:
            тот же природы вывод встретился впервые → ЧЕРНОВИК (раз=1),
            стол его видит, но пониженным голосом («замечаю, не
            подтвердилось»). Встретился РОВНО В ТУ ЖЕ природу ещё раз —
            раз+=1, текст обновляется свежим. Набрал PROMOTE_THRESHOLD
            повторов → ПОВЫШЕН: уходит из черновиков, ложится постоянной
            строкой в Anchor_Points (тот же лимит 7-10, то же архивное
            вытеснение старейшего, что и раньше).

        Дубликат ТОЧНОГО текста не плодит строку ни в одном ярусе.
        Классификатор (какой текст → какой pattern) сюда НЕ входит —
        dvizhok не знает слова «трейдер»; ключ передаёт вызывающий код
        (Закон Фрактала: один механизм, разные источники).
        # DVIZHOK_STOL_CHISTO_VYVOD_V1 · ''' + MARKER + '''
        """
        vyvod = (vyvod or "").strip()
        if not vyvod:
            return {"дописано": False, "причина": "пустой вывод"}

        raw = self.p.get("Anchor_Points", "") or ""
        sep = self._yakorya_razdelitel(raw)
        lines = self._yakorya_spisok(raw)

        if vyvod in lines:
            return {"дописано": False, "причина": "уже среди устойчивых якорей",
                    "всего": len(lines)}

        # ── СТАРОЕ ПОВЕДЕНИЕ: pattern не передали — пишем сразу ───
        if pattern is None:
            lines.append(vyvod)
            ushlo = []
            if len(lines) > limit:
                ushlo = lines[:len(lines) - limit]
                lines = lines[len(lines) - limit:]
                for old in ushlo:
                    self._archive_zapis(old, "якорь вытеснен (лимит опыта)")
            self.p["Anchor_Points"] = sep.join(lines)
            self.passport_path.write_text(
                json.dumps(self.p, ensure_ascii=False, indent=2),
                encoding="utf-8")
            return {"дописано": True, "тип": "устойчивый", "всего": len(lines),
                    "вытеснено": len(ushlo)}

        # ── НОВОЕ: два яруса ────────────────────────────────────
        drafts = list(self.p.get("Draft_Anchors") or [])
        for d in drafts:
            if d.get("текст") == vyvod:
                return {"дописано": False, "причина": "уже среди черновиков",
                        "паттерн": pattern, "раз": d.get("раз", 1)}

        found = None
        for d in drafts:
            if d.get("паттерн") == pattern:
                found = d
                break

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if found is not None:
            found["раз"] = found.get("раз", 1) + 1
            found["текст"] = vyvod
            found["последний_раз"] = now_iso
            raz = found["раз"]
        else:
            found = {"текст": vyvod, "паттерн": pattern, "раз": 1,
                     "первый_раз": now_iso, "последний_раз": now_iso}
            drafts.append(found)
            raz = 1

        promoted = False
        ushlo = []
        if raz >= self.PROMOTE_THRESHOLD:
            drafts = [d for d in drafts if d is not found]
            lines.append(found["текст"])
            promoted = True
            if len(lines) > limit:
                ushlo = lines[:len(lines) - limit]
                lines = lines[len(lines) - limit:]
                for old in ushlo:
                    self._archive_zapis(old, "якорь вытеснен (лимит опыта)")
            self.p["Anchor_Points"] = sep.join(lines)

        # ── шапка черновиков: не резиновый склад ─────────────────
        vytesneno_ch = []
        if len(drafts) > self.DRAFT_CAP:
            drafts.sort(key=lambda d: (d.get("раз", 1), d.get("первый_раз", "")))
            vytesneno_ch = drafts[:len(drafts) - self.DRAFT_CAP]
            drafts = drafts[len(drafts) - self.DRAFT_CAP:]
            for d in vytesneno_ch:
                self._archive_zapis(
                    d.get("текст", ""),
                    f"черновик вытеснен, не набрал повтора ({d.get('раз',1)}/"
                    f"{self.PROMOTE_THRESHOLD})")

        self.p["Draft_Anchors"] = drafts
        self.passport_path.write_text(
            json.dumps(self.p, ensure_ascii=False, indent=2),
            encoding="utf-8")

        return {
            "дописано": True,
            "тип": "устойчивый" if promoted else "черновик",
            "раз": raz,
            "якорей": len(self._yakorya_spisok(self.p.get("Anchor_Points", "") or "")),
            "черновиков": len(drafts),
            "вытеснено_якорей": len(ushlo),
            "вытеснено_черновиков": len(vytesneno_ch),
        }
'''

# ── чтение: стол показывает черновики отдельным полем ───────────
OLD_STOL_YAKORYA = '''            "якоря":        self.p.get("Anchor_Points", ""),
'''
NEW_STOL_YAKORYA = '''            "якоря":        self.p.get("Anchor_Points", ""),
            "черновики":    self.p.get("Draft_Anchors", []),   # ''' + MARKER + '''
'''

# ══════════════════════════════════════════════════════════════
# 2. nositel.py: классификаторы паттернов + чтение черновиков
# ══════════════════════════════════════════════════════════════

CLASSIFIERS = '''

# ── КЛЮЧИ ПАТТЕРНОВ (''' + MARKER + ''') ──────────────────────────
# Природа вывода, не его точный текст. dvizhok использует ключ, чтобы
# копить повторы; сниффинг безопасен — это НАШИ ЖЕ шаблоны, не LLM.
# Порядок проверки важен: специфичные маркеры раньше общих.

def _klyuch_trader(vyvod: str) -> str:
    if "удача, а не правота" in vyvod:
        return "трейдер_плюс_удача_против_ветра"
    if "редкая ставка, не хлеб" in vyvod:
        return "трейдер_минус_против_ветра"
    if "Плата по системе" in vyvod:
        return "трейдер_минус_по_системе"
    if "Так это и работает" in vyvod:
        return "трейдер_плюс_по_ветру"
    return "трейдер_прочее"


def _klyuch_sensora(vyvod: str) -> str:
    if "МОЯ ОШИБКА" in vyvod:
        return "сенсор_ошибка"
    if "ПРОСПАЛ" in vyvod:
        return "сенсор_проспал"
    if "Подтвердилось" in vyvod:
        return "сенсор_подтвердилось"
    if "молчание было право" in vyvod:
        return "сенсор_молчание_право"
    return "сенсор_прочее"

'''

# ── zapisat_vyvod (трейдер): передать pattern + сверить черновики +
#    почистить хвостовой принт (старый ключ «всего» умер вместе с
#    одноярусной моделью; хвост ещё и рисковал задвоить лог, потому что
#    "дописано": True стоит теперь у ОБОИХ ярусов) ────────────────
OLD_TRADER_DEDUP = '''    try:
        _raw = d.p.get("Anchor_Points", "") or ""
        _est = [x.strip() for x in _raw.replace("\\\\n", "\\n").split("\\n") if x.strip()]
        _bar = ""
        if "(" in vyvod and ")" in vyvod:
            _bar = vyvod[vyvod.find("(") + 1:vyvod.find(")")]
        _dir = "SHORT" if "SHORT" in vyvod else "LONG" if "LONG" in vyvod else ""
        if _bar and _dir:
            for _e in _est:
                if _bar in _e and _dir in _e:
                    return {"дописано": False,
                            "причина": f"этот урок уже есть ({_bar} {_dir})"}
    except Exception:
        pass

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit)
    except AttributeError:
        print("[МОСТ] ⚠️  в dvizhok нет dopisat_vyvod — "
              "нужен patch_dvizhok_stol_chisto_vyvod_v1")
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']}: «{vyvod}» "
              f"(якорей: {res.get('всего')})")
    return res'''

NEW_TRADER_DEDUP = '''    try:
        _raw = d.p.get("Anchor_Points", "") or ""
        _est = [x.strip() for x in _raw.replace("\\\\n", "\\n").split("\\n") if x.strip()]
        # ''' + MARKER + ''': та же сделка не должна засчитаться как ВТОРОЙ
        # повтор паттерна — сверяем и черновики, не только устойчивые якоря.
        _est += [dd.get("текст", "") for dd in (d.p.get("Draft_Anchors") or [])]
        _bar = ""
        if "(" in vyvod and ")" in vyvod:
            _bar = vyvod[vyvod.find("(") + 1:vyvod.find(")")]
        _dir = "SHORT" if "SHORT" in vyvod else "LONG" if "LONG" in vyvod else ""
        if _bar and _dir:
            for _e in _est:
                if _bar in _e and _dir in _e:
                    return {"дописано": False,
                            "причина": f"этот урок уже есть ({_bar} {_dir})"}
    except Exception:
        pass

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit,
                              pattern=_klyuch_trader(vyvod))   # ''' + MARKER + '''
    except AttributeError:
        print("[МОСТ] ⚠️  в dvizhok нет dopisat_vyvod — "
              "нужен patch_dvizhok_stol_chisto_vyvod_v1")
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("тип") == "черновик":
        print(f"[МОСТ] 📝 черновик → {n['имя']}: «{vyvod[:60]}...» "
              f"(раз: {res.get('раз')}/3)")
    elif res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']}: «{vyvod}» "
              f"(якорей: {res.get('якорей')})")
    return res'''

# ── zapisat_vyvod_pare (сенсор): та же идемпотентность + pattern ───
OLD_SENSOR_TAIL = '''    try:
        if pnl_r is not None:
            sila = min(1.0, abs(float(pnl_r)) / 6.0)   # чужая сделка — тише
            tonus = ("минус" if "ОШИБКА" in vyvod or "ПРОСПАЛ" in vyvod
                     else "плюс")
            d.vdoh("работа", sila=sila, svezhest=1.0, tonus=tonus)
            d.sохранить()
    except Exception as e:
        print(f"[МОСТ] ⚠️  вдох не прошёл ({e})")

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit)
    except AttributeError:
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']} ({slot}): «{vyvod[:60]}...»")
    return res'''

NEW_SENSOR_TAIL = '''    try:
        if pnl_r is not None:
            sila = min(1.0, abs(float(pnl_r)) / 6.0)   # чужая сделка — тише
            tonus = ("минус" if "ОШИБКА" in vyvod or "ПРОСПАЛ" in vyvod
                     else "плюс")
            d.vdoh("работа", sila=sila, svezhest=1.0, tonus=tonus)
            d.sохранить()
    except Exception as e:
        print(f"[МОСТ] ⚠️  вдох не прошёл ({e})")

    # ''' + MARKER + ''': та же защита от ложного счёта, что у трейдера —
    # не дать одному и тому же бару засчитаться дважды в раз повтора.
    try:
        _raw = d.p.get("Anchor_Points", "") or ""
        _est = [x.strip() for x in _raw.replace("\\\\n", "\\n").split("\\n") if x.strip()]
        _est += [dd.get("текст", "") for dd in (d.p.get("Draft_Anchors") or [])]
        _bar = ""
        if "(" in vyvod and ")" in vyvod:
            _bar = vyvod[vyvod.find("(") + 1:vyvod.find(")")]
        if _bar:
            for _e in _est:
                if _bar in _e:
                    return {"дописано": False,
                            "причина": f"этот урок уже есть ({_bar})"}
    except Exception:
        pass

    try:
        res = d.dopisat_vyvod(vyvod, limit=limit,
                              pattern=_klyuch_sensora(vyvod))   # ''' + MARKER + '''
    except AttributeError:
        return {"дописано": False, "причина": "нет руки опыта"}

    if res.get("тип") == "черновик":
        print(f"[МОСТ] 📝 черновик → {n['имя']} ({slot}): «{vyvod[:60]}...» "
              f"(раз: {res.get('раз')}/3)")
    elif res.get("дописано"):
        print(f"[МОСТ] 🧠 ОПЫТ → {n['имя']} ({slot}): «{vyvod[:60]}...»")
    return res'''

# ── _sobrat_dushu: показать черновики честно, пониженным голосом ───
OLD_DUSHA_TAIL = '''    if s_domom and stol.get("дом"):
        L.append(f"\\nТвой дом: {stol['дом']}")

    return "\\n".join(L)'''

NEW_DUSHA_TAIL = '''    # ''' + MARKER + ''': черновики — видны, но НЕ равны якорям. Гл.4.4
    # Чертежа: один вывод — не опыт; показываем честно, без притворства.
    chernoviki = stol.get("черновики") or []
    if chernoviki:
        L.append("\\nЗАМЕЧАЮ ЗА СОБОЙ (пока не подтвердилось повтором —"
                 " не готовый вывод, наблюдение):")
        for d in chernoviki:
            raz = d.get("раз", 1)
            hvost = "" if raz < 2 else f" (уже {raz} раз(а) — похоже на закономерность)"
            L.append(f"  • {d.get('текст','')}{hvost}")

    if s_domom and stol.get("дом"):
        L.append(f"\\nТвой дом: {stol['дом']}")

    return "\\n".join(L)'''


def die(m, c=1):
    print("✗ " + m)
    return c


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("═══ ДВА ЯРУСА ЯКОРЕЙ — черновик и устойчивый ═══")

    for p in (DVIZHOK, NOSITEL):
        if not p.exists():
            return die(f"не нашёл {p} — ты в КОРНЕ репы?")

    # ── dvizhok ──────────────────────────────────────────────
    d = DVIZHOK.read_text(encoding="utf-8")
    if MARKER in d:
        print("✓ dvizhok уже пропатчен")
    else:
        for old, what in ((OLD_DOPISAT, "dopisat_vyvod (одноярусный)"),
                          (OLD_STOL_YAKORYA, "строка «якоря» в чистом столе")):
            if old not in d:
                return die(f"dvizhok: не нашёл «{what}». Сверь глазами — "
                           "патчи A/B/C легли не так, как ожидалось.", 3)
        bak = DVIZHOK.with_suffix(".py.bak_yarus")
        if not bak.exists():
            bak.write_text(d, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        d = d.replace(OLD_DOPISAT, NEW_DOPISAT, 1)
        d = d.replace(OLD_STOL_YAKORYA, NEW_STOL_YAKORYA, 1)
        DVIZHOK.write_text(d, encoding="utf-8")
        print("✓ dvizhok: dopisat_vyvod несёт два яруса (pattern=None — "
              "старое поведение, кто не знает — не заметит)")

    # ── nositel ──────────────────────────────────────────────
    n = NOSITEL.read_text(encoding="utf-8")
    if MARKER in n:
        print("✓ nositel уже пропатчен")
    else:
        for old, what in ((OLD_TRADER_DEDUP, "хвост zapisat_vyvod (трейдер)"),
                          (OLD_SENSOR_TAIL, "хвост zapisat_vyvod_pare (сенсор)"),
                          (OLD_DUSHA_TAIL, "хвост _sobrat_dushu")):
            if old not in n:
                return die(f"nositel: не нашёл «{what}». Сверь глазами.", 4)
        bak = NOSITEL.with_suffix(".py.bak_yarus")
        if not bak.exists():
            bak.write_text(n, encoding="utf-8")
            print(f"  • бэкап: {bak}")
        # классификаторы — перед первым использованием (после sudit_po_kotinu)
        anchor = "def zapisat_vyvod(magic"
        if anchor not in n:
            return die("nositel: не нашёл начало zapisat_vyvod для врезки "
                       "классификаторов.", 5)
        n = n.replace(anchor, CLASSIFIERS.strip() + "\n\n\n" + anchor, 1)
        n = n.replace(OLD_TRADER_DEDUP, NEW_TRADER_DEDUP, 1)
        n = n.replace(OLD_SENSOR_TAIL, NEW_SENSOR_TAIL, 1)
        n = n.replace(OLD_DUSHA_TAIL, NEW_DUSHA_TAIL, 1)
        NOSITEL.write_text(n, encoding="utf-8")
        print("✓ nositel: классификаторы паттернов + черновики в душе + "
              "защита от ложного счёта")

    print("───")
    print("Порог повтора: 3 (тот же, что Путь Зрелости — не новое число).")
    print("Первый минус против ветра — теперь ЧЕРНОВИК, не якорь.")
    print("Третий такой же — ПОВЫШАЕТСЯ в устойчивый Anchor_Points.")
    print("\nПроверка: python proverka_koltsa.py — увидишь и якоря, и черновики.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
