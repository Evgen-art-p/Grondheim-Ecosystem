# -*- coding: utf-8 -*-
"""
obrazcy_v_znaniya.py — образцы уходят к Синди ВМЕСТЕ СО ЗНАНИЯМИ, а не
рядом с её кадром.

Что сломалось (22.09, прогон с 2025.05.01): образцы шли в одном
сообщении с её кадром — модель смешала картинки и описала образец
(«восходящий ход замедляется, AO показывает дивергенцию») вместо своего
графика. Подпись «не твой рынок» не удержала.

Что стало:
  1. Биржа/llm.py — у chat_with_images и chat_with_images_and_tools
     новый вход knowledge_images. Образцы кладутся в сообщение
     «БАЗА ЗНАНИЙ» в самом начале разговора, как учебник, с пометкой
     «это НЕ твой рынок, твой кадр придёт позже, в вопросе». Кто этот
     вход не передаёт — у того всё как было.
  2. Мозг A06 — образцы передаются через knowledge_images, в вопросе
     остаётся только её кадр (и кадр Шефа из «Взгляда», если есть).
     Её кадр подписан «ТВОЙ КАДР, рынок сейчас». В лог — строчка
     «[ОБРАЗЦЫ] в знаниях: N», чтобы видно было, что дошли.

Нужен уже накатанный obrazcy_A06.py.

Запуск: положить в корень репы, запустить. Сам находит оба файла.
Сначала проверяет оба, потом пишет. Копии: llm.py.bak_obrazcy_znaniya,
мозг.py.bak_obrazcy_znaniya. Повторный запуск ничего не ломает.
"""
import ast
import os
import py_compile
import shutil

METKA = "OBRAZCY_V_ZNANIYA_V1"
PUT_LLM = os.path.join("Биржа", "llm.py")
PUT_MOZG = os.path.join("GRONDHEIM_CITY", "Биржа", "цеха", "торговый_хаос",
                        "слоты", "A06", "мозг.py")

POMOSHCHNIK = '''

# ── OBRAZCY_V_ZNANIYA_V1: образцы идут со знаниями, не с кадром ──
# Образцы в одном сообщении с кадром модель смешивала и описывала
# образец вместо своего рынка. Теперь они — часть «базы знаний» в
# начале разговора, как учебник; кадр остаётся один в вопросе.
def _znaniya_s_obrazcami(knowledge: str, knowledge_images=None):
    if not knowledge_images:
        return f"БАЗА ЗНАНИЙ:\\n{knowledge}"
    kuski = [{"type": "text", "text": f"БАЗА ЗНАНИЙ:\\n{knowledge}"},
             {"type": "text", "text":
              "ОБРАЗЦЫ ИЗ УЧЕБНИКА. Это НЕ твой рынок и НЕ сегодняшний "
              "кадр — так выглядит правило. Твой кадр придёт позже, в "
              "вопросе, отдельно."}]
    for img in knowledge_images:
        b64 = img.get("base64", "")
        if not b64:
            continue
        kuski.append({"type": "text",
                      "text": f"[Образец: {img.get('name', 'образец')}]"})
        kuski.append({"type": "image_url", "image_url": {
            "url": f"data:{img.get('mime_type', 'image/png')};base64,{b64}"}})
    return kuski


'''

L_ZNANIYA_1 = '''    if knowledge:
        messages.append({"role": "user", "content": f"БАЗА ЗНАНИЙ:\\n{knowledge}"})
        messages.append({"role": "assistant", "content": "Принял базу знаний. Готов к работе."})
'''
L_ZNANIYA_1_NOV = '''    if knowledge or knowledge_images:   # OBRAZCY_V_ZNANIYA_V1
        messages.append({"role": "user", "content":
                         _znaniya_s_obrazcami(knowledge, knowledge_images)})
        messages.append({"role": "assistant", "content": "Принял базу знаний. Готов к работе."})
'''
L_ZNANIYA_2 = '''    if knowledge:
        messages.append({"role": "user",
                         "content": f"БАЗА ЗНАНИЙ:\\n{knowledge}"})
        messages.append({"role": "assistant",
                         "content": "Принял базу знаний. Готов к работе."})
'''
L_ZNANIYA_2_NOV = '''    if knowledge or knowledge_images:   # OBRAZCY_V_ZNANIYA_V1
        messages.append({"role": "user", "content":
                         _znaniya_s_obrazcami(knowledge, knowledge_images)})
        messages.append({"role": "assistant",
                         "content": "Принял базу знаний. Готов к работе."})
'''
L_SIG_1 = '''                     knowledge_source: str = "internal") -> str:
    """
    Отправляет запрос с изображениями (vision).'''
L_SIG_1_NOV = '''                     knowledge_source: str = "internal",
                     knowledge_images: Optional[list] = None) -> str:
    """
    Отправляет запрос с изображениями (vision).'''
L_SIG_2 = '''    knowledge_source: str = "internal",
) -> str:
    """Разговор с кадром'''
L_SIG_2_NOV = '''    knowledge_source: str = "internal",
    knowledge_images: Optional[list] = None,
) -> str:
    """Разговор с кадром'''
L_DEF_1 = "def chat_with_images(system"
L_DEF_2 = "def chat_with_images_and_tools("

M_OBRAZCY = "                            + _kadr_shefa() + _obrazcy()),  # OBRAZCY_V1\n"
M_OBRAZCY_NOV = ("                            + _kadr_shefa()),\n"
                 "                    knowledge_images=_obrazcy(),  # OBRAZCY_V_ZNANIYA_V1\n")
