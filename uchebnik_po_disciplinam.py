# -*- coding: utf-8 -*-
"""
uchebnik_po_disciplinam.py · MARKER: UCHEBNIK_DISCIPLINY_V1

ЗАЧЕМ ПЕРЕДЕЛЫВАЕМ СРАЗУ
───────────────────────
Слово Шефа: «только эти рисунки, в будущем, если материал добавится?
Хорошо было бы по темам. Давай сразу переделаем, а то потом больше
вдруг придётся.»

Верно: вчерашняя рука была привязана к ОДНОЙ книге — путь до
«Торгового Хаоса» зашит в код, опись одна. Добавишь Котина, вторую
книгу Вильямса, свои разборы — рука их не увидит, пока кто-то не
полезет в файл. Это ровно тот «список за других», от которого город
уходит везде: Закон Картриджа велит СКАНИРОВАТЬ, а не помнить имена.

ЧТО ЕСТЬ СЕЙЧАС НА ДИСКЕ
────────────────────────
    дисциплины/финансы/торговый_хаос/уроки/картинки/  ← 84 рисунка + опись
    дисциплины/общие_дисциплины/беседы_о_смыслах/
    дисциплины/искусство/

То есть дерево дисциплин уже живёт, просто рука смотрела в одну ветку.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Учебник СКАНИРУЕТ всё дерево дисциплин и собирает картинки
   отовсюду, где они есть. Появится новая книга — положил папку с
   картинками, и она в тот же миг доступна. Правок в коде НЕ НУЖНО.

2. ТЕМА = ДИСЦИПЛИНА, а не ярлык на картинке. Раздел и предмет
   берутся из пути:

       финансы / торговый_хаос      искусство / …
       общие_дисциплины / беседы_о_смыслах

   Размечать 84 рисунка руками не надо, и новые размечать тоже не
   придётся — тема появляется сама, из того, куда положили.

3. Трейдер может спросить и широко, и узко:

       uchebnik("приседающий бар")            — ищет во всех дисциплинах
       uchebnik("восприятие", тема="психология") — только в своей ветке
       uchebnik_temy()                        — что вообще есть в Академии

4. Опись читается, если она есть, — там авторские подписи, они лучше
   любых наших ярлыков. Описи нет — картинки всё равно видны, просто
   ищутся по имени файла и папке. Новую книгу можно положить без
   описи и пользоваться сразу.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py uchebnik_po_disciplinam.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "UCHEBNIK_DISCIPLINY_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ruki_treydera.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


UCHEBNIK_PY = '''# -*- coding: utf-8 -*-
# UCHEBNIK_DISCIPLINY_V1
"""
УЧЕБНИК — картинки Академии, по всем дисциплинам.

СЛОВА ШЕФА
    «Есть же в Академии архив с картинками, накидать по темам — и
    пусть по запросу получит в работе. Она там с глазами.»
    «Только эти рисунки? В будущем, если материал добавится?»

ЗАКОН ЭТОГО ФАЙЛА
    СКАНИРУЕМ, А НЕ ПОМНИМ. Списка книг здесь нет и не будет: положил
    папку с картинками в дисциплины — она доступна в тот же миг, без
    единой правки. Тот же Закон Картриджа, что у цехов и истоков.

    ТЕМА — ЭТО ДИСЦИПЛИНА, из пути: раздел/предмет. Ярлыки на каждую
    картинку не вешаем: их пришлось бы проставлять руками сейчас и
    для каждой новой книги потом.

    Ищем по АВТОРСКИМ подписям из описи, если она есть. Своих
    толкований не добавляем: показали рисунок — дальше дело смотрящего.
