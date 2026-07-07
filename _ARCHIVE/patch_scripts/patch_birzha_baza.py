# -*- coding: utf-8 -*-
"""
PATCH: БАЗА БИРЖИ — первый кирпич картриджной архитектуры нового города.
Маркер: BIRZHA_BAZA_V1

Что делает (только СОЗДАЁТ новые файлы, ничего живого не трогает):

  1. Биржа/cartridge_registry.py
       — сканер цехов (Закон Картриджа: папка+манифест = цех, id = имя папки)
       — resolve_para(цех, слот) (Закон Пары: носитель ищется ТОЛЬКО по
         mask.json жителя — Workshop_ID + Turbo_Role, никогда по ID_Object)
       — без LLM, без UI, без списков. Один механизм, корень параметром
         (квартал="Биржа" | "Студия") — один движок, два крана.

  2. GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/manifest.json
       — первый цех: 9 слотов (роли, не носители), судья: рынок.
       — слот = ВАКАНСИЯ. Носители (Роды) рождаются Страницей Жизни и
         нанимаются кнопкой «Роль» в кабинете Брата.

Идемпотентен: файл уже существует → пропускает, не перезаписывает.
В конце — самопроверка: сканер находит цех, resolve сводит пару,
честный None на пустое.

Запуск из корня репо:  python patch_birzha_baza.py
"""
import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
MARKER = "BIRZHA_BAZA_V1"

# ═══════════════════════════════════════════════════════════════
# ФАЙЛ 1: Биржа/cartridge_registry.py
# ═══════════════════════════════════════════════════════════════

