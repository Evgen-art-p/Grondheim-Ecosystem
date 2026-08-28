# -*- coding: utf-8 -*-
# MENEDZHER_KARTRIDZHEY_V1
"""
ПАТЧ · Менеджер картриджей — один на весь город.

ЗАЧЕМ
    Страница /ceha была прибита к Бирже в четырёх местах: путь, заголовок,
    «свой стол» через trading_state.json и кнопка торгового кабинета.
    Студия в неё не попадала вовсе. Менеджер нужен один: город растёт,
    заводить по странице на квартал — плодить системы.

ЧТО ДЕЛАЕТ
    1. ГОРОД/rabota.py :: kartridzhi() — добавляет в запись "папка"
       (путь картриджа). Менеджеру нужен путь, чтобы двигать папки;
       вычислять его у себя значит держать знание о раскладке города
       в двух местах.

    2. ГОРОД/ui_ceha.py — пять правок:
       · ceha()      берёт список у kartridzhi(), а не ходит по путям
                     сама. Один сканер на город.
       · razmnozhit() кладёт копию РЯДОМ с оригиналом (в его квартал) —
                     и вообще перестаёт знать, где что лежит.
                     Контору не размножает.
       · ubrat()      контору не вынимает. ЗАКРЫВАЕТ ДЫРУ: до этого
                     патча пустую контору Биржи можно было выдернуть
                     кнопкой вместе со всеми её журналами.
       · page_ceha()  заголовок «ГОРОД · КАРТРИДЖИ», список сгруппирован
                     по кварталам, у конторы вместо кнопок — объяснение.
       · кабинет /torg/ показывается только цехам Биржи (у Студии свой
                     появится вместе с первым цехом).

БИРЖА
    Поведение не меняется ни на шаг. Её цеха как размножались и
    вынимались, так и будут. Пропадает ровно одно — возможность снести
    контору. Кнопка, которой пользоваться нельзя, не функция.

ИДЕМПОТЕНТНОСТЬ
    Маркеры в каждом файле, .bak перед правкой, отказ работать по
    неузнанному тексту. Второй запуск молчит.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "MENEDZHER_KARTRIDZHEY_V1"

# ═════════════════════════════════════════════════════════════
# ПРАВКА 1 — rabota.py: путь картриджа в записи
# ═════════════════════════════════════════════════════════════

R_STAR = '''            out.append({"цех": cd.name, "папка_квартала": kv.name,
                        "вид": "контора" if cd.name == "контора" else "цех",'''

R_NOV = '''            out.append({"цех": cd.name, "папка_квартала": kv.name,
                        "вид": "контора" if cd.name == "контора" else "цех",
                        "папка": str(cd),   # MENEDZHER_KARTRIDZHEY_V1
'''.rstrip("\n")

# ═════════════════════════════════════════════════════════════
# ПРАВКА 2 — ui_ceha.py
# ═════════════════════════════════════════════════════════════

U1_STAR = '''KOREN = Path(__file__).resolve().parent.parent
CEHA = KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха"
CHULAN = KOREN / "_УБОРКА"'''

U1_NOV = '''KOREN = Path(__file__).resolve().parent.parent
CHULAN = KOREN / "_УБОРКА"

# MENEDZHER_KARTRIDZHEY_V1: путей к кварталам страница больше не держит.
# Список приходит от kartridzhi() — единственного сканера города. Куда
# класть копию, знает сам картридж: рядом с собой.'''

U2_STAR = '''def ceha() -> list:
    """Цеха Биржи. Списка не держим — смотрим папки."""
    out = []
    if not CEHA.is_dir():
        return out
    R = _rabota()
    for d in sorted(CEHA.iterdir()):
        mf = d / "manifest.json"
        if not d.is_dir() or not mf.exists():
            continue
        m = _chitat(mf) or {}
        sloty = []
        for s in (m.get("слоты") or []):
            imya = s.get("слот")
            if not imya:
                continue
            kto = ""
            if R is not None:
                try:
                    kto = R.kto_na_slote(d.name, imya)
                except Exception:
                    kto = ""
            sloty.append({
                "слот": imya, "роль": s.get("роль", ""),
                "мозг": (d / "слоты" / imya / "мозг.py").exists(),
                "кто": kto})
        out.append({
            "имя": d.name, "папка": d, "манифест": m,
            "название": m.get("название", d.name),
            "здание": m.get("здание", ""),
            "слоты": sloty,
            "свой_стол": (d / "данные" / "trading_state.json").exists(),
            "от_кого": m.get("_от_кого", ""),
        })
    return out'''

U2_NOV = '''def ceha() -> list:
    """Картриджи ВСЕГО города. MENEDZHER_KARTRIDZHEY_V1.

    Списка не держим и по папкам сами не ходим — спрашиваем kartridzhi(),
    единственный сканер города. Он же говорит вид: контора или цех.
    Контора постоянная, её не размножают и не вынимают.
    """
    out = []
    R = _rabota()
    if R is None:
        return out
    try:
        vse = R.kartridzhi()
    except Exception:
        return out

    for k in vse:
        d = Path(k.get("папка") or "")
        if not d.is_dir():
            continue
        m = _chitat(d / "manifest.json") or {}
        sloty = []
        for s in (m.get("слоты") or []):
            imya = s.get("слот")
            if not imya:
                continue
            kto = ""
            try:
                kto = R.kto_na_slote(k["цех"], imya)
            except Exception:
                kto = ""
            sloty.append({
                "слот": imya, "роль": s.get("роль", ""),
                "мозг": (d / "слоты" / imya / "мозг.py").exists(),
                "кто": kto})
        out.append({
            "имя": k["цех"], "папка": d, "манифест": m,
            "квартал": k.get("папка_квартала", ""),
            "вид": k.get("вид", "цех"),
            "название": m.get("название", k["цех"]),
            "здание": m.get("здание", ""),
            "слоты": sloty,
            "свой_стол": (d / "данные").is_dir(),
            "от_кого": m.get("_от_кого", ""),
        })
    out.sort(key=lambda c: (c["квартал"], c["вид"] != "контора", c["имя"]))
    return out'''

U3_STAR = '''    imya = _chistoe(imya)
    if not imya:
        return False, "у цеха должно быть имя"
    cel = CEHA / imya
    if cel.exists():
        return False, f"цех «{imya}» уже есть"'''

U3_NOV = '''    # MENEDZHER_KARTRIDZHEY_V1: контору не размножают — она одна на
    # квартал по устройству. Копия ложится РЯДОМ с оригиналом, то есть
    # в его же квартал: цех привязан к зданию и судье, копия в чужом
    # квартале была бы сиротой.
    if iz.get("вид") == "контора":
        return False, "контора не размножается — она одна на квартал"
    imya = _chistoe(imya)
    if not imya:
        return False, "у цеха должно быть имя"
    cel = Path(iz["папка"]).parent / imya
    if cel.exists():
        return False, f"цех «{imya}» уже есть"'''

U4_STAR = '''def ubrat(ceh: dict) -> tuple:
    """Вынуть картридж. Занятый не выдёргиваем."""
    zanyaty = [s for s in ceh["слоты"] if s["кто"]]'''

U4_NOV = '''def ubrat(ceh: dict) -> tuple:
    """Вынуть картридж. Занятый не выдёргиваем.

    MENEDZHER_KARTRIDZHEY_V1: контору не вынимаем никогда. Она часть
    квартала, а не сменная деталь: вместе с папкой уехали бы её журналы.
    """
    if ceh.get("вид") == "контора":
        return False, "контора не вынимается — она часть квартала"
    zanyaty = [s for s in ceh["слоты"] if s["кто"]]'''

U5_STAR = '''                'font-size:0.95rem;">БИРЖА · ЦЕХА</div>')'''
U5_NOV = '''                'font-size:0.95rem;">ГОРОД · КАРТРИДЖИ</div>')'''

# список: группировка по кварталам + пометка конторы
U6_STAR = '''            for c in vse:
                zhivyh = sum(1 for s in c["слоты"] if s["мозг"])
                kto = sum(1 for s in c["слоты"] if s["кто"])

                def _vyb(c=c):
                    sost["вybrano"] = c["имя"]
                    risovat_kartu()

                ui.button(f'{c["название"][:24]}  ·  мест {len(c["слоты"])}'
                          f'  ·  людей {kto}', on_click=_vyb).props('''

U6_NOV = '''            kvartal_bylo = None
            for c in vse:
                # MENEDZHER_KARTRIDZHEY_V1: группируем по кварталам —
                # город растёт, плоский список перестал читаться.
                if c.get("квартал") != kvartal_bylo:
                    kvartal_bylo = c.get("квартал")
                    ui.html(f'<div class="c-podpis">{kvartal_bylo}</div>')
                zhivyh = sum(1 for s in c["слоты"] if s["мозг"])
                kto = sum(1 for s in c["слоты"] if s["кто"])
                znak = "◆ " if c.get("вид") == "контора" else ""

                def _vyb(c=c):
                    sost["вybrano"] = (c.get("квартал", ""), c["имя"])
                    risovat_kartu()

                ui.button(f'{znak}{c["название"][:24]}  ·  мест {len(c["слоты"])}'
                          f'  ·  людей {kto}', on_click=_vyb).props('''

U7_STAR = '''    def risovat_kartu():
        refs["karta"].clear()
        imya = sost["вybrano"]
        vse = {c["имя"]: c for c in ceha()}
        with refs["karta"]:
            if imya not in vse:
                ui.label("Выбери цех слева — здесь откроется его карточка."
                         ).style("color:rgba(255,255,255,0.4); "
                                 "font-size:0.82rem;")
                return
            c = vse[imya]'''

U7_NOV = '''    def risovat_kartu():
        refs["karta"].clear()
        klyuch = sost["вybrano"]
        # MENEDZHER_KARTRIDZHEY_V1: ключ теперь пара (квартал, имя) —
        # «контора» есть в каждом квартале, по одному имени не найти.
        vse = {(c.get("квартал", ""), c["имя"]): c for c in ceha()}
        with refs["karta"]:
            if klyuch not in vse:
                ui.label("Выбери картридж слева — здесь откроется карточка."
                         ).style("color:rgba(255,255,255,0.4); "
                                 "font-size:0.82rem;")
                return
            c = vse[klyuch]'''

# карточка: у конторы вместо кнопок — объяснение
U8_STAR = '''            ui.html('<div class="c-podpis">снять копию</div>')
            ui.label("Копия идёт чистой: без данных, журналов и стола. "
                     "Новый цех начинает свою жизнь.").style('''

U8_NOV = '''            # MENEDZHER_KARTRIDZHEY_V1: контора не сменная деталь —
            # ни копий, ни вынимания. Показываем почему, а не прячем.
            if c.get("вид") == "контора":
                ui.html('<div class="c-podpis">картридж?</div>')
                ui.label("Нет. Контора — часть квартала, одна и навсегда: "
                         "вход, выход и общие журналы. Её не размножают "
                         "и не вынимают. Сменные — цеха рядом.").style(
                    "color:rgba(255,255,255,0.45); font-size:0.74rem;")
                return

            ui.html('<div class="c-podpis">снять копию</div>')
            ui.label("Копия идёт чистой: без данных, журналов и стола. "
                     "Новый цех начинает свою жизнь.").style('''

U9_STAR = '''                if ok:
                    sost["вybrano"] = _chistoe(novoe_imya.value or "")'''
U9_NOV = '''                if ok:
                    sost["вybrano"] = (c.get("квартал", ""),
                                       _chistoe(novoe_imya.value or ""))'''

U10_STAR = '''            ui.html('<div class="c-podpis">кабинет</div>')
            ui.button(f'открыть /torg/{c["имя"]}','''

U10_NOV = '''            # MENEDZHER_KARTRIDZHEY_V1: /torg/ — торговый кабинет, роут
            # биржевой. У Студии кабинет свой, появится с первым цехом.
            if c.get("квартал") != "Биржа":
                return
            ui.html('<div class="c-podpis">кабинет</div>')
            ui.button(f'открыть /torg/{c["имя"]}','''

PRAVKI_UI = [
    ("пути квартала убраны", U1_STAR, U1_NOV),
    ("ceha() спрашивает сканер", U2_STAR, U2_NOV),
    ("razmnozhit: копия рядом, контору не копируем", U3_STAR, U3_NOV),
    ("ubrat: контору не вынимаем", U4_STAR, U4_NOV),
    ("заголовок города", U5_STAR, U5_NOV),
    ("список по кварталам", U6_STAR, U6_NOV),
    ("карточка по паре квартал+имя", U7_STAR, U7_NOV),
    ("карточка конторы без кнопок", U8_STAR, U8_NOV),
    ("выбор после копии", U9_STAR, U9_NOV),
    ("кабинет только Бирже", U10_STAR, U10_NOV),
]


# ═════════════════════════════════════════════════════════════

def _teper() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def naiti_koren() -> Path:
    starty = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starty:
        for kand in [start, *start.parents]:
            if (kand / "GRONDHEIM_CITY" / "локации").is_dir() \
                    and (kand / "ГОРОД" / "rabota.py").is_file():
                return kand
    raise SystemExit("Не нашёл корень репо. Запусти из корня "
                     "Grondheim-Ecosystem.")


def patchit(put: Path, pravki: list) -> str:
    """Все замены или ни одной. Половину не оставляем."""
    if not put.exists():
        return f"нет файла {put.name}"
    tekst = put.read_text(encoding="utf-8")
    if MARKER in tekst:
        return "уже пропатчен, не трогал"

    ne_nashlos = [imya for imya, star, _ in pravki if star not in tekst]
    if ne_nashlos:
        return ("НЕ НАШЁЛ куски: " + "; ".join(ne_nashlos) +
                ". Файл уже правили. Ничего не менял.")

    novyy = tekst
    for _, star, nov in pravki:
        if novyy.count(star) != 1:
            return (f"кусок встречается не один раз — не рискую. "
                    f"Ничего не менял.")
        novyy = novyy.replace(star, nov, 1)

    bak = put.with_suffix(put.suffix + f".bak_{_teper()}")
    shutil.copyfile(put, bak)
    put.write_text(novyy, encoding="utf-8")
    return f"пропатчен ({len(pravki)} правок), старый в {bak.name}"


def proverit(koren: Path) -> None:
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(
            "_rabota_probe", koren / "ГОРОД" / "rabota.py")
        if spec is None or spec.loader is None:
            print("  · сканер не завёлся"); return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        vse = mod.kartridzhi()
    except Exception as e:
        print(f"  · сканер споткнулся: {e}")
        print("    ОТКАТ: верни файлы из .bak рядом")
        return
    for k in vse:
        est = "есть" if Path(k.get("папка") or "").is_dir() else "НЕТ"
        print(f"  · {k['папка_квартала']:<10} {k.get('вид','?'):<8} "
              f"{k['цех']:<16} папка: {est}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass
    koren = naiti_koren()
    print(f"Корень: {koren}\n")
    print("rabota.py:  " + patchit(koren / "ГОРОД" / "rabota.py",
                                   [("путь картриджа", R_STAR, R_NOV)]))
    print("ui_ceha.py: " + patchit(koren / "ГОРОД" / "ui_ceha.py", PRAVKI_UI))
    print("\nСпрашиваю город:")
    proverit(koren)
    print("\nГотово. Открой /ceha — там теперь весь город.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
