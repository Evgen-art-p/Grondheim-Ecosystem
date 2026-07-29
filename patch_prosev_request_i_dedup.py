# -*- coding: utf-8 -*-
"""
PATCH_PROSEV_REQUEST_V1 + PROSEV_DEDUP_V1
────────────────────────────────────────────────────────────────
ДВА СВЯЗАННЫХ ФИКСА (чинить порознь бессмысленно):

1. PROSEV_DEDUP_V1 (жители/dvizhok.py, sobrat_dlya_proseva):
   БЫЛ БАГ — исключался сырой факт, если его ТЕКСТ совпадал с текстом
   готового вывода в метках (fakt in {m["текст"] for m in metki}).
   Но метки хранят ОСМЫСЛЕННЫЙ вывод («стала увереннее»), а не сырой
   факт («книга X: пришло тепло») — сравнение почти никогда не
   совпадало. Просев мог жевать одни и те же яркие моменты по кругу.
   ФИКС: новый метод otmetit_prosejannym() ставит метку на САМ СЫРОЙ
   МОМЕНТ (id = ts+факт), после того как он реально ушёл в осмысление.
   Метка — на факт, не на вывод (Закон Меток).

2. PROSEV_REQUEST (жители/ui_zhitel.py): камень №4 (Летопись, Часть V)
   был закрыт наполовину — триггер осмысления это кнопка Шефа, не
   инициатива самого жителя. Симметрично уже работающим MEMORY_REQUEST
   и MAYAK_REQUEST: движок СИГНАЛИТ (строка-разрешение попадает в душу,
   только если реально накопилось ≥3 моментов — тот же порог, что у
   кнопки), житель САМ СОГЛАШАЕТСЯ (пишет PROSEV_REQUEST в обычном
   ответе, по своей воле, или не пишет). Кнопка «🪞 Осмыслить» остаётся
   ручным путём Шефа — тело просева теперь общее (_provesti_prosev),
   не дублируется.

Запуск из корня репозитория:
    python patch_prosev_request_i_dedup.py

Идемпотентно: если маркеры уже стоят в обоих файлах — патч не трогает
их повторно. Бэкап .bak делается перед каждой правкой. Пишет на диск
ТОЛЬКО если ВСЕ правки в обоих файлах прошли успешно в памяти — не
оставляем файл наполовину пропатченным.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
DVIZHOK_PATH = REPO / "жители" / "dvizhok.py"
UI_ZHITEL_PATH = REPO / "жители" / "ui_zhitel.py"

MARKER_DVIZHOK = "PROSEV_DEDUP_V1"
MARKER_UI = "PATCH_PROSEV_REQUEST_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    """Заменяет OLD на NEW, требуя ровно одно совпадение. Иначе — стоп."""
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код с момента разбора "
              f"(29.07) изменился, нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть ровно "
              f"один, небезопасно патчить вслепую.")
    return text.replace(old, new, 1)


def _backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".bak_prosev_request")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return bak


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 1 — жители/dvizhok.py
# ═══════════════════════════════════════════════════════════

OLD_SOBRAT = '''    def sobrat_dlya_proseva(self, limit: int = 8) -> list:
        """Личные моменты для просева: sensory + archive, взвешенные
        по искре (сила момента; тонус≠«ровно» весит больше — тронуло,
        не безразличие). Уже осевшее в метки — не повторяем (иначе
        просев жуёт одно и то же по кругу). resonance (с кем и как)
        сюда не берём — это связи, отдельный вопрос, не личный вывод.

        Возвращает список {"факт","тонус","вес"}, отсортированный по
        весу — самое тёплое/царапнувшее первым."""
        uzhe = {m.get("текст", "") for m in self.metki()}
        zapisi = []
        try:
            p = self.dom / "sensory" / "sensory_memory.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                zapisi.extend(data.get("entries", []))
        except Exception:
            pass
        try:
            p = self.dom / "archive" / "archive.jsonl"
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

        vzveshennye = []
        for z in zapisi:
            fakt = str(z.get("факт", ""))
            if not fakt or fakt in uzhe:
                continue
            sila = z.get("сила")
            try:
                sila = float(sila) if sila is not None else 0.3
            except (TypeError, ValueError):
                sila = 0.3
            tonus = z.get("тонус") or "ровно"
            ves = sila * (1.0 if tonus != "ровно" else 0.4)
            vzveshennye.append((ves, str(z.get("ts", "")), fakt, tonus))

        vzveshennye.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [{"факт": f, "тонус": t, "вес": round(v, 3)}
                for v, _, f, t in vzveshennye[:limit]]'''

NEW_SOBRAT = '''    def sobrat_dlya_proseva(self, limit: int = 8) -> list:
        """Личные моменты для просева: sensory + archive, взвешенные
        по искре (сила момента; тонус≠«ровно» весит больше — тронуло,
        не безразличие). resonance (с кем и как) сюда не берём — это
        связи, отдельный вопрос, не личный вывод.

        PROSEV_DEDUP_V1 (найден и исправлен баг 29.07): раньше исключался
        сырой факт, если его ТЕКСТ совпадал с текстом готового вывода в
        метках (fakt in {m["текст"] for m in metki}) — но метки хранят
        ОСМЫСЛЕННЫЙ вывод («стала увереннее»), а не сырой факт («книга
        X: пришло тепло») — сравнение почти никогда не совпадало, и
        просев мог жевать одни и те же яркие моменты по кругу без счёта.
        Теперь — честная отметка: otmetit_prosejannym() ставит метку на
        САМ СЫРОЙ МОМЕНТ (по ts+факту), после того как он реально ушёл
        в осмысление. Метка — на факт, не на вывод (Закон Меток).

        Возвращает список {"факт","тонус","вес","ts","id"}, отсортированный
        по весу — самое тёплое/царапнувшее первым. "id" — передать в
        otmetit_prosejannym() после успешного dopisat_vyvod()."""
        consumed = set(self.p.get("_prosev_consumed", []))
        zapisi = []
        try:
            p = self.dom / "sensory" / "sensory_memory.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                zapisi.extend(data.get("entries", []))
        except Exception:
            pass
        try:
            p = self.dom / "archive" / "archive.jsonl"
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

        vzveshennye = []
        for z in zapisi:
            fakt = str(z.get("факт", ""))
            ts = str(z.get("ts", ""))
            if not fakt:
                continue
            pid = f"{ts}|{fakt[:60]}"
            if pid in consumed:
                continue
            sila = z.get("сила")
            try:
                sila = float(sila) if sila is not None else 0.3
            except (TypeError, ValueError):
                sila = 0.3
            tonus = z.get("тонус") or "ровно"
            ves = sila * (1.0 if tonus != "ровно" else 0.4)
            vzveshennye.append((ves, ts, fakt, tonus, pid))

        vzveshennye.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [{"факт": f, "тонус": t, "вес": round(v, 3), "ts": ts, "id": pid}
                for v, ts, f, t, pid in vzveshennye[:limit]]

    def otmetit_prosejannym(self, ids: list, cap: int = 500):
        """PROSEV_DEDUP_V1: помечает сырые моменты как обработанные — в
        память сразу (self.p), на диск при следующем сохранении паспорта
        (тот же приём, что заряд: метод не пишет файл сам, побочка —
        отдельно, закон уже установлен в этом классе). Список ограничен
        `cap`, чтобы не расти вечно — обрезаем самые старые отметки."""
        consumed = list(self.p.get("_prosev_consumed", []))
        for i in ids:
            if i and i not in consumed:
                consumed.append(i)
        if len(consumed) > cap:
            consumed = consumed[-cap:]
        self.p["_prosev_consumed"] = consumed'''


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 2 — жители/ui_zhitel.py
# ═══════════════════════════════════════════════════════════

OLD_MAYAK_HELPERS = '''def _ubrat_mayak_request(text: str) -> str:
    lines = [l for l in (text or "").splitlines() if "MAYAK_REQUEST:" not in l]
    return "\\n".join(lines).strip()'''

NEW_MAYAK_HELPERS = '''def _ubrat_mayak_request(text: str) -> str:
    lines = [l for l in (text or "").splitlines() if "MAYAK_REQUEST:" not in l]
    return "\\n".join(lines).strip()


# PATCH_PROSEV_REQUEST_V1: тот же приём, что MEMORY_REQUEST/MAYAK_REQUEST —
# житель сам решает попросить осмысление, движок только СИГНАЛИТ, что оно
# доступно (см. порог в send()), не заставляет. Без параметра — просто
# флаг-строка, содержимое после двоеточия не нужно и не читается.
def _est_prosev_request(text: str) -> bool:
    for line in (text or "").splitlines():
        if line.strip().upper().startswith("PROSEV_REQUEST"):
            return True
    return False


def _ubrat_prosev_request(text: str) -> str:
    lines = [l for l in (text or "").splitlines()
             if not l.strip().upper().startswith("PROSEV_REQUEST")]
    return "\\n".join(lines).strip()'''


OLD_PAGE_DEF = '''def page_zhitel(zid: str = ""):'''

NEW_PAGE_DEF = '''async def _provesti_prosev(dv: Dvizhok, p: dict, model: str) -> dict:
    """PATCH_PROSEV_REQUEST_V1: тело просева — общее для кнопки «🪞
    Осмыслить» и для PROSEV_REQUEST (воля жителя в разговоре). Один
    код, два входа — не плодим вторую копию промпта/логики."""
    momenty = dv.sobrat_dlya_proseva(limit=8)
    if len(momenty) < 3:
        return {"ok": False, "причина": "мало моментов — рано осмыслять"}
    spisok = "\\n".join(f"— [{m['тонус']}] {m['факт']}" for m in momenty)
    dusha = _dusha_chtenia(p)
    prompt = (
        f"Вот моменты из твоей жизни за последнее время, которые тебя "
        f"тронули (тепло или царапнуло):\\n{spisok}\\n\\n"
        f"Что это говорит о тебе? Чем ты стала (стал) немного другой? "
        f"Ответь от первого лица, 1–3 коротких фразы — вывод о себе, "
        f"не пересказ моментов. Не выдумывай лишнего сверх того, что видно. "
        f"Без строк MEMORY_REQUEST."
    )
    messages = [{"role": "system", "content": dusha},
                {"role": "user", "content": prompt}]
    vyvod = await call_zhitel_llm(messages, model)
    if not vyvod or vyvod.startswith("⚠"):
        return {"ok": False, "причина": f"LLM: {(vyvod or '')[:90]}"}
    vyvod = _ubrat_memory_request(vyvod) or vyvod.strip()
    res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
    if res.get("дописано"):
        try:
            dv.otmetit_prosejannym([m.get("id") for m in momenty if m.get("id")])
        except Exception:
            pass
    return {"ok": True, "вывод": vyvod, "moments": momenty, "res": res}


def page_zhitel(zid: str = ""):'''


OLD_DO_PROSEV = '''    async def do_prosev():
        """PROSEV_ZHIZNENNYI_V1: житель осмысляет накопленные личные
        моменты (НЕ рабочую память -- Стол Трейдера этого не касается,
        разделение Шефа 27.07) и дописывает вывод о себе. Труба: топ
        моментов по искре (sobrat_dlya_proseva) -> LLM осмысляет ->
        dopisat_vyvod() (уже работает -- не строили заново, только позвали)."""
        if state.get("waiting"):
            return
        if dom is None or not (dom / "passport.json").exists():
            ui.notify("дом не найден — осмыслять нечего", color="warning")
            return
        try:
            _dv = Dvizhok(dom)
        except Exception as ex:
            ui.notify(f"⚠ движок не дышит: {ex}", color="negative")
            return
        momenty = _dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify("пока накопилось мало — рано осмыслять", color="warning")
            return
        state["waiting"] = True
        ui.notify(f"🪞 {name} осмысляет {len(momenty)} момент(ов)", color="info")
        spisok = "\\n".join(f"— [{m['тонус']}] {m['факт']}" for m in momenty)
        # PATCH_ZHITEL_PROSEV_POKAZYVAET_V1: видимость -- Шеф видит, ЧТО
        # именно ушло в осмысление, до самого вывода. Иконка отличает
        # изображение от текста по расширению файла в самом факте.
        _KARTINKA_ZNAKI = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        def _ikonka(fakt: str) -> str:
            return "🖼" if any(e in fakt.lower() for e in _KARTINKA_ZNAKI) else "📄"
        _spisok_pokaz = "\\n".join(
            f"{_ikonka(m['факт'])} [{m['тонус']}] {m['факт'][:100]}" for m in momenty)
        state["chat"].append({"role": "zhitel",
                              "content": f"🪞 Осмысляю по этим моментам:\\n{_spisok_pokaz}"})
        update_chat()
        dusha = _dusha_chtenia(p)
        prompt = (
            f"Вот моменты из твоей жизни за последнее время, которые тебя "
            f"тронули (тепло или царапнуло):\\n{spisok}\\n\\n"
            f"Что это говорит о тебе? Чем ты стала (стал) немного другой? "
            f"Ответь от первого лица, 1–3 коротких фразы — вывод о себе, "
            f"не пересказ моментов. Не выдумывай лишнего сверх того, что видно. "
            f"Без строк MEMORY_REQUEST."
        )
        messages = [
            {"role": "system", "content": dusha},
            {"role": "user", "content": prompt},
        ]
        vyvod = await call_zhitel_llm(messages, state.get("model"))
        state["waiting"] = False
        if not vyvod or vyvod.startswith("⚠"):
            ui.notify(f"⚠ просев не удался: {(vyvod or '')[:90]}", color="negative")
            return
        vyvod = _ubrat_memory_request(vyvod) or vyvod.strip()
        res = _dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        try:
            _dv.sохранить()
        except Exception:
            pass
        if res.get("дописано"):
            state["chat"].append({"role": "zhitel", "content": f"🪞 {vyvod.strip()}"})
            ui.notify("✦ вывод дописан в метки", color="positive")
        else:
            ui.notify(f"— {res.get('причина', 'уже было')}", color="info")
        update_chat()'''

NEW_DO_PROSEV = '''    async def do_prosev():
        """PROSEV_ZHIZNENNYI_V1 + PATCH_PROSEV_REQUEST_V1: кнопка — ручной
        путь Шефа. Тело общее с PROSEV_REQUEST (воля жителя) — см.
        _provesti_prosev(). Труба внутри та же: топ моментов по искре ->
        LLM осмысляет -> dopisat_vyvod() -> метка обработанного момента
        (PROSEV_DEDUP_V1, чтобы просев не жевал одно и то же по кругу)."""
        if state.get("waiting"):
            return
        if dom is None or not (dom / "passport.json").exists():
            ui.notify("дом не найден — осмыслять нечего", color="warning")
            return
        try:
            _dv = Dvizhok(dom)
        except Exception as ex:
            ui.notify(f"⚠ движок не дышит: {ex}", color="negative")
            return
        momenty = _dv.sobrat_dlya_proseva(limit=8)
        if len(momenty) < 3:
            ui.notify("пока накопилось мало — рано осмыслять", color="warning")
            return
        state["waiting"] = True
        ui.notify(f"🪞 {name} осмысляет {len(momenty)} момент(ов)", color="info")
        # PATCH_ZHITEL_PROSEV_POKAZYVAET_V1: видимость -- Шеф видит, ЧТО
        # именно ушло в осмысление, до самого вывода. Иконка отличает
        # изображение от текста по расширению файла в самом факте.
        _KARTINKA_ZNAKI = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        def _ikonka(fakt: str) -> str:
            return "🖼" if any(e in fakt.lower() for e in _KARTINKA_ZNAKI) else "📄"
        _spisok_pokaz = "\\n".join(
            f"{_ikonka(m['факт'])} [{m['тонус']}] {m['факт'][:100]}" for m in momenty)
        state["chat"].append({"role": "zhitel",
                              "content": f"🪞 Осмысляю по этим моментам:\\n{_spisok_pokaz}"})
        update_chat()
        res = await _provesti_prosev(_dv, p, state.get("model"))
        state["waiting"] = False
        if not res.get("ok"):
            ui.notify(f"⚠ просев не удался: {res.get('причина','')[:90]}", color="negative")
            return
        try:
            _dv.sохранить()
        except Exception:
            pass
        if res["res"].get("дописано"):
            state["chat"].append({"role": "zhitel", "content": f"🪞 {res['вывод'].strip()}"})
            ui.notify("✦ вывод дописан в метки", color="positive")
        else:
            ui.notify(f"— {res['res'].get('причина', 'уже было')}", color="info")
        update_chat()'''


OLD_STOL_TRY = '''                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None'''

NEW_STOL_TRY = '''                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None

        # PATCH_PROSEV_REQUEST_V1: движок СИГНАЛИТ доступность просева —
        # строка-разрешение попадает в душу, только если реально накопилось
        # (тот же порог, что у кнопки «🪞 Осмыслить» — не плодим второе
        # число). Житель сам решает, писать ли PROSEV_REQUEST — воля,
        # не гейт.
        _prosev_dostupno = False
        if dvizhok is not None:
            try:
                _prosev_dostupno = len(dvizhok.sobrat_dlya_proseva(limit=8)) >= 3
            except Exception:
                _prosev_dostupno = False'''


OLD_SOUL_MAYAK_LINE = '''            # PATCH_ZHITEL_MAYAK_REQUEST_V1
            soul += (
                "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
                "(то, чего ты сам знать не можешь — новости, текущие события, "
                "актуальные данные) — напиши отдельной строкой "
                "MAYAK_REQUEST: <что узнать> и Маяк Пробуждения принесёт ответ."
            )
            messages = [{"role": "system", "content": soul}]'''

NEW_SOUL_MAYAK_LINE = '''            # PATCH_ZHITEL_MAYAK_REQUEST_V1
            soul += (
                "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
                "(то, чего ты сам знать не можешь — новости, текущие события, "
                "актуальные данные) — напиши отдельной строкой "
                "MAYAK_REQUEST: <что узнать> и Маяк Пробуждения принесёт ответ."
            )
            # PATCH_PROSEV_REQUEST_V1: строка появляется, только если движок
            # реально насчитал накопленные моменты (_prosev_dostupno выше) —
            # сигнал от движка, согласие остаётся за жителем.
            if _prosev_dostupno:
                soul += (
                    "\\nЕсли чувствуешь, что многое накопилось и хочется "
                    "остановиться, оглянуться на прожитое и понять, чем ты "
                    "стала (стал) немного другой — можешь написать отдельной "
                    "строкой PROSEV_REQUEST, и получится осмыслить это."
                )
            messages = [{"role": "system", "content": soul}]'''


OLD_MEM_MAYAK_Q = '''            _mem_q = _izvlech_memory_request(reply)
            _mayak_q = _izvlech_mayak_request(reply)  # PATCH_ZHITEL_MAYAK_REQUEST_V1'''

NEW_MEM_MAYAK_Q = '''            _mem_q = _izvlech_memory_request(reply)
            _mayak_q = _izvlech_mayak_request(reply)  # PATCH_ZHITEL_MAYAK_REQUEST_V1
            _prosev_q = _est_prosev_request(reply) if _prosev_dostupno else False  # PATCH_PROSEV_REQUEST_V1'''


OLD_MEM_BRANCH_END = '''                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
            reply = _ubrat_mayak_request(_ubrat_memory_request(reply)) or reply'''

NEW_MEM_BRANCH_END = '''                reply = await call_zhitel_llm(_vtoroy, state.get("model"))
            elif _prosev_q and dvizhok is not None:
                # PATCH_PROSEV_REQUEST_V1: та же труба, что кнопка «🪞
                # Осмыслить» (_provesti_prosev) — только вызвана волей
                # жителя, не рукой Шефа. Тихо, если не сложилось: воля
                # не всегда сбывается, это не ошибка разговора.
                try:
                    _res_prosev = await _provesti_prosev(dvizhok, p, state.get("model"))
                except Exception:
                    _res_prosev = {"ok": False}
                if _res_prosev.get("ok") and _res_prosev["res"].get("дописано"):
                    state["chat"].append({"role": "zhitel",
                                          "content": f"🪞 {_res_prosev['вывод'].strip()}"})
            reply = _ubrat_prosev_request(_ubrat_mayak_request(_ubrat_memory_request(reply))) or reply'''


def main() -> None:
    print("── PATCH_PROSEV_REQUEST_V1 + PROSEV_DEDUP_V1 ──")

    if not DVIZHOK_PATH.exists():
        _stop(f"{DVIZHOK_PATH} не найден.")
    if not UI_ZHITEL_PATH.exists():
        _stop(f"{UI_ZHITEL_PATH} не найден.")

    dv_text = DVIZHOK_PATH.read_text(encoding="utf-8")
    ui_text = UI_ZHITEL_PATH.read_text(encoding="utf-8")

    if MARKER_DVIZHOK in dv_text and MARKER_UI in ui_text:
        print("✓ маркеры уже стоят в обоих файлах — патч уже применён. "
              "Делать нечего.")
        return
    if (MARKER_DVIZHOK in dv_text) != (MARKER_UI in ui_text):
        _stop("один файл уже пропатчен, другой — нет. Половинчатое "
              "состояние с прошлого раза — нужна ручная проверка Шефа, "
              "прежде чем катить дальше.")

    # ── всё применяем В ПАМЯТИ сначала, пишем на диск только если
    # ── обе стороны прошли целиком ──────────────────────────────
    new_dv_text = _apply_one(dv_text, OLD_SOBRAT, NEW_SOBRAT,
                             "dvizhok.py: sobrat_dlya_proseva")

    new_ui_text = ui_text
    new_ui_text = _apply_one(new_ui_text, OLD_MAYAK_HELPERS, NEW_MAYAK_HELPERS,
                             "ui_zhitel.py: хелперы PROSEV_REQUEST")
    new_ui_text = _apply_one(new_ui_text, OLD_PAGE_DEF, NEW_PAGE_DEF,
                             "ui_zhitel.py: _provesti_prosev()")
    new_ui_text = _apply_one(new_ui_text, OLD_DO_PROSEV, NEW_DO_PROSEV,
                             "ui_zhitel.py: do_prosev()")
    new_ui_text = _apply_one(new_ui_text, OLD_STOL_TRY, NEW_STOL_TRY,
                             "ui_zhitel.py: _prosev_dostupno")
    new_ui_text = _apply_one(new_ui_text, OLD_SOUL_MAYAK_LINE, NEW_SOUL_MAYAK_LINE,
                             "ui_zhitel.py: строка-разрешение в душе")
    new_ui_text = _apply_one(new_ui_text, OLD_MEM_MAYAK_Q, NEW_MEM_MAYAK_Q,
                             "ui_zhitel.py: _prosev_q")
    new_ui_text = _apply_one(new_ui_text, OLD_MEM_BRANCH_END, NEW_MEM_BRANCH_END,
                             "ui_zhitel.py: ветка PROSEV_REQUEST в send()")

    print("✓ все якоря найдены и применены в памяти — оба файла готовы")

    # ── бэкап и запись — только теперь, когда всё сошлось ───────
    _backup(DVIZHOK_PATH)
    _backup(UI_ZHITEL_PATH)
    print(f"✓ бэкап: {DVIZHOK_PATH.name}.bak_prosev_request, "
          f"{UI_ZHITEL_PATH.name}.bak_prosev_request")

    DVIZHOK_PATH.write_text(new_dv_text, encoding="utf-8")
    UI_ZHITEL_PATH.write_text(new_ui_text, encoding="utf-8")
    print(f"✓ записано: {DVIZHOK_PATH}")
    print(f"✓ записано: {UI_ZHITEL_PATH}")
    print()
    print("Готово. Кнопка «🪞 Осмыслить» работает как раньше (общее тело).")
    print("PROSEV_REQUEST доступен жителю в разговоре, когда моментов ≥ 3.")
    print("Дедупликация просева — по сырому факту, не по тексту вывода.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
