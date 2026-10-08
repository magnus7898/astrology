"""
Human Design transits.

What a transit is in HD:
    Only the CURRENT positions of the 13 bodies (Sun, Earth, both Nodes,
    Moon, Mercury ... Pluto), decomposed into gate.line exactly like the
    personality side of a chart. The 88-degree solar-arc rule belongs to the
    natal DESIGN imprint only; it is applied once, at birth, and never to a
    transit. Earth = Sun + 180, South Node = North Node + 180, as in the natal.

Three things are computed:

  1. status at one moment — every one of the 36 channels classified as
       natal          both gates are yours, transit irrelevant
       completed      you have one gate (hanging), a transit body sits in
                      the other  ->  the channel is open while it stays there
       transit        both gates are held by transit bodies only (collective)
     plus the chart "under the transit": natal gates + transit gates,
     with its centers, type, authority and definition.

  2. ingress table — for every body, every gate it occupies during the
     period (entry, exit, retrograde). Any gate or channel question
     ("when is 20 activated", "when does 10-20 open") is answered from it
     on the page without another request.

  3. the transit sky's own chart (its channels and centers).

Gate boundaries are found by stepping (2 h for the Moon up to 5 days for
Pluto - see STEP) and refining by bisection to under a minute.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Set

import pytz
import swisseph as swe

from hd_calc import (CHANNELS, CENTER_GATES, GATE_TO_CENTER, MOTORS,
                     PLANET_DEFS, calc_planets, decompose, get_definition)

BODY_ORDER = [n for n, _, _ in PLANET_DEFS]
GLYPH = {n: g for n, _, g in PLANET_DEFS}
FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


# ── classification shared by every view (same rules as hd_calc.analyze) ──
def classify(gates: Set[int]) -> Dict:
    chans = [(a, b, n) for a, b, n in CHANNELS if a in gates and b in gates]
    centers: Set[str] = set()
    adj: Dict[str, set] = {c: set() for c in CENTER_GATES}
    for a, b, _ in chans:
        ca, cb = GATE_TO_CENTER[a], GATE_TO_CENTER[b]
        centers |= {ca, cb}
        if ca != cb:
            adj[ca].add(cb)
            adj[cb].add(ca)

    def reach(start):
        seen, st = {start}, [start]
        while st:
            n = st.pop()
            for m in adj[n]:
                if m in centers and m not in seen:
                    seen.add(m)
                    st.append(m)
        return seen

    sacral = "Sacral" in centers
    t2m = "Throat" in centers and any(m in reach("Throat") for m in MOTORS)
    if not centers:
        typ = "Reflector"
    elif sacral and t2m:
        typ = "Manifesting Generator"
    elif sacral:
        typ = "Generator"
    elif t2m:
        typ = "Manifestor"
    else:
        typ = "Projector"

    if "Solar Plexus" in centers:
        auth = "ემოციური (მზის წნული)"
    elif sacral:
        auth = "საკრალური"
    elif "Spleen" in centers:
        auth = "სპლენური (ელენთა)"
    elif "Heart" in centers:
        auth = "ეგო (გული)"
    elif "G" in centers:
        auth = "თვით-პროექცია (G)"
    elif typ == "Reflector":
        auth = "მთვარე"
    else:
        auth = "მენტალური / გარემო"

    return {"channels": [{"gate_a": a, "gate_b": b, "name": n} for a, b, n in chans],
            "centers": sorted(centers), "type": typ, "authority": auth,
            "definition": get_definition(centers, adj)}


# ── time helpers ──
def _jd_from_local(date_str, time_str, tz_name):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.UTC
    u = tz.localize(dt).astimezone(pytz.UTC)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def _local(jd, tz_name):
    y, m, d, h = swe.revjul(jd)
    dt = datetime(y, m, d, tzinfo=pytz.UTC) + timedelta(hours=h, seconds=30)  # nearest minute
    try:
        dt = dt.astimezone(pytz.timezone(tz_name))
    except Exception:
        pass
    return dt.strftime("%Y-%m-%d %H:%M")


# ── body longitudes (Earth / South Node derived like the natal) ──
_BASE = {"Sun": swe.SUN, "North Node": swe.TRUE_NODE, "Moon": swe.MOON,
         "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
         "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS,
         "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO}


def _lon(body, jd):
    if body == "Earth":
        return (swe.calc_ut(jd, swe.SUN, FLAGS)[0][0] + 180.0) % 360.0
    if body == "South Node":
        return (swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)[0][0] + 180.0) % 360.0
    return swe.calc_ut(jd, _BASE[body], FLAGS)[0][0] % 360.0


def _speed(body, jd):
    pid = _BASE.get({"Earth": "Sun", "South Node": "North Node"}.get(body, body))
    return swe.calc_ut(jd, pid, FLAGS)[0][3]


def _gate(body, jd):
    return decompose(_lon(body, jd))[0]


def _edge(body, j0, j1, g0):
    """Instant in (j0, j1] where body leaves gate g0 (bisection, < 1 min)."""
    for _ in range(30):
        if j1 - j0 < 1.0 / 1440:
            break
        m = (j0 + j1) / 2
        if _gate(body, m) == g0:
            j0 = m
        else:
            j1 = m
    return j1


# ── 1. one moment ──
def _act(a):
    return {"planet": a.planet, "glyph": a.glyph, "gate": a.gate, "line": a.line,
            "color": a.color, "tone": a.tone, "base": a.base,
            "longitude": round(a.longitude, 4)}


def status_at(natal_gates: Set[int], natal_centers: Set[str], jd: float) -> Dict:
    acts = calc_planets(jd)
    t_gates = {a.gate for a in acts}
    by_gate: Dict[int, List[str]] = {}
    for a in acts:
        by_gate.setdefault(a.gate, []).append(a.planet)

    rows = []
    for a, b, name in CHANNELS:
        na, nb = a in natal_gates, b in natal_gates
        ta, tb = a in t_gates, b in t_gates
        if na and nb:
            kind = "natal"
        elif (na and tb) or (nb and ta):
            kind = "completed"
        elif ta and tb:
            kind = "transit"
        else:
            continue
        rows.append({
            "gate_a": a, "gate_b": b, "name": name, "kind": kind,
            "natal_gates": [g for g in (a, b) if g in natal_gates],
            "transit": {str(g): by_gate.get(g, []) for g in (a, b) if g in t_gates},
            "new_centers": sorted({GATE_TO_CENTER[a], GATE_TO_CENTER[b]} - natal_centers)
                           if kind != "natal" else [],
        })

    combined = classify(natal_gates | t_gates)
    combined["new_centers"] = sorted(set(combined["centers"]) - natal_centers)
    return {"activations": [_act(a) for a in acts],
            "channels": rows,
            "combined": combined,
            "sky": classify(t_gates)}


# ── 2. ingress table: every gate every body passes through in the period ──
# scan step per body (days): max daily motion × step stays well under the
# 5.625° gate width, so no gate can be skipped between two samples.
# Verified against a fine brute-force scan over 10 years (see tests).
STEP = {"Moon": 1.0 / 12, "Mercury": 0.25, "Sun": 0.5, "Earth": 0.5, "Venus": 0.5,
        "Mars": 1.0, "North Node": 1.0, "South Node": 1.0, "Jupiter": 2.0,
        "Saturn": 3.0, "Uranus": 4.0, "Neptune": 5.0, "Pluto": 5.0}


def segments(jd0: float, days: float, include_moon: bool) -> Dict[str, List]:
    """{body: [[gate, start_jd, end_jd, retro], ...]} covering [jd0, jd0+days]
    without gaps. A retrograde loop simply produces the gate again."""
    jd1 = jd0 + days
    out: Dict[str, List] = {}
    for body in BODY_ORDER:
        if body == "Moon" and not include_moon:
            continue
        step = STEP.get(body, 0.25)
        segs = []
        j, g, s = jd0, _gate(body, jd0), jd0
        while j < jd1:
            jn = min(j + step, jd1)
            gn = _gate(body, jn)
            if gn != g:
                t = _edge(body, j, jn, g)
                segs.append([g, s, t])
                g, s, j = _gate(body, t), t, t
                continue
            j = jn
        segs.append([g, s, jd1])
        nodes = body in ("North Node", "South Node")
        out[body] = [[g, round(a, 5), round(e, 5),
                      (not nodes) and _speed(body, (a + e) / 2) < 0]
                     for g, a, e in segs]
    return out


def hanging_targets(natal_gates: Set[int]) -> Dict[int, List[Dict]]:
    """missing partner gate -> the channels it would complete."""
    out: Dict[int, List[Dict]] = {}
    for a, b, name in CHANNELS:
        for have, miss in ((a, b), (b, a)):
            if have in natal_gates and miss not in natal_gates:
                out.setdefault(miss, []).append(
                    {"gate_a": a, "gate_b": b, "name": name, "natal_gate": have})
    return out


# ── entry point used by the Flask route ──
def compute_hd_transit(natal_chart: Dict, t_date: str, t_time: str, tz_name: str,
                       days: int = 365, include_moon: bool = False) -> Dict:
    natal_gates = {int(g) for g in natal_chart["gate_sources"]}
    natal_centers = set(natal_chart["defined_centers"])
    jd = _jd_from_local(t_date, t_time, tz_name)
    days = max(1, min(int(days), 3660))
    if include_moon:
        days = min(days, 400)            # the Moon makes ~13 windows per gate a year
    st = status_at(natal_gates, natal_centers, jd)
    return {
        "moment": {"date": t_date, "time": t_time, "tz": tz_name,
                   "utc": _local(jd, "UTC")},
        "natal_gates": sorted(natal_gates),
        "natal_centers": sorted(natal_centers),
        **st,
        "period": {"jd0": round(jd, 5), "jd1": round(jd + days, 5),
                   "days": days, "moon": include_moon},
        "segments": segments(jd, days, include_moon),
        "channels_all": [{"gate_a": a, "gate_b": b, "name": n,
                          "center_a": GATE_TO_CENTER[a], "center_b": GATE_TO_CENTER[b]}
                         for a, b, n in CHANNELS],
        "note": ("ტრანზიტი = პლანეტების მიმდინარე პოზიციები (13 აქტივაცია). "
                 "88°-იანი წესი მხოლოდ ნატალური დიზაინისთვისაა და ტრანზიტზე არ ვრცელდება."),
    }


# ══════════════════════════════════════════════════════════════════
# 4. NEAREST-ACTIVATION SEARCH  (no fixed period: scans forward until found)
#    planet_gate : when does <planet> enter <gate>?            (each pass)
#    gate        : when is <gate> activated by any transit body?
#    channel     : when is <a-b> open?
#                  with natal   -> your own gate counts (hanging gate +
#                                  transit in the partner)
#                  transit only -> both gates held by transit bodies
# ══════════════════════════════════════════════════════════════════
JD_MAX = 2597641.0          # 2400-01-01, end of the sepl_18/semo_18 files


def _segs(body, j0, days):
    """[[gate, start, end], ...] for one body over [j0, j0+days]."""
    j1 = min(j0 + days, JD_MAX)
    step = STEP.get(body, 0.25)
    out, j, g, s = [], j0, _gate(body, j0), j0
    while j < j1:
        jn = min(j + step, j1)
        gn = _gate(body, jn)
        if gn != g:
            t = _edge(body, j, jn, g)
            out.append([g, s, t])
            g, s, j = _gate(body, t), t, t
            continue
        j = jn
    out.append([g, s, j1])
    return out


def _entry_before(body, jd, g, max_days=36600):
    """True start of the stay of `body` in gate g that contains jd."""
    step = STEP.get(body, 0.25) * 4
    j, back = jd, 0.0
    while back < max_days:
        jp = j - step
        if _gate(body, jp) != g:
            lo, hi = jp, j                       # gate changes in (lo, hi]
            for _ in range(40):
                if hi - lo < 1.0 / 1440:
                    break
                m = (lo + hi) / 2
                if _gate(body, m) == g:
                    hi = m
                else:
                    lo = m
            return hi
        j, back = jp, back + step
    return jd - max_days


def _merge(iv):
    """Union of [s, e, {bodies}, retro] intervals."""
    out = []
    for s, e, b, r in sorted(iv, key=lambda x: x[0]):
        if out and s <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], e)
            out[-1][2] |= b
            out[-1][3] = out[-1][3] or r
        else:
            out.append([s, e, set(b), r])
    return out


def _intersect(A, B):
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        s, e = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if e > s + 1e-6:
            out.append([s, e, A[i], B[j]])
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


def search_nearest(kind: str, jd_from: float, count: int = 3, include_moon: bool = False,
                   planet: str = None, gate: int = None, channel=None,
                   natal_gates: Set[int] = None, tz_name: str = "UTC") -> Dict:
    count = max(1, min(int(count), 12))
    if kind == "planet_gate":
        if planet not in BODY_ORDER:
            raise ValueError("unknown planet")
        bodies = [planet]
        horizon = 300 * 365.25 if planet in ("Uranus", "Neptune", "Pluto") else 100 * 365.25
        chunk = {"Pluto": 3650, "Neptune": 3650, "Uranus": 1825, "Saturn": 1095,
                 "Jupiter": 730}.get(planet, 365)
        gates = [int(gate)]
    else:
        bodies = [b for b in BODY_ORDER if include_moon or b != "Moon"]
        horizon = 60 * 365.25
        chunk = 60 if include_moon else 365
        gates = [int(gate)] if kind == "gate" else [int(channel[0]), int(channel[1])]
    for g in gates:
        if not 1 <= g <= 64:
            raise ValueError("gate must be 1-64")
    if kind == "channel":
        a, b = gates
        ch = next(((x, y, n) for x, y, n in CHANNELS if {x, y} == {a, b}), None)
        if not ch:
            raise ValueError("no such channel")
        gates = [ch[0], ch[1]]
    natal = set(natal_gates or [])

    # stays of the relevant bodies in the relevant gates, accumulated chunk by chunk
    stays = {g: [] for g in gates}          # g -> [[s, e, body, retro], ...]
    j, end = jd_from, min(jd_from + horizon, JD_MAX)
    windows = []
    while j < end:
        days = min(chunk, end - j)
        for body in bodies:
            for g, s, e in _segs(body, j, days):
                if g in stays:
                    lst = stays[g]
                    prev = next((x for x in reversed(lst) if x[2] == body), None)
                    if prev and abs(prev[1] - s) < 1e-6:
                        prev[1] = e                    # continues across chunks
                    else:
                        lst.append([s, e, body, False])
        j += days

        # windows found so far
        if kind == "planet_gate":
            windows = [[s, e, {bd}, r] for s, e, bd, r in stays[gates[0]]]
        elif kind == "gate":
            windows = _merge([[s, e, {bd}, False] for s, e, bd, _ in stays[gates[0]]])
        else:
            cov = []
            for g in gates:
                if g in natal:
                    cov.append([[-1e12, 1e12, {"natal"}, False]])
                else:
                    cov.append(_merge([[s, e, {bd}, False] for s, e, bd, _ in stays[g]]))
            windows = [[s, e, x[2] | y[2], False] for s, e, x, y in _intersect(cov[0], cov[1])]
        closed = [w for w in windows if w[1] < j - 1e-6]
        if len(closed) >= count:
            break

    # retrograde flag for single-planet passes, true start for "active now"
    out = []
    for s, e, bset, _ in windows[:count]:
        ongoing = e >= j - 1e-6 and j >= end
        start = s
        if s <= jd_from + 1e-6:
            per_gate = []
            for g in gates:
                if g in natal and kind == "channel":
                    continue
                st = [_entry_before(body, jd_from, g) for body in (bset - {"natal"})
                      if body in bodies and _gate(body, jd_from) == g]
                if st:
                    per_gate.append(min(st))
            if per_gate:
                start = max(per_gate) if kind == "channel" else min(per_gate)
        who = {}
        for g in gates:
            if g in natal and kind == "channel":
                who[str(g)] = ["natal"]
                continue
            who[str(g)] = sorted({bd for ss, ee, bd, _ in stays[g] if ss < e - 1e-6 and ee > s + 1e-6},
                                 key=BODY_ORDER.index)
        retro = None
        if kind == "planet_gate" and planet not in ("North Node", "South Node"):
            retro = _speed(planet, start + 0.01) < 0      # entered moving retrograde
        out.append({"start": round(start, 5), "end": None if ongoing else round(e, 5),
                    "start_local": _local(start, tz_name),
                    "end_local": None if ongoing else _local(e, tz_name),
                    "days": None if ongoing else round(e - start, 3),
                    "active_now": s <= jd_from + 1e-6,
                    "who": who, "retro": retro})

    res = {"kind": kind, "from": round(jd_from, 5), "from_local": _local(jd_from, tz_name),
           "searched_to_local": _local(j, tz_name), "windows": out,
           "gates": gates, "moon": include_moon, "natal_used": bool(natal)}
    if kind == "channel":
        res["channel"] = {"gate_a": gates[0], "gate_b": gates[1],
                          "name": next(n for x, y, n in CHANNELS if x == gates[0] and y == gates[1]),
                          "natal_gates": [g for g in gates if g in natal]}
        if all(g in natal for g in gates):
            res["note"] = "ეს არხი შენს ნატალურ რუქაში მუდმივად ღიაა."
    if kind == "gate" and gates[0] in natal:
        res["note"] = "ეს კარიბჭე შენს ნატალურ რუქაში უკვე აქტიურია — ქვემოთ ტრანზიტული გავლებია."
    if not out:
        res["note"] = "არ მოიძებნა %s-მდე." % _local(j, tz_name)[:4]
    return res
