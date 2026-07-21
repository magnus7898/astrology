# -*- coding: utf-8 -*-
"""
esoteric_numerology.py  —  MAGNUS calculation cores (5 methods)

Pure functions, no deps. Interpretation strings are kept OUT of the math:
each method returns raw structured results + the objective "keys" (star number,
arrow id, ruling planet, compound number...). Wire your own Georgian
interpretation tables to those keys in the DB layer.

Methods
  1. Nine Star Ki (Kyusei)     -> nine_star_ki()
  2. Arrows of Pythagoras      -> pythagoras_arrows()
  3. Ank Jyotish (Vedic)       -> ank_jyotish()
  4. Gematria / Abjad / Isopsephy -> gematria()
  5. Chaldean name numerology  -> chaldean_name()

All dates as datetime.date.
"""

from datetime import date
import unicodedata

# ─────────────────────────────────────────────────────────────────────────────
# shared
# ─────────────────────────────────────────────────────────────────────────────

def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))

def reduce_num(n: int, keep_master=False, masters=(11, 22, 33)) -> int:
    """Repeated digit-sum to 1..9. keep_master stops on 11/22/33."""
    n = abs(int(n))
    while n > 9:
        if keep_master and n in masters:
            return n
        n = digit_sum(n)
    return n


# ─────────────────────────────────────────────────────────────────────────────
# 1) NINE STAR KI  (九星気学)
# ─────────────────────────────────────────────────────────────────────────────
# Solar year begins at risshun (~Feb 4). Births before it belong to prev year.
# Month star uses solar-term boundaries (~4th–8th). Defaults below are the
# conventional approximations; for exactness feed true solar longitude from
# your swisseph layer and override MONTH_BOUNDARIES.

STAR_META = {
    1: {"element": "წყალი",   "element_en": "Water",  "trigram": "☵ Kan",  "color": "White"},
    2: {"element": "მიწა",    "element_en": "Earth",  "trigram": "☷ Kon",  "color": "Black"},
    3: {"element": "ხე",      "element_en": "Wood",   "trigram": "☳ Shin", "color": "Jade"},
    4: {"element": "ხე",      "element_en": "Wood",   "trigram": "☴ Son",  "color": "Green"},
    5: {"element": "მიწა",    "element_en": "Earth",  "trigram": "—",      "color": "Yellow"},
    6: {"element": "ლითონი",  "element_en": "Metal",  "trigram": "☰ Ken",  "color": "White"},
    7: {"element": "ლითონი",  "element_en": "Metal",  "trigram": "☱ Da",   "color": "Red"},
    8: {"element": "მიწა",    "element_en": "Earth",  "trigram": "☶ Gon",  "color": "White"},
    9: {"element": "ცეცხლი",  "element_en": "Fire",   "trigram": "☲ Ri",   "color": "Purple"},
}

# (month_index 1..12 starting at Feb) -> month star, keyed by year-star group
_MONTH_STAR = {
    "147": [8, 7, 6, 5, 4, 3, 2, 1, 9, 8, 7, 6],
    "258": [2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 9],
    "369": [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3],
}

# (month, day) on/after which the solar month flips. Index 0 => Feb block.
MONTH_BOUNDARIES = [
    (2, 4), (3, 6), (4, 5), (5, 6), (6, 6), (7, 7),
    (8, 8), (9, 8), (10, 8), (11, 7), (12, 7), (1, 6),
]

def _solar_month_index(d: date) -> int:
    """0..11 where 0 = Feb solar block ... 11 = Jan block."""
    for i, (m, day) in enumerate(MONTH_BOUNDARIES):
        # find the boundary this date falls into by walking backwards
        pass
    # simpler: build the 12 flip-points for the relevant year window and locate
    year = d.year
    points = []
    for i, (m, day) in enumerate(MONTH_BOUNDARIES):
        y = year if m != 1 else year + 1   # Jan block belongs to the next cal year
        # Feb..Dec of `year`, then Jan of year+1
        points.append((date(y, m, day), i))
    # a date before Feb-4 of its own year belongs to Jan block of prev cycle
    if d < date(year, 2, 4):
        return 11
    idx = 0
    for pt, i in points:
        if d >= pt:
            idx = i
    return idx

