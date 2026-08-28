# -*- coding: utf-8 -*-
# KLIENTY_STUDII_V1
"""
ПАТЧ · Клиенты и клиентская память Студии.

Второй камень, первая половина. Под кнопками появляется механика:
    панель КЛИЕНТ   выбор, создание, бейдж
    🧠              память клиента: конспекты сессий и выводы мест
    📁 RUNS         прогоны выбранного клиента, а не все подряд

ОТКУДА ВЗЯТО
    studio/workshop/clients.py (106 строк) и memory.py (159 строк) —
    по смыслу один в один: info.json и memory.json у клиента,
    _sandbox по умолчанию, конспекты сессий (последние три),
    выводы по местам с правкой и удалением, полная очистка.

ЧТО ИЗМЕНЕНО ПРОТИВ СТАРОЙ
    · agent_id → слот. Вывод принадлежит МЕСТУ, а не жителю: сменится
      житель — накопленное по клиенту останется при месте. Это тот же
      закон, по которому журналы живут в роли.
    · пути русские, при Студии: Студия/клиенты/{slug}/
    · раны Студии: Студия/прогоны/{дата}_{клиент}_{цех}/

ГДЕ ЛЕЖИТ КОД
    GRONDHEIM_CITY/Студия/klienty.py — код Студии живёт при Студии,
    как код Биржи при Бирже. main.py добавляет папку в sys.path.
    Копия Студии на остров уедет вместе со своим кодом.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KLIENTY_STUDII_V1"

KOD = '''# -*- coding: utf-8 -*-
# KLIENTY_STUDII_V1
"""
КЛИЕНТЫ СТУДИИ и их память.

    Студия/клиенты/{slug}/info.json     карточка: имя, ниша, описание
    Студия/клиенты/{slug}/память.json   конспекты сессий + выводы мест
    Студия/прогоны/{дата}_{клиент}_{цех}/   файлы прогона

Песочница «_проба» — работа без клиента. В неё ничего не копится:
память ведём только настоящему заказчику.

ВЫВОД ПРИНАДЛЕЖИТ МЕСТУ, НЕ ЖИТЕЛЮ. Сменится житель на A03 — то, что
накоплено по клиенту, останется при месте. Тот же закон, по которому
журналы живут в роли.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

STUDIYA = Path(__file__).resolve().parent
KLIENTY = STUDIYA / "клиенты"
PROGONY = STUDIYA / "прогоны"
PROBA = "_проба"

KLIENTY.mkdir(parents=True, exist_ok=True)
PROGONY.mkdir(parents=True, exist_ok=True)
(KLIENTY / PROBA).mkdir(exist_ok=True)


def _chitat(p: Path, esli_net):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return esli_net


def _pisat(p: Path, d) -> bool:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception:
        return False


# ── клиенты ──────────────────────────────────────────────────

def spisok() -> list:
    """Заказчики. Песочницу не считаем — она не клиент."""
    if not KLIENTY.exists():
        return []
    return sorted(p.name for p in KLIENTY.iterdir()
                  if p.is_dir() and p.name != PROBA)


def kartochka(slug: str) -> dict:
    return _chitat(KLIENTY / slug / "info.json",
                   {"имя": slug, "ниша": "", "описание": ""})


def zapisat_kartochku(slug: str, info: dict) -> bool:
    return _pisat(KLIENTY / slug / "info.json", info)