M_IMYA = '_P(put).name}]'
M_IMYA_NOV = '"ТВОЙ КАДР, рынок сейчас · " + _P(put).name}]'
M_RETURN = "        return vyshlo\n"
M_RETURN_NOV = ("        if vyshlo:\n"
                "            print(f\"[ОБРАЗЦЫ] в знаниях: {len(vyshlo)}\")\n"
                "        return vyshlo\n")


def pauza():
    try:
        input("\nНажми Enter, чтобы закрыть окно...")
    except Exception:
        pass


def godnyy(papka):
    return papka if (os.path.isfile(os.path.join(papka, PUT_LLM)) and
                     os.path.isfile(os.path.join(papka, PUT_MOZG))) else None


def nayti():
    zdes = os.path.dirname(os.path.abspath(__file__))
    for papka in (zdes, os.getcwd()):
        if godnyy(papka):
            return papka
    kandidaty = []
    for koren in {os.path.dirname(zdes), os.path.dirname(os.getcwd())}:
        try:
            for imya in os.listdir(koren):
                p = os.path.join(koren, imya)
                if godnyy(p) and p not in kandidaty:
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
    otv = input("Перетащи сюда папку репы и нажми Enter:\n").strip().strip('"').strip("'")
    return godnyy(otv)


def prochest(put):
    with open(put, "rb") as f:
        t = f.read().decode("utf-8")
    return t.replace("\r\n", "\n"), "\r\n" in t


def v_funkcii(t, imya_def, staroe, novoe):
    """Заменить staroe один раз — только внутри функции imya_def."""
    i = t.find(imya_def)
    if i < 0:
        return None
    j = t.find("\ndef ", i + 1)
    j = len(t) if j < 0 else j
    kusok = t[i:j]
    if kusok.count(staroe) != 1:
        return None
    return t[:i] + kusok.replace(staroe, novoe, 1) + t[j:]


def pravit_llm(t):
    for imya_def, s, n in ((L_DEF_1, L_ZNANIYA_1, L_ZNANIYA_1_NOV),
                           (L_DEF_2, L_ZNANIYA_2, L_ZNANIYA_2_NOV),
                           (L_DEF_1, L_SIG_1, L_SIG_1_NOV),
                           (L_DEF_2, L_SIG_2, L_SIG_2_NOV)):
        t = v_funkcii(t, imya_def, s, n)
        if t is None:
            return None
    i = t.find(L_DEF_1)
    return t[:i] + POMOSHCHNIK.lstrip("\n") + t[i:]


def pravit_mozg(t):
    if "OBRAZCY_V1" not in t:
        return "нет_образцов"
    if t.count(M_OBRAZCY) != 2 or t.count(M_IMYA) != 2 or t.count(M_RETURN) != 1:
        return None
    return (t.replace(M_OBRAZCY, M_OBRAZCY_NOV)
             .replace(M_IMYA, M_IMYA_NOV)
             .replace(M_RETURN, M_RETURN_NOV, 1))


def zapisat(put, t, crlf):
    bak = put + ".bak_obrazcy_znaniya"
    if not os.path.exists(bak):
        shutil.copy2(put, bak)
    with open(put, "wb") as f:
        f.write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return bak


def main():
    repo = nayti()
    if not repo:
        print("✗ Не нашёл репу (нужны Биржа/llm.py и мозг.py A06). Ничего не менял.")
        return
    p_llm = os.path.join(repo, PUT_LLM)
    p_mozg = os.path.join(repo, PUT_MOZG)
    t_llm, crlf_llm = prochest(p_llm)
    t_mozg, crlf_mozg = prochest(p_mozg)

    if METKA in t_llm and METKA in t_mozg:
        print("✓ Уже накатано раньше — ничего не менял.")
        return

    n_llm = t_llm if METKA in t_llm else pravit_llm(t_llm)
    n_mozg = t_mozg if METKA in t_mozg else pravit_mozg(t_mozg)
    if n_mozg == "нет_образцов":
        print("✗ В мозге нет образцов — сначала obrazcy_A06.py. Ничего не менял.")
        return
    if n_llm is None or n_mozg is None:
        print("✗ Места нашлись не так, как ожидалось "
              f"({'llm.py' if n_llm is None else 'мозг.py'}). Ничего не менял. Покажи Брату.")
        return
    for imya, t in (("llm.py", n_llm), ("мозг.py", n_mozg)):
        try:
            ast.parse(t)
        except SyntaxError as e:
            print(f"✗ {imya} после правки не собирается: {e}. Ничего не менял.")
            return

    zapisany = []
    for put, t, staroe, crlf in ((p_llm, n_llm, t_llm, crlf_llm),
                                 (p_mozg, n_mozg, t_mozg, crlf_mozg)):
        if t == staroe:
            continue
        bak = zapisat(put, t, crlf)
        zapisany.append((put, bak))
        try:
            py_compile.compile(put, doraise=True)
        except py_compile.PyCompileError as e:
            for p, b in zapisany:
                shutil.copy2(b, p)
            print(f"✗ Не скомпилировалось, вернул оба как было: {e}")
            return
    for put, bak in zapisany:
        print(f"✓ {put}\n  копия до правки: {bak}")
    print("  Образцы теперь идут со знаниями, в вопросе — только её кадр.")
    print("  Верни три .png в знания/образцы/ и запускай.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Ошибка: {e}")
    pauza()
