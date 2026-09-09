# -*- coding: utf-8 -*-
# POSTAVIT_KLYUCH_V1 — ключ начинает работать
"""
ПЕРВЫЙ ПАТЧ КЛЮЧА · кладёт модуль и дописывает ключ туда, где
человека ищут ПОПЕРЁК города

ЧТО ДЕЛАЕТ, ровно две вещи:

 1. Кладёт ГОРОД/klyuch.py — одно место на весь город, которое
    отвечает на вопросы «кто это по ключу» и «какой ключ у этого».
    Ключ = отпечаток печати создателя (_Creator_Seal_Hash), тот, что
    посчитан при рождении и не меняется никогда.

 2. Дописывает поле "ключ" РЯДОМ с именем в четырёх местах:
        GRONDHEIM_CITY/посты/*/пост.json      (кто_сидит, трудовая_история)
        GRONDHEIM_CITY/Академия/ученики.json  (места[].житель)
        GRONDHEIM_CITY/Академия/выпускники.json
        GRONDHEIM_CITY/посты/mayak/журнал.jsonl
    Около шестидесяти записей. Имя НЕ убирается — ключ встаёт рядом.

ЧЕГО НЕ ДЕЛАЕТ (сознательно, решение Шефа):
 · не трогает дневники мест и прогоны — там рутина и следы тестов,
   плюс дневник A06 загрязнён прежним жителем: проставить там ключ
   значило бы УГАДАТЬ, кто это был, и объявить догадку фактом;
 · не трогает стенограммы в ковчеге — они и так лежат в папке своего
   жителя, адрес у них есть;
 · не переименовывает папки ковчега и ничего не удаляет;
 · не даёт ключу никаких прав: ключ находит, а не пускает.

БЕЗОПАСНОСТЬ:
 · перед каждой правкой кладётся .bak_klyuch рядом с файлом;
 · идемпотентен — второй прогон ничего не меняет;
 · неизвестное имя ("Шеф", "академия-ученик", пустое) пропускается
   молча: ключ ставится ТОЛЬКО при точном совпадении с жителем ковчега;
 · `--suho` — показать, что было бы сделано, не трогая диск.

    python postavit_klyuch.py --suho
    python postavit_klyuch.py

`шесть·проверено·до·корня`
"""
import json
import shutil
import sys
from pathlib import Path

MARKER = "KLYUCH_V_SLEDAH_V1"

_HERE = Path(__file__).resolve().parent
_REPO = _HERE
CITY = _REPO / "GRONDHEIM_CITY"
KOVCHEG = CITY / "жители" / "ковчег"
POSTY = CITY / "посты"
AKADEMIA = CITY / "Академия"
GOROD = _REPO / "ГОРОД"

SUHO = "--suho" in sys.argv
POLE = "ключ"


# ═══════════════════════════════════════════════════════════
# МОДУЛЬ, КОТОРЫЙ КЛАДЁМ
# ═══════════════════════════════════════════════════════════

