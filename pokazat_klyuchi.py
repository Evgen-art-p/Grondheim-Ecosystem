# -*- coding: utf-8 -*-
# POKAZAT_KLYUCHI_V1 — смотрелец ключей города
"""
СМОТРЕЛЕЦ КЛЮЧЕЙ · только читает, НИЧЕГО НЕ МЕНЯЕТ

Зачем. Прежде чем учить город искать по ключу, надо увидеть,
что у нас на самом деле лежит:

  1. ПЕЧАТИ — у кого есть Creator_Seal и его отпечаток, сходится ли
     отпечаток с печатью по счёту, уникальны ли они;
  2. КАТАЛОГ — сходятся ли ковчег и 00_REGISTRY_NFT/catalog.json;
  3. СЛЕДЫ — где в городе записи подписаны ИМЕНЕМ, а ключа рядом нет.
     Это и есть будущий объём дописки.

Ничего не пишет, ничего не удаляет, ни одного файла не трогает.
Запускать сколько угодно раз.

    python pokazat_klyuchi.py            — общий отчёт
    python pokazat_klyuchi.py --podrobno — плюс список файлов со следами

`шесть·проверено·до·корня`
"""
import json
import sys
import hashlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE

KOVCHEG = _REPO / "GRONDHEIM_CITY" / "жители" / "ковчег"
KATALOG = _REPO / "00_REGISTRY_NFT" / "catalog.json"
CITY = _REPO / "GRONDHEIM_CITY"

# папки, куда не ходим: бэкапы, уборка, архивы чистки
PROPUSK = ("_УБОРКА", "_ARCHIVE", "_OLD", "_АРХИВ_ЧИСТКИ", ".git",
           "__pycache__", "node_modules")

# поля, в которых город обычно подписывает, ЧЕЙ это след
POLYA_IMENI = ("житель", "имя", "кто", "агент", "хозяин", "автор",
               "подпись", "student", "zhitel", "владелец", "от_кого")

# поля, которые уже могли бы быть ключом
POLYA_KLYUCHA = ("ключ", "печать", "отпечаток", "ID_Object",
                 "_Creator_Seal_Hash", "klyuch", "hash")


def _chitat_json(p: Path):
    for kod in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return json.loads(p.read_text(encoding=kod))
        except Exception:
            continue
    return None


def _otpechatok(pechat: str) -> str:
    return hashlib.sha256((pechat or "").encode("utf-8")).hexdigest()


def _korotko(s, n=14):
    s = str(s or "—")
    return s if len(s) <= n else s[:n]


# ═══════════════════════════════════════════════════════════
# 1. ПЕЧАТИ В КОВЧЕГЕ
# ═══════════════════════════════════════════════════════════

def sobrat_kovcheg() -> list:
    """Все жители ковчега: имя папки, ID, печать, отпечаток."""
    out = []
    if not KOVCHEG.exists():
        return out
    for d in sorted(KOVCHEG.iterdir()):
        if not d.is_dir():
            continue
        p = d / "passport.json"
        if not p.exists():
            out.append({"папка": d.name, "паспорт": False})
            continue
        pasp = _chitat_json(p) or {}
        pechat = pasp.get("Creator_Seal", "")
        out.append({
            "папка": d.name,
            "паспорт": True,
            "имя": pasp.get("Official_Name", ""),
            "id": pasp.get("ID_Object", ""),
            "печать": pechat,
            "отпечаток": pasp.get("_Creator_Seal_Hash", ""),
            "сходится": (bool(pechat) and
                         _otpechatok(pechat) == pasp.get("_Creator_Seal_Hash", "")),
        })
    return out


