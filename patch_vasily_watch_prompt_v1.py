# -*- coding: utf-8 -*-
# patch_vasily_watch_prompt_v1.py
# ─────────────────────────────────────────────────────────────
# VASILY_NABLYUDENIE_V1 · Патч 1 из 3 — ЯЗЫК ЗАСАДЫ
#
# Даёт станции «Консерватор» (A08) новый глагол: WATCH.
# Сейчас Вася обязан кричать REJECT на хорошую, но ещё не созревшую
# структуру — и это отравляет его же дневник (он читает свою историю
# и видит отказы там, где было терпение). WATCH даёт ему легальное
# право сидеть в засаде: «не отказ — жду волну 1 и откат к опоре».
#
# КАНОН (его же промпт, последняя строка): «входит реже всех. Но когда
# входит — рынок уже сказал "да" дважды». WATCH — это язык для того,
# кем он уже является.
#
# ЖЁСТКОЕ ТРЕБОВАНИЕ (решение Тройки): объявляя WATCH, Вася ОБЯЗАН
# назвать direction + опору (cons_watch_opora) + стоп. Без координат
# алгоритм не сможет механически перевести WATCHING→PENDING — засада
# без цифр это потерянное время.
#
# Идемпотентность: маркер VASILY_WATCH_V1. Уже стоит — выходим чисто.
# Запуск: python patch_vasily_watch_prompt_v1.py   (из корня репо)
# ─────────────────────────────────────────────────────────────
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent
PROMPT = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
          / "слоты" / "A08" / "промпт.md")

MARKER = "VASILY_WATCH_V1"


def main():
    if not PROMPT.exists():
        print(f"✗ не нашёл промпт: {PROMPT}")
        print("  запусти из КОРНЯ репо (там, где GRONDHEIM_CITY/)")
        return 1

    text = PROMPT.read_text(encoding="utf-8")

    if MARKER in text:
        print(f"✓ {MARKER} уже стоит — промпт Васи не трогаю (идемпотентно)")
        return 0

    # ── ЯКОРЬ 1: список действий в блоке «ЕСЛИ ТЫ УЖЕ В РЫНКЕ» ──
    # Вставляем WATCH в перечень доступных действий.
    # ВАЖНО: в реальном файле фраза РАЗОРВАНА переводом строки между
    # "(ENTER)" и "или ждёшь" — якорь учитывает это (\n внутри).
    ankor1 = "входишь (ENTER)\nили ждёшь (WAIT)."
    if ankor1 not in text:
        # запасной вариант — вдруг перенос убрали при редактуре
        ankor1_alt = "входишь (ENTER) или ждёшь (WAIT)."
        if ankor1_alt in text:
            ankor1 = ankor1_alt
        else:
            print("✗ якорь 1 не найден (строка про ENTER/WAIT).")
            print("  Проверь блок «ЕСЛИ ТЫ УЖЕ В РЫНКЕ» — патч НЕ применён.")
            return 1

    zamena1 = (
        "входишь (ENTER), ждёшь (WAIT) или **встаёшь в засаду (WATCH)** — "
        "видишь хорошую структуру, но она ещё не созрела (волна 1 не "
        "подтверждена Моржом или цена не откатила к опоре). WATCH — не "
        "отказ: ты назвал координаты и ждёшь, пока рынок сам их выполнит. "
        "# VASILY_WATCH_V1"
    )
    text = text.replace(ankor1, zamena1, 1)

    # ── ЯКОРЬ 2: JSON-схема сигнала — добавляем поле опоры засады ──
    # cons_action уже перечисляет действия — дописываем WATCH в enum.
    ankor2 = '"cons_action": "ENTER | WAIT | HOLD | MOVE_STOP | ADD | CLOSE"'
    if ankor2 not in text:
        print("✗ якорь 2 не найден (enum cons_action).")
        return 1
    zamena2 = ('"cons_action": "ENTER | WAIT | WATCH | HOLD | MOVE_STOP '
               '| ADD | CLOSE"')
    text = text.replace(ankor2, zamena2, 1)

    # ── ЯКОРЬ 3: добавить поле cons_watch_opora в signal ──
    # Кладём его сразу после cons_add_lot (последнее поле signal).
    ankor3 = '"cons_add_lot": null\n  },'
    if ankor3 not in text:
        print("✗ якорь 3 не найден (cons_add_lot — конец блока signal).")
        return 1
    zamena3 = ('"cons_add_lot": null,\n'
               '    "cons_watch_opora": null\n  },')
    text = text.replace(ankor3, zamena3, 1)

    # ── ЯКОРЬ 4: инструкция по заполнению полей входа ──
    # Дописываем правило WATCH рядом с правилом ENTER.
    ankor4 = ("Если входишь — `cons_direction`, `cons_entry`, `cons_stop` "
              "ты посчитал сам,\n`cons_lot` назови сам. Если нет — они `null`.")
    if ankor4 not in text:
        print("✗ якорь 4 не найден (инструкция по полям входа).")
        return 1
    zamena4 = (
        "Если входишь (ENTER) — `cons_direction`, `cons_entry`, `cons_stop` "
        "ты посчитал сам,\n`cons_lot` назови сам. Если нет — они `null`.\n\n"
        "**Если встаёшь в засаду (WATCH)** — ты ОБЯЗАН назвать координаты, "
        "иначе засада пуста и бессмысленна:\n"
        "- `cons_direction` — сторона будущего входа (LONG/SHORT);\n"
        "- `cons_watch_opora` — цена опоры (фрактал/Зубы), к которой должна "
        "откатить цена, прежде чем ты войдёшь;\n"
        "- `cons_entry` — цена твоей Buy/Sell Stop заявки, которую алгоритм "
        "выставит ПОСЛЕ подтверждённого отскока от опоры;\n"
        "- `cons_stop` — твой стоп для этого входа.\n"
        "Ты ждёшь ДВУХ подтверждений (канон твоей станции — «да» дважды): "
        "(1) Морж подтвердил волну 1, (2) цена коснулась опоры и следующий "
        "бар закрылся обратно в сторону тренда. Только тогда заявка оживёт. "
        "Не назвал опору или стоп — это уже не WATCH, а болтовня; алгоритм "
        "такую засаду отклонит."
    )
    text = text.replace(ankor4, zamena4, 1)

    PROMPT.write_text(text, encoding="utf-8")
    print(f"✓ WATCH вписан в промпт Васи (A08). Маркер {MARKER}.")
    print("  Изменено: список действий, enum cons_action, поле "
          "cons_watch_opora, инструкция засады.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
