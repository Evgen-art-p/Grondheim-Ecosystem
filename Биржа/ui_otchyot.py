# -*- coding: utf-8 -*-
# UI_OTCHYOT_V1
"""
СТРАНИЦА ОТЧЁТА · каждый кадр со своим разбором

ЗАЧЕМ. Прогон писал итог в консоль и складывал кадры по папкам. Ни
туда, ни туда никто не пойдёт: «в терминале неудобно — никто там
смотреть не будет, и в папках в репе искать тоже никто не будет»
(слово Шефа 11.09).

А смотреть надо: прогон и делается ради того, чтобы глазами увидеть,
где трейдер был прав, а где выдумал условие.

ЧТО ЭТО. Лента по местам, сверху вниз. На каждое место карточка:
слева кадр ТОГО САМОГО бара, справа — когда, что разбудило, что он
решил и его слова целиком, не обрезанные.

Сверху — итог: мест, входов, ведения, отказов, молчаний. И выбор
прогона: последний открывается сам, прошлые — из списка.

ОТКУДА БЕРЁТ. Из `места.jsonl`, который отчёт уже пишет, и из
подпапки `кадры`. Ничего не пересчитывает и ничего не меняет:
страница только показывает.

    /otchyot                  — последний прогон торгового цеха
    /otchyot/{ceh}            — последний прогон этого цеха
    /otchyot/{ceh}/{папка}    — конкретный прогон

`шесть·проверено·до·корня`
"""
import json
from pathlib import Path

from nicegui import app, ui

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
_CEHA = _REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха"

# кадры отдаём как статику — иначе браузер их не покажет
try:
    if _CEHA.exists():
        app.add_static_files("/otchyot-kadry", str(_CEHA))
except Exception as _e:
    print(f"[ОТЧЁТ] статика кадров не поднялась: {_e}")

FON = "#0d1117"
RAMKA = "1px solid rgba(255,255,255,0.10)"


def _progony(ceh: str) -> list:
    """Папки прогонов, свежие первыми."""
    p = _CEHA / ceh / "прогоны"
    if not p.exists():
        return []
    return sorted((d for d in p.iterdir() if d.is_dir()),
                  key=lambda d: d.name, reverse=True)


def _mesta(papka: Path) -> list:
    f = papka / "места.jsonl"
    if not f.exists():
        return []
    out = []
    for s in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = s.strip()
        if not s:
            continue
        try:
            out.append(json.loads(s))
        except Exception:
            continue
    return out


def _chto_sdelal(m: dict) -> tuple:
    """(метка, цвет) — вошёл, ведёт, отказался или промолчал."""
    d = str(m.get("действие") or "").upper()
    v = str(m.get("вердикт") or "").upper()
    if d == "ENTER" or v in ("APPROVED", "ENTER", "OK"):
        c = m.get("цена_входа")
        s = m.get("стоп_входа")
        hvost = (f" @ {c}" if c else "") + (f", стоп {s}" if s else "")
        return f"ВОШЁЛ{hvost}", "#3ddc6b"
    if d in ("HOLD", "MOVE_STOP", "ADD", "CLOSE"):
        return {"HOLD": "ДЕРЖУ", "MOVE_STOP": "СТОП ПЕРЕНЁС",
                "ADD": "ДОЛИЛ", "CLOSE": "ЗАКРЫЛ"}[d], "#4d9bff"
    if d == "WAIT" or v in ("REJECTED", "WAIT"):
        return "ОТКАЗ", "#ffb454"
    return "ПОДУМАЛ, приказа не было", "#ff5c5c"


def _shapka(ceh: str, papka: Path, mesta: list):
    schet = {"ВОШЁЛ": 0, "ВЕДЕНИЕ": 0, "ОТКАЗ": 0, "БЕЗ ПРИКАЗА": 0}
    for m in mesta:
        metka, _ = _chto_sdelal(m)
        if metka.startswith("ВОШЁЛ"):
            schet["ВОШЁЛ"] += 1
        elif metka in ("ДЕРЖУ", "СТОП ПЕРЕНЁС", "ДОЛИЛ", "ЗАКРЫЛ"):
            schet["ВЕДЕНИЕ"] += 1
        elif metka == "ОТКАЗ":
            schet["ОТКАЗ"] += 1
        else:
            schet["БЕЗ ПРИКАЗА"] += 1

    with ui.element("div").style(
        f"background:{FON}; border:{RAMKA}; border-radius:14px; "
        f"padding:16px 20px; margin-bottom:18px;"
    ):
        with ui.row().style("align-items:baseline; gap:14px; width:100%;"):
            ui.html('<span style="color:rgba(255,255,255,0.9); '
                    'font-weight:700; letter-spacing:0.08em;">'
                    'ОТЧЁТ ПРОГОНА</span>')
            ui.html(f'<span style="color:rgba(255,255,255,0.45); '
                    f'font-size:0.8rem;">{papka.name} · цех {ceh}</span>')
            ui.element("div").style("flex:1")
            ui.button("← в кабинет",
                      on_click=lambda: ui.navigate.to(f"/torg/{ceh}")
                      ).props("flat no-caps dense").style(
                "color:rgba(255,255,255,0.5); font-size:0.75rem;")

        ui.html(
            '<div style="margin-top:10px; display:flex; gap:18px; '
            'flex-wrap:wrap; font-size:0.82rem;">'
            + f'<span style="color:rgba(255,255,255,0.75);">мест: '
              f'<b>{len(mesta)}</b></span>'
            + f'<span style="color:#3ddc6b;">вошёл: '
              f'<b>{schet["ВОШЁЛ"]}</b></span>'
            + f'<span style="color:#4d9bff;">ведение: '
              f'<b>{schet["ВЕДЕНИЕ"]}</b></span>'
            + f'<span style="color:#ffb454;">отказов: '
              f'<b>{schet["ОТКАЗ"]}</b></span>'
            + f'<span style="color:#ff5c5c;">без приказа: '
              f'<b>{schet["БЕЗ ПРИКАЗА"]}</b></span>'
            + '</div>')

        # выбор другого прогона
        vse = _progony(ceh)
        if len(vse) > 1:
            with ui.row().style("margin-top:10px; gap:6px; "
                                "flex-wrap:wrap; align-items:center;"):
                ui.html('<span style="color:rgba(255,255,255,0.4); '
                        'font-size:0.72rem;">другие прогоны:</span>')
                for d in vse[:10]:
                    if d.name == papka.name:
                        continue
                    ui.button(
                        d.name,
                        on_click=lambda _=None, n=d.name:
                            ui.navigate.to(f"/otchyot/{ceh}/{n}")
                    ).props("flat no-caps dense").style(
                        "font-size:0.7rem; color:rgba(120,168,201,0.9);")


