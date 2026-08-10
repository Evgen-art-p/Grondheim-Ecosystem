# -*- coding: utf-8 -*-
# STANDART_RABOTY_V1
"""
СТАНДАРТ РАБОТЫ — один реестр мест на весь город, четыре руки.

    python postavit_standart_raboty.py --suho    посмотреть
    python postavit_standart_raboty.py           поставить

Запускать из КОРНЯ репо. Идемпотентно.

СТАНДАРТ (принят Шефом 08.08)

  1. Место называется ПОСТ. Реестр один: GRONDHEIM_CITY/посты/{id}/пост.json
  2. Пост — один файл, поля у всех одинаковые.
  3. Кто сидит — написано в посте. В паспорте жителя отметка, чтобы он
     знал о работе везде. Разошлись — верим посту.
  4. Четыре руки: завести · принять · уволить · снести.
     Снести можно только свободный пост.
  5. Одна дверь (Страница Работы) и один запасной ход (пульт из корня).
  6. Привязка к движку — поля квартал/цех/слот в том же бланке.
  7. Старое сводится в этот реестр.

ПРО СЕДЬМОЙ ПУНКТ — ВАЖНОЕ

  Полез считать твои полторы сотни и нашёл их: в старой студии
  двенадцать цехов-картриджей по 9–18 агентов, плюс девять резидентов.
  Это и есть ~150 мест.

  Тащить их руками не надо и не буду. По вашему же Закону Картриджа
  никто не ведёт списков — все сканируют папки. Так и здесь: сканер
  обходит манифесты (и нового города, и старой студии, если укажешь
  путь) и показывает КАЖДОЕ место. У которого поста ещё нет — оно
  честно помечено «должности нет», и завести бланк можно одним
  движением. Ничего не потеряется и ничего не размножится.

  Путь к старой студии: положи его строкой в файл
  `ГОРОД/студия_путь.txt` (например C:\\...\\-2). Нет файла — сканер
  просто не увидит студию, всё остальное работает.

ЧТО СНОСИТСЯ

  Мой вчерашний дубль: Биржа/rabota.py и документы должность.json при
  слотах. Правда о найме была там второй — теперь она одна, в посте.
  Правка cartridge_registry переписывается на посты.

ЧЕГО ЗДЕСЬ ПОКА НЕТ
  Страницы Работы с деревом и поиском — она следующим шагом. Сейчас
  ставится сам стандарт и пульт, чтобы можно было принимать и
  увольнять уже сегодня и проверить, что механизм честный.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

KOREN = Path(__file__).resolve().parent
GOROD = KOREN / "ГОРОД"
BIRZHA = KOREN / "Биржа"
REG = BIRZHA / "cartridge_registry.py"
CITY = KOREN / "GRONDHEIM_CITY"
MARKER = "# STANDART_RABOTY_V1 - marker"
BAK = ".bak_standart"


RABOTA_PY = r'''# -*- coding: utf-8 -*-
# STANDART_RABOTY_V1
"""
РАБОТА — единый стандарт мест города.

ЗАКОН ЭТОГО ФАЙЛА
    Место называется ПОСТ, и реестр один: GRONDHEIM_CITY/посты/.
    Пост — полноценный бланк, а не строчка. Кто сидит — написано в
    посте; у жителя в паспорте отметка, чтобы он знал о работе где
    угодно. Разошлись — правда за постом.

    Списков мест здесь нет и не будет: места СКАНИРУЮТСЯ (Закон
    Картриджа — никто не ведёт списков). Появился цех — появились его
    места. Удалил папку — места ушли.

    Четыре руки: zavesti · prinyat · uvolit · snesti.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_GOROD = Path(__file__).resolve().parent
KOREN = _GOROD.parent
CITY = KOREN / "GRONDHEIM_CITY"
POSTY = CITY / "посты"
KOVCHEG = CITY / "жители" / "ковчег"
STUDIA_PUT = _GOROD / "студия_путь.txt"

POLYA_BLANKA = ("название", "где", "квартал", "цех", "слот", "чем_занят",
                "обязанности", "судья", "требования", "условия", "движок")


