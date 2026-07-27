# PATCH_REKTOR_DISTSIPLINY_V1
"""
PATCH_REKTOR_DISTSIPLINY_V1 -- модель Дисциплин (АКАДЕМИЯ_ГРОНДХЕЙМА.md
§12, слово Шефа 27.07): курс (одна строка) заменяется на НАПРАВЛЕНИЯ
(Финансы/Искусство/Общие дисциплины) -> внутри каждого ДИСЦИПЛИНЫ ->
внутри каждой ТЕОРИЯ и ПРАКТИКА, оцениваются раздельно. Студент учится
по нескольким дисциплинам одновременно -- реестр хранит список.

АДДИТИВНО: старые функции (postavit_otsenku, provesti_ekzamen без
привязки к дисциплине) не трогаются и не удаляются -- работающее не
ломаем без причины. zachislit() дополняется полем "дисциплины": []
рядом с "курс" (курс остаётся для обратной совместимости с тем, что
уже читает ui_akademia.py).

Требует: Академия/rektor.py в исходном виде (26.07). Этот патч трогает
ТОЛЬКО Академия/rektor.py -- диск-скелет (папки направлений,
ученики.json) кладётся отдельно (см. приложенные файлы).

Идемпотентно: если маркер PATCH_REKTOR_DISTSIPLINY_V1 уже стоит в
файле -- патч молча выходит, повторно не наложится. Бэкап .bak
делается один раз, при первом применении.

Запуск из корня репо:  python patch_rektor_distsipliny.py
`шесть·проверено·до·корня`
"""
from pathlib import Path
import sys

TARGET = Path('Академия/rektor.py')
MARKER = 'PATCH_REKTOR_DISTSIPLINY_V1'

OLD_KONSTANTY = '''_DATA = _REPO / "GRONDHEIM_CITY" / "Академия"
_UCHENIKI = _DATA / "ученики.json"
MEST = 10   # то же число мест, что у кабинета Академии'''

NOVYE_KONSTANTY = '''_DATA = _REPO / "GRONDHEIM_CITY" / "Академия"
_UCHENIKI = _DATA / "ученики.json"
MEST = 10   # то же число мест, что у кабинета Академии

# PATCH_REKTOR_DISTSIPLINY_V1: направления вместо одного "курса".
# Список открыт -- четвёртое направление родится той же папкой на
# диске, код его не хардкодит нигде, кроме этого стартового списка
# (три полки, которые Шеф назвал 27.07).
_DISTSIPLINY_DIR = _DATA / "дисциплины"
NAPRAVLENIA = ["финансы", "искусство", "общие_дисциплины"]
CHASTI_DISTSIPLINY = ("теория", "практика")'''

NOVYE_FUNKTSII = '''def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            _sokhranit_zapisi(zapisi)
            _prof = professiya or "специалист(ка)"
            _zapomnit_uchebu(
                imya, f"Получил(а) диплом Академии по специальности «{_prof}»",
                f"Я — дипломированный(ая) {_prof}, умею применять эти "
                f"знания в работе, не только помнить их как урок",
                pattern=None, sila=0.9)
            return True, f"диплом «{professiya or 'без указания профессии'}» выдан {imya}"
    return False, f"{imya} не студент(ка) — диплом выдавать некому"


# ═══════════════════════════════════════════════════════════
# ДИСЦИПЛИНЫ (PATCH_REKTOR_DISTSIPLINY_V1) -- направления, теория и
# практика раздельно, несколько дисциплин разом. АКАДЕМИЯ_ГРОНДХЕЙМА.md
# §12: дисциплина -- книга на полке направления, студент не выбирает
# одну и ждёт диплома, а записывается на сколько угодно сразу.
# ═══════════════════════════════════════════════════════════

def list_napravlenia() -> list:
    """Три полки, заведённые Шефом 27.07. Список открыт на будущее --
    новое направление появится той же папкой, здесь просто стартовые."""
    return list(NAPRAVLENIA)


def list_distsipliny(napravlenie: str = "") -> list:
    """Дисциплины на диске. Пусто направление -- по всем сразу. Честно:
    ни одной дисциплины ещё нет, пока вернёт пустой список -- не
    выдумываем то, чего на диске нет."""
    out = []
    if not _DISTSIPLINY_DIR.exists():
        return out
    papki = ([_DISTSIPLINY_DIR / napravlenie] if napravlenie
             else [_DISTSIPLINY_DIR / n for n in NAPRAVLENIA])
    for napr_dir in papki:
        if not napr_dir.exists():
            continue
        for d in sorted(napr_dir.iterdir()):
            if not d.is_dir():
                continue
            man = _read_json(d / "manifest.json")
            if man:
                out.append(man)
    return out


def _najti_mesto(imya: str):
    """Индекс места студента в списке или None. Внутренний помощник --
    дисциплины живут внутри записи места, не отдельным реестром."""
    zapisi = _zapisi()
    for i, z in enumerate(zapisi):
        if z.get("житель") == imya:
            return zapisi, i
    return zapisi, None


def zapisat_na_distsiplinu(imya: str, distsiplina_id: str,
                          napravlenie: str) -> tuple:
    """Записывает студента на дисциплину. НЕ блокирует, если он уже
    учит другие -- несколько дисциплин разом это норма (§12), не
    исключение. Повторная запись на ТУ ЖЕ дисциплину -- честный отказ,
    не дублируем строку."""
    zapisi, idx = _najti_mesto(imya)
    if idx is None:
        return False, f"{imya} не студент(ка) — сперва зачислить в Академию"
    z = zapisi[idx]
    distsipliny = z.setdefault("дисциплины", [])
    if any(d.get("дисциплина") == distsiplina_id for d in distsipliny):
        return False, f"{imya} уже записан(а) на «{distsiplina_id}»"
    distsipliny.append({
        "дисциплина": distsiplina_id,
        "направление": napravlenie,
        "записан": _now(),
        "теория": {"оценки": []},
        "практика": {"оценки": []},
    })
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Начал(а) изучать «{distsiplina_id}» ({napravlenie})",
        f"Я изучаю «{distsiplina_id}»", pattern=None, sila=0.4)
    return True, f"{imya} записан(а) на «{distsiplina_id}» ({napravlenie})"


def postavit_otsenku_distsipliny(imya: str, distsiplina_id: str,
                                 chast: str, otsenka: str) -> tuple:
    """Оценка ЗА ЧАСТЬ дисциплины -- теория и практика раздельно
    (§12), не смешиваются в один список, как было у postavit_otsenku()
    для курса целиком. Каждая часть -- свой ключ в личной памяти
    студента (dopisat_vyvod), свой порог 3, друг другу не мешают."""
    if chast not in CHASTI_DISTSIPLINY:
        return False, f"часть должна быть 'теория' или 'практика', не «{chast}»"
    zapisi, idx = _najti_mesto(imya)
    if idx is None:
        return False, f"{imya} не студент(ка) — оценку ставить некуда"
    z = zapisi[idx]
    distsipliny = z.get("дисциплины", [])
    d = next((d for d in distsipliny if d.get("дисциплина") == distsiplina_id), None)
    if d is None:
        return False, f"{imya} не записан(а) на «{distsiplina_id}»"
    d.setdefault(chast, {"оценки": []}).setdefault("оценки", []).append({
        "оценка": otsenka, "когда": _now()})
    _sokhranit_zapisi(zapisi)
    _zapomnit_uchebu(
        imya, f"Оценка по «{distsiplina_id}» ({chast}): {otsenka}",
        f"По «{distsiplina_id}» ({chast}): {otsenka}",
        pattern=f"{distsiplina_id}:{chast}", sila=0.5)
    return True, f"оценка «{otsenka}» ({chast}, «{distsiplina_id}») выставлена {imya}"


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста (собеседование). Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════'''