def _kartochka(ceh: str, papka: Path, nomer: int, m: dict):
    metka, cvet = _chto_sdelal(m)
    kadr = str(m.get("кадр") or "")
    kogda = str(m.get("когда_на_рынке") or m.get("место_найдено_на") or "?")
    nayden = str(m.get("место_найдено_на") or "")
    povod = str(m.get("разворотный") or "")
    cena_r = m.get("цена_разворотного")
    skazal = str(m.get("сказал") or m.get("причина") or "").strip()

    with ui.element("div").style(
        f"background:{FON}; border:{RAMKA}; border-left:3px solid {cvet}; "
        f"border-radius:12px; padding:14px 16px; margin-bottom:14px;"
    ):
        with ui.row().style("gap:16px; width:100%; align-items:flex-start; "
                            "flex-wrap:wrap;"):
            # кадр
            if kadr:
                ui.html(
                    f'<a href="/otchyot-kadry/{ceh}/прогоны/{papka.name}'
                    f'/кадры/{kadr}" target="_blank">'
                    f'<img src="/otchyot-kadry/{ceh}/прогоны/{papka.name}'
                    f'/кадры/{kadr}" '
                    f'style="width:460px; max-width:46vw; border-radius:8px; '
                    f'border:1px solid rgba(255,255,255,0.08);"></a>')
            else:
                ui.html('<div style="width:460px; max-width:46vw; '
                        'height:120px; display:flex; align-items:center; '
                        'justify-content:center; border-radius:8px; '
                        'border:1px dashed rgba(255,255,255,0.15); '
                        'color:rgba(255,255,255,0.3); font-size:0.75rem;">'
                        'кадра нет</div>')

            # разбор
            with ui.element("div").style("flex:1; min-width:280px;"):
                ui.html(
                    f'<div style="display:flex; gap:10px; '
                    f'align-items:baseline; flex-wrap:wrap;">'
                    f'<span style="color:rgba(255,255,255,0.35); '
                    f'font-size:0.72rem;">{nomer:02d}</span>'
                    f'<span style="color:rgba(255,255,255,0.9); '
                    f'font-weight:700; font-size:0.86rem;">{kogda}</span>'
                    f'<span style="color:{cvet}; font-weight:700; '
                    f'font-size:0.82rem;">{metka}</span></div>')

                _hv = []
                if povod:
                    _hv.append(f"разбудило: {povod}"
                               + (f" @ {cena_r}" if cena_r else ""))
                if nayden and nayden != kogda:
                    _hv.append(f"место найдено на {nayden}")
                if m.get("этаж"):
                    _hv.append(f"{m.get('инструмент', '')} "
                               f"{m.get('этаж', '')}".strip())
                if _hv:
                    ui.html(f'<div style="color:rgba(255,255,255,0.45); '
                            f'font-size:0.74rem; margin-top:4px;">'
                            f'{" · ".join(_hv)}</div>')

                if skazal:
                    ui.html(
                        f'<div style="color:rgba(255,255,255,0.78); '
                        f'font-size:0.82rem; line-height:1.55; '
                        f'margin-top:10px; white-space:pre-wrap;">'
                        f'{skazal}</div>')


def page_otchyot(ceh: str = "торговый_хаос", papka: str = ""):
    """Страница отчёта. Пусто — берём свежий прогон цеха."""
    ui.query("body").style(f"background:#070a0e;")
    with ui.element("div").style(
        "max-width:1180px; margin:0 auto; padding:22px 18px 60px;"
    ):
        vse = _progony(ceh)
        if not vse:
            ui.html('<div style="color:rgba(255,255,255,0.6);">'
                    'Прогонов пока нет — сходи в кабинет и запусти.</div>')
            ui.button("← в кабинет",
                      on_click=lambda: ui.navigate.to(f"/torg/{ceh}")
                      ).props("flat no-caps")
            return

        p = None
        if papka:
            p = next((d for d in vse if d.name == papka), None)
        if p is None:
            p = vse[0]

        mesta = _mesta(p)
        _shapka(ceh, p, mesta)

        if not mesta:
            ui.html('<div style="color:rgba(255,255,255,0.5); '
                    'font-size:0.85rem;">В этом прогоне мест не '
                    'записано.</div>')
            return

        for i, m in enumerate(mesta, 1):
            _kartochka(ceh, p, i, m)
