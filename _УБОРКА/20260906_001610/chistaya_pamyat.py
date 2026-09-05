# -*- coding: utf-8 -*-
# MARKER: CHISTAYA_PAMYAT_PERED_PROGONOM_V1
"""
ЧИСТЫЙ ЛИСТ ПЕРЕД ПРОГОНОМ.

ЗАЧЕМ
    Сплошной прогон идёт по истории с прошлого года. Но в памяти
    города лежит ЖИВАЯ точка от сегодняшних запусков — и прогон
    начинает год, уже «зная» её. Первые события считаются поверх
    чужого хвоста, и сравнивать цифры становится не с чем.

    Прогон сам эту память не чистит — проверено по коду кабинета.

ЧТО ДЕЛАЕТ
    Убирает ТОЛЬКО точки (блок «точки» и старый общий «iskra»).
    Позиции, журнал, наблюдения, деньги, посты — НЕ ТРОГАЕТ.

    Перед правкой кладёт полную копию памяти рядом (.bak) — вернуть
    как было можно всегда.

    Показывает, что именно убирает, и спрашивает подтверждение.

ПОСЛЕ ЭТОГО
    Гони прогон: EURUSD H4, с 2025.08.14, как в прошлый раз.
    Смотреть на два числа — сколько раз структура прошла целиком
    (точка → вершина → откат) и сколько входов.

Запуск:  py chistaya_pamyat.py
"""
import json
import shutil
import sys
from pathlib import Path


def _nayti_koren() -> Path:
    def eto_koren(p: Path) -> bool:
        try:
            return (p / "Биржа" / "hooks.py").exists()
        except OSError:
            return False

    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd().resolve(), *zdes.parents):
        if eto_koren(kand):
            return kand
    nashli = []
    for baza in (zdes, zdes.parent, Path.cwd().resolve()):
        try:
            for d in baza.iterdir():
                if d.is_dir() and eto_koren(d) and d not in nashli:
                    nashli.append(d)
        except OSError:
            pass
    if len(nashli) == 1:
        return nashli[0]
    if len(nashli) > 1:
        print("Нашёл несколько городов:")
        for i, d in enumerate(nashli, 1):
            print(f"  {i}. {d}")
        return nashli[int((input("который? номер: ").strip() or "1")) - 1]
    print("Не нашёл корень города (папку с Биржа/hooks.py).")
    s = input("Перетащи сюда папку репозитория и нажми Enter:\n> ")
    p = Path(s.strip().strip('"').strip("'"))
    if eto_koren(p):
        return p
    raise SystemExit("Это не корень репо — там нет Биржа/hooks.py")


def main():
    koren = _nayti_koren()
    print(f"\nГород: {koren}\n")

    fayly = sorted(koren.rglob("trading_state.json"))
    if not fayly:
        print("Памяти на диске нет — чистить нечего, гони прогон.")
        return

    # ── что нашли ──────────────────────────────────────────────
    k_chistke = []
    for f in fayly:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  . {f.name}: не прочитан ({e}) — пропускаю")
            continue

        tochki = t.get("точки") or {}
        zhivye = [(p, b) for p, b in tochki.items()
                  if isinstance(b, dict) and b.get("alive")]
        stariy = bool((t.get("iskra") or {}).get("alive"))
        if not tochki and not stariy:
            continue

        k_chistke.append((f, t))
        print(f"  {f.parent.name}/{f.name}")
        for para, b in zhivye:
            kv = (b.get("konec_volny_1") or {})
            print(f"      живая точка {para}: "
                  f"{b.get('trend_direction')} @ {b.get('zero_point_price')}"
                  + (f", вершина {kv.get('цена')}" if kv else "")
                  + (", откат отмечен" if b.get("konec_volny_2") else ""))
        molchat = len(tochki) - len(zhivye)
        if molchat > 0:
            print(f"      и ещё {molchat} погасш(их) — тоже уберу")
        if stariy:
            print("      старый общий блок iskra — тоже уберу")
        pozic = len(t.get("positions") or [])
        if pozic:
            print(f"      позиций: {pozic} — НЕ ТРОГАЮ")

    if not k_chistke:
        print("Живых точек в памяти нет — можно гнать как есть.")
        return

    print("\nУберу только точки. Позиции, журнал, наблюдения, деньги "
          "останутся как есть.")
    print("Полная копия памяти ляжет рядом (.bak).")
    if input("Чистим? [Enter=да, любое другое — отмена] ").strip():
        print("Отменено, ничего не тронул.")
        return

    for f, t in k_chistke:
        shutil.copy2(f, f.with_suffix(".json.bak"))
        t["точки"] = {}
        isk = t.get("iskra")
        if isinstance(isk, dict):
            isk["alive"] = False
            isk["t1_status"] = "NOT_FOUND"
            isk["trend_direction"] = None
            isk["zero_point_price"] = None
            isk["rodilas_na_bare"] = None
            for k in ("konec_volny_1", "konec_volny_2", "kray_posle",
                      "barov_s_tochki", "нога", "попыток",
                      "reshali_na_bare", "otvet_bara", "struktura_pozadi"):
                isk.pop(k, None)
        f.write_text(json.dumps(t, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print(f"  + {f.parent.name}/{f.name}: точки убраны (.bak рядом)")

    print("\nЛист чистый. Теперь прогон: EURUSD H4, с 2025.08.14.")
    print("Смотреть на два числа: сколько раз структура прошла целиком")
    print("(точка → вершина → откат) и сколько входов.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e)
    except Exception:
        import traceback
        traceback.print_exc()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно ")
