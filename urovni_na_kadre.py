# -*- coding: utf-8 -*-
# urovni_na_kadre.py — уровни ордеров на кадре + правка старого абзаца.
#
# Кладётся в КОРЕНЬ репозитория, рядом с main.py.
# Запуск из PowerShell, из корня:
#     python urovni_na_kadre.py
#
# ═══ 1. УРОВНИ ОРДЕРОВ НА КАДРЕ ═══
#
# Слово Шефа: «заявка зелёным, стоп красным, старый стоп жёлтым,
# открытый ордер тоже зелёным, только сплошной линией, а остальные
# пунктиром».
#
#     заявка (ждёт пробоя)      — зелёный пунктир
#     вход (позиция открыта)    — зелёная СПЛОШНАЯ
#     стоп                      — красный пунктир
#     старый стоп (до трейлинга) — жёлтый пунктир
#
# Линии через весь кадр, как в терминале; цена подписана у правого
# края. Старый стоп рисуется, только если трейлинг его подвинул —
# чтобы было видно, откуда уехал.
#
# Уровни берутся со стола — там лежат все позиции и заявки с ценами.
# Показываются только по той паре и этажу, чей это кадр.
#
# Если уровень лежит за краем кадра, кадр чуть раздвигается, чтобы
# линия была видна. Стоп обычно в одну свечу от цены — свечи почти не
# сожмутся.
#
# ВАЖНО: трейдер видит тот же кадр. Значит и Синди теперь увидит свою
# заявку и стоп на картинке — не только в столе числами.
#
# ═══ 2. АБЗАЦ В ЗАДАНИИ ═══
#
# Под новым текстом «стоп ведёт код за Зубами» остался старый кусок:
#
#   «Подтянутый стоп снимает тебя ровно на этом откате. Не рынок
#    выбивает — ты сама себя закрываешь за шаг до главного движения.»
#
# Писался, когда стоп двигала ЕЁ РУКА по фракталам — тогда правда.
# Теперь рядом сказано «код подтягивает», и выходит противоречие: в
# одном месте подтяжка убивает, в соседнем код подтягивает. Уточняем:
# вредна была подтяжка по фракталам её рукой.
#
# БЕЗОПАСНО. Правит два файла, готовит оба и пишет, только если сошлись
# оба. Рядом кладёт копии. Запускать можно сколько угодно раз.

import ast
import shutil
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent
MARKER_G = "UROVNI_ORDEROV_V1"
MARKER_P = "<!-- ABZAC_PODTYAZHKA_V1 -->"

