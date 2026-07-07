# -*- coding: utf-8 -*-
"""
PATCH: ЖИТЕЛЬ · ПРАВАЯ ПАНЕЛЬ — живое место, показатели, аватарка локации.
Маркер: ZHITEL_PANEL_ZHIVAYA_V1

ТРИ ПРАВКИ (по слову Шефа, сверено со старым кабинетом -2):

  1. ЗАГОЛОВОК "ковчег · прибытие" — был ЗАХАРДКОЖЕН (прибитый текст,
     не смотрел на место). Отсюда "Ковчег" даже когда Вера прописана.
     СТАЛО: заголовок = где житель СЕЙЧАС (sostoyanie.gde_ya) —
     "ДОМА · Торговый Квартал" / "НА СМЕНЕ · Биржа" / "В КОВЧЕГЕ".

  2. ПОКАЗАТЕЛИ под аватаром (как в -2: под точкой агента — его
     жизненные показатели). Живое состояние из паспорта:
       ЗАРЯД   — _charge (dvizhok), −1..+1, с полосой и знаком
       ОПТИКА  — муть = |заряд| словом (чисто/мутит/залито) —
                 та же шкала, что калибровка (kalibrovka_core)
       НАТУРА  — 6 DNA-ручек компактно
     Не выдумка: ровно те поля, что реально есть у жителя.

  3. АВАТАРКА ЛОКАЦИИ под аватаром жителя — маленький образ места,
     где он сейчас (image.* той же локации, что даёт фон). Фон
     оставляем как есть (patch_zhitel_tekushaya_lokacia уже сделал
     его живым) — здесь только миниатюра-плашка.

ЧЕСТНОСТЬ: sostoyanie нет → заголовок падает на прописку (как было).
image локации нет → плашка не рисуется (не пустой квадрат).

Идемпотентен: маркер ZHITEL_PANEL_ZHIVAYA в файле → не трогаем.
Требует: patch_zhitel_tekushaya_lokacia.py (для tekushaya_lokacia).

Запуск из корня репо:  python patch_zhitel_panel.py
"""
import sys
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
TARGET = REPO / "жители" / "ui_zhitel.py"

# ── Якорь: весь старый блок правой панели (аватар + захардкоженная плашка)
ANCHOR = '''        # RIGHT — аватар + приборы
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                with ui.element("div").classes("zavatar"):
                    av = _avatar_url(dom, p)
                    if av:
                        ui.html(f'<img src="{av}" onerror="this.style.display=\\'none\\'">')
                    else:
                        ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.5);">⬡</div>')
                    ui.html(f'<div class="zavatar-cap"><div class="nm">{name}</div>'
                            f'<div class="role">{rank}</div></div>')
                with ui.element("div").classes("glass runs-panel"):
                    ui.html('<div class="panel-title">ковчег · прибытие</div>')
                    if core_phrase:
                        ui.html(f'<div class="zcore">«{core_phrase}»</div>')
                    _propiska = p.get("прописка")
                    if not _propiska:
                        ui.html('<div class="zcore" style="opacity:0.7;">⬡ в ковчеге — '
                                'приземлилась, ждёт прописки. Город ещё не принял.</div>')
                    else:
                        ui.html(f'<div class="zcore" style="opacity:0.7;">⬡ прописана: {_propiska}</div>')'''

