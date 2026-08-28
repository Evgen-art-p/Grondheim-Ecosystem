# -*- coding: utf-8 -*-
# KONVEYER_STUDII_V1
"""
ПАТЧ · Шасси Студии — конвейер.

ЧТО КЛАДЁТ
    GRONDHEIM_CITY/Студия/конвейер.py

ГРАНИЦА, РАДИ КОТОРОЙ ВСЁ
    ШАССИ (этот файл)   собирает трубу по стыкам берёт/даёт, зовёт
                        места по очереди, ведёт стол и журнал.
                        НЕ знает ни одного провайдера. Не знает слова
                        «турбо». Не знает, что такое проба.

    ДВИЖОК ЦЕХА         руки: картинка, звук, анимация. Показывает
    (следующим камнем)  работнику его работу, крутит пробы.

    Проверка границы простая: если холостой прогон едет БЕЗ движка
    цеха — граница проведена верно. Если шасси понадобится знать про
    fal или про пробы — значит проведена неверно, и это видно сразу,
    а не через полгода.

ТРУБА СОБИРАЕТСЯ, А НЕ ОБЪЯВЛЯЕТСЯ
    Списка мест нет нигде. Место готово, когда все ключи из его
    «берёт» уже лежат на столе. Готовы несколько разом — это и есть
    параллель, объявлять её не надо.

    В старом городе то же самое требовало phases, turbo_workers,
    turbo_parallel и ветки в общем движке.

ХОЛОСТОЙ ПРОГОН
    ruki=None — руки не зовём. Места думают, отвечают JSON, но файлов
    не появляется. Приёмка честно скажет BLOCKED: путей нет. Это не
    поломка, а доказательство, что приёмка работает.

ЛИЧНОСТЬ
    Если на посту кто-то сидит — rezidenty.sobrat_dushu() даёт блок
    «КТО ТЫ» поверх бумаги. Пусто — работает чистое ремесло, без лица.
    Место не обязано быть занятым, чтобы цех поехал.

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "KONVEYER_STUDII_V1"

KOD = '''# -*- coding: utf-8 -*-
# KONVEYER_STUDII_V1
"""
ШАССИ СТУДИИ — конвейер.

Собирает трубу цеха по стыкам берёт/даёт и гоняет по ней наряд.
Про провайдеров, пробы и цеховые повадки не знает ничего: это дело
движка цеха. Шасси знает только ключи и места.

    из ГОРОД:      rabota (картриджи, посты), rezidenty (личность)
    из Биржа:      llm (голова)  ← долг: llm.py переехать в ГОРОД/

    шесть·проверено·до·корня
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # GRONDHEIM_CITY/Студия
_CITY = _HERE.parent                              # GRONDHEIM_CITY
_REPO = _CITY.parent                              # корень

