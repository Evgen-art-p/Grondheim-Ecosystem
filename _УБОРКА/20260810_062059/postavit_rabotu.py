# -*- coding: utf-8 -*-
# RABOTA_DOKUMENT_V1
"""
РАБОТА — должность становится документом при месте.

    python postavit_rabotu.py --suho     посмотреть, ничего не менять
    python postavit_rabotu.py            поставить
    python postavit_rabotu.py --zavesti  и завести документы трёх мест

Запускать из КОРНЯ репо. Идемпотентно. Копия правленого файла рядом.

ЗАЧЕМ

    Работа была вкручена в личность. У жителя в его личной папке лежала
    бумажка «я работаю в цехе таком-то на слоте таком-то», и город,
    чтобы узнать, кто сидит на месте, обходил всех жителей и заглядывал
    им внутрь. Уволить — значит лезть человеку в личность и выскабливать.
    Кнопкой это и не делалось: принять она умела, уволить — нет.

СТАНОВИТСЯ

    У места появляется свой документ — `слоты/{слот}/должность.json`.
    Полноценный бланк, а не строчка: название, где, чем занят,
    обязанности, судья, требования, условия — и ТРУДОВАЯ ИСТОРИЯ:
    кто принят, когда, кем, когда уволен и почему. История копится и
    не перетирается.

    Правда о том, кто сидит, живёт в этом документе. У жителя остаётся
    мягкая ОТМЕТКА в паспорте — «работаю там-то, с такого-то числа»:
    её читают и дом, и Академия, и Ректор, так что он знает, кто он,
    не только стоя на Бирже. Разошлось — верим документу.

    Приняли — отметка зажглась. Уволили — погасла сама.

ЧТО УЕЗЖАЕТ, ЧТО ОСТАЁТСЯ (слово Шефа)

    Личное — с жителем: его дневник переезжает к нему домой, в папку
    `опыт/`. Следующий человек садится за чистый стол и не читает
    чужую память.
    Статистика места — при месте: `данные/*_stats.json` не трогаем.

СТАРОЕ НЕ ЛОМАЕТСЯ

    Пока документа у места нет, всё работает по-старому — по бумажке
    в жителе. Поэтому Илья не выпадет из строя в ту же секунду.
    Появился документ — правду говорит он.

ЧТО СТАВИТСЯ
    · Биржа/rabota.py        — сам механизм (документ, приём, увольнение)
    · Биржа/cartridge_registry.py — правится: сперва документ, потом бумажка
    · rabota_pult.py         — пульт из корня: смотреть, принимать, увольнять
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
BIRZHA = KOREN / "Биржа"
REG = BIRZHA / "cartridge_registry.py"
MARKER = "# RABOTA_DOKUMENT_V1 - marker"
BAK = ".bak_rabota"


# ═══════════════════════════════════════════════════════════════
# ФАЙЛ 1 — Биржа/rabota.py
# ═══════════════════════════════════════════════════════════════
RABOTA_PY = r'''# -*- coding: utf-8 -*-
# RABOTA_DOKUMENT_V1
"""
РАБОТА — должность как документ при месте.

ЗАКОН ЭТОГО ФАЙЛА
    Работа не вкручивается в личность. Место несёт свой документ:
    `слоты/{слот}/должность.json`. В нём написано, что это за
    должность и кто на ней сейчас сидит. У жителя — только мягкая
    отметка в паспорте, чтобы он знал, кто он, где бы ни находился.
    Разошлось — правда за документом.

    Здесь нет UI и нет модели. Чистое чтение и запись диска.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
CITY = _BIRZHA.parent / "GRONDHEIM_CITY"
IMYA_DOKUMENTA = "должность.json"


def _teper() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _chitat_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pisat_json(p: Path, d) -> bool:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# ГДЕ ЛЕЖИТ ДОКУМЕНТ
# ─────────────────────────────────────────────────────────────

def put_slota(ceh: str, slot: str, kvartal: str = "Биржа") -> Path:
    return CITY / kvartal / "цеха" / ceh / "слоты" / slot


def put_dokumenta(ceh: str, slot: str, kvartal: str = "Биржа") -> Path:
    return put_slota(ceh, slot, kvartal) / IMYA_DOKUMENTA


def blank(ceh: str, slot: str, nazvanie: str = "",
          kvartal: str = "Биржа") -> dict:
    """Пустой бланк должности. Заполняется на Странице Работы или
    пультом; поля, которые не заполнили, честно остаются пустыми."""
    return {
        "документ": "должность",
        "версия": 1,
        "название": nazvanie or f"{ceh} · {slot}",
        "квартал": kvartal,
        "цех": ceh,
        "слот": slot,
        "чем_занят": "",
        "обязанности": [],
        "судья": "",
        "требования": "",
        "условия": "",
        "движок": "мозг.py",
        "кто_сидит": None,
        "трудовая_история": [],
        "заведён": _teper(),
    }


