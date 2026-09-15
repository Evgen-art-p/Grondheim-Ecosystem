# -*- coding: utf-8 -*-
# PROVERKA_SKLADA_V1
"""
ПРОВЕРКА СКЛАДА АКАДЕМИИ — что на складе и дышит ли он.

Запускать из КОРНЯ РЕПО:
    python proverka_sklada.py

Имя файла ASCII нарочно: кириллицу терминал Шефа режет — первая
буква пути теряется. Модуль склада находим сами, руками пути не
вписываем.

Проверка показывает ФАКТ (ключи, числа, живые записи с диска), а не
галочку «готово». Пластик прячется в галочках.
"""
import sys
from pathlib import Path

_KOREN = Path(__file__).resolve().parent


def _nayti_sklad():
    """Найти Академию по приметам, не по прописанному пути."""
    kandidaty = []
    for p in sorted(_KOREN.iterdir()):
        if p.is_dir() and (p / "sklad.py").is_file():
            kandidaty.append(p)
    if not kandidaty:
        print("⚠ не нашёл sklad.py ни в одной папке рядом.")
        print("  Положи его в папку Академия/ и запусти снова.")
        return None
    if len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p.name}")
        try:
            n = int(input("Который? номер: ").strip())
            papka = kandidaty[n - 1]
        except Exception:
            print("Не понял — беру первый.")
            papka = kandidaty[0]
    else:
        papka = kandidaty[0]
    sys.path.insert(0, str(papka))
    import sklad
    return sklad


def main():
    print("=" * 58)
    print("СКЛАД АКАДЕМИИ · проверка")
    print("=" * 58)

    sklad = _nayti_sklad()
    if sklad is None:
        return

    print(f"\nмодуль: {sklad.__file__}")
    print(f"склад:  {sklad._SKLAD}")
    print(f"есть на диске: {'да' if sklad._SKLAD.exists() else 'нет (заведётся при первой укладке)'}")

    print("\n--- ЧТО ЛЕЖИТ ---")
    print(sklad.chto_est())

    vse = sklad.vse_kartochki()
    if vse:
        print("\n--- ПЕРВЫЕ ПЯТЬ КАРТОЧЕК ---")
        for kl in list(vse)[:5]:
            k = vse[kl]
            podp = k.get("подпись") or "— без подписи —"
            kto = k.get("подписал") or "?"
            print(f"  [{kl}]")
            print(f"     вид:     {k.get('вид','')}")
            print(f"     откуда:  {k.get('откуда','') or '—'}")
            print(f"     подпись: {podp}  (подписал: {kto})")

    # ── живая проба: положить, найти, достать, убрать ──
    print("\n--- ЖИВАЯ ПРОБА ---")
    proba = _KOREN / "_proba_sklada.txt"
    try:
        proba.write_text("Фрактал — бар, чей максимум выше двух "
                         "предшествующих и двух последующих.",
                         encoding="utf-8")
        klyuch = sklad.polozhit(
            put_faila=proba,
            otkuda="проба проверки, не материал",
            podpis="проба склада",
            tema="проба")
        print(f"  положил:  {klyuch}")

        naydeno = sklad.nayti("фрактал", tema="проба")
        print(f"  нашёл по слову «фрактал»: {len(naydeno)} шт.")

        k, put, tekst = sklad.dostat(klyuch)
        print(f"  достал:   материал на диске "
              f"{'есть' if put and put.exists() else 'НЕТ'}, "
              f"текста {len(tekst)} знаков")

        # личная половина — на временном доме
        dom_proba = _KOREN / "_proba_dom"
        dom_proba.mkdir(exist_ok=True)
        sklad.pomenit(dom_proba, klyuch, ["два и два", "определение"],
                      "высокая")
        sklad.otmetit_prochitannym(dom_proba, klyuch)
        sklad.popravka(dom_proba, klyuch,
                       "не «соседи», а ДВА предшествующих и ДВА последующих")
        moyo = sklad.moy_klyuch(dom_proba, klyuch)
        print(f"  ярлыки:   {moyo.get('ярлыки')}")
        print(f"  важность: {moyo.get('важность')}")
        print(f"  поправок: {len(moyo.get('поправки', []))}")

        s_yarlykom = sklad.nayti("определение", dom=dom_proba)
        vpered = (s_yarlykom and s_yarlykom[0][0] == klyuch)
        print(f"  ярлык поднял карточку в поиске: "
              f"{'да' if vpered else 'нет'}")

        print(f"\n  кусок в промпт:\n{sklad.dlya_promta(dom_proba)}")

        # убираем за собой — проба не должна остаться на складе
        vse2 = sklad.vse_kartochki()
        if klyuch in vse2:
            fajl = vse2[klyuch].get("файл")
            if fajl:
                try:
                    (sklad._MATERIALY / fajl).unlink()
                except Exception:
                    pass
            del vse2[klyuch]
            sklad._pisat_json(sklad._KARTOCHKI, {"карточки": vse2})
        for f in dom_proba.iterdir():
            f.unlink()
        dom_proba.rmdir()
        proba.unlink()
        print("  прибрал за собой: проба со склада снята")

        print("\n✓ склад дышит")
    except Exception as e:
        print(f"\n⚠ проба не прошла: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if proba.exists():
            try:
                proba.unlink()
            except Exception:
                pass

    print("=" * 58)


if __name__ == "__main__":
    main()
    # окно не должно захлопываться при запуске двойным кликом
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# PROVERKA_SKLADA_V1 - marker
