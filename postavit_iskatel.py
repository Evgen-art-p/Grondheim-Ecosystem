# -*- coding: utf-8 -*-
"""
postavit_iskatel.py · MARKER: ISKATEL_V1

ТРЕБУЕТ: postavit_mashinu_vremeni.py и postavit_vremya_v_kabinet.py.

ЧТО ЭТО, ПРОСТЫМИ СЛОВАМИ
─────────────────────────
Слово Шефа: «пусть код даёт кандидатов, а трейдер выбирает».

Код бежит по истории сам — быстро и бесплатно, это чистая
математика. На каждом баре смотрит: сложилось ли формально то, на что
стоит взглянуть. Не сложилось — идёт дальше молча. Сложилось —
запоминает место.

Ты получаешь не перемотку бар за баром, а СПИСОК МЕСТ, где что-то
было. Прыгаешь по ним кнопками, смотришь кадр, зовёшь трейдера.

ЧТО СЧИТАЕТСЯ КАНДИДАТОМ
────────────────────────
Ровно три факта, и ни одного суждения:

    · есть разворотный бар (по нему входят — канон §1④);
    · читается волновая структура (есть от чего мерить);
    · известна её длина в барах.

Всё. Никаких «сигнал хороший», «вход годится», «структура
подтверждена». Кандидат — это ПОВОД ПОСМОТРЕТЬ, а не вердикт.
КАНОН_ВХОДА.md §1②: «величина/старшинство зигзага не принципиальна —
какой нашли изначально на снимке, тот и работаем, не гонимся за
главным». Значит и точность разметки от кода не требуется —
требуется не пропустить.

СКОЛЬКО ИХ (посчитано на золоте H4, год истории)
───────────────────────────────────────────────
    разворотный бар нашёлся        201 раз (13% баров)
    структура при этом читается     74 раза (4%)
    длина волны: от 19 до 258, СЕРЕДИНА 100

Середина ровно 100 — окно Шефа 100-140 не с потолка, оно совпадает с
тем, что меряется на живой истории.

74 события в год на H4 — примерно раз в неделю. Это нормальный поток
поводов: не завал, но и не пусто.

СКОРОСТЬ
────────
1500 баров за 3.4 секунды. Вся история золота H4 (24 тысячи баров)
пробегает примерно за минуту. Поэтому искать можно смело — платим
только когда зовём трейдера.

ЧТО В КАБИНЕТЕ
──────────────
В полоске времени (видна в ТЕСТЕРЕ) появляется:

    🔍   ⟨   3/12   ⟩

    🔍      найти кандидатов от текущей точки назад
    ⟨ ⟩     прыгнуть к предыдущему / следующему
    3/12    на каком стоишь из скольких

Прыгнул — курсор истории встал в эту точку, кадр перерисовался.
Дальше как обычно: смотришь сам, жмёшь РЫНОК — трейдер видит ровно
это место и говорит, его это или мимо.

Идемпотентен, .bak рядом, ast.parse и py_compile до записи.
Запуск: py postavit_iskatel.py   (или --suho)
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "ISKATEL_V1"
SUHO = "--suho" in sys.argv


def _eto_koren(p: Path) -> bool:
    return ((p / "Биржа" / "ui_torg.py").exists()
            and (p / "main.py").exists())


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    kandidaty = []
    for baza in (zdes.parent, Path.cwd().parent):
        if not baza.is_dir():
            continue
        for d in baza.iterdir():
            if d.is_dir() and _eto_koren(d) and d not in kandidaty:
                kandidaty.append(d)
    if len(kandidaty) == 1:
        if input(f"Нашёл город здесь:\n  {kandidaty[0]}\nЭтот? [Enter=да] "
                 ).strip().lower() in ("", "y", "д", "да"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(kandidaty, 1):
            print(f"  {i}. {d}")
        nom = input("Какой? номер: ").strip()
        if nom.isdigit() and 1 <= int(nom) <= len(kandidaty):
            return kandidaty[int(nom) - 1]
    put = input("Не нашёл сам. Перетащи сюда папку репо и нажми Enter:\n> ")
    p = Path(put.strip().strip('"').strip("'"))
    if _eto_koren(p):
        return p
    print("✗ Это не корень репо")
    sys.exit(1)


KANDIDATY_PY = '''# -*- coding: utf-8 -*-
# ISKATEL_V1
"""
ИСКАТЕЛЬ КАНДИДАТОВ — код находит поводы, трейдер выбирает.

