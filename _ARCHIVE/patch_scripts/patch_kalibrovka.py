# -*- coding: utf-8 -*-
"""
PATCH: КАЛИБРОВКА — единый механизм настройки единиц на такт.
Маркер: KALIBROVKA_V1

Метафора Шефа: перед входом в рабочий такт единица протирает призму
(Характер + Заряд), чтобы смотреть на факты без искажений вчерашнего дня.

Кладёт три вещи (только создаёт/дополняет, живого не ломает):

  1. kalibrovka_core.py  (КОРЕНЬ репо)
       compute_mode(passport) → GENIUS/NORMAL/SAFE/RECOVERY.
       Физика ЕДИНИЦЫ — одна на весь город (Закон Фрактала: житель
       есть житель, режим считается одинаково у трейдера и мастера).
       Здания зовут ядро, не копируют. Читает РЕАЛЬНЫЕ поля нового
       города (_charge + 6 канонных ручек), не породу -2.

  2. Биржа/kalibrovka.py  (РУКА здания Биржа)
       граница = торговая сессия (реальный UTC), источник = журнал цеха.
       Зовёт ядро для режима, строит план на сессию. ШОВ под LLM.
       Когда родится Студия — у неё своя рука, зовущая то же ядро.

  3. манифест торгового_хаоса — блок "калибровка"
       {граница: "сессия", источник_памяти: "журналы/pnl.jsonl"}
       Параметры при цехе, не в коде — другой цех калибруется той же
       рукой без единой правки.

Идемпотентен: существующий файл не трогает; в манифест блок добавляет
только если его там нет.

Запуск из корня репо:  python patch_kalibrovka.py
"""
import sys
import json
import ast
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
MARKER = "KALIBROVKA_V1"
HERE = Path(__file__).resolve().parent  # где лежат исходники core/рука рядом с патчем


def _load_source(name: str) -> str:
    """Исходник модуля лежит рядом с патчем (в поставке)."""
    p = HERE / name
    return p.read_text(encoding="utf-8")


