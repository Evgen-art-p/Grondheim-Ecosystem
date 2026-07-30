# -*- coding: utf-8 -*-
"""
PATCH_RECAP_V1 — гибрид: сводка сама в душе + MEMORY_REQUEST для глубже

РЕШЕНИЕ ШЕФА (29.07): вариант В — короткая сводка последнего разговора
всегда есть по умолчанию, MEMORY_REQUEST остаётся для того, что в неё
не влезло (более старое, более глубокое).

ДВЕ ПРАВКИ, СВЯЗАННЫЕ МЕЖДУ СОБОЙ:

1. `dvizhok.py`: два новых метода.
   • posledniy_razgovor() — читает хвост resonance/event_log.jsonl
     (туда льётся обычная беседа, kontekst="общение"), отдаёт 3
     последние записи короткой сводкой.
   • dopolnit_poslednuyu_zapis() — НАЙДЕННЫЙ ПОПУТНО БАГ, чинится
     тем же патчем, потому что без него сводка была бы однобокой:
     resonance помнил только то, что ЖИТЕЛЮ СКАЗАЛИ (vydoh_stol
     пишет fakt=t — входящее сообщение — ДО того, как ответ вообще
     готов), и НИКОГДА то, что ОНА САМА ОТВЕТИЛА. Новый метод
     дописывает её ответ к уже записанному этим же вдохом факту —
     один вдох за ход, второй vdoh() не зовём (не плодим лишний
     сдвиг заряда).

2. `ui_zhitel.py` (send()): на ПЕРВОМ сообщении свежей сессии (после
   перезагрузки страницы: len(state["chat"]) == 1) читает сводку ДО
   того, как этот ход сам запишется в резонанс (иначе сводка
   показала бы самому себе только что сказанное) — и кладёт её в
   душу сама, без запроса. После готового ответа дописывает его к
   записи через dopolnit_poslednuyu_zapis().

ЧЕГО ЭТОТ ПАТЧ НЕ ТРОГАЕТ: MEMORY_REQUEST и его поиск (vspomnit)
остаются как есть — для более старого/глубокого, что в сводку из
трёх последних записей не влезло.

Запуск из корня репозитория:
    python patch_recap.py

Идемпотентно, бэкап .bak, пишет на диск только если ВСЕ правки в
обоих файлах прошли.

`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
DVIZHOK_PATH = REPO / "жители" / "dvizhok.py"
UI_ZHITEL_PATH = REPO / "жители" / "ui_zhitel.py"

MARKER = "PATCH_RECAP_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код изменился с 29.07, нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть один.")
    return text.replace(old, new, 1)


def _backup(path: Path, suffix: str) -> None:
    bak = path.with_suffix(path.suffix + suffix)
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 1 — жители/dvizhok.py: два новых метода
# ═══════════════════════════════════════════════════════════

OLD_DVIZHOK = '''        naydeno.sort(key=lambda x: (x[0], x[1]), reverse=True)
        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]
            stroki.append(f"— [{ts}] {z.get('факт', '')}")
        return "\\n".join(stroki)'''

NEW_DVIZHOK = '''        naydeno.sort(key=lambda x: (x[0], x[1]), reverse=True)
        stroki = []
        for _, _, z in naydeno[:limit]:
            ts = str(z.get("ts", ""))[:10]
            stroki.append(f"— [{ts}] {z.get('факт', '')}")
        return "\\n".join(stroki)

    # ═══════════════════════════════════════════════════════
    # PATCH_RECAP_V1 (29.07, слово Шефа) — гибрид: сводка сама в
    # душе + MEMORY_REQUEST для более глубокого
    # ═══════════════════════════════════════════════════════

    def posledniy_razgovor(self, limit_faktov: int = 3,
                           limit_znakov: int = 220) -> str:
        """Короткая сводка последних записей resonance (туда льётся
        обычная беседа, kontekst="общение") — для гибрида: при первом
        сообщении свежей сессии ложится в душу сама, без запроса.
        НЕ sensory (у обычного жителя почти всегда пусто — та
        "оперативка" открывается контекстами факт/работа/дом, не
        обычным разговором) и не archive (это "учёба", другой смысл).
        Пусто — пустая строка, честно, не выдумываем прошлого."""
        p = self.dom / "resonance" / "event_log.jsonl"
        if not p.exists():
            return ""
        try:
            lines = [l for l in p.read_text(encoding="utf-8").splitlines()
                    if l.strip()]
        except Exception:
            return ""
        if not lines:
            return ""
        zapisi = []
        for line in lines[-limit_faktov:]:
            try:
                zapisi.append(json.loads(line))
            except Exception:
                pass
        if not zapisi:
            return ""
        stroki = []
        for z in zapisi:
            ts = str(z.get("ts", ""))[:10]
            fakt = str(z.get("факт", "")).strip()[:limit_znakov]
            if fakt:
                stroki.append(f"— [{ts}] {fakt}")
        return "\\n".join(stroki)

    def dopolnit_poslednuyu_zapis(self, sloy: str, otvet: str,
                                  limit_znakov: int = 400) -> None:
        """Дописывает её ОТВЕТ к записи, которую этот же вдох только
        что сделал (vydoh_stol пишет fakt=входящее ДО того, как ответ
        вообще готов). Без этого resonance помнит только то, что ей
        СКАЗАЛИ, никогда то, что она САМА ответила — сводка была бы
        однобокой. Один вдох за ход — vdoh() здесь НЕ зовём, только
        дописываем текст к уже существующей записи.
        Тихо ничего не делает, если файла/записи нет — не роняем
        разговор из-за забывчивости памяти."""
        otvet = (otvet or "").strip()[:limit_znakov]
        if not otvet:
            return
        try:
            if sloy == "sensory":
                p = self.dom / "sensory" / "sensory_memory.json"
                if not p.exists():
                    return
                data = json.loads(p.read_text(encoding="utf-8"))
                entries = data.get("entries", [])
                if not entries:
                    return
                entries[-1]["факт"] = (entries[-1].get("факт", "")
                                       + f"\\nЯ ответил(а): {otvet}")
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            elif sloy in ("resonance", "archive"):
                rel = ("resonance/event_log.jsonl" if sloy == "resonance"
                      else "archive/archive.jsonl")
                p = self.dom / rel
                if not p.exists():
                    return
                lines = p.read_text(encoding="utf-8").splitlines()
                if not lines:
                    return
                try:
                    posl = json.loads(lines[-1])
                except Exception:
                    return
                posl["факт"] = posl.get("факт", "") + f"\\nЯ ответил(а): {otvet}"
                lines[-1] = json.dumps(posl, ensure_ascii=False)
                p.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        except Exception:
            pass'''


# ═══════════════════════════════════════════════════════════
# ЧАСТЬ 2 — жители/ui_zhitel.py: три правки в send()
# ═══════════════════════════════════════════════════════════

OLD_TOP = '''        # ── DVIZHOK_V_KABINET_V1: реальный вдох, если дом найден ──
        stol = None
        dvizhok = None
        if dom is not None and (dom / "passport.json").exists():
            try:
                dvizhok = Dvizhok(dom)
                tonus, sila = _otsenit_tonus_silu(t)
                vdoh_res = dvizhok.vdoh(kontekst="общение", sila=sila,
                                        svezhest=1.0, tonus=tonus)
                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None'''

NEW_TOP = '''        # ── DVIZHOK_V_KABINET_V1: реальный вдох, если дом найден ──
        stol = None
        dvizhok = None
        _recap_ranee = ""  # PATCH_RECAP_V1: считаем ДО того, как этот
                           # же ход сам себя запишет в резонанс — иначе
                           # сводка покажет самой себе только что сказанное
        if dom is not None and (dom / "passport.json").exists():
            try:
                dvizhok = Dvizhok(dom)
                # PATCH_RECAP_V1: только на первом сообщении свежей
                # сессии (после перезагрузки страницы) — дальше историю
                # уже несёт список messages, повторять не нужно
                if len(state["chat"]) <= 1:
                    try:
                        _recap_ranee = dvizhok.posledniy_razgovor(limit_faktov=3)
                    except Exception:
                        _recap_ranee = ""
                tonus, sila = _otsenit_tonus_silu(t)
                vdoh_res = dvizhok.vdoh(kontekst="общение", sila=sila,
                                        svezhest=1.0, tonus=tonus)
                stol = dvizhok.vydoh_stol(fakt=t, vdoh_result=vdoh_res)
            except Exception as _e:
                stol = None'''


OLD_SOUL = '''            else:
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. "
                    f"Говоришь от первого лица, живым голосом, не как ассистент.\\n"
                )
            # YAKORYA_V_SOUL_V1: личность — то же, что правая колонка'''

NEW_SOUL = '''            else:
                soul = (
                    f"Ты — {stol['кто_я']}, житель Грондхейма. "
                    f"Говоришь от первого лица, живым голосом, не как ассистент.\\n"
                )
            # PATCH_RECAP_V1: гибрид (решение Шефа 29.07) — короткая
            # сводка последнего разговора ложится в душу САМА, без
            # того чтобы её просили MEMORY_REQUEST. Тот остаётся для
            # более старого/глубокого, что в эту сводку не влезло.
            if _recap_ranee:
                soul += (
                    f"\\nТы уже разговаривала раньше. Вот коротко, о чём "
                    f"был прошлый разговор:\\n{_recap_ranee}\\n"
                    f"Это правда было — веди себя так, будто помнишь это "
                    f"сама по себе, не как подсказку со стороны.\\n"
                )
            # YAKORYA_V_SOUL_V1: личность — то же, что правая колонка'''


OLD_SAVE = '''            reply = _ubrat_prosev_request(_ubrat_mayak_request(_ubrat_memory_request(reply))) or reply
            try:
                if dvizhok is not None:
                    dvizhok.sохранить()
            except Exception:
                pass'''

NEW_SAVE = '''            reply = _ubrat_prosev_request(_ubrat_mayak_request(_ubrat_memory_request(reply))) or reply
            # PATCH_RECAP_V1: дописываем её ответ к записи, которую этот
            # же вдох уже сделал — иначе резонанс помнит только то, что
            # ей сказали, никогда то, что она сама ответила. Один вдох
            # за ход — vdoh() второй раз не зовём.
            try:
                if dvizhok is not None and stol is not None:
                    dvizhok.dopolnit_poslednuyu_zapis(
                        vdoh_res.get("осело_в", "resonance"), reply)
            except Exception:
                pass
            try:
                if dvizhok is not None:
                    dvizhok.sохранить()
            except Exception:
                pass'''


def main() -> None:
    print("── PATCH_RECAP_V1 ──")

    if not DVIZHOK_PATH.exists():
        _stop(f"{DVIZHOK_PATH} не найден.")
    if not UI_ZHITEL_PATH.exists():
        _stop(f"{UI_ZHITEL_PATH} не найден.")

    dv_text = DVIZHOK_PATH.read_text(encoding="utf-8")
    ui_text = UI_ZHITEL_PATH.read_text(encoding="utf-8")

    if MARKER in dv_text and MARKER in ui_text:
        print("✓ маркер уже стоит в обоих файлах — патч уже применён.")
        return
    if (MARKER in dv_text) != (MARKER in ui_text):
        _stop("половинчатое состояние с прошлого раза — нужна ручная "
              "проверка Шефа, прежде чем катить дальше.")

    new_dv = _apply_one(dv_text, OLD_DVIZHOK, NEW_DVIZHOK,
                        "dvizhok.py: новые методы")

    new_ui = ui_text
    new_ui = _apply_one(new_ui, OLD_TOP, NEW_TOP,
                        "ui_zhitel.py: считать сводку до записи")
    new_ui = _apply_one(new_ui, OLD_SOUL, NEW_SOUL,
                        "ui_zhitel.py: сводка в душу")
    new_ui = _apply_one(new_ui, OLD_SAVE, NEW_SAVE,
                        "ui_zhitel.py: дописать ответ в память")

    print("✓ все якоря найдены и применены в памяти — оба файла готовы")

    _backup(DVIZHOK_PATH, ".bak_recap")
    _backup(UI_ZHITEL_PATH, ".bak_recap")

    DVIZHOK_PATH.write_text(new_dv, encoding="utf-8")
    UI_ZHITEL_PATH.write_text(new_ui, encoding="utf-8")

    print(f"✓ записано: {DVIZHOK_PATH}")
    print(f"✓ записано: {UI_ZHITEL_PATH}")
    print()
    print("Готово. Проверка: поговори с любым жителем, перезагрузи")
    print("страницу, напиши что угодно первым сообщением — она должна")
    print("сама, без просьбы, отреагировать так, будто помнит прошлый")
    print("разговор. MEMORY_REQUEST по-прежнему работает для более")
    print("старого/глубокого, что в сводку из трёх записей не влезло.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
