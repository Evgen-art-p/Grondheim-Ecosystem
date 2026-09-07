# -*- coding: utf-8 -*-
# KLYUCHI_LATINICEY_V1
"""
ПАТЧ: имена полей у рук едут на провод латиницей, а домой возвращаются
русскими.

ПОЧЕМУ
    Клод сказал дословно:
        tools.0.custom.input_schema.properties:
        Property keys should match pattern '^[a-zA-Z0-9_.-]{1,64}$'
    То есть ИМЕНА ПОЛЕЙ в описании руки («этаж», «с», «по», «о_чём»)
    обязаны быть латиницей. Это общий стандарт, просто снисходительные
    провайдеры его не проверяли, а строгий проверил.

ПОЧЕМУ НЕ ПЕРЕПИСАЛИ САМИ РУКИ
    Город говорит по-русски — это не случайность и не мелочь. Переписав
    ruki_treydera.py на латиницу, мы бы протащили чужой алфавит внутрь
    дома ради требования провода. Здесь чинится ровно то место, где
    провод и начинается: перед отправкой ключи переводятся, на входе
    переводятся обратно. Руки, картины, дневники и все будущие руки
    остаются как есть и НЕ ТРОГАЮТСЯ вовсе.

ЧТО ИМЕННО
    1. Перед отправкой: у каждой руки ключи полей (и список
       обязательных) переводятся в латиницу. Описания полей остаются
       русскими — на них запрета нет, и модель по ним и понимает смысл.
    2. Имя самой руки — тоже (на случай, если где-то в городе заведут
       руку с русским именем; сейчас таких нет, латинские не меняются).
    3. Когда рука вызвана: имя и ключи возвращаются к родным русским
       ДО того, как рука исполнится. Исполнитель получает ровно то, что
       ждал всегда.

    Ничего не выдумывается: перевод — таблица букв, взаимно однозначная
    в пределах одной руки. Столкновения разводятся подчёркиванием.

ЗАПУСК: двойной клик или `python postavit_klyuchi_latinicey.py`.
Идемпотентен. Требует, чтобы уже стоял KLOD_STROGIY_V1 (иначе не
увидишь, что ответит провайдер дальше).
"""
import ast
import py_compile
import shutil
import sys
from pathlib import Path

MARKER = "KLYUCHI_LATINICEY_V1"
BAK = ".bak_klyuchi_latinicey"


# ── найти репо САМ ────────────────────────────────────────────────
def _est_repo(p: Path) -> bool:
    try:
        return (p / "Биржа" / "llm.py").is_file()
    except Exception:
        return False


def nayti_repo():
    tut = Path(__file__).resolve().parent
    spisok = []
    for k in [tut, Path.cwd(), *tut.parents]:
        if _est_repo(k) and k.resolve() not in spisok:
            spisok.append(k.resolve())
    for baza in (tut, tut.parent):
        try:
            for sosed in baza.iterdir():
                if sosed.is_dir() and _est_repo(sosed) and sosed.resolve() not in spisok:
                    spisok.append(sosed.resolve())
        except Exception:
            pass

    if len(spisok) == 1:
        print(f"Нашёл репозиторий: {spisok[0]}")
        if input("Этот? [Enter — да, n — нет]: ").strip().lower() in ("", "y", "д"):
            return spisok[0]
    elif len(spisok) > 1:
        print("Нашёл несколько:")
        for i, p in enumerate(spisok, 1):
            print(f"  {i}) {p}")
        v = input("Какой? [цифра, Enter — первый]: ").strip()
        if not v:
            return spisok[0]
        if v.isdigit() and 1 <= int(v) <= len(spisok):
            return spisok[int(v) - 1]

    print("\nСам не нашёл. Перетащи папку репозитория в это окно и нажми Enter.")
    p = Path(input("Папка: ").strip().strip('"').strip("'")).expanduser()
    if _est_repo(p):
        return p.resolve()
    print(f"✕ По этому пути нет Биржа/llm.py: {p}")
    return None


