# -*- coding: utf-8 -*-
# POSTAVIT_CHTENIE_S_KLYUCHOM_V1
"""
ПАТЧ: житель читает карточку — и может к ней ВЕРНУТЬСЯ.

Запускать из КОРНЯ РЕПО (после postavit_sklad_v_zagruzchik.py):
    python postavit_chtenie_s_klyuchom.py

РАДИ ЧЕГО ВСЁ ЗАТЕВАЛОСЬ
    Раньше в память ученика ложился только его ПЕРЕСКАЗ: «по такому-то
    файлу я понял то-то». Вернуться к оригиналу он не мог ничем.
    Посмотрел раз, пересказал — и живёшь с пересказом.
    Теперь рядом с выводом лежит КЛЮЧ, и он достаёт оригинал своей
    рукой: и за партой, и потом на Бирже за столом. Склад один.

ЧТО МЕНЯЕТ (Академия/ui_akademia.py):

  1. ВЫВОД ЛОЖИТСЯ С КЛЮЧОМ. В памяти: «[Академия] «подпись»
     [ключ]: вывод». По ключу оригинал достижим.

  2. ЯРЛЫКИ ЕГО СЛОВАМИ. Прочитал — последней строкой называет
     материал сам, два-четыре слова. Ложатся в его личную половину
     ключа и весят в поиске как пять слов (закон меток 09.09).
     Общую подпись Шефа не трогают никогда.

  3. ДВЕ НОВЫЕ РУКИ:
       sklad_nayti  — поискать на складе своими словами
       sklad_dostat — достать карточку по ключу и ПОСМОТРЕТЬ
     Картинка приходит настоящей картинкой: метка [КАДР: …] уже
     умеет досылать изображение, эту машинку не переделываем.

  4. ЧТО Я УЖЕ РАЗБИРАЛ. В разговор ученику кладётся список его
     ключей с его ярлыками — не материал, только адреса. Материал
     он достанет рукой, и только тогда за него заплатим.

  5. «УЖЕ ЧИТАЛ» СЧИТАЕТСЯ ПО КЛЮЧУ, а не по имени файла. Старый
     реестр остаётся рабочим для того, что легло без ключа.

ПОРЯДОК
    Идемпотентен. Бэкап .bak_chtenie, ast.parse перед записью.
    Требует, чтобы уже стоял склад в загрузчике — иначе честно
    откажется и ничего не тронет.

`шесть·проверено·до·корня`
"""
import ast
import shutil
from pathlib import Path

_KOREN = Path(__file__).resolve().parent
MARKER = "# CHTENIE_S_KLYUCHOM_V1"
NUZHEN = "SKLAD_V_ZAGRUZCHIKE_V1"


def _nayti_kabinet():
    kandidaty = [p for p in _KOREN.rglob("ui_akademia.py")
                 if "_АРХИВ" not in str(p) and "_УБОРКА" not in str(p)]
    if not kandidaty:
        print("⚠ не нашёл ui_akademia.py. Запускай из корня репозитория.")
        return None
    if len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p.relative_to(_KOREN)}")
        try:
            return kandidaty[int(input("Который? номер: ").strip()) - 1]
        except Exception:
            print("Не понял — беру первый.")
    return kandidaty[0]


# ═══════════════════════════════════════════════════════════
# 1. руки склада + ярлыки из ответа
# ═══════════════════════════════════════════════════════════
STARO_1 = '''async def _zvat_llm_akademii(messages, model: str = "") -> str:'''

NOVO_1 = '''def _vynut_yarlyki(tekst: str):
    """(текст без строки ЯРЛЫКИ, [ярлыки]).

    CHTENIE_S_KLYUCHOM_V1. Ярлыки житель ставит САМ, своими словами —
    это его личная половина ключа. Не нашлось строки — пустой список,
    и это нормальный ответ: придумывать за него нельзя.
    """
    stroki, yarlyki = [], []
    for s in (tekst or "").splitlines():
        if s.strip().upper().startswith("ЯРЛЫКИ"):
            hvost = s.split(":", 1)[1] if ":" in s else ""
            for y in hvost.replace(";", ",").split(","):
                y = y.strip().strip(".").lower()
                if y and y not in yarlyki:
                    yarlyki.append(y)
            continue
        stroki.append(s)
    return "\\n".join(stroki).strip(), yarlyki[:4]


async def _zvat_llm_akademii(messages, model: str = "", dom=None) -> str:'''


STARO_2 = '''    ruki_shema, ruki = _ruki_uchenika()'''
NOVO_2 = '''    ruki_shema, ruki = _ruki_uchenika(dom)'''


STARO_3 = '''def _ruki_uchenika():'''
NOVO_3 = '''def _ruki_uchenika(dom=None):'''