def _year_star(solar_year: int) -> int:
    s = reduce_num(digit_sum(solar_year))
    star = 11 - s
    if star == 10:
        star = 1
    if star == 11:  # s==0 guard (won't happen for 4-digit years)
        star = 2
    return star

def nine_star_ki(d: date, include_day_star=False) -> dict:
    # risshun shift: Jan 1 .. ~Feb 3 -> previous solar year
    solar_year = d.year - 1 if d < date(d.year, 2, 4) else d.year
    y = _year_star(solar_year)

    group = "147" if y in (1, 4, 7) else "258" if y in (2, 5, 8) else "369"
    mi = _solar_month_index(d)
    m = _MONTH_STAR[group][mi]

    out = {
        "year_star": {"n": y, **STAR_META[y]},
        "month_star": {"n": m, **STAR_META[m]},
        "solar_year_used": solar_year,
        "solar_month_index": mi,  # 0=Feb ... 11=Jan
    }
    if include_day_star:
        # day star is school-dependent; expose the raw ordinal for your table
        out["day_ordinal"] = d.toordinal()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 2) ARROWS OF PYTHAGORAS  (psychomatrix lines)
# ─────────────────────────────────────────────────────────────────────────────
# Grid:   3 6 9
#         2 5 8
#         1 4 7
# 8 lines. A line fully present = strength arrow; fully absent = lesson arrow.
# Objective part = which lines are full/empty. Names are your interpretation
# table (David Phillips / Simpson etc.) keyed by the tuple id.

ARROW_LINES = {
    (3, 6, 9): {"axis": "row_top",    "theme_en": "Intellect / Mind"},
    (2, 5, 8): {"axis": "row_mid",    "theme_en": "Emotion / Balance"},
    (1, 4, 7): {"axis": "row_bottom", "theme_en": "Practical / Physical"},
    (1, 2, 3): {"axis": "col_left",   "theme_en": "Planner / Thought"},
    (4, 5, 6): {"axis": "col_mid",    "theme_en": "Will / Determination"},
    (7, 8, 9): {"axis": "col_right",  "theme_en": "Action / Activity"},
    (1, 5, 9): {"axis": "diag_up",    "theme_en": "Determination"},
    (3, 5, 7): {"axis": "diag_down",  "theme_en": "Spirituality / Compassion"},
}

def digit_counts(d: date, extra_working_numbers=None) -> dict:
    """Count digits 1..9 across the birth date. Zeros are ignored (grid has no 0).
    extra_working_numbers: optional list of ints (e.g. life-path chain) to fold in."""
    counts = {k: 0 for k in range(1, 10)}
    blob = f"{d.day:02d}{d.month:02d}{d.year:04d}"
    for ch in blob:
        n = int(ch)
        if n:
            counts[n] += 1
    for wn in (extra_working_numbers or []):
        for ch in str(abs(int(wn))):
            n = int(ch)
            if n:
                counts[n] += 1
    return counts

def pythagoras_arrows(d: date, extra_working_numbers=None) -> dict:
    counts = digit_counts(d, extra_working_numbers)
    strengths, lessons = [], []
    for line, meta in ARROW_LINES.items():
        present = all(counts[n] > 0 for n in line)
        absent = all(counts[n] == 0 for n in line)
        rec = {"line": line, **meta}
        if present:
            strengths.append(rec)
        elif absent:
            lessons.append(rec)
    return {"counts": counts, "strength_arrows": strengths, "lesson_arrows": lessons}


# ─────────────────────────────────────────────────────────────────────────────
# 3) ANK JYOTISH  (Vedic planetary numerology)
# ─────────────────────────────────────────────────────────────────────────────
# Moolank  = reduced day of birth (psychic).
# Bhagyank = reduced full DOB (destiny).
# Each digit 1..9 rules a graha; compatibility via naisargika (natural) maitri.