# ── что вставляем ─────────────────────────────────────────────────
YAKOR_HELPERY = "def stress_to_temperature(stress: float = 0.0, light: float = 0.8) -> float:"

HELPERY = '''# ══ KLYUCHI_LATINICEY_V1 ══════════════════════════════════════════
# Клод (и стандарт вообще) требует, чтобы имена полей в описании руки
# были латиницей: '^[a-zA-Z0-9_.-]{1,64}$'. Город говорит по-русски —
# значит переводим на проводе, а не внутри дома. Туда — латиницей,
# обратно — как было.

_RUS_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_skazali_pro_latinicu = False


def _v_latinicu(s: str) -> str:
    """Русское имя поля → допустимое латинское. Таблица, не выдумка."""
    out = []
    for ch in (s or ""):
        nizh = ch.lower()
        if nizh in _RUS_LAT:
            out.append(_RUS_LAT[nizh])
        elif ch.isascii() and (ch.isalnum() or ch in "_.-"):
            out.append(ch)
        else:
            out.append("_")
    itog = "".join(out).strip("_")
    return (itog or "arg")[:64]


def _uzel_na_latinicu(uzel, karta_poley: dict) -> None:
    """Перевести ключи properties (и вложенные) на месте."""
    if not isinstance(uzel, dict):
        return
    props = uzel.get("properties")
    if isinstance(props, dict):
        novye, staroe_v_novoe = {}, {}
        for k, v in props.items():
            nk = _v_latinicu(k)
            while nk in novye:
                nk = (nk + "_")[:64]
            novye[nk] = v
            staroe_v_novoe[k] = nk
            if nk != k:
                karta_poley[nk] = k
        uzel["properties"] = novye
        treb = uzel.get("required")
        if isinstance(treb, list):
            uzel["required"] = [staroe_v_novoe.get(x, x) for x in treb]
        for v in novye.values():
            if isinstance(v, dict):
                _uzel_na_latinicu(v, karta_poley)
                _uzel_na_latinicu(v.get("items"), karta_poley)


def _shema_na_latinicu(tools_schema):
    """(схема для провода, карта обратного перевода).

    Схема НЕ портится: работаем на глубокой копии. Если всё и так
    латиницей — возвращаем как было, без копирования.
    """
    global _skazali_pro_latinicu
    if not tools_schema:
        return tools_schema, {}

    nado = False
    for t in tools_schema:
        fn = (t or {}).get("function") or {}
        if not str(fn.get("name", "")).isascii():
            nado = True
        par = fn.get("parameters") or {}
        for k in (par.get("properties") or {}):
            if not str(k).isascii():
                nado = True
    if not nado:
        return tools_schema, {}

    import copy
    novaya = copy.deepcopy(tools_schema)
    imena, polya = {}, {}
    skolko = 0
    for t in novaya:
        fn = (t or {}).get("function") or {}
        rodnoe_imya = str(fn.get("name", ""))
        karta_poley = {}
        _uzel_na_latinicu(fn.get("parameters"), karta_poley)
        if karta_poley:
            polya[rodnoe_imya] = karta_poley
            skolko += len(karta_poley)
        if not rodnoe_imya.isascii():
            novoe = _v_latinicu(rodnoe_imya)
            fn["name"] = novoe
            imena[novoe] = rodnoe_imya
            polya[rodnoe_imya] = karta_poley

    if not _skazali_pro_latinicu:
        _skazali_pro_latinicu = True
        print(f"[РУКИ] ключи полей едут на провод латиницей "
              f"({skolko} шт.) — домой вернутся русскими")
    return novaya, {"imena": imena, "polya": polya}


def _ruka_obratno(imya: str, args, karta):
    """Имя руки и ключи — обратно в русские, до исполнения."""
    if not karta:
        return imya, args
    rodnoe = (karta.get("imena") or {}).get(imya, imya)
    perevod = (karta.get("polya") or {}).get(rodnoe) or {}
    if perevod and isinstance(args, dict):
        args = {perevod.get(k, k): v for k, v in args.items()}
    return rodnoe, args


'''

