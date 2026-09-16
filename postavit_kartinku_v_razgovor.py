# -*- coding: utf-8 -*-
# POSTAVIT_KARTINKU_V_RAZGOVOR_V1
"""
ПАТЧ: картинка со стола ДОХОДИТ до жителя в разговоре.

Запускать из КОРНЯ РЕПО:
    python postavit_kartinku_v_razgovor.py

ЧТО БЫЛО СЛОМАНО — и сломал это я
    Раньше картинка клалась прямо в историю чата. Она доходила, но
    рисовалка чата умеет показывать только строку и вываливала на
    экран весь PNG буквами. Я убрал причину и сказал: картинка теперь
    живёт на складе, достанется рукой по ключу.
    Руки склада я и правда добавил — но в дверь ЧТЕНИЯ. А разговор
    идёт другой дверью, и рук у неё нет вовсе: там прямой вызов без
    инструментов. Вышло, что картинку я забрал, а замену к разговору
    не подключил.
    Результат видели живьём: Илья описал на скрине USDCNH уровень
    1.26780, которого там нет. Не смотрел — сочинял.

ЧТО ДЕЛАЕТ
    Если на столе лежит картинка, она досылается К ВОПРОСУ — ровно
    так же, как в прогоне трейдеру досылается кадр. Житель видит её
    по-настоящему.

ПОЧЕМУ НЕ ВЕРНУЛ КАК БЫЛО
    Тогда картинка ложилась в историю НАВСЕГДА и ехала с каждым
    следующим вопросом: и простыня на экране, и деньги на ветер.
    Теперь она подмешивается только в текущий вопрос, а в истории
    остаётся строкой с ключом — читаемой и лёгкой.

    Берётся ПОСЛЕДНЯЯ картинка со стола: спрашивают обычно про то,
    что сейчас положили. Несколько разом не шлём — за каждую платим.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_kartinka_razgovor, ast.parse перед
    записью. Требует, чтобы уже стоял склад в загрузчике.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# KARTINKA_V_RAZGOVOR_V1"
NUZHEN = "SKLAD_V_ZAGRUZCHIKE_V1"


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


STARO = '''            messages.append({"role": r, "content": m.get("content", "")})
        messages.append({"role": "user", "content": vopros})'''

NOVO = '''            messages.append({"role": r, "content": m.get("content", "")})

        # KARTINKA_V_RAZGOVOR_V1: если на столе лежит картинка — она
        # едет ВМЕСТЕ С ЭТИМ вопросом, а не остаётся в истории навсегда.
        # Без этого житель не смотрит, а сочиняет: проверено живьём.
        _kart_stola = None
        try:
            for _r_st in reversed(state.get("руда") or []):
                if (_r_st.get("вид") or "") != "изображение":
                    continue
                _p_st = Path(_r_st.get("путь") or "")
                if _p_st.is_file():
                    _kart_stola = (_p_st, _r_st)
                    break
        except Exception as _e_ks:
            print(f"[СТОЛ] картинку со стола не взял: {_e_ks}")

        if _kart_stola is not None:
            _p_st, _r_st = _kart_stola
            try:
                _mime = _KARTINKA_MIME_STOL.get(_p_st.suffix.lower(),
                                                "image/png")
                _url = (f"data:{_mime};base64,"
                        f"{base64.b64encode(_p_st.read_bytes()).decode('ascii')}")
                # подпись Шефа и ключ едут рядом: житель должен знать,
                # ЧТО ему показали и как это потом достать самому
                _podp = (_r_st.get("подпись") or "").strip()
                _kl_st = (_r_st.get("ключ") or "").strip()
                _hvost = ""
                if _podp:
                    _hvost += f"\\n(положено на стол: {_podp})"
                if _kl_st:
                    _hvost += f"\\n(ключ карточки: {_kl_st})"
                messages.append({"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": _url}},
                    {"type": "text", "text": (vopros or "") + _hvost},
                ]})
                print(f"[СТОЛ] 🖼 дослал картинку: {_p_st.name}")
            except Exception as _e_dk:
                print(f"[СТОЛ] картинка не дослалась ({_e_dk}) — "
                      f"спрашиваю словами")
                messages.append({"role": "user", "content": vopros})
        else:
            messages.append({"role": "user", "content": vopros})'''


def main():
    print("=" * 58)
    print("КАРТИНКА В РАЗГОВОР")
    print("=" * 58)

    fajl = _nayti()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")
    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return
    if NUZHEN not in tekst:
        print("\n⚠ сперва нужен postavit_sklad_v_zagruzchik.py.")
        print("  Ничего не тронул.")
        return

    n = tekst.count(STARO)
    print(f"\n--- ЗАМЕНА ---")
    print(f"  {'✓' if n == 1 else '⚠ ' + str(n)}  досылка картинки к вопросу")
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

    bak = fajl.with_suffix(fajl.suffix + ".bak_kartinka_razgovor")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Что смотреть глазами:")
    print("  1. Положи картинку в загрузчик Академии с подписью.")
    print("  2. Спроси ученика: «что на картинке?»")
    print("  3. В консоли должно мелькнуть: [СТОЛ] 🖼 дослал картинку")
    print("  4. В ответе должно быть то, ЧТО НА НЕЙ — а не выдуманные")
    print("     цифры. Если назовёт уровень, которого нет, — он опять")
    print("     сочиняет, и смотреть надо на заряд (кнопка ❄ Душ).")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_KARTINKU_V_RAZGOVOR_V1 - marker
