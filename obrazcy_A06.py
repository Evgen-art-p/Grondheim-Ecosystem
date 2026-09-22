# -*- coding: utf-8 -*-
"""
obrazcy_A06.py — Синди видит картинки-образцы из своих знаний.

Слово Шефа 22.09: «ей видеть нужно, что я показываю, а она только
читает». Знания уходили к ней только текстом.

Что делает:
  1. В её мозг.py добавляет: при каждом пробуждении после её кадра
     (и кадра Шефа из «Взгляда», если он есть) ей показываются
     картинки из знания/образцы/ — с подписью «ОБРАЗЕЦ из знаний,
     не твой рынок» и текстом из .md/.txt с тем же именем.
     Не больше трёх картинок. Её кадр, стол и руки не трогаются.
  2. Создаёт пустую папку
     GRONDHEIM_CITY/Биржа/цеха/торговый_хаос/слоты/A06/знания/образцы/

Запуск: положить в корень репы, запустить. Сам находит мозг.py.
Копия: мозг.py.bak_obrazcy. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "OBRAZCY_V1"
PUT = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                   "слоты", "A06", "мозг.py")
STAROE = "                            + _kadr_shefa()),\n"
NOVOE = "                            + _kadr_shefa() + _obrazcy()),  # OBRAZCY_V1\n"
YAKOR = "# VZGLYAD_DOHODIT_V1 - marker\n"
FUNK = '\n\n# ── OBRAZCY_V1: картинки-образцы из знаний ────────────────────\n# Слово Шефа 22.09: «ей видеть нужно, что я показываю, а она только\n# читает». Знания уходят к ней текстом, картинки из них не брались.\n# Теперь в знаниях есть папка образцы/: картинка + рядом .md/.txt с\n# тем же именем — пара строк, что на ней. Её кадр остаётся ПЕРВЫМ,\n# кадр Шефа (если есть) — вторым, образцы — после, с подписью.\n# Образцов не больше трёх: каждая картинка идёт в каждое пробуждение.\nOBRAZCY_DIR = KNOWLEDGE_DIR / "образцы"\nOBRAZCY_MAKS = 3\n\n\ndef _obrazcy() -> list:\n    """Картинки-образцы из знания/образцы/. Нет папки — пусто."""\n    try:\n        import base64\n        if not OBRAZCY_DIR.exists():\n            return []\n        mime = {".png": "image/png", ".jpg": "image/jpeg",\n                ".jpeg": "image/jpeg", ".webp": "image/webp"}\n        kartinki = [f for f in sorted(OBRAZCY_DIR.iterdir())\n                    if f.is_file() and f.suffix.lower() in mime]\n        if len(kartinki) > OBRAZCY_MAKS:\n            print(f"[ОБРАЗЦЫ] ⚠️  в папке {len(kartinki)}, беру первые "\n                  f"{OBRAZCY_MAKS} по алфавиту")\n            kartinki = kartinki[:OBRAZCY_MAKS]\n        vyshlo = []\n        for f in kartinki:\n            podpis = ""\n            for ext in (".md", ".txt"):\n                t = f.with_suffix(ext)\n                if t.exists():\n                    try:\n                        podpis = " ".join(\n                            t.read_text(encoding="utf-8").split())\n                    except Exception:\n                        podpis = ""\n                    break\n            vyshlo.append({\n                "base64": base64.b64encode(f.read_bytes()).decode("ascii"),\n                "mime_type": mime[f.suffix.lower()],\n                "name": (f"ОБРАЗЕЦ из знаний, не твой рынок · {f.stem}"\n                         + (f" — {podpis}" if podpis else ""))})\n        return vyshlo\n    except Exception as _e:\n        print(f"[ОБРАЗЦЫ] не подложились ({_e}) — не беда")\n        return []\n\n\n# OBRAZCY_V1 - marker\n'


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    p = os.path.join(papka, PUT)
    return p if os.path.isfile(p) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        p = godnyy(papka)
        if p:
            return p
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = godnyy(os.path.join(koren, imya))
                if p and p not in kandidaty:
                    kandidaty.append(p)
        except Exception:
            pass
    if len(kandidaty) == 1:
        otv = input(f"Нашёл: {kandidaty[0]}\nЭтот? (Enter — да, н — нет): ")
        if otv.strip().lower() not in ("н", "n", "нет", "no"):
            return kandidaty[0]
    elif len(kandidaty) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(kandidaty, 1):
            print(f"  {i}. {p}")
        otv = input("Какой? Цифра: ").strip()
        if otv.isdigit() and 1 <= int(otv) <= len(kandidaty):
            return kandidaty[int(otv) - 1]
    otv = input("Перетащи сюда папку репы и нажми Enter:\n")
    return godnyy(otv.strip().strip('"').strip("'"))


def main():
    put = nayti()
    if not put:
        print("✗ мозг.py слота A06 не найден. Ничего не менял.")
        return
    papka = os.path.join(os.path.dirname(put), "знания", "образцы")
    os.makedirs(papka, exist_ok=True)

    with open(put, "rb") as f:
        tekst = f.read().decode("utf-8")
    crlf = "\r\n" in tekst
    t = tekst.replace("\r\n", "\n")
    if METKA in t:
        print("✓ Уже накатано раньше — ничего не менял.")
        print(f"  папка образцов: {papka}")
        return
    k = t.count(STAROE)
    if k != 2 or t.count(YAKOR) != 1:
        print(f"✗ Места в мозге не нашлись как ожидалось (картинок: {k}, "
              f"метка: {t.count(YAKOR)}). Ничего не менял. Покажи Брату.")
        return
    t = t.replace(STAROE, NOVOE)
    t = t.replace(YAKOR, YAKOR + FUNK, 1)
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"✗ После правки файл не собирается: {e}. Ничего не менял.")
        return
    bak = put + ".bak_obrazcy"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    vyvod = t.replace("\n", "\r\n") if crlf else t
    with open(put, "wb") as f:
        f.write(vyvod.encode("utf-8"))
    try:
        py_compile.compile(put, doraise=True)
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, put)
        print(f"✗ Не скомпилировался, вернул как было: {e}")
        return
    print(f"✓ Готово: {put}")
    print(f"  копия до правки: {bak}")
    print(f"  папка образцов: {papka}")
    print("  Клади туда картинку и рядом .md с тем же именем — пара строк, что на ней.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
