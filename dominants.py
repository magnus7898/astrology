# -*- coding: utf-8 -*-
"""
dominants.py — Walter Pullen (Astrolog) "-j" influence chart algorithm.
Exact port of ComputeInfluence()/ChartInfluence() from Astrolog 7.x
(intrpret.cpp) with the standard-rulership path (esoteric/hierarchical off).

Input: dict of object longitudes (tropical or sidereal, degrees 0-360)
       + list of 12 house cusp longitudes (house 1 first).
Output: per-planet position/aspect/total powers + percentages + ranks,
        and per-sign powers + percentages.
"""

# ---------------------------------------------------------------- tables

OBJ_KEYS = ["sun", "moon", "mercury", "venus", "mars", "jupiter",
            "saturn", "uranus", "neptune", "pluto",
            "chiron", "node", "lilith", "asc", "mc"]

# Base influence of each object (rObjInf)
OBJ_INF = {"sun": 30, "moon": 25, "mercury": 10, "venus": 10, "mars": 10,
           "jupiter": 10, "saturn": 10, "uranus": 10, "neptune": 10,
           "pluto": 10, "chiron": 5, "node": 5, "lilith": 5,
           "asc": 20, "mc": 15}

# House strength hierarchy: angular (ASC>MC>DSC>IC) > succedent > cadent
HOUSE_INF = [20, 5, 2, 8, 5, 2, 10, 5, 2, 15, 5, 2]

# Conjunction-to-angle proximity bonus, linear falloff within ANGLE_ORB
ANGLE_ORB = 10.0
ANGLE_PROX = {"asc": 15.0, "mc": 12.0, "dsc": 8.0, "ic": 6.0}

# Critical degrees: 0° and 29° of any sign
CRITICAL_BONUS = 15.0

# Flat bonus per aspect a planet participates in (aspect-count factor)
ASPECT_COUNT_BONUS = 3.0

# Dignity bonuses (rObjInf[oNorm1+1..2], rHouseInf[cSign+1..2])
BONUS_RULE_SIGN, BONUS_EXALT_SIGN = 20.0, 10.0
BONUS_RULE_HOUSE, BONUS_EXALT_HOUSE = 15.0, 5.0

# Sign (1..12) -> ruling planet(s)  (rules / rules2)
RULES1 = {1: "pluto", 2: "venus", 3: "mercury", 4: "moon", 5: "sun",
          6: "mercury", 7: "venus", 8: "mars", 9: "jupiter",
          10: "saturn", 11: "uranus", 12: "neptune"}
RULES2 = {1: "mars", 8: "pluto", 11: "saturn", 12: "jupiter"}

# Object -> sign(s) it rules (ruler1 / ruler2) and sign of exaltation (exalt)
RULER1 = {"sun": 5, "moon": 4, "mercury": 3, "venus": 7, "mars": 8,
          "jupiter": 9, "saturn": 10, "uranus": 11, "neptune": 12,
          "pluto": 1, "chiron": 9, "node": 11, "lilith": 8,
          "asc": 1, "mc": 10}
RULER2 = {"mercury": 6, "venus": 2, "mars": 1, "jupiter": 12,
          "saturn": 11, "pluto": 8}
EXALT = {"sun": 1, "moon": 2, "mercury": 6, "venus": 12, "mars": 10,
         "jupiter": 4, "saturn": 7, "uranus": 8, "neptune": 4,
         "pluto": 11, "chiron": 12, "node": 3, "lilith": 12,
         "asc": 2, "mc": 10}

# Aspects: (angle, influence rAspInf, max orb rAspOrb) — first 11 of Astrolog
ASPECTS = [
    ("con", 0.0,   1.0, 7.0),
    ("opp", 180.0, 0.8, 7.0),
    ("squ", 90.0,  0.8, 7.0),
    ("tri", 120.0, 0.6, 7.0),
    ("sex", 60.0,  0.6, 6.0),
    ("inc", 150.0, 0.4, 3.0),
    ("ssx", 30.0,  0.4, 3.0),
    ("ssq", 45.0,  0.2, 3.0),
    ("ses", 135.0, 0.2, 3.0),
    ("qui", 72.0,  0.2, 2.0),
    ("bqn", 144.0, 0.2, 2.0),
]

# Per-object orb limits/additions (rObjOrb / rObjAdd)
OBJ_ORB = {"node": 2.0, "lilith": 360.0}          # default 360
OBJ_ADD = {"sun": 1.0, "moon": 1.0}               # default 0

# Retrograde weighting (Astrolog -j itself ignores retrogradation).
# Applied to the base influence of real planets only.
RETRO_FACTOR = 0.9
RETRO_ELIGIBLE = {"mercury", "venus", "mars", "jupiter", "saturn",
                  "uranus", "neptune", "pluto", "chiron"}

SIGNS_KA = ["ვერძი", "კურო", "ტყუპები", "კირჩხიბი", "ლომი", "ქალწული",
            "სასწორი", "მორიელი", "მშვილდოსანი", "თხის რქა",
            "მერწყული", "თევზები"]