REGISTRY_CODE = '''# -*- coding: utf-8 -*-
# BIRZHA_BAZA_V1
"""
CARTRIDGE REGISTRY — сканер цехов нового города.

ЗАКОН КАРТРИДЖА (перенесён из -2 ПРИНЦИПОМ, не кодом):
  1. Цех объявляет себя сам: папка + manifest.json = цех,
     его id — ИМЯ ПАПКИ, не поле внутри манифеста.
  2. Никто не ведёт списков: этот модуль сканирует диск на лету.
     Удалил папку — цех исчез отовсюду.
  3. Город помнит снаружи: хроники/резонанс живут вне цеха.

ЗАКОН ПАРЫ (новый город, Чертёж §1.5.2б / §4.4а):
  Цех объявляет СЛОТЫ (роли-вакансии). Носителей у цеха НЕТ.
  Житель (Род) живёт в GRONDHEIM_CITY/жители/ и надевается на слот
  актом «Роль» (кабинет Брата) — кнопка пишет в его
  маски/работа/mask.json поля Workshop_ID + Turbo_Role.
  resolve_para() сводит пару НА ЛЕТУ по этим полям.
  ID_Object жителя в опознании роли НЕ УЧАСТВУЕТ НИКОГДА —
  это лекарство от болезни -2 («стресс 0.0»: суд по роли,
  id по реестру, письмо на несуществующий адрес).

ОДИН МЕХАНИЗМ, ДВА КРАНА:
  корень данных — параметр `kvartal`:
    "Биржа"  → GRONDHEIM_CITY/Биржа/цеха/
    "Студия" → GRONDHEIM_CITY/Студия/цеха/
  Механизм один — источники разные (Закон Фрактала).

Без LLM. Без UI. Без NiceGUI. Чистое чтение диска.
"""
import json
from pathlib import Path

# Корень города — от места этого файла (Биржа/ лежит рядом с GRONDHEIM_CITY/)
_REPO = Path(__file__).resolve().parent.parent
CITY = _REPO / "GRONDHEIM_CITY"


def _read_json(path: Path):
    """Честное чтение: битый файл → None, не падение."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ───────────────────────────────────────────────────────────────
# СТАТЬЯ 1-2: сканер цехов
# ───────────────────────────────────────────────────────────────

def list_ceha(kvartal: str = "Биржа") -> list:
    """Все цеха квартала. Папка с manifest.json = цех, id = имя папки.
    Битый манифест → цех виден, но с честной пометкой _битый."""
    root = CITY / kvartal / "цеха"
    out = []
    if not root.exists():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if not mf.exists():
            continue  # папка без манифеста — не цех (статья 1)
        m = _read_json(mf)
        if m is None:
            out.append({"id": d.name, "_битый": True, "_путь": str(d)})
            continue
        m["id"] = d.name          # id = имя папки, всегда (статья 1)
        m["_путь"] = str(d)
        out.append(m)
    return out


def get_ceh(ceh_id: str, kvartal: str = "Биржа"):
    """Один цех по id. Честный None, если нет."""
    for c in list_ceha(kvartal):
        if c["id"] == ceh_id:
            return c
    return None


# ───────────────────────────────────────────────────────────────
# ЗАКОН ПАРЫ: свод носителя и слота на лету
# ───────────────────────────────────────────────────────────────

def _scan_zhiteli_maski():
    """Все жители с активной маской «работа».
    Скан: GRONDHEIM_CITY/жители/{профиль}/{Имя}/маски/работа/mask.json
    Это граница жителя (паспорт+маска), не его кухня — слои не трогаем."""
    root = CITY / "жители"
    out = []
    if not root.exists():
        return out
    for passport_path in sorted(root.glob("*/*/passport.json")):
        dom = passport_path.parent
        mask_path = dom / "маски" / "работа" / "mask.json"
        if not mask_path.exists():
            continue
        mask = _read_json(mask_path)
        if not mask or not mask.get("_активна"):
            continue
        p = _read_json(passport_path) or {}
        out.append({
            "имя": p.get("Official_Name", dom.name),
            "id": p.get("ID_Object", ""),
            "тип": p.get("тип", ""),
            "папка": str(dom),
            "цех": (mask.get("Workshop_ID") or "").strip(),
            "слот": (mask.get("Turbo_Role") or "").strip(),
            "core_phrase": mask.get("Core_Phrase", ""),
        })
    return out


def resolve_para(ceh_id: str, slot: str, kvartal: str = "Биржа"):
    """ЕДИНСТВЕННАЯ точка правды пары (цех, слот) → носитель.
    Ищет ТОЛЬКО по mask.json (Workshop_ID + Turbo_Role).
    Честный None: слот пуст / цеха нет / слота в манифесте нет."""
    ceh = get_ceh(ceh_id, kvartal)
    if ceh is None:
        return None
    slots = [s.get("слот") for s in ceh.get("слоты", [])]
    if slot not in slots:
        return None  # такой вакансии в цехе не объявлено
    for z in _scan_zhiteli_maski():
        if z["цех"] == ceh_id and z["слот"] == slot:
            return z
    return None  # вакансия есть, носителя нет — слот пуст, честно


def list_nositeli(ceh_id: str, kvartal: str = "Биржа") -> list:
    """Все носители цеха: по слоту — кто нанят (или None).
    Для UI приборной панели: рисовать универсально, без хардкода имён."""
    ceh = get_ceh(ceh_id, kvartal)
    if ceh is None:
        return []
    nanyatye = {(z["цех"], z["слот"]): z for z in _scan_zhiteli_maski()}
    out = []
    for s in ceh.get("слоты", []):
        slot = s.get("слот", "")
        out.append({
            "слот": slot,
            "роль": s.get("роль", ""),
            "носитель": nanyatye.get((ceh_id, slot)),  # None = вакансия
        })
    return out


# ───────────────────────────────────────────────────────────────
# Самопроверка (запуск напрямую): python Биржа/cartridge_registry.py
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys as _s
    try:
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("═══ CARTRIDGE REGISTRY — самопроверка ═══")
    ceha = list_ceha("Биржа")
    print(f"цехов на Бирже: {len(ceha)}")
    for c in ceha:
        if c.get("_битый"):
            print(f"  ⚠ {c['id']} — манифест битый")
            continue
        slots = c.get("слоты", [])
        print(f"  ⚙ {c['id']} — «{c.get('название','?')}» · "
              f"слотов: {len(slots)} · судья: {c.get('судья','?')}")
        for row in list_nositeli(c["id"]):
            n = row["носитель"]
            who = f"{n['имя']} ({n['id']})" if n else "— вакансия —"
            print(f"     {row['слот']:>4} {row['роль']:<22} {who}")
    print(f"несуществующий цех → {get_ceh('нет_такого')}")
    print(f"несуществующий слот → {resolve_para('торговый_хаос', 'A99')}")
    print("═══ конец самопроверки ═══")
'''

