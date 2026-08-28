# -*- coding: utf-8 -*-
# STRANICA_STUDII_V1
"""
ПАТЧ · Рабочая страница Студии.

ЧТО КЛАДЁТ
    ГОРОД/ui_studia.py       страница цеха: наряд, пуск, волны, приёмка
    main.py                  роут /studia/{ceh}
    ГОРОД/ui_ceha.py         кнопка кабинета для цехов Студии
                             (была скрыта — «появится вместе с цехом»)

ЧЕГО СТРАНИЦА НЕ ЗНАЕТ
    Ни одного имени цеха. Ни фаз, ни чекпоинтов списком, ни отдельного
    пути «если турбо». Всё из манифеста: волны собирает шасси, роли и
    ключи берутся оттуда же. Появится второй цех — страница откроет
    его, не заметив.

    В старой странице было иначе: run_cartridge_pipeline() и рядом
    run_cartridge_turbo(), почти одинаковые, плюс DEPT_PIPELINE_CONFIG
    со списками чекпоинтов по цехам. Турбо прорастил себе третий путь
    после манифеста и движка.

ЧТО ВЗЯТО ИЗ СТАРОЙ
    поле наряда · живой показ по ходу · история прогонов · просмотр
    того, что дало каждое место.

ЧТО НЕ ВЗЯТО
    клиенты и их память (сущности нет), экспорт в docx/pdf, диалоги
    ассетов, Виктор по имени, чекпоинты (вернём, когда понадобятся —
    не раньше).

    шесть·проверено·до·корня
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "STRANICA_STUDII_V1"

STRANICA = '''# -*- coding: utf-8 -*-
# STRANICA_STUDII_V1
"""
СТУДИЯ · рабочая страница цеха.

Страница ничего не знает про устройство цеха. Спрашивает манифест,
показывает волны, зовёт места по одному и рисует, что вышло.

    /studia/турбо        цех Студии по имени папки

    шесть·проверено·до·корня
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from nicegui import ui

KOREN = Path(__file__).resolve().parent.parent
STUDIYA = KOREN / "GRONDHEIM_CITY" / "Студия"

CSS = """
<style>
.s-page { background:#0b0f14; color:#e6edf3;
          font-family:'Inter',system-ui,sans-serif; }
.s-head { padding:14px 20px; border-bottom:1px solid rgba(255,255,255,0.08);
          display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
.s-body { display:flex; gap:16px; padding:16px 20px; align-items:flex-start; }
.s-left { width:340px; flex-shrink:0; }
.s-right { flex:1; min-width:0; }
.s-card { background:rgba(255,255,255,0.03); border-radius:14px;
          border:1px solid rgba(255,255,255,0.08); padding:14px;
          margin-bottom:12px; }
.s-podpis { color:rgba(255,255,255,0.42); font-size:0.66rem;
            letter-spacing:0.08em; text-transform:uppercase;
            margin:12px 0 6px; }
.s-volna { border-left:2px solid rgba(139,233,253,0.25);
           padding-left:12px; margin-bottom:10px; }
</style>
"""


def _shassi():
    """Конвейер лежит в Студии — кириллица в пути, грузим по файлу."""
    put = STUDIYA / "конвейер.py"
    if not put.exists():
        return None
    spec = importlib.util.spec_from_file_location("_konveyer", put)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _zhurnal(m: dict, skolko: int = 8) -> list:
    put = Path(m["_папка"]) / "журналы" / "прогоны.jsonl"
    if not put.exists():
        return []
    out = []
    for stroka in put.read_text(encoding="utf-8").splitlines()[-skolko:]:
        try:
            out.append(json.loads(stroka))
        except Exception:
            pass
    return list(reversed(out))