ZACHISLIT_STAROE = '''    zapisi = _zapisi()
    zapisi.append({
        "место": mesto, "житель": imya, "курс": kurs,
        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
    })'''

ZACHISLIT_NOVOE = '''    zapisi = _zapisi()
    zapisi.append({
        "место": mesto, "житель": imya, "курс": kurs,
        # PATCH_REKTOR_DISTSIPLINY_V1: "курс" оставлен для обратной
        # совместимости (ui_akademia.py его читает), но новый багаж --
        # список дисциплин, не одна строка. Несколько дисциплин разом.
        "дисциплины": [],
        "статус": "студент", "зачислен": _now(),
        "оценки": [], "экзамены": [], "диплом": None,
    })'''

REPLACEMENTS = [
    (OLD_KONSTANTY, NOVYE_KONSTANTY),
    (
        '''def vydat_diplom(imya: str, professiya: str = "") -> tuple:
    zapisi = _zapisi()
    for z in zapisi:
        if z.get("житель") == imya:
            z["диплом"] = {"профессия": professiya, "выдан": _now()}
            z["статус"] = "выпускник"
            _sokhranit_zapisi(zapisi)
            _prof = professiya or "специалист(ка)"
            _zapomnit_uchebu(
                imya, f"Получил(а) диплом Академии по специальности «{_prof}»",
                f"Я — дипломированный(ая) {_prof}, умею применять эти "
                f"знания в работе, не только помнить их как урок",
                pattern=None, sila=0.9)
            return True, f"диплом «{professiya or 'без указания профессии'}» выдан {imya}"
    return False, f"{imya} не студент(ка) — диплом выдавать некому"


# ═══════════════════════════════════════════════════════════
# РОЛЬ — инструкция поста (собеседование). Личности здесь нет ни строчки.
# ═══════════════════════════════════════════════════════════''',
        NOVYE_FUNKTSII,
    ),
    (ZACHISLIT_STAROE, ZACHISLIT_NOVOE),
]

REPLACE_ALL = [
]


def main():
    if not TARGET.exists():
        print(f"⚠ не найден {TARGET} — запускай из корня репо")
        sys.exit(1)
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"✓ {MARKER} уже стоит в {TARGET} — патч не нужен")
        return
    for old, new in REPLACEMENTS:
        if old not in text:
            print("⚠ не нашёл кусок для замены — файл изменился с момента патча:")
            print(old[:200])
            sys.exit(1)
        if text.count(old) > 1:
            print("⚠ кусок встречается больше одного раза — небезопасно патчить:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new, 1)
    for old, new in REPLACE_ALL:
        if old not in text:
            print("⚠ не нашёл кусок для повсеместной замены — файл изменился:")
            print(old[:200])
            sys.exit(1)
        text = text.replace(old, new)
    bak = TARGET.with_suffix(TARGET.suffix + ".bak_distsipliny")
    if not bak.exists():
        bak.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(text, encoding="utf-8")
    print(f"✓ пропатчено: {TARGET} (бэкап: {bak})")


if __name__ == "__main__":
    main()
