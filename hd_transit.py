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

  2. timeline — for every hanging gate of the natal chart, the windows in
     which a transit body stands in the missing partner gate: body, gate,
     start, end, duration, and which centers become defined.

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
    dt = datetime(y, m, d, tzinfo=pytz.UTC) + timedelta(hours=h)
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


# ── 2. timeline of channel completions ──
def hanging_targets(natal_gates: Set[int]) -> Dict[int, List[Dict]]:
    """missing partner gate -> the channels it would complete."""
    out: Dict[int, List[Dict]] = {}
    for a, b, name in CHANNELS:
        for have, miss in ((a, b), (b, a)):
            if have in natal_gates and miss not in natal_gates:
                out.setdefault(miss, []).append(
                    {"gate_a": a, "gate_b": b, "name": name, "natal_gate": have})
    return out


# scan step per body (days): max daily motion × step stays well under the
# 5.625° gate width, so no gate can be skipped between two samples.
# Verified against a 30-min brute-force scan over 10 years (see tests).
STEP = {"Moon": 1.0 / 12, "Mercury": 0.25, "Sun": 0.5, "Earth": 0.5, "Venus": 0.5,
        "Mars": 1.0, "North Node": 1.0, "South Node": 1.0, "Jupiter": 2.0,
        "Saturn": 3.0, "Uranus": 4.0, "Neptune": 5.0, "Pluto": 5.0}


def timeline(natal_gates: Set[int], natal_centers: Set[str], jd0: float,
             days: int, tz_name: str, include_moon: bool) -> Dict:
    targets = hanging_targets(natal_gates)
    bodies = [b for b in BODY_ORDER if include_moon or b != "Moon"]
    jd1 = jd0 + days
    wins = []
    for body in bodies:
        step = STEP.get(body, 0.25)
        j = jd0
        g = _gate(body, j)
        start = jd0 if g in targets else None
        start_open = start is not None
        while j < jd1:
            jn = min(j + step, jd1)
            gn = _gate(body, jn)
            if gn != g:
                t = _edge(body, j, jn, g)
                if start is not None:                       # leaving a target gate
                    wins.append((body, g, start, t, start_open, False))
                    start = None
                g = _gate(body, t)
                if g in targets:                            # entering one
                    start, start_open = t, False
                # the body may have crossed again before jn (rare): continue from t
                j = t
                continue
            j = jn
        if start is not None:
            wins.append((body, g, start, jd1, start_open, True))

    out = []
    for body, gate, s, e, open_s, open_e in wins:
        retro = _speed(body, (s + e) / 2) < 0 if body not in ("North Node", "South Node") else False
        for ch in targets[gate]:
            new_c = sorted({GATE_TO_CENTER[ch["gate_a"]], GATE_TO_CENTER[ch["gate_b"]]} - natal_centers)
            out.append({
                "planet": body, "glyph": GLYPH.get(body, ""),
                "gate": gate, "natal_gate": ch["natal_gate"],
                "gate_a": ch["gate_a"], "gate_b": ch["gate_b"], "name": ch["name"],
                "start": _local(s, tz_name), "end": _local(e, tz_name),
                "start_jd": round(s, 5), "end_jd": round(e, 5),
                "days": round(e - s, 2),
                "open_start": open_s, "open_end": open_e,
                "retrograde": retro,
                "new_centers": new_c,
            })
    out.sort(key=lambda w: (w["start_jd"], BODY_ORDER.index(w["planet"])))
    return {"targets": {str(g): v for g, v in sorted(targets.items())},
            "windows": out, "days": days, "moon": include_moon}


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
    tl = timeline(natal_gates, natal_centers, jd, days, tz_name, include_moon)
    return {
        "moment": {"date": t_date, "time": t_time, "tz": tz_name,
                   "utc": _local(jd, "UTC")},
        "natal_gates": sorted(natal_gates),
        "natal_centers": sorted(natal_centers),
        **st,
        "timeline": tl,
        "note": ("ტრანზიტი = პლანეტების მიმდინარე პოზიციები (13 აქტივაცია). "
                 "88°-იანი წესი მხოლოდ ნატალური დიზაინისთვისაა და ტრანზიტზე არ ვრცელდება."),
    }
