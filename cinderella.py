# -*- coding: utf-8 -*-
"""
cinderella.py — "Cinderella gate" (ცინდერელას კარიბჭე) transit scanner.

Scans N years from birth for harmonious transit links among
Chiron–Venus–Jupiter–Neptune:
  transit Chiron  -> natal Venus / Jupiter / Neptune
  transit Venus / Jupiter / Neptune -> natal Chiron
Aspects: conjunction (0°), trine (120°), inconjunction/quincunx (150°),
optional sextile (60°).

Gate = day where the combined weighted score of simultaneous links
reaches the threshold. If the natal chart is "predisposed" (harmonious
natal aspect between Chiron and Venus/Jupiter/Neptune), the threshold
drops so a single Jupiter/Chiron transit link is enough; transit Venus
alone never opens a gate but amplifies concurrent windows.
"""

import swisseph as swe

BODIES = {"chiron": swe.CHIRON, "venus": swe.VENUS,
          "jupiter": swe.JUPITER, "neptune": swe.NEPTUNE}

BODY_KA = {"chiron": "ქირონი", "venus": "ვენერა",
           "jupiter": "იუპიტერი", "neptune": "ნეპტუნი"}
SIGNS_KA = ["ვერძი", "კურო", "ტყუპები", "კირჩხიბი", "ლომი", "ქალწული",
            "სასწორი", "მორიელი", "მშვილდოსანი", "თხის რქა",
            "მერწყული", "თევზები"]

# transit aspect config: angle -> (weight, symbol)
ASPECTS = {0.0: (1.0, "☌"), 120.0: (0.9, "△"), 150.0: (0.85, "⚻"),
           60.0: (0.6, "⚹")}
# transit orbs per aspect (max allowed deviation)
ASPECT_ORB = {0.0: 3.0, 120.0: 1.5, 150.0: 1.0, 60.0: 1.0}
# weight of the moving body itself (venus = trigger/amplifier only)
BODY_WEIGHT = {"chiron": 1.0, "jupiter": 1.0, "neptune": 1.0, "venus": 0.5}

# natal predisposition: harmonious natal aspect chiron<->venus/jupiter/neptune
NATAL_ORB = {0.0: 6.0, 120.0: 6.0, 150.0: 4.0, 60.0: 4.0}

THRESHOLD_NORMAL = 1.5        # needs >= 2 simultaneous links
THRESHOLD_PREDISPOSED = 0.85  # single jupiter/chiron trine or conj enough

# the six transit->natal link definitions
LINKS = [("chiron", "venus"), ("chiron", "jupiter"), ("chiron", "neptune"),
         ("venus", "chiron"), ("jupiter", "chiron"), ("neptune", "chiron")]


def _sep(a, b):
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def _fmt_pos(lon, retro):
    lon %= 360.0
    si = int(lon // 30)
    return {"lon": round(lon, 2), "sign": si + 1, "sign_ka": SIGNS_KA[si],
            "deg": round(lon % 30.0, 1), "retro": retro}


def _revjul(jd):
    y, m, d, _ = swe.revjul(jd)
    return f"{d:02d}.{m:02d}.{y}"


def compute_cinderella(year, month, day, hour, minute, lat, lon,
                       jd_birth, years=100, use_sextile=True,
                       max_periods=200):
    """jd_birth: precomputed UT julian day of birth (caller handles tz)."""
    # ---- natal positions -------------------------------------------------
    natal, natal_retro = {}, {}
    for k, pid in BODIES.items():
        xx = swe.calc_ut(jd_birth, pid)[0]
        natal[k] = xx[0]
        natal_retro[k] = len(xx) > 3 and xx[3] < 0

    # ---- natal predisposition -------------------------------------------
    natal_aspects = []
    for other in ("venus", "jupiter", "neptune"):
        d = _sep(natal["chiron"], natal[other])
        for ang, (w, sym) in ASPECTS.items():
            if not use_sextile and ang == 60.0:
                continue
            diff = abs(d - ang)
            if diff <= NATAL_ORB[ang]:
                natal_aspects.append({
                    "a": "chiron", "b": other, "a_ka": BODY_KA["chiron"],
                    "b_ka": BODY_KA[other], "aspect": sym,
                    "angle": ang, "orb": round(diff, 2)})
                break
    predisposed = len(natal_aspects) > 0
    threshold = THRESHOLD_PREDISPOSED if predisposed else THRESHOLD_NORMAL

    # ---- daily scan -------------------------------------------------------
    n_days = int(years * 365.25)
    aspects = {a: v for a, v in ASPECTS.items()
               if use_sextile or a != 60.0}

    periods = []
    cur = None                                     # active period accumulator

    for i in range(n_days + 1):
        jd = jd_birth + i
        score = 0.0
        links = []
        tpos, tretro = {}, {}
        for k, pid in BODIES.items():
            xx = swe.calc_ut(jd, pid)[0]
            tpos[k] = xx[0]
            tretro[k] = len(xx) > 3 and xx[3] < 0
        for tb, nb in LINKS:
            d = _sep(tpos[tb], natal[nb])
            for ang, (aw, sym) in aspects.items():
                orb_max = ASPECT_ORB[ang]
                diff = abs(d - ang)
                if diff <= orb_max:
                    w = aw * BODY_WEIGHT[tb] * (1.0 - 0.5 * diff / orb_max)
                    score += w
                    links.append({"t": tb, "n": nb, "aspect": sym,
                                  "angle": ang, "orb": round(diff, 2)})
                    break

        if score >= threshold:
            if cur is None:
                cur = {"start": jd, "peak": jd, "peak_score": score,
                       "peak_links": links,
                       "peak_pos": {k: _fmt_pos(tpos[k], tretro[k])
                                    for k in BODIES},
                       "end": jd}
            else:
                cur["end"] = jd
                if score > cur["peak_score"]:
                    cur["peak_score"] = score
                    cur["peak"] = jd
                    cur["peak_links"] = links
                    cur["peak_pos"] = {k: _fmt_pos(tpos[k], tretro[k])
                                       for k in BODIES}
        else:
            if cur is not None:
                periods.append(cur)
                cur = None
    if cur is not None:
        periods.append(cur)

    # ---- format output ----------------------------------------------------
    out = []
    for p in periods[:max_periods]:
        sc = p["peak_score"]
        stars = "★★★" if sc >= 2.5 else ("★★" if sc >= 1.7 else "★")
        out.append({
            "start": _revjul(p["start"]), "end": _revjul(p["end"]),
            "peak": _revjul(p["peak"]),
            "days": int(p["end"] - p["start"]) + 1,
            "age": round((p["peak"] - jd_birth) / 365.25, 1),
            "score": round(sc, 2), "stars": stars,
            "links": [{**l, "t_ka": BODY_KA[l["t"]], "n_ka": BODY_KA[l["n"]]}
                      for l in p["peak_links"]],
            "transit_chart": p["peak_pos"],
        })

    return {
        "natal": {k: _fmt_pos(natal[k], natal_retro[k]) for k in BODIES},
        "natal_aspects": natal_aspects,
        "predisposed": predisposed,
        "threshold": threshold,
        "years_scanned": years,
        "periods": out,
        "total_periods": len(periods),
    }
