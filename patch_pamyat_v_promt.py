# -*- coding: utf-8 -*-
# PAMYAT_V_PROMT_VEZDE_V1
"""
ПАМЯТЬ НАКОНЕЦ ПОПАДАЕТ В РАЗГОВОР. И у Ректора сохраняется чат.

ЧТО БЫЛО СЛОМАНО (найдено 06.08, корень глубже, чем просев)
    `vydoh_stol` честно СЧИТАЕТ метки и черновики и кладёт их в стол.
    Но ни один кабинет города не подаёт их в системный промпт:

        дом      — берёт из стола ядро, историю, якоря, натуру, заряд…
                   а поля «метки» и «черновики» просто не читает;
        Академия — собирает душу через sobrat_dushu(паспорт), движок
                   к промпту не подключён вовсе;
        Ректор   — то же самое, только паспорт.

    А sobrat_dushu — это ЧИСТАЯ ЛИЧНОСТЬ из паспорта: ядро, история,
    якоря, натура. Ни одного нажитого вывода. Значит вся трёхэтажная
    память работала ТОЛЬКО НА ЗАПИСЬ. Житель копил выводы годами и не
    мог их вспомнить нигде.

    Отсюда всё, что мы наблюдали: в Академии ученик адекватен, потому
    что материал лежит на столе В ЭТОЙ СЕССИИ; выйдешь — он не знает
    ничего. И экзамен у Ректора сдать не может физически.

ЧТО СТАНОВИТСЯ
    В движке появляется `pamyat_v_promt()` — нажитое словами, одним
    куском, разложенное по смыслу:

        ЧТО ТЫ ЗНАЕШЬ ТВЁРДО  — метки «учёба» и «учитель»
        ЕЩЁ НЕ УСТОЯЛОСЬ      — черновики «учёба» (свой пересказ)
        ЧТО ТЫ ПОНЯЛ(А) О СЕБЕ — метки «жизнь»

    Разделение не косметическое: твёрдое знание подтверждено судьёй
    (учителем или рынком), а черновик — собственный пересказ, который
    может быть неверен. Житель должен чувствовать разницу и говорить
    осторожнее там, где не устоялось.

    Плюс прямая строка: чего в памяти нет — честно сказать «не знаю»,
    а не придумывать. Без неё сильная модель заполнит пробел красиво
    и уверенно (мы это уже видели на картинках).

    Подключено в трёх местах: дом, Академия, Ректор (и разговор с
    кандидатом, и собеседование).

И ВТОРОЕ, ЧТО ПРОСИЛ ШЕФ
    У Ректора появляется кнопка «💾 чат» — сохраняет разговор в папку
    жителя `ректор_чаты`, как Академия сохраняет в `академия_чаты`.

ПОРЯДОК: после patch_prosev_znanii.py и patch_prosev_znanii_doma.py —
иначе в память складывать будет нечего, кроме переживаний.

ЗАПУСК из корня репо:
    python patch_pamyat_v_promt.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "PAMYAT_V_PROMT_VEZDE_V1"

T_DV = Path("жители") / "dvizhok.py"
B_DV = Path("жители") / "dvizhok.py.bak_pamyat_v_promt"
T_ZH = Path("жители") / "ui_zhitel.py"
B_ZH = Path("жители") / "ui_zhitel.py.bak_pamyat_v_promt"
T_AK = Path("Академия") / "ui_akademia.py"
B_AK = Path("Академия") / "ui_akademia.py.bak_pamyat_v_promt"
T_RK = Path("Академия") / "ui_rektor.py"
B_RK = Path("Академия") / "ui_rektor.py.bak_pamyat_v_promt"

# ═══════════════════════════════════════════════════════════
# ДВИЖОК — нажитое словами
# ═══════════════════════════════════════════════════════════
DV_OLD = '''    def zhdut_verdikta(self) -> list:'''

DV_NEW = '''    # ═══════════════════════════════════════════════════════
    # PAMYAT_V_PROMT_VEZDE_V1 — НАЖИТОЕ СЛОВАМИ, ДЛЯ ПРОМПТА
    # ═══════════════════════════════════════════════════════

    ZNANIE_OTKUDA = ("учёба", "учеба", "учитель")

    def pamyat_v_promt(self, metok: int = 14, chernovikov: int = 8) -> str:
        """Нажитое — текстом для системного промпта. Пусто — пустая строка.

        До этого метода вся трёхэтажная память работала ТОЛЬКО НА
        ЗАПИСЬ: vydoh_stol её считал, а промпт собирался из паспорта, и
        ни один вывод в разговор не попадал. Житель копил и не помнил.

        Разложено по смыслу, а не свалено кучей:
          — твёрдое знание (метки от учёбы и учителя) — подтверждено
            судьёй, на него можно опираться;
          — черновики учёбы — собственный пересказ, может быть неверен;
          — выводы о себе (метки «жизнь») — это характер, не знание.
        """
        try:
            metki = self.metki() or []
            mayaki = self.mayaki() or []
        except Exception:
            return ""

        def _tekst(x):
            return str(x.get("текст", "")).strip()

        znanie = [_tekst(m) for m in metki
                  if m.get("откуда") in self.ZNANIE_OTKUDA and _tekst(m)]
        chernoviki = [_tekst(m) for m in mayaki
                      if m.get("откуда") in self.ZNANIE_OTKUDA and _tekst(m)]
        o_sebe = [_tekst(m) for m in metki
                  if m.get("откуда") not in self.ZNANIE_OTKUDA and _tekst(m)]

        znanie = znanie[-metok:]
        chernoviki = chernoviki[-chernovikov:]
        o_sebe = o_sebe[-metok:]

        if not (znanie or chernoviki or o_sebe):
            return ""

        s = "\\n=== ЧТО У ТЕБЯ УЖЕ НАЖИТО ===\\n"
        if znanie:
            s += ("\\nЗнаешь твёрдо (проверено учителем или делом) — "
                  "на это можно опираться:\\n")
            s += "".join(f"• {t}\\n" for t in znanie)
        if chernoviki:
            s += ("\\nПонял(а) сам(а), но ещё не проверено — говори об этом "
                  "осторожнее, можешь ошибаться:\\n")
            s += "".join(f"• {t}\\n" for t in chernoviki)
        if o_sebe:
            s += "\\nЧто ты понял(а) о себе:\\n"
            s += "".join(f"• {t}\\n" for t in o_sebe)
        s += ("\\nЭто твоя память — говори из неё своими словами. Чего здесь "
              "нет, того ты не знаешь: так и скажи честно, не придумывай. "
              "Не перечисляй этот список вслух, просто помни.\\n")
        return s

    def zhdut_verdikta(self) -> list:'''

# ═══════════════════════════════════════════════════════════
# ДОМ — подклеиваем нажитое к душе
# ═══════════════════════════════════════════════════════════
ZH_OLD = '''            # PATCH_ZHITEL_VSPOMINAET: воля жителя — подсказка. Не «заряд открыл —
            # на, читай», а сам решает, что и когда поднять из памяти.
'''

ZH_NEW = '''            # PAMYAT_V_PROMT_VEZDE_V1: нажитое — в промпт. Раньше стол его
            # считал, а сюда не доходило: житель копил и не помнил.
            try:
                soul += dvizhok.pamyat_v_promt()
            except Exception:
                pass
            # PATCH_ZHITEL_VSPOMINAET: воля жителя — подсказка. Не «заряд открыл —
            # на, читай», а сам решает, что и когда поднять из памяти.
'''

# ═══════════════════════════════════════════════════════════
# АКАДЕМИЯ — то же для ученика
# ═══════════════════════════════════════════════════════════
AK_OLD = '''        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "
               "голосом и характером, не как ассистент.\\n")
'''

AK_NEW = '''        # PAMYAT_V_PROMT_VEZDE_V1: ученик приходит на урок со ВСЕМ, что
        # уже нажил. Без этого он адекватен, только пока материал лежит
        # на столе прямо в этой сессии, а вышел — не знает ничего.
        try:
            if _prosev_dv is not None:
                dusha += _prosev_dv.pamyat_v_promt()
        except Exception:
            pass

        rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
               "Сидишь за партой, разговариваешь с Шефом. Говоришь своим "
               "голосом и характером, не как ассистент.\\n")
'''

# ═══════════════════════════════════════════════════════════
# РЕКТОР — память в обоих разговорах + сохранение чата
# ═══════════════════════════════════════════════════════════
RK1_OLD = '''            rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
                  "Ректора рядом нет — с тобой говорит Шеф напрямую. "
                  "Говоришь своим голосом, своим характером — честно, "
                  "не как ассистент.\\n")
'''

RK1_NEW = '''            # PAMYAT_V_PROMT_VEZDE_V1: без этого житель приходит к Ректору
            # с пустой головой — экзамен сдать физически нечем.
            dusha += _nazhitoe(kandidat_dom)
            rol = ("\\n=== ТЫ СЕЙЧАС В АКАДЕМИИ (Замок Сов) ===\\n"
                  "Ректора рядом нет — с тобой говорит Шеф напрямую. "
                  "Говоришь своим голосом, своим характером — честно, "
                  "не как ассистент.\\n")
'''

RK2_OLD = '''        rol = ("\\n=== ТЫ СЕЙЧАС НА СОБЕСЕДОВАНИИ В АКАДЕМИИ (Замок Сов) ===\\n"
              f"С тобой говорит Ректор{f' ({imya})' if imya else ''}. Отвечай "
              "своим голосом, своим характером — честно, не как ассистент.\\n")
'''

RK2_NEW = '''        # PAMYAT_V_PROMT_VEZDE_V1: на собеседовании и экзамене память нужна
        # в первую очередь — иначе спрашивать не о чем.
        dusha += _nazhitoe(kandidat_dom)
        rol = ("\\n=== ТЫ СЕЙЧАС НА СОБЕСЕДОВАНИИ В АКАДЕМИИ (Замок Сов) ===\\n"
              f"С тобой говорит Ректор{f' ({imya})' if imya else ''}. Отвечай "
              "своим голосом, своим характером — честно, не как ассистент.\\n")
'''

RK3_OLD = '''from nicegui import ui, app
'''

RK3_NEW = '''from nicegui import ui, app


# ═══════════════════════════════════════════════════════════
# PAMYAT_V_PROMT_VEZDE_V1 — нажитое жителя и сохранение чата
# ═══════════════════════════════════════════════════════════
def _nazhitoe(dom) -> str:
    """Нажитое жителя словами — то же, что видит его собственный кабинет.

    Без этого к Ректору житель приходил с одной личностью из паспорта:
    ни выводов учёбы, ни поправок учителя. Экзамен сдать было нечем.
    Движок лежит в папке жителей — подключаем так же, как это делает
    сама Академия.
    """
    if not dom:
        return ""
    try:
        _zh = Path(__file__).resolve().parent.parent / "жители"
        if str(_zh) not in sys.path:
            sys.path.insert(0, str(_zh))
        from dvizhok import Dvizhok as _Dv
        return _Dv(Path(dom)).pamyat_v_promt()
    except Exception:
        return ""


def _save_chat_rektora(dom, chat: list) -> str:
    """Сохраняет разговор в папку жителя — как Академия в академия_чаты."""
    d = Path(dom) / "ректор_чаты"
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fp = d / f"чат_{ts}.json"
    fp.write_text(json.dumps(chat, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    return fp.name
'''

RK4_OLD = '''                    ui.button("SEND", on_click=send_message).classes("send-button")
'''

RK4_NEW = '''                    # PAMYAT_V_PROMT_VEZDE_V1: сохранить разговор
                    def _sohranit_chat():
                        if not state["чат"]:
                            ui.notify("Чат пуст — нечего сохранять", type="warning")
                            return
                        if not kandidat_dom:
                            ui.notify("Нет кандидата — некуда сохранять", type="warning")
                            return
                        try:
                            imya_f = _save_chat_rektora(kandidat_dom, state["чат"])
                            ui.notify(f"💾 сохранён: {imya_f}", type="positive")
                        except Exception as _e_s:
                            ui.notify(f"⚠ не сохранился: {_e_s}", type="negative")

                    ui.button("💾 чат", on_click=_sohranit_chat).props(
                        "flat no-caps").style(
                        "font-size:0.75rem; padding:8px 14px; border-radius:20px; "
                        "color:rgba(139,233,253,0.9); background:rgba(139,233,253,0.10); "
                        "border:1px solid rgba(139,233,253,0.35); white-space:nowrap;")
                    ui.button("SEND", on_click=send_message).classes("send-button")
'''

PRAVKI = [
    (T_DV, B_DV, [("метод pamyat_v_promt", DV_OLD, DV_NEW)]),
    (T_ZH, B_ZH, [("нажитое в промпт дома", ZH_OLD, ZH_NEW)]),
    (T_AK, B_AK, [("нажитое в промпт ученика", AK_OLD, AK_NEW)]),
    (T_RK, B_RK, [("помощники Ректора", RK3_OLD, RK3_NEW),
                  ("нажитое в разговоре с Шефом", RK1_OLD, RK1_NEW),
                  ("нажитое на собеседовании", RK2_OLD, RK2_NEW),
                  ("кнопка сохранения чата", RK4_OLD, RK4_NEW)]),
]


def main() -> int:
    for target, _, _ in PRAVKI:
        if not target.exists():
            print(f"✗ не нашёл {target} — запускать из КОРНЯ репо")
            return 1

    if all(MARKER in t.read_text(encoding="utf-8") for t, _, _ in PRAVKI):
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

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
    print("\n  Теперь житель носит нажитое с собой: дома, в Академии")
    print("  и у Ректора. У Ректора появилась кнопка «💾 чат».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