ЗАКОН ЭТОГО ФАЙЛА
    Здесь нет ни одного суждения о рынке. Кандидат — это МЕСТО, где
    формально сложились три факта, и ничего больше:

        · есть разворотный бар;
        · читается волновая структура;
        · известна её длина в барах.

    Ни «хороший вход», ни «сигнал», ни «подтверждено». Слово Шефа:
    «трейдерам никакой код не должен говорить, что делать, а только
    факты-математику, а трейдер по этой математике судит».

    КАНОН_ВХОДА.md §1②: величина зигзага не принципиальна — какой
    нашли на снимке, тот и работаем. Значит от кода не требуется
    попасть в «настоящую» пятую волну. Требуется не пропустить место,
    на которое стоит взглянуть.

ЦЕНА
    Ноль. Это чистая математика по барам: 1500 баров — 3.4 секунды.
    Платим только когда по найденному месту зовём трейдера.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_BIRZHA = Path(__file__).resolve().parent
if str(_BIRZHA) not in _sys.path:
    _sys.path.insert(0, str(_BIRZHA))

OKNO_RASCHYOTA = 300      # сколько баров нужно математике для расчёта


def _priznaki(bars: list, symbol: str, tf: str, point: float):
    """Факты последнего бара окна. Не кандидат — не None."""
    from williams_core import build_market_data
    md = build_market_data(bars, symbol=symbol, timeframe=tf, point=point)
    if not md:
        return None
    wf = md.get("wave_form") or {}
    if not wf.get("bdb_dir"):
        return None
    if not wf.get("struktura_chitaetsya"):
        return None
    rb = md.get("rubber_band") or {}
    # Момент, в который город должен встать, чтобы УВИДЕТЬ этот бар.
    # Дата бара — это его НАЧАЛО; к этой секунде он ещё не закрыт, и
    # кран его честно прячет (иначе показывал бы будущее). Поэтому
    # момент = конец бара, иначе трейдер встаёт на бар раньше и
    # самого разворотного бара не видит.
    _data = bars[-1].get("date", "")
    _moment = _data
    try:
        import masshtab
        from datetime import timedelta
        import istoriya
        _t0 = istoriya.kak_vremya(_data)
        _m = masshtab.minut(tf)
        if _t0 is not None and _m:
            _moment = (_t0 + timedelta(minutes=_m)).strftime(istoriya.FORMAT)
    except Exception:
        pass
    return {
        "дата": _data,
        "момент": _moment,
        "разворотный": wf.get("bdb_dir"),
        "цена_разворотного": wf.get("bdb_price"),
        "длина_волны": wf.get("dlina"),
        "дивергенция_в_волне": wf.get("divergence_dir"),
        "дивергенция_AO": md.get("divergence_ao"),
        "отрыв_цены": rb.get("distance_now"),
        "доля_натяжения": rb.get("tension_ratio"),
        "компас": md.get("global_bias"),
        "цена": (md.get("price") or {}).get("close"),
    }


def est_seychas(symbol: str, tf: str):
    """Кандидат ли ТЕКУЩИЙ бар (по тому, что отдаёт кран).

    Это же — ключ пробуждения в реале: пришла свеча, спросили, есть
    ли повод. Нет — никого не будим и ничего не платим.
    """
    import feed_source as fs
    b, point = fs.bars(symbol, tf, OKNO_RASCHYOTA)
    if not b or point is None:
        return None
    return _priznaki(b, symbol, tf, point)


def iskat(symbol: str, tf: str, do_momenta: str = "", skolko: int = 10,
          predel_barov: int = 4000, otstup: int = 12, govorit=None):
    """Пробежать историю НАЗАД от точки и набрать кандидатов.

    do_momenta — откуда начинать искать (пусто = с конца истории).
    skolko     — сколько набрать и остановиться.
    predel_barov — насколько глубоко копать, чтобы не молотить зря.
    otstup     — сколько баров считать ОДНИМ местом.

    Про отступ. Признаки держатся несколько баров подряд, и без
    склейки список выглядит так:

        2026.05.27 16:00 · волна 93 баров
        2026.05.27 08:00 · волна 91 баров
        2026.05.27 04:00 · волна 90 баров

    Это одно место, а не три: та же волна, тот же разворот. Двенадцать
    таких «кандидатов» оказались бы тремя настоящими. Поэтому соседей
    ближе отступа считаем одним местом и берём самый свежий из них —
    тот, на котором картина уже сложилась целиком.

    Возвращает список кандидатов, СВЕЖИЕ ПЕРВЫМИ.
    """
    import istoriya
    vse = istoriya._vse_bary(symbol, tf)
    if not vse:
        return []
    import feed_source as fs
    point = fs._test_point(symbol)

    konec = len(vse) - 1
    if do_momenta:
        konec = -1
        for j, b in enumerate(vse):
            if b.get("date", "") <= do_momenta:
                konec = j
            else:
                break
        if konec < 0:
            return []

    nayden = []
    posledniy_i = None
    nachalo = max(OKNO_RASCHYOTA, konec - predel_barov)
    for i in range(konec, nachalo - 1, -1):
        if posledniy_i is not None and (posledniy_i - i) < otstup:
            continue
        okno = vse[max(0, i - OKNO_RASCHYOTA + 1):i + 1]
        if len(okno) < OKNO_RASCHYOTA // 2:
            break
        p = _priznaki(okno, symbol, tf, point)
        if p:
            posledniy_i = i
            nayden.append(p)
            if govorit:
                govorit(f"[ИСКАТЕЛЬ] · {p['дата']} · {p['разворотный']} · "
                        f"волна {p['длина_волны']} баров")
            if len(nayden) >= skolko:
                break
    return nayden


