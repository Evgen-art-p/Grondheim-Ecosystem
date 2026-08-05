# -*- coding: utf-8 -*-
# POPRAVKA_UCHITELYA_V1
"""
ПОПРАВКА УЧИТЕЛЯ СТАНОВИТСЯ ЗНАНИЕМ, А НЕ РЕПЛИКОЙ.

ЧТО БЫЛО СЛОМАНО
    Разговор в Академии ложился ученику в память сырым моментом:
    «Шеф спросил: … Я ответил(а): …», вес 0.5, тонус «ровно». То есть
    твоя поправка и её ошибка лежали РЯДОМ и весили ОДИНАКОВО.
    А поверх этого — механика памяти: вывод твердеет от повторения.
    Значит назавтра всплывала её собственная версия (она её повторяла,
    рассуждая), а поправка тонула в общем шуме разговоров.

    На живом уроке это уже видно: из точного определения фрактала
    Нина потеряла «два предшествующих и два последующих» и осталась
    с «по сравнению с соседями». Поправишь в чате — завтра она этого
    не вспомнит.

ЧТО СТАНОВИТСЯ
    У Шефа появляется способ сказать: «это не реплика, это поправка».
    Сообщение, начинающееся с восклицательного знака, ложится ученику
    СРАЗУ МЕТКОЙ — твёрдым знанием, минуя накопление повторов.

        ! фрактал — центральный бар выше ДВУХ слева и ДВУХ справа

    Восклицательный знак ученику не показывается: он видит обычную
    фразу учителя и отвечает на неё как всегда.

ПОЧЕМУ СРАЗУ МЕТКОЙ, А НЕ ЧЕРЕЗ ТРИ ПОВТОРА
    Тот же закон, что мы уже приняли для Биржи: знание твердеет от
    СУДЬИ, а не от повторения. На Бирже судья — рынок (verdikt_rynka).
    В Академии рынка ещё нет, и судья — учитель. Учитель сказал один
    раз — этого довольно, повторять трижды незачем.

    Ошибка ученика при этом НЕ стирается: она остаётся сырым моментом
    в разговоре, как и была. Просто рядом встаёт метка, которая весит
    больше. Прошлое не переписываем — наращиваем.

ДВА ФАЙЛА
    жители/dvizhok.py      — новый метод popravka_uchitelya()
    Академия/ui_akademia.py — распознаёт «!» и зовёт его

ЗАПУСК из корня репо:
    python patch_popravka_uchitelya.py
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "POPRAVKA_UCHITELYA_V1"

T_DVI = Path("жители") / "dvizhok.py"
B_DVI = Path("жители") / "dvizhok.py.bak_popravka_uchitelya"
T_UI = Path("Академия") / "ui_akademia.py"
B_UI = Path("Академия") / "ui_akademia.py.bak_popravka_uchitelya"

# ═══════════════════════════════════════════════════════════
# DVIZHOK — новый метод
# ═══════════════════════════════════════════════════════════
D_OLD = '''    def zhdut_verdikta(self) -> list:'''

D_NEW = '''    # ═══════════════════════════════════════════════════════
    # POPRAVKA_UCHITELYA_V1 — СЛОВО УЧИТЕЛЯ
    # ═══════════════════════════════════════════════════════

    def popravka_uchitelya(self, tekst: str, pattern: str = "") -> dict:
        """Учитель поправил — ложится СРАЗУ меткой, твёрдым знанием.

        Тот же закон, что и verdikt_rynka: знание твердеет от СУДЬИ, а
        не от числа повторов. На Бирже судья — рынок. В Академии рынка
        ещё нет, и судья — учитель. Сказал один раз, повторять трижды
        незачем.

        Ошибку ученика не трогаем: она остаётся сырым моментом в
        разговоре. Просто рядом встаёт метка, которая весит больше.
        Прошлое не переписываем — наращиваем.

        pattern — необязательный ключ темы («фрактал», «вход»), чтобы
                  поправка по той же теме заменяла прежнюю, а не
                  копилась дублями.
        """
        tekst = (tekst or "").strip()
        if not tekst:
            return {"легло": False, "причина": "пустая поправка"}

        metki = self.metki()
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        pattern = (pattern or "").strip()

        # поправка по той же теме заменяет прежнюю: учитель передумал —
        # держим последнее слово, а прежнее уходит в архив, не пропадая
        if pattern:
            byvshie = [m for m in metki if m.get("паттерн") == pattern]
            for b in byvshie:
                self._archive_zapis(b.get("текст", ""),
                                    "заменено новой поправкой учителя")
            metki = [m for m in metki if m.get("паттерн") != pattern]

        metki.append({
            "текст": tekst,
            "паттерн": pattern,
            "откуда": "учитель",
            "когда": now_iso,
            "раз": 1,
        })
        if len(metki) > self.METKI_CAP:
            for old in metki[:len(metki) - self.METKI_CAP]:
                self._archive_zapis(old.get("текст", ""),
                                    "метка вытеснена (лимит нажитого)")
            del metki[:len(metki) - self.METKI_CAP]
        self._pisat_etazh(self._metki_path(), metki)
        return {"легло": True, "этаж": "метки", "паттерн": pattern}

    def zhdut_verdikta(self) -> list:'''

# ═══════════════════════════════════════════════════════════
# UI — распознаём «!» и снимаем его перед показом
# ═══════════════════════════════════════════════════════════
U1_OLD = '''        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""
'''

U1_NEW = '''        msg = (input_ref["element"].value or "").strip()
        if not msg:
            return
        input_ref["element"].value = ""

        # POPRAVKA_UCHITELYA_V1: сообщение с восклицательного знака —
        # это не реплика, а ПОПРАВКА. Ляжет ученику сразу меткой.
        # Сам знак ученику не показываем: он видит обычную фразу
        # учителя и отвечает на неё как всегда.
        _eto_popravka = msg.startswith("!")
        if _eto_popravka:
            msg = msg[1:].strip()
            if not msg:
                return
'''

U2_OLD = '''                from dvizhok import Dvizhok as _Dvizhok_pm
                _dv_pm = _Dvizhok_pm(m["дом"])
                _vdoh_pm = _dv_pm.vdoh(kontekst="общение", sila=0.5, svezhest=1.0, tonus="ровно")
                _dv_pm.vydoh_stol(
                    fakt=f"[Академия] Шеф спросил: {msg}\\nЯ ответил(а): {_otvet}",
                    vdoh_result=_vdoh_pm)
                _dv_pm.sохранить()
'''

U2_NEW = '''                from dvizhok import Dvizhok as _Dvizhok_pm
                _dv_pm = _Dvizhok_pm(m["дом"])
                _vdoh_pm = _dv_pm.vdoh(kontekst="общение", sila=0.5, svezhest=1.0, tonus="ровно")
                _dv_pm.vydoh_stol(
                    fakt=f"[Академия] Шеф спросил: {msg}\\nЯ ответил(а): {_otvet}",
                    vdoh_result=_vdoh_pm)
                _dv_pm.sохранить()
                # POPRAVKA_UCHITELYA_V1: поправка ложится ОТДЕЛЬНО и
                # сразу меткой — твёрдым знанием. Разговор остаётся
                # сырым моментом рядом, ничего не стирая.
                if _eto_popravka:
                    try:
                        _res_p = _dv_pm.popravka_uchitelya(msg)
                        if _res_p.get("легло"):
                            ui.notify("✎ поправка легла в знание",
                                      type="positive")
                        else:
                            ui.notify(f"⚠ поправка не легла: "
                                      f"{_res_p.get('причина','?')}",
                                      type="warning")
                    except AttributeError:
                        ui.notify("⚠ движок без popravka_uchitelya — "
                                  "накати патч на dvizhok.py",
                                  type="negative")
'''

PRAVKI = [
    (T_DVI, B_DVI, [("метод popravka_uchitelya", D_OLD, D_NEW)]),
    (T_UI, B_UI, [("распознаём знак поправки", U1_OLD, U1_NEW),
                  ("поправка ложится меткой", U2_OLD, U2_NEW)]),
]


def main() -> int:
    for target, _, _ in PRAVKI:
        if not target.exists():
            print(f"✗ не нашёл {target} — запускать из КОРНЯ репо")
            return 1

    if all(MARKER in t.read_text(encoding="utf-8") for t, _, _ in PRAVKI):
        print(f"✓ {MARKER} уже стоит — патч идемпотентен, ничего не делаю")
        return 0

    if "PAMYAT_RYNOK_SUDYA_V1" not in T_DVI.read_text(encoding="utf-8"):
        print("✗ сначала накати patch_pamyat_rynok_sudya.py "
              "(этот патч встаёт рядом с его методами)")
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
    print("\n  Теперь поправка пишется так — с восклицательного знака:")
    print("    ! фрактал: центральный бар выше ДВУХ слева и ДВУХ справа")
    print("  Знак ученику не виден, он ответит как на обычную фразу,")
    print("  но поправка ляжет ему твёрдым знанием, а не репликой.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