def chitat(ceh: str, slot: str, kvartal: str = "Биржа"):
    """Документ места или None, если его ещё не заводили."""
    return _chitat_json(put_dokumenta(ceh, slot, kvartal))


def zavesti(ceh: str, slot: str, polya: dict | None = None,
            kvartal: str = "Биржа") -> tuple:
    """Завести документ. Заведённый не перетираем — только дополняем
    пустые поля: трудовую историю терять нельзя."""
    put = put_dokumenta(ceh, slot, kvartal)
    if not put.parent.exists():
        return False, f"нет слота {ceh}/{slot}"
    d = _chitat_json(put)
    if d is None:
        d = blank(ceh, slot, (polya or {}).get("название", ""), kvartal)
        novy = True
    else:
        novy = False
    for k, v in (polya or {}).items():
        if k in ("кто_сидит", "трудовая_история"):
            continue          # это не бланк, это жизнь документа
        if v in (None, "", []):
            continue
        if novy or not d.get(k):
            d[k] = v
    if not _pisat_json(put, d):
        return False, "не записался"
    return True, ("документ заведён" if novy else "документ обновлён")


def spisok(kvartal: str = "Биржа") -> list:
    """Все места квартала: что за слот, есть ли документ, кто сидит.
    Слоты читаются из манифестов цехов — списков нигде не держим."""
    out = []
    root = CITY / kvartal / "цеха"
    if not root.exists():
        return out
    for ceh_dir in sorted(root.iterdir()):
        mf = ceh_dir / "manifest.json"
        if not ceh_dir.is_dir() or not mf.exists():
            continue
        m = _chitat_json(mf) or {}
        for s in m.get("слоты", []) or []:
            slot = s.get("слот")
            if not slot:
                continue
            d = chitat(ceh_dir.name, slot, kvartal)
            out.append({
                "цех": ceh_dir.name,
                "слот": slot,
                "роль": s.get("роль", ""),
                "документ": bool(d),
                "название": (d or {}).get("название", ""),
                "кто_сидит": ((d or {}).get("кто_сидит") or {}).get("имя", ""),
                "мозг": (put_slota(ceh_dir.name, slot, kvartal)
                         / "мозг.py").exists(),
            })
    return out


def kto_sidit(ceh: str, slot: str, kvartal: str = "Биржа") -> str:
    """Имя того, кто на месте. Документа нет — пустая строка, и это
    значит «спрашивай по-старому», а не «место пусто»."""
    d = chitat(ceh, slot, kvartal)
    if not d:
        return ""
    return ((d.get("кто_сидит") or {}).get("имя") or "").strip()


def est_dokument(ceh: str, slot: str, kvartal: str = "Биржа") -> bool:
    return put_dokumenta(ceh, slot, kvartal).exists()


# ─────────────────────────────────────────────────────────────
# ЖИТЕЛЬ: дом, отметка в паспорте
# ─────────────────────────────────────────────────────────────

def dom_zhitelya(imya: str):
    """Папка жителя по имени. Ищем по паспорту, не по имени папки —
    папка может называться иначе."""
    imya = (imya or "").strip()
    if not imya:
        return None
    root = CITY / "жители"
    if not root.exists():
        return None
    for p in sorted(root.glob("*/*/passport.json")):
        d = _chitat_json(p) or {}
        if (d.get("Official_Name") or p.parent.name).strip() == imya:
            return p.parent
    return None


def _zapisat_otmetku(imya: str, d: dict) -> bool:
    """Мягкая отметка в паспорт: «работаю там-то, с такого-то числа».
    Читается везде, где читают паспорт. Правды не несёт — правда в
    документе места."""
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _chitat_json(pp)
    if p is None:
        return False
    p["Работа"] = {
        "должность": d.get("название", ""),
        "где": f"{d.get('квартал','')} · {d.get('цех','')} · {d.get('слот','')}",
        "с": _teper(),
        "_note": ("отметка о работе. Правда о найме живёт в документе "
                  "места (должность.json); эта строка — чтобы житель "
                  "знал, кто он, и вне своего квартала."),
    }
    return _pisat_json(pp, p)


def _pogasit_otmetku(imya: str) -> bool:
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _chitat_json(pp)
    if p is None:
        return False
    if "Работа" in p:
        p.pop("Работа", None)
        return _pisat_json(pp, p)
    return True