# ═══════════════════════════════════════════════════════════════
# ФАЙЛ 2: manifest.json Цеха Торгового Хаоса
# ═══════════════════════════════════════════════════════════════
# Слоты = РОЛИ (вакансии), не носители. Имена дадут Роды при найме.
# Роли и приборы — по канону Совета (Котин/Вильямс), носители новые.
# core_phrase слотов пустые — слово Шефа/Локи, не выдумка патча.

MANIFEST = {
    "_note": ("Цех Торгового Хаоса — первый картридж Биржи нового города. "
              "id цеха = имя папки (Закон Картриджа). Слоты — вакансии ролей; "
              "носители нанимаются кнопкой «Роль» в кабинете Брата "
              "(Workshop_ID=торговый_хаос, Turbo_Role=A0X)."),
    "_маркер": "BIRZHA_BAZA_V1",
    "версия": 1,
    "название": "Цех Торгового Хаоса",
    "квартал": "0013_TRADING_QUARTER",
    "судья": "рынок",
    "client_facing": False,
    "слоты": [
        {
            "слот": "A01",
            "роль": "компас",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A01/промпт.md",
            "приборы": [
                {"поле": "ao", "подпись": "AO", "вид": "число"},
                {"поле": "точка_ноль", "подпись": "ТОЧКА НОЛЬ", "вид": "статус"},
                {"поле": "дивергенция", "подпись": "ДИВЕРГЕНЦИЯ", "вид": "статус"},
                {"поле": "спуск", "подпись": "СПУСК ТФ", "вид": "текст"},
            ],
        },
        {
            "слот": "A02",
            "роль": "пасть и резинка",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A02/промпт.md",
            "приборы": [
                {"поле": "пасть", "подпись": "ПАСТЬ", "вид": "статус"},
                {"поле": "резинка", "подпись": "РЕЗИНКА", "вид": "статус"},
                {"поле": "натяжение", "подпись": "НАТЯЖЕНИЕ", "вид": "число"},
            ],
        },
        {
            "слот": "A03",
            "роль": "фаза толпы",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A03/промпт.md",
            "приборы": [
                {"поле": "фаза", "подпись": "ФАЗА", "вид": "текст"},
                {"поле": "mfi", "подпись": "MFI", "вид": "текст"},
            ],
        },
        {
            "слот": "A04",
            "роль": "фрактал",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A04/промпт.md",
            "приборы": [
                {"поле": "фрактал", "подпись": "ФРАКТАЛ", "вид": "статус"},
                {"поле": "цена_фрактала", "подпись": "ЦЕНА", "вид": "число"},
            ],
        },
        {
            "слот": "A05",
            "роль": "память цеха",
            "рекомендуемый_тип": "хранитель",
            "core_phrase": "",
            "промпт": "слоты/A05/промпт.md",
            "приборы": [
                {"поле": "память", "подпись": "ПАМЯТЬ", "вид": "текст"},
            ],
        },
        {
            "слот": "A06",
            "роль": "трейдер-пробой",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A06/промпт.md",
            "приборы": [
                {"поле": "вердикт", "подпись": "ВЕРДИКТ", "вид": "статус"},
                {"поле": "позиция", "подпись": "ПОЗИЦИЯ", "вид": "текст"},
                {"поле": "pnl_r", "подпись": "PnL (R)", "вид": "число"},
            ],
        },
        {
            "слот": "A07",
            "роль": "трейдер-ранний",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A07/промпт.md",
            "приборы": [
                {"поле": "вердикт", "подпись": "ВЕРДИКТ", "вид": "статус"},
                {"поле": "позиция", "подпись": "ПОЗИЦИЯ", "вид": "текст"},
                {"поле": "pnl_r", "подпись": "PnL (R)", "вид": "число"},
            ],
        },
        {
            "слот": "A08",
            "роль": "трейдер-откат",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A08/промпт.md",
            "приборы": [
                {"поле": "вердикт", "подпись": "ВЕРДИКТ", "вид": "статус"},
                {"поле": "позиция", "подпись": "ПОЗИЦИЯ", "вид": "текст"},
                {"поле": "pnl_r", "подпись": "PnL (R)", "вид": "число"},
            ],
        },
        {
            "слот": "A09",
            "роль": "казначей",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/A09/промпт.md",
            "приборы": [
                {"поле": "ордера", "подпись": "ОРДЕРА", "вид": "текст"},
                {"поле": "баланс", "подпись": "БАЛАНС", "вид": "число"},
            ],
        },
    ],
    "журналы": {
        "_note": ("ПАМЯТЬ живёт в РОЛИ (Чертёж §4.4а): журналы цеха — "
                  "объективная история, не форкается по носителю. "
                  "ОПЫТ (выводы) — у жителя, форкается по Роду. "
                  "Файлы появятся с первой сделкой — не создаём пустышки."),
        "pnl": "журналы/pnl.jsonl",
        "atlas": "журналы/atlas.jsonl",
    },
}