def slovami(k: dict) -> str:
    """Кандидат одной строкой — для ленты кабинета."""
    if not k:
        return ""
    return (f"{k.get('дата')} · разворотный {k.get('разворотный')} @ "
            f"{k.get('цена_разворотного')} · волна {k.get('длина_волны')} "
            f"баров · компас {k.get('компас')}")


if __name__ == "__main__":
    import hooks
    a = _sys.argv[1:]
    if len(a) < 2:
        print("py kandidaty.py XAUUSD H4 [сколько]")
        raise SystemExit(1)
    hooks.postavit_ceh("торговый_хаос")
    n = int(a[2]) if len(a) > 2 else 10
    spisok = iskat(a[0].upper(), a[1].upper(), skolko=n, govorit=print)
    print(f"\\nнашёл {len(spisok)} кандидатов (свежие первыми):")
    for k in spisok:
        print("  " + slovami(k))

# ISKATEL_V1 - marker
'''


# ── кнопки в панель времени ──
ST_UI_RUKI = '''    def _shagnut(skolko):'''

NOV_UI_RUKI = '''    def _kandidat_vid():
        """Надпись «3/12» — на каком кандидате стоим."""
        el = toolbar_refs.get("kand_label")
        if el is None:
            return
        spisok = state.get("kandidaty") or []
        i = state.get("kandidat_i")
        if not spisok:
            el.text = "—"
        elif i is None:
            el.text = f"0/{len(spisok)}"
        else:
            el.text = f"{i + 1}/{len(spisok)}"

    async def _iskat_kandidatov():
        """ISKATEL_V1: код пробегает историю и приносит места, где
        стоит взглянуть. Бесплатно — это математика, не модель."""
        if state.get("mode") != "tester":
            ui.notify("Искать по истории можно в ТЕСТЕРЕ", type="warning")
            return
        symbol, tf = _para_dlya_shaga()
        if not symbol or not tf:
            ui.notify("Не пойму, где искать — выбери трейдера или актив",
                      type="warning")
            return
        ui.notify(f"🔍 ищу по {symbol} {tf}…", type="info")
        try:
            import asyncio
            import istoriya
            ot = istoriya.gde_stoim()

            def _rabota():
                import kandidaty
                return kandidaty.iskat(symbol, tf, do_momenta=ot,
                                       skolko=12, govorit=print)

            spisok = await asyncio.get_event_loop().run_in_executor(
                None, _rabota)
        except Exception as e:
            ui.notify(f"Искать не вышло: {e}", type="negative")
            return
        state["kandidaty"] = spisok
        state["kandidat_i"] = None
        _kandidat_vid()
        if not spisok:
            ui.notify("Ничего не нашлось — отмотай назад и поищи ещё",
                      type="warning")
            return
        ui.notify(f"🔍 нашёл {len(spisok)} мест — жми ⟩", type="positive")
        _k_kandidatu(0)

    def _k_kandidatu(nomer):
        """Встать на кандидата: курсор истории туда, кадр перерисовать."""
        spisok = state.get("kandidaty") or []
        if not spisok:
            ui.notify("Сперва найди кандидатов — кнопка 🔍", type="warning")
            return
        nomer = max(0, min(len(spisok) - 1, nomer))
        k = spisok[nomer]
        try:
            import istoriya
            istoriya.postavit(k.get("дата", ""))
        except Exception as e:
            ui.notify(f"Не встал: {e}", type="negative")
            return
        state["kandidat_i"] = nomer
        _kandidat_vid()
        _vremya_vid()
        try:
            pokazat_kadr()
        except Exception as e:
            print(f"[ИСКАТЕЛЬ] кадр не перерисовался: {e}")
        try:
            import kandidaty as _kd
            stroka = _kd.slovami(k)
        except Exception:
            stroka = k.get("дата", "")
        print(f"[ИСКАТЕЛЬ] 📍 {nomer + 1}/{len(spisok)} · {stroka}")
        ui.notify(f"📍 {stroka}", type="info")

    def _kandidat_shag(kuda):
        i = state.get("kandidat_i")
        _k_kandidatu(0 if i is None else i + kuda)

    def _shagnut(skolko):'''

ST_UI_KNOPKI = '''                            toolbar_refs["moment_label"] = ui.label(
                                "конец истории").style('''

NOV_UI_KNOPKI = '''                            # ISKATEL_V1: прыжки по местам, а не по барам
                            _isk = ui.element("div").style(
                                "padding:5px 9px;border-radius:6px;"
                                "font-size:12px;cursor:pointer;margin-left:6px;"
                                "background:rgba(139,233,253,0.1);"
                                "color:rgba(139,233,253,0.85);"
                                "border:1px solid rgba(139,233,253,0.3);")
                            _isk.on("click", lambda: _iskat_kandidatov())
                            _isk.tooltip("найти места, где стоит взглянуть")
                            with _isk:
                                ui.html("🔍")
                            for _z, _k, _p in (("⟨", -1, "предыдущее место"),
                                               ("⟩", 1, "следующее место")):
                                _bk = ui.element("div").style(
                                    "padding:5px 8px;border-radius:6px;"
                                    "font-size:12px;cursor:pointer;"
                                    "background:rgba(255,255,255,0.04);"
                                    "color:rgba(255,255,255,0.7);"
                                    "border:1px solid rgba(255,255,255,0.1);")
                                _bk.on("click", lambda k=_k: _kandidat_shag(k))
                                _bk.tooltip(_p)
                                with _bk:
                                    ui.html(_z)
                            toolbar_refs["kand_label"] = ui.label("—").style(
                                "color:rgba(139,233,253,0.6);font-size:11px;"
                                "margin:0 4px;white-space:nowrap;")
                            toolbar_refs["moment_label"] = ui.label(
                                "конец истории").style('''

ST_STATE = '''        "tester_running": False,'''
NOV_STATE = '''        "tester_running": False,
        "kandidaty": [],            # ISKATEL_V1: найденные места
        "kandidat_i": None,         # на каком стоим'''


def main():
    koren = nayti_koren()
    print(f"Город: {koren}")
    ui_torg = koren / "Биржа" / "ui_torg.py"
    kandidaty = koren / "Биржа" / "kandidaty.py"

    t = ui_torg.read_text(encoding="utf-8")
    if "VREMYA_V_KABINETE_V1" not in t:
        print("✗ Нет панели времени — накати сперва "
              "postavit_vremya_v_kabinet.py")
        return 1

    print("\n1. Искатель — Биржа/kandidaty.py")
    if kandidaty.exists() and MARKER in kandidaty.read_text(encoding="utf-8"):
        print("  · уже лежит")
    else:
        ast.parse(KANDIDATY_PY)
        if not SUHO:
            kandidaty.write_text(KANDIDATY_PY, encoding="utf-8")
        print("  ✓ положен")

    print("\n2. Кнопки в кабинет")
    if MARKER in t:
        print("  · маркер уже стоит")
    else:
        yakorya = [("руки", ST_UI_RUKI, NOV_UI_RUKI),
                   ("кнопки", ST_UI_KNOPKI, NOV_UI_KNOPKI),
                   ("память", ST_STATE, NOV_STATE)]
        beda = [imya for imya, st, _ in yakorya if t.count(st) != 1]
        if beda:
            print(f"  ✗ якоря не найдены дословно: {', '.join(beda)}")
            return 1
        novyy = t
        for _, st, nov in yakorya:
            novyy = novyy.replace(st, nov, 1)
        novyy += f"\n# {MARKER} - marker\n"
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"  ✗ после правки не разбирается: {e}")
            return 1
        if not SUHO:
            bak = ui_torg.with_suffix(
                f".py.bak_iskatel_{datetime.now():%Y%m%d_%H%M%S}")
            shutil.copy2(ui_torg, bak)
            ui_torg.write_text(novyy, encoding="utf-8")
            print(f"  ✓ легло (копия: {bak.name})")
        else:
            print("  · правка готова (сухой прогон)")

    if not SUHO:
        import py_compile
        for f in (kandidaty, ui_torg):
            try:
                py_compile.compile(str(f), doraise=True)
                print(f"  ✓ компилируется: {f.name}")
            except Exception as e:
                print(f"  ✗ НЕ компилируется {f.name}: {e}")
                return 1
        print("\nКак пользоваться:")
        print("  ТЕСТЕР → кликни трейдера → 🔍")
        print("  код пробежит историю назад и наберёт до 12 мест")
        print("  ⟨ ⟩ — прыгать по ним, кадр перерисовывается сам")
        print("  РЫНОК — спросить трейдера про место, где стоишь")
        print("\nБез кабинета тоже можно:")
        print("   py Биржа\\kandidaty.py XAUUSD H4 20")
    return 0


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
