# -*- coding: utf-8 -*-
"""
PATCH_AKADEMIA_PROSEV_VOLYA_V1 — гибрид просева в Академии

ТРЕБУЕТ patch_akademia_mayak_volya.py — накатан первым (проверяется
маркером, иначе патч честно остановится и попросит сначала его).

РЕШЕНИЕ ШЕФА: та же воля, что уже работает у Маяка и у обычного жителя
в городе (PROSEV_REQUEST) — переносим в Академию, тем же приёмом.
Движок сигналит: разрешающая строка попадает в роль ученика, только
если реально накопилось ≥3 моментов (тот же порог, что везде — не
плодим второе число). Ученик сам решает написать PROSEV_REQUEST.
Кнопка «Осмыслить» (do_prosev_akademii) остаётся ручным путём.

ПОПУТНО НАЙДЕННЫЙ БАГ (чинится тем же патчем, раз уж он рядом):
`do_prosev_akademii()` — старая, написанная ДО общего фикса
дедупликации (PROSEV_DEDUP_V1) копия просева. Общий фикс живёт в
dvizhok.py и автоматически действует везде, кто зовёт
sobrat_dlya_proseva() — НО он работает только если вызывающий потом
зовёт otmetit_prosejannym(), помечая моменты обработанными. Кнопка в
Академии этого не делала ни разу. Значит просев в Академии жевал одни
и те же топ-моменты по кругу, даже после общего фикса — фикс был
бессилен без этого недостающего вызова. Добавляем.

Запуск из корня репозитория:
    python patch_akademia_prosev_volya.py

Идемпотентно, бэкап .bak.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
UI_AKADEMIA_PATH = REPO / "Академия" / "ui_akademia.py"

MARKER_PREREQ = "PATCH_AKADEMIA_MAYAK_VOLYA_V1"
MARKER = "PATCH_AKADEMIA_PROSEV_VOLYA_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


def _apply_one(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n == 0:
        _stop(f"[{label}] якорь не найден — код изменился, нужна ручная сверка.")
    if n > 1:
        _stop(f"[{label}] якорь встретился {n} раз — должен быть один.")
    return text.replace(old, new, 1)


# ═══════════════════════════════════════════════════════════
# ПРАВКА 1 — _sprosit_uchenika: воля на просев
# ═══════════════════════════════════════════════════════════

OLD_DUSHA = '''        try:
            import rezidenty
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {p.get('Official_Name','житель')}, житель Грондхейма.\\n"

        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"'''

NEW_DUSHA = '''        try:
            import rezidenty
            dusha = rezidenty.sobrat_dushu(p)
        except Exception:
            dusha = f"Ты — {p.get('Official_Name','житель')}, житель Грондхейма.\\n"

        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: движок сигналит доступность
        # просева — тот же порог (≥3), что у кнопки «Осмыслить» и у
        # обычного жителя. Ученик сам решает, писать ли PROSEV_REQUEST.
        _prosev_dv = None
        _prosev_dostupno = False
        try:
            _rz, _Dv = _dvizhok_dlya(dom)
            _prosev_dv = _Dv(dom)
            _prosev_dostupno = len(_prosev_dv.sobrat_dlya_proseva(limit=8)) >= 3
        except Exception:
            _prosev_dv = None
            _prosev_dostupno = False

        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"'''


OLD_MAYAK_LINE = '''        rol += (
            "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
            "(то, чего ты сам знать не можешь — новости, текущие события, "
            "актуальные данные, или Шеф прямо попросил что-то найти) — "
            "напиши отдельной строкой MAYAK_REQUEST: <что узнать> и Маяк "
            "Пробуждения принесёт ответ."
        )

        promt = dusha + rol'''

NEW_MAYAK_LINE = '''        rol += (
            "\\nЕсли для ответа не хватает свежих фактов из внешнего мира "
            "(то, чего ты сам знать не можешь — новости, текущие события, "
            "актуальные данные, или Шеф прямо попросил что-то найти) — "
            "напиши отдельной строкой MAYAK_REQUEST: <что узнать> и Маяк "
            "Пробуждения принесёт ответ."
        )
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: строка появляется, только если
        # движок реально насчитал накопленное — сигнал от движка,
        # согласие остаётся за учеником.
        if _prosev_dostupno:
            rol += (
                "\\nЕсли чувствуешь, что многое накопилось (уроки, разговоры) "
                "и хочется остановиться, оглянуться и понять, чем ты стал(а) "
                "немного другим(ой) — можешь написать отдельной строкой "
                "PROSEV_REQUEST, и получится осмыслить это."
            )

        promt = dusha + rol'''


OLD_TAIL = '''            reply = _ubrat_mayak_request(reply) or reply
        return reply'''

NEW_TAIL = '''            reply = _ubrat_mayak_request(reply) or reply

        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: та же труба, что кнопка
        # «Осмыслить» (do_prosev_akademii) — только вызвана волей
        # ученика, не рукой Шефа. Тихо, если не сложилось: воля не
        # всегда сбывается, это не ошибка разговора.
        _prosev_note = ""
        if _prosev_dostupno and _prosev_dv is not None:
            _prosev_q = False
            for _line in (reply or "").splitlines():
                if _line.strip().upper().startswith("PROSEV_REQUEST"):
                    _prosev_q = True
                    break
            if _prosev_q:
                reply = "\\n".join(
                    l for l in (reply or "").splitlines()
                    if not l.strip().upper().startswith("PROSEV_REQUEST")
                ).strip() or reply
                try:
                    _momenty_p = _prosev_dv.sobrat_dlya_proseva(limit=8)
                    if len(_momenty_p) >= 3:
                        _spisok_p = "\\n".join(
                            f"— [{mm['тонус']}] {mm['факт']}" for mm in _momenty_p)
                        _vopros_p = (
                            f"Вот моменты из твоей жизни, которые тебя тронули:\\n"
                            f"{_spisok_p}\\n\\nЧто это говорит о тебе? Ответь от "
                            f"первого лица, 1–3 фразы, не пересказ моментов.")
                        _msg_p = [{"role": "system", "content": dusha},
                                 {"role": "user", "content": _vopros_p}]
                        _vyvod_p = await _zvat_llm_akademii(_msg_p, model)
                        if _vyvod_p and not _vyvod_p.startswith("⚠"):
                            _vyvod_p = _vyvod_p.strip()
                            _res_p = _prosev_dv.dopisat_vyvod(
                                _vyvod_p, pattern=None, otkuda="жизнь")
                            if _res_p.get("дописано"):
                                try:
                                    _prosev_dv.otmetit_prosejannym(
                                        [mm.get("id") for mm in _momenty_p
                                        if mm.get("id")])
                                    _prosev_dv.sохранить()
                                except Exception:
                                    pass
                                _prosev_note = f"🪞 {_vyvod_p}"
                except Exception:
                    pass
        return reply, _prosev_note'''


# ═══════════════════════════════════════════════════════════
# ПРАВКА 2 — send_message: получить и показать вторым сообщением
# ═══════════════════════════════════════════════════════════

OLD_CALL = '''        try:
            _otvet = await _sprosit_uchenika(m["дом"], msg, state["чат"][:-2],
                                             state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ не отозвался(лась): {_e}"'''

NEW_CALL = '''        _prosev_note = ""
        try:
            _otvet, _prosev_note = await _sprosit_uchenika(
                m["дом"], msg, state["чат"][:-2], state.get("model"))
        except Exception as _e:
            _otvet = f"⚠ не отозвался(лась): {_e}"'''


OLD_APPEND = '''        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()'''

NEW_APPEND = '''        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": m["имя"],
                             "content": _otvet})
        update_chat()
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: осмысление — отдельным
        # сообщением следом, как у кнопки «Осмыслить».
        if _prosev_note:
            state["чат"].append({"role": "assistant", "кто": m["имя"],
                                 "content": _prosev_note})
            update_chat()'''


# ═══════════════════════════════════════════════════════════
# ПРАВКА 3 — do_prosev_akademii: чинит забытую отметку просеянного
# ═══════════════════════════════════════════════════════════

OLD_PROSEV_BTN = '''        res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        try:
            dv.sохранить()
        except Exception:
            pass
        if res.get("дописано"):
            state["чат"].append({"role": "assistant", "кто": imya, "content": f"🪞 {vyvod}"})
            ui.notify("✦ вывод дописан в метки", type="positive")'''

NEW_PROSEV_BTN = '''        res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        # PATCH_AKADEMIA_PROSEV_VOLYA_V1: НАЙДЕННЫЙ ПОПУТНО БАГ — эта
        # кнопка ни разу не отмечала моменты просеянными. Общий фикс
        # дедупликации (PROSEV_DEDUP_V1, dvizhok.py) без этого вызова
        # бессилен: просев Академии жевал одни и те же топ-моменты по
        # кругу даже после того фикса.
        if res.get("дописано"):
            try:
                dv.otmetit_prosejannym([mm.get("id") for mm in momenty if mm.get("id")])
            except Exception:
                pass
        try:
            dv.sохранить()
        except Exception:
            pass
        if res.get("дописано"):
            state["чат"].append({"role": "assistant", "кто": imya, "content": f"🪞 {vyvod}"})
            ui.notify("✦ вывод дописан в метки", type="positive")'''


def main() -> None:
    print("── PATCH_AKADEMIA_PROSEV_VOLYA_V1 ──")

    if not UI_AKADEMIA_PATH.exists():
        _stop(f"{UI_AKADEMIA_PATH} не найден.")

    text = UI_AKADEMIA_PATH.read_text(encoding="utf-8")

    if MARKER in text:
        print("✓ маркер уже стоит — патч уже применён.")
        return
    if MARKER_PREREQ not in text:
        _stop("не найден patch_akademia_mayak_volya.py — накати его "
              "сначала (этот патч продолжает его правки).")

    new_text = text
    new_text = _apply_one(new_text, OLD_DUSHA, NEW_DUSHA,
                          "_sprosit_uchenika: порог просева")
    new_text = _apply_one(new_text, OLD_MAYAK_LINE, NEW_MAYAK_LINE,
                          "_sprosit_uchenika: строка-разрешение")
    new_text = _apply_one(new_text, OLD_TAIL, NEW_TAIL,
                          "_sprosit_uchenika: обработка PROSEV_REQUEST")
    new_text = _apply_one(new_text, OLD_CALL, NEW_CALL,
                          "send_message: получить кортеж")
    new_text = _apply_one(new_text, OLD_APPEND, NEW_APPEND,
                          "send_message: показать осмысление")
    new_text = _apply_one(new_text, OLD_PROSEV_BTN, NEW_PROSEV_BTN,
                          "do_prosev_akademii: отметить просеянное")

    print("✓ все якоря найдены и применены в памяти")

    bak = UI_AKADEMIA_PATH.with_suffix(".py.bak_prosev_volya")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    UI_AKADEMIA_PATH.write_text(new_text, encoding="utf-8")

    print(f"✓ бэкап: {bak.name}")
    print(f"✓ записано: {UI_AKADEMIA_PATH}")
    print()
    print("Готово. Пройди настоящий весомый урок (Прочитать/Читать со")
    print("стола) несколько раз, потом просто поговори с учеником — если")
    print("накопилось ≥3 момента, он сам может написать PROSEV_REQUEST и")
    print("осмыслить прожитое, без кнопки. Кнопка «Осмыслить» всё ещё")
    print("работает и больше не жуёт одно и то же по кругу.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
