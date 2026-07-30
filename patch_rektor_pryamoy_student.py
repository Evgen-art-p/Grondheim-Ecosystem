# -*- coding: utf-8 -*-
"""
PATCH_REKTOR_PRYAMOY_STUDENT_V1 — Ректор уходит, когда неактивен

НАЙДЕНО (слово Шефа, 30.07): в кабинете Ректора деактивация пузырька
не освобождала разговор для прямого письма студенту — send_message()
при state["активен"]=False просто ОТКАЗЫВАЛ в отправке целиком:

    if not input_ref["element"] or not state["активен"]:
        if not state["активен"]:
            ui.notify("Сначала кликни по пузырьку", type="warning")
        return

Раньше в кабинете уже был путь «услышать кандидата своим голосом» —
do_otvet_kandidata(), кнопка, автоответ на последнюю реплику Ректора.
Но НЕ было пути «Шеф печатает СВОЁ сообщение, и оно идёт студенту
напрямую» — то, чего просит Шеф. Разница важна: не автоответ на то,
что сказал Ректор, а то, что Шеф сам решил написать.

ФИКС: send_message() теперь смотрит на state["активен"] и решает,
КОМУ идёт сообщение:
  • активен  → как раньше, Ректору (_rek.sprosit) — ничего не меняем
  • неактивен → напрямую кандидату/студенту, его собственным голосом
    (rezidenty.sobrat_dushu, та же развязка личность/роль, что везде
    в городе), с отпечатком в его личной памяти (PATCH_PAMYAT_VEZDE_V1,
    тот же приём, что и в do_otvet_kandidata() рядом).

Кнопка do_otvet_kandidata() (автоответ на реплику Ректора) остаётся
как была — это отдельный, не конкурирующий путь.

Запуск из корня репозитория:
    python patch_rektor_pryamoy_student.py

Идемпотентно, бэкап .bak.
`шесть·проверено·до·корня`
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
UI_REKTOR_PATH = REPO / "Академия" / "ui_rektor.py"

MARKER = "PATCH_REKTOR_PRYAMOY_STUDENT_V1"


def _stop(msg: str) -> None:
    print(f"⛔ ОСТАНОВКА: {msg}")
    print("Ничего не записано на диск.")
    sys.exit(1)


OLD_SEND = '''    async def send_message():
        if not input_ref["element"] or not state["активен"]:
            if not state["активен"]:
                ui.notify("Сначала кликни по пузырьку", type="warning")
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()
        state["чат"].append({"role": "assistant", "кто": imya, "content": "…думает"})
        update_chat()
        try:
            otvet = await _rek.sprosit(msg, state["чат"][:-2], kandidat_p, "Шеф",
                                       model=state.get("model"))
        except Exception as e:
            otvet = f"⚠ не отозвался(лась): {e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": imya, "content": otvet})
        update_chat()'''

NEW_SEND = '''    async def send_message():
        if not input_ref["element"]:
            return
        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return

        # PATCH_REKTOR_PRYAMOY_STUDENT_V1: Ректор неактивен — он ушёл,
        # Шеф пишет СТУДЕНТУ напрямую (свои слова, не автоответ кнопкой
        # на реплику Ректора — тот путь остался отдельно, do_otvet_kandidata).
        if not state["активен"]:
            if not kandidat_imya:
                ui.notify("Нет кандидата — писать некому", type="warning")
                return
            input_ref["element"].value = ""
            state["чат"].append({"role": "user", "content": msg})
            update_chat()
            state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                                 "content": "…думает"})
            update_chat()
            try:
                import rezidenty
                dusha = rezidenty.sobrat_dushu(kandidat_p)
            except Exception:
                dusha = (f"Ты — {kandidat_imya}, житель Грондхейма. "
                        f"Говоришь от первого лица.\\n")
            rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
                  "Ректора рядом нет — с тобой говорит Шеф напрямую. "
                  "Говоришь своим голосом, своим характером — честно, "
                  "не как ассистент.\\n")
            _key = os.getenv("OPENROUTER_API_KEY", "")
            if not _key:
                otvet = "⚠ OPENROUTER_API_KEY не задан."
            else:
                messages = [{"role": "system", "content": dusha + rol}]
                for _m in state["чат"][:-2][-10:]:
                    _r = "user" if _m.get("role") == "user" else "assistant"
                    messages.append({"role": _r, "content": _m.get("content", "")})
                messages.append({"role": "user", "content": msg})
                import httpx
                # PATCH_PROXY_VEZDE_V1: та же настройка, что и в остальном городе.
                _proxy = os.getenv("PROXY_URL", "") or None
                headers = {"Authorization": f"Bearer {_key}",
                          "Content-Type": "application/json"}
                payload = {"model": state.get("model") or DEFAULT_MODEL,
                          "messages": messages}
                try:
                    async with httpx.AsyncClient(timeout=120, proxy=_proxy) as client:
                        r = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers, json=payload)
                        r.raise_for_status()
                        otvet = r.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    otvet = f"⚠ {kandidat_imya} не отозвалась: {e}"
            # PATCH_PAMYAT_VEZDE_V1 (тот же приём, что в do_otvet_kandidata
            # рядом): отпечаток в её личной памяти.
            if kandidat_dom and not otvet.startswith("⚠"):
                try:
                    from dvizhok import Dvizhok as _Dvizhok_pm2
                    _dv_pm2 = _Dvizhok_pm2(kandidat_dom)
                    _vdoh_pm2 = _dv_pm2.vdoh(kontekst="общение", sila=0.5,
                                             svezhest=1.0, tonus="ровно")
                    _dv_pm2.vydoh_stol(
                        fakt=f"[Академия] Шеф спросил: {msg}\\nЯ ответила: {otvet}",
                        vdoh_result=_vdoh_pm2)
                    _dv_pm2.sохранить()
                except Exception:
                    pass
            state["чат"].pop()
            state["чат"].append({"role": "assistant", "кто": kandidat_imya,
                                 "content": otvet})
            update_chat()
            return

        input_ref["element"].value = ""
        state["чат"].append({"role": "user", "content": msg})
        update_chat()
        state["чат"].append({"role": "assistant", "кто": imya, "content": "…думает"})
        update_chat()
        try:
            otvet = await _rek.sprosit(msg, state["чат"][:-2], kandidat_p, "Шеф",
                                       model=state.get("model"))
        except Exception as e:
            otvet = f"⚠ не отозвался(лась): {e}"
        state["чат"].pop()
        state["чат"].append({"role": "assistant", "кто": imya, "content": otvet})
        update_chat()'''


def main() -> None:
    print("── PATCH_REKTOR_PRYAMOY_STUDENT_V1 ──")

    if not UI_REKTOR_PATH.exists():
        _stop(f"{UI_REKTOR_PATH} не найден.")

    text = UI_REKTOR_PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("✓ маркер уже стоит — патч уже применён.")
        return

    n = text.count(OLD_SEND)
    if n == 0:
        _stop("якорь send_message() не найден — код изменился с 30.07, "
              "нужна ручная сверка.")
    if n > 1:
        _stop(f"якорь встретился {n} раз — должен быть один.")

    new_text = text.replace(OLD_SEND, NEW_SEND, 1)

    bak = UI_REKTOR_PATH.with_suffix(".py.bak_pryamoy_student")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
    UI_REKTOR_PATH.write_text(new_text, encoding="utf-8")

    print(f"✓ бэкап: {bak.name}")
    print(f"✓ записано: {UI_REKTOR_PATH}")
    print()
    print("Готово. Кликни пузырёк Ректора, чтобы ПОГАСИТЬ его (второй")
    print("клик по уже активному) — теперь можно написать студенту")
    print("напрямую, ответит он сам, своим голосом. Кнопка автоответа")
    print("кандидата на реплику Ректора работает как раньше.")
    print("шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
