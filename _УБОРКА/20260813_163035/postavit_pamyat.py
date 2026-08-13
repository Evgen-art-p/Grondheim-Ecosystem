#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PAMYATI_GORODA_V1
"""
АРХИВ КАК ДОСТУП — не склад, а окно во все памяти города.

    python postavit_pamyat.py            посмотреть
    python postavit_pamyat.py --sdelat   поставить

Запускать из КОРНЯ (материк или остров).

МЫСЛЬ ШЕФА

    «Архив — не папка со всей памятью мира, а страница с доступом ко
    всей памяти мира».

    Сегодня он именно папка: руда падает к нему во двор, раскладывается
    по разделам, пишется каталог. Своё хранилище, и только своё.

ЧТО СТАНОВИТСЯ

    В кабинете Архива появляется кнопка ПАМЯТИ. За ней — список того,
    что в этом городе реально помнится, и любое открывается в правом
    окне.

    Сам Архив при этом ничего к себе не тащит. Он знает, ГДЕ лежит, и
    умеет показать. Его собственный склад становится одной памятью среди
    прочих, а не единственной.

КАК УСТРОЕНО (как кран на Бирже)

    `Архив/памяти/` — папка, и в ней по файлу на память. Файл крошечный:
    как называется, есть ли она здесь, и как достать записи. Страница
    обходит папку и показывает ТОЛЬКО те памяти, что нашлись на диске.

    Отсюда две вещи разом. На острове зажгутся Биржа и Маяк — потому
    что больше там пока и нет. А новая память потом — это один новый
    файл в папке; страницу трогать не надо, она сама его подхватит.

ЧТО СТАВИТСЯ СЕЙЧАС

    Механизм и семь памятей: сделки Биржи, дневники трейдеров, статистика
    мест, трудовые истории постов, Маяк с пульсами островов, метки
    жителей, книги города и собственный склад Архива.
"""
import argparse
import ast
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KOREN = Path(__file__).resolve().parent
ARKHIV = KOREN / "Архив"
PAMYATI = ARKHIV / "памяти"
UI = ARKHIV / "ui_arkhiv.py"
MARKER = "# PAMYATI_GORODA_V1 - marker"
BAK = ".bak_pamyati"


PAMYAT_PY = r'''# -*- coding: utf-8 -*-
# PAMYATI_GORODA_V1
"""
ПАМЯТИ ГОРОДА — реестр того, что помнится, и где оно лежит.

ЗАКОН ЭТОГО ФАЙЛА
    Архив ничего не хранит у себя и ничего не переносит. Он знает, ГДЕ
    лежит память, и умеет её показать.

    Списков здесь нет: памяти СКАНИРУЮТСЯ из папки `памяти/`, как истоки
    крана на Бирже. Появился новый файл — появилась новая память, сама.
    Ни эту страницу, ни этот файл править не надо.

    Каждая память — файл с тремя вещами:
        ИМЯ    — как называется
        est()  — есть ли она в ЭТОМ городе (на острове половины не будет)
        zapisi(predel) — записи, свежие сверху
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PAPKA = _HERE / "памяти"


def _podnyat(put: Path):
    try:
        spec = importlib.util.spec_from_file_location(f"pamyat_{put.stem}", put)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception as e:
        print(f"[ПАМЯТЬ] ⚠️  {put.name} не поднялась: {e}")
        return None


def vse() -> list:
    """Все памяти, которые ЕСТЬ в этом городе. Пусто — честно пусто."""
    out = []
    if not PAPKA.is_dir():
        return out
    for p in sorted(PAPKA.glob("*.py")):
        if p.name.startswith("_"):
            continue
        m = _podnyat(p)
        if m is None:
            continue
        try:
            if not m.est():
                continue
        except Exception:
            continue
        out.append({"ключ": p.stem, "имя": getattr(m, "ИМЯ", p.stem),
                    "модуль": m})
    return out


def zapisi(klyuch: str, predel: int = 200) -> list:
    for p in vse():
        if p["ключ"] == klyuch:
            try:
                return p["модуль"].zapisi(predel)
            except Exception as e:
                return [{"когда": "", "что": f"память не открылась: {e}",
                         "откуда": ""}]
    return []
'''


