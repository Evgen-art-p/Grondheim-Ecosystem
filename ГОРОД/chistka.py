# -*- coding: utf-8 -*-
# MENEDZHER_CHISTKI_V1
"""
МЕНЕДЖЕР ЧИСТКИ · один список на все клинеры

ЗАЧЕМ. Клинеров в городе стало четыре, и каждый жил сам по себе:
один на кнопке у Брата, три из командной строки. Кнопка знала про
одного и ничего про остальных.

Здесь они собраны в РЕЕСТР. Появится пятый — вписывается строкой,
кнопка не меняется. Это тот же Закон Картриджа: список ведётся в
одном месте, а не размазан по кабинетам.

ЧТО В РЕЕСТРЕ СЕГОДНЯ:

    репозиторий  копии от патчей, отработавшие патчи, разовое
    бэкапы_цеха  .bak в слотах торгового цеха
    память       разговоры, отклик, архив жителей
    атлас        Атлас и лента PnL — ТОРГОВАЯ ИСТОРИЯ, осторожно

ПРАВИЛО ОДНО НА ВСЕХ: ничего не удаляется. Всё переезжает в чулан
с манифестом — что, откуда, сколько весило и как вернуть.

И второе: клинер сам ничего не решает. Он показывает, а убирает
строго то, что назвали. Разница между «мусор» и «жизнь» — не его
дело.

    python chistka.py                 что где накопилось
    python chistka.py --chto память   подробно по одному
    python chistka.py --slovo         что об этом думает Брат

`шесть·проверено·до·корня`
"""
import sys
from pathlib import Path

MARKER = "MENEDZHER_CHISTKI_V1"

_HERE = Path(__file__).resolve().parent          # ГОРОД/
_REPO = _HERE.parent


def _koren_v_put():
    k = str(_REPO)
    if k not in sys.path:
        sys.path.insert(0, k)


def _krasivo(b: int) -> str:
    if b < 1024:
        return f"{b} б"
    if b < 1024 * 1024:
        return f"{b / 1024:.0f} КБ"
    return f"{b / 1024 / 1024:.1f} МБ"


def _ves_putey(puti) -> tuple:
    fajlov = bajt = 0
    for p in puti:
        p = Path(p)
        if p.is_file():
            fajlov += 1
            try:
                bajt += p.stat().st_size
            except Exception:
                pass
    return fajlov, bajt


# ═══════════════════════════════════════════════════════════
# РАЗВЕДКИ · каждая отвечает: что нашлось и сколько весит
# ═══════════════════════════════════════════════════════════

def _razvedka_repo() -> dict:
    """Зовём сам uborshchik.py — чтобы кнопка и он не разошлись."""
    _koren_v_put()
    try:
        import uborshchik as U
    except Exception as e:
        return {"беда": f"уборщик не поднялся: {e}"}
    try:
        teksty = dict(U._tekstovye())
        gotovye, _zhdut = U.sobrat_patchi(teksty)
        gruppy = [
            ("копии, оставленные патчами", U.sobrat_kopii()),
            ("патчи, которые отработали", gotovye),
            ("разовые инструменты", U.sobrat_poimenno(U.RAZOVYE)),
            ("заменённое другим", U.sobrat_poimenno(U.OTSLUZHIVSHIE)),
            ("батники, у которых есть кнопка", U.sobrat_batniki()),
        ]
    except Exception as e:
        return {"беда": f"разведка не прошла: {e}"}
    stroki, vsego_f, vsego_b = [], 0, 0
    for imya, spisok in gruppy:
        f, b = _ves_putey(spisok)
        vsego_f += f
        vsego_b += b
        if f:
            stroki.append(f"{imya}: {f} · {_krasivo(b)}")
    return {"файлов": vsego_f, "байт": vsego_b, "строки": stroki}


def _razvedka_bak_ceha() -> dict:
    baza = (_REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" /
            "торговый_хаос" / "слоты")
    if not baza.exists():
        return {"файлов": 0, "байт": 0, "строки": ["слотов нет"]}
    najdeno = [p for p in baza.rglob("*") if p.is_file() and ".bak" in p.name]
    f, b = _ves_putey(najdeno)
    po_slotam = {}
    for p in najdeno:
        po_slotam[p.parts[len(baza.parts)]] = \
            po_slotam.get(p.parts[len(baza.parts)], 0) + 1
    stroki = [f"{k}: {v}" for k, v in sorted(po_slotam.items())]
    return {"файлов": f, "байт": b, "строки": stroki, "пути": najdeno}


def _razvedka_pamyati() -> dict:
    _koren_v_put()
    try:
        import chistilshchik_pamyati as P
    except Exception as e:
        return {"беда": f"клинер памяти не поднялся: {e}"}
    itog, stroki, vsego_f, vsego_b = {}, [], 0, 0
    for dom in P.zhiteli():
        k = P.kartina(dom)
        b = sum(v[1] for v in k.values())
        f = sum(v[0] for v in k.values())
        itog[dom.name] = k
        vsego_f += f
        vsego_b += b
    tyazhelye = sorted(itog.items(),
                       key=lambda x: -sum(v[1] for v in x[1].values()))[:6]
    for imya, k in tyazhelye:
        razg = k.get("разговоры", (0, 0, 0))[1]
        metki = k.get("метки", (0, 0, 0))[1] + k.get("маяки", (0, 0, 0))[1]
        stroki.append(f"{imya}: разговоры {_krasivo(razg)} · "
                      f"нажитое {_krasivo(metki)}")
    return {"файлов": vsego_f, "байт": vsego_b, "строки": stroki,
            "по жителям": itog}


