# -*- coding: utf-8 -*-
"""
yashchik_stola.py   ·   MARKER: YASHCHIK_STOLA_V1

ЧТО НАШЛОСЬ
-----------
Илья описал свой вход так: «пробой валидного фрактала за пастью
Аллигатора на импульсе, отложенная заявка на тик выше хая». Это не
одно из трёх мест канона. Это канон БРУТА — прежнего жителя места
A06, уволенного полтора месяца назад.

Пришло оно не из знаний и не из имени места, а из ящика стола. В
`данные/diary_brut.jsonl` лежат десятки записей: «по канону Брута
нужен пробой валидного фрактала за пастью на импульсе», «канон Брута:
пробой…», и так сорок раз подряд — золото, Искра, Морж, Паникёр,
сенсоры, которых давно нет. Пять последних записей подмешиваются в
рабочую стопку КАЖДЫЙ бар под заголовком «ТВОЙ ДНЕВНИК — твоя
память». Дневник лежит при МЕСТЕ, а не при человеке: Брута уволили,
тетрадь осталась на столе, и Илья читает её как свою.

Мы весь день снимали влияние места на выбор входа. Самое сильное
лежало в ящике.

СЛОВО ШЕФА
----------
«Дневник жителю не нужен, это лишний шум. События в память покрепче —
и жителю. А рутина — нежелательно. Как в студии делали клиентскую
память: на работе есть, дома частично, а документы в архив —
вернулся, достал. Слом, уход — та же рутина. А вход и результат —
это событие.»

ЧТО ДЕЛАЕМ
----------
  1. В голову жителю каждый бар идут ТОЛЬКО СОБЫТИЯ: вход и чем он
     кончился. Отказы, ожидания, сломы, уходы — рутина, в голову не
     лезет.
  2. Журнал места пишется как писался, ничего не теряется.
  3. Достать рутину можно рукой `moy_dnevnik` — она уже есть. И
     отдаёт теперь честно: с именем автора и пометкой, чьи это
     записи, если они не твои. Архив, из которого достают, а не
     память, которую носят.

ЧЕГО НЕ ДЕЛАЕМ
--------------
  · дневник не чистим и не переносим: это летопись места, Лока её
    заберёт в архив;
  · статистику не трогаем;
  · чужие записи не прячем — прячем только их выдачу за свои.

Идемпотентен, кладёт `.bak_yashchik_ГГГГММДД_ЧЧММСС`.

  py -3 yashchik_stola.py           — сделать
  py -3 yashchik_stola.py --suho    — только показать
"""

import ast
import sys
import time
from pathlib import Path

MARKER = "YASHCHIK_STOLA_V1"
SHTAMP = time.strftime("%Y%m%d_%H%M%S")
SUHO = "--suho" in sys.argv


# ───────────── 1. мозги: в голову только события ─────────────

M1_STAROE = '''    recent = _read_recent_diary(5, as_of_bar_time=md.get("bar_time"))'''

M1_NOVOE = '''    # YASHCHIK_STOLA_V1: в голову — только СОБЫТИЯ, не рутина.
    recent = _moi_sobytiya(5, as_of_bar_time=md.get("bar_time"))'''

M2_STAROE = '''        "=== ТВОЙ ДНЕВНИК (последние события — твоя память) ===\\n"'''

M2_NOVOE = '''        "=== ТВОИ СОБЫТИЯ (входы и чем кончились — что помнишь сам) ===\\n"'''

M3_STAROE = '''def _read_recent_diary(n: int = 5, as_of_bar_time=None) -> list:'''

M3_NOVOE = '''def _moi_sobytiya(n: int = 5, as_of_bar_time=None) -> list:
    """YASHCHIK_STOLA_V1: только СОБЫТИЯ, и только свои.

    Слово Шефа: «слом, уход — та же рутина, а вход и результат — это
    событие». Событие — то, что стоит помнить наизусть: ты вошёл, и
    чем это кончилось. Отказы и ожидания в голову не идут: их сотни,
    они одинаковые, и именно они выучиваются наизусть вместо канона.

    Почему это важно, а не косметика: в ящике стола A06 лежали сорок
    записей прежнего жителя, где сто раз повторено «канон Брута —
    пробой фрактала за пастью». Пять из них ехали в стопку каждый
    бар, и следующий человек честно выучил чужой канон, приняв его
    за свою память.

    Чужие записи сюда не попадают вовсе. Тетрадь лежит при МЕСТЕ и
    переживает жильцов — значит своим считаем только то, что подписано
    тобой. Подписи нет (старые записи, до имён) — тоже не берём:
    лучше пустая голова, чем чужая.
    """
    zhitel = ""
    try:
        zhitel = (_kto_ya() or "").strip()
    except Exception:
        pass
    svoi = []
    for e in _read_recent_diary(400, as_of_bar_time=as_of_bar_time):
        verdikt = str(e.get("verdict") or "").upper()
        vhod = verdikt in ("APPROVED", "ENTER", "OK") or e.get("entry")
        itog = e.get("result") not in (None, "")
        if not (vhod or itog):
            continue                      # рутина — в журнале, не в голове
        avtor = str(e.get("кто") or e.get("житель") or "").strip()
        if zhitel and avtor and avtor != zhitel:
            continue                      # чужое событие — не моя память
        if zhitel and not avtor:
            continue                      # без подписи — не присваиваем
        svoi.append(e)
    return svoi[-n:]


def _read_recent_diary(n: int = 5, as_of_bar_time=None) -> list:'''


