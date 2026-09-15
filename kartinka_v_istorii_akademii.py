# -*- coding: utf-8 -*-
# kartinka_v_istorii_akademii.py — картинка живёт В ИСТОРИИ разговора,
# один раз, там, где её положили — не собирается заново «стол + текущий
# вопрос» на каждый вызов.
#
# Кладётся в КОРЕНЬ репозитория (рядом с папкой Академия/). Запуск из
# PowerShell, из корня:
#   python kartinka_v_istorii_akademii.py
#
# Найдено 15.09 (Шеф + София): «Прочитать» и обычный чат — два разных,
# не разговаривающих друг с другом вызова. История чата несла только
# текст; картинка каждый раз приклеивалась заново, инструкцией
# («на столе N изображений...»), поверх ПОСЛЕДНЕГО вопроса — и от
# этого не помнила, что говорилось до, и не видела то, что Шеф сказал
# перед показом.
#
# Правка меняет саму модель хранения:
#   1. Когда картинка ложится на стол (`handle_ruda`) — в state["чат"]
#      сразу пишется НАСТОЯЩЕЕ сообщение с картинкой (без слов, молча
#      положили), а не только текстовая пометка загрузчика.
#   2. Обычный чат (`_sprosit_uchenika`) больше не собирает "стол"
#      отдельно и не приклеивает его к последнему вопросу — просто
#      проигрывает всю историю как есть, картинка уже там, где легла.
#   3. «Прочитать» для картинки перестаёт быть изолированным вызовом
#      без истории — тот же фиксированный вопрос («ЧТО ВИЖУ / ЧТО ЭТО
#      ВО МНЕ»), но теперь с историей чата впереди; сама картинка не
#      прикладывается заново — она уже в истории с момента, когда её
#      положили.
#
# Текстовое чтение книг/материалов (chtenie_knigi) не тронуто —
# отдельная задача (усвоение в личную память), не живой разговор.
#
# Ничего не удаляет. Кладёт рядом копию ui_akademia.py.bak_kartinka_istoriya.
# Запускать можно сколько угодно раз.

import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
FAYL = KOREN / "Академия" / "ui_akademia.py"

# ── 1. handle_ruda: картинка сразу в историю ────────────────────────

BYLO_1 = (
    '        else:\n'
    '            # PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1: разбор при загрузке убран\n'
    '            # -- жил один ход чата и дублировал то, что уже делает и\n'
    '            # СОХРАНЯЕТ "📖 Прочитать" (личная память активного студента).\n'
    '            # Стол только принимает, как и для текста.\n'
    '            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",\n'
    '                                 "content": f"🖼 Принял «{imya}» — лежит на столе, "\n'
    '                                           f"разберёт тот, кто сядет читать."})\n'
    '            ui.notify(f"🖼 Принято: {imya}", type="info")\n'
)

STALO_1 = (
    '        else:\n'
    '            # PATCH_AKADEMIA_RUDA_BEZ_ANALIZA_V1: разбор при загрузке убран\n'
    '            # -- жил один ход чата и дублировал то, что уже делает и\n'
    '            # СОХРАНЯЕТ "📖 Прочитать" (личная память активного студента).\n'
    '            # Стол только принимает, как и для текста.\n'
    '            state["чат"].append({"role": "assistant", "кто": "ЗАГРУЗЧИК",\n'
    '                                 "content": f"🖼 Принял «{imya}» — лежит на столе."})\n'
    '            # AKADEMIA_KARTINKA_V_ISTORII_V1 (15.09, Шеф+София): сама\n'
    '            # картинка ложится в историю ОДИН раз, здесь, как обычное\n'
    '            # сообщение — молча, без слов. Дальше она едет с историей\n'
    '            # естественно, её не нужно объяснять заново на каждый вызов.\n'
    '            try:\n'
    '                _mime_p = _KARTINKA_MIME_STOL.get(ext, "image/png")\n'
    '                _url_p = (f"data:{_mime_p};base64,"\n'
    '                          f"{base64.b64encode(dest.read_bytes()).decode(\'ascii\')}")\n'
    '                state["чат"].append({"role": "user", "content": [\n'
    '                    {"type": "image_url", "image_url": {"url": _url_p}},\n'
    '                ]})\n'
    '            except Exception as _ie:\n'
    '                print(f"[СТОЛ] картинка не легла в историю ({_ie})")\n'
    '            ui.notify(f"🖼 Принято: {imya}", type="info")\n'
)

# ── 2. _sprosit_uchenika: просто проигрываем историю, без "стола" сбоку ──