ZAMENY = [
    (
        "перевод схемы · руки",
        """    tool_calls_made = 0""",
        """    # KLYUCHI_LATINICEY_V1
    tools_schema, _karta_ruk = _shema_na_latinicu(tools_schema)

    tool_calls_made = 0""",
        1,
    ),
    (
        "перевод схемы · кадр+руки",
        """    ruki = dict(executors or {})""",
        """    # KLYUCHI_LATINICEY_V1
    tools_schema, _karta_ruk = _shema_na_latinicu(tools_schema)

    ruki = dict(executors or {})""",
        1,
    ),
    (
        "возврат ключей · руки",
        """            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                fn_args = {}""",
        """            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                fn_args = {}
            # KLYUCHI_LATINICEY_V1: домой — русскими
            fn_name, fn_args = _ruka_obratno(fn_name, fn_args, _karta_ruk)""",
        1,
    ),
    (
        "возврат ключей · кадр+руки",
        """            imya = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}""",
        """            imya = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            # KLYUCHI_LATINICEY_V1: домой — русскими
            imya, args = _ruka_obratno(imya, args, _karta_ruk)""",
        1,
    ),
]


def pochinit(put: Path) -> bool:
    tekst = put.read_text(encoding="utf-8")

    if MARKER in tekst:
        print(f"• {put.name}: уже стоит ({MARKER}) — не трогаю.")
        return True
    if "KLOD_STROGIY_V1" not in tekst:
        print("⚠  Не вижу KLOD_STROGIY_V1 — сначала накати его,\n"
              "   иначе следующую жалобу провайдера снова не увидишь.")
        return False

    beda = False
    for imya, staroe, _n, zhdyom in ZAMENY:
        est = tekst.count(staroe)
        if est != zhdyom:
            print(f"✕ якорь «{imya}»: ждал {zhdyom}, нашёл {est}")
            beda = True
    if YAKOR_HELPERY not in tekst:
        print("✕ не нашёл места для вставки помощников")
        beda = True
    if beda:
        print("\nФайл отличается от ожидаемого — НИЧЕГО не менял.")
        return False

    novyy = tekst.replace(YAKOR_HELPERY, HELPERY + YAKOR_HELPERY, 1)
    for imya, staroe, novoe, _z in ZAMENY:
        novyy = novyy.replace(staroe, novoe)
        print(f"  ✓ {imya}")

    try:
        ast.parse(novyy)
    except SyntaxError as e:
        print(f"✕ после правки нерабочий Python: {e}")
        return False

    bak = put.with_suffix(put.suffix + BAK)
    if not bak.exists():
        shutil.copy2(put, bak)
        print(f"  ✓ бэкап: {bak.name}")
    put.write_text(novyy, encoding="utf-8")

    try:
        py_compile.compile(str(put), doraise=True)
        print(f"  ✓ {put.name} компилируется")
    except Exception as e:
        shutil.copy2(bak, put)
        print(f"✕ не компилируется, откатил: {e}")
        return False
    return True


def main():
    print("═══ ПАТЧ: ключи рук латиницей (KLYUCHI_LATINICEY_V1) ═══\n")
    repo = nayti_repo()
    if repo is None:
        return 1
    llm = repo / "Биржа" / "llm.py"
    print(f"\nПравлю: {llm}\n")
    ok = pochinit(llm)
    print("\n" + ("═══ ГОТОВО ═══" if ok else "═══ НЕ ВЫШЛО ═══"))
    if ok:
        print("Перезапусти город на Соннете и спроси трейдера «что на 15-минутке?».\n"
              "В логе должна пройти строка [РУКИ] ключи полей едут…, а потом\n"
              "обычная [РУКА] 🖐 stol_na_etazhe({'этаж': 'M15'}) — уже по-русски.")
    return 0 if ok else 1


if __name__ == "__main__":
    kod = main()
    try:
        input("\nEnter — закрыть окно...")
    except Exception:
        pass
    sys.exit(kod)
