# -*- coding: utf-8 -*-
"""
negative.py — hard-transit periods scanner (რთული პერიოდები).

Scans N years from birth for windows when MANY hard transit aspects
(conjunction / square / opposition) from the slow malefics — Saturn,
Pluto, Uranus, Neptune, with Mars as a fast trigger — simultaneously
hit the natal planets and angles. A day belongs to a negative period
when the weighted sum of active hard links reaches the threshold
(single hits don't qualify — "many" is the point).
"""

import swisseph as swe

TRANSIT_BODIES = {"saturn": swe.SATURN, "pluto": swe.PLUTO,
                  "uranus": swe.URANUS, "neptune": swe.NEPTUNE,
                  "mars": swe.MARS}
TRANSIT_W = {"saturn": 1.0, "pluto": 1.0, "uranus": 0.9,
             "neptune": 0.8, "mars": 0.4}

NATAL_BODIES = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
                "venus": swe.VENUS, "mars": swe.MARS,
                "jupiter": swe.JUPITER, "saturn": swe.SATURN,
                "uranus": swe.URANUS, "neptune": swe.NEPTUNE,
                "pluto": swe.PLUTO, "node": swe.MEAN_NODE}
NATAL_W = {"sun": 1.0, "moon": 1.0, "mercury": 0.7, "venus": 0.8,
           "mars": 0.8, "jupiter": 0.5, "saturn": 0.7, "uranus": 0.4,
           "neptune": 0.4, "pluto": 0.4, "node": 0.6,
           "asc": 0.9, "mc": 0.8}

KA = {"sun": "მზე", "moon": "მთვარე", "mercury": "მერკური",
      "venus": "ვენერა", "mars": "მარსი", "jupiter": "იუპიტერი",
      "saturn": "სატურნი", "uranus": "ურანი", "neptune": "ნეპტუნი",
      "pluto": "პლუტონი", "node": "კვანძი", "asc": "ASC", "mc": "MC"}

# hard aspects: angle -> (weight, symbol, max orb)
HARD_ASPECTS = {0.0: (1.0, "☌", 3.0), 90.0: (0.9, "□", 2.0),
                180.0: (0.95, "☍", 2.5)}

THRESHOLD = 2.0
MONTHS_KA = ["იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი",
             "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი",
             "ნოემბერი", "დეკემბერი"]


def _sep(a, b):
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def _label(jd):
    y, m, d, _ = swe.revjul(jd)
    return f"{d:02d}.{m:02d}.{y}"


def compute_negative(jd_birth, lat, lon, years=100, threshold=THRESHOLD,
                     max_periods=400):
    # ---- natal targets (planets + angles) ------------------------------
    natal = {}
    for k, pid in NATAL_BODIES.items():
        natal[k] = swe.calc_ut(jd_birth, pid, swe.FLG_MOSEPH)[0][0]
    try:
        _, ascmc = swe.houses_ex(jd_birth, lat, lon, b'P', swe.FLG_MOSEPH)
        natal["asc"] = float(ascmc[0])
        natal["mc"] = float(ascmc[1])
    except Exception:
        pass

    n_days = int(years * 365.25)
    periods, cur = [], None

    for i in range(n_days + 1):
        jd = jd_birth + i
        score, links = 0.0, []
        tpos = {k: swe.calc_ut(jd, pid, swe.FLG_MOSEPH)[0][0]
                for k, pid in TRANSIT_BODIES.items()}
        for tb, tlon in tpos.items():
            for nb, nlon in natal.items():
                d = _sep(tlon, nlon)
                for ang, (aw, sym, orb) in HARD_ASPECTS.items():
                    diff = abs(d - ang)
                    if diff <= orb:
                        w = (aw * TRANSIT_W[tb] * NATAL_W[nb]
                             * (1.0 - 0.5 * diff / orb))
                        score += w
                        links.append({"t": tb, "n": nb, "aspect": sym,
                                      "orb": round(diff, 2),
                                      "t_ka": KA[tb], "n_ka": KA[nb]})
                        break

        if score >= threshold:
            if cur is None:
                cur = {"start": jd, "end": jd, "peak": jd,
                       "peak_score": score, "peak_links": links}
            else:
                cur["end"] = jd
                if score > cur["peak_score"]:
                    cur.update(peak=jd, peak_score=score, peak_links=links)
        else:
            if cur is not None:
                periods.append(cur)
                cur = None
    if cur is not None:
        periods.append(cur)

    out = []
    for p in periods[:max_periods]:
        sc = p["peak_score"]
        marks = "⚠⚠⚠" if sc >= 3.5 else ("⚠⚠" if sc >= 2.7 else "⚠")
        out.append({
            "start": _label(p["start"]), "end": _label(p["end"]),
            "peak": _label(p["peak"]),
            "days": int(p["end"] - p["start"]) + 1,
            "age": round((p["peak"] - jd_birth) / 365.25, 1),
            "score": round(sc, 2), "marks": marks,
            "links": p["peak_links"],
        })

    return {"years_scanned": years, "threshold": threshold,
            "periods": out, "total_periods": len(periods)}