def _dnevnik_uezzhaet(ceh: str, slot: str, imya: str,
                      kvartal: str = "Биржа") -> int:
    """Личное уезжает с жителем (слово Шефа): дневники из данных места
    переезжают к нему домой, в `опыт/`. Статистика места остаётся.
    Следующий садится за чистый стол и чужой памяти не читает."""
    dom = dom_zhitelya(imya)
    dannye = put_slota(ceh, slot, kvartal) / "данные"
    if dom is None or not dannye.exists():
        return 0
    kuda = dom / "опыт"
    kuda.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(dannye.glob("diary_*.jsonl")):
        cel = kuda / f"{kvartal}_{ceh}_{slot}_{f.name}"
        i = 1
        while cel.exists():
            cel = kuda / f"{kvartal}_{ceh}_{slot}_{i}_{f.name}"
            i += 1
        try:
            f.replace(cel)
            n += 1
        except Exception:
            pass
    return n


# ─────────────────────────────────────────────────────────────
# ПРИЁМ И УВОЛЬНЕНИЕ
# ─────────────────────────────────────────────────────────────

def prinyat(ceh: str, slot: str, imya: str, kem: str = "Шеф",
            pochemu: str = "", kvartal: str = "Биржа") -> tuple:
    """Принять жителя на место. Занято другим — не вышибаем молча."""
    imya = (imya or "").strip()
    if not imya:
        return False, "не сказано, кого принимаем"
    put = put_dokumenta(ceh, slot, kvartal)
    d = _chitat_json(put)
    if d is None:
        return False, "у места нет документа — сперва заведи должность"
    if dom_zhitelya(imya) is None:
        return False, f"жителя «{imya}» в городе не нашёл"
    zanyal = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if zanyal and zanyal != imya:
        return False, f"место занято: {zanyal} — сперва уволь"
    if zanyal == imya:
        return True, f"{imya} и так на этом месте"
    d["кто_сидит"] = {"имя": imya, "с": _teper()}
    d.setdefault("трудовая_история", []).append({
        "когда": _teper(), "что": "принят", "кто": imya,
        "кем": kem, "почему": pochemu,
    })
    if not _pisat_json(put, d):
        return False, "документ не записался"
    _zapisat_otmetku(imya, d)
    return True, f"{imya} принят на «{d.get('название','место')}»"


def uvolit(ceh: str, slot: str, kem: str = "Шеф", pochemu: str = "",
           kvartal: str = "Биржа") -> tuple:
    """Уволить того, кто на месте. Личное уезжает с ним."""
    put = put_dokumenta(ceh, slot, kvartal)
    d = _chitat_json(put)
    if d is None:
        return False, "у места нет документа"
    imya = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if not imya:
        return True, "место и так свободно"
    d["кто_сидит"] = None
    d.setdefault("трудовая_история", []).append({
        "когда": _teper(), "что": "уволен", "кто": imya,
        "кем": kem, "почему": pochemu,
    })
    if not _pisat_json(put, d):
        return False, "документ не записался"
    _pogasit_otmetku(imya)
    n = _dnevnik_uezzhaet(ceh, slot, imya, kvartal)
    hvost = f", дневников уехало с ним: {n}" if n else ""
    return True, f"{imya} уволен, место свободно{hvost}"
'''


# ═══════════════════════════════════════════════════════════════
# ФАЙЛ 2 — rabota_pult.py (корень)
# ═══════════════════════════════════════════════════════════════
PULT_PY = r'''# -*- coding: utf-8 -*-
# RABOTA_PULT_V1
"""
ПУЛЬТ РАБОТЫ — смотреть, принимать, увольнять. Из корня репо.

    python rabota_pult.py                      кто где сидит
    python rabota_pult.py --zavesti            завести документы мест
    python rabota_pult.py --prinyat A06 Брут   принять на место
    python rabota_pult.py --uvolit A06         уволить с места
    python rabota_pult.py --uvolit A06 --pochemu "ушёл учиться"

Цех по умолчанию — торговый_хаос, другой задаётся ключом --ceh.
Кнопки в кабинете Брата придут следом; пульт останется как есть —
он же и проверка, что механизм работает без всякого UI.
"""
import argparse
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
sys.path.insert(0, str(KOREN / "Биржа"))

import rabota as R   # noqa: E402

# заготовки бланка для трёх мест Биржи: что можно заполнить, не
# придумывая — остальное Шеф допишет на Странице Работы.
ZAGOTOVKI = {
    "A06": {"название": "Трейдер-пробой",
            "чем_занят": "входит по пробою",
            "судья": "рынок"},
    "A07": {"название": "Трейдер-ранний",
            "чем_занят": "входит рано, на первой волне движения",
            "судья": "рынок"},
    "A08": {"название": "Трейдер-откат",
            "чем_занят": "входит на откате к первой волне",
            "судья": "рынок"},
}


