# -*- coding: utf-8 -*-
# STRANICA_CEHOV_V1
"""
ЦЕХА — картриджи Биржи. Вставить, посмотреть, вынуть.

Страница ничего не знает про устройство цеха. Она смотрит папки:
есть папка с манифестом — есть цех; есть слот с мозгом — есть место.
Закон Картриджа, как и везде в городе.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from nicegui import ui

KOREN = Path(__file__).resolve().parent.parent
CEHA = KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха"
CHULAN = KOREN / "_УБОРКА"

# что НЕ переезжает в копию: это нажитое оригиналом, не устройство
NE_KOPIRUEM = {"данные", "журналы", "__pycache__", "кадры"}

CSS = """
<style>
.c-page { background:#0b0f14; color:#e6edf3;
          font-family:'Inter',system-ui,sans-serif; }
.c-head { padding:14px 20px; border-bottom:1px solid rgba(255,255,255,0.08);
          display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
.c-body { display:flex; gap:16px; padding:16px 20px; align-items:flex-start; }
.c-left { width:330px; flex-shrink:0; }
.c-right { flex:1; min-width:0; }
.c-card { background:rgba(255,255,255,0.03); border-radius:14px;
          border:1px solid rgba(255,255,255,0.08); padding:14px; }
.c-podpis { color:rgba(255,255,255,0.42); font-size:0.66rem;
            letter-spacing:0.08em; text-transform:uppercase;
            margin:12px 0 4px; }
</style>
"""


def _chitat(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _rabota():
    import sys
    g = str(KOREN / "ГОРОД")
    if g not in sys.path:
        sys.path.insert(0, g)
    try:
        import rabota
        return rabota
    except Exception:
        return None


def ceha() -> list:
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
    return out


def _chistoe(s: str) -> str:
    s = (s or "").strip().replace(" ", "_")
    return re.sub(r"[^0-9A-Za-zА-Яа-яёЁ_\-]", "", s)


def razmnozhit(iz: dict, imya: str, nazvanie: str) -> tuple:
    """Снять копию цеха один в один. Оригинал не трогаем."""
    imya = _chistoe(imya)
    if not imya:
        return False, "у цеха должно быть имя"
    cel = CEHA / imya
    if cel.exists():
        return False, f"цех «{imya}» уже есть"

    def _mimo(_d, imena):
        return {i for i in imena
                if i in NE_KOPIRUEM or ".bak" in i
                or i.endswith((".pyc", ".log", ".snesen"))}

    try:
        shutil.copytree(iz["папка"], cel, ignore=_mimo)
    except Exception as e:
        return False, f"не скопировалось: {e}"

    m = _chitat(cel / "manifest.json") or {}
    m["название"] = nazvanie or imya
    m["_от_кого"] = iz["имя"]
    m["_заведён"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    m["_note"] = (f"Картридж-цех, снят с «{iz['имя']}» один в один. "
                  f"Слоты те же; стол, журналы и данные — свои, с нуля.")
    try:
        (cel / "manifest.json").write_text(
            json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        return False, f"манифест копии не записался: {e}"

    R = _rabota()
    zavedeno = 0
    if R is not None:
        for s in (m.get("слоты") or []):
            slot = s.get("слот")
            if not slot:
                continue
            ok, _ = R.zavesti(R.id_dlya_slota(imya, slot), {
                "название": f"{s.get('роль', slot)} · {m['название']}",
                "квартал": m.get("квартал", ""), "цех": imya, "слот": slot,
                "локация": m.get("здание", ""),
                "чем_занят": s.get("роль", ""),
                "судья": m.get("судья", ""), "движок": "мозг.py"})
            if ok:
                zavedeno += 1
    return True, f"цех «{m['название']}» снят, вакансий {zavedeno}"


def ubrat(ceh: dict) -> tuple:
    """Вынуть картридж. Занятый не выдёргиваем."""
    zanyaty = [s for s in ceh["слоты"] if s["кто"]]
    if zanyaty:
        kto = ", ".join(s["кто"] for s in zanyaty)
        return False, f"в цехе сидят: {kto} — сперва уволь"
    kuda = CHULAN / datetime.now().strftime("%Y%m%d_%H%M%S") / "цеха"
    try:
        kuda.mkdir(parents=True, exist_ok=True)
        shutil.move(str(ceh["папка"]), str(kuda / ceh["имя"]))
    except Exception as e:
        return False, str(e)
    return True, f"цех «{ceh['название']}» вынут (лежит в _УБОРКА)"


def page_ceha():
    ui.add_head_html(CSS)
    ui.query("body").classes("c-page")
    sost: dict[str, Any] = {"вybrano": None}
    refs: dict[str, Any] = {}

    with ui.element("div").classes("c-head"):
        ui.html('<div style="font-weight:800; letter-spacing:0.14em; '
                'font-size:0.95rem;">БИРЖА · ЦЕХА</div>')
        refs["schet"] = ui.html("")
        ui.element("div").style("flex:1")
        ui.button("← РАБОТА",
                  on_click=lambda: ui.navigate.to("/rabota")).props(
            "flat no-caps").style("font-size:0.72rem; "
                                  "color:rgba(139,233,253,0.85);")

    with ui.element("div").classes("c-body"):
        with ui.element("div").classes("c-left"):
            with ui.element("div").classes("c-card"):
                refs["spisok"] = ui.element("div")
        with ui.element("div").classes("c-right"):
            refs["karta"] = ui.element("div").classes("c-card")

    def risovat_spisok():
        refs["spisok"].clear()
        vse = ceha()
        mest = sum(len(c["слоты"]) for c in vse)
        zanyato = sum(1 for c in vse for s in c["слоты"] if s["кто"])
        refs["schet"].content = (
            f'<div style="color:rgba(139,233,253,0.75); font-size:0.72rem;">'
            f'цехов {len(vse)} · мест {mest} · занято {zanyato}</div>')
        with refs["spisok"]:
            if not vse:
                ui.label("цехов нет").style(
                    "color:rgba(255,255,255,0.35); font-size:0.78rem;")
                return
            for c in vse:
                zhivyh = sum(1 for s in c["слоты"] if s["мозг"])
                kto = sum(1 for s in c["слоты"] if s["кто"])

                def _vyb(c=c):
                    sost["вybrano"] = c["имя"]
                    risovat_kartu()

                ui.button(f'{c["название"][:24]}  ·  мест {len(c["слоты"])}'
                          f'  ·  людей {kto}', on_click=_vyb).props(
                    "flat no-caps").style(
                    f"width:100%; text-align:left; font-size:0.76rem; "
                    f"padding:7px 10px; border-radius:8px; margin-bottom:4px; "
                    f"background:rgba(255,255,255,0.04); "
                    f"color:{'rgba(80,250,123,0.85)' if zhivyh else 'rgba(255,255,255,0.5)'};")

    def risovat_kartu():
        refs["karta"].clear()
        imya = sost["вybrano"]
        vse = {c["имя"]: c for c in ceha()}
        with refs["karta"]:
            if imya not in vse:
                ui.label("Выбери цех слева — здесь откроется его карточка."
                         ).style("color:rgba(255,255,255,0.4); "
                                 "font-size:0.82rem;")
                return
            c = vse[imya]
            ui.html(f'<div style="font-weight:800; font-size:0.95rem;">'
                    f'{c["название"]}</div>'
                    f'<div style="color:rgba(255,255,255,0.35); '
                    f'font-size:0.68rem; font-family:monospace; '
                    f'margin-bottom:10px;">{c["имя"]}'
                    f'{"  ·  снят с " + c["от_кого"] if c["от_кого"] else ""}'
                    f'</div>')

            ui.label(f'здание: {c["здание"] or "—"}   ·   '
                     f'свой стол: {"есть" if c["свой_стол"] else "ещё нет"}'
                     ).style("color:rgba(255,255,255,0.5); font-size:0.75rem;")

            ui.html('<div class="c-podpis">места</div>')
            for s in c["слоты"]:
                kto = s["кто"] or "— свободно"
                cvet = ("rgba(80,250,123,0.85)" if s["кто"]
                        else "rgba(255,255,255,0.55)")
                mozg = "" if s["мозг"] else "   (мозга нет)"
                ui.label(f'{s["слот"]}  ·  {s["роль"]}  ·  {kto}{mozg}').style(
                    f"color:{cvet}; font-size:0.78rem; "
                    f"font-family:monospace;")

            ui.html('<div class="c-podpis">снять копию</div>')
            ui.label("Копия идёт чистой: без данных, журналов и стола. "
                     "Новый цех начинает свою жизнь.").style(
                "color:rgba(255,255,255,0.4); font-size:0.72rem;")
            novoe_imya = ui.input("Имя папки (без пробелов)").props(
                "dark dense outlined").style(
                "width:100%; font-size:0.78rem; margin-top:6px;")
            novoe_nazv = ui.input("Название по-человечески").props(
                "dark dense outlined").style(
                "width:100%; font-size:0.78rem; margin-top:6px;")

            def _kopiya():
                ok, msg = razmnozhit(c, novoe_imya.value or "",
                                     (novoe_nazv.value or "").strip())
                ui.notify(("🧩 " if ok else "⚠ ") + msg,
                          color="positive" if ok else "negative")
                if ok:
                    sost["вybrano"] = _chistoe(novoe_imya.value or "")
                risovat_spisok()
                risovat_kartu()

            with ui.row().style("gap:8px; margin-top:10px; width:100%;"):
                ui.button("размножить", on_click=_kopiya).props(
                    "flat no-caps").style(
                    "padding:7px 18px; border-radius:8px; font-weight:700; "
                    "font-size:0.78rem; color:#fff; "
                    "background:linear-gradient(135deg,rgba(120,168,201,0.30),"
                    "rgba(120,168,201,0.18)); "
                    "border:1px solid rgba(120,168,201,0.55);")
                ui.element("div").style("flex:1")

                def _ubrat():
                    ok, msg = ubrat(c)
                    ui.notify(("🧩 " if ok else "⚠ ") + msg,
                              color="positive" if ok else "negative")
                    if ok:
                        sost["вybrano"] = None
                    risovat_spisok()
                    risovat_kartu()

                ui.button("вынуть картридж", on_click=_ubrat).props(
                    "flat no-caps").style(
                    "padding:7px 14px; border-radius:8px; font-size:0.74rem; "
                    "color:rgba(255,255,255,0.55); "
                    "border:1px solid rgba(255,255,255,0.18);")

            ui.html('<div class="c-podpis">кабинет</div>')
            ui.button(f'открыть /torg/{c["имя"]}',
                      on_click=lambda c=c: ui.navigate.to(
                          f'/torg/{c["имя"]}', new_tab=True)).props(
                "flat no-caps").style(
                "font-size:0.76rem; color:rgba(139,233,253,0.85);")

    risovat_spisok()
    risovat_kartu()