# ───────────── 2. рука: журнал места, с именем автора ─────────────

R_STAROE = '''    def _dnevnik(args: dict) -> str:
        n = int(args.get("сколько") or 5)
        if dnevnik_fn is None:
            return "дневник недоступен"
        try:
            zapisi = dnevnik_fn(n) or []
            if not zapisi:
                return "записей пока нет"
            return ("=== ДНЕВНИК · последние " + str(len(zapisi)) + " ===\\n"
                    + json.dumps(zapisi, ensure_ascii=False, indent=1)[:3000])
        except Exception as e:
            return f"дневник не прочитался: {e}"'''

R_NOVOE = '''    def _dnevnik(args: dict) -> str:
        """YASHCHIK_STOLA_V1: журнал МЕСТА, а не твоя память.

        Тетрадь лежит при посте и переживает жильцов. Раньше она
        отдавалась молча, и чужие записи читались как свои — так
        новый человек на A06 выучил канон прежнего. Теперь у каждой
        записи видно автора, а сверху сказано прямо, чьё это.
        """
        n = int(args.get("сколько") or 5)
        if dnevnik_fn is None:
            return "дневник недоступен"
        try:
            zapisi = dnevnik_fn(n) or []
            if not zapisi:
                return "записей пока нет"
            _ya = (imya_zhitelya or "").strip()
            _avtory = sorted({str(z.get("кто") or z.get("житель") or "").strip()
                              for z in zapisi} - {""})
            _chuzhie = [a for a in _avtory if _ya and a != _ya]
            _shapka = (f"=== ЖУРНАЛ МЕСТА · последние {len(zapisi)} ===\\n"
                       "Это записи РАБОЧЕГО МЕСТА, а не твоя память. "
                       "Место старше тебя.\\n")
            if _chuzhie:
                _shapka += (f"Среди них есть чужие — писали: "
                            f"{', '.join(_chuzhie)}. Их канон это ИХ канон, "
                            f"не твой.\\n")
            elif not _avtory:
                _shapka += ("Записи без подписи — старые, автор "
                            "неизвестен. Своими их не считай.\\n")
            return (_shapka
                    + json.dumps(zapisi, ensure_ascii=False, indent=1)[:3000])
        except Exception as e:
            return f"журнал не прочитался: {e}"'''


# ───────────── 3. подписывать новые записи именем ─────────────

P_STAROE = '''def _append_diary(signal: dict, diary_entry: dict, market: dict, table: dict):'''

P_NOVOE = '''def _podpisat(zapis: dict) -> dict:
    """YASHCHIK_STOLA_V1: поставить имя автора на запись.

    Без подписи следующий житель не отличит свои события от чужих —
    и присвоит их, как случилось на A06. Имя не читается — оставляем
    без подписи: неподписанное чужим не станет, а выдуманное станет.
    """
    try:
        imya = (_kto_ya() or "").strip()
        if imya:
            zapis = dict(zapis)
            zapis["кто"] = imya
    except Exception:
        pass
    return zapis


def _append_diary(signal: dict, diary_entry: dict, market: dict, table: dict):'''


P2_STAROE = '''    STATE_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts":        time.time(),'''

P2_NOVOE = '''    STATE_DIR.mkdir(parents=True, exist_ok=True)
    # YASHCHIK_STOLA_V1: каждая запись подписывается автором — см.
    # _podpisat ниже по файлу. Тетрадь переживает жильцов, и без
    # подписи следующий не отличит своё от чужого.
    event = _podpisat({
        "ts":        time.time(),'''

# хвост словаря записан в мозгах по-разному — закрываем скобку по
# ближайшему общему якорю, а не по комментарию, который у каждого свой
def _hvost_zapisi(text: str):
    """(старое, новое) для закрытия скобки словаря записи."""
    for staroe in ('        "result":    None,   # допишет жизнь при закрытии позиции\n    }',
                   '        "result":    None,\n    }'):
        if text.count(staroe) == 1:
            return staroe, staroe[:-1] + "})"
    return None, None


