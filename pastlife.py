# -*- coding: utf-8 -*-
"""
pastlife.py — past-life incarnation scanner (dragon chart method).

Method: the draconic Pluto degree (natal Pluto shifted by the North Node,
i.e. the "dragon chart" Pluto) is the karmic marker. Times in the past
when transiting Pluto occupied that same zodiacal degree are taken as
prior incarnation epochs. Pluto's ~248-year cycle gives up to ~8 passages
per 2000 years; retrograde loops within one passage are grouped together.

A Pluto passage alone is only a CANDIDATE: many epochs have Pluto at
that degree with no other tie to the natal chart. Each candidate is
therefore scored by RESONANCE — cross-aspects between the historical
chart and the natal chart (karmic weight on Sun/Moon/Nodes), plus a
geographic bonus when the historical Sun-IC meridian falls close to
the NATAL Sun-IC astrocartography line. High-scoring passages are the
probable incarnations; low scores are Pluto coincidences.

For each epoch the Sun-IC meridian is computed: the geographic
longitude where the Sun was exactly on the IC (4th house — roots,
homeland). Uses the Moshier ephemeris (no ephemeris file limits).
"""

import swisseph as swe

SIGNS_KA = ["ვერძი", "კურო", "ტყუპები", "კირჩხიბი", "ლომი", "ქალწული",
            "სასწორი", "მორიელი", "მშვილდოსანი", "თხის რქა",
            "მერწყული", "თევზები"]
MONTHS_KA = ["იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი",
             "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი",
             "ნოემბერი", "დეკემბერი"]

GREGORIAN_START_JD = 2299160.5     # 1582-10-15

# ---- resonance scoring configuration ----
RES_BODIES = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
              "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
              "saturn": swe.SATURN, "uranus": swe.URANUS,
              "neptune": swe.NEPTUNE, "pluto": swe.PLUTO,
              "node": swe.MEAN_NODE, "lilith": swe.MEAN_APOG}
RES_KA = {"sun": "მზე", "moon": "მთვარე", "mercury": "მერკური",
          "venus": "ვენერა", "mars": "მარსი", "jupiter": "იუპიტერი",
          "saturn": "სატურნი", "uranus": "ურანი", "neptune": "ნეპტუნი",
          "pluto": "პლუტონი", "node": "კვანძი", "snode": "სამხ. კვანძი",
          "lilith": "ლილიტი"}
# karmic planet weights
RES_W = {"sun": 1.0, "moon": 1.0, "node": 1.2, "snode": 1.2,
         "pluto": 0.8, "saturn": 0.8, "lilith": 0.7}
RES_W_DEFAULT = 0.6
# aspect: angle -> (max orb, quality, symbol)
RES_ASP = {0.0: (3.0, 1.0, "☌"), 180.0: (2.5, 0.6, "☍"),
           120.0: (2.0, 0.45, "△"), 90.0: (2.0, 0.4, "□")}
GEO_ORB = 15.0        # meridian closeness bonus range (degrees)
GEO_BONUS = 1.5
STRONG_SCORE = 3.0    # probable incarnation
MID_SCORE = 1.8


def _norm(d):
    d %= 360.0
    return d + 360.0 if d < 0 else d


def _norm180(d):
    d = _norm(d)
    return d - 360.0 if d > 180.0 else d


def _sdiff(a, b):
    """signed shortest angular difference a-b in (-180, 180]"""
    d = (a - b) % 360.0
    return d - 360.0 if d > 180.0 else d


def _pluto(jd):
    return swe.calc_ut(jd, swe.PLUTO, swe.FLG_MOSEPH)[0][0]


def _date_of(jd):
    cal = swe.GREG_CAL if jd >= GREGORIAN_START_JD else swe.JUL_CAL
    y, m, d, _ = swe.revjul(jd, cal)
    return {"year": y, "month": m, "day": d,
            "label": f"{d} {MONTHS_KA[m - 1]}, {y}",
            "julian_cal": jd < GREGORIAN_START_JD}