G_STAROE = (
    "    except Exception as _e_kod:\n"
    "        print(f'[КАДР] метка не встала: {_e_kod}')\n"
    "\n"
    "    kuda = Path(kuda)\n"
)
G_NOVOE = (
    "    except Exception as _e_kod:\n"
    "        print(f'[КАДР] метка не встала: {_e_kod}')\n"
    "\n"
    "    # UROVNI_ORDEROV_V1: уровни заявок и позиций на кадре. Слово\n"
    "    # Шефа: заявка — зелёный пунктир, вход открытой позиции —\n"
    "    # зелёная сплошная, стоп — красный пунктир, старый стоп (до\n"
    "    # трейлинга) — жёлтый пунктир. Цена у правого края.\n"
    "    try:\n"
    "        from hooks import load_trading_state as _lts_u\n"
    "        _poz = (_lts_u() or {}).get('positions') or []\n"
    "        _sym = str(symbol or '').strip().upper()\n"
    "        _tf = str(timeframe or '').strip().upper()\n"
    "        _linii = []   # (цена, цвет, стиль, подпись)\n"
    "        for _p in _poz:\n"
    "            _ps = str(_p.get('symbol') or '').strip().upper()\n"
    "            _pt = str(_p.get('timeframe') or '').strip().upper()\n"
    "            if _ps and _sym and _ps != _sym:\n"
    "                continue\n"
    "            if _pt and _tf and _pt != _tf:\n"
    "                continue\n"
    "            _st = str(_p.get('status') or '').upper()\n"
    "            _vh = _p.get('entry')\n"
    "            _sp = _p.get('stop')\n"
    "            _s0 = _p.get('stop_initial')\n"
    "            if _st == 'OPEN':\n"
    "                if _vh is not None:\n"
    "                    _linii.append((float(_vh), '#3ddc6b', '-', 'вход'))\n"
    "            elif _st in ('PENDING', 'WATCHING'):\n"
    "                if _vh is not None:\n"
    "                    _linii.append((float(_vh), '#3ddc6b', '--', 'заявка'))\n"
    "            else:\n"
    "                continue\n"
    "            if _sp is not None:\n"
    "                _linii.append((float(_sp), '#ff5c5c', '--', 'стоп'))\n"
    "            if (_s0 is not None and _sp is not None\n"
    "                    and abs(float(_s0) - float(_sp)) > 1e-9):\n"
    "                _linii.append((float(_s0), '#ffd866', '--', 'был стоп'))\n"
    "        if _linii:\n"
    "            _lo, _hi = ax.get_ylim()\n"
    "            _ceny = [c for c, *_ in _linii] + [_lo, _hi]\n"
    "            _nlo, _nhi = min(_ceny), max(_ceny)\n"
    "            _zap = (_nhi - _nlo) * 0.03\n"
    "            if _nlo < _lo or _nhi > _hi:\n"
    "                ax.set_ylim(_nlo - _zap, _nhi + _zap)\n"
    "            # знаков после точки — по величине самой цены\n"
    "            _c0 = abs(_linii[0][0])\n"
    "            _znakov = 5 if _c0 < 20 else (3 if _c0 < 500 else 2)\n"
    "            # линии через весь кадр\n"
    "            for _c, _cv, _ls, _pod in _linii:\n"
    "                ax.axhline(_c, color=_cv, linestyle=_ls,\n"
    "                           linewidth=1.4, alpha=0.95, zorder=15)\n"
    "            # подписи ВНУТРИ кадра у правого края: справа от свечей\n"
    "            # пустое поле сдвига Аллигатора. Снаружи справа стоит\n"
    "            # легенда — там подписи прятались под её рамкой.\n"
    "            # Близкие цены разводим по вертикали, иначе слипаются.\n"
    "            _ylo, _yhi = ax.get_ylim()\n"
    "            _raz = (_yhi - _ylo) or 1.0\n"
    "            _por = sorted(_linii, key=lambda t: t[0])\n"
    "            _pos = []\n"
    "            for _c, _cv, _ls, _pod in _por:\n"
    "                _f = (_c - _ylo) / _raz\n"
    "                if _pos and _f - _pos[-1] < 0.045:\n"
    "                    _f = _pos[-1] + 0.045\n"
    "                _pos.append(_f)\n"
    "                ax.text(0.995, _f, f'{_pod} {_c:.{_znakov}f}',\n"
    "                        transform=ax.transAxes, color=_cv,\n"
    "                        fontsize=10, va='center', ha='right',\n"
    "                        family='monospace', zorder=17,\n"
    "                        bbox=dict(facecolor='#0d1117', alpha=0.85,\n"
    "                                  edgecolor=_cv, linewidth=0.6,\n"
    "                                  boxstyle='round,pad=0.25'))\n"
    "            print(f'[КАДР] уровни на кадре: {len(_linii)}')\n"
    "    except Exception as _e_ur:\n"
    "        print(f'[КАДР] уровни не встали ({_e_ur}) — рисую без них')\n"
    "\n"
    "    kuda = Path(kuda)\n"
)