def _teper() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _chitat(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pisat(p: Path, d) -> bool:
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return True
    except Exception:
        return False


def put_posta(post_id: str) -> Path:
    return POSTY / post_id / "пост.json"


def blank(post_id: str, polya: dict | None = None) -> dict:
    d = {
        "id": post_id,
        "название": "",
        "где": "",
        "квартал": "",
        "цех": "",
        "слот": "",
        "чем_занят": "",
        "обязанности": [],
        "судья": "",
        "требования": "",
        "условия": "",
        "движок": "",
        "кто_сидит": None,
        "трудовая_история": [],
        "заведён": _teper(),
    }
    for k, v in (polya or {}).items():
        if k in POLYA_BLANKA and v not in (None, "", []):
            d[k] = v
    if not d["название"]:
        d["название"] = post_id
    return d


def chitat(post_id: str):
    return _chitat(put_posta(post_id))


def id_dlya_slota(ceh: str, slot: str) -> str:
    """Имя поста для места в цехе. Одно правило на весь город, чтобы
    один и тот же слот не завёлся дважды под разными именами."""
    return f"{ceh}__{slot}"


# ─────────────────────────────────────────────────────────────
# СКАНЕР МЕСТ — списков не ведём
# ─────────────────────────────────────────────────────────────

def _studia_koren():
    """Корень старой студии, если Шеф указал путь. Нет — None."""
    try:
        p = Path(STUDIA_PUT.read_text(encoding="utf-8").strip())
        return p if p.exists() else None
    except Exception:
        return None


def _mesta_novogo_goroda() -> list:
    out = []
    if not CITY.exists():
        return out
    for kv in sorted(CITY.iterdir()):
        ceha = kv / "цеха"
        if not ceha.is_dir():
            continue
        for cd in sorted(ceha.iterdir()):
            mf = cd / "manifest.json"
            if not mf.exists():
                continue
            m = _chitat(mf) or {}
            for s in m.get("слоты", []) or []:
                slot = s.get("слот")
                if slot:
                    out.append({"квартал": kv.name, "цех": cd.name,
                                "слот": slot, "роль": s.get("роль", ""),
                                "откуда": "город"})
    return out


def _mesta_staroy_studii() -> list:
    """Слоты картриджей старой студии. Путь не указан — пусто."""
    out = []
    koren = _studia_koren()
    if koren is None:
        return out
    mods = koren / "studio" / "modules"
    if not mods.is_dir():
        return out
    for cd in sorted(mods.iterdir()):
        mf = cd / "manifest.json"
        if not mf.exists():
            continue
        m = _chitat(mf) or {}
        vidno = []
        for spisok in (m.get("phases") or {}).values():
            for a in spisok or []:
                if a not in vidno:
                    vidno.append(a)
        for a in vidno:
            out.append({"квартал": "Студия", "цех": cd.name, "слот": a,
                        "роль": "", "откуда": "студия"})
    return out


def mesta() -> list:
    """ВСЕ места города: заведённые посты плюс слоты цехов, у которых
    поста ещё нет. Одно место — одна строка, дублей не бывает: слот
    и пост сходятся по id_dlya_slota."""
    out = []
    vidennye = set()

    if POSTY.exists():
        for d in sorted(POSTY.iterdir()):
            p = _chitat(d / "пост.json")
            if not p:
                continue
            out.append({
                "id": p.get("id", d.name),
                "название": p.get("название", d.name),
                "квартал": p.get("квартал", ""),
                "цех": p.get("цех", ""),
                "слот": p.get("слот", ""),
                "кто_сидит": ((p.get("кто_сидит") or {}).get("имя") or ""),
                "есть_пост": True,
                "откуда": "пост",
            })
            if p.get("цех") and p.get("слот"):
                vidennye.add(id_dlya_slota(p["цех"], p["слот"]))
            vidennye.add(p.get("id", d.name))

    for m in _mesta_novogo_goroda() + _mesta_staroy_studii():
        pid = id_dlya_slota(m["цех"], m["слот"])
        if pid in vidennye:
            continue
        out.append({
            "id": pid,
            "название": m.get("роль") or f'{m["цех"]} · {m["слот"]}',
            "квартал": m["квартал"], "цех": m["цех"], "слот": m["слот"],
            "кто_сидит": "", "есть_пост": False, "откуда": m["откуда"],
        })
    return out


def schet() -> dict:
    v = mesta()
    return {"всего": len(v),
            "с должностью": sum(1 for m in v if m["есть_пост"]),
            "занято": sum(1 for m in v if m["кто_сидит"]),
            "свободно": sum(1 for m in v if m["есть_пост"] and not m["кто_сидит"]),
            "без должности": sum(1 for m in v if not m["есть_пост"])}


# ─────────────────────────────────────────────────────────────
# ЖИТЕЛЬ: дом и отметка
# ─────────────────────────────────────────────────────────────

def dom_zhitelya(imya: str):
    imya = (imya or "").strip()
    if not imya or not KOVCHEG.exists():
        return None
    for p in sorted(KOVCHEG.glob("*/passport.json")):
        d = _chitat(p) or {}
        if (d.get("Official_Name") or p.parent.name).strip() == imya:
            return p.parent
    return None


def _otmetka(imya: str, post: dict | None):
    """Отметка в паспорте: житель знает о работе где угодно. Правды не
    несёт — правда в посте. post=None — гасим."""
    dom = dom_zhitelya(imya)
    if dom is None:
        return False
    pp = dom / "passport.json"
    p = _chitat(pp)
    if p is None:
        return False
    if post is None:
        p.pop("Работа", None)
    else:
        gde = " · ".join(x for x in (post.get("квартал"), post.get("цех"),
                                     post.get("слот")) if x) or post.get("где", "")
        p["Работа"] = {"должность": post.get("название", ""), "где": gde,
                       "пост": post.get("id", ""), "с": _teper(),
                       "_note": ("отметка о работе. Правда о найме — в "
                                 "документе поста; здесь для того, чтобы "
                                 "житель знал о ней где угодно.")}
    return _pisat(pp, p)


# ─────────────────────────────────────────────────────────────
# ЧЕТЫРЕ РУКИ
# ─────────────────────────────────────────────────────────────

def zavesti(post_id: str, polya: dict | None = None) -> tuple:
    """Завести должность. Заведённую не перетираем — дополняем."""
    put = put_posta(post_id)
    d = _chitat(put)
    if d is None:
        d = blank(post_id, polya)
        msg = "должность заведена"
    else:
        for k, v in (polya or {}).items():
            if k in POLYA_BLANKA and v not in (None, "", []) and not d.get(k):
                d[k] = v
        msg = "должность обновлена"
    return (True, msg) if _pisat(put, d) else (False, "не записался")


def obnovit(post_id: str, polya: dict) -> tuple:
    """Переписать поля бланка. Кто сидит и историю не трогаем."""
    put = put_posta(post_id)
    d = _chitat(put)
    if d is None:
        return False, "такой должности нет"
    for k, v in (polya or {}).items():
        if k in POLYA_BLANKA:
            d[k] = v
    return (True, "бланк переписан") if _pisat(put, d) else (False, "не записался")


def prinyat(post_id: str, imya: str, kem: str = "Шеф",
            pochemu: str = "") -> tuple:
    imya = (imya or "").strip()
    if not imya:
        return False, "не сказано, кого принимаем"
    put = put_posta(post_id)
    d = _chitat(put)
    if d is None:
        return False, "у места нет должности — сперва заведи"
    if dom_zhitelya(imya) is None:
        return False, f"жителя «{imya}» в городе не нашёл"
    zanyal = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if zanyal == imya:
        return True, f"{imya} и так на этом месте"
    if zanyal:
        return False, f"место занято: {zanyal} — сперва уволь"
    d["кто_сидит"] = {"имя": imya, "с": _teper()}
    d.setdefault("трудовая_история", []).append(
        {"когда": _teper(), "что": "принят", "кто": imya,
         "кем": kem, "почему": pochemu})
    if not _pisat(put, d):
        return False, "документ не записался"
    _otmetka(imya, d)
    return True, f"{imya} принят на «{d.get('название', post_id)}»"


def uvolit(post_id: str, kem: str = "Шеф", pochemu: str = "") -> tuple:
    put = put_posta(post_id)
    d = _chitat(put)
    if d is None:
        return False, "такой должности нет"
    imya = ((d.get("кто_сидит") or {}).get("имя") or "").strip()
    if not imya:
        return True, "место и так свободно"
    d["кто_сидит"] = None
    d.setdefault("трудовая_история", []).append(
        {"когда": _teper(), "что": "уволен", "кто": imya,
         "кем": kem, "почему": pochemu})
    if not _pisat(put, d):
        return False, "документ не записался"
    _otmetka(imya, None)
    return True, f"{imya} уволен, место свободно"


def snesti(post_id: str) -> tuple:
    """Снести должность совсем. Занятую не сносим — сперва уволь."""
    d = chitat(post_id)
    if d is None:
        return False, "такой должности нет"
    if ((d.get("кто_сидит") or {}).get("имя") or "").strip():
        return False, "место занято — сперва уволь"
    try:
        put = put_posta(post_id)
        put.unlink()
        try:
            put.parent.rmdir()
        except OSError:
            pass
        return True, "должность снесена"
    except Exception as e:
        return False, str(e)


def kto_sidit(post_id: str) -> str:
    d = chitat(post_id)
    return ((d or {}).get("кто_сидит") or {}).get("имя", "") if d else ""


def kto_na_slote(ceh: str, slot: str) -> str:
    """Кто сидит на месте цеха. Ищем пост по привязке, а не по имени
    папки: пост мог быть заведён и вручную, с другим id."""
    if not POSTY.exists():
        return ""
    for d in sorted(POSTY.iterdir()):
        p = _chitat(d / "пост.json")
        if not p:
            continue
        if p.get("цех") == ceh and p.get("слот") == slot:
            return ((p.get("кто_сидит") or {}).get("имя") or "").strip()
    return ""


def est_post_na_slote(ceh: str, slot: str) -> bool:
    if not POSTY.exists():
        return False
    for d in sorted(POSTY.iterdir()):
        p = _chitat(d / "пост.json")
        if p and p.get("цех") == ceh and p.get("слот") == slot:
            return True
    return False
'''


PULT_PY = r'''# -*- coding: utf-8 -*-
# STANDART_RABOTY_V1
"""
ПУЛЬТ РАБОТЫ — запасной ход к тем же четырём рукам.

    python rabota_pult.py                       все места города
    python rabota_pult.py --svobodnye           только свободные
    python rabota_pult.py --iskat трейдер       поиск по названию
    python rabota_pult.py --zavesti ID --ceh X --slot A06 --nazvanie "..."
    python rabota_pult.py --prinyat ID Имя
    python rabota_pult.py --uvolit ID --pochemu "..."
    python rabota_pult.py --snesti ID
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ГОРОД"))
import rabota as R   # noqa: E402


def pokazat(a):
    v = R.mesta()
    if a.iskat:
        q = a.iskat.lower()
        v = [m for m in v if q in (m["название"] + m["цех"] + m["слот"]).lower()]
    if a.svobodnye:
        v = [m for m in v if not m["кто_сидит"]]
    s = R.schet()
    print("═" * 66)
    print(f"МЕСТА ГОРОДА · всего {s['всего']} · с должностью "
          f"{s['с должностью']} · занято {s['занято']} · "
          f"свободно {s['свободно']} · без должности {s['без должности']}")
    print("═" * 66)
    kvartal = None
    for m in sorted(v, key=lambda x: (x["квартал"], x["цех"], x["слот"])):
        if m["квартал"] != kvartal:
            kvartal = m["квартал"]
            print(f"\n  {kvartal or '(без квартала)'}")
        kto = m["кто_сидит"] or ("— свободно" if m["есть_пост"]
                                 else "— должности нет")
        print(f"    {m['цех']:<16} {m['слот']:<6} {m['название']:<26} {kto}")
        print(f"      id: {m['id']}")
    print("\n" + "─" * 66)
    print("принять:  python rabota_pult.py --prinyat <id> Имя")
    print("уволить:  python rabota_pult.py --uvolit <id>")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iskat", default="")
    ap.add_argument("--svobodnye", action="store_true")
    ap.add_argument("--zavesti", metavar="ID")
    ap.add_argument("--ceh", default="")
    ap.add_argument("--slot", default="")
    ap.add_argument("--kvartal", default="")
    ap.add_argument("--nazvanie", default="")
    ap.add_argument("--prinyat", nargs=2, metavar=("ID", "ИМЯ"))
    ap.add_argument("--uvolit", metavar="ID")
    ap.add_argument("--snesti", metavar="ID")
    ap.add_argument("--pochemu", default="")
    a = ap.parse_args()

    if a.zavesti:
        ok, msg = R.zavesti(a.zavesti, {
            "название": a.nazvanie, "квартал": a.kvartal,
            "цех": a.ceh, "слот": a.slot})
        print(("✓ " if ok else "✗ ") + msg + "\n")
    if a.prinyat:
        ok, msg = R.prinyat(a.prinyat[0], a.prinyat[1], pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg + "\n")
    if a.uvolit:
        ok, msg = R.uvolit(a.uvolit, pochemu=a.pochemu)
        print(("✓ " if ok else "✗ ") + msg + "\n")
    if a.snesti:
        ok, msg = R.snesti(a.snesti)
        print(("✓ " if ok else "✗ ") + msg + "\n")

    pokazat(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# ── правка Закона Пары: спрашиваем ПОСТ ───────────────────────
STAROE_REG = '''    try:
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
'''
NOVOE_REG = '''    try:
        # STANDART_RABOTY_V1: правду о найме говорит ПОСТ — единый
        # реестр мест города. Поста на этом слоте нет — работаем
        # по-старому, по mask.json, чтобы сидящие не выпали.
        import sys as _sys
        _g = str(CITY.parent / "ГОРОД")
        if _g not in _sys.path:
            _sys.path.insert(0, _g)
        import rabota as _rab
        if _rab.est_post_na_slote(ceh_id, slot):
            _imya = _rab.kto_na_slote(ceh_id, slot)
            if not _imya:
                return None            # пост говорит: место свободно
            _z = _zhitel_po_imeni(_imya)
            if _z is None:
                return None            # в посте имя, а жителя нет
            _z["цех"] = ceh_id
            _z["слот"] = slot
            return _z
    except Exception:
        pass
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  ✗ {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ {imya}: не компилируется ({e}) — НЕ пишу")
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
        print(f"  {put.name}: ✓ ляжет")
        return True
    put.parent.mkdir(parents=True, exist_ok=True)
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
        print("  cartridge_registry.py: уже на посты")
        return True
    if tekst.count(STAROE_REG) != 1:
        print("  ✗ cartridge_registry.py: не вижу вчерашней вставки — "
              "не трогаю. Покажи файл.")
        return False
    tekst = tekst.replace(STAROE_REG, NOVOE_REG, 1)
    tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
    if not proverit_python(tekst, "cartridge_registry.py"):
        return False
    if suho:
        print("  cartridge_registry.py: ✓ переведётся на посты")
        return True
    shutil.copy2(REG, REG.with_suffix(REG.suffix + BAK))
    REG.write_text(tekst, encoding="utf-8")
    print("  cartridge_registry.py: ✓ переведён на посты")
    return True


def snesti_dubl(suho: bool):
    """Вчерашний дубль: Биржа/rabota.py и должность.json при слотах."""
    dubl = [BIRZHA / "rabota.py"]
    dubl += sorted(CITY.rglob("должность.json"))
    if not dubl or not any(p.exists() for p in dubl):
        print("  дубля нет — чисто")
        return
    for p in dubl:
        if not p.exists():
            continue
        if suho:
            print(f"  снесу: {p.relative_to(KOREN)}")
            continue
        p.replace(p.with_suffix(p.suffix + ".snesen"))
        print(f"  снесён: {p.relative_to(KOREN)} (лежит рядом как .snesen)")


# Известная сшивка: посты, заведённые 07.08, — это те же самые места
# торгового цеха. Без привязки они бы висели в списке ВТОРОЙ раз,
# рядом со слотами A06/A07/A08. Проставляем квартал/цех/слот.
SSHIVKA = {
    "treyder_proboy": ("Биржа", "торговый_хаос", "A06"),
    "treyder_ranniy": ("Биржа", "торговый_хаос", "A07"),
    "treyder_otkat":  ("Биржа", "торговый_хаос", "A08"),
}


def sshit(suho: bool):
    import json
    for pid, (kv, ceh, slot) in SSHIVKA.items():
        p = CITY / "посты" / pid / "пост.json"
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            print(f"  ✗ {pid}: не читается — пропускаю")
            continue
        if d.get("цех") and d.get("слот"):
            print(f"  {pid}: уже привязан")
            continue
        d["квартал"], d["цех"], d["слот"] = kv, ceh, slot
        if suho:
            print(f"  {pid}: ✓ привяжется к {ceh}/{slot}")
            continue
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print(f"  {pid}: ✓ привязан к {ceh}/{slot}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suho", action="store_true")
    a = ap.parse_args()

    if not CITY.exists():
        print("✗ не вижу GRONDHEIM_CITY — запускай из КОРНЯ репо")
        return 1

    print("═" * 62)
    print("СТАНДАРТ РАБОТЫ" + ("   [СУХОЙ ПРОГОН]" if a.suho else ""))
    print("═" * 62)

    ok = True
    print("\nмеханизм:")
    ok &= polozhit(GOROD / "rabota.py", RABOTA_PY, a.suho)
    print("\nпульт:")
    ok &= polozhit(KOREN / "rabota_pult.py", PULT_PY, a.suho)
    print("\nЗакон Пары:")
    ok &= pravit_registry(a.suho)
    print("\nсшивка старых постов со слотами:")
    sshit(a.suho)
    print("\nвчерашний дубль:")
    snesti_dubl(a.suho)

    if not ok:
        print("\n⚠ что-то не легло — дальше не иду")
        return 1
    if a.suho:
        print("\nСухой прогон прошёл. Ставить: "
              "python postavit_standart_raboty.py")
        return 0

    print("\n" + "─" * 62)
    print("Смотреть места:      python rabota_pult.py")
    print("Только свободные:    python rabota_pult.py --svobodnye")
    print("Найти:               python rabota_pult.py --iskat трейдер")
    print()
    print("Старая студия подцепится, если положишь путь к ней строкой")
    print("в файл ГОРОД/студия_путь.txt — тогда её цеха появятся в")
    print("списке как места без должности.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