def _chart(jd):
    ch = {}
    for k, pid in RES_BODIES.items():
        ch[k] = swe.calc_ut(jd, pid, swe.FLG_MOSEPH)[0][0]
    ch["snode"] = _norm(ch["node"] + 180.0)
    return ch


def _resonance(hist, natal):
    """cross-aspects historical chart -> natal chart, karmic-weighted."""
    conns, score = [], 0.0
    for hk, hlon in hist.items():
        for nk, nlon in natal.items():
            if hk == "snode" and nk == "node":
                continue                      # mirror duplicates
            if hk == "node" and nk == "snode":
                continue
            d = abs(_sdiff(hlon, nlon))
            nodal = hk in ("node", "snode") or nk in ("node", "snode")
            for ang, (orb, q, sym) in RES_ASP.items():
                if nodal and ang != 0.0:
                    continue        # nodal axis: conjunctions only
                                    # (opp node = conj snode; avoids doubles)
                diff = abs(d - ang)
                if diff <= orb:
                    w = (RES_W.get(hk, RES_W_DEFAULT)
                         + RES_W.get(nk, RES_W_DEFAULT)) / 2.0
                    v = w * q * (1.0 - diff / orb)
                    score += v
                    conns.append({"h": hk, "n": nk,
                                  "h_ka": RES_KA[hk], "n_ka": RES_KA[nk],
                                  "aspect": sym, "orb": round(diff, 2),
                                  "v": round(v, 2)})
                    break
    conns.sort(key=lambda c: -c["v"])
    return score, conns


GEO_KA = {"sun": "მზე", "moon": "მთვარე", "mercury": "მერკური",
          "venus": "ვენერა", "mars": "მარსი", "jupiter": "იუპიტერი",
          "saturn": "სატურნი", "uranus": "ურანი", "neptune": "ნეპტუნი",
          "pluto": "პლუტონი", "lilith": "ლილიტი"}