def pokazat(ceh: str):
    print("═" * 60)
    print("МЕСТА БИРЖИ")
    print("═" * 60)
    for m in R.spisok():
        if ceh and m["цех"] != ceh:
            continue
        kto = m["кто_сидит"] or "— свободно"
        dok = "документ есть" if m["документ"] else "документа нет"
        mozg = "" if m["мозг"] else "  (мозга в слоте нет)"
        print(f"  {m['слот']}  {m['роль'] or m['название']:<22} "
              f"{kto:<16} {dok}{mozg}")
    print("─" * 60)
    print("принять:  python rabota_pult.py --prinyat A06 Имя")
    print("уволить:  python rabota_pult.py --uvolit A06")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceh", default="торговый_хаос")
    ap.add_argument("--zavesti", action="store_true")
    ap.add_argument("--prinyat", nargs=2, metavar=("СЛОТ", "ИМЯ"))
    ap.add_argument("--uvolit", metavar="СЛОТ")
    ap.add_argument("--pochemu", default="")
    a = ap.parse_args()

    if a.zavesti:
        for m in R.spisok():
            if m["цех"] != a.ceh:
                continue
            polya = dict(ZAGOTOVKI.get(m["слот"], {}))
            polya.setdefault("название", m["роль"] or m["слот"])
            ok, msg = R.zavesti(a.ceh, m["слот"], polya)
            print(f"  {m['слот']}: {msg}" if ok else f"  ✗ {m['слот']}: {msg}")
        print()

    if a.prinyat:
        slot, imya = a.prinyat
        ok, msg = R.prinyat(a.ceh, slot, imya, pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg)
        print()

    if a.uvolit:
        ok, msg = R.uvolit(a.ceh, a.uvolit, pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg)
        print()

    pokazat(a.ceh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# ═══════════════════════════════════════════════════════════════
# ПРАВКА — cartridge_registry.resolve_para: сперва документ
# ═══════════════════════════════════════════════════════════════
STAROE_RESOLVE = '''def resolve_para(ceh_id: str, slot: str, kvartal: str = "Биржа"):
    """ЕДИНСТВЕННАЯ точка правды пары (цех, слот) → носитель.
    Ищет ТОЛЬКО по mask.json (Workshop_ID + Turbo_Role).
    Честный None: слот пуст / цеха нет / слота в манифесте нет."""
    ceh = get_ceh(ceh_id, kvartal)
    if ceh is None:
        return None
    slots = [s.get("слот") for s in ceh.get("слоты", [])]
    if slot not in slots:
        return None  # такой вакансии в цехе не объявлено
    for z in _scan_zhiteli_maski():
'''

NOVOE_RESOLVE = '''def _zhitel_po_imeni(imya: str):
    """RABOTA_DOKUMENT_V1: житель по имени, без всяких масок работы.
    Нужен, когда правду о найме говорит документ места, а не бумажка
    в жителе. Магик по-прежнему берём из маски — он про человека и
    его сделки, а не про место."""
    imya = (imya or "").strip()
    if not imya:
        return None
    root = CITY / "жители"
    if not root.exists():
        return None
    for passport_path in sorted(root.glob("*/*/passport.json")):
        p = _read_json(passport_path) or {}
        if (p.get("Official_Name") or passport_path.parent.name).strip() != imya:
            continue
        dom = passport_path.parent
        mask = _read_json(dom / "маски" / "работа" / "mask.json") or {}
        return {
            "имя": p.get("Official_Name", dom.name),
            "id": p.get("ID_Object", ""),
            "тип": p.get("тип", ""),
            "папка": str(dom),
            "цех": "",
            "слот": "",
            "core_phrase": mask.get("Core_Phrase", ""),
            "magic": mask.get("magic"),
        }
    return None


def resolve_para(ceh_id: str, slot: str, kvartal: str = "Биржа"):
    """ЕДИНСТВЕННАЯ точка правды пары (цех, слот) → носитель.

    RABOTA_DOKUMENT_V1: сперва спрашиваем ДОКУМЕНТ МЕСТА
    (слоты/{слот}/должность.json) — там написано, кого приняли.
    Работа больше не вкручена в личность: уволить можно, не трогая
    жителя. Документа у места ещё нет — работаем по-старому, по
    mask.json, чтобы уже сидящие не выпали из строя.
    Честный None: слот пуст / цеха нет / слота в манифесте нет."""
    ceh = get_ceh(ceh_id, kvartal)
    if ceh is None:
        return None
    slots = [s.get("слот") for s in ceh.get("слоты", [])]
    if slot not in slots:
        return None  # такой вакансии в цехе не объявлено

    try:
        import rabota as _rab
        if _rab.est_dokument(ceh_id, slot, kvartal):
            _imya = _rab.kto_sidit(ceh_id, slot, kvartal)
            if not _imya:
                return None            # документ говорит: место свободно
            _z = _zhitel_po_imeni(_imya)
            if _z is None:
                return None            # в документе имя, а жителя нет
            _z["цех"] = ceh_id
            _z["слот"] = slot
            return _z
    except Exception:
        pass                            # механизма нет — по-старому

    for z in _scan_zhiteli_maski():
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"    ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"    ✗ {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def polozhit(put: Path, soderzhimoe: str, suho: bool) -> bool:
    if put.exists() and put.read_text(encoding="utf-8") == soderzhimoe:
        print(f"  {put.name}: уже стоит")
        return True
    if not proverit_python(soderzhimoe, put.name):
        return False
    if suho:
        print(f"  {put.name}: ✓ ляжет ({'замена' if put.exists() else 'новый'})")
        return True
    if put.exists():
        shutil.copy2(put, put.with_suffix(put.suffix + BAK))
    put.write_text(soderzhimoe, encoding="utf-8")
    print(f"  {put.name}: ✓ положен")
    return True


def pravit_registry(suho: bool) -> bool:
    if not REG.exists():
        print("  ✗ не вижу Биржа/cartridge_registry.py")
        return False
    tekst = REG.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  cartridge_registry.py: уже правлен")
        return True
    n = tekst.count(STAROE_RESOLVE)
    if n != 1:
        print(f"  ✗ cartridge_registry.py: якорь найден {n} раз — не трогаю")
        return False
    tekst = tekst.replace(STAROE_RESOLVE, NOVOE_RESOLVE, 1)
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "cartridge_registry.py"):
        return False
    if suho:
        print("  cartridge_registry.py: ✓ готов к правке")
        return True
    shutil.copy2(REG, REG.with_suffix(REG.suffix + BAK))
    REG.write_text(tekst, encoding="utf-8")
    print(f"  cartridge_registry.py: ✓ правлен (копия рядом: *{BAK})")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    ap.add_argument("--zavesti", action="store_true",
                    help="сразу завести документы мест торгового_хаоса")
    a = ap.parse_args()

    if not BIRZHA.exists():
        print("✗ не вижу папку Биржа — запускай из КОРНЯ репо")
        return 1

    print("═" * 60)
    print("РАБОТА · должность документом" +
          ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 60)

    ok = True
    print("\nмеханизм:")
    ok &= polozhit(BIRZHA / "rabota.py", RABOTA_PY, a.suho)
    print("\nпульт из корня:")
    ok &= polozhit(KOREN / "rabota_pult.py", PULT_PY, a.suho)
    print("\nправда о найме:")
    ok &= pravit_registry(a.suho)

    if not ok:
        print("\n⚠ что-то не легло — ничего дальше не делаю")
        return 1

    if a.suho:
        print("\nСухой прогон прошёл. Ставить: python postavit_rabotu.py")
        return 0

    if a.zavesti:
        print("\nзавожу документы мест:")
        sys.path.insert(0, str(BIRZHA))
        import rabota as R
        import importlib
        importlib.reload(R)
        from rabota_pult import ZAGOTOVKI
        for m in R.spisok():
            if m["цех"] != "торговый_хаос":
                continue
            polya = dict(ZAGOTOVKI.get(m["слот"], {}))
            polya.setdefault("название", m["роль"] or m["слот"])
            ok2, msg = R.zavesti("торговый_хаос", m["слот"], polya)
            print(f"  {m['слот']}: {msg}" if ok2 else f"  ✗ {m['слот']}: {msg}")

    print("\n" + "─" * 60)
    print("Дальше — пультом из корня:")
    print("  python rabota_pult.py                     кто где сидит")
    if not a.zavesti:
        print("  python rabota_pult.py --zavesti           завести документы")
    print("  python rabota_pult.py --prinyat A07 Илья   принять")
    print("  python rabota_pult.py --uvolit A07         уволить")
    print()
    print("ВАЖНО: пока документа у места нет — всё по-старому.")
    print("Как только документ появился, правду говорит он: место без")
    print("имени в документе считается свободным, даже если у жителя")
    print("осталась старая бумажка. Поэтому сразу после --zavesti")
    print("посади тех, кто должен сидеть.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