STARO_4 = '''    return shema, {"uchebnik": _pokazat,
                   "chemu_uchili": lambda a: "=== ДИСЦИПЛИНЫ ===\\n"
                                             + _u.temy()}'''

NOVO_4 = '''    ruki = {"uchebnik": _pokazat,
            "chemu_uchili": lambda a: "=== ДИСЦИПЛИНЫ ===\\n" + _u.temy()}

    # CHTENIE_S_KLYUCHOM_V1: руки склада. Вот ради чего всё —
    # житель возвращается к материалу САМ, когда ему понадобилось,
    # а не когда Шеф решит показать.
    if _sklad is not None:
        shema.append({"type": "function", "function": {
            "name": "sklad_nayti",
            "description": (
                "ПОИСК по складу Академии своими словами. Ищет и по "
                "подписям, и по ТВОИМ собственным ярлыкам — тем, что "
                "ты вешал(а), когда читал(а). Отдаёт ключи, сам "
                "материал не показывает."),
            "parameters": {"type": "object", "properties": {
                "о_чём": {"type": "string", "description": "словами"},
                "тема": {"type": "string",
                         "description": "необязательно: сузить"}},
                "required": ["о_чём"]}}})
        shema.append({"type": "function", "function": {
            "name": "sklad_dostat",
            "description": (
                "ПОСМОТРЕТЬ карточку по ключу. Картинку увидишь "
                "по-настоящему, текст прочитаешь. Зови, когда хочешь "
                "свериться с оригиналом, а не вспоминать."),
            "parameters": {"type": "object", "properties": {
                "ключ": {"type": "string"}},
                "required": ["ключ"]}}})

        def _sk_nayti(args):
            o = str(args.get("о_чём", "")).strip()
            t = str(args.get("тема", "")).strip()
            try:
                naydeno = _sklad.nayti(o, tema=t, dom=dom, skolko_nado=6)
            except Exception as e:
                return f"склад не открылся: {e}"
            if not naydeno:
                return (f"по «{o}» ничего не нашлось.\\n"
                        + _sklad.chto_est())
            stroki = []
            for kl, k, _o in naydeno:
                moyo = _sklad.moy_klyuch(dom, kl) if dom else {}
                hvost = ""
                if moyo.get("ярлыки"):
                    hvost = " · мои ярлыки: " + ", ".join(moyo["ярлыки"])
                stroki.append(f"  [{kl}] "
                              f"{k.get('подпись') or k.get('откуда') or '—'}"
                              f"{hvost}")
            return ("=== НАШЛОСЬ (достань нужное рукой sklad_dostat) ===\\n"
                    + "\\n".join(stroki))

        def _sk_dostat(args):
            kl = str(args.get("ключ", "")).strip()
            try:
                k, put, tekst = _sklad.dostat(kl)
            except Exception as e:
                return f"склад не открылся: {e}"
            if not k:
                return (f"ключа «{kl}» на складе нет. "
                        f"Поищи рукой sklad_nayti.")
            podp = k.get("подпись") or ""
            otk = k.get("откуда") or ""
            shapka = f"{podp}" + (f" · {otk}" if otk else "")
            moyo = _sklad.moy_klyuch(dom, kl) if dom else {}
            hvost = ""
            if moyo.get("поправки"):
                hvost = "\\nчто мне про это говорил учитель:\\n" + "\\n".join(
                    f"  — {p.get('текст','')}"
                    for p in moyo["поправки"][-3:])
            # метка [КАДР: …] — та же машинка, что у учебника:
            # картинка досылается настоящей картинкой, не путём
            if put is not None and put.suffix.lower() in KARTINKA_EXT:
                return f"[КАДР: {put}] {shapka}{hvost}"
            if tekst:
                return f"=== {kl} · {shapka} ===\\n{tekst[:6000]}{hvost}"
            return f"{kl} · {shapka} — материала нет, только подпись.{hvost}"

        ruki["sklad_nayti"] = _sk_nayti
        ruki["sklad_dostat"] = _sk_dostat

    return shema, ruki'''


# ═══════════════════════════════════════════════════════════
# 2. чтение: ключ в память, ярлыки от жителя
# ═══════════════════════════════════════════════════════════
STARO_5 = '''            fp = Path(_p)
            if fp.is_file():
                fajly.append((fp, _r.get("вид") or "текст"))'''

NOVO_5 = '''            fp = Path(_p)
            if fp.is_file():
                # CHTENIE_S_KLYUCHOM_V1: ключ едет вместе с файлом —
                # без него вывод опять лёг бы «в никуда».
                fajly.append((fp, _r.get("вид") or "текст",
                              _r.get("ключ") or ""))'''


