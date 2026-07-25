# -*- coding: utf-8 -*-
# PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1 — аватар + живой библиотекарь
"""
Делает три вещи:

  1. ЗАВОДИТ ПОСТ библиотекаря в реестре города:
       GRONDHEIM_CITY/посты/bibliotekar/пост.json
     Если Брат уже назначал библиотекаря раньше (в
     Академия/библиотека/хранитель.json) — переносит его на пост,
     чтобы старое назначение не потерялось.

  2. ЧИНИТ АВАТАР в Академия/ui_akademia.py.
     Было: подпись налеплена ПОВЕРХ фото (имя, место, курс —
     градиентом по лицу). Стало: аватар — чистое лицо, без единой
     буквы, ровно как в кабинете Брата; подпись и показатели уехали
     в панель ПОД ним.

  3. ОЖИВЛЯЕТ ЧАТ: сообщение в консоли Академии теперь идёт
     библиотекарю (Академия/bibliotekar.py) — он ищет книги и
     отвечает своим голосом. Поста нет — честно скажет, что
     библиотекаря в городе ещё не посадили.

Идемпотентно: маркер PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1 в файле —
второй прогон молчит. Бэкап перед правкой, ast.parse после.

ПЕРЕД ЗАПУСКОМ положи:
    ГОРОД/rezidenty.py
    Академия/bibliotekar.py

Запуск ИЗ КОРНЯ РЕПО:
    python patch_akademia_bibliotekar_ui_v1.py

`шесть·проверено·до·корня`
"""
import ast
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()
TARGET = ROOT / "Академия" / "ui_akademia.py"
POSTY = ROOT / "GRONDHEIM_CITY" / "посты"
STARY_HRANITEL = ROOT / "GRONDHEIM_CITY" / "Академия" / "библиотека" / "хранитель.json"

MARKER = "# PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1"


# ══════════════════════════════════════════════════════════
# ШАГ 1 — пост в реестре города
# ══════════════════════════════════════════════════════════