MODUL = '''# -*- coding: utf-8 -*-
# GOROD_KLYUCH_V1 — ключ клетки
"""
КЛЮЧ · одно место на весь город

Ключ клетки — ОТПЕЧАТОК ПЕЧАТИ СОЗДАТЕЛЯ (_Creator_Seal_Hash из
паспорта). Посчитан один раз, при рождении, из печати — и не
пересчитывается никогда. Имя может повториться (Илья может быть
три), номер могут переставить — а печать у каждого своя.

ЧТО КЛЮЧ ДЕЛАЕТ: находит. Назови ключ — получишь, кто это.
ЧЕГО НЕ ДЕЛАЕТ: не хранит ничего, ничего не открывает и не пускает.
Что кому можно — решают веса и области, не ключ.

И отдельно, закон из реестра картриджей, он в силе: ключ отвечает
на вопрос «КТО ЭТО» и никогда на «кем он работает». Роль по-прежнему
решает пара и маска.

    import klyuch
    klyuch.klyuch_zhitelya("Илья")   -> "bc9dd782..."
    klyuch.kto("bc9dd782...")        -> "Илья"
    klyuch.pasport("bc9dd782...")    -> паспорт словарём
    klyuch.dom("bc9dd782...")        -> папка жителя
    klyuch.vse()                     -> [{имя, ключ, id}, ...]

Список берётся с диска при каждом обращении (Закон Картриджа —
реестра в коде не держим). Кто завёлся в ковчеге — тот и найдётся.

`шесть·проверено·до·корня`
"""
import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent      # ГОРОД/
_REPO = _HERE.parent
KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
KATALOG = _REPO / "00_REGISTRY_NFT" / "catalog.json"

POLE_KLYUCHA = "_Creator_Seal_Hash"


def _chitat(p: Path):
    for kod in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return json.loads(p.read_text(encoding=kod))
        except Exception:
            continue
    return None


def _zhiteli() -> list:
    """Все жители ковчега с их ключами. Нет паспорта — нет жителя."""
    out = []
    if not KOVCHEG.exists():
        return out
    for d in sorted(KOVCHEG.iterdir()):
        if not d.is_dir():
            continue
        p = d / "passport.json"
        if not p.exists():
            continue
        pasp = _chitat(p) or {}
        k = pasp.get(POLE_KLYUCHA, "")
        if not k:
            continue
        out.append({
            "имя": pasp.get("Official_Name") or d.name,
            "папка": d.name,
            "ключ": k,
            "id": pasp.get("ID_Object", ""),
            "дом": d,
        })
    return out


def vse() -> list:
    """Список всех: имя, ключ, id. Без домов — для показа."""
    return [{"имя": z["имя"], "ключ": z["ключ"], "id": z["id"]}
            for z in _zhiteli()]


def klyuch_zhitelya(imya: str) -> str:
    """Ключ по имени. Нет такого — пустая строка, честно.

    Имя пока однозначно (все девятнадцать разные). Заведётся второй
    с тем же именем — эта функция станет неоднозначной, и тогда
    звать нужно будет уже по ключу. Здесь это не прячется.
    """
    if not imya:
        return ""
    for z in _zhiteli():
        if imya in (z["имя"], z["папка"]):
            return z["ключ"]
    return ""


def odnoimenniki(imya: str) -> list:
    """Все, кто носит это имя. Больше одного — имя перестало быть
    адресом, зовите по ключу."""
    return [z["ключ"] for z in _zhiteli()
            if imya in (z["имя"], z["папка"])]


def kto(k: str) -> str:
    """Имя по ключу. Нет такого ключа — пустая строка."""
    if not k:
        return ""
    for z in _zhiteli():
        if z["ключ"] == k:
            return z["имя"]
    return ""


def dom(k: str):
    """Папка жителя по ключу. Нет — None."""
    for z in _zhiteli():
        if z["ключ"] == k:
            return z["дом"]
    return None


def pasport(k: str) -> dict:
    """Паспорт по ключу. Нет — пустой словарь."""
    d = dom(k)
    if d is None:
        return {}
    return _chitat(d / "passport.json") or {}


def mesta() -> list:
    """Места города из каталога: у них тоже есть ключи."""
    kat = _chitat(KATALOG)
    if not isinstance(kat, list):
        return []
    return [{"имя": x.get("Official_Name", ""),
             "ключ": x.get(POLE_KLYUCHA, ""),
             "id": x.get("ID_Object", "")}
            for x in kat if x.get("Object_Type_Class") == "location"]


if __name__ == "__main__":
    print("ЖИТЕЛИ:")
    for z in vse():
        print(f"  {z['имя']:12} {z['ключ'][:16]}  {z['id']}")
    print()
    print("МЕСТА:")
    for m in mesta():
        print(f"  {m['имя']:24} {m['ключ'][:16]}  {m['id']}")
'''


# ═══════════════════════════════════════════════════════════
# ОБЩЕЕ
# ═══════════════════════════════════════════════════════════

def _chitat(p: Path):
    for kod in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return json.loads(p.read_text(encoding=kod))
        except Exception:
            continue
    return None


def _pisat(p: Path, data):
    if SUHO:
        return
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                 encoding="utf-8")


def _bak(p: Path):
    b = p.with_suffix(p.suffix + ".bak_klyuch")
    if not b.exists() and not SUHO:
        shutil.copy2(p, b)


def karta_klyuchey() -> dict:
    """имя (и имя папки) -> ключ. Только те, у кого ключ есть."""
    karta = {}
    if not KOVCHEG.exists():
        return karta
    for d in sorted(KOVCHEG.iterdir()):
        if not d.is_dir():
            continue
        p = d / "passport.json"
        if not p.exists():
            continue
        pasp = _chitat(p) or {}
        k = pasp.get("_Creator_Seal_Hash", "")
        if not k:
            continue
        karta[d.name] = k
        imya = pasp.get("Official_Name")
        if imya:
            karta[imya] = k
    return karta


def _dopisat_zapis(z: dict, polya: tuple, karta: dict) -> bool:
    """Ставит ключ рядом с именем в одной записи. Уже стоит — не
    трогает. Имя незнакомое — пропускает молча."""
    if not isinstance(z, dict) or z.get(POLE):
        return False
    for pole in polya:
        imya = z.get(pole)
        if isinstance(imya, str) and imya in karta:
            z[POLE] = karta[imya]
            return True
    return False


# ═══════════════════════════════════════════════════════════
# ЧЕТЫРЕ МЕСТА
# ═══════════════════════════════════════════════════════════

