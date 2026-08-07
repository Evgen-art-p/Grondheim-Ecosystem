# -*- coding: utf-8 -*-
# PROSEV_ZNANII_V1
"""
ПРОСЕВ НАЧИНАЕТ ОСТАВЛЯТЬ ЗНАНИЕ, А НЕ ТОЛЬКО ПЕРЕЖИВАНИЕ.

ЧТО БЫЛО СЛОМАНО (проверено на памяти Нины 06.08)
    Прочитанное со стола ложится СОБЫТИЕМ в слой (для «учёбы» — в
    архив). В разговор же подаются метки и черновики, а не события.
    Мост из событий наверх один — просев. И он спрашивает дословно:

        «Что это говорит о ТЕБЕ? … НЕ пересказ моментов.»

    Пересказ запрещён прямым текстом. Значит из главы про фракталы
    выйти может только «я стала внимательнее прислушиваться к своим
    чувствам» — что и вышло.

    У Нины 14 меток. Тринадцать про себя: холст, страх, охра под
    ногтями. От учёбы ОДНА, и та пустая: «Я изучаю „торговый_хаос"».
    Ни Вильямса, ни пяти баров. Отсюда и то, что вне Академии она
    ничего не знает: ей нечего вспомнить, материал остался на столе
    той сессии.

ЧТО СТАНОВИТСЯ
    Просев делает ДВА захода вместо одного:

      1) как раньше — «что это говорит о тебе» → метка «жизнь»;
      2) НОВОЕ — по учебным моментам отдельно: «что ты УЗНАЛА,
         своими словами, но точно» → вывод «учёба» с ключом темы.

    Заходы не мешают друг другу: переживание остаётся переживанием,
    знание встаёт рядом отдельной строкой.

ПОЧЕМУ ЗНАНИЕ ЛОЖИТСЯ ЧЕРНОВИКОМ, А НЕ СРАЗУ МЕТКОЙ
    Это её собственный пересказ, а он может быть неверен — мы это уже
    видели: из точного определения фрактала она потеряла «по отношению
    к ДВУМ предшествующим и ДВУМ последующим». Черновик в промпт всё
    равно подаётся, значит вне Академии знание с ней. А затвердеет оно
    по нашему же закону — от СУДЬИ: Шеф подтвердит поправкой с «!»
    (popravka_uchitelya), либо она встретит то же в третий раз.

КЛЮЧ ТЕМЫ
    Берётся имя материала из самой записи — «[Академия] «практика_04»: …»
    даёт ключ «знание:практика_04». Перечитала тот же материал — вывод
    ОБНОВИТ прежний, а не заведёт дубль.

ЦЕНА
    Один дополнительный вызов модели на тему, не больше трёх тем за
    просев — иначе после длинного дня чтения набежит десяток.

ЗАПУСК из корня репо:
    python patch_prosev_znanii.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "PROSEV_ZNANII_V1"
TARGET = Path("Академия") / "ui_akademia.py"
BAK = Path("Академия") / "ui_akademia.py.bak_prosev_znanii"

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 1 — сам заход за знанием
# ═══════════════════════════════════════════════════════════
A1_OLD = '''async def _zvat_llm_akademii(messages, model: str = "") -> str:
    """Общий вызов LLM -- тот же способ, что и весь кабинет.
'''

A1_NEW = '''# PROSEV_ZNANII_V1 — второй заход просева: за содержанием
_ZNANIE_MAX_TEM = 3   # больше трёх тем за просев не берём — это деньги


def _uchebnye_temy(momenty: list) -> dict:
    """Разбирает моменты просева на темы учёбы: {имя материала: [моменты]}.

    Учебные записи стол пишет в виде «[Академия] «имя»: выжимка» —
    по этой форме их и узнаём. Всё остальное — личная жизнь, её не
    трогаем, она уходит в первый заход как раньше.
    """
    import re as _re
    temy = {}
    for mm in momenty or []:
        fakt = str(mm.get("факт", ""))
        if not fakt.startswith("[Академия]"):
            continue
        m = _re.search(r"«([^»]+)»", fakt)
        tema = (m.group(1) if m else "материал").strip()
        temy.setdefault(tema, []).append(mm)
    return temy


