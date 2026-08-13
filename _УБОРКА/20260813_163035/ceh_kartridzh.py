#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# KARTRIDZH_CEHA_V1
"""
КАРТРИДЖ ЦЕХА — размножить цех один в один.

Двойной щелчок по `ЦЕХ.bat`, из корня города.

ЧТО ДЕЛАЕТ

    Показывает цеха Биржи, спрашивает, какой размножить и как назвать
    новый. Дальше сам:

      · копирует папку цеха со всеми слотами, мозгами, промптами и
        знаниями — один в один;
      · правит манифест копии: имя цеха, название, отметка, от кого
        пошёл;
      · заводит вакансии для его слотов на Странице Работы;
      · оставляет копию ПУСТОЙ: без данных, журналов и стола. Новый цех
        начинает свою жизнь, а не донашивает чужие позиции.

    Ничего не удаляет и оригинал не трогает.

ПОЧЕМУ ЭТО РАБОТАЕТ БЕЗ ПРАВОК КОДА

    Совет сканирует цех и зовёт всех, у кого есть мозг (Закон
    Картриджа). Стол у каждого цеха свой. Кабинет открывается по адресу
    цеха и говорит Совету, какой сегодня. Значит копия — самостоятельный
    картридж: вставил и работает, вынул папку — его нет.

ПРО ПРИСТАВКИ ПОЛЕЙ

    Внутри цеха у трейдеров разные приставки решения (brut, avan,
    cons) — иначе они писали бы в одну строку стола. МЕЖДУ цехами
    приставки могут совпадать: стол-то у каждого свой. Поэтому копия
    один в один — законна.

ЧЕГО НЕ ДЕЛАЕТ

    Не сажает людей. Вакансии заводятся пустыми — кого посадить, решишь
    на Странице Работы. И не трогает локацию: копия наследует здание
    оригинала, поменяешь в манифесте, если надо.
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
CEHA = KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха"

# что НЕ копируем: это нажитое оригиналом, не картридж
NE_KOPIRUEM = {"данные", "журналы", "__pycache__", "кадры"}
NE_FAYLY = {".pyc", ".log"}
# копии, оставленные патчами, картриджу не нужны — это следы починок
# оригинала, а не его устройство


def skazat(s=""):
    print(s, flush=True)


def cherta():
    skazat("─" * 62)


def _sprosit(vopros: str) -> str:
    try:
        return input(vopros).strip()
    except Exception:
        return ""


def cheha_spisok() -> list:
    if not CEHA.is_dir():
        return []
    out = []
    for d in sorted(CEHA.iterdir()):
        if not d.is_dir() or not (d / "manifest.json").exists():
            continue
        try:
            m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        except Exception:
            m = {}
        sloty = [s.get("слот") for s in (m.get("слоты") or []) if s.get("слот")]
        s_mozgom = [s for s in sloty
                    if (d / "слоты" / s / "мозг.py").exists()]
        out.append({"имя": d.name, "название": m.get("название", d.name),
                    "слотов": len(sloty), "с_мозгом": len(s_mozgom),
                    "папка": d})
    return out


def _chistoe_imya(s: str) -> str:
    s = (s or "").strip().replace(" ", "_")
    s = re.sub(r"[^0-9A-Za-zА-Яа-яёЁ_\-]", "", s)
    return s


def razmnozhit(iz: dict, novoe_imya: str, novoe_nazvanie: str) -> bool:
    cel = CEHA / novoe_imya
    if cel.exists():
        skazat(f"  x цех «{novoe_imya}» уже есть — выбери другое имя")
        return False

    # ── 1. копия папки, без нажитого ──
    def _mimo(dirpath, imena):
        propustit = set()
        for i in imena:
            if (i in NE_KOPIRUEM or Path(i).suffix.lower() in NE_FAYLY
                    or ".bak" in i or i.endswith(".snesen")):
                propustit.add(i)
        return propustit

    shutil.copytree(iz["папка"], cel, ignore=_mimo)
    faylov = sum(1 for _ in cel.rglob("*") if _.is_file())
    skazat(f"  + папка скопирована: {faylov} файлов")

    # ── 2. манифест копии ──
    mf = cel / "manifest.json"
    try:
        m = json.loads(mf.read_text(encoding="utf-8"))
    except Exception as e:
        skazat(f"  x манифест копии не читается: {e}")
        return False
    m["название"] = novoe_nazvanie or novoe_imya
    m["_от_кого"] = iz["имя"]
    m["_заведён"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    m["_note"] = (f"Картридж-цех, снят с «{iz['имя']}» один в один. "
                  f"Слоты те же; стол, журналы и данные — свои, с нуля. "
                  f"Совет находит его сканером (Закон Картриджа).")
    mf.write_text(json.dumps(m, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    skazat(f"  + манифест поправлен: «{m['название']}»")

    # ── 3. вакансии ──
    try:
        _g = str(KOREN / "ГОРОД")
        if _g not in sys.path:
            sys.path.insert(0, _g)
        import rabota as R
    except Exception as e:
        skazat(f"  ! механизм работы не поднялся ({e}) — вакансии заведи "
               f"сам на Странице Работы")
        return True

    zavedeno = 0
    for s in (m.get("слоты") or []):
        slot = s.get("слот")
        if not slot:
            continue
        pid = R.id_dlya_slota(novoe_imya, slot)
        ok, _msg = R.zavesti(pid, {
            "название": f"{s.get('роль', slot)} · {m['название']}",
            "квартал": m.get("квартал", ""), "цех": novoe_imya,
            "слот": slot, "локация": m.get("здание", ""),
            "чем_занят": s.get("роль", ""),
            "судья": m.get("судья", ""), "движок": "мозг.py",
        })
        if ok:
            zavedeno += 1
    skazat(f"  + вакансий заведено: {zavedeno} (пустые, людей посадишь сам)")
    return True


def main() -> int:
    skazat("=" * 62)
    skazat("КАРТРИДЖ ЦЕХА")
    skazat("=" * 62)

    if not CEHA.is_dir():
        skazat("\nx не вижу цеха Биржи — запускай из корня города")
        return 1

    spisok = cheha_spisok()
    if not spisok:
        skazat("\nx цехов не нашёл")
        return 1

    skazat("\nЦеха Биржи:\n")
    for i, c in enumerate(spisok, 1):
        skazat(f"  {i:>2}. {c['имя']:<20} {c['название'][:28]:<30} "
               f"слотов {c['слотов']} (с мозгом {c['с_мозгом']})")

    skazat("\n  номер цеха, который размножить · Enter — выйти")
    otvet = _sprosit("\n> ")
    if not otvet.isdigit() or not (1 <= int(otvet) <= len(spisok)):
        skazat("вышел, ничего не трогал")
        return 0
    iz = spisok[int(otvet) - 1]

    skazat(f"\nРазмножаю «{iz['имя']}».")
    skazat("Как назвать новый цех? Это имя папки — коротко, без пробелов.")
    skazat("Например: торговый_муж")
    imya = _chistoe_imya(_sprosit("\nимя папки > "))
    if not imya:
        skazat("без имени не могу — вышел")
        return 0

    skazat("\nЧеловеческое название (можно с пробелами). Enter — как имя.")
    nazvanie = _sprosit("название > ") or imya

    cherta()
    skazat(f"из:    {iz['имя']}  ({iz['слотов']} слотов)")
    skazat(f"в:     {imya}")
    skazat(f"звать: {nazvanie}")
    skazat("не копирую: данные, журналы, стол — новый цех живёт своей")
    skazat("жизнью, а не донашивает чужие позиции")
    cherta()
    if _sprosit("делаем? [да / Enter — нет]: ").strip().lower() not in (
            "да", "y", "yes", "д"):
        skazat("отменил")
        return 0

    skazat("")
    if not razmnozhit(iz, imya, nazvanie):
        return 1

    cherta()
    skazat("Готово. Что дальше:")
    skazat(f"  1. открой кабинет нового цеха: /torg/{imya}")
    skazat("  2. на Странице Работы посади в него людей")
    skazat("  3. жми РЫНОК — Совет соберёт ЭТОТ цех, со своим столом")
    skazat("")
    skazat("Не понравился — просто удали папку "
           f"GRONDHEIM_CITY/Биржа/цеха/{imya},")
    skazat("и его как не бывало. Это и есть картридж.")
    return 0


if __name__ == "__main__":
    try:
        kod = main()
    except Exception as e:
        skazat(f"\nx что-то пошло не так: {type(e).__name__}: {e}")
        kod = 1
    if sys.platform == "win32":
        try:
            input("\nEnter — закрыть окно.")
        except Exception:
            pass
    sys.exit(kod)
