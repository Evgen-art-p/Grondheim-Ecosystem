# -*- coding: utf-8 -*-
# PROSEV_ZNANII_DOMA_V1
"""
ЗНАНИЕ ОСЕДАЕТ И ДОМА, НЕ ТОЛЬКО В АКАДЕМИИ.

ЗАЧЕМ. У жителя есть СВОЙ загрузчик и своя руда (dom/руда_входящее), и
читает он дома так же, как студент в Академии. Но просев дома —
отдельный код в ui_zhitel.py, и он спрашивает ровно то же самое:

    «Что это говорит о тебе? Чем ты стал(а) немного другой?
     …вывод о себе, НЕ пересказ моментов.»

То есть дома та же дыра, что мы нашли в Академии: прочитанное ложится
событием в архив, а наверх поднимается только переживание. PROSEV_ZNANII_V1
туда не достаёт — другой файл.

ВТОРАЯ ПРИЧИНА, ПОЧЕМУ НЕ ДОСТАЁТ. Метка контекста разная:
    Академия пишет   «[Академия] «имя»: …»
    дом пишет        «[Знание: Дом] книга «имя»: …»  /  «[Знание: Цех] …»
Разбор тем в Академии ловил только первую форму. Здесь он расширен на
обе — и в ОБОИХ файлах, чтобы просев ловил всё, что житель читал, где
бы он его ни запустил.

ЧТО СТАНОВИТСЯ
    Дома просев тоже ходит дважды: сперва «что это говорит о тебе»
    (как было, метка «жизнь»), потом «что ты УЗНАЛА» по учебным
    записям — вывод «учёба» с ключом темы.

    Дома есть своя особенность: прочитанная книга ПЕРЕЕЗЖАЕТ в папку
    «прочитано» и со стола пропадает (в Академии руда общая и остаётся).
    Значит второго шанса прочитать её нет — тем важнее, чтобы с первого
    раза осталось не только впечатление.

ПОРЯДОК: после patch_prosev_znanii.py — этот патч правит его же разбор тем.

ЗАПУСК из корня репо:
    python patch_prosev_znanii_doma.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "PROSEV_ZNANII_DOMA_V1"

T_AK = Path("Академия") / "ui_akademia.py"
B_AK = Path("Академия") / "ui_akademia.py.bak_znanie_doma"
T_ZH = Path("жители") / "ui_zhitel.py"
B_ZH = Path("жители") / "ui_zhitel.py.bak_znanie_doma"

# ═══════════════════════════════════════════════════════════
# АКАДЕМИЯ — расширяем разбор тем на домашнюю метку
# ═══════════════════════════════════════════════════════════
AK_OLD = '''    import re as _re
    temy = {}
    for mm in momenty or []:
        fakt = str(mm.get("факт", ""))
        if not fakt.startswith("[Академия]"):
            continue
'''

AK_NEW = '''    import re as _re
    temy = {}
    for mm in momenty or []:
        fakt = str(mm.get("факт", ""))
        # PROSEV_ZNANII_DOMA_V1: житель читает и дома, а дом ставит свою
        # метку контекста. Ловим обе формы, иначе просев видит только
        # половину прочитанного — смотря где его запустили.
        if not (fakt.startswith("[Академия]") or fakt.startswith("[Знание:")):
            continue
'''

# ═══════════════════════════════════════════════════════════
# ДОМ — свой заход за знанием
# ═══════════════════════════════════════════════════════════
ZH_OLD = '''async def _provesti_prosev(dv: Dvizhok, p: dict, model: str) -> dict:
    """PATCH_PROSEV_REQUEST_V1: тело просева — общее для кнопки «🪞
'''

ZH_NEW = '''# PROSEV_ZNANII_DOMA_V1 — второй заход просева: за содержанием
_ZNANIE_MAX_TEM_DOMA = 3   # больше трёх тем за просев не берём — это деньги


def _uchebnye_temy_doma(momenty: list) -> dict:
    """Разбирает моменты просева на темы учёбы: {имя книги: [моменты]}.

    Читальные записи узнаём по метке контекста в начале факта: дома это
    «[Знание: Дом]» или «[Знание: Цех]», в Академии — «[Академия]».
    Ловим обе, потому что архив у жителя один: читал он и там, и тут.
    Всё прочее — личная жизнь, её не трогаем.
    """
    import re as _re
    temy = {}
    for mm in momenty or []:
        fakt = str(mm.get("факт", ""))
        if not (fakt.startswith("[Знание:") or fakt.startswith("[Академия]")):
            continue
        m = _re.search(r"«([^»]+)»", fakt)
        tema = (m.group(1) if m else "материал").strip()
        temy.setdefault(tema, []).append(mm)
    return temy