INSERT = '''        # RIGHT — аватар + ЖИВЫЕ показатели (ZHITEL_PANEL_ZHIVAYA_V1)
        with ui.element("div").classes("area-right"):
            with ui.element("div").classes("right-col"):
                with ui.element("div").classes("zavatar"):
                    av = _avatar_url(dom, p)
                    if av:
                        ui.html(f'<img src="{av}" onerror="this.style.display=\\'none\\'">')
                    else:
                        ui.html('<div style="font-size:3rem; color:rgba(201,168,76,0.5);">⬡</div>')
                    ui.html(f'<div class="zavatar-cap"><div class="nm">{name}</div>'
                            f'<div class="role">{rank}</div></div>')

                # аватарка ЛОКАЦИИ где житель сейчас (под аватаром жителя)
                _loc_thumb = _lokacia_thumb(tekushaya_lokacia)
                _mesto_zag, _mesto_pod = _mesto_podpis(dom, tekushaya_lokacia, p)
                if _loc_thumb:
                    ui.html(
                        f'<div class="zloc-strip">'
                        f'<div class="zloc-thumb" style="background-image:url(\\'{_loc_thumb}\\');"></div>'
                        f'<div class="zloc-meta"><div class="zloc-zag">{_mesto_zag}</div>'
                        f'<div class="zloc-pod">{_mesto_pod}</div></div></div>'
                    )

                # ЖИВЫЕ ПОКАЗАТЕЛИ агента (как в старом кабинете — под точкой)
                with ui.element("div").classes("glass runs-panel"):
                    ui.html(f'<div class="panel-title">{_mesto_zag}</div>')
                    ui.html(_pokazateli_html(p))
                    if core_phrase:
                        ui.html(f'<div class="zcore">«{core_phrase}»</div>')'''

# ── CSS + функции показателей вставляем перед page_zhitel
ANCHOR_CSS = '.nicegui-content{ overflow:hidden !important; height:100% !important; }\n"""'
INSERT_CSS = '''.nicegui-content{ overflow:hidden !important; height:100% !important; }

/* ZHITEL_PANEL_ZHIVAYA_V1 — плашка локации + показатели */
.zloc-strip{ flex-shrink:0; display:flex; gap:10px; align-items:center;
  padding:8px; border-radius:14px; border:1px solid rgba(255,255,255,0.08);
  background:rgba(255,255,255,0.03); }
.zloc-thumb{ width:52px; height:52px; border-radius:10px; flex-shrink:0;
  background-size:cover; background-position:center;
  border:1px solid rgba(201,168,76,0.3); }
.zloc-meta{ min-width:0; }
.zloc-zag{ font-size:0.72rem; font-weight:800; color:#c9a84c;
  text-transform:uppercase; letter-spacing:0.06em; }
.zloc-pod{ font-size:0.56rem; color:rgba(255,255,255,0.5);
  letter-spacing:0.04em; margin-top:2px; }
.zpok{ padding:10px 16px; display:flex; flex-direction:column; gap:9px; }
.zpok-row{ display:flex; flex-direction:column; gap:3px; }
.zpok-lab{ display:flex; justify-content:space-between; font-size:0.56rem;
  text-transform:uppercase; letter-spacing:0.08em; color:rgba(255,255,255,0.5); }
.zpok-lab b{ color:rgba(255,255,255,0.85); font-weight:700; }
.zpok-bar{ height:6px; border-radius:4px; background:rgba(255,255,255,0.08);
  overflow:hidden; }
.zpok-fill{ height:100%; border-radius:4px; }
.zpok-dna{ font-size:0.55rem; color:rgba(255,255,255,0.45);
  font-family:'JetBrains Mono',monospace; line-height:1.6;
  padding-top:4px; border-top:1px solid rgba(255,255,255,0.06); }
"""'''