def page_studia(ceh_imya: str = "турбо"):
    ui.add_head_html(CSS)
    ui.query("body").classes("s-page")

    K = _shassi()
    if K is None:
        ui.label("Шасси не найдено: GRONDHEIM_CITY/Студия/конвейер.py")
        return
    try:
        m = K.ceh("Студия", ceh_imya)
        volny = K.truba(m)
    except SystemExit as e:
        ui.label(f"Цех не собрался: {e}").style("color:#ff8080;")
        return

    sost: dict[str, Any] = {"идёт": False, "стол": {}}
    refs: dict[str, Any] = {}

    with ui.element("div").classes("s-head"):
        ui.html(f'<div style="font-weight:800; letter-spacing:0.14em; '
                f'font-size:0.95rem;">СТУДИЯ · {m.get("название", ceh_imya)}'
                f'</div>')
        ui.html(f'<div style="color:rgba(139,233,253,0.75); '
                f'font-size:0.72rem;">судья: {m.get("судья", "—")} · '
                f'мест {len(m.get("слоты", []))} · проб {m.get("проб", "—")}'
                f'</div>')
        ui.element("div").style("flex:1")
        ui.button("← КАРТРИДЖИ",
                  on_click=lambda: ui.navigate.to("/ceha")).props(
            "flat no-caps").style("font-size:0.72rem; "
                                  "color:rgba(139,233,253,0.85);")

    with ui.element("div").classes("s-body"):
        with ui.element("div").classes("s-left"):
            with ui.element("div").classes("s-card"):
                ui.html('<div class="s-podpis">наряд</div>')
                tema = ui.input("Тема ролика").props(
                    "dark dense outlined").style("width:100%;")
                ploshchadka = ui.select(
                    ["YouTube Shorts", "TikTok", "Reels", "VK", "универсально"],
                    value="YouTube Shorts", label="Площадка").props(
                    "dark dense outlined").style("width:100%; margin-top:6px;")
                cel = ui.select(["охват", "доверие", "продажа", "польза"],
                                value="охват", label="Цель").props(
                    "dark dense outlined").style("width:100%; margin-top:6px;")

                refs["pusk"] = ui.button("ПУСТИТЬ").props(
                    "flat no-caps").style(
                    "width:100%; margin-top:12px; padding:9px; "
                    "border-radius:8px; font-weight:700; font-size:0.8rem; "
                    "color:#fff; background:linear-gradient(135deg,"
                    "rgba(80,250,123,0.28),rgba(80,250,123,0.16)); "
                    "border:1px solid rgba(80,250,123,0.5);")
                ui.label("Руки цеха не подключены: места подумают, "
                         "файлов не будет. Приёмка это увидит.").style(
                    "color:rgba(255,255,255,0.35); font-size:0.7rem; "
                    "margin-top:8px; display:block;")

            with ui.element("div").classes("s-card"):
                ui.html('<div class="s-podpis">прошлые прогоны</div>')
                refs["istoriya"] = ui.element("div")

        with ui.element("div").classes("s-right"):
            with ui.element("div").classes("s-card"):
                ui.html('<div class="s-podpis">труба</div>')
                refs["truba"] = ui.element("div")
            refs["itog"] = ui.element("div")

    # ── рисуем ────────────────────────────────────────────────

    def risovat_trubu(idut: dict | None = None):
        refs["truba"].clear()
        idut = idut or {}
        with refs["truba"]:
            for i, volna in enumerate(volny, 1):
                with ui.element("div").classes("s-volna"):
                    znak = "  ∥ параллель" if len(volna) > 1 else ""
                    ui.label(f"волна {i}{znak}").style(
                        "color:rgba(255,255,255,0.35); font-size:0.68rem; "
                        "text-transform:uppercase; letter-spacing:0.08em;")
                    for s in volna:
                        st = idut.get(s["слот"], {})
                        cvet = {"идёт": "rgba(255,220,120,0.9)",
                                "готово": "rgba(80,250,123,0.9)",
                                "беда": "rgba(255,120,120,0.9)"}.get(
                            st.get("что"), "rgba(255,255,255,0.5)")
                        hvost = ""
                        if st.get("что") == "готово":
                            hvost = (f"   {st.get('сек', 0):.1f}с  дал: "
                                     f"{', '.join(st.get('дал', [])) or '—'}")
                            if st.get("не_дал"):
                                hvost += f"   НЕ ДАЛ: {st['не_дал']}"
                        elif st.get("что") == "идёт":
                            hvost = "   думает…"
                        elif st.get("что") == "беда":
                            hvost = f"   {st.get('беда', '')}"
                        ui.label(
                            f'{s["слот"]} · {s.get("роль", "")}'
                            f'   {s.get("берёт", [])} → {s.get("даёт", [])}'
                            f'{hvost}').style(
                            f"color:{cvet}; font-size:0.76rem; "
                            f"font-family:monospace; display:block; "
                            f"margin:3px 0;")

    def risovat_istoriyu():
        refs["istoriya"].clear()
        zapisi = _zhurnal(m)
        with refs["istoriya"]:
            if not zapisi:
                ui.label("прогонов ещё не было").style(
                    "color:rgba(255,255,255,0.3); font-size:0.75rem;")
                return
            for z in zapisi:
                tema_z = (z.get("наряд") or {}).get("тема", "—")
                ruki = "с руками" if z.get("с_руками") else "холостой"
                sek = sum(x.get("секунд", 0) for x in z.get("места", []))
                ui.label(f'{z.get("ts", "")[:16]} · {ruki} · {sek:.0f}с\\n'
                         f'{tema_z[:40]}').style(
                    "color:rgba(255,255,255,0.55); font-size:0.72rem; "
                    "display:block; white-space:pre-line; "
                    "border-bottom:1px solid rgba(255,255,255,0.06); "
                    "padding:5px 0;")

    def risovat_itog(stol: dict):
        refs["itog"].clear()
        dopusk = stol.get("допуск") or {}
        with refs["itog"]:
            with ui.element("div").classes("s-card"):
                ui.html('<div class="s-podpis">приёмка цеха</div>')
                if not dopusk:
                    ui.label("допуска нет — приёмка не отработала").style(
                        "color:rgba(255,255,255,0.4); font-size:0.8rem;")
                    return
                status = str(dopusk.get("статус", "?"))
                cvet = ("rgba(80,250,123,0.9)" if status == "APPROVED"
                        else "rgba(255,150,80,0.95)")
                ui.label(status).style(
                    f"color:{cvet}; font-weight:800; font-size:1.1rem;")
                upalo = dopusk.get("failed_checks") or []
                if upalo:
                    ui.label("не прошло: " + ", ".join(map(str, upalo))).style(
                        "color:rgba(255,255,255,0.6); font-size:0.78rem; "
                        "font-family:monospace; display:block; margin-top:6px;")
                if status != "APPROVED":
                    ui.label("Руки не подключены — файлов нет, и приёмка "
                             "честно это показала. Так и должно быть.").style(
                        "color:rgba(255,255,255,0.35); font-size:0.72rem; "
                        "display:block; margin-top:8px;")

            with ui.element("div").classes("s-card"):
                ui.html('<div class="s-podpis">что на столе</div>')
                for k in sorted(x for x in stol if x != "наряд"):
                    with ui.expansion(k).classes("w-full").style(
                            "font-size:0.78rem;"):
                        ui.code(json.dumps(stol[k], ensure_ascii=False,
                                           indent=2)[:4000]).style(
                            "font-size:0.7rem;")

    # ── пуск ──────────────────────────────────────────────────

    async def pustit():
        if sost["идёт"]:
            ui.notify("уже идёт", color="warning")
            return
        if not (tema.value or "").strip():
            ui.notify("скажи тему ролика", color="warning")
            return

        sost["идёт"] = True
        refs["pusk"].disable()
        refs["itog"].clear()
        idut: dict = {}
        stol = {"наряд": {"тема": tema.value.strip(),
                          "площадка": ploshchadka.value,
                          "цель": cel.value}}
        zhurnal = []
        risovat_trubu(idut)

        from llm import chat

        for nomer, volna in enumerate(volny, 1):
            for s in volna:
                idut[s["слот"]] = {"что": "идёт"}
                risovat_trubu(idut)
                nachalo = datetime.now()
                try:
                    sistema = K.bumaga(m, s)
                    znanie = K.znaniya(m, s)
                    vhod = {k: stol.get(k) for k in s.get("берёт", [])}
                    otvet = await asyncio.to_thread(
                        chat, system=sistema,
                        user="Вот что тебе пришло:\\n\\n"
                             + json.dumps(vhod, ensure_ascii=False, indent=2),
                        knowledge=znanie)
                    d = K.razobrat(otvet)
                    moyo = d.get("моё", {}) or {}
                    dal, ne_dal = [], []
                    for k in s.get("даёт", []):
                        if k in moyo:
                            stol[k] = moyo[k]
                            dal.append(k)
                        else:
                            ne_dal.append(k)
                    sek = (datetime.now() - nachalo).total_seconds()
                    idut[s["слот"]] = {"что": "готово", "сек": sek,
                                       "дал": dal, "не_дал": ne_dal}
                    zhurnal.append({"слот": s["слот"], "роль": s.get("роль", ""),
                                    "волна": nomer, "секунд": round(sek, 1),
                                    "дал": dal, "не_дал": ne_dal,
                                    "знаний": len(s.get("знания", []))})
                except Exception as e:
                    idut[s["слот"]] = {"что": "беда", "беда": str(e)[:120]}
                    zhurnal.append({"слот": s["слот"], "беда": str(e)[:200]})
                risovat_trubu(idut)

        try:
            K.zapisat(m, stol["наряд"], stol, zhurnal, False)
        except Exception:
            pass

        sost["стол"] = stol
        risovat_itog(stol)
        risovat_istoriyu()
        refs["pusk"].enable()
        sost["идёт"] = False
        ui.notify("прогон закончен", color="positive")

    refs["pusk"].on_click(pustit)
    risovat_trubu()
    risovat_istoriyu()