"""
from __future__ import annotations

import re
from pathlib import Path

_KOREN = Path(__file__).resolve().parent.parent
_DISCIPLINY = _KOREN / "GRONDHEIM_CITY" / "Академия" / "дисциплины"
_RASSHIRENIYA = (".jpeg", ".jpg", ".png", ".gif", ".webp")


def _opis_ryadom(papka: Path) -> dict:
    """{имя файла: (глава, подпись)} из ОПИСЬ.md, если она есть.

    Опись необязательна: без неё картинки всё равно видны, просто
    ищутся по имени файла и папке. Новую книгу можно положить без
    описи и пользоваться сразу.
    """
    out, glava = {}, ""
    for imya in ("ОПИСЬ.md", "опись.md", "ОПИСЬ.txt"):
        f = papka / imya
        if not f.exists():
            continue
        for s in f.read_text(encoding="utf-8", errors="replace").splitlines():
            s = s.strip()
            if s.startswith("## "):
                glava = s[3:].strip()
                continue
            m = re.match(r"^-\\s+`([^`]+)`\\s*(?:\\([^)]*\\))?\\s*—?\\s*(.*)$", s)
            if m:
                out[m.group(1).strip()] = (glava, m.group(2).strip())
        break
    return out


def _tema_iz_puti(p: Path) -> tuple:
    """(раздел, предмет) — из того, КУДА положили. Например
    финансы/торговый_хаос или общие_дисциплины/беседы_о_смыслах."""
    try:
        chasti = p.relative_to(_DISCIPLINY).parts
    except Exception:
        return ("", "")
    razdel = chasti[0] if len(chasti) > 0 else ""
    predmet = chasti[1] if len(chasti) > 1 else ""
    return (razdel, predmet)


def vse_kartinki() -> list:
    """[(путь, раздел, предмет, глава, подпись)] — скан всего дерева."""
    if not _DISCIPLINY.exists():
        return []
    opisi: dict = {}
    out = []
    for p in sorted(_DISCIPLINY.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in _RASSHIRENIYA:
            continue
        # опись ищем в папке картинок и на две ступени выше
        podpis, glava = "", ""
        for kandidat in (p.parent, p.parent.parent, p.parent.parent.parent):
            if kandidat in opisi:
                o = opisi[kandidat]
            else:
                o = _opis_ryadom(kandidat)
                opisi[kandidat] = o
            if p.name in o:
                glava, podpis = o[p.name]
                break
        razdel, predmet = _tema_iz_puti(p)
        out.append((p, razdel, predmet, glava, podpis))
    return out


def temy() -> str:
    """Что вообще есть в Академии — по дисциплинам."""
    vse = vse_kartinki()
    if not vse:
        return "картинок в дисциплинах пока нет"
    po_temam: dict = {}
    for _p, razdel, predmet, _g, _po in vse:
        klyuch = f"{razdel} / {predmet}" if predmet else (razdel or "прочее")
        po_temam[klyuch] = po_temam.get(klyuch, 0) + 1
    return "\\n".join(f"  · {t} — {n} рисунк(ов)"
                      for t, n in sorted(po_temam.items()))


def nayti(o_chyom: str, skolko: int = 1, tema: str = "") -> list:
    """[(путь, тема, глава, подпись)] по словам запроса.

    tema — сузить до дисциплины («психология», «финансы», имя книги).
    Пусто — ищем везде.
    """
    zapros = (o_chyom or "").strip().lower()
    tema = (tema or "").strip().lower()
    slova = [w for w in re.split(r"[^\\wа-яё]+", zapros) if len(w) > 3]
    if not slova and zapros:
        slova = [zapros]

    ocenki = []
    for p, razdel, predmet, glava, podpis in vse_kartinki():
        if tema and tema not in f"{razdel} {predmet}".lower():
            continue
        if not slova:
            ocenki.append((0, p, razdel, predmet, glava, podpis))
            continue
        seno = f"{podpis} {glava} {p.name} {razdel} {predmet}".lower()
        ochki = sum(1 for w in slova if w in seno)
        # авторская подпись весит больше имени файла
        ochki += sum(1 for w in slova if w in podpis.lower())
        if ochki:
            ocenki.append((ochki, p, razdel, predmet, glava, podpis))

    ocenki.sort(key=lambda x: -x[0])
    out = []
    for _o, p, razdel, predmet, glava, podpis in ocenki[:skolko]:
        t = f"{razdel} / {predmet}" if predmet else (razdel or "")
        out.append((p, t, glava, podpis))
    return out


# UCHEBNIK_DISCIPLINY_V1 - marker
'''


ST_SHEMA = '''            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ картинку из книги «Торговый Хаос», по которой тебя "
                "учили: «приседающий бар», «фрактал», «волны AO», «окно "
                "объёма». Ты УВИДИШЬ сам рисунок и авторскую подпись к нему. "
                "Полезно, когда сомневаешься, как выглядит паттерн в "
                "учебнике — сравни с тем, что на графике сейчас."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string",
                          "description": "тема словами, например «приседающий бар»"}},
                "required": ["о_чём"]}}},'''

NOV_SHEMA = '''            "name": "uchebnik",
            "description": (
                "ПОКАЗАТЬ картинку из того, по чему тебя учили в Академии: "
                "«приседающий бар», «фрактал», «волны AO», «окно объёма». "
                "Ты УВИДИШЬ сам рисунок и авторскую подпись к нему. Полезно, "
                "когда сомневаешься, как выглядит паттерн в учебнике — "
                "сравни с тем, что на графике сейчас. Можно сузить до "
                "дисциплины: финансы, психология, искусство."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string",
                          "description": "тема словами, например «приседающий бар»"},
                "дисциплина": {"type": "string",
                               "description": "необязательно: сузить поиск"}},
                "required": ["о_чём"]}}},
        {"type": "function", "function": {
            "name": "chemu_uchili",
            "description": (
                "Какие дисциплины и сколько рисунков есть в Академии. "
                "Смотри, если не знаешь, о чём вообще можно спросить."),
            "parameters": {"type": "object", "properties": {},
                           "required": []}}},'''

ST_RUKA = '''    def _uchebnik(args: dict) -> str:
        """UCHEBNIK_V_RUKE_V1: показать рисунок из книги."""
        o = str(args.get("о_чём", "")).strip()
        try:
            import uchebnik as _u
            nashlos = _u.nayti(o, skolko=1)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            try:
                import uchebnik as _u
                spisok = _u.temy()
            except Exception:
                spisok = ""
            return (f"по «{o}» в учебнике рисунка не нашёл. Что есть:\\n"
                    f"{spisok}")
        p, glava, podpis = nashlos[0]
        return (f"[КАДР: {p}] учебник · {glava} · {p.name}\\n"
                f"подпись автора: {podpis}")'''

NOV_RUKA = '''    def _uchebnik(args: dict) -> str:
        """UCHEBNIK_DISCIPLINY_V1: показать рисунок из Академии.

        Ищет по ВСЕМ дисциплинам: списка книг в коде нет, сканируется
        дерево. Появится новая книга — будет видна сразу.
        """
        o = str(args.get("о_чём", "")).strip()
        tema = str(args.get("дисциплина", "")).strip()
        try:
            import uchebnik as _u
            nashlos = _u.nayti(o, skolko=1, tema=tema)
        except Exception as e:
            return f"учебник не открылся: {e}"
        if not nashlos:
            try:
                import uchebnik as _u
                spisok = _u.temy()
            except Exception:
                spisok = ""
            gde = f" в дисциплине «{tema}»" if tema else ""
            return (f"по «{o}»{gde} рисунка не нашёл. Что есть в Академии:\\n"
                    f"{spisok}")
        p, t, glava, podpis = nashlos[0]
        hvost = f" · {glava}" if glava else ""
        podp = f"\\nподпись автора: {podpis}" if podpis else ""
        return f"[КАДР: {p}] учебник · {t}{hvost} · {p.name}{podp}"

    def _chemu_uchili(args: dict) -> str:
        try:
            import uchebnik as _u
            return "=== ЧЕМУ УЧАТ В АКАДЕМИИ ===\\n" + _u.temy()
        except Exception as e:
            return f"дисциплины не прочитались: {e}"'''

ST_KLYUCH = '''            "uchebnik": _uchebnik,          # UCHEBNIK_V_RUKE_V1'''
NOV_KLYUCH = '''            "uchebnik": _uchebnik,          # UCHEBNIK_DISCIPLINY_V1
            "chemu_uchili": _chemu_uchili,'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    uchebnik = koren / "Биржа" / "uchebnik.py"
    ruki = koren / "Биржа" / "ruki_treydera.py"

    if not uchebnik.exists():
        print("✗ Нет Биржа/uchebnik.py — накати сперва "
              "postavit_ruku_uchebnika.py")
        return 1

    print("\n1. Учебник сканирует ВСЕ дисциплины")
    if MARKER in uchebnik.read_text(encoding="utf-8"):
        print("  · уже переделан")
    else:
        try:
            ast.parse(UCHEBNIK_PY)
        except SyntaxError as e:
            print(f"  ✗ мой же файл не разбирается: {e}")
            return 1
        if not SUHO:
            shutil.copy2(uchebnik, uchebnik.with_suffix(
                f".py.bak_discipliny_{datetime.now():%Y%m%d_%H%M%S}"))
            uchebnik.write_text(UCHEBNIK_PY, encoding="utf-8")
        print("  ✓ теперь тема = дисциплина, книги не перечисляются")

    print("\n2. Руки: сузить до дисциплины и спросить, чему учили")
    t = ruki.read_text(encoding="utf-8")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        pary = [("схема", ST_SHEMA, NOV_SHEMA), ("рука", ST_RUKA, NOV_RUKA),
                ("ключ", ST_KLYUCH, NOV_KLYUCH)]
        beda = [imya for imya, st, _ in pary if t.count(st) != 1]
        if beda:
            print(f"  ✗ якоря не найдены: {', '.join(beda)}")
            return 1
        novyy = t
        for _, st, nov in pary:
            novyy = novyy.replace(st, nov, 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if SUHO:
            print("  · правка готова (сухой прогон)")
        else:
            shutil.copy2(ruki, ruki.with_suffix(
                f".py.bak_discipliny_{datetime.now():%Y%m%d_%H%M%S}"))
            ruki.write_text(novyy, encoding="utf-8")
            print("  ✓ встали")

    if not SUHO:
        import py_compile
        for f in (uchebnik, ruki):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nТеперь новая книга подключается ТАК:")
        print("  положил папку с картинками в дисциплины/<раздел>/<книга>/")
        print("  — и она доступна сразу. Кода трогать не надо.")
        print("  Есть рядом ОПИСЬ.md с подписями — будет искать по ним;")
        print("  нет описи — по именам файлов и папке.")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