STARO_6 = '''        uzhe = set(_kto_chto_prochital().get(imya, []))
        novye = [(fp, vid) for fp, vid in fajly if fp.name not in uzhe]'''

NOVO_6 = '''        # CHTENIE_S_KLYUCHOM_V1: «уже читал» считается по КЛЮЧУ.
        # Старый реестр по именам остаётся рабочим для того, что легло
        # без ключа — не ломаем то, что работает.
        uzhe = set(_kto_chto_prochital().get(imya, []))
        uzhe_klyuchi = set()
        if _sklad is not None:
            try:
                uzhe_klyuchi = set(_sklad.prochitannoe(dom))
            except Exception:
                uzhe_klyuchi = set()
        novye = [(fp, vid, kl) for fp, vid, kl in fajly
                 if ((kl not in uzhe_klyuchi) if kl
                     else (fp.name not in uzhe))]'''


STARO_7 = '''        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\nНа столе лежит материал "
               "для изучения — тот же, что видят другие студенты. Читай своей "
               "натурой, не чужой.\\n")'''

NOVO_7 = '''        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\nНа столе лежит материал "
               "для изучения — тот же, что видят другие студенты. Читай своей "
               "натурой, не чужой.\\n")
        # CHTENIE_S_KLYUCHOM_V1: ярлыки ставит САМ житель, своими
        # словами. Это его личная половина ключа: по ней он потом сам
        # себя и найдёт. Придумывать за него нельзя.
        rol += ("\\nСАМОЙ ПОСЛЕДНЕЙ строкой напиши:\\n"
                "ЯРЛЫКИ: два-четыре слова своими словами — как ты сам(а) "
                "назовёшь этот материал, чтобы потом его найти. Не "
                "пересказ, а метки для себя.\\n")'''


STARO_8 = '''        for fp, vid in novye:'''
NOVO_8 = '''        for fp, vid, _klyuch in novye:'''


STARO_9 = '''            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"))
            # CHTENIE_KNIGI_V1: остальные части — по очереди, с памятью'''

NOVO_9 = '''            vyzhimka = await _zvat_llm_akademii(messages, state.get("model"),
                                                dom=dom)
            # CHTENIE_KNIGI_V1: остальные части — по очереди, с памятью'''


STARO_10 = '''            try:
                vdoh_res = dv.vdoh(kontekst="учёба", sila=0.8, svezhest=1.0, tonus="плюс")
                dv.vydoh_stol(fakt=f"[Академия] «{fp.name}»: {vyzhimka.strip()}", vdoh_result=vdoh_res)
                dv.sохранить()
            except Exception:
                pass
            _otmetit_prochitannym(imya, fp.name)'''

NOVO_10 = '''            # CHTENIE_S_KLYUCHOM_V1: ярлыки жителя отделяем от вывода —
            # они уходят в его личную половину ключа, а не в текст.
            vyzhimka, _yarlyki = _vynut_yarlyki(vyzhimka)
            _kart = (_sklad.kartochka(_klyuch)
                     if (_sklad is not None and _klyuch) else {})
            _zaglavie = (_kart.get("подпись") or _kart.get("откуда")
                         or fp.name)
            # ВОТ РАДИ ЧЕГО ВСЁ: рядом с выводом лежит КЛЮЧ. Житель
            # достанет оригинал сам, рукой, когда понадобится — а не
            # будет жить со своим пересказом месячной давности.
            _hvost_kl = f" [{_klyuch}]" if _klyuch else ""
            try:
                vdoh_res = dv.vdoh(kontekst="учёба", sila=0.8, svezhest=1.0, tonus="плюс")
                dv.vydoh_stol(
                    fakt=f"[Академия] «{_zaglavie}»{_hvost_kl}: "
                         f"{vyzhimka.strip()}",
                    vdoh_result=vdoh_res)
                dv.sохранить()
            except Exception:
                pass
            if _sklad is not None and _klyuch:
                try:
                    _sklad.otmetit_prochitannym(dom, _klyuch)
                    if _yarlyki:
                        _sklad.pomenit(dom, _klyuch, _yarlyki)
                except Exception as _e_sk3:
                    print(f"[СКЛАД] личная половина не легла: {_e_sk3}")
            _otmetit_prochitannym(imya, fp.name)'''


STARO_11 = '''            state["чат"].append({"role": "assistant", "кто": imya,
                                 "content": f"📖 «{fp.name}» — {vyzhimka.strip()}"})
            ui.notify(f"✦ {imya} прочитал(а): {fp.name}", type="positive")'''

