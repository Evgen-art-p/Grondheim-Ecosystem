# -*- coding: utf-8 -*-
"""
proverka_mayaka.py — почему город не выходит наружу.

Ничего не чинит и не меняет. Смотрит и говорит, где обрыв:

    · какой .env читается (и читается ли вообще);
    · какие имена ключей в нём лежат — ЗНАЧЕНИЯ НЕ ПОКАЗЫВАЕТ,
      только длину и первые пару символов, чтобы ключ не утёк
      в переписку и в скриншот;
    · горит ли Маяк с точки зрения кода;
    · и, если горит, делает один живой запрос — отвечает ли Tavily.

Самая частая причина, когда «ключ есть, а не работает»: имя строки
в .env другое. На сайте Tavily ключ зовут TAVILY_API_KEY, а город
ищет TAVILY_KEY. Проверялка это увидит и скажет прямо.

Запуск из корня репо:  py proverka_mayaka.py
"""
import os
import sys
from pathlib import Path


def _eto_koren(p: Path) -> bool:
    return (p / "main.py").exists() and (p / "Маяк" / "mayak.py").exists()


def nayti_koren() -> Path:
    zdes = Path(__file__).resolve().parent
    for kand in (zdes, Path.cwd(), *zdes.parents):
        if _eto_koren(kand):
            return kand
    print("✗ Запусти из корня репо (там, где main.py)")
    sys.exit(1)


def pokazat(imya: str, znachenie: str) -> str:
    """Показать ключ, не выдавая его: длина и первые три символа."""
    z = (znachenie or "").strip()
    if not z:
        return "пусто"
    hvost = "…" if len(z) > 3 else ""
    return f"{z[:3]}{hvost} · длина {len(z)}"


def main():
    koren = nayti_koren()
    print(f"Город: {koren}\n")

    # ── 1. какие .env лежат рядом ──
    print("1. Файлы окружения в корне:")
    nashlos = False
    for imya in (".env", ".env.example", ".env.local"):
        f = koren / imya
        if f.exists():
            nashlos = True
            print(f"   {imya:16} есть · {f.stat().st_size} байт")
        else:
            print(f"   {imya:16} нет")
    if not nashlos:
        print("   ⚠ ни одного файла окружения — ключам взяться неоткуда")

    # ── 2. что внутри .env: ИМЕНА, не значения ──
    env = koren / ".env"
    stroki = {}
    if env.exists():
        print("\n2. Что в .env (значения скрыты):")
        try:
            for nomer, s in enumerate(
                    env.read_text(encoding="utf-8", errors="replace")
                    .splitlines(), 1):
                s = s.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                k = k.strip()
                v = v.strip()
                stroki[k] = v
                beda = ""
                if v.startswith(("'", '"')) or v.endswith(("'", '"')):
                    beda = "  ⚠ кавычки — их не надо, значение берётся как есть"
                elif v != v.strip():
                    beda = "  ⚠ лишние пробелы"
                print(f"   строка {nomer}: {k:22} = {pokazat(k, v)}{beda}")
        except Exception as e:
            print(f"   ✗ не читается: {e}")
    else:
        print("\n2. .env нет — а ключи город берёт только из него")

    # ── 3. то ли имя ──
    print("\n3. Имя ключа поиска:")
    if "TAVILY_KEY" in stroki and stroki["TAVILY_KEY"]:
        print("   ✓ TAVILY_KEY на месте — имя правильное")
    else:
        pohozhie = [k for k in stroki
                    if "TAVILY" in k.upper() and stroki[k]]
        if pohozhie:
            print(f"   ✗ ГОРОД ИЩЕТ строку TAVILY_KEY, а у тебя лежит: "
                  f"{', '.join(pohozhie)}")
            print("     Это и есть обрыв. Допиши в .env отдельной строкой:")
            print(f"       TAVILY_KEY={{сюда то же значение, что в "
                  f"{pohozhie[0]}}}")
        else:
            print("   ✗ строки с TAVILY в .env нет вовсе")

    # ── 4. что видит сам код ──
    print("\n4. Что видит код после загрузки .env:")
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env if env.exists() else None)
        print("   dotenv загружен")
    except Exception as e:
        print(f"   ✗ dotenv не сработал: {e}")
    kluch = os.getenv("TAVILY_KEY", "")
    print(f"   TAVILY_KEY в окружении: {pokazat('TAVILY_KEY', kluch)}")

    sys.path.insert(0, str(koren / "Маяк"))
    try:
        import mayak
        print(f"   Маяк горит: {'ДА' if mayak.gorit() else 'НЕТ'}")
    except Exception as e:
        print(f"   ✗ Маяк не импортируется: {e}")
        return 1

    if not mayak.gorit():
        print("\n✗ ИТОГ: маяк тёмный. Смотри пункт 3 — скорее всего дело")
        print("  в имени строки. Поправишь — перезапусти город, ключ")
        print("  читается один раз при старте.")
        return 1

    # ── 5. живая проверка ──
    print("\n5. Живой запрос наружу (одна проверка, копейки):")
    try:
        import asyncio
        rez = asyncio.run(mayak.poisk("что такое экосистема", skolko=2))
    except Exception as e:
        print(f"   ✗ запрос сорвался: {e}")
        return 1
    if rez.get("ok"):
        ist = rez.get("источники", [])
        print(f"   ✓ Tavily ответил · источников: {len(ist)}")
        for s in ist[:2]:
            print(f"     · {s.get('название','')[:60]} — {s.get('url','')[:60]}")
        print("\n✓ ИТОГ: выход наружу работает. Если Лока всё равно")
        print("  говорит про туман — перезапусти город: ключ читается")
        print("  при старте, на лету не подхватывается.")
        return 0
    print(f"   ✗ Tavily отказал: {rez.get('ошибка','')}")
    print("\n✗ ИТОГ: ключ город видит, но провайдер не пускает —")
    print("  проверь ключ на tavily.com (не истёк, не исчерпан лимит).")
    return 1


if __name__ == "__main__":
    kod = main()
    if sys.platform.startswith("win"):
        input("\nEnter — закрыть окно. ")
    sys.exit(kod)