NUM_TO_GRAHA = {
    1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
    6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars",
}
GRAHA_KA = {
    "Sun": "მზე", "Moon": "მთვარე", "Jupiter": "იუპიტერი", "Rahu": "რაჰუ",
    "Mercury": "მერკური", "Venus": "ვენერა", "Ketu": "კეტუ",
    "Saturn": "სატურნი", "Mars": "მარსი",
}

# Parashari natural relationships. Nodes: Rahu ~ Saturn, Ketu ~ Mars.
_FRIENDS = {
    "Sun":     {"Moon", "Mars", "Jupiter"},
    "Moon":    {"Sun", "Mercury"},
    "Mars":    {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus":   {"Mercury", "Saturn"},
    "Saturn":  {"Mercury", "Venus"},
}
_ENEMIES = {
    "Sun":     {"Venus", "Saturn"},
    "Moon":    set(),
    "Mars":    {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus":   {"Sun", "Moon"},
    "Saturn":  {"Sun", "Moon", "Mars"},
}
def _resolve_node(g):  # map nodes onto their proxy for maitri lookup
    return {"Rahu": "Saturn", "Ketu": "Mars"}.get(g, g)

def graha_relation(a: str, b: str) -> str:
    a, b = _resolve_node(a), _resolve_node(b)
    if a == b:
        return "same"
    if b in _FRIENDS.get(a, set()):
        return "friend"
    if b in _ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"

_LETTER_PLANET = {  # Chaldean-style values reused for Naamank, mapped to graha
    1: "AIJQY", 2: "BKR", 3: "CGLS", 4: "DMT",
    5: "EHNX", 6: "UVW", 7: "OZ", 8: "FP",
}
def _naamank_value(name: str) -> int:
    total = 0
    for ch in name.upper():
        for val, letters in _LETTER_PLANET.items():
            if ch in letters:
                total += val
                break
    return total

def ank_jyotish(d: date, name: str = "") -> dict:
    moolank = reduce_num(d.day)
    bhagyank = reduce_num(int(f"{d.day:02d}{d.month:02d}{d.year:04d}"))
    out = {
        "moolank": {"n": moolank, "graha": NUM_TO_GRAHA[moolank],
                    "graha_ka": GRAHA_KA[NUM_TO_GRAHA[moolank]]},
        "bhagyank": {"n": bhagyank, "graha": NUM_TO_GRAHA[bhagyank],
                     "graha_ka": GRAHA_KA[NUM_TO_GRAHA[bhagyank]]},
        "moolank_bhagyank_relation":
            graha_relation(NUM_TO_GRAHA[moolank], NUM_TO_GRAHA[bhagyank]),
    }
    if name.strip():
        raw = _naamank_value(name)
        naamank = reduce_num(raw)
        out["naamank"] = {"n": naamank, "raw": raw, "graha": NUM_TO_GRAHA[naamank],
                          "graha_ka": GRAHA_KA[NUM_TO_GRAHA[naamank]]}
        out["name_vs_birth_relation"] = graha_relation(
            NUM_TO_GRAHA[naamank], NUM_TO_GRAHA[moolank])
    return out

def ank_compatibility(d1: date, d2: date) -> dict:
    """Two-chart harmony via ruling grahas of the moolanks + bhagyanks."""
    m1, m2 = reduce_num(d1.day), reduce_num(d2.day)
    b1 = reduce_num(int(f"{d1.day:02d}{d1.month:02d}{d1.year:04d}"))
    b2 = reduce_num(int(f"{d2.day:02d}{d2.month:02d}{d2.year:04d}"))
    score_map = {"friend": 2, "same": 2, "neutral": 1, "enemy": 0}
    pairs = {
        "moolank": graha_relation(NUM_TO_GRAHA[m1], NUM_TO_GRAHA[m2]),
        "bhagyank": graha_relation(NUM_TO_GRAHA[b1], NUM_TO_GRAHA[b2]),
        "cross": graha_relation(NUM_TO_GRAHA[m1], NUM_TO_GRAHA[b2]),
    }
    score = sum(score_map[v] for v in pairs.values())
    return {"relations": pairs, "score": score, "max": 6}


# ─────────────────────────────────────────────────────────────────────────────
# 4) GEMATRIA / ABJAD / ISOPSEPHY
# ─────────────────────────────────────────────────────────────────────────────
# Same reduction pipeline, different value tables. Non-letters ignored.

HEBREW = {
    'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,
    'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,
    'ק':100,'ר':200,'ש':300,'ת':400,
    # sofit (final) — standard values; enable via use_sofit
    'ך':500,'ם':600,'ן':700,'ף':800,'ץ':900,
}
HEBREW_SOFIT_TO_BASE = {'ך':20,'ם':40,'ן':50,'ף':80,'ץ':90}

GREEK = {
    'α':1,'β':2,'γ':3,'δ':4,'ε':5,'ϝ':6,'ζ':7,'η':8,'θ':9,
    'ι':10,'κ':20,'λ':30,'μ':40,'ν':50,'ξ':60,'ο':70,'π':80,'ϙ':90,
    'ρ':100,'σ':200,'ς':200,'τ':300,'υ':400,'φ':500,'χ':600,'ψ':700,
    'ω':800,'ϡ':900,
}

ARABIC_ABJAD = {  # mashriqi order
    'ا':1,'ب':2,'ج':3,'د':4,'ه':5,'و':6,'ز':7,'ح':8,'ط':9,
    'ي':10,'ك':20,'ل':30,'م':40,'ن':50,'س':60,'ع':70,'ف':80,'ص':90,
    'ق':100,'ر':200,'ش':300,'ت':400,'ث':500,'خ':600,'ذ':700,'ض':800,
    'ظ':900,'غ':1000,
    'أ':1,'إ':1,'آ':1,'ء':1,'ة':5,'ى':10,  # variants
}

def gematria(text: str, system: str = "hebrew", use_sofit=True) -> dict:
    text = unicodedata.normalize("NFC", text)
    if system == "hebrew":
        table = dict(HEBREW)
        if not use_sofit:
            table.update(HEBREW_SOFIT_TO_BASE)
    elif system == "greek":
        table = GREEK
    elif system in ("arabic", "abjad"):
        table = ARABIC_ABJAD
    else:
        raise ValueError("system must be hebrew | greek | arabic")
    total = sum(table.get(ch, 0) for ch in text)
    return {
        "system": system,
        "value": total,
        "reduced": reduce_num(total) if total else 0,
        "digit_root_9": (total % 9) or (9 if total else 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5) CHALDEAN  name numerology
# ─────────────────────────────────────────────────────────────────────────────
# Values 1..8 for letters (9 is "sacred", never assigned to a letter but can
# appear as a total). Keeps the COMPOUND number (its interpretation matters)
# alongside the single reduced digit.

CHALDEAN = {}
for _v, _letters in {1:"AIJQY",2:"BKR",3:"CGLS",4:"DMT",
                     5:"EHNX",6:"UVW",7:"OZ",8:"FP"}.items():
    for _l in _letters:
        CHALDEAN[_l] = _v

def chaldean_name(name: str) -> dict:
    total = sum(CHALDEAN.get(ch, 0) for ch in name.upper() if ch.isalpha())
    return {
        "compound": total,          # interpret this (10..52 have distinct meanings)
        "single": reduce_num(total) if total else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# self-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    d = date(1988, 3, 23)
    print("== Nine Star Ki ==");   print(nine_star_ki(d))
    print("== Arrows ==");         print(pythagoras_arrows(d))
    print("== Ank Jyotish ==");    print(ank_jyotish(d, "Alex"))
    print("== Compatibility ==");  print(ank_compatibility(d, date(1990, 7, 11)))
    print("== Gematria HE ==");    print(gematria("שלום", "hebrew"))
    print("== Gematria GR ==");    print(gematria("λογος", "greek"))
    print("== Abjad ==");          print(gematria("محمد", "arabic"))
    print("== Chaldean ==");       print(chaldean_name("Alex"))