'''

# ── правки в main.py и ui_ceha.py ────────────────────────────

M_STAR = '''from ui_ceha import page_ceha
@ui.page("/ceha")
def _ceha():
    page_ceha()'''

M_NOV = '''from ui_ceha import page_ceha
@ui.page("/ceha")
def _ceha():
    page_ceha()

# ── СТУДИЯ — рабочая страница цеха (STRANICA_STUDII_V1) ──
# Наряд, пуск, волны, приёмка. Имени цеха не знает: берёт из адреса,
# устройство — из манифеста.
from ui_studia import page_studia

@ui.page("/studia/{ceh}")
def _studia(ceh: str = "турбо"):
    page_studia(ceh)

@ui.page("/studia")
def _studia0():
    page_studia()'''

C_STAR = '''            # MENEDZHER_KARTRIDZHEY_V1: /torg/ — торговый кабинет, роут
            # биржевой. У Студии кабинет свой, появится с первым цехом.
            if c.get("квартал") != "Биржа":
                return
            ui.html('<div class="c-podpis">кабинет</div>')'''

C_NOV = '''            # STRANICA_STUDII_V1: у каждого квартала свой кабинет.
            # Появился цех Студии — появилась и кнопка к нему.
            ui.html('<div class="c-podpis">кабинет</div>')
            if c.get("квартал") == "Студия":
                ui.button(f'открыть /studia/{c["имя"]}',
                          on_click=lambda c=c: ui.navigate.to(
                              f'/studia/{c["имя"]}', new_tab=True)).props(
                    "flat no-caps").style(
                    "font-size:0.76rem; color:rgba(139,233,253,0.85);")
                return
            if c.get("квартал") != "Биржа":
                return'''


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


def polozhit(put: Path, tekst: str, imya: str) -> str:
    if put.exists():
        if put.read_text(encoding="utf-8") == tekst:
            return "уже стоит, не трогал"
        bak = put.with_suffix(put.suffix + f".bak_{_teper()}")
        shutil.copyfile(put, bak)
        put.write_text(tekst, encoding="utf-8")
        return f"обновлено, старое в {bak.name}"
    put.write_text(tekst, encoding="utf-8")
    return f"положено ({len(tekst.splitlines())} строк)"


def patchit(put: Path, star: str, nov: str, marker: str) -> str:
    if not put.exists():
        return f"нет {put.name}"
    t = put.read_text(encoding="utf-8")
    if marker in t:
        return "уже пропатчен, не трогал"
    if t.count(star) != 1:
        return (f"якорь встречается {t.count(star)} раз — не рискую, "
                f"ничего не менял")
    bak = put.with_suffix(put.suffix + f".bak_{_teper()}")
    shutil.copyfile(put, bak)
    put.write_text(t.replace(star, nov, 1), encoding="utf-8")
    return f"пропатчен, старый в {bak.name}"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

    koren = naiti_koren()
    print(f"Корень: {koren}\n")

    if not (koren / "GRONDHEIM_CITY" / "Студия" / "конвейер.py").exists():
        raise SystemExit("Шасси нет — сперва накати konveyer_studii.py")

    print("ui_studia.py: " + polozhit(koren / "ГОРОД" / "ui_studia.py",
                                      STRANICA, "страница"))
    print("main.py:      " + patchit(koren / "main.py", M_STAR, M_NOV,
                                     MARKER))
    print("ui_ceha.py:   " + patchit(koren / "ГОРОД" / "ui_ceha.py",
                                     C_STAR, C_NOV, MARKER))

    print("\nПроверка: страница читает манифест, не зная имени цеха.")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_k", koren / "GRONDHEIM_CITY" / "Студия" / "конвейер.py")
    k = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(k)  # type: ignore[union-attr]
    m = k.ceh("Студия", "турбо")
    for i, v in enumerate(k.truba(m), 1):
        for s in v:
            print(f"  волна {i}  {s['слот']} · {s.get('роль')}")

    print("\nГотово. Перезапусти приложение и открой:\n"
          "  /ceha  →  Студия  →  ТУРБО  →  «открыть /studia/турбо»\n"
          "  или прямо /studia/турбо\n\n"
          "Впиши тему, нажми ПУСТИТЬ. Места пойдут волнами, приёмка\n"
          "внизу покажет допуск. Руки не подключены — ждём BLOCKED.\n"
          "шесть·проверено·до·корня")


if __name__ == "__main__":
    main()