NOVO_11 = '''            _pokaz_yar = (" · 🏷 " + ", ".join(_yarlyki)) if _yarlyki else ""
            state["чат"].append({"role": "assistant", "кто": imya,
                                 "content": f"📖 «{_zaglavie}»{_hvost_kl} — "
                                            f"{vyzhimka.strip()}{_pokaz_yar}"})
            ui.notify(f"✦ {imya} прочитал(а): {_zaglavie}", type="positive")'''


# ═══════════════════════════════════════════════════════════
# 3. разговор: ученик знает свои ключи
# ═══════════════════════════════════════════════════════════
STARO_12 = '''        promt = dusha + rol'''

NOVO_12 = '''        # CHTENIE_S_KLYUCHOM_V1: кладём СПИСОК КЛЮЧЕЙ, не материал.
        # Ключи и ярлыки весят копейки, материал достаётся рукой — и
        # только тогда за него платим.
        if _sklad is not None:
            try:
                _kusok_sk = _sklad.dlya_promta(dom)
                if _kusok_sk:
                    rol += _kusok_sk
                    rol += ("Достать любое можно рукой sklad_dostat по "
                            "ключу, поискать — рукой sklad_nayti.\\n")
            except Exception:
                pass

        promt = dusha + rol'''


ZAMENY = [
    ("ярлыки из ответа + dom в вызове", STARO_1, NOVO_1),
    ("руки получают дом", STARO_2, NOVO_2),
    ("руки: подпись функции", STARO_3, NOVO_3),
    ("руки склада", STARO_4, NOVO_4),
    ("ключ едет со стола", STARO_5, NOVO_5),
    ("«уже читал» по ключу", STARO_6, NOVO_6),
    ("просьба про ярлыки", STARO_7, NOVO_7),
    ("цикл чтения", STARO_8, NOVO_8),
    ("дом в вызов модели", STARO_9, NOVO_9),
    ("ключ в память", STARO_10, NOVO_10),
    ("показ в чате", STARO_11, NOVO_11),
    ("ключи в разговор", STARO_12, NOVO_12),
]


def main():
    print("=" * 58)
    print("ЧТЕНИЕ С КЛЮЧОМ")
    print("=" * 58)

    fajl = _nayti_kabinet()
    if fajl is None:
        return
    print(f"\nфайл: {fajl.relative_to(_KOREN)}")

    tekst = fajl.read_text(encoding="utf-8")

    if MARKER in tekst:
        print("\n✓ патч уже стоит — ничего не делаю.")
        return
    if NUZHEN not in tekst:
        print("\n⚠ сперва нужен postavit_sklad_v_zagruzchik.py —")
        print("  без склада в загрузчике ключей ещё нет. Ничего не тронул.")
        return

    print("\n--- ЗАМЕНЫ ---")
    ne_nashlos = []
    for imya, staro, _novo in ZAMENY:
        n = tekst.count(staro)
        znak = "✓" if n == 1 else ("⚠ НЕ НАЙДЕНО" if n == 0 else f"⚠ {n} совп.")
        print(f"  {znak}  {imya}")
        if n != 1:
            ne_nashlos.append(imya)

    if ne_nashlos:
        print(f"\n⚠ не сошлось: {', '.join(ne_nashlos)}")
        print("  Ничего не тронул — покажи мне файл, пересоберу.")
        return

    novyy = tekst
    for _imya, staro, novo in ZAMENY:
        novyy = novyy.replace(staro, novo, 1)
    novyy = novyy.rstrip() + f"\n\n{MARKER} - marker\n"

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"\n⚠ после правок файл не разбирается: "
              f"строка {e.lineno}: {e.msg}")
        print("  На диск НЕ писал. Ничего не сломано.")
        return
    print("\n  ast.parse — чисто")

    bak = fajl.with_suffix(fajl.suffix + ".bak_chtenie")
    shutil.copy2(fajl, bak)
    fajl.write_text(novyy, encoding="utf-8")
    print(f"  бэкап:  {bak.name}")
    print(f"  записан: {fajl.name}")

    print("\n✓ готово. Что смотреть глазами:")
    print("  1. Положи картинку с источником и подписью.")
    print("  2. Жми «📖 Прочитать» — в конце ответа должны появиться")
    print("     🏷 ярлыки ЕГО словами и [ключ] рядом с подписью.")
    print("  3. Спроси его в чате: «достань, что ты читал про …»")
    print("     В консоли должно мелькнуть [УЧЕНИК] 🖐 sklad_nayti,")
    print("     потом sklad_dostat — и он увидит картинку заново.")
    print("  4. Если позвал руку и честно сказал «не разглядел» —")
    print("     это тоже успех: значит смотрит, а не сочиняет.")
    print("=" * 58)


if __name__ == "__main__":
    main()
    try:
        input("\nEnter — закрыть: ")
    except Exception:
        pass

# POSTAVIT_CHTENIE_S_KLYUCHOM_V1 - marker