async def _prosev_znanii_doma(dv, dusha: str, momenty: list,
                              model: str = "") -> list:
    """Спрашивает, что житель УЗНАЛ — отдельно от того, что почувствовал.

    Вопрос нарочно противоположен первому заходу: там «не пересказывай»,
    здесь «перескажи точно». Без этого содержание из памяти выпадает
    целиком, а остаётся одно впечатление.

    Ложится черновиком, а не сразу меткой: это собственный пересказ
    жителя, он может быть неверен. Черновики в промпт подаются, значит
    знание с ним везде. Затвердеет от судьи — поправка учителя или
    третья встреча с тем же.
    """
    itogi = []
    temy = list(_uchebnye_temy_doma(momenty).items())[:_ZNANIE_MAX_TEM_DOMA]
    for tema, gruppa in temy:
        spisok = "\\n".join(f"— {str(g.get('факт',''))}" for g in gruppa)
        vopros = (
            f"Вот что ты читал(а) по теме «{tema}»:\\n{spisok}\\n\\n"
            f"Что ты УЗНАЛ(А)? Своими словами, но ТОЧНО: определения, "
            f"порядок действий, названия и числа сохрани как есть, ничего "
            f"не округляй и не сглаживай. Это не про чувства — про "
            f"содержание.\\n3–6 строк. Чего-то не понял(а) — так и напиши, "
            f"это нормальный ответ и он полезнее выдуманного.\\n"
            f"Без строк MEMORY_REQUEST."
        )
        try:
            vyvod = await call_zhitel_llm(
                [{"role": "system", "content": dusha},
                 {"role": "user", "content": vopros}], model)
        except Exception:
            continue
        if not vyvod or vyvod.startswith("⚠"):
            continue
        try:
            vyvod = _ubrat_memory_request(vyvod) or vyvod.strip()
            res = dv.dopisat_vyvod(vyvod.strip(),
                                   pattern=f"знание:{tema}", otkuda="учёба")
        except Exception:
            continue
        if res.get("дописано"):
            itogi.append((tema, res.get("этаж", "?")))
    return itogi


async def _provesti_prosev(dv: Dvizhok, p: dict, model: str) -> dict:
    """PATCH_PROSEV_REQUEST_V1: тело просева — общее для кнопки «🪞
'''

# ═══════════════════════════════════════════════════════════
# ДОМ — врезка в само тело просева
# ═══════════════════════════════════════════════════════════
ZH2_OLD = '''    res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
    if res.get("дописано"):
        try:
            dv.otmetit_prosejannym([m.get("id") for m in momenty if m.get("id")])
        except Exception:
            pass
    return {"ok": True, "вывод": vyvod, "moments": momenty, "res": res}
'''

ZH2_NEW = '''    res = dv.dopisat_vyvod(vyvod, pattern=None, otkuda="жизнь")
    # PROSEV_ZNANII_DOMA_V1: второй заход — за содержанием, отдельной
    # строкой от чувств. Не удался — просев всё равно состоялся.
    _znaniya = []
    try:
        _znaniya = await _prosev_znanii_doma(dv, dusha, momenty, model)
    except Exception:
        pass
    if res.get("дописано"):
        try:
            dv.otmetit_prosejannym([m.get("id") for m in momenty if m.get("id")])
        except Exception:
            pass
    return {"ok": True, "вывод": vyvod, "moments": momenty, "res": res,
            "знания": _znaniya}
'''

PRAVKI = [
    (T_AK, B_AK, [("разбор тем ловит и домашнюю метку", AK_OLD, AK_NEW)]),
    (T_ZH, B_ZH, [("заход за знанием дома", ZH_OLD, ZH_NEW),
                  ("врезка в тело просева", ZH2_OLD, ZH2_NEW)]),
]


def main() -> int:
    for target, _, _ in PRAVKI:
        if not target.exists():
            print(f"✗ не нашёл {target} — запускать из КОРНЯ репо")
            return 1

    if all(MARKER in t.read_text(encoding="utf-8") for t, _, _ in PRAVKI):
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    if "PROSEV_ZNANII_V1" not in T_AK.read_text(encoding="utf-8"):
        print("✗ сначала накати patch_prosev_znanii.py")
        return 1

    gotovo = []
    for target, bak, pravki in PRAVKI:
        src = target.read_text(encoding="utf-8")
        if MARKER in src:
            print(f"  · {target.name} — уже пропатчен, пропускаю")
            continue
        novyy = src
        for imya, old, new in pravki:
            n = novyy.count(old)
            if n != 1:
                print(f"✗ {target.name}, якорь «{imya}»: найден {n} раз "
                      f"(нужно 1). НИЧЕГО не применено.")
                return 1
            novyy = novyy.replace(old, new, 1)
        try:
            ast.parse(novyy)
        except SyntaxError as e:
            print(f"✗ {target.name}: ast.parse упал: {e}. Не записал.")
            return 1
        gotovo.append((target, bak, src, novyy))
        print(f"  · {target.name} — готов")

    for target, bak, src, novyy in gotovo:
        shutil.copy2(target, bak)
        target.write_text(novyy, encoding="utf-8")
        try:
            py_compile.compile(str(target), doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, target)
            print(f"✗ {target.name}: py_compile упал: {e}. Откатил.")
            return 1
        print(f"✓ {target.name}: {len(src)} → {len(novyy)} символов")

    print(f"\n✓ {MARKER} применён")
    print("\n  Теперь знание оседает и дома, и в Академии — где бы")
    print("  житель ни читал и где бы ты ни нажал «Осмыслить».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