BYLO_2 = (
    '        messages = [{"role": "system", "content": promt}]\n'
    '        for m in (istoria or [])[-10:]:\n'
    '            r = "user" if m.get("role") == "user" else "assistant"\n'
    '            messages.append({"role": r, "content": m.get("content", "")})\n'
    '        # AKADEMIA_GLAZA_V_CHATE_V1: к вопросу прикрепляем то, что лежит\n'
    '        # на столе. Раньше чат нёс один текст, и на вопрос «что на\n'
    '        # картинке?» ученик отвечал по имени файла из переписки — то\n'
    '        # есть сочинял. Картинки нет — всё как раньше.\n'
    '        # AKADEMIA_STOL_ETO_ZAGRUZCHIK_V1: стол — список загрузчика этой\n'
    '        # сессии, а не всё, что накопилось в папке руды.\n'
    '        # AKADEMIA_VSE_KARTINKI_STOLA_V1: кладём ВСЕ, чтобы можно было\n'
    '        # сравнивать страницы между собой.\n'
    '        _stol = _kartinka_na_stole(state.get("руда"))\n'
    '        _url_stol = _stol[0][1] if _stol else ""\n'
    '        if _stol:\n'
    '            _skolko = ("На столе перед тобой лежит изображение."\n'
    '                       if len(_stol) == 1 else\n'
    '                       f"На столе перед тобой {len(_stol)} изображени"\n'
    '                       f"{\'я\' if len(_stol) < 5 else \'й\'}, по порядку.")\n'
    '            _content = [{"type": "text", "text": (\n'
    '                f"({_skolko} Если речь о них — смотри на сами изображения, "\n'
    '                f"а не на названия. Не разглядела — так и скажи.)\\n\\n" + vopros)}]\n'
    '            for _fp_i, _url_i in _stol:\n'
    '                _content.append({"type": "image_url",\n'
    '                                 "image_url": {"url": _url_i}})\n'
    '            messages.append({"role": "user", "content": _content})\n'
    '        else:\n'
    '            messages.append({"role": "user", "content": vopros})\n'
)

STALO_2 = (
    '        # AKADEMIA_KARTINKA_V_ISTORII_V1 (15.09, Шеф+София): картинка\n'
    '        # больше не собирается заново из "стола" на каждый вызов — она\n'
    '        # уже сидит в истории тем сообщением, в которое легла, когда её\n'
    '        # положили (handle_ruda). Здесь просто проигрываем историю как\n'
    '        # есть, текст или картинка — без разницы, без повторных\n'
    '        # объяснений "вот что перед тобой".\n'
    '        messages = [{"role": "system", "content": promt}]\n'
    '        for m in (istoria or [])[-20:]:\n'
    '            r = "user" if m.get("role") == "user" else "assistant"\n'
    '            messages.append({"role": r, "content": m.get("content", "")})\n'
    '        messages.append({"role": "user", "content": vopros})\n'
)

# ── 3. Прочитать (картинка): та же история впереди, без своей копии ──

BYLO_3 = (
    '                messages = [{"role": "system", "content": dusha + rol},\n'
    '                           {"role": "user", "content": [\n'
    '                               {"type": "text", "text": vopros},\n'
    '                               {"type": "image_url", "image_url": {"url": url}},\n'
    '                           ]}]\n'
)

STALO_3 = (
    '                # AKADEMIA_KARTINKA_V_ISTORII_V1 (15.09): картинка уже\n'
    '                # лежит в state["чат"] с момента, когда её положили на\n'
    '                # стол — заново прикладывать её здесь не нужно, только\n'
    '                # история впереди и сам вопрос.\n'
    '                messages = [{"role": "system", "content": dusha + rol}]\n'
    '                for _m in (state.get("чат") or [])[-20:]:\n'
    '                    _r = ("user" if _m.get("role") == "user"\n'
    '                          else "assistant")\n'
    '                    messages.append({"role": _r,\n'
    '                                     "content": _m.get("content", "")})\n'
    '                messages.append({"role": "user", "content": vopros})\n'
)


def _pravka(tekst, bylo, stalo, opisanie):
    if stalo in tekst:
        print(f"· уже сделано — {opisanie}")
        return tekst, False
    if bylo not in tekst:
        print(f"✗ не нашёл место — {opisanie}. Скажи Брату, поправим по месту")
        return tekst, False
    print(f"✓ {opisanie}")
    return tekst.replace(bylo, stalo, 1), True


def main() -> int:
    if not FAYL.exists():
        print(f"✗ нет файла {FAYL} — запускать из корня репозитория")
        return 1

    tekst = FAYL.read_text(encoding="utf-8")
    ishodnyy = tekst
    sdelano = 0

    tekst, ok = _pravka(tekst, BYLO_1, STALO_1,
                         "картинка ложится в историю при загрузке")
    sdelano += ok
    tekst, ok = _pravka(tekst, BYLO_2, STALO_2,
                         "обычный чат проигрывает историю без 'стола' сбоку")
    sdelano += ok
    tekst, ok = _pravka(tekst, BYLO_3, STALO_3,
                         "«Прочитать» картинки — с историей впереди")
    sdelano += ok

    if tekst != ishodnyy:
        kopiya = FAYL.with_suffix(FAYL.suffix + ".bak_kartinka_istoriya")
        if not kopiya.exists():
            shutil.copy2(FAYL, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        FAYL.write_text(tekst, encoding="utf-8")

    print()
    print(f"ИТОГ: правок {sdelano} из 3")
    if sdelano:
        print("Перезапусти Кабинет (main.py) — правка кода не подхватится "
              "на лету.")
    return 0 if sdelano == 3 or (sdelano == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
