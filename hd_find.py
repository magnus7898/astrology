"""
Human Design · moment search  (POST /api/hd_find)

Looks forward ("next") or backward ("prev") from a moment for the times when

  profile      personality-Sun line / design-Sun line            e.g. 4/6
  digestion    design Sun color (+ arrow from its tone)          PHS food
  environment  design North Node color (+ arrow)
  motivation   personality Sun color (+ arrow)
  perspective  personality North Node color (+ arrow)
      -> a person born then would have it (the sky's own chart)

  center       a center is defined —
                 with natal gates: transit bodies + your gates complete a
                 channel into that center (your open center gets defined)
                 without natal:    the transit sky defines it by itself

Same conventions as hd_calc: the design moment is where the Sun stood 88°
earlier (find_design_jd), true node, arrow = tone 1-3 left / 4-6 right.
Because design-Sun = personality-Sun − 88° exactly, profile / digestion /
motivation depend on the Sun alone and are scanned in 20-minute steps;
environment / perspective follow the node (1-hour steps). Every edge is
refined by bisection to under a minute.
"""

from typing import Dict, List, Optional, Set

import swisseph as swe

from hd_calc import (CHANNELS, GATE_TO_CENTER, PROFILE_NAMES, DIGESTION, ENVIRONMENT,
                     MOTIVATION, PERSPECTIVE, decompose, find_design_jd)
from hd_transit import BODY_ORDER, JD_MAX, _local, _segs

FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED
JD_MIN = 2268923.5            # 1500-01-01, start of the sepl_18/semo_18 files

CENTER_KA = {"Head": "თავი", "Ajna": "აჯნა", "Throat": "ყელი", "G": "G · მე",
             "Heart": "გული · ეგო", "Solar Plexus": "მზის წნული", "Spleen": "ელენთა",
             "Sacral": "საკრალი", "Root": "ფესვი"}


def _sun(jd):
    return swe.calc_ut(jd, swe.SUN, FLAGS)[0][0] % 360.0


def _node(jd):
    return swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)[0][0] % 360.0


def _arrow(tone):
    return "left" if tone <= 3 else "right"


# ── value of a variable at a moment ──
def _value(kind, jd):
    if kind == "profile":
        s = _sun(jd)
        return (decompose(s)[1], decompose(s - 88.0)[1])
    if kind == "digestion":
        _, _, c, t, _ = decompose(_sun(jd) - 88.0)
        return (c, _arrow(t))
    if kind == "motivation":
        _, _, c, t, _ = decompose(_sun(jd))
        return (c, _arrow(t))
    if kind == "environment":
        _, _, c, t, _ = decompose(_node(find_design_jd(jd)))
        return (c, _arrow(t))
    if kind == "perspective":
        _, _, c, t, _ = decompose(_node(jd))
        return (c, _arrow(t))
    raise ValueError("unknown kind")


STEP = {"profile": 1 / 72, "digestion": 1 / 72, "motivation": 1 / 72,
        "environment": 1 / 24, "perspective": 1 / 24}
HORIZON = {"profile": 800, "digestion": 120, "motivation": 120,
           "environment": 3 * 365.25, "perspective": 3 * 365.25}
TABLE = {"digestion": DIGESTION, "environment": ENVIRONMENT,
         "motivation": MOTIVATION, "perspective": PERSPECTIVE}


def _label(kind, target):
    if kind == "profile":
        k = "%d/%d" % target
        return PROFILE_NAMES.get(k, k)
    c, side = target
    tbl = TABLE[kind]
    if side:
        return tbl.get((c, side), "")
    return tbl.get((c, "left"), "").split(" — ")[0] + " (ორივე ისარი)"


def _edge(f, a, b):
    """f(a) != f(b): the instant of change in (a, b], to < 1 minute."""
    fa = f(a)
    for _ in range(40):
        if abs(b - a) < 1.0 / 1440:
            break
        m = (a + b) / 2
        if f(m) == fa:
            a = m
        else:
            b = m
    return b


def _scan(kind, target, jd_from, direction, count):
    """Windows [start, end] in which the variable equals target."""
    side = target[1] if kind != "profile" else True
    def ok(jd):
        v = _value(kind, jd)
        if kind == "profile":
            return v == target
        return v[0] == target[0] and (not side or v[1] == side)

    step = STEP[kind] * (1 if direction == "next" else -1)
    limit = HORIZON[kind]
    lo_lim, hi_lim = max(JD_MIN, jd_from - limit), min(JD_MAX, jd_from + limit)
    out = []

    # a window already running at jd_from: find both of its ends
    if ok(jd_from):
        s = jd_from
        while s > lo_lim and ok(s - abs(step)):
            s -= abs(step)
        s = _edge(ok, s, s - abs(step)) if s > lo_lim else s
        e = jd_from
        while e < hi_lim and ok(e + abs(step)):
            e += abs(step)
        e = _edge(ok, e, e + abs(step)) if e < hi_lim else e
        out.append([s, e, True])
        j = e if direction == "next" else s
    else:
        j = jd_from

    cur = ok(j)
    while len(out) < count:
        jn = j + step
        if jn < lo_lim or jn > hi_lim:
            break
        nx = ok(jn)
        if nx != cur:
            t = _edge(ok, j, jn)
            if nx:                                   # entering a window
                a = t
                k = t
                while ok(k + step) and lo_lim < k + step < hi_lim:
                    k += step
                b = _edge(ok, k, k + step)
                s, e = (a, b) if direction == "next" else (b, a)
                out.append([s, e, False])
                j, cur = b, False
                continue
            j, cur = t, nx
            continue
        j = jn
    return out, (hi_lim if direction == "next" else lo_lim)