def posty(karta: dict) -> int:
    """пост.json: кто_сидит + трудовая_история[].кто.

    "кем" (обычно Шеф) НЕ трогаем — он не житель ковчега.
    """
    if not POSTY.exists():
        return 0
    tronuto = 0
    for d in sorted(POSTY.iterdir()):
        if not d.is_dir():
            continue
        p = d / "пост.json"
        if not p.exists():
            continue
        post = _chitat(p)
        if not isinstance(post, dict):
            continue
        izmenili = 0
        kto_sidit = post.get("кто_сидит")
        if (isinstance(kto_sidit, str) and kto_sidit in karta
                and not post.get("ключ_сидящего")):
            post["ключ_сидящего"] = karta[kto_sidit]
            izmenili += 1
        for z in post.get("трудовая_история", []) or []:
            if _dopisat_zapis(z, ("кто",), karta):
                izmenili += 1
        if izmenili:
            _bak(p)
            _pisat(p, post)
            tronuto += izmenili
            print(f"    {d.name}/пост.json — {izmenili}")
    return tronuto


def spisok_v_fajle(p: Path, pole_spiska: str, karta: dict) -> int:
    """ученики.json / выпускники.json: {pole_spiska: [ {житель: ...} ]}"""
    if not p.exists():
        return 0
    d = _chitat(p)
    if not isinstance(d, dict):
        return 0
    spisok = d.get(pole_spiska)
    if not isinstance(spisok, list):
        return 0
    izmenili = sum(1 for z in spisok
                   if _dopisat_zapis(z, ("житель",), karta))
    if izmenili:
        _bak(p)
        _pisat(p, d)
        print(f"    {p.name} — {izmenili}")
    return izmenili


def zhurnal_mayaka(karta: dict) -> int:
    """журнал.jsonl: построчно, поле "кто". Там бывают не-жители
    ("академия-ученик") — их пропускаем."""
    p = POSTY / "mayak" / "журнал.jsonl"
    if not p.exists():
        return 0
    stroki = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    novye, izmenili = [], 0
    for s in stroki:
        t = s.strip()
        if not t:
            novye.append(s)
            continue
        try:
            z = json.loads(t)
        except Exception:
            novye.append(s)
            continue
        if _dopisat_zapis(z, ("кто",), karta):
            izmenili += 1
        novye.append(json.dumps(z, ensure_ascii=False))
    if izmenili:
        _bak(p)
        if not SUHO:
            p.write_text("\n".join(novye) + "\n", encoding="utf-8")
        print(f"    mayak/журнал.jsonl — {izmenili}")
    return izmenili


# ═══════════════════════════════════════════════════════════

def polozhit_modul() -> str:
    p = GOROD / "klyuch.py"
    if p.exists() and MARKER in p.read_text(encoding="utf-8", errors="ignore"):
        return "уже лежит"
    if p.exists():
        _bak(p)
    if not SUHO:
        GOROD.mkdir(parents=True, exist_ok=True)
        p.write_text(MODUL.replace("GOROD_KLYUCH_V1",
                                   f"GOROD_KLYUCH_V1 · {MARKER}"),
                     encoding="utf-8")
    return "положен"


def main():
    print()
    print("ПЕРВЫЙ ПАТЧ КЛЮЧА" + ("  · СУХОЙ ПРОГОН, диск не трогаю" if SUHO else ""))
    print("корень:", _REPO)
    print()

    if not KOVCHEG.exists():
        print("!! ковчега нет — запускать надо из корня репы")
        return

    karta = karta_klyuchey()
    lyudi = len({v for v in karta.values()})
    print(f"1. КЛЮЧИ ИЗ КОВЧЕГА: {lyudi} жителей с печатью")
    if not lyudi:
        print("   !! ни одного ключа — дальше идти незачем")
        return

    print()
    print("2. МОДУЛЬ ГОРОД/klyuch.py:", polozhit_modul())

    print()
    print("3. ДОПИСКА КЛЮЧА РЯДОМ С ИМЕНЕМ:")
    vsego = 0
    vsego += posty(karta)
    vsego += spisok_v_fajle(AKADEMIA / "ученики.json", "места", karta)
    vsego += spisok_v_fajle(AKADEMIA / "выпускники.json", "выпуски", karta)
    vsego += zhurnal_mayaka(karta)
    if not vsego:
        print("    нечего дописывать — всё уже с ключами")

    print()
    print(f"ИТОГО записей тронуто: {vsego}")
    if SUHO:
        print("Сухой прогон: на диске НИЧЕГО не изменилось.")
    else:
        print("Рядом с каждым правленым файлом лежит .bak_klyuch")
    print("Имена на месте, ключ встал рядом. Прогони ещё раз — "
          "ничего не изменится.")
    print()


if __name__ == "__main__":
    main()