def shag_1_post():
    print("── ШАГ 1: пост библиотекаря ──")
    d = POSTY / "bibliotekar"
    mf = d / "пост.json"
    if mf.exists():
        print("  = пост уже заведён")
    else:
        d.mkdir(parents=True, exist_ok=True)
        mf.write_text(json.dumps({
            "id": "bibliotekar",
            "название": "Библиотекарь Академии",
            "где": "0008_OWL_CASTLE",
            "движок": "bibliotekar",
            "заведён": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("  ✓ пост заведён: GRONDHEIM_CITY/посты/bibliotekar/")

    # перенос старого назначения, чтобы не потерялось
    hr_new = d / "хранитель.json"
    if hr_new.exists():
        who = json.loads(hr_new.read_text(encoding="utf-8")).get("житель", "")
        print(f"  = на посту: {who or '(вакансия)'}")
    elif STARY_HRANITEL.exists():
        try:
            old = json.loads(STARY_HRANITEL.read_text(encoding="utf-8"))
            hr_new.write_text(json.dumps({
                "житель": old.get("житель", ""),
                "id": old.get("id", ""),
                "с": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✓ перенёс прежнее назначение: {old.get('житель','')}")
        except Exception as e:
            print(f"  ⚠ старое назначение не перенеслось: {e}")
    else:
        print("  = вакансия свободна (Брат ещё никого не сажал)")
    return True


# ══════════════════════════════════════════════════════════
# ШАГ 2 — правки ui_akademia.py
# ══════════════════════════════════════════════════════════

# 2а. Аватар: убрать подпись с лица, вынести под него ────────
ANCHOR_AVATAR = '''            av = _avatar_url(m["дом"]) if (m and m["занято"]) else ""
            img = (f'<img src="{av}" style="width:100%;height:100%;object-fit:cover;'
                   f'border-radius:12px;opacity:0.85;" onerror="this.style.display=\\'none\\'">'
                   if av else "")
            imya = m["имя"] if (m and m["занято"]) else "—"
            kurs = (m or {}).get("курс", "") or "курс не назначен"
            note = "" if (m and m["занято"]) else (
                '<div style="font-size:0.65rem;color:rgba(255,80,80,0.6);">'
                'место свободно</div>')
            ui.html(f\'\'\'
                <div style="position:relative; width:100%; height:100%; min-height:200px;">
                    {img}
                    <div style="position:absolute; bottom:0; left:0; right:0;
                                padding:15px; background:linear-gradient(transparent, rgba(0,0,0,0.8));
                                border-radius:0 0 12px 12px;">
                        <div style="font-size:0.65rem; color:rgba(255,255,255,0.5);
                                    letter-spacing:0.15em;">СТУДЕНТ · МЕСТО {m["место"] if m else "—"}</div>
                        <div style="font-size:1.3rem; font-weight:700; color:#00ff88;">{imya}</div>
                        <div style="font-size:0.8rem; color:rgba(255,255,255,0.8);">{kurs}</div>
                        {note}
                    </div>
                </div>
            \'\'\')'''

BLOCK_AVATAR = '''            # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: аватар — ЧИСТОЕ ЛИЦО.
            # Ни имени, ни места, ни курса поверх фото (так в кабинете
            # Брата: "аватар — чистое лицо, без подписи"). Всё словами
            # уехало в панель ПОД аватаром — update_vitals().
            av = _avatar_url(m["дом"]) if (m and m["занято"]) else ""
            if av:
                ui.html(f'<img src="{av}" style="width:100%;height:100%;'
                        f'object-fit:cover;border-radius:19px;opacity:0.9;" '
                        f'onerror="this.style.display=\\'none\\'">')
            else:
                ui.html('<div style="font-size:3rem; color:rgba(0,255,136,0.35);">⬡</div>')'''

# 2б. Показатели: подпись + заряд ПОД аватаром ────────────────
ANCHOR_VITALS = '''        with vitals_ref["element"]:
            if m and m["занято"]:
                p = _read_json(m["дом"] / "passport.json", {}) or {}
                ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))
            else:
                ui.html('<div style="color:rgba(255,255,255,0.3); font-size:10px; '
                        'padding:8px 16px;">— место свободно, показывать нечего —</div>')'''

BLOCK_VITALS = '''        with vitals_ref["element"]:
            # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: подпись студента живёт
            # ЗДЕСЬ, под аватаром — не поверх лица.
            if m and m["занято"]:
                p = _read_json(m["дом"] / "passport.json", {}) or {}
                kurs = (m.get("курс", "") or "курс не назначен")
                ui.html(
                    f'<div style="padding:12px 16px 4px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">'
                    f'студент · место {m["место"]}</div>'
                    f'<div style="font-size:1.15rem;font-weight:800;color:#00ff88;'
                    f'line-height:1.3;">{m["имя"]}</div>'
                    f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.6);">'
                    f'{kurs}</div></div>')
                ui.html(_bar_html(float(p.get("_charge", 0.0) or 0.0)))
            else:
                ui.html(
                    f'<div style="padding:12px 16px;">'
                    f'<div style="font-size:0.6rem;color:rgba(255,255,255,0.45);'
                    f'letter-spacing:0.14em;text-transform:uppercase;">'
                    f'место {m["место"] if m else "—"}</div>'
                    f'<div style="font-size:0.8rem;color:rgba(255,80,80,0.55);'
                    f'margin-top:2px;">свободно</div></div>')'''

# 2в. Чат: сообщение идёт живому библиотекарю ─────────────────
ANCHOR_SEND = '''        m = _mesto_row(mesta, state["активное_место"])
        if not (m and m["занято"]):
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": "Место свободно — отвечать некому. Запиши сюда студента."})
        else:
            state["чат"].append({
                "role": "assistant", "кто": m["имя"],
                "content": ("живой разговор с учеником — следующий слой. "
                            "Сейчас стоит только экран, и врать я не буду.")})
        update_chat()'''

BLOCK_SEND = '''        # PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: говорит БИБЛИОТЕКАРЬ.
        # Личность его — из паспорта того, кто на посту; роль — из
        # bibliotekar.py. Две разные вещи, склеенные в момент работы.
        try:
            import bibliotekar as _bib
        except Exception as _e:
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": f"движок библиотекаря не поднялся: {_e}"})
            update_chat()
            return

        _imya_bib = ""
        try:
            _promt, _imya_bib = _bib.sobrat_promt(msg, "Шеф")
        except Exception:
            _promt = ""

        if not _promt:
            state["чат"].append({
                "role": "assistant", "кто": "СИСТЕМА",
                "content": ("Библиотекаря в городе пока нет — пост свободен. "
                            "Посади кого-нибудь: Брат → Роль → библиотекарь.")})
            update_chat()
            return

        state["чат"].append({"role": "assistant", "кто": _imya_bib,
                             "content": "…ищу на полках"})
        update_chat()
        try:
            _otvet = await _bib.sprosit(msg, state["чат"][:-2], "Шеф")
        except Exception as _e:
            _otvet = f"⚠ библиотекарь не отозвался: {_e}"
        state["чат"].pop()          # снимаем «ищу»
        state["чат"].append({"role": "assistant", "кто": _imya_bib,
                             "content": _otvet})
        update_chat()'''

# 2г. sys.path: Академия должна видеть ГОРОД (там rezidenty.py) ──
ANCHOR_PATH = '''_HERE = Path(__file__).resolve().parent           # Академия/
_REPO = _HERE.parent                              # корень репо
for _p in (_REPO, _HERE):'''

BLOCK_PATH = '''_HERE = Path(__file__).resolve().parent           # Академия/
_REPO = _HERE.parent                              # корень репо
# PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1: ГОРОД в пути — там rezidenty.py
for _p in (_REPO, _REPO / "ГОРОД", _HERE):'''


def shag_2_ui():
    print("── ШАГ 2: правки кабинета Академии ──")
    if not TARGET.exists():
        print(f"  ✗ {TARGET} не найден.")
        return False

    src = TARGET.read_text(encoding="utf-8")
    if MARKER in src:
        print("  = патч уже накатан")
        return True

    novyy = src
    izmeneno = []

    for imya, ank, blok in (
        ("sys.path -> ГОРОД", ANCHOR_PATH, BLOCK_PATH),
        ("аватар — чистое лицо", ANCHOR_AVATAR, BLOCK_AVATAR),
        ("подпись под аватар", ANCHOR_VITALS, BLOCK_VITALS),
        ("чат -> библиотекарь", ANCHOR_SEND, BLOCK_SEND),
    ):
        if ank not in novyy:
            print(f"  ✗ якорь не найден: {imya}")
            print("    Файл ui_akademia.py менялся — правь вручную.")
            return False
        novyy = novyy.replace(ank, blok, 1)
        izmeneno.append(imya)

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"  ✗ после правки файл не парсится: {e}")
        print("  ФАЙЛ НЕ ЗАПИСАН — ничего не сломано.")
        return False

    bak = TARGET.with_suffix(".py.bak_bibliotekar_ui")
    shutil.copy2(TARGET, bak)
    TARGET.write_text(novyy, encoding="utf-8")
    print(f"  ✓ бэкап: {bak.name}")
    for i in izmeneno:
        print(f"  ✓ {i}")
    return True


def shag_3_proverka():
    print("── ШАГ 3: проверка ──")
    ok = True
    for f in (ROOT / "ГОРОД" / "rezidenty.py",
              ROOT / "Академия" / "bibliotekar.py",
              TARGET):
        if not f.exists():
            print(f"  ⚠ нет файла: {f}")
            ok = False
            continue
        try:
            ast.parse(f.read_text(encoding="utf-8"))
            print(f"  ✓ парсится: {f.name}")
        except SyntaxError as e:
            print(f"  ✗ не парсится {f.name}: {e}")
            ok = False
    return ok


if __name__ == "__main__":
    try:
        import sys as _s
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("═══ PATCH_AKADEMIA_BIBLIOTEKAR_UI_V1 ═══")
    print(f"корень: {ROOT}\n")
    ok = shag_1_post() and shag_2_ui() and shag_3_proverka()
    print()
    if ok:
        print("✅ ГОТОВО.")
        print("   Аватар чистый, подпись под ним.")
        print("   Чат Академии говорит с библиотекарём.")
        print("   Пост пуст? Брат → Роль → библиотекарь.")
    else:
        print("❌ Не докатилось — смотри выше. Ничего не сломано.")
    print("`шесть·проверено·до·корня`")