def _razvedka_atlasa() -> dict:
    kandidaty = []
    for imya in ("atlas.jsonl", "Атлас.jsonl", "pnl.jsonl", "лента_pnl.jsonl"):
        kandidaty += list((_REPO / "GRONDHEIM_CITY").rglob(imya))
    f, b = _ves_putey(kandidaty)
    stroki = [f"{p.relative_to(_REPO)} · {_krasivo(p.stat().st_size)}"
              for p in kandidaty if p.is_file()]
    return {"файлов": f, "байт": b, "строки": stroki or ["не нашёл"],
            "пути": kandidaty}


# ═══════════════════════════════════════════════════════════
# РЕЕСТР
# ═══════════════════════════════════════════════════════════

REESTR = [
    {"имя": "репозиторий",
     "что": "копии от патчей, отработавшие патчи, разовое",
     "куда": "_УБОРКА",
     "опасно": False,
     "разведка": _razvedka_repo,
     "как убрать": "python uborshchik.py --ubrat"},
    {"имя": "бэкапы_цеха",
     "что": ".bak в слотах торгового цеха",
     "куда": "_АРХИВ_ЧИСТКИ",
     "опасно": False,
     "разведка": _razvedka_bak_ceha,
     "как убрать": "python arkhivirovat_bak.py"},
    {"имя": "память",
     "что": "разговоры, отклик, архив жителей",
     "куда": "_УБОРКА_ПАМЯТИ",
     "опасно": False,
     "разведка": _razvedka_pamyati,
     "как убрать": "python chistilshchik_pamyati.py "
                   "--zhitel ИМЯ --chto разговоры --ubrat"},
    {"имя": "атлас",
     "что": "Атлас и лента PnL — ТОРГОВАЯ ИСТОРИЯ",
     "куда": "рядом, с меткой времени",
     "опасно": True,
     "разведка": _razvedka_atlasa,
     "как убрать": "python ochistit_atlas.py"},
]


def spisok() -> list:
    """Реестр без разведки — для отрисовки списка."""
    return [{k: v for k, v in c.items() if k != "разведка"}
            for c in REESTR]


def razvedat(imya: str = "") -> dict:
    """Разведка одного или всех. Долгая — звать в фоне."""
    itog = {}
    for c in REESTR:
        if imya and c["имя"] != imya:
            continue
        try:
            itog[c["имя"]] = c["разведка"]()
        except Exception as e:
            itog[c["имя"]] = {"беда": f"{e}"}
    return itog


# ═══════════════════════════════════════════════════════════
# СЛОВО БРАТА · не цифры, а что они значат
# ═══════════════════════════════════════════════════════════

def slovo_brata(razvedka: dict = None) -> list:
    """Что видно поверх чисел. Только наблюдения, без приказов."""
    r = razvedka or razvedat()
    slova = []

    p = r.get("память") or {}
    po = p.get("по жителям") or {}
    if po:
        razg = sum(k.get("разговоры", (0, 0, 0))[1] for k in po.values())
        nazhito = sum(k.get("метки", (0, 0, 0))[1] +
                      k.get("маяки", (0, 0, 0))[1] for k in po.values())
        if razg and nazhito and razg > nazhito * 20:
            slova.append(
                f"Памяти {_krasivo(p.get('байт', 0))}, и почти всё это "
                f"разговоры ({_krasivo(razg)}). Нажитого — меток и маяков — "
                f"{_krasivo(nazhito)}. Память забита протоколом, а не опытом.")
        molchuny = [imya for imya, k in po.items()
                    if sum(v[1] for v in k.values()) < 2048]
        if molchuny:
            slova.append(
                "Следов почти нет у: " + ", ".join(sorted(molchuny)) +
                ". Они живут, но ничего не оставляют — когда дойдёт до "
                "весов, предъявить будет нечего.")
        bez_mayakov = [imya for imya, k in po.items()
                       if k.get("маяки", (0, 0, 0))[0] == 0
                       and k.get("метки", (0, 0, 0))[0] > 0]
        if bez_mayakov:
            slova.append("Маяков нет вовсе у: " + ", ".join(sorted(bez_mayakov))
                         + " — метки есть, а замеченного за собой нет.")

    rp = r.get("репозиторий") or {}
    if rp.get("файлов"):
        slova.append(f"В репозитории лишнего {rp['файлов']} файл(ов), "
                     f"{_krasivo(rp.get('байт', 0))}.")

    at = r.get("атлас") or {}
    if at.get("файлов"):
        slova.append("Атлас трогать в последнюю очередь: это торговая "
                     "история, из неё потом считаются веса.")
    return slova


def _pokazat(imya: str = "", so_slovom: bool = False):
    print()
    print("МЕНЕДЖЕР ЧИСТКИ · ничего не удаляется, всё в чулан с манифестом")
    print()
    r = razvedat(imya)
    for c in REESTR:
        if imya and c["имя"] != imya:
            continue
        d = r.get(c["имя"], {})
        znak = " ⚠" if c["опасно"] else "  "
        if d.get("беда"):
            print(f"{znak} {c['имя']:14} — не смотрится: {d['беда']}")
            continue
        print(f"{znak} {c['имя']:14} {d.get('файлов', 0):5} файл(ов) · "
              f"{_krasivo(d.get('байт', 0)):>9}   ({c['что']})")
        for s in d.get("строки", [])[:8 if imya else 3]:
            print(f"        {s}")
        if imya:
            print(f"        убрать: {c['как убрать']}")
    if so_slovom:
        print()
        print("── что об этом думает Брат ──")
        for s in slovo_brata(r):
            print("  ·", s)
    print()


if __name__ == "__main__":
    argv = sys.argv[1:]
    kto = ""
    if "--chto" in argv:
        i = argv.index("--chto")
        if i + 1 < len(argv):
            kto = argv[i + 1]
    _pokazat(kto, so_slovom=("--slovo" in argv or not kto))