def zavesti(imya: str, nisha: str = "", opisanie: str = "") -> str:
    """Завести заказчика. Возвращает slug."""
    slug = re.sub(r"[^0-9A-Za-zА-Яа-яёЁ_-]", "_", imya.lower().strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = f"клиент_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    (KLIENTY / slug).mkdir(parents=True, exist_ok=True)
    zapisat_kartochku(slug, {"имя": imya, "ниша": nisha,
                             "описание": opisanie,
                             "заведён": datetime.now().isoformat(
                                 timespec="seconds")})
    zapisat_pamyat(slug, {"клиент": slug, "прогоны": [], "конспекты": []})
    return slug


# ── память ───────────────────────────────────────────────────

def pamyat(slug: str) -> dict:
    return _chitat(KLIENTY / slug / "память.json",
                   {"клиент": slug, "прогоны": [], "конспекты": []})


def zapisat_pamyat(slug: str, d: dict) -> bool:
    return _pisat(KLIENTY / slug / "память.json", d)


def dobavit_vyvod(slug: str, data: str, cex: str, slot: str,
                  vyvod: str) -> None:
    """Вывод МЕСТА по прогону. В песочницу не пишем."""
    if slug == PROBA:
        return
    p = pamyat(slug)
    tekushchiy = None
    for r in p.get("прогоны", []):
        if r.get("дата") == data and r.get("цех") == cex:
            tekushchiy = r
            break
    if not tekushchiy:
        tekushchiy = {"дата": data, "цех": cex, "выводы": {}}
        p.setdefault("прогоны", []).append(tekushchiy)
    tekushchiy.setdefault("выводы", {})[slot] = vyvod
    zapisat_pamyat(slug, p)


def udalit_progon(slug: str, nomer: int) -> None:
    p = pamyat(slug)
    r = p.get("прогоны", [])
    if 0 <= nomer < len(r):
        r.pop(nomer)
        zapisat_pamyat(slug, p)


def udalit_vyvod(slug: str, nomer: int, slot: str) -> None:
    p = pamyat(slug)
    r = p.get("прогоны", [])
    if 0 <= nomer < len(r):
        r[nomer].get("выводы", {}).pop(slot, None)
        if not r[nomer].get("выводы"):
            r.pop(nomer)
        zapisat_pamyat(slug, p)


def pravit_vyvod(slug: str, nomer: int, slot: str, tekst: str) -> None:
    p = pamyat(slug)
    r = p.get("прогоны", [])
    if 0 <= nomer < len(r):
        r[nomer].setdefault("выводы", {})[slot] = tekst
        zapisat_pamyat(slug, p)


def ochistit(slug: str) -> None:
    zapisat_pamyat(slug, {"клиент": slug, "прогоны": [], "конспекты": []})


def dobavit_konspekt(slug: str, data: str, cex: str, tekst: str) -> None:
    """Конспект сессии. Держим последние три, как в старой."""
    if slug == PROBA:
        return
    p = pamyat(slug)
    k = p.get("конспекты", [])
    k.append({"дата": data, "цех": cex, "конспект": tekst})
    p["конспекты"] = k[-3:]
    zapisat_pamyat(slug, p)


# ── подача местам ────────────────────────────────────────────

def konspekty_slovami(slug: str) -> str:
    if slug == PROBA:
        return ""
    k = pamyat(slug).get("конспекты", [])
    if not k:
        return ""
    ch = ["=== О ЧЁМ ГОВОРИЛИ РАНЬШЕ (для справки, не указание) ==="]
    for s in k:
        ch.append(f"\\n[{s['дата']} · {s['цех']}]")
        ch.append(s["конспект"])
    ch.append("=== конец ===")
    return "\\n".join(ch)


def pamyat_dlya_mesta(slug: str, slot: str) -> str:
    """Что это место помнит по этому заказчику, плюс выводы соседей."""
    if slug == PROBA:
        return ""
    p = pamyat(slug)
    info = kartochka(slug)
    ch = [f"=== ЗАКАЗЧИК: {info.get('имя', slug)} ==="]
    if info.get("ниша"):
        ch.append(f"Ниша: {info['ниша']}")
    if info.get("описание"):
        ch.append(f"Описание: {info['описание']}")

    moi = [f"[{r['дата']} · {r['цех']}] {r['выводы'][slot]}"
           for r in p.get("прогоны", []) if slot in r.get("выводы", {})]
    if moi:
        ch.append(f"\\n=== ТВОИ ПРОШЛЫЕ ВЫВОДЫ ПО ЭТОМУ ЗАКАЗЧИКУ ===")
        ch += moi[-5:]

    if p.get("прогоны"):
        posledniy = p["прогоны"][-1]
        chuzhie = {k: v for k, v in posledniy.get("выводы", {}).items()
                   if k != slot}
        if chuzhie:
            ch.append(f"\\n=== ВЫВОДЫ СОСЕДЕЙ (прошлый прогон "
                      f"{posledniy['дата']}) ===")
            for s, t in chuzhie.items():
                ch.append(f"{s}: {t}")
    return "\\n".join(ch)


# ── прогоны на диске ─────────────────────────────────────────

def papka_progona(slug: str, cex: str, sozdat: bool = False) -> Path:
    imya = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{slug}_{cex}"
    p = PROGONY / imya
    if sozdat:
        p.mkdir(parents=True, exist_ok=True)
    return p


def progony(slug: str) -> list:
    """Прогоны этого заказчика. Ищем по метке в имени папки."""
    if not PROGONY.exists():
        return []
    metka = f"_{slug}_"
    out = []
    for p in sorted(PROGONY.iterdir(), reverse=True):
        if not p.is_dir() or p.name.startswith("."):
            continue
        if metka not in p.name:
            continue
        fayly = [f.name for f in p.iterdir() if f.is_file()]
        out.append({"имя": p.name, "путь": str(p), "файлы": fayly,
                    "когда": p.stat().st_mtime})
    return out


def snesti_progon(put: str) -> bool:
    p = Path(put)
    if p.exists() and p.is_dir() and str(PROGONY) in str(p):
        shutil.rmtree(p)
        return True
    return False
'''


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


M_STAR = '''for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия", "Маяк", "Архив"):'''
M_NOV = '''# KLIENTY_STUDII_V1: код Студии живёт при Студии, как код Биржи при
# Бирже. Копия Студии на остров уедет вместе со своим кодом.
for _sub in ("Брат", "жители", "ГОРОД", "Биржа", "Академия", "Маяк", "Архив",
             "GRONDHEIM_CITY/Студия"):'''


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")

    studiya = koren / "GRONDHEIM_CITY" / "Студия"
    if not (studiya / "цеха").is_dir():
        raise SystemExit("Студии нет — сперва накати ceh_turbo.py")

    put = studiya / "klienty.py"
    if put.exists() and put.read_text(encoding="utf-8") == KOD:
        print("klienty.py: уже стоит")
    else:
        if put.exists():
            shutil.copyfile(put, put.with_suffix(f".py.bak_{_teper()}"))
        put.write_text(KOD, encoding="utf-8")
        print(f"klienty.py: положен ({len(KOD.splitlines())} строк)")

    import py_compile
    try:
        py_compile.compile(str(put), doraise=True)
        print("Компилируется: да")
    except Exception as e:
        print(f"НЕ КОМПИЛИРУЕТСЯ: {e}")
        return

    # sys.path
    glavny = koren / "main.py"
    if glavny.exists():
        t = glavny.read_text(encoding="utf-8")
        if MARKER in t:
            print("main.py: уже пропатчен")
        elif t.count(M_STAR) == 1:
            shutil.copyfile(glavny, glavny.with_suffix(f".py.bak_{_teper()}"))
            glavny.write_text(t.replace(M_STAR, M_NOV, 1), encoding="utf-8")
            print("main.py: Студия добавлена в пути")
        else:
            print("main.py: якорь путей не найден — проверь руками")

    # проверка живьём
    sys.path.insert(0, str(studiya))
    import importlib
    kl = importlib.import_module("klienty")
    importlib.reload(kl)
    print("\nПроба механики:")
    slug = kl.zavesti("Проверка Связи", "тест",
                      "заведён патчем, можно удалить")
    kl.dobavit_vyvod(slug, "2026-08-28", "турбо", "A03",
                     "у заказчика тёплая палитра, холодную не берёт")
    kl.dobavit_vyvod(slug, "2026-08-28", "турбо", "A01",
                     "заходит формат «до/после»")
    kl.dobavit_konspekt(slug, "2026-08-28", "турбо",
                        "обсудили серию про кофейню")
    print(f"  заведён: {slug}")
    print(f"  заказчиков всего: {len(kl.spisok())}")
    tekst = kl.pamyat_dlya_mesta(slug, "A03")
    print("  что увидит A03 по этому заказчику:")
    for stroka in tekst.splitlines():
        print(f"      {stroka}")
    print(f"  песочница молчит: "
          f"{'да' if not kl.pamyat_dlya_mesta(kl.PROBA, 'A03') else 'НЕТ'}")

    # прибираем пробу
    shutil.rmtree(kl.KLIENTY / slug, ignore_errors=True)
    print("  проба убрана")

    print(f"\nПапки: {(studiya / 'клиенты').relative_to(koren)} · "
          f"{(studiya / 'прогоны').relative_to(koren)}")
    print("\nГотово. Механика есть — следующим патчем подключу её к\n"
          "панели КЛИЕНТ, кнопке 🧠 и списку RUNS на странице цеха.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