P_STAROE = (
    "Подтянутый стоп снимает тебя ровно на этом откате. Не рынок\n"
    "выбивает — ты сама себя закрываешь за шаг до главного движения.\n"
    "Так погибли четыре сделки подряд, каждая шла на четыре-семь рисков.\n"
)
P_NOVOE = (
    "Раньше стоп подтягивала ТВОЯ РУКА — за каждый свежий фрактал. И\n"
    "он снимал тебя ровно на этом откате: фрактал своего этажа\n"
    "подтверждается поздно, стоп встаёт вплотную к цене. Так погибли\n"
    "четыре сделки подряд, каждая шла на четыре-семь рисков.\n"
    "\n"
    "Код тянет иначе — за Зубами, плавно и с запасом. Его подтяжка тебя\n"
    "не душит, а бережёт. Потому стоп и отдан ему, а не тебе.\n"
)


def podozhdat():
    try:
        input("\nГотово. Нажми Enter, чтобы закрыть окно.")
    except Exception:
        pass


def nayti(pryamo, imya, primeta=None):
    if pryamo.exists():
        return pryamo
    musor = ("_ARCHIVE", "_OLD", "_АРХИВ", "_УБОРКА", ".bak")
    nash = [p for p in KOREN.rglob(imya)
            if not any(m in str(p) for m in musor)
            and (primeta is None or primeta in str(p))]
    if len(nash) == 1:
        return nash[0]
    if len(nash) > 1:
        print(f"Нашёл несколько {imya}:")
        for n, p in enumerate(nash, 1):
            print(f"  {n}. {p}")
        o = input("Какой правим? номер: ").strip()
        if o.isdigit() and 1 <= int(o) <= len(nash):
            return nash[int(o) - 1]
    return None


def main():
    gr = nayti(KOREN / "Биржа" / "grafik.py", "grafik.py")
    pr = nayti(KOREN / "GRONDHEIM_CITY" / "Биржа" / "цеха" / "торговый_хаос"
               / "слоты" / "A06" / "промпт.md", "промпт.md", "A06")
    if not (gr and pr):
        print("✗ не нашёл grafik.py или промпт A06 — запускай из корня")
        return 1

    tg = gr.read_text(encoding="utf-8")
    tp = pr.read_text(encoding="utf-8")
    ng = np_ = None

    if MARKER_G not in tg:
        if tg.count(G_STAROE) != 1:
            print(f"✗ grafik.py: нашёл {tg.count(G_STAROE)} мест вместо одного.")
            print("  Ничего не тронул ни в одном файле.")
            return 1
        ng = tg.replace(G_STAROE, G_NOVOE, 1)
        try:
            ast.parse(ng)
        except SyntaxError as beda:
            print(f"✗ grafik.py поломался бы (строка {beda.lineno})")
            return 1

    if MARKER_P not in tp:
        if tp.count(P_STAROE) != 1:
            print(f"✗ промпт: абзац нашёл {tp.count(P_STAROE)} раз вместо одного.")
            print("  Ничего не тронул ни в одном файле.")
            return 1
        np_ = tp.replace(P_STAROE, P_NOVOE, 1).rstrip("\n") + "\n" + MARKER_P + "\n"

    if ng is None and np_ is None:
        print("· уже сделано")
        return 0

    for put, novyy in ((gr, ng), (pr, np_)):
        if novyy is None:
            continue
        kopiya = put.with_suffix(put.suffix + ".bak_urovni")
        if not kopiya.exists():
            shutil.copy2(put, kopiya)
            print(f"  (копия старого: {kopiya.name})")
        put.write_text(novyy, encoding="utf-8")

    print("✓ готово:")
    if ng:
        print("    · на кадре уровни: заявка — зелёный пунктир, вход —")
        print("      зелёная сплошная, стоп — красный пунктир, старый стоп")
        print("      — жёлтый пунктир; цена у правого края")
    if np_:
        print("    · абзац про подтяжку поправлен: вредна была подтяжка")
        print("      её рукой по фракталам, а код тянет с запасом")
    print()
    print("Перезапусти Кабинет (main.py). Уровни появятся на кадре, как")
    print("только есть заявка или позиция. В логе — строчка")
    print("[КАДР] уровни на кадре: N")
    return 0


if __name__ == "__main__":
    kod = main()
    podozhdat()
    sys.exit(kod)