def _chart_payload(jd, hist, lat, lon):
    """Historical chart in the same shape /chart returns, so the frontend
    wheel renders it directly (Moshier — works for any epoch)."""
    def disp(deg):
        d = int(deg % 30)
        return d, round((deg % 30 - d) * 60 / 60 * 100)
    planets = {}
    for k, ka in GEO_KA.items():
        deg = hist[k]
        xx = swe.calc_ut(jd, RES_BODIES[k], swe.FLG_MOSEPH)[0]
        dv, c = disp(deg)
        planets[ka] = {"degree": round(deg, 4),
                       "sign": SIGNS_KA[int(_norm(deg) // 30)],
                       "sign_degree": dv, "centesimal": c,
                       "retrograde": len(xx) > 3 and xx[3] < 0}
    for ka, deg in (("ჩრდ. კვანძი", hist["node"]),
                    ("სამხ. კვანძი", hist["snode"])):
        dv, c = disp(deg)
        planets[ka] = {"degree": round(deg, 4),
                       "sign": SIGNS_KA[int(_norm(deg) // 30)],
                       "sign_degree": dv, "centesimal": c,
                       "retrograde": True}
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_MOSEPH)
    return {"planets": planets, "houses": [round(c, 4) for c in cusps[:12]],
            "asc": round(ascmc[0], 4), "mc": round(ascmc[1], 4)}


def compute_pastlife(jd_birth, count=4, span_years=2000, step_days=30.0,
                     lat=0.0, lon=0.0):
    """Returns up to `count` most recent incarnation passages within
    span_years before birth, resonance-scored against the natal chart."""
    # ---- natal chart + draconic Pluto target ---------------------------
    natal = _chart(jd_birth)
    pl, nn = natal["pluto"], natal["node"]
    target = _norm(pl - nn)
    # natal Sun-IC astrocartography meridian (location-independent)
    n_ra = swe.calc_ut(jd_birth, swe.SUN,
                       swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)[0][0]
    n_gst = swe.sidtime(jd_birth) * 15.0
    natal_ic_lon = _norm180(_norm180(n_ra - n_gst) + 180.0)

    # ---- scan for crossings -------------------------------------------
    jd0 = jd_birth - span_years * 365.25
    crossings = []
    prev_jd = jd0
    prev_diff = _sdiff(_pluto(jd0), target)
    jd = jd0 + step_days
    while jd < jd_birth:
        diff = _sdiff(_pluto(jd), target)
        if prev_diff == 0.0:
            crossings.append(prev_jd)
        elif diff == 0.0:
            pass                                # handled next iteration
        elif (prev_diff < 0 < diff or prev_diff > 0 > diff) \
                and abs(diff - prev_diff) < 90.0:
            a, b, fa = prev_jd, jd, prev_diff   # bisect to ~10 seconds:
            for _ in range(48):                  # the Sun-IC meridian
                m = (a + b) / 2.0                # rotates 360°/day, so the
                fm = _sdiff(_pluto(m), target)   # crossing instant matters
                if fm == 0.0 or (b - a) < 1.2e-4:
                    a = b = m
                    break
                if (fa < 0 < fm) or (fa > 0 > fm):
                    b = m
                else:
                    a, fa = m, fm
            crossings.append((a + b) / 2.0)
        prev_jd, prev_diff = jd, diff
        jd += step_days

    # ---- group crossings into passages (retro loops ~ within 4 years) --
    passages = []
    for c in crossings:
        if passages and c - passages[-1][-1] < 1500.0:
            passages[-1].append(c)
        else:
            passages.append([c])

    recent = passages[::-1]                     # ALL passages, newest first

    # ---- per-passage: date, Sun-IC meridian, resonance score -----------
    out = []
    for grp in recent:
        jdp = grp[len(grp) // 2]                # exact middle crossing
        hist = _chart(jdp)
        sun = hist["sun"]
        ra = swe.calc_ut(jdp, swe.SUN,
                         swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)[0][0]
        gst = swe.sidtime(jdp) * 15.0           # GMST in degrees
        mc_lon = _norm180(ra - gst)             # Sun-on-MC meridian
        ic_lon = _norm180(mc_lon + 180.0)       # Sun-on-IC meridian
        score, conns = _resonance(hist, natal)
        geo_d = abs(_sdiff(ic_lon, natal_ic_lon))
        geo_hit = geo_d <= GEO_ORB
        if geo_hit:
            score += GEO_BONUS * (1.0 - geo_d / GEO_ORB)
        si = int(sun // 30)
        out.append({
            "date": _date_of(jdp),
            "jd": round(jdp, 6),
            "years_ago": round((jd_birth - jdp) / 365.25),
            "crossings": len(grp),
            "span_days": int(grp[-1] - grp[0]),
            "sun": {"lon": round(sun, 2), "sign": si + 1,
                    "sign_ka": SIGNS_KA[si], "deg": round(sun % 30.0, 1)},
            "ic_lon": round(ic_lon, 2),
            "mc_lon": round(mc_lon, 2),
            "crossing_dates": [_date_of(c)["label"] for c in grp],
            "chart": _chart_payload(jdp, hist, lat, lon),
            "score": round(score, 2),
            "n_connections": len(conns),
            "connections": conns[:12],
            "geo_match": geo_hit,
            "geo_delta": round(geo_d, 1),
            "grade": "strong" if score >= STRONG_SCORE
                     else ("mid" if score >= MID_SCORE else "weak"),
        })
    # probable incarnations = highest resonance; keep `count` strongest,
    # but return all so the UI can show weak Pluto-coincidences dimmed
    ranked = sorted(range(len(out)), key=lambda i: -out[i]["score"])
    for r_i, idx in enumerate(ranked):
        out[idx]["rank"] = r_i + 1
        out[idx]["probable"] = r_i < count and out[idx]["grade"] != "weak"

    si = int(target // 30)
    return {
        "target": {"lon": round(target, 2), "sign": si + 1,
                   "sign_ka": SIGNS_KA[si], "deg": round(target % 30.0, 1)},
        "span_years": span_years,
        "total_passages": len(passages),
        "natal_ic_lon": round(natal_ic_lon, 2),
        "incarnations": out,
    }