# ── сами памяти ───────────────────────────────────────────────
PAMYAT_FAYLY = {

"birzha_sdelki.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: сделки Биржи — атлас случаев и результат по деньгам."""
import json
from pathlib import Path

ИМЯ = "Биржа · сделки"
_D = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "Биржа" / "данные"


def _faily():
    if not _D.is_dir():
        return []
    return [p for p in _D.glob("*.jsonl")
            if p.name.startswith(("atlas_trading", "trading_pnl"))
            and "archive" not in p.name]


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        try:
            stroki = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for s in stroki[-predel:]:
            try:
                d = json.loads(s)
            except Exception:
                continue
            out.append({
                "когда": str(d.get("ts") or d.get("время") or d.get("когда")
                             or d.get("timestamp") or "")[:16],
                "что": (d.get("итог") or d.get("вердикт") or d.get("сигнал")
                        or json.dumps(d, ensure_ascii=False))[:220],
                "откуда": f.name})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"dnevniki.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: дневники работников — что делал и почему, своими словами."""
import json
from pathlib import Path

ИМЯ = "Дневники работников"
_CITY = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY"


def _faily():
    if not _CITY.is_dir():
        return []
    return sorted(_CITY.rglob("данные/diary_*.jsonl"))


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        chasti = f.parts
        slot = chasti[-3] if len(chasti) > 3 else ""
        try:
            stroki = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for s in stroki[-predel:]:
            try:
                d = json.loads(s)
            except Exception:
                continue
            zapis = d.get("diary_entry") or d
            kogda = d.get("ts") or d.get("когда") or d.get("время") or ""
            # время бывает числом секунд — переводим в человеческое
            try:
                if isinstance(kogda, (int, float)) or (
                        isinstance(kogda, str) and kogda.replace(".", "", 1).isdigit()):
                    from datetime import datetime
                    kogda = datetime.fromtimestamp(float(kogda)).strftime(
                        "%Y-%m-%d %H:%M")
            except Exception:
                pass
            out.append({
                "когда": str(kogda)[:16],
                "что": (str(zapis.get("action") or zapis.get("что") or "")
                        [:220] or json.dumps(zapis, ensure_ascii=False)[:220]),
                "откуда": f"{slot} · {f.name}"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"posty.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: трудовые истории мест — кого принимали и за что снимали."""
import json
from pathlib import Path

ИМЯ = "Трудовые истории мест"
_P = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "посты"


def est() -> bool:
    return _P.is_dir() and any(_P.glob("*/пост.json"))


def zapisi(predel: int = 200) -> list:
    out = []
    for f in sorted(_P.glob("*/пост.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        nazv = d.get("название", f.parent.name)
        for z in d.get("трудовая_история", []) or []:
            pochemu = f" — {z.get('почему')}" if z.get("почему") else ""
            out.append({
                "когда": str(z.get("когда", ""))[:16],
                "что": f"{z.get('что','')}: {z.get('кто','')}{pochemu}",
                "откуда": nazv})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"mayak.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: Маяк — кто и когда откликался с той стороны."""
import json
from pathlib import Path

ИМЯ = "Маяк · пульсы и гнёзда"
_M = Path(__file__).resolve().parents[2] / "Маяк"


def _faily():
    if not _M.is_dir():
        return []
    return sorted(_M.rglob("пульсы.jsonl"))


def est() -> bool:
    return bool(_faily()) or (_M / "острова").is_dir()


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        kto = f.parent.name
        try:
            stroki = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for s in stroki[-predel:]:
            try:
                d = json.loads(s)
            except Exception:
                continue
            out.append({
                "когда": str(d.get("когда") or d.get("time") or "")[:16],
                "что": json.dumps({k: v for k, v in d.items()
                                   if k not in ("когда", "time")},
                                  ensure_ascii=False)[:220],
                "откуда": kto})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"zhiteli.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: метки жителей — то, что человек нажил и оплатил."""
import json
from pathlib import Path

ИМЯ = "Жители · метки"
_K = Path(__file__).resolve().parents[2] / "GRONDHEIM_CITY" / "жители" / "ковчег"


def _faily():
    if not _K.is_dir():
        return []
    return sorted(_K.glob("*/2_метки/metki.json"))


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    out = []
    for f in _faily():
        kto = f.parents[1].name
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        spisok = d if isinstance(d, list) else d.get("метки", [])
        for m in spisok or []:
            if not isinstance(m, dict):
                continue
            out.append({
                "когда": str(m.get("когда", ""))[:16],
                "что": str(m.get("текст", ""))[:220],
                "откуда": f"{kto} · {m.get('откуда', '')}"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"knigi.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: книги города — летопись, чертёж, законы кварталов."""
from pathlib import Path

ИМЯ = "Книги города"
_K = Path(__file__).resolve().parents[2]


def _faily():
    return sorted(p for p in _K.glob("*.md") if p.stat().st_size > 800)


def est() -> bool:
    return bool(_faily())


def zapisi(predel: int = 200) -> list:
    from datetime import datetime
    out = []
    for f in _faily():
        try:
            razmer = f.stat().st_size // 1024
            kogda = datetime.fromtimestamp(f.stat().st_mtime)
        except Exception:
            continue
        pervaya = ""
        try:
            for s in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if s.strip() and not s.startswith("#"):
                    pervaya = s.strip()[:160]
                    break
        except Exception:
            pass
        out.append({"когда": kogda.strftime("%Y-%m-%d %H:%M"),
                    "что": f"{f.name} · {razmer} КБ — {pervaya}",
                    "откуда": "корень города"})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',

"sklad_arkhiva.py": r'''# -*- coding: utf-8 -*-
"""ПАМЯТЬ: собственный склад Архива — то, что принесли рудой.

Раньше он был единственным. Теперь — одна память среди прочих.
"""
import json
from pathlib import Path

ИМЯ = "Склад Архива"
_K = Path(__file__).resolve().parents[1] / "данные" / "архив" / "каталог.json"


def est() -> bool:
    return _K.is_file()


def zapisi(predel: int = 200) -> list:
    try:
        d = json.loads(_K.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for z in (d.get("записи") or []):
        if not isinstance(z, dict):
            continue
        out.append({"когда": str(z.get("когда") or z.get("дата", ""))[:16],
                    "что": str(z.get("название") or z.get("что", ""))[:220],
                    "откуда": str(z.get("раздел", ""))})
    out.sort(key=lambda x: x["когда"], reverse=True)
    return out[:predel]
''',
}


# ── правка кабинета ───────────────────────────────────────────
STAROE_FUNC = '''    def idti_v_biblioteku():
'''
NOVOE_FUNC = '''    def otkryt_pamyati():
        """PAMYATI_GORODA_V1: Архив как ДОСТУП, а не как склад.

        Ничего к себе не тащим: спрашиваем реестр памятей, он обходит
        папку `Архив/памяти/` и отдаёт только то, что в этом городе
        реально есть. Выбранное показываем в правом окне.
        """
        try:
            import sys as _sys
            _p = str(Path(__file__).resolve().parent)
            if _p not in _sys.path:
                _sys.path.insert(0, _p)
            import pamyat as _pam
        except Exception as e:
            ui.notify(f"⚠ реестр памятей не поднялся: {e}", color="negative")
            return

        spisok = _pam.vse()
        if not spisok:
            ui.notify("Памятей не нашёл — в этом городе пока пусто",
                      color="warning")
            return

        with ui.dialog() as dlg, ui.card().style(
            "background:#0d1117; border:1px solid rgba(201,168,76,0.30); "
            "border-radius:16px; min-width:420px; padding:20px;"
        ):
            ui.html('<div style="color:rgba(255,255,255,0.92); '
                    'font-weight:800; letter-spacing:0.10em; '
                    'font-size:0.9rem; margin-bottom:4px;">'
                    '🧠 ПАМЯТИ ГОРОДА</div>')
            ui.html('<div style="color:rgba(255,255,255,0.45); '
                    'font-size:0.72rem; margin-bottom:12px;">'
                    'Архив ничего из этого у себя не держит — он знает, '
                    'где лежит, и показывает.</div>')

            def _otkryt(p):
                zapisi = _pam.zapisi(p["ключ"], 200)
                stroki = [f'# {p["имя"]}', "",
                          f'*записей: {len(zapisi)}*', ""]
                if not zapisi:
                    stroki.append("*пусто — память есть, а записей ещё нет*")
                for z in zapisi:
                    kogda = z.get("когда") or "—"
                    otkuda = f'  ·  `{z.get("откуда","")}`' if z.get("откуда") else ""
                    stroki.append(f'**{kogda}**{otkuda}  \\n{z.get("что","")}')
                    stroki.append("")
                update_viewer("\\n".join(stroki))
                dlg.close()

            for p in spisok:
                ui.button(p["имя"], on_click=lambda p=p: _otkryt(p)).props(
                    "flat no-caps").style(
                    "width:100%; text-align:left; padding:8px 12px; "
                    "border-radius:8px; margin-bottom:4px; font-size:0.8rem; "
                    "color:rgba(255,255,255,0.85); "
                    "background:rgba(255,255,255,0.04);")

            ui.button("закрыть", on_click=dlg.close).props("flat").style(
                "margin-top:8px; color:rgba(255,255,255,0.4); "
                "font-size:0.75rem;")
        dlg.open()

    def idti_v_biblioteku():
'''

STAROE_KNOPKA = '''                    _b3 = ui.element("div").classes("arkhiv-btn")
                    _b3.on("click", lambda: idti_v_gorod())
                    with _b3:
                        ui.html("🏙 ГОРОД")
'''
NOVOE_KNOPKA = '''                    # PAMYATI_GORODA_V1: окно во все памяти города
                    _b0 = ui.element("div").classes("arkhiv-btn")
                    _b0.on("click", lambda: otkryt_pamyati())
                    with _b0:
                        ui.html("🧠 ПАМЯТИ")
                    _b3 = ui.element("div").classes("arkhiv-btn")
                    _b3.on("click", lambda: idti_v_gorod())
                    with _b3:
                        ui.html("🏙 ГОРОД")
'''


def proverit_python(tekst: str, imya: str) -> bool:
    try:
        ast.parse(tekst)
    except SyntaxError as e:
        print(f"  x {imya}: синтаксис сломан ({e}) — НЕ пишу")
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as f:
        f.write(tekst)
        vrem = f.name
    try:
        py_compile.compile(vrem, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"  x {imya}: не компилируется ({e}) — НЕ пишу")
        return False
    finally:
        Path(vrem).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdelat", action="store_true")
    a = ap.parse_args()
    suho = not a.sdelat

    print("=" * 62)
    print("ПАМЯТИ ГОРОДА" + ("   [СУХОЙ ПРОГОН]" if suho else ""))
    print("=" * 62)

    if not ARKHIV.is_dir():
        print("x не вижу папку Архив — запускай из корня города")
        print("  (на острове Архива пока нет — скажи, и привезу)")
        return 1

    print("\nмеханизм:")
    if not proverit_python(PAMYAT_PY, "pamyat.py"):
        return 1
    print(f"  Архив/pamyat.py: "
          f"{'обновится' if (ARKHIV / 'pamyat.py').exists() else 'ляжет'}")

    print("\nпамяти:")
    for imya, telo in PAMYAT_FAYLY.items():
        if not proverit_python(telo, imya):
            return 1
        print(f"  {imya}")

    print("\nкнопка в кабинете:")
    if not UI.exists():
        print("  x нет Архив/ui_arkhiv.py")
        return 1
    tekst = UI.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("  ui_arkhiv.py: уже накатано")
    else:
        for nazv, staroe, novoe in (("дверь памятей", STAROE_FUNC, NOVOE_FUNC),
                                    ("кнопка ПАМЯТИ", STAROE_KNOPKA,
                                     NOVOE_KNOPKA)):
            n = tekst.count(staroe)
            if n != 1:
                print(f"  x якорь «{nazv}» найден {n} раз — не трогаю")
                return 1
            tekst = tekst.replace(staroe, novoe, 1)
            print(f"    · {nazv}")
        tekst = tekst.rstrip("\n") + "\n\n" + MARKER + "\n"
        if not proverit_python(tekst, "ui_arkhiv.py"):
            return 1

    if suho:
        print("\nЭто был показ. Ставить: python postavit_pamyat.py --sdelat")
        return 0

    (ARKHIV / "pamyat.py").write_text(PAMYAT_PY, encoding="utf-8")
    PAMYATI.mkdir(exist_ok=True)
    for imya, telo in PAMYAT_FAYLY.items():
        (PAMYATI / imya).write_text(telo, encoding="utf-8")
    if MARKER not in UI.read_text(encoding="utf-8"):
        shutil.copy2(UI, UI.with_suffix(UI.suffix + BAK))
        UI.write_text(tekst, encoding="utf-8")

    print("\n+ готово. В кабинете Архива — кнопка ПАМЯТИ.")
    print("  Новая память потом = один новый файл в Архив/памяти/,")
    print("  страницу трогать не надо.")
    return 0


if __name__ == "__main__":
    _kod = main()
    if sys.platform == "win32" and len(sys.argv) == 1:
        try:
            input("\nготово. Enter — закрыть окно.")
        except Exception:
            pass
    sys.exit(_kod)
