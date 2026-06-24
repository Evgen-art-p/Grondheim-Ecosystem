# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ПАТЧ: ОБРУБИТЬ НИТОЧКУ studio/ из ui_registry.py            ║
║                                                              ║
║  Беда: ui_registry (копия из -2) зовёт                      ║
║    from studio.modules_registry import list_cartridges      ║
║  В новом городе папки studio/ НЕТ → ModuleNotFoundError.     ║
║                                                              ║
║  Чиним: оборачиваем все обращения к studio в try/except.    ║
║  Нет studio → отдаём fallback-списки (они уже есть в файле). ║
║  Страница открывается. Новый город · ни нитки из старого.   ║
║                                                              ║
║  Идемпотентно.                                               ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = Path("ui_registry.py")
MARK = "# PATCH_NO_STUDIO_APPLIED"


def fail(m):
    print(f"[ПАТЧ] ✗ {m}")
    sys.exit(1)


def _already_guarded(out_lines):
    """Грубо: предыдущая непустая строка — 'try:'? Значит уже обёрнуто."""
    for ln in reversed(out_lines):
        if ln.strip():
            return ln.strip() == "try:"
    return False


def main():
    if not TARGET.exists():
        fail("ui_registry.py не найден — запускай из корня Grondheim-Ecosystem")
    src = TARGET.read_text(encoding="utf-8")

    if MARK in src:
        print("[ПАТЧ] ⊙ ниточка studio уже обрублена — пропускаю")
        return

    changed = 0

    # ── 1. get_workshop_options: studio → fallback ──
    old1 = (
        'def get_workshop_options() -> list[str]:\n'
        '    """Цеха для селекта рождения: residents + все картриджи (живой скан)."""\n'
        '    from studio.modules_registry import list_cartridges\n'
        '    return ["", "residents"] + [c["id"] for c in list_cartridges()]\n'
    )
    new1 = (
        'def get_workshop_options() -> list[str]:\n'
        '    """Цеха для селекта рождения. Новый город: studio/ нет — fallback."""\n'
        '    try:\n'
        '        from studio.modules_registry import list_cartridges\n'
        '        return ["", "residents"] + [c["id"] for c in list_cartridges()]\n'
        '    except Exception:\n'
        '        # Новый город — старого studio/ нет. Отдаём встроенный список.\n'
        '        return WORKSHOP_OPTIONS\n'
    )
    if old1 in src:
        src = src.replace(old1, new1, 1)
        changed += 1
        print("[ПАТЧ] ✓ get_workshop_options обёрнут (fallback на WORKSHOP_OPTIONS)")
    else:
        print("[ПАТЧ] ⚠ get_workshop_options не совпал дословно — проверю по строке")

    # ── 2. get_role_options: studio → fallback ──
    old2 = (
        '    if workshop == "residents":\n'
        '        return RESIDENT_ROLE_OPTIONS\n'
        '    from studio.modules_registry import get_cartridge\n'
        '    cart = get_cartridge(workshop)\n'
        '    if cart and cart.get("roles"):\n'
        '        return [""] + list(cart["roles"])\n'
        '    return PIPELINE_ROLE_OPTIONS\n'
    )
    new2 = (
        '    if workshop == "residents":\n'
        '        return RESIDENT_ROLE_OPTIONS\n'
        '    try:\n'
        '        from studio.modules_registry import get_cartridge\n'
        '        cart = get_cartridge(workshop)\n'
        '        if cart and cart.get("roles"):\n'
        '            return [""] + list(cart["roles"])\n'
        '    except Exception:\n'
        '        pass\n'
        '    return ROLE_OPTIONS_MAP.get(workshop, PIPELINE_ROLE_OPTIONS)\n'
    )
    if old2 in src:
        src = src.replace(old2, new2, 1)
        changed += 1
        print("[ПАТЧ] ✓ get_role_options обёрнут (fallback на ROLE_OPTIONS_MAP)")
    else:
        print("[ПАТЧ] ⚠ get_role_options не совпал дословно")

    # ── 3. on_workshop_change: внутренний import get_cartridge ──
    old3 = (
        '                                    if agent_quarter_widget["w"] and ws:\n'
        '                                        from studio.modules_registry import get_cartridge\n'
        '                                        _cart = get_cartridge(ws)\n'
        '                                        auto_q = (_cart or {}).get("quarter") or _WORKSHOP_QUARTER.get(ws, "Квартал Мастеров")\n'
    )
    new3 = (
        '                                    if agent_quarter_widget["w"] and ws:\n'
        '                                        _cart = None\n'
        '                                        try:\n'
        '                                            from studio.modules_registry import get_cartridge\n'
        '                                            _cart = get_cartridge(ws)\n'
        '                                        except Exception:\n'
        '                                            _cart = None\n'
        '                                        auto_q = (_cart or {}).get("quarter") or _WORKSHOP_QUARTER.get(ws, "Квартал Мастеров")\n'
    )
    if old3 in src:
        src = src.replace(old3, new3, 1)
        changed += 1
        print("[ПАТЧ] ✓ on_workshop_change обёрнут (quarter fallback)")
    else:
        # Запасной способ: ищем любую оставшуюся строку 'from studio...get_cartridge'
        # с отступом и оборачиваем её в try/except по месту.
        wrapped = 0
        out = []
        for ln in src.splitlines(keepends=True):
            bare = ln.strip()
            if bare.startswith("from studio.modules_registry import get_cartridge") \
               and not _already_guarded(out):
                indent = ln[:len(ln) - len(ln.lstrip())]
                out.append(f"{indent}try:\n")
                out.append(f"{indent}    {bare}\n")
                out.append(f"{indent}except Exception:\n")
                out.append(f"{indent}    get_cartridge = lambda *a, **k: None\n")
                wrapped += 1
            else:
                out.append(ln)
        if wrapped:
            src = "".join(out)
            changed += wrapped
            print(f"[ПАТЧ] ✓ on_workshop_change обёрнут запасным способом ({wrapped})")
        else:
            print("[ПАТЧ] ⊙ on_workshop_change: голых import studio не осталось")

    # ── метка ──
    src = src.replace('import json\n', f'import json\n{MARK}\n', 1)
    if MARK not in src:
        src = MARK + "\n" + src

    if changed == 0:
        fail("ни одно место не совпало — покажи свежий ui_registry.py, поправлю якоря")

    TARGET.write_text(src, encoding="utf-8")
    print()
    print(f"[ПАТЧ] ✓ Готово. Обёрнуто мест: {changed} из 3.")
    print("       Ниточка studio/ обрублена — страница откроется без старого города.")
    print("       python main.py → /registry должна открыться.")


if __name__ == "__main__":
    main()
