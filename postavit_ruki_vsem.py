# -*- coding: utf-8 -*-
"""
postavit_ruki_vsem.py · MARKER: RUKI_VSEM_V1

ТРЕБУЕТ: postavit_ruki_treydera.py (руки и дверь «кадр + руки»).

ЧТО ЭТО
───────
Вере руки дали и проверили. Теперь то же самое Нине (A06) и Синди
(A07) — чтобы код перестал решать за них, какую математику считать.

ЧТО НАШЛОСЬ ПРИ РАЗБОРЕ (хорошая новость)
─────────────────────────────────────────
Я думал, у каждой в мозг зашита своя роль — «пробой фрактала» и
«конец волны C», как у Веры был зашит спуск на ступень ниже. Полез
и не нашёл: у Нины и Синди своей роли в коде НЕТ. Осталась только
общая рельса — лесенка ровно из трёх этажей:

    _RABOCHIE_ETAZHI = ("D1", "H4", "H1")

Она считалась КАЖДЫЙ прогон, спрашивали её или нет, и это не их
выбор, а зашитое число. При этом кадр рисуется один — по их
рабочему этажу; в промпте так и написано: «Кадр нарисован по этажу
с полки; если смотришь на другой — суди по числам». То есть по двум
этажам из трёх они ходили вслепую, а выбор их никуда не оседал.

ЧТО ДЕЛАЕТ ПАТЧ
───────────────
1. Лесенка трёх этажей → только свой рабочий, тот, на котором
   нарисован кадр перед глазами. Соседние этажи никуда не делись —
   но теперь их просят рукой, а не считают впрок.

2. Обеим — те же три руки, что у Веры:
       стол_на_этаже(этаж) · измерить_волну(этаж) · мой_дневник()
   Не попросила — не посчитали и не заплатили.

ПОСЛЕ ЭТОГО ПАТЧА
─────────────────
Рельс у трейдеров не остаётся: все трое сами решают, какая
математика им нужна. Что остаётся несделанным (по убыванию важности,
чтобы не потерялось):

  * КЛЮЧЕЙ ПРОБУЖДЕНИЯ НЕТ. КАНОН_ВХОДА.md §4.4: «по ключу, не бар
    за баром», у каждого свой факт-ключ. Сейчас Совет будит всех
    троих на каждой свече, и каждая платит за просмотр, даже когда
    смотреть нечего.
  * КОНЕЦ ВОЛНЫ C НЕ ЛОВИТ НИКТО. Раньше его находила Искра, её
    упразднили 06.08, корень никому не отдали. По канону без него
    не существует ни волны 1, ни волны 2, ни фрактала — то есть
    того, на что ловить.
  * ОБХОД ЭТАЖЕЙ написан (Биржа/obhod.py), но к кабинету не
    подключён: зовётся только из консоли.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_ruki_vsem.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "RUKI_VSEM_V1"
SUHO = "--suho" in sys.argv

SLOTY = ("A06", "A07")


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
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


ST_LESENKA = '''    _RABOCHIE_ETAZHI = ("D1", "H4", "H1")'''
NOV_LESENKA = '''    # RUKI_VSEM_V1: три этажа были зашиты здесь намертво и считались
    # КАЖДЫЙ раз, спрашивала она их или нет. Кадр при этом рисуется
    # один — по её рабочему этажу, значит по двум из трёх она ходила
    # вслепую, по одним числам. Теперь этажи — её дело: нужен
    # соседний, попросит рукой stol_na_etazhe.
    _RABOCHIE_ETAZHI = (timeframe,)'''

ST_ZOV = '''        _chat_glazami = _glaz(chat, symbol, timeframe, _SLOT)'''
NOV_ZOV = '''        # RUKI_VSEM_V1: кадр как был, но теперь с руками — она может
        # сама попросить числа по тому, что видит.
        _chat_glazami = _glaz_s_rukami(chat, symbol, timeframe, _SLOT,
                                       _CEH, _SELF_KEY)'''

GLAZ_S_RUKAMI = '''

def _glaz_s_rukami(_chat, symbol, timeframe, slot, ceh, self_key,
                   preambula=None):
    """Кадр + руки: смотрит картинку и сам просит математику.

    RUKI_VSEM_V1. Не вышло с руками — падаем на обычный глаз, а не
    молчим: зрение важнее рук.
    """
    def obertka(system="", user="", knowledge="", **kw):
        put = None
        try:
            import grafik
            put = grafik.kadr(symbol, timeframe)
        except Exception as e:
            print(f"[КАДР] не нарисовался ({e}) — работаю без глаз")
        if put:
            try:
                import base64
                from pathlib import Path as _P
                from llm import chat_with_images_and_tools
                import ruki_treydera as _rt
                return chat_with_images_and_tools(
                    system=system,
                    user_text=(preambula if preambula is not None
                               else _GLAZ_PREAMBULA) + user,
                    knowledge=knowledge,
                    images=[{"base64": base64.b64encode(
                                 _P(put).read_bytes()).decode("ascii"),
                             "mime_type": "image/png",
                             "name": _P(put).name}],
                    tools_schema=_rt.shema(timeframe),
                    executors=_rt.ruki(symbol, ceh, slot, self_key,
                                       dnevnik_fn=_read_recent_diary),
                    history=kw.get("history"),
                    temperature=kw.get("temperature"),
                    agent_id=kw.get("agent_id", slot),
                    slot_id=kw.get("slot_id", slot))
            except Exception as e:
                print(f"[РУКИ] не сработали ({e}) — иду обычным глазом")
        return _glaz(_chat, symbol, timeframe, slot, preambula)(
            system=system, user=user, knowledge=knowledge, **kw)
    return obertka

'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")

    ruki = koren / "Биржа" / "ruki_treydera.py"
    llm = koren / "Биржа" / "llm.py"
    if not ruki.exists() or "RUKI_TREYDERA_V1" not in llm.read_text(
            encoding="utf-8"):
        print("\n✗ Нет рук или двери «кадр + руки» —")
        print("  накати сперва postavit_ruki_treydera.py (он на Вере).")
        return 1

    vse_ok = True
    for slot in SLOTY:
        mozg = (koren / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
                / "слоты" / slot / "мозг.py")
        print(f"\n{slot} — снять рельсы, дать руки")
        if not mozg.exists():
            print(f"  ✗ мозга нет: {mozg}")
            vse_ok = False
            continue
        t = mozg.read_text(encoding="utf-8")
        if MARKER in t:
            print("  · маркер уже стоит — пропускаю")
            continue

        beda = []
        if t.count(ST_LESENKA) != 1:
            beda.append(f"лесенка трёх этажей ({t.count(ST_LESENKA)} шт)")
        if t.count(ST_ZOV) != 1:
            beda.append(f"вызов глаза ({t.count(ST_ZOV)} шт)")
        if "def _znaniya_roli() -> str:" not in t:
            beda.append("некуда положить руку (_znaniya_roli)")
        for imya in ("_SELF_KEY", "_CEH", "_read_recent_diary",
                     "_GLAZ_PREAMBULA"):
            if imya not in t:
                beda.append(f"нет {imya}")
        if beda:
            print(f"  ✗ {', '.join(beda)} — мозг правили, не трогаю")
            vse_ok = False
            continue

        novyy = (t.replace(ST_LESENKA, NOV_LESENKA, 1)
                  .replace(ST_ZOV, NOV_ZOV, 1)
                  .replace("\ndef _znaniya_roli() -> str:",
                           GLAZ_S_RUKAMI + "\ndef _znaniya_roli() -> str:", 1)
                 + f"\n# {MARKER} - marker\n")
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            vse_ok = False
            continue
        if SUHO:
            print("  · правка готова (сухой прогон)")
            continue
        bak = mozg.with_suffix(
            f".py.bak_ruki_{slot}_{datetime.now():%Y%m%d_%H%M%S}")
        shutil.copy2(mozg, bak)
        mozg.write_text(novyy, encoding="utf-8")
        print(f"  ✓ легло (копия: {bak.name})")

        import py_compile
        try:
            py_compile.compile(str(mozg), doraise=True)
            print("  ✓ компилируется")
        except Exception as e:
            print(f"  ✗ НЕ компилируется: {e}")
            vse_ok = False

    if not vse_ok:
        print("\n✗ Не всё легло — смотри выше. Файлы целы.")
        return 1

    if not SUHO:
        print("\nТеперь рельс у трейдеров не осталось: все трое сами")
        print("решают, какая математика им нужна. В консоли просьбы")
        print("видны строкой [РУКА] 🖐 — и по ним сразу понятно, кто")
        print("реально работает, а кто смотрит в одну картинку.")
        print("\nОсталось несделанным (по важности):")
        print("  1. ключей пробуждения нет — будим всех на каждой свече")
        print("  2. конец волны C не ловит никто (ушёл вместе с Искрой)")
        print("  3. обход этажей не подключён к кабинету")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