# ── center definition windows ──
def _union(iv):
    out = []
    for s, e, ch, bd in sorted(iv, key=lambda x: x[0]):
        if out and s <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], e)
            out[-1][2] |= ch
            out[-1][3] |= bd
        else:
            out.append([s, e, set(ch), set(bd)])
    return out


def _cover(stays):
    """Merge one gate's stays into continuous coverage with the bodies inside."""
    return _union([[s, e, set(), {b}] for s, e, b in stays])


def _isect(A, B):
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        s, e = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if e > s + 1e-6:
            out.append([s, e, A[i][3] | B[j][3]])
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


def _center_scan(center, jd_from, direction, count, natal: Set[int], include_moon):
    chans = [(a, b, n) for a, b, n in CHANNELS
             if center in (GATE_TO_CENTER[a], GATE_TO_CENTER[b])]
    bodies = [b for b in BODY_ORDER if include_moon or b != "Moon"]
    gates = {g for a, b, _ in chans for g in (a, b) if g not in natal}
    span, horizon = (45.0 if include_moon else 180.0), (2 * 365.25 if include_moon else 40 * 365.25)
    while True:
        if direction == "next":
            lo, hi = jd_from - (30 if include_moon else 400), min(JD_MAX, jd_from + span)
        else:
            lo, hi = max(JD_MIN, jd_from - span), min(JD_MAX, jd_from + (30 if include_moon else 400))
        stays = {g: [] for g in gates}
        for body in bodies:
            for g, s, e in _segs(body, lo, hi - lo):
                if g in stays:
                    stays[g].append([s, e, body])
        cov = {g: _cover(v) for g, v in stays.items()}
        ALL = [[-1e12, 1e12, set(), {"natal"}]]
        wins = []
        for a, b, n in chans:
            ca, cb = (ALL if a in natal else cov[a]), (ALL if b in natal else cov[b])
            for s, e, bd in _isect(ca, cb):
                wins.append([max(s, lo), min(e, hi), {"%d-%d" % (a, b)}, bd - {"natal"}])
        wins = _union(wins)
        if direction == "next":
            sel = [w for w in wins if w[1] > jd_from + 1e-6]
            closed = [w for w in sel if w[1] < hi - 1e-6]
        else:
            sel = sorted([w for w in wins if w[0] < jd_from - 1e-6], key=lambda w: -w[0])
            closed = [w for w in sel if w[0] > lo + 1e-6]
        if len(closed) >= count or span >= horizon or hi >= JD_MAX or lo <= JD_MIN:
            return sel[:count], lo, hi
        span *= 2


def find(kind: str, jd_from: float, direction: str = "next", count: int = 5,
         value=None, side: Optional[str] = None, natal_gates: Optional[Set[int]] = None,
         natal_centers: Optional[Set[str]] = None, include_moon: bool = False,
         tz_name: str = "UTC") -> Dict:
    direction = "prev" if direction == "prev" else "next"
    count = max(1, min(int(count), 12))
    res = {"kind": kind, "direction": direction, "from_local": _local(jd_from, tz_name)}

    if kind == "center":
        if value not in GATE_TO_CENTER.values():
            raise ValueError("unknown center")
        natal = set(natal_gates or [])
        res["center"], res["center_ka"] = value, CENTER_KA.get(value, value)
        res["natal_used"] = bool(natal)
        res["label"] = "%s ცენტრის განსაზღვრა" % res["center_ka"]
        if natal_centers and value in natal_centers:
            res["windows"] = []
            res["note"] = "ეს ცენტრი შენს ნატალურ რუქაში უკვე განსაზღვრულია — ტრანზიტი მას არ „ააქტიურებს“, ის მუდამ შენია."
            return res
        wins, lo, hi = _center_scan(value, jd_from, direction, count, natal, include_moon)
        out = []
        for s, e, chs, bd in wins:
            open_s, open_e = s <= lo + 1e-6, e >= hi - 1e-6
            out.append({"start": round(s, 5), "end": round(e, 5),
                        "start_local": None if open_s else _local(s, tz_name),
                        "end_local": None if open_e else _local(e, tz_name),
                        "days": None if (open_s or open_e) else round(e - s, 3),
                        "active_now": s <= jd_from + 1e-6 <= e,
                        "channels": sorted(chs, key=lambda x: int(x.split("-")[0])),
                        "bodies": sorted(bd, key=BODY_ORDER.index)})
        res["windows"] = out
        res["label"] = "%s ცენტრის განსაზღვრა" % res["center_ka"]
        if not out:
            res["note"] = "ამ ჰორიზონტზე ვერ მოიძებნა."
        return res

    if kind not in STEP:
        raise ValueError("unknown kind")
    if kind == "profile":
        try:
            a, b = (int(x) for x in str(value).split("/"))
        except Exception:
            raise ValueError("profile must look like 4/6")
        if "%d/%d" % (a, b) not in PROFILE_NAMES:
            raise ValueError("no such profile")
        target = (a, b)
    else:
        c = int(value)
        if not 1 <= c <= 6:
            raise ValueError("color must be 1-6")
        target = (c, side if side in ("left", "right") else None)
    wins, edge = _scan(kind, target, jd_from, direction, count)
    out = []
    for s, e, now in wins:
        mid = (s + e) / 2
        out.append({"start": round(s, 5), "end": round(e, 5),
                    "start_local": _local(s, tz_name), "end_local": _local(e, tz_name),
                    "mid_local": _local(mid, tz_name), "hours": round((e - s) * 24, 2),
                    "active_now": now})
    res.update({"windows": out, "label": _label(kind, target),
                "searched_to_local": _local(edge, tz_name)})
    if not out:
        res["note"] = "ვერ მოიძებნა %s-მდე." % _local(edge, tz_name)[:10]
    return res
