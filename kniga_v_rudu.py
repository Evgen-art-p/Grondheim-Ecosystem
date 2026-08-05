# -*- coding: utf-8 -*-
# KNIGA_V_RUDU_V1
"""
КНИГА → РУДА АКАДЕМИИ. Раскладывает PDF-книгу постранично так, чтобы
ученик читал её со стола по порядку, своим глазом.

ЗАЧЕМ ИМЕННО ПОСТРАНИЧНО
    В книге Вильямса картинка и разбор стоят НА ОДНОЙ СТРАНИЦЕ, рядом.
    Резать иллюстрации отдельно — значит разорвать пару «график и что
    про него сказано». Поэтому страница идёт целиком.

ДВА ВИДА СТРАНИЦ — РАЗНАЯ ЦЕНА
    страница С РИСУНКАМИ  -> PNG, идёт в руду/изображения (работает глаз)
    страница БЕЗ рисунков -> TXT, идёт в руду/тексты      (работает чтение)
    Гнать чистый текст картинкой можно, но это впустую: зрение дорогое,
    а разглядывать там нечего.

ПОРЯДОК ВИДЕН В ИМЕНИ
    kn1_gl08_str04.png — книга 1, глава 8, страница 4. Папки в Академии
    разные (тексты/изображения), поэтому порядок держится именем, иначе
    ученик прочтёт вразнобой.

ЧТО НУЖНО ОДИН РАЗ:
    pip install pymupdf

ЗАПУСК из корня репо:
    python kniga_v_rudu.py <папка_с_pdf> --kniga 1
    python kniga_v_rudu.py <папка_с_pdf> --kniga 1 --dpi 240   # если мелко
    python kniga_v_rudu.py <папка_с_pdf> --kniga 1 --suho      # проверка

Повторный запуск ничего не портит: готовые страницы пропускаются.
"""
import argparse
import re
import sys
from pathlib import Path

MARKER = "KNIGA_V_RUDU_V1"
_REPO = Path(__file__).resolve().parent
_RUDA = _REPO / "GRONDHEIM_CITY" / "Академия" / "руда"

# 200 точек на дюйм: на пробе главы 8 бары и подписи читались уверенно.
# Мельче — модель начнёт додумывать; крупнее — файлы тяжелеют без пользы.
DPI_PO_UMOLCHANIYU = 200

# Порядок глав в имени файла берём из имени PDF: trch8.pdf -> 08.
# Если в имени числа нет, глава уйдёт в конец (99) — не потеряется.
_NOMER = re.compile(r"(\d+)")


def _nomer_glavy(imya: str) -> int:
    m = _NOMER.search(imya)
    return int(m.group(1)) if m else 99


def main() -> int:
    p = argparse.ArgumentParser(description="Книга → руда Академии")
    p.add_argument("papka", help="папка с PDF-файлами книги")
    p.add_argument("--kniga", default="1", help="номер книги для имён (по умолчанию 1)")
    p.add_argument("--dpi", type=int, default=DPI_PO_UMOLCHANIYU)
    p.add_argument("--suho", action="store_true", help="только показать, ничего не писать")
    a = p.parse_args()

    try:
        import fitz  # pymupdf
    except ImportError:
        print("✗ нет pymupdf. Поставь один раз:  pip install pymupdf")
        return 1

    src = Path(a.papka)
    if not src.is_dir():
        print(f"✗ не папка: {src}")
        return 1

    pdfy = sorted(src.glob("*.pdf"), key=lambda f: _nomer_glavy(f.stem))
    if not pdfy:
        print(f"✗ в {src} нет ни одного .pdf")
        return 1

    kartinki = _RUDA / "изображения"
    teksty = _RUDA / "тексты"
    if not a.suho:
        kartinki.mkdir(parents=True, exist_ok=True)
        teksty.mkdir(parents=True, exist_ok=True)

    vsego_kart = vsego_tekst = propushcheno = 0
    print(f"Книга {a.kniga}: {len(pdfy)} файл(ов), {a.dpi} dpi"
          f"{'  [СУХОЙ ПРОГОН]' if a.suho else ''}\n")

    for f in pdfy:
        gl = _nomer_glavy(f.stem)
        try:
            doc = fitz.open(f)
        except Exception as e:
            print(f"  ⚠ {f.name}: не открыть ({e}) — пропускаю")
            continue

        s_kart = s_tekst = 0
        for i, stranica in enumerate(doc, start=1):
            osnova = f"kn{a.kniga}_gl{gl:02d}_str{i:02d}"
            # Рисунок на странице ищем двумя способами: вставленной
            # картинкой и векторным чертежом. В книге встречается и то,
            # и другое -- графики бывают нарисованы линиями, а не фото.
            est_risunok = bool(stranica.get_images(full=True)) or \
                          len(stranica.get_drawings()) > 2

            if est_risunok:
                out = kartinki / f"{osnova}.png"
                if out.exists():
                    propushcheno += 1
                    continue
                if not a.suho:
                    stranica.get_pixmap(dpi=a.dpi).save(out)
                s_kart += 1
            else:
                tekst = stranica.get_text().strip()
                if not tekst:
                    continue          # пустая страница -- не мусорим
                out = teksty / f"{osnova}.txt"
                if out.exists():
                    propushcheno += 1
                    continue
                if not a.suho:
                    out.write_text(tekst, encoding="utf-8")
                s_tekst += 1

        vsego_kart += s_kart
        vsego_tekst += s_tekst
        print(f"  глава {gl:02d} ({f.name}): {len(doc):3d} стр. → "
              f"{s_kart:3d} с рисунками, {s_tekst:3d} текстом")
        doc.close()

    print(f"\n✓ {MARKER}")
    print(f"  страниц с рисунками: {vsego_kart}  → {kartinki}")
    print(f"  страниц текстом:     {vsego_tekst}  → {teksty}")
    if propushcheno:
        print(f"  уже лежало, не трогал: {propushcheno}")
    if a.suho:
        print("\n  Это был сухой прогон — на диск не писал ничего.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
