# -*- coding: utf-8 -*-
"""
PATCH: КОНТОРА БИРЖИ — архивариус и исполнитель как штаб, не по цеху.
Маркер: KONTORA_BIRZHI_V1

ЗАМЫСЕЛ ШЕФА: Архивариус и Исполнитель привязаны к самой БИРЖЕ, не к
одному торговому цеху — ровно как Оле не привязана к одному кварталу
города, а хранит память всей Грондхейма. Родится второй торговый цех
(скальперы) — ему не нужен СВОЙ архивариус, он пользуется тем же.

ЧТО ДЕЛАЕТ:
  1. Убирает слоты A05 (память цеха) и A09 (казначей) из манифеста
     торгового_хаоса — они переезжают в штаб.
  2. Рождает GRONDHEIM_CITY/Биржа/цеха/контора/manifest.json —
     ДВА слота: архивариус, исполнитель. Тот же механизм сканера
     (Закон Пары не спрашивает природу цеха — только папку+слот).
  3. Кладёт в манифест торгового_хаоса поле "штаб": "контора" —
     метка для БУДУЩЕГО рабочего Совета (когда построим кабинет):
     "своего архивариуса у меня нет, спроси в конторе".

СВЯЗКА РЕЗИДЕНТА — та же кнопка «Роль», что уже работает для Веры:
  Workshop_ID: контора · Turbo_Role: архивариус (одному резиденту)
  Workshop_ID: контора · Turbo_Role: исполнитель (другому)
Новый код для самой связки НЕ нужен — resolve_para("контора", "архивариус")
уже умеет это, сканер видит контору как обычный цех.

Идемпотентен: если контора уже существует — не создаёт заново.
Если A05/A09 уже убраны из торгового_хаоса — не трогает повторно.

Запуск из корня репо:  python patch_kontora_birzhi.py
"""
import sys
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
MARKER = "KONTORA_BIRZHI_V1"

KONTORA_MANIFEST = {
    "_note": ("КОНТОРА БИРЖИ — штаб, общий на ВСЕ торговые цеха. Не цех "
              "в смысле торговли (нет своего рынка-судьи), а служба: "
              "память сделок биржи целиком + казначейство целиком. "
              "Ровно как Оле — не привязана к одному кварталу города."),
    "_маркер": MARKER,
    "версия": 1,
    "название": "Контора Биржи",
    "квартал": "0013_TRADING_QUARTER",
    "здание": "0014_EXCHANGE",
    "судья": "рынок",
    "client_facing": False,
    "слоты": [
        {
            "слот": "архивариус",
            "роль": "память биржи",
            "рекомендуемый_тип": "хранитель",
            "core_phrase": "",
            "промпт": "слоты/архивариус/промпт.md",
            "приборы": [
                {"поле": "память", "подпись": "ПАМЯТЬ БИРЖИ", "вид": "текст"},
            ],
        },
        {
            "слот": "исполнитель",
            "роль": "казначей биржи",
            "рекомендуемый_тип": "воркер",
            "core_phrase": "",
            "промпт": "слоты/исполнитель/промпт.md",
            "приборы": [
                {"поле": "ордера", "подпись": "ОРДЕРА (ВСЕ ЦЕХА)", "вид": "текст"},
                {"поле": "баланс", "подпись": "БАЛАНС БИРЖИ", "вид": "число"},
            ],
        },
    ],
    "журналы": {
        "_note": "общий журнал биржи — все цеха пишут сюда, не каждый свой.",
        "pnl": "журналы/pnl.jsonl",
        "ордера": "журналы/orders.jsonl",
    },
}


def install():
    print(f"═══ PATCH {MARKER} — Контора Биржи ═══")
    print(f"репо: {REPO}")

    # 1. Убрать A05/A09 из торгового_хаоса
    th_path = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха"
               / "торговый_хаос" / "manifest.json")
    if not th_path.exists():
        print(f"  ✖ нет манифеста торгового_хаоса — накати сначала "
              f"patch_birzha_baza.py")
        return False

    th = json.loads(th_path.read_text(encoding="utf-8"))
    old_slots = th.get("слоты", [])
    new_slots = [s for s in old_slots if s.get("слот") not in ("A05", "A09")]
    if len(new_slots) != len(old_slots):
        th["слоты"] = new_slots
        th["штаб"] = "контора"
        th_path.write_text(json.dumps(th, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        print(f"  ✔ убраны A05/A09 из торгового_хаоса "
              f"({len(old_slots)} → {len(new_slots)} слотов)")
        print(f"  ✔ добавлено поле 'штаб': 'контора'")
    else:
        if th.get("штаб") == "контора":
            print(f"  ○ торговый_хаос уже без A05/A09, штаб указан — пропускаю")
        else:
            th["штаб"] = "контора"
            th_path.write_text(json.dumps(th, ensure_ascii=False, indent=2),
                               encoding="utf-8")
            print(f"  ✔ A05/A09 уже отсутствовали, добавил поле 'штаб'")

    # 2. Родить контору
    kont_dir = REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "контора"
    kont_path = kont_dir / "manifest.json"
    if kont_path.exists():
        print(f"  ○ контора уже существует — пропускаю")
    else:
        kont_dir.mkdir(parents=True, exist_ok=True)
        kont_path.write_text(
            json.dumps(KONTORA_MANIFEST, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"  ✔ создана: GRONDHEIM_CITY/Биржа/цеха/контора/manifest.json")

    # 3. Самопроверка сканером — контора видна, слоты правильные
    print("\n─── самопроверка ───")
    sys.path.insert(0, str(REPO / "Биржа"))
    import importlib
    import cartridge_registry as cr
    importlib.reload(cr)

    ceha = cr.list_ceha("Биржа")
    print(f"  цеха на Бирже: {[c['id'] for c in ceha]}")
    kont = cr.get_ceh("контора")
    assert kont is not None, "контора не видна сканеру!"
    slots = [s["слот"] for s in kont.get("слоты", [])]
    print(f"  слоты конторы: {slots}")
    assert set(slots) == {"архивариус", "исполнитель"}

    th_check = cr.get_ceh("торговый_хаос")
    if th_check:
        th_slots = [s["слот"] for s in th_check.get("слоты", [])]
        print(f"  слоты торгового_хаоса теперь: {th_slots}")
        assert "A05" not in th_slots and "A09" not in th_slots
        print(f"  штаб торгового_хаоса: {th_check.get('штаб')}")
        assert th_check.get("штаб") == "контора"

    # доклад по слотам конторы — кто занят, а не требование пустоты
    # (после реального найма слоты и должны быть заняты — это не ошибка)
    for row in cr.list_nositeli("контора"):
        n = row["носитель"]
        who = f"{n['имя']} ({n['id']})" if n else "— вакансия —"
        print(f"  {row['слот']:<12} {who}")

    print("\n═══ ИТОГ ═══")
    print("  Дальше: роди двух резидентов Страницей Жизни, затем кнопкой")
    print("  «Роль» в кабинете Брата:")
    print("    Workshop_ID: контора · Turbo_Role: архивариус")
    print("    Workshop_ID: контора · Turbo_Role: исполнитель")
    print("  Новый код для связки не нужен — тот же механизм, что у Веры.")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