def sobrat(koren: Path) -> list:
    g = koren / "GRONDHEIM_CITY"
    mozgi = sorted(g.glob("Биржа/цеха/*/слоты/*/мозг.py"))
    out = []
    for p in mozgi:
        t = p.read_text(encoding="utf-8")
        if "_read_recent_diary" not in t:
            continue
        _h = _hvost_zapisi(t)
        out.append((p, [(M3_STAROE, M3_NOVOE), (M1_STAROE, M1_NOVOE),
                        (M2_STAROE, M2_NOVOE), (P_STAROE, P_NOVOE),
                        (P2_STAROE, P2_NOVOE)]
                   + ([_h] if _h[0] else [])))
    out.append((koren / "Биржа" / "ruki_treydera.py", [(R_STAROE, R_NOVOE)]))
    return out


# ─────────────────────────── механика ───────────────────────────

def nayti_koren() -> Path:
    for k in (Path(__file__).resolve().parent, Path.cwd()):
        for p in [k, *k.parents]:
            if (p / "GRONDHEIM_CITY").is_dir() and (p / "Биржа").is_dir():
                return p
    print("Не нашёл корень репозитория (нужны папки GRONDHEIM_CITY и Биржа).")
    zhdat_i_vyyti(1)


def pravit(put: Path, zameny) -> str:
    if not put.is_file():
        return "мимо: файла нет"
    text = put.read_text(encoding="utf-8")
    if MARKER in text:
        return "уже"
    for staroe, _ in zameny:
        n = text.count(staroe)
        if n != 1:
            return f"мимо: якорь «{staroe.strip().splitlines()[0][:44]}…» × {n}"
    novyy = text
    for staroe, novoe in zameny:
        novyy = novyy.replace(staroe, novoe, 1)
    novyy = novyy.rstrip("\n") + f"\n\n# {MARKER} - marker\n"
    try:
        ast.parse(novyy)
    except SyntaxError as e:
        return f"мимо: правка ломает синтаксис ({e.lineno}: {e.msg})"
    if SUHO:
        return "сделано (сухой прогон)"
    put.with_name(put.name + f".bak_yashchik_{SHTAMP}").write_text(
        text, encoding="utf-8")
    put.write_text(novyy, encoding="utf-8")
    return "сделано"


def zhdat_i_vyyti(kod=0):
    try:
        input("\nEnter — закрыть окно...")
    except EOFError:
        pass
    sys.exit(kod)


def main():
    koren = nayti_koren()
    print(f"Корень города: {koren}")
    if SUHO:
        print("СУХОЙ ПРОГОН — ничего не записываю.\n")

    itogi = []
    print()
    for put, zameny in sobrat(koren):
        r = pravit(put, zameny)
        print(f"  {r:<30} {put.relative_to(koren)}")
        itogi.append(r)

    print("\n" + "─" * 66)
    print(f"поправлено: {sum(1 for x in itogi if x.startswith('сделано'))}   "
          f"уже стояло: {sum(1 for x in itogi if x == 'уже')}   "
          f"не тронуто: {sum(1 for x in itogi if x.startswith('мимо'))}")
    print("─" * 66)
    if any(x.startswith("мимо") for x in itogi):
        print("Что не нашлось — НЕ тронуто, наугад не правлю.")

    print("""
ЧТО ИЗМЕНИТСЯ

  В стопке было:  === ТВОЙ ДНЕВНИК (последние события — твоя память) ===
                  [пять отказов Брута про пробой фрактала]

  Станет:         === ТВОИ СОБЫТИЯ (входы и чем кончились) ===
                  (пусто — первое решение)

  У Ильи входов ещё не было, значит в голове будет ЧИСТО. Это и
  нужно: пусть скажет свой канон, а не заученный чужой.

  Журнал места цел, ничего не удалено. Захочет посмотреть, что тут
  делали до него, — попросит рукой, и первой строкой прочтёт:
  «Это записи РАБОЧЕГО МЕСТА, а не твоя память. Место старше тебя.
   Среди них есть чужие — писали: Брут.»

ЧТО СПРОСИТЬ ПОСЛЕ НАКАТКИ
  Тот же вопрос: «опиши свой вход». Если он снова скажет про пробой
  фрактала — значит это уже его собственное убеждение, и разговор
  пойдёт с ним. Если скажет иначе — мы весь день чистили правильно.
""")
    zhdat_i_vyyti(0)


if __name__ == "__main__":
    main()