OBJ_KA = {"sun": "მზე", "moon": "მთვარე", "mercury": "მერკური",
          "venus": "ვენერა", "mars": "მარსი", "jupiter": "იუპიტერი",
          "saturn": "სატურნი", "uranus": "ურანი", "neptune": "ნეპტუნი",
          "pluto": "პლუტონი", "chiron": "ქირონი",
          "node": "ჩრდილო კვანძი", "lilith": "ლილიტი",
          "asc": "ასცენდენტი", "mc": "MC"}

# ---------------------------------------------------------------- helpers

def _r1(x):
    return int(x * 10 + 0.5) / 10.0

def _norm(d):
    d %= 360.0
    return d + 360.0 if d < 0 else d

def _sign_of(lon):
    return int(_norm(lon) // 30.0) + 1          # 1..12

def _house_of(lon, cusps):
    lon = _norm(lon)
    for h in range(12):
        a, b = _norm(cusps[h]), _norm(cusps[(h + 1) % 12])
        if a <= b:
            if a <= lon < b:
                return h + 1
        else:                                   # wraps 360
            if lon >= a or lon < b:
                return h + 1
    return 12

def _sep(a, b):
    d = abs(_norm(a) - _norm(b))
    return d if d <= 180.0 else 360.0 - d

def _get_orb(o1, o2, asp_orb):
    orb = min(asp_orb, OBJ_ORB.get(o1, 360.0), OBJ_ORB.get(o2, 360.0))
    return orb + OBJ_ADD.get(o1, 0.0) + OBJ_ADD.get(o2, 0.0)

# ---------------------------------------------------------------- core

def compute_dominants(positions, cusps, n_aspects=5, use_minor_objects=True,
                      retro=None, retro_factor=RETRO_FACTOR):
    """
    positions: {objkey: longitude}. Keys from OBJ_KEYS; 'asc'/'mc' optional
               (taken from cusps[0]/cusps[9] if absent).
    cusps:     list of 12 house-cusp longitudes, house 1 first.
    n_aspects: how many aspects from ASPECTS to use (Astrolog default 5).
    retro:     {objkey: bool} retrograde flags; retro planets get their
               base influence scaled by retro_factor (planets only).
    """
    pos = {k: _norm(v) for k, v in positions.items() if k in OBJ_INF
           and v is not None}
    if "asc" not in pos:
        pos["asc"] = _norm(cusps[0])
    if "mc" not in pos:
        pos["mc"] = _norm(cusps[9])
    if not use_minor_objects:
        for k in ("chiron", "node", "lilith"):
            pos.pop(k, None)

    objs = [k for k in OBJ_KEYS if k in pos]
    retro = retro or {}
    is_rx = {o: bool(retro.get(o)) and o in RETRO_ELIGIBLE for o in objs}
    sign = {o: _sign_of(pos[o]) for o in objs}
    house = {o: _house_of(pos[o], cusps) for o in objs}
    # cusp objects live on their own cusps by definition
    if "asc" in house:
        house["asc"] = 1
    if "mc" in house:
        house["mc"] = 10

    p1 = {o: 0.0 for o in objs}                 # position power
    p2 = {o: 0.0 for o in objs}                 # aspect power
    angles = {"asc": _norm(cusps[0]), "mc": _norm(cusps[9]),
              "dsc": _norm(cusps[0] + 180.0), "ic": _norm(cusps[9] + 180.0)}

    # --- 1. placement power -------------------------------------------
    for o in objs:
        s, h = sign[o], house[o]
        p1[o] += OBJ_INF[o]
        p1[o] += HOUSE_INF[h - 1]
        # dignities by sign
        if RULER1.get(o) == s or RULER2.get(o) == s:
            p1[o] += BONUS_RULE_SIGN
        if EXALT.get(o) == s:
            p1[o] += BONUS_EXALT_SIGN
        # dignities by house-as-sign
        if RULER1.get(o) == h or RULER2.get(o) == h:
            p1[o] += BONUS_RULE_HOUSE
        if EXALT.get(o) == h:
            p1[o] += BONUS_EXALT_HOUSE
        # critical degrees: 0° or 29° within the sign
        sd = pos[o] % 30.0
        crit = sd < 1.0 or sd >= 29.0
        if crit:
            p1[o] += CRITICAL_BONUS
        # angular proximity (skip the angle objects themselves)
        if o not in ("asc", "mc"):
            best = 0.0
            for ang, mx in ANGLE_PROX.items():
                d = _sep(pos[o], angles[ang])
                if d <= ANGLE_ORB:
                    best = max(best, mx * (1.0 - d / ANGLE_ORB))
            p1[o] += best
        # dispersal: rulers of the sign & house the object is in get half
        half = OBJ_INF[o] / 2.0
        for target_sign in (s, h):
            for rl in (RULES1.get(target_sign), RULES2.get(target_sign)):
                if rl and rl != o and rl in p1:
                    p1[rl] += half

    # rulers of the sign on each house cusp get that house's influence
    for h in range(1, 13):
        s = _sign_of(cusps[h - 1])
        rl = RULES1.get(s)
        if rl in p1:
            p1[rl] += HOUSE_INF[h - 1]

    # --- 2. aspect power ----------------------------------------------
    asps = ASPECTS[:n_aspects]
    found = []
    asp_count = {o: 0 for o in objs}
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            a, b = objs[i], objs[j]
            d = _sep(pos[a], pos[b])
            best = None
            for name, angle, inf, aorb in asps:
                orb = _get_orb(a, b, aorb)
                diff = abs(d - angle)
                if diff <= orb and (best is None or diff < best[0]):
                    best = (diff, name, inf, orb)
            if best:
                diff, name, inf, orb = best
                frac = 1.0 - diff / orb
                p2[a] += inf * OBJ_INF[b] * frac
                p2[b] += inf * OBJ_INF[a] * frac
                asp_count[a] += 1
                asp_count[b] += 1
                found.append({"a": a, "b": b, "aspect": name,
                              "orb": round(diff, 2)})
    for o in objs:
        p2[o] += ASPECT_COUNT_BONUS * asp_count[o]

    # --- 3. retro scaling, totals, ranks, percentages -----------------
    for o in objs:
        if is_rx[o]:
            p1[o] *= retro_factor
            p2[o] *= retro_factor
    total = sum(p1.values()) + sum(p2.values())
    tot = {o: p1[o] + p2[o] for o in objs}
    order = sorted(objs, key=lambda o: -tot[o])
    rank = {o: i + 1 for i, o in enumerate(order)}

    planets_out = [{
        "key": o, "name_ka": OBJ_KA[o],
        "retrograde": is_rx[o],
        "critical": (pos[o] % 30.0) < 1.0 or (pos[o] % 30.0) >= 29.0,
        "aspect_count": asp_count[o],
        "sign": sign[o], "sign_ka": SIGNS_KA[sign[o] - 1],
        "house": house[o],
        "position_power": _r1(p1[o]),
        "aspect_power": _r1(p2[o]),
        "total": _r1(tot[o]),
        "percent": _r1(tot[o] / total * 100.0) if total else 0.0,
        "rank": rank[o],
    } for o in order]

    # --- 4. sign power (-j0): half of occupant power, third to ruled sign
    sp = {s: 0.0 for s in range(1, 13)}
    for o in objs:
        sp[sign[o]] += tot[o] / 2.0
        r1 = RULER1.get(o)
        if r1:
            sp[r1] += tot[o] / 3.0
        r2 = RULER2.get(o)
        if r2:
            sp[r2] += tot[o] / 3.0
    stotal = sum(sp.values())
    sorder = sorted(sp, key=lambda s: -sp[s])
    signs_out = [{
        "sign": s, "name_ka": SIGNS_KA[s - 1],
        "power": _r1(sp[s]),
        "percent": _r1(sp[s] / stotal * 100.0) if stotal else 0.0,
        "rank": i + 1,
    } for i, s in enumerate(sorder)]

    return {"planets": planets_out, "signs": signs_out,
            "aspects_found": found,
            "dominant_planet": planets_out[0]["key"] if planets_out else None,
            "dominant_sign": signs_out[0]["sign"] if signs_out else None}


# ------------------------------------------------ optional Flask endpoint
# In app.py:
#   from dominants import compute_dominants, dominants_from_birth
#
#   @app.route('/api/dominants', methods=['POST'])
#   def api_dominants():
#       d = request.get_json()
#       return jsonify(dominants_from_birth(
#           d['year'], d['month'], d['day'], d['hour'], d['minute'],
#           d['lat'], d['lon'], d.get('tz_offset', 0.0),
#           sidereal=d.get('sidereal', False)))

def dominants_from_birth(year, month, day, hour, minute, lat, lon,
                         tz_offset=0.0, sidereal=False, hsys=b'P'):
    import swisseph as swe
    ut = hour + minute / 60.0 - tz_offset
    jd = swe.julday(year, month, day, ut)
    flags = swe.FLG_MOSEPH
    if sidereal:
        swe.set_sid_mode(swe.SIDM_LAHIRI)       # adjust to your zodiac
        flags |= swe.FLG_SIDEREAL
    ids = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
           "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
           "saturn": swe.SATURN, "uranus": swe.URANUS,
           "neptune": swe.NEPTUNE, "pluto": swe.PLUTO,
           "chiron": swe.CHIRON, "node": swe.TRUE_NODE,
           "lilith": swe.MEAN_APOG}
    positions, retro = {}, {}
    for k, pid in ids.items():
        try:
            xx = swe.calc_ut(jd, pid, flags)[0]
            positions[k] = xx[0]
            retro[k] = len(xx) > 3 and xx[3] < 0
        except Exception:
            pass                                # e.g. Chiron w/o ephemeris
    if sidereal:
        cusps, _ = swe.houses_ex(jd, lat, lon, hsys, swe.FLG_SIDEREAL)
    else:
        cusps, _ = swe.houses(jd, lat, lon, hsys)
    return compute_dominants(positions, list(cusps[:12]), retro=retro)