def install():
    print(f"═══ PATCH {MARKER} — Калибровка ═══")
    print(f"репо: {REPO}")
    sdelano, propushcheno = [], []

    # 0. состояние жителя в корень (единая дверь к месту)
    sost_dst = REPO / "sostoyanie.py"
    if sost_dst.exists():
        propushcheno.append(sost_dst.name)
        print(f"  ○ уже стоит: {sost_dst.name}")
    else:
        sost_dst.write_text(_load_source("sostoyanie.py"), encoding="utf-8")
        sdelano.append(sost_dst.name)
        print(f"  ✔ создан: {sost_dst.name}")

    # 1. ядро в корень
    core_dst = REPO / "kalibrovka_core.py"
    if core_dst.exists():
        propushcheno.append(core_dst.name)
        print(f"  ○ уже стоит: {core_dst.name}")
    else:
        core_dst.write_text(_load_source("kalibrovka_core.py"), encoding="utf-8")
        sdelano.append(core_dst.name)
        print(f"  ✔ создан: {core_dst.name}")

    # 2. рука в Биржу
    birzha_dir = REPO / "Биржа"
    if not birzha_dir.exists():
        print(f"  ✖ нет папки Биржа/ — сначала накати patch_birzha_baza.py")
        return False
    ruka_dst = birzha_dir / "kalibrovka.py"
    _ruka_ustarela = (ruka_dst.exists()
                      and "postavit_mesto" not in ruka_dst.read_text(encoding="utf-8"))
    if ruka_dst.exists() and not _ruka_ustarela:
        propushcheno.append("Биржа/kalibrovka.py")
        print(f"  ○ уже стоит (новая, со связкой места): Биржа/kalibrovka.py")
    else:
        if _ruka_ustarela:
            print(f"  ⚠ старая рука без связки места (sostoyanie) — заменяю честно")
        ruka_dst.write_text(_load_source("kalibrovka_birzha.py"), encoding="utf-8")
        sdelano.append("Биржа/kalibrovka.py" + (" (обновлена)" if _ruka_ustarela else ""))
        print(f"  ✔ создан/обновлён: Биржа/kalibrovka.py")

    # 3. блок калибровки в манифест цеха
    mf_path = (REPO / "GRONDHEIM_CITY" / "Биржа" / "цеха"
               / "торговый_хаос" / "manifest.json")
    if not mf_path.exists():
        print(f"  ✖ нет манифеста торгового_хаоса — накати patch_birzha_baza.py")
        return False
    mf = json.loads(mf_path.read_text(encoding="utf-8"))
    mf_changed = False
    if "калибровка" in mf:
        propushcheno.append("манифест: блок калибровки")
        print(f"  ○ блок 'калибровка' уже в манифесте")
    else:
        mf["калибровка"] = {
            "_note": ("параметры Калибровки цеха. Граница такта = сессия "
                      "(рынок открывается по UTC). Источник следа — журнал "
                      "цеха. Рука Биржи читает это, не хардкод."),
            "граница": "сессия",
            "источник_памяти": "журналы/pnl.jsonl",
        }
        mf_changed = True
        sdelano.append("манифест: блок калибровки")
        print(f"  ✔ добавлен блок 'калибровка' в манифест")

    # поле "здание" — куда физически ходят на смену (для штампа места).
    # Житель сам держит место, но калибровке нужен адрес рабочего здания.
    if "здание" in mf:
        propushcheno.append("манифест: поле здание")
        print(f"  ○ поле 'здание' уже в манифесте")
    else:
        mf["здание"] = "0014_EXCHANGE"
        mf["_note_здание"] = ("локация-здание, куда единицы приходят на "
                              "смену. Калибровка штампует её жителю на "
                              "время сессии; карта читает и светит точку.")
        mf_changed = True
        sdelano.append("манифест: поле здание")
        print(f"  ✔ добавлено поле 'здание' (0014_EXCHANGE) в манифест")

    if mf_changed:
        mf_path.write_text(json.dumps(mf, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    # 4. синтаксис обоих модулей
    for path in (core_dst, ruka_dst):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            print(f"  ✖ СИНТАКСИС БИТЫЙ в {path.name}: {e}")
            return False
    print("  ✔ синтаксис ядра и руки — чистый")

    # 5. самопроверка вживую
    print("\n─── самопроверка ───")
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(birzha_dir))
    import importlib
    import kalibrovka_core as core
    importlib.reload(core)
    sys.modules.pop("kalibrovka", None)
    import kalibrovka as ruka
    importlib.reload(ruka)

    from datetime import datetime, timezone
    fake_europe = datetime.now(timezone.utc).replace(hour=10, minute=0)
    r = ruka.kalibrovat_ceh("торговый_хаос", now_utc=fake_europe, stamp=False)
    print(f"  сессия (UTC 10:00): {r.get('сессия')} · сухой прогон, "
          f"место жителей НЕ трогаю (это лишь проверка установки)")
    edinicy = r.get("единицы", [])
    if not edinicy:
        print("  ⚙ занятых слотов нет — калибровать некого (все вакансии).")
        print("    Найми Веру в A01 и прогони: python Биржа/kalibrovka.py")
    else:
        for e in edinicy:
            nam = e.get("намерения")
            nam_txt = " · ".join(nam) if nam else "(RECOVERY — пропускает сессию)"
            print(f"  {e['слот']} {e['кто']} → {e['режим']} (муть {e['муть']}) → {nam_txt}")

    print("\n═══ ИТОГ ═══")
    for f in sdelano:
        print(f"  ✔ создано: {f}")
    for f in propushcheno:
        print(f"  ○ пропущено (было): {f}")
    return True


if __name__ == "__main__":
    ok = install()
    sys.exit(0 if ok else 1)