# ═══════════════════════════════════════════════════════════════
# УСТАНОВКА
# ═══════════════════════════════════════════════════════════════

def install():
    print(f"═══ PATCH {MARKER} — база Биржи ═══")
    print(f"репо: {REPO}")
    sdelano, propushcheno = [], []

    # 1. сканер
    reg_dir = REPO / "Биржа"
    reg_path = reg_dir / "cartridge_registry.py"
    if reg_path.exists():
        propushcheno.append(str(reg_path))
        print(f"  ○ уже стоит, пропускаю: {reg_path.relative_to(REPO)}")
    else:
        reg_dir.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(REGISTRY_CODE, encoding="utf-8")
        sdelano.append(str(reg_path))
        print(f"  ✔ создан: {reg_path.relative_to(REPO)}")

    # 2. манифест первого цеха
    ceh_dir = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
    mf_path = ceh_dir / "manifest.json"
    if mf_path.exists():
        propushcheno.append(str(mf_path))
        print(f"  ○ уже стоит, пропускаю: {mf_path.relative_to(REPO)}")
    else:
        ceh_dir.mkdir(parents=True, exist_ok=True)
        mf_path.write_text(
            json.dumps(MANIFEST, ensure_ascii=False, indent=2),
            encoding="utf-8")
        sdelano.append(str(mf_path))
        print(f"  ✔ создан: {mf_path.relative_to(REPO)}")

    # 3. проверка синтаксиса сканера
    import ast
    try:
        ast.parse(reg_path.read_text(encoding="utf-8"))
        print("  ✔ синтаксис cartridge_registry.py — чистый (ast.parse)")
    except SyntaxError as e:
        print(f"  ✖ СИНТАКСИС БИТЫЙ: {e}")
        return False

    # 4. самопроверка: сканер + пара
    print("\n─── самопроверка ───")
    sys.path.insert(0, str(reg_dir))
    import importlib
    import cartridge_registry as cr
    importlib.reload(cr)

    ceha = cr.list_ceha("Биржа")
    assert len(ceha) >= 1, "сканер не нашёл ни одного цеха"
    ceh = cr.get_ceh("торговый_хаос")
    assert ceh is not None, "get_ceh не нашёл торговый_хаос"
    assert len(ceh.get("слоты", [])) == 9, "слотов не 9"
    print(f"  ✔ сканер видит цех: «{ceh['название']}» · слотов: 9 · "
          f"судья: {ceh['судья']}")

    assert cr.get_ceh("нет_такого") is None, "нет честного None на цех"
    assert cr.resolve_para("торговый_хаос", "A99") is None, \
        "нет честного None на слот"
    print("  ✔ честный None: несуществующий цех / несуществующий слот")

    print("\n─── слоты и носители ───")
    est_nositel = False
    for row in cr.list_nositeli("торговый_хаос"):
        n = row["носитель"]
        who = f"{n['имя']} ({n['id']})" if n else "— вакансия —"
        if n:
            est_nositel = True
        print(f"  {row['слот']:>4} {row['роль']:<22} {who}")

    print("\n═══ ИТОГ ═══")
    for f in sdelano:
        print(f"  ✔ создано: {Path(f).relative_to(REPO)}")
    for f in propushcheno:
        print(f"  ○ пропущено (уже было): {Path(f).relative_to(REPO)}")
    if not est_nositel:
        print("\n  ⚙ Все слоты пусты — это честно, найма ещё не было.")
        print("    Нанять Веру: кабинет Брата → кнопка «Роль» →")
        print("    Вера → воркер → Цех: торговый_хаос · Слот: A01")
        print("    После найма прогони: python Биржа/cartridge_registry.py")
        print("    — resolve_para сведёт пару, увидишь её в слоте A01.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