async def _prosev_znanii(dv, dusha: str, momenty: list, model: str = "") -> list:
    """Спрашивает у ученика, что он УЗНАЛ — отдельно от того, что
    почувствовал. Возвращает список (тема, этаж) для показа Шефу.

    Вопрос нарочно противоположен вопросу первого захода: там «не
    пересказывай», здесь — «перескажи точно». Без этого содержание
    из памяти выпадает целиком (проверено на Нине 06.08).
    """
    itogi = []
    for tema, gruppa in list(_uchebnye_temy(momenty).items())[:_ZNANIE_MAX_TEM]:
        spisok = "\\n".join(f"— {str(g.get('факт',''))}" for g in gruppa)
        vopros = (
            f"Вот что ты читала по теме «{tema}»:\\n{spisok}\\n\\n"
            f"Что ты УЗНАЛА? Своими словами, но ТОЧНО: определения, порядок "
            f"действий, названия и числа сохрани как есть, ничего не округляй "
            f"и не сглаживай. Это не про чувства — про содержание.\\n"
            f"3–6 строк. Чего-то не поняла — так и напиши, это нормальный "
            f"ответ и он полезнее выдуманного."
        )
        try:
            vyvod = await _zvat_llm_akademii(
                [{"role": "system", "content": dusha},
                 {"role": "user", "content": vopros}], model)
        except Exception:
            continue
        if not vyvod or vyvod.startswith("⚠"):
            continue
        try:
            res = dv.dopisat_vyvod(vyvod.strip(),
                                   pattern=f"знание:{tema}", otkuda="учёба")
        except Exception:
            continue
        if res.get("дописано"):
            itogi.append((tema, res.get("этаж", "?")))
    return itogi


async def _zvat_llm_akademii(messages, model: str = "") -> str:
    """Общий вызов LLM -- тот же способ, что и весь кабинет.
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 2 — просев по просьбе самого ученика (PROSEV_REQUEST)
# ═══════════════════════════════════════════════════════════
A2_OLD = '''                            _res_p = _prosev_dv.dopisat_vyvod(
                                _vyvod_p, pattern=None, otkuda="жизнь")
'''

A2_NEW = '''                            _res_p = _prosev_dv.dopisat_vyvod(
                                _vyvod_p, pattern=None, otkuda="жизнь")
                            # PROSEV_ZNANII_V1: второй заход — за
                            # содержанием, отдельной строкой от чувств.
                            try:
                                _zn = await _prosev_znanii(
                                    _prosev_dv, dusha, _momenty_p, model)
                                if _zn:
                                    _prosev_note = (
                                        (_prosev_note + "  ") if _prosev_note else ""
                                    ) + "📚 узнала: " + ", ".join(t for t, _ in _zn)
                            except Exception:
                                pass
'''

# ═══════════════════════════════════════════════════════════
# ЯКОРЬ 3 — просев кнопкой
# ═══════════════════════════════════════════════════════════
A3_OLD = '''        res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
'''

A3_NEW = '''        res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
        # PROSEV_ZNANII_V1: второй заход — за содержанием.
        try:
            _zn = await _prosev_znanii(dv, dusha, momenty, state.get("model"))
            if _zn:
                ui.notify("📚 " + imya + " узнала: "
                          + ", ".join(f"{t} → {e}" for t, e in _zn),
                          type="positive")
        except Exception as _e_zn:
            ui.notify(f"⚠ знание не осело: {_e_zn}", type="warning")
'''

PRAVKI = [
    ("заход просева за знанием", A1_OLD, A1_NEW),
    ("просев по просьбе ученика", A2_OLD, A2_NEW),
    ("просев кнопкой", A3_OLD, A3_NEW),
]


def main() -> int:
    if not TARGET.exists():
        print(f"✗ не нашёл {TARGET} — запускать из КОРНЯ репо")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    novyy = src
    for imya, old, new in PRAVKI:
        n = novyy.count(old)
        if n != 1:
            print(f"✗ якорь «{imya}»: найден {n} раз (нужно 1). "
                  f"Файл изменился — патч НЕ применён, оригинал цел.")
            return 1
        novyy = novyy.replace(old, new, 1)
        print(f"  · {imya} — ок")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✗ ast.parse упал: {e}. Ничего не записал.")
        return 1

    shutil.copy2(TARGET, BAK)
    TARGET.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(BAK, TARGET)
        print(f"✗ py_compile упал: {e}. Откатил из {BAK.name}.")
        return 1

    print(f"\n✓ {MARKER} применён")
    print(f"  бэкап: {BAK}")
    print("\n  Теперь после чтения жми «Осмыслить» — и рядом с выводом")
    print("  о себе ляжет отдельная строка о том, ЧТО она узнала.")
    print("  Проверить: спроси её вне Академии, кто написал книгу.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