# ── Функции: вставляем перед "def page_zhitel"
ANCHOR_FUNC = 'def page_zhitel(zid: str = ""):'
INSERT_FUNC = '''def _lokacia_thumb(loc_id: str) -> str:
    """Мини-образ локации где житель сейчас. image.* той же локации,
    что даёт фон. Нет — пусто (плашка не рисуется, не пустой квадрат)."""
    if not loc_id:
        return ""
    loc_dir = LOKACII_DIR / loc_id
    if not loc_dir.exists():
        return ""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (loc_dir / ("image" + ext)).exists():
            return f"/lokacia-static/{loc_id}/image{ext}"
    return ""


def _lokacia_name(loc_id: str) -> str:
    """Имя локации из её паспорта (для подписи). Нет — сам id."""
    if not loc_id:
        return ""
    import json as _j
    pp = LOKACII_DIR / loc_id / "passport.json"
    if pp.exists():
        try:
            return _j.loads(pp.read_text(encoding="utf-8")).get("Official_Name", loc_id)
        except Exception:
            pass
    return loc_id


def _mesto_podpis(dom, loc_id: str, p: dict):
    """Живой заголовок места: ГДЕ житель сейчас (sostoyanie.gde_ya).
    Возвращает (заголовок, подпись). Не хардкод 'ковчег'."""
    imya_loc = _lokacia_name(loc_id) if loc_id else ""
    doma = True
    try:
        _repo = Path(__file__).resolve().parent.parent
        if str(_repo) not in sys.path:
            sys.path.insert(0, str(_repo))
        import sostoyanie as _sost
        r = _sost.gde_ya(dom)
        doma = r.get("дома", True)
    except Exception:
        pass
    if not loc_id:
        return ("В КОВЧЕГЕ", "приземлилась, ждёт прописки")
    if doma:
        return (f"ДОМА · {imya_loc}", "по месту прописки")
    return (f"НА МЕСТЕ · {imya_loc}", "сейчас здесь")


def _pokazateli_html(p: dict) -> str:
    """Живые показатели жителя из паспорта: заряд, оптика, натура.
    Как в старом кабинете — под аватаром жизненные показатели."""
    try:
        charge = float(p.get("_charge", 0.0) or 0.0)
    except (TypeError, ValueError):
        charge = 0.0
    mut = abs(charge)
    # оптика словом (та же шкала, что kalibrovka_core)
    if mut < 0.25:
        optika, ocolor = "чисто", "rgba(80,250,123,0.9)"
    elif mut < 0.55:
        optika, ocolor = "ровно", "rgba(201,168,76,0.9)"
    elif mut < 0.8:
        optika, ocolor = "мутит", "rgba(255,160,60,0.9)"
    else:
        optika, ocolor = "залито", "rgba(255,80,80,0.9)"
    # полоса заряда: от центра, знак цветом
    znak = "+" if charge >= 0 else "−"
    zcolor = "rgba(80,250,123,0.9)" if charge >= 0 else "rgba(255,120,120,0.9)"
    zwidth = int(mut * 100)

    dna = p.get("DNA_Static", {}) or {}
    dna_str = " · ".join(f"{k.split('_')[0]} {v}" for k, v in dna.items())

    return (
        '<div class="zpok">'
        f'<div class="zpok-row"><div class="zpok-lab">заряд<b>{znak}{mut:.2f}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" '
        f'style="width:{zwidth}%; background:{zcolor};"></div></div></div>'
        f'<div class="zpok-row"><div class="zpok-lab">оптика<b style="color:{ocolor};">{optika}</b></div>'
        f'<div class="zpok-bar"><div class="zpok-fill" '
        f'style="width:{int((1-mut)*100)}%; background:{ocolor};"></div></div></div>'
        + (f'<div class="zpok-dna">{dna_str}</div>' if dna_str else '')
        + '</div>'
    )


def page_zhitel(zid: str = ""):'''


def install():
    print("═══ PATCH ZHITEL_PANEL_ZHIVAYA_V1 — живая правая панель ═══")
    print(f"репо: {REPO}")

    if not TARGET.exists():
        print(f"  ✖ не найден: {TARGET.relative_to(REPO)}")
        return False

    src = TARGET.read_text(encoding="utf-8")

    if "ZHITEL_PANEL_ZHIVAYA" in src:
        print("  ○ уже накатано — не трогаю")
        return True

    if "tekushaya_lokacia" not in src:
        print("  ✖ patch_zhitel_tekushaya_lokacia.py ещё не накатан — сначала он")
        return False

    for name, a in (("панель", ANCHOR), ("CSS", ANCHOR_CSS), ("func", ANCHOR_FUNC)):
        if a not in src:
            print(f"  ✖ якорь «{name}» не найден — файл менялся, останавливаюсь. "
                  f"Покажи текущий ui_zhitel.py.")
            return False

    src = src.replace(ANCHOR_FUNC, INSERT_FUNC, 1)  # только первое (определение)
    src = src.replace(ANCHOR_CSS, INSERT_CSS)
    src = src.replace(ANCHOR, INSERT)

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    TARGET.write_text(src, encoding="utf-8")
    print("  ✔ заголовок места — живой (gde_ya), не 'ковчег' хардкодом")
    print("  ✔ показатели агента под аватаром (заряд/оптика/натура)")
    print("  ✔ аватарка локации где житель сейчас")
    print("  ✔ синтаксис чист")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