def pokazat_pechati(zhiteli: list):
    print("═" * 66)
    print("1. ПЕЧАТИ В КОВЧЕГЕ")
    print("═" * 66)
    if not zhiteli:
        print("  ковчег не найден:", KOVCHEG)
        return
    print(f"  {'папка':12} {'имя':12} {'ID':18} {'отпечаток':14} счёт")
    bez_pasporta, bez_pechati, ne_shoditsya = [], [], []
    for z in zhiteli:
        if not z.get("паспорт"):
            bez_pasporta.append(z["папка"])
            print(f"  {z['папка']:12} {'—':12} {'ПАСПОРТА НЕТ'}")
            continue
        if not z.get("печать"):
            bez_pechati.append(z["папка"])
        if z.get("печать") and not z.get("сходится"):
            ne_shoditsya.append(z["папка"])
        znak = "OK" if z.get("сходится") else ("нет печати" if not z.get("печать") else "РАСХОД")
        print(f"  {z['папка']:12} {_korotko(z.get('имя'),12):12} "
              f"{_korotko(z.get('id'),18):18} {_korotko(z.get('отпечаток'),14):14} {znak}")

    est = [z for z in zhiteli if z.get("паспорт")]
    otp = [z["отпечаток"] for z in est if z.get("отпечаток")]
    print()
    print(f"  всего папок: {len(zhiteli)} · с паспортом: {len(est)}")
    print(f"  отпечатков: {len(otp)} · уникальных: {len(set(otp))}")
    if len(otp) != len(set(otp)):
        vidno = {}
        for z in est:
            vidno.setdefault(z.get("отпечаток"), []).append(z["папка"])
        for k, v in vidno.items():
            if len(v) > 1:
                print(f"  !! ОДИН ОТПЕЧАТОК У РАЗНЫХ: {v}")
    if bez_pasporta:
        print(f"  !! без паспорта: {bez_pasporta}")
    if bez_pechati:
        print(f"  !! без печати: {bez_pechati}")
    if ne_shoditsya:
        print(f"  !! отпечаток НЕ сходится с печатью: {ne_shoditsya}")
        print("     (значит печать правили после рождения — разобраться!)")


# ═══════════════════════════════════════════════════════════
# 2. КАТАЛОГ
# ═══════════════════════════════════════════════════════════

def pokazat_katalog(zhiteli: list):
    print()
    print("═" * 66)
    print("2. КАТАЛОГ 00_REGISTRY_NFT")
    print("═" * 66)
    if not KATALOG.exists():
        print("  каталога нет:", KATALOG)
        return
    kat = _chitat_json(KATALOG)
    if not isinstance(kat, list):
        print("  каталог не список — не разбираю, чтобы не гадать")
        return

    po_klassam = {}
    for x in kat:
        po_klassam.setdefault(x.get("Object_Type_Class", "—"), []).append(x)
    print(f"  записей: {len(kat)}")
    for k, v in sorted(po_klassam.items()):
        print(f"    {k:12} {len(v)}")

    otp = [x.get("_Creator_Seal_Hash", "") for x in kat if x.get("_Creator_Seal_Hash")]
    print(f"  отпечатков: {len(otp)} · уникальных: {len(set(otp))}")
    ploho = [x.get("Official_Name") for x in kat
             if x.get("Creator_Seal") and
             _otpechatok(x["Creator_Seal"]) != x.get("_Creator_Seal_Hash", "")]
    if ploho:
        print(f"  !! отпечаток не сходится с печатью: {ploho}")

    # сверка с ковчегом
    kat_agent = {x.get("Official_Name"): x for x in kat
                 if x.get("Object_Type_Class") == "agent"}
    kov = {z.get("имя") or z["папка"]: z for z in zhiteli if z.get("паспорт")}
    net_v_kat = sorted(set(kov) - set(kat_agent))
    net_v_kov = sorted(set(kat_agent) - set(kov))
    print()
    print(f"  жителей в ковчеге: {len(kov)} · агентов в каталоге: {len(kat_agent)}")
    print(f"  в ковчеге, но не в каталоге: {net_v_kat or 'нет'}")
    print(f"  в каталоге, но не в ковчеге: {net_v_kov or 'нет'}")

    razoshlis = [n for n in (set(kov) & set(kat_agent))
                 if kov[n].get("отпечаток") != kat_agent[n].get("_Creator_Seal_Hash")]
    if razoshlis:
        print(f"  !! ОТПЕЧАТОК В ПАСПОРТЕ И В КАТАЛОГЕ РАЗНЫЙ: {razoshlis}")
        print("     (две правды об одном — чинить до всякой дописки)")
    else:
        print("  отпечатки паспорта и каталога сходятся у всех")


