# -*- coding: utf-8 -*-
# POSTAVIT_KARTINKU_V_CHTENIE_V1
"""
ПАТЧ: при чтении картинка снова ДОХОДИТ до жителя.

Запускать из КОРНЯ РЕПО:
    python postavit_kartinku_v_chtenie.py

ЧТО СЛОМАЛ Я — и это целиком моя вина
    15.09 картинку клали прямо в историю чата, и чтение на это
    рассчитывало: «картинка уже лежит в истории, заново прикладывать её
    здесь не нужно». Я убрал укладку в историю (она вываливала на
    экран весь PNG буквами) — а эту строчку не тронул.
    Вышло, что картинка в коде чтения готовится... и никуда не идёт.
    Модель получает голый текст вопроса.

    Видели живьём: Паник «прочитал» скрин с диверами и сообщил, что на
    графике есть текст со словом «Дивергенция». Такого на картинке нет
    — это ИМЯ ФАЙЛА. Дальше общими словами: «оси X и Y», «линии,
    вероятно, ценовые». Так описывает тот, кто не смотрит, а угадывает.

ЧТО ДЕЛАЕТ
    Прикладывает картинку к самому вопросу чтения — и только к нему.
    В историю она не ложится: там остаётся лёгкая строка с ключом,
    и экран чистый.

    Вопрос при этом не трогаю ни на букву. «ЧТО ВИЖУ / ЧТО ЭТО ВО МНЕ»,
    разведённые по времени, и оговорка «её название ничего не значит»
    — всё выстрадано раньше и остаётся как есть.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_kartinka_chtenie, ast.parse перед записью.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# KARTINKA_V_CHTENIE_V1"


def _nayti():
    kand = [p for p in _KOREN.rglob("ui_akademia.py")
            if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)
            and ".bak" not in p.name]
    if not kand:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
        return None
    if len(kand) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kand, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kand[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kand[0]


STARO = '''                # AKADEMIA_KARTINKA_V_ISTORII_V1 (15.09): картинка уже
                # лежит в state["чат"] с момента, когда её положили на
                # стол — заново прикладывать её здесь не нужно, только
                # история впереди и сам вопрос.
                messages = [{"role": "system", "content": dusha + rol}]
                for _m in (state.get("чат") or [])[-20:]:
                    _r = ("user" if _m.get("role") == "user"
                          else "assistant")
                    messages.append({"role": _r,
                                     "content": _m.get("content", "")})
                messages.append({"role": "user", "content": vopros})'''

NOVO = '''                # KARTINKA_V_CHTENIE_V1: картинка едет ВМЕСТЕ С ЭТИМ
                # вопросом.
                # Здесь стояло: «картинка уже лежит в истории, заново
                # прикладывать не нужно». Так было 15.09, когда её
                # клали в историю. Укладку сняли — она вываливала на
                # экран весь PNG буквами, — а эту строчку забыли, и
                # картинка готовилась впустую. Житель описывал материал
                # по имени файла и выдумывал.
                # В историю не кладём: там остаётся строка с ключом,
                # экран чистый, и за одну картинку платим один раз.
                messages = [{"role": "system", "content": dusha + rol}]
                for _m in (state.get("чат") or [])[-20:]:
                    _r = ("user" if _m.get("role") == "user"
                          else "assistant")
                    messages.append({"role": _r,
                                     "content": _m.get("content", "")})
                messages.append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": url}},
                    {"type": "text", "text": vopros},
                ]})
                print(f"[ЧТЕНИЕ] 🖼 приложил картинку: {fp.name} "
                      f"({len(data) / 1024:.0f} КБ)")'''


def main():
    print("=" * 58)
    print("КАРТИНКА В ЧТЕНИЕ")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return

    n = tekst.count(STARO)
    print("\n--- ЗАМЕНА ---")
    print(f"  {'✓' if n == 1 else '⚠ ' + str(n)}  картинка к вопросу чтения")
    if n != 1:
        print("\n⚠ не сошлось — ничего не тронул. Покажи файл, пересоберу.")
        return

    novyy = tekst.replace(STARO, NOVO, 1).rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ не разбирается: строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_kartinka_chtenie")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Перезапусти город и проверь:")
    print("  1. Положи картинку, жми «📖 Прочитать».")
    print("  2. В консоли должно мелькнуть:")
    print("     [ЧТЕНИЕ] 🖼 приложил картинку: … (84 КБ)")
    print("  3. В ответе должно быть то, что НА НЕЙ. Если снова")
    print("     назовёт слова из имени файла — картинка не дошла,")
    print("     и виновата уже модель: не всякая умеет смотреть.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_KARTINKU_V_CHTENIE_V1 - marker
