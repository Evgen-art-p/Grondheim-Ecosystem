# patch_fon_po_propiske.py
"""
Камень третий: фон кабинета жителя по прописке.

_bg_for_mask() до патча вообще не знал о прописке — искал только маску,
свой bg.* в корне дома жителя, и КОВЧЕГ. Даже прописанный житель видел
в чате фон ковчега.

После патча: маска → свой bg.* → ПРОПИСКА (образ локации) → КОВЧЕГ →
дефолт. Никакого отдельного bg.* заводить не нужно — берём тот же
image.*, что локация уже показывает на своей странице (/lokacia/{id}),
по указанию Шефа: "фон можно брать рисунок самой локации, в репе в
папке в локации есть".

Что делает патч в жители/ui_zhitel.py:
  1. LOKACII_DIR — тот же путь, что в ui_lokacia.py (локально, без
     кросс-импорта — иначе цикл: ui_lokacia уже импортирует ui_zhitel).
  2. _bg_for_mask() принимает propiska, добавляет шаг между "свой bg"
     и "КОВЧЕГ".
  3. page_zhitel() — монтирует статику /lokacia-static/{propiska} сама,
     не полагаясь на то, что Шеф уже заходил на страницу этой локации
     в этой сессии сервера (иначе картинка была бы 404 при первом заходе
     в чат жителя раньше, чем на страницу его локации).

Запуск из КОРНЯ репо:
    python patch_fon_po_propiske.py

Идемпотентен — если маркер PATCH_FON_PO_PROPISKE уже стоит в файле,
скрипт не тронет его повторно.

Бэкап: жители/ui_zhitel.py.bak_fon_po_propiske
`шесть·проверено·до·корня`
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
TARGET = _ROOT / "жители" / "ui_zhitel.py"
MARKER = "PATCH_FON_PO_PROPISKE"


def main():
    if not TARGET.exists():
        print(f"✗ не найден: {TARGET}")
        print("  запускай из корня репо (там же, где main.py)")
        return

    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print(f"— уже применён ({MARKER} найден в {TARGET.name}) — пропускаю")
        return

    # ── 1. LOKACII_DIR + новая _bg_for_mask() целиком ──
    anchor_bg = (
        'KOVCHEG_DIR = _ROOT / "GRONDHEIM_CITY" / "ковчег"\n'
        '\n'
        '\n'
        'def _bg_for_mask(dom: Path, mask: str = None) -> str:\n'
        '    """Путь фона кабинета. Порядок: активная маска → жильё жителя → КОВЧЕГ → дефолт.\n'
        '    ШОВ: маски/{mask}/bg.* оживёт, когда появятся маски с фонами."""\n'
        '    # 1. фон активной маски (будущее: маски/работа/bg.*, маски/дом/bg.* ...)\n'
        '    if dom is not None and mask:\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = dom / "маски" / mask / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return f"/zhitel-static/{dom.name}/маски/{mask}/bg{ext}"\n'
        '    # 2. фон в корне дома жителя (если положен)\n'
        '    if dom is not None:\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = dom / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return f"/zhitel-static/{dom.name}/bg{ext}"\n'
        '    # 3. КОВЧЕГ — общий фон прибытия (нет маски, нет своего жилья)\n'
        '    if KOVCHEG_DIR.exists():\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = KOVCHEG_DIR / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return "/kovcheg-static/bg" + ext\n'
        '    return ""   # дефолт — тёмный градиент с золотом (CSS). Здесь будет ковчег.\n'
    )
    if anchor_bg not in src:
        print("✗ не нашёл _bg_for_mask() целиком — файл изменился, откатываю")
        return

    new_bg = (
        'KOVCHEG_DIR = _ROOT / "GRONDHEIM_CITY" / "ковчег"\n'
        '\n'
        f'# {MARKER}: тот же путь, что LOKACII_DIR в ui_lokacia.py — не\n'
        '# импортируем оттуда (ui_lokacia сам импортирует нас, цикл).\n'
        'LOKACII_DIR = _ROOT / "GRONDHEIM_CITY" / "локации"\n'
        '\n'
        '\n'
        'def _bg_for_mask(dom: Path, mask: str = None, propiska: str = None) -> str:\n'
        '    """Путь фона кабинета. Порядок: активная маска → жильё жителя →\n'
        '    прописка (образ локации) → КОВЧЕГ → дефолт.\n'
        '    ШОВ: маски/{mask}/bg.* оживёт, когда появятся маски с фонами."""\n'
        '    # 1. фон активной маски (будущее: маски/работа/bg.*, маски/дом/bg.* ...)\n'
        '    if dom is not None and mask:\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = dom / "маски" / mask / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return f"/zhitel-static/{dom.name}/маски/{mask}/bg{ext}"\n'
        '    # 2. фон в корне дома жителя (если положен)\n'
        '    if dom is not None:\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = dom / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return f"/zhitel-static/{dom.name}/bg{ext}"\n'
        f'    # {MARKER}: 3. прописка — берём тот же image.*, что локация\n'
        '    # показывает на своей странице (/lokacia/{id}). Отдельный bg.*\n'
        '    # заводить не нужно — образ места один на всех, кто там бывает.\n'
        '    if propiska:\n'
        '        loc_dir = LOKACII_DIR / propiska\n'
        '        if loc_dir.exists():\n'
        '            for ext in (".png", ".jpg", ".jpeg", ".webp"):\n'
        '                cand = loc_dir / ("image" + ext)\n'
        '                if cand.exists():\n'
        '                    return f"/lokacia-static/{propiska}/image{ext}"\n'
        '    # 4. КОВЧЕГ — общий фон прибытия (нет маски, нет своего жилья, нет прописки)\n'
        '    if KOVCHEG_DIR.exists():\n'
        '        for ext in (".jpg", ".png", ".jpeg", ".webp"):\n'
        '            cand = KOVCHEG_DIR / ("bg" + ext)\n'
        '            if cand.exists():\n'
        '                return "/kovcheg-static/bg" + ext\n'
        '    return ""   # дефолт — тёмный градиент с золотом (CSS).\n'
    )
    src = src.replace(anchor_bg, new_bg, 1)

    # ── 2. page_zhitel(): своя статика для локации прописки + передача propiska ──
    anchor_page = (
        'def page_zhitel(zid: str = ""):\n'
        '    p, dom = find_dom(zid) if zid else (None, None)\n'
        '\n'
        '    # статика дома жителя + ковчега (общий фон прибытия)\n'
        '    try:\n'
        '        from nicegui import app\n'
        '        if dom is not None and dom.exists():\n'
        '            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))\n'
        '        if KOVCHEG_DIR.exists():\n'
        '            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))\n'
        '    except Exception:\n'
        '        pass\n'
        '\n'
        '    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")\n'
        '\n'
        '    # ФОН по маске (шов): пока активной маски нет → общий/дефолт\n'
        '    bg = _bg_for_mask(dom, mask=None)\n'
    )
    if anchor_page not in src:
        print("✗ не нашёл начало page_zhitel() — файл изменился, откатываю")
        return

    new_page = (
        'def page_zhitel(zid: str = ""):\n'
        '    p, dom = find_dom(zid) if zid else (None, None)\n'
        f'    propiska = p.get("прописка") if p else None  # {MARKER}\n'
        '\n'
        '    # статика дома жителя + ковчега (общий фон прибытия) + локации прописки\n'
        '    try:\n'
        '        from nicegui import app\n'
        '        if dom is not None and dom.exists():\n'
        '            app.add_static_files(f"/zhitel-static/{dom.name}", str(dom))\n'
        '        if KOVCHEG_DIR.exists():\n'
        '            app.add_static_files("/kovcheg-static", str(KOVCHEG_DIR))\n'
        f'        if propiska:  # {MARKER}: своя статика, не ждём захода на /lokacia/{{id}}\n'
        '            _loc_dir = LOKACII_DIR / propiska\n'
        '            if _loc_dir.exists():\n'
        '                app.add_static_files(f"/lokacia-static/{propiska}", str(_loc_dir))\n'
        '    except Exception:\n'
        '        pass\n'
        '\n'
        '    ui.add_head_html(f"<style>{ZHITEL_CSS}</style>")\n'
        '\n'
        '    # ФОН по маске → прописке → ковчегу\n'
        '    bg = _bg_for_mask(dom, mask=None, propiska=propiska)\n'
    )
    src = src.replace(anchor_page, new_page, 1)

    # ── бэкап + запись ──
    backup = TARGET.with_name(TARGET.name + ".bak_fon_po_propiske")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")

    print(f"✓ патч применён: {TARGET}")
    print(f"✓ бэкап:         {backup}")
    print("— фон кабинета жителя теперь смотрит на прописку → image.* локации.")
    print("— проверь: python main.py → /zhitel/001_GENESIS_LOKA (Лока, прописана в Высотку)")


if __name__ == "__main__":
    main()