# ═══════════════════════════════════════════════════════════
# 3. СЛЕДЫ, ПОДПИСАННЫЕ ИМЕНЕМ
# ═══════════════════════════════════════════════════════════

def _zapisi_iz(p: Path):
    """Записи файла: .json (список/словарь со списком) или .jsonl."""
    if p.suffix == ".jsonl":
        out = []
        try:
            for s in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = s.strip()
                if not s:
                    continue
                try:
                    z = json.loads(s)
                except Exception:
                    continue
                if isinstance(z, dict):
                    out.append(z)
        except Exception:
            pass
        return out
    d = _chitat_json(p)
    if isinstance(d, list):
        return [x for x in d if isinstance(x, dict)]
    if isinstance(d, dict):
        out = []
        for v in d.values():
            if isinstance(v, list):
                out += [x for x in v if isinstance(x, dict)]
        return out
    return []


def naiti_sledy(imena: set, podrobno: bool = False):
    print()
    print("═" * 66)
    print("3. СЛЕДЫ, ПОДПИСАННЫЕ ИМЕНЕМ (объём будущей дописки)")
    print("═" * 66)
    if not CITY.exists():
        print("  города нет:", CITY)
        return

    fajly = []
    vsego_zapisey = 0
    vsego_imenem = 0
    vsego_s_klyuchom = 0

    for p in CITY.rglob("*"):
        if p.is_dir():
            continue
        if any(x in p.parts for x in PROPUSK):
            continue
        if p.suffix not in (".json", ".jsonl"):
            continue
        if ".bak" in p.name:
            continue
        zapisi = _zapisi_iz(p)
        if not zapisi:
            continue
        imenem = 0
        s_klyuchom = 0
        for z in zapisi:
            nashli_imya = False
            for pole in POLYA_IMENI:
                v = z.get(pole)
                if isinstance(v, str) and v in imena:
                    nashli_imya = True
                    break
            if not nashli_imya:
                continue
            imenem += 1
            if any(z.get(k) for k in POLYA_KLYUCHA):
                s_klyuchom += 1
        vsego_zapisey += len(zapisi)
        if imenem:
            fajly.append((str(p.relative_to(_REPO)), len(zapisi), imenem, s_klyuchom))
            vsego_imenem += imenem
            vsego_s_klyuchom += s_klyuchom

    fajly.sort(key=lambda x: -x[2])
    print(f"  просмотрено записей: {vsego_zapisey}")
    print(f"  подписано именем жителя: {vsego_imenem}")
    print(f"  из них уже несут ключ рядом: {vsego_s_klyuchom}")
    print(f"  ДОПИСАТЬ ПРИДЁТСЯ: {vsego_imenem - vsego_s_klyuchom}")
    print(f"  файлов со следами: {len(fajly)}")
    print()
    skolko = len(fajly) if podrobno else min(15, len(fajly))
    print(f"  {'файл':52} {'всего':>6} {'именем':>7} {'с ключом':>9}")
    for f, vsego, imenem, klyuch in fajly[:skolko]:
        print(f"  {_korotko(f, 52):52} {vsego:>6} {imenem:>7} {klyuch:>9}")
    if not podrobno and len(fajly) > skolko:
        print(f"  … ещё {len(fajly) - skolko} файлов (--podrobno покажет все)")


def main():
    podrobno = "--podrobno" in sys.argv
    print()
    print("СМОТРЕЛЕЦ КЛЮЧЕЙ · ничего не меняет, только читает")
    print("корень:", _REPO)
    print()
    zhiteli = sobrat_kovcheg()
    pokazat_pechati(zhiteli)
    pokazat_katalog(zhiteli)
    imena = set()
    for z in zhiteli:
        imena.add(z["папка"])
        if z.get("имя"):
            imena.add(z["имя"])
    naiti_sledy(imena, podrobno)
    print()
    print("═" * 66)
    print("Ничего не изменено. Это смотрелец.")
    print("═" * 66)


if __name__ == "__main__":
    main()