# KONVEYER_STUDII_V1: llm пока живёт в Бирже — общегородская голова в
# квартале, потому что Биржу строили первой. В долгах на переезд.
for _p in ("ГОРОД", "Биржа"):
    _s = str(_REPO / _p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


# ── чтение ───────────────────────────────────────────────────

def _chitat(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def ceh(kvartal: str, imya: str) -> dict:
    """Картридж со своей папкой. Списка цехов не держим."""
    papka = _CITY / kvartal / "цеха" / imya
    m = _chitat(papka / "manifest.json")
    if m is None:
        raise SystemExit(f"нет манифеста: {papka}")
    m["_папка"] = str(papka)
    return m


# ── труба ────────────────────────────────────────────────────

def truba(m: dict, izvne: set | None = None) -> list:
    """Порядок мест по стыкам. Возвращает волны: [[A01], [A02, A03], …].

    Одна волна — места, готовые разом. Это и есть параллель: никто её
    не объявлял, она следует из того, что двое взяли один ключ.
    """
    izvne = set(izvne or {"наряд"})
    ostalos = list(m.get("слоты") or [])
    na_stole = set(izvne)
    volny = []

    while ostalos:
        gotovy = [s for s in ostalos
                  if all(k in na_stole for k in s.get("берёт", []))]
        if not gotovy:
            zastryali = [s["слот"] for s in ostalos]
            nekhvatka = sorted({k for s in ostalos
                                for k in s.get("берёт", [])
                                if k not in na_stole})
            raise SystemExit(
                f"труба не сходится: застряли {zastryali}, "
                f"некому дать {nekhvatka}")
        volny.append(gotovy)
        for s in gotovy:
            na_stole.update(s.get("даёт", []))
            ostalos.remove(s)
    return volny


# ── бумага места ─────────────────────────────────────────────

def kto_ty(m: dict, slot: str) -> str:
    """Блок «КТО ТЫ» — личность того, кто на посту. Пусто — значит
    работает чистое ремесло, и это законно."""
    try:
        import rabota
        import rezidenty
        pid = rabota.id_dlya_slota(_imya_ceha(m), slot)
        pasport, _dom = rezidenty.lichnost_na_postu(pid)
        if not pasport:
            return ""
        return "## КТО ТЫ\\n\\n" + rezidenty.sobrat_dushu(pasport) + "\\n\\n---\\n\\n"
    except Exception:
        return ""


def _imya_ceha(m: dict) -> str:
    return Path(m["_папка"]).name


def znaniya(m: dict, s: dict) -> str:
    """Формуляр места: со склада цеха, только свой список."""
    sklad = Path(m["_папка"]) / "знания"
    kuski = []
    for f in s.get("знания", []):
        p = sklad / f
        if p.exists():
            try:
                kuski.append(f"### {f}\\n\\n" + p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return "\\n\\n".join(kuski)


def bumaga(m: dict, s: dict) -> str:
    p = Path(m["_папка"]) / "слоты" / s["слот"] / "промпт.md"
    if not p.exists():
        raise SystemExit(f"нет бумаги у места {s['слот']}")
    return kto_ty(m, s["слот"]) + p.read_text(encoding="utf-8")


# ── разбор ответа ────────────────────────────────────────────

_JSON = re.compile(r"SYSTEM_JSON_START(.*?)SYSTEM_JSON_END", re.S)


def razobrat(otvet: str) -> dict:
    """Достать JSON из ответа. Работник обязан класть его первым."""
    kusok = _JSON.search(otvet)
    tekst = kusok.group(1) if kusok else otvet
    tekst = tekst.replace("\\U0001f447", "").replace("\\U0001f446", "")
    tekst = tekst.strip().strip("👇👆").strip()
    i, j = tekst.find("{"), tekst.rfind("}")
    if i < 0 or j < 0:
        return {}
    try:
        return json.loads(tekst[i:j + 1])
    except Exception:
        return {}


# ── прогон ───────────────────────────────────────────────────

def progon(m: dict, naryad: dict, ruki=None, govorit=print) -> dict:
    """Прогнать наряд по трубе цеха.

    ruki — движок цеха. None: холостой прогон, руки не зовём, файлов
    не появляется. Приёмка на это честно скажет BLOCKED.
    """
    from llm import chat

    stol = {"наряд": naryad}
    zhurnal = []
    volny = truba(m)

    for nomer, volna in enumerate(volny, 1):
        imena = ", ".join(s["слот"] for s in volna)
        govorit(f"\\n── волна {nomer}: {imena}"
                + ("   (параллель)" if len(volna) > 1 else ""))

        for s in volna:
            vhod = {k: stol.get(k) for k in s.get("берёт", [])}
            sistema = bumaga(m, s)
            znanie = znaniya(m, s)
            nachalo = datetime.now()

            otvet = chat(
                system=sistema,
                user="Вот что тебе пришло:\\n\\n"
                     + json.dumps(vhod, ensure_ascii=False, indent=2),
                knowledge=znanie)

            d = razobrat(otvet)
            moyo = d.get("моё", {}) or {}

            dano, poteryano = [], []
            for k in s.get("даёт", []):
                if k in moyo:
                    stol[k] = moyo[k]
                    dano.append(k)
                else:
                    poteryano.append(k)

            sek = (datetime.now() - nachalo).total_seconds()
            govorit(f"   {s['слот']} · {s['роль']:<14} {sek:5.1f}с  "
                    f"дал: {', '.join(dano) or '—'}"
                    + (f"   НЕ ДАЛ: {poteryano}" if poteryano else ""))

            zhurnal.append({
                "слот": s["слот"], "роль": s.get("роль", ""),
                "волна": nomer, "секунд": round(sek, 1),
                "дал": dano, "не_дал": poteryano,
                "знаний": len(s.get("знания", [])),
            })

            # руки цеха — если движок подан. Шасси не знает, что они делают.
            if ruki is not None and hasattr(ruki, "posle_mesta"):
                ruki.posle_mesta(m, s, stol, govorit)

    zapisat(m, naryad, stol, zhurnal, ruki is not None)
    return stol


def zapisat(m: dict, naryad: dict, stol: dict, zhurnal: list,
            s_rukami: bool) -> None:
    """Журнал прогона. Память живёт в РОЛИ: это история места, не жителя."""
    put = Path(m["_папка"]) / "журналы" / "прогоны.jsonl"
    put.parent.mkdir(parents=True, exist_ok=True)
    zapis = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "цех": _imya_ceha(m),
        "наряд": naryad,
        "с_руками": s_rukami,
        "места": zhurnal,
        "ключи_на_столе": sorted(k for k in stol if k != "наряд"),
    }
    with put.open("a", encoding="utf-8") as f:
        f.write(json.dumps(zapis, ensure_ascii=False) + "\\n")


# ── с руки ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Конвейер Студии")
    p.add_argument("--цех", default="турбо")
    p.add_argument("--квартал", default="Студия")
    p.add_argument("--наряд", default="", help="тема ролика")
    p.add_argument("--площадка", default="YouTube Shorts")
    p.add_argument("--сухой", action="store_true",
                   help="только показать трубу, никого не звать")
    a = p.parse_args()

    m = ceh(a.квартал, a.цех)
    print(f"Цех: {m.get('название')}   судья: {m.get('судья')}")

    volny = truba(m)
    print("\\nТруба собралась по стыкам:")
    for i, v in enumerate(volny, 1):
        for s in v:
            print(f"  волна {i}  {s['слот']} · {s['роль']:<14} "
                  f"берёт {s.get('берёт', [])} → даёт {s.get('даёт', [])}")

    if a.сухой:
        print("\\nСухой прогон: никого не звал.")
        raise SystemExit(0)

    if not a.наряд:
        raise SystemExit("нужен --наряд «тема ролика»")

    stol = progon(m, {"тема": a.наряд, "площадка": a.площадка,
                      "цель": "охват"})
    print("\\nНа столе:", ", ".join(sorted(k for k in stol if k != "наряд")))
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


def dopisat_env(koren: Path) -> str:
    """Ключи звука и анимации в .env.example — под теми именами, под
    какими их звала старая студия. Настоящий .env не трогаем."""
    p = koren / ".env.example"
    if not p.exists():
        return "нет .env.example"
    t = p.read_text(encoding="utf-8")
    nado = ["ELEVENLABS_API_KEY=", "SILICONFLOW_API_KEY="]
    net = [n for n in nado if n.split("=")[0] not in t]
    if not net:
        return "ключи уже описаны"
    shutil.copyfile(p, p.with_suffix(f".example.bak_{_teper()}"))
    p.write_text(t.rstrip("\n") + "\n" + "\n".join(net) + "\n",
                 encoding="utf-8")
    return f"дописано: {', '.join(n.rstrip('=') for n in net)}"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")

    studiya = koren / "GRONDHEIM_CITY" / "Студия"
    if not (studiya / "цеха" / "турбо" / "manifest.json").exists():
        raise SystemExit("Цеха турбо нет — сперва накати ceh_turbo.py")

    put = studiya / "конвейер.py"
    if put.exists():
        if put.read_text(encoding="utf-8") == KOD:
            print("Шасси: уже стоит, не трогал")
        else:
            bak = put.with_suffix(f".py.bak_{_teper()}")
            shutil.copyfile(put, bak)
            put.write_text(KOD, encoding="utf-8")
            print(f"Шасси: обновлено, старое в {bak.name}")
    else:
        put.write_text(KOD, encoding="utf-8")
        print(f"Шасси: положено ({len(KOD.splitlines())} строк)")

    print(f"Ключи:  {dopisat_env(koren)}")

    # ── сухая проверка: труба собирается? ─────────────────────
    print("\nСухая проверка — собираю трубу, никого не зову:")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_konv", put)
    k = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    try:
        spec.loader.exec_module(k)  # type: ignore[union-attr]
        m = k.ceh("Студия", "турбо")
        for i, volna in enumerate(k.truba(m), 1):
            for s in volna:
                znak = "  ∥" if len(volna) > 1 else "   "
                print(f"  волна {i}{znak} {s['слот']} · {s['роль']:<14} "
                      f"{s.get('берёт', [])} → {s.get('даёт', [])}")
    except SystemExit as e:
        print(f"  ТРУБА НЕ СОБРАЛАСЬ: {e}")
        return
    except Exception as e:
        print(f"  споткнулся: {e}")
        return

    print("\nШасси стоит. Холостой прогон — с руки, из корня:\n"
          '  python GRONDHEIM_CITY/Студия/конвейер.py --наряд "тема ролика"\n'
          "\nРуки не подключены: места подумают, файлов не будет,\n"
          "приёмка честно скажет BLOCKED. Так и должно быть.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
