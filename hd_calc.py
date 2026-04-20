"""Human Design calculations.

Uses the Swiss Ephemeris (pyswisseph) to compute planet positions for both
the Personality (birth moment) and Design (when the Sun was 88° earlier
in ecliptic longitude — roughly 88 days before birth).

Each planet's tropical longitude is mapped onto the 64-gate mandala that
starts at Gate 41 at 2°00' Aquarius (302° tropical). Each gate spans 5.625°
and is subdivided into line (×6), color (×6), tone (×6), base (×5).
"""

import csv
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

# ---------- The 64-gate wheel ----------
# Starting at Gate 41 = 2° Aquarius (302° tropical), reading forward.
GATE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
GATE_START = 302.0                   # 2° Aquarius, tropical
GATE_WIDTH = 360.0 / 64              # 5.625°

# ---------- Planet list ----------
# Order matters for display. Earth and South Node are derived (+180°).
PLANET_DEFS: List[Tuple[str, Optional[int], str]] = [
    ("Sun",         swe.SUN,        "☉"),
    ("Earth",       None,           "⊕"),
    ("North Node",  swe.TRUE_NODE,  "☊"),
    ("South Node",  None,           "☋"),
    ("Moon",        swe.MOON,       "☽"),
    ("Mercury",     swe.MERCURY,    "☿"),
    ("Venus",       swe.VENUS,      "♀"),
    ("Mars",        swe.MARS,       "♂"),
    ("Jupiter",     swe.JUPITER,    "♃"),
    ("Saturn",      swe.SATURN,     "♄"),
    ("Uranus",      swe.URANUS,     "♅"),
    ("Neptune",     swe.NEPTUNE,    "♆"),
    ("Pluto",       swe.PLUTO,      "♇"),
]

# ---------- Centers and gates ----------
CENTER_GATES: Dict[str, List[int]] = {
    "Head":         [64, 61, 63],
    "Ajna":         [47, 24, 4, 17, 11, 43],
    "Throat":       [62, 23, 56, 16, 35, 12, 45, 33, 8, 31, 20],
    "G":            [1, 2, 7, 10, 13, 15, 25, 46],
    "Heart":        [21, 26, 40, 51],
    "Solar Plexus": [6, 22, 30, 36, 37, 49, 55],
    "Spleen":       [18, 28, 32, 44, 48, 50, 57],
    "Sacral":       [3, 5, 9, 14, 27, 29, 34, 42, 59],
    "Root":         [19, 38, 39, 41, 52, 53, 54, 58],
}
GATE_TO_CENTER: Dict[int, str] = {
    g: c for c, gates in CENTER_GATES.items() for g in gates
}

# The 36 classical channels (gate pair, name).
CHANNELS: List[Tuple[int, int, str]] = [
    (1, 8, "Inspiration"),
    (2, 14, "The Beat"),
    (3, 60, "Mutation"),
    (4, 63, "Logic"),
    (5, 15, "Rhythm"),
    (6, 59, "Mating"),
    (7, 31, "The Alpha"),
    (9, 52, "Concentration"),
    (10, 20, "Awakening"),
    (10, 34, "Exploration"),
    (10, 57, "Perfected Form"),
    (11, 56, "Curiosity"),
    (12, 22, "Openness"),
    (13, 33, "The Prodigal"),
    (16, 48, "Wavelength"),
    (17, 62, "Acceptance"),
    (18, 58, "Judgment"),
    (19, 49, "Synthesis"),
    (20, 34, "Charisma"),
    (20, 57, "Brainwave"),
    (21, 45, "Money"),
    (23, 43, "Structuring"),
    (24, 61, "Awareness"),
    (25, 51, "Initiation"),
    (26, 44, "Surrender"),
    (27, 50, "Preservation"),
    (28, 38, "Struggle"),
    (29, 46, "Discovery"),
    (30, 41, "Recognition"),
    (32, 54, "Transformation"),
    (34, 57, "Power"),
    (35, 36, "Transitoriness"),
    (37, 40, "Community"),
    (39, 55, "Emoting"),
    (42, 53, "Maturation"),
    (47, 64, "Abstraction"),
]

MOTORS = {"Heart", "Sacral", "Solar Plexus", "Root"}

# --------------------------------------------------------------------
# Integration cluster (gates 10, 57, 34, 20) — 256 combinations
# --------------------------------------------------------------------
# CSV column order: 10, 57, 34, 20  (MSB → LSB for the detail index).
# Each gate has 4 possible states:
#   None = 0   (not activated)
#   A    = 1   (personality only)
#   B    = 2   (design only)
#   Both = 3   (personality AND design)
# Detail number N (1..256) = state_10*64 + state_57*16 + state_34*4 + state_20 + 1
INTEGRATION_GATES = (10, 57, 34, 20)        # MSB first
INTEGRATION_STATE_VAL = {"None": 0, "A": 1, "B": 2, "Both": 3}


def _load_integration_csv() -> List[Dict]:
    """Load the 256-row CSV that enumerates every combination."""
    path = Path(__file__).parent / "static" / "integration_conditions.csv"
    if not path.exists():
        # Fall back to the original upload if available
        alt = Path("/mnt/user-data/uploads/Book_Sheet1___1_.csv")
        if alt.exists():
            path = alt
        else:
            return []
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)          # ["10","57","34","20", ...]
        for r_idx, row in enumerate(reader, start=1):
            if len(row) < 4:
                continue
            g10, g57, g34, g20 = row[0], row[1], row[2], row[3]
            # Optional 5th column = title (if user adds one later)
            title = row[4].strip() if len(row) > 4 and row[4].strip() else ""
            rows.append({
                "n": r_idx,
                "states": {"10": g10, "57": g57, "34": g34, "20": g20},
                "title": title,
            })
    return rows


INTEGRATION_CONDITIONS = _load_integration_csv()


def gate_state(gate: int, p_gates: set, d_gates: set) -> int:
    """Return 0 (None), 1 (A=P-only), 2 (B=D-only), 3 (Both)."""
    in_p = gate in p_gates
    in_d = gate in d_gates
    if in_p and in_d:
        return 3
    if in_p:
        return 1
    if in_d:
        return 2
    return 0


def integration_condition(p_gates: set, d_gates: set) -> Dict:
    """Compute the 1..256 condition number for the 10-57-34-20 integration
    cluster from the personality/design gate sets.
    """
    s10 = gate_state(10, p_gates, d_gates)
    s57 = gate_state(57, p_gates, d_gates)
    s34 = gate_state(34, p_gates, d_gates)
    s20 = gate_state(20, p_gates, d_gates)
    n = s10 * 64 + s57 * 16 + s34 * 4 + s20 + 1
    label = {0: "None", 1: "A", 2: "B", 3: "Both"}
    row = INTEGRATION_CONDITIONS[n - 1] if (1 <= n <= len(INTEGRATION_CONDITIONS)) else None
    return {
        "n": n,
        "states": {
            "10": label[s10],
            "57": label[s57],
            "34": label[s34],
            "20": label[s20],
        },
        "title": row.get("title", "") if row else "",
    }


@dataclass
class Activation:
    planet: str
    glyph: str
    longitude: float      # tropical, 0..360
    gate: int
    line: int             # 1..6
    color: int            # 1..6
    tone: int             # 1..6
    base: int             # 1..5


# ---------- Gate/line/color/tone/base decomposition ----------
def decompose(longitude: float) -> Tuple[int, int, int, int, int]:
    """Given tropical longitude (0..360), return (gate, line, color, tone, base)."""
    lon = longitude % 360
    offset = (lon - GATE_START) % 360
    gate_idx = int(offset // GATE_WIDTH)
    gate = GATE_ORDER[gate_idx]

    rem = offset - gate_idx * GATE_WIDTH          # remainder within gate
    line_w = GATE_WIDTH / 6                        # 0.9375°
    line = int(rem // line_w) + 1
    rem -= (line - 1) * line_w

    color_w = line_w / 6                           # 0.15625°
    color = int(rem // color_w) + 1
    rem -= (color - 1) * color_w

    tone_w = color_w / 6                           # ≈0.02604°
    tone = int(rem // tone_w) + 1
    rem -= (tone - 1) * tone_w

    base_w = tone_w / 5                            # ≈0.00521°
    base = min(5, int(rem // base_w) + 1)
    return gate, max(1, min(6, line)), max(1, min(6, color)), max(1, min(6, tone)), base


# ---------- Core calc ----------
def calc_planets(jd_ut: float) -> List[Activation]:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    longs: Dict[str, float] = {}
    for name, pid, _ in PLANET_DEFS:
        if pid is None:
            continue
        data, _ = swe.calc_ut(jd_ut, pid, flags)
        longs[name] = data[0] % 360
    longs["Earth"] = (longs["Sun"] + 180) % 360
    longs["South Node"] = (longs["North Node"] + 180) % 360

    results: List[Activation] = []
    for name, _pid, glyph in PLANET_DEFS:
        lon = longs[name]
        g, l, c, t, b = decompose(lon)
        results.append(Activation(name, glyph, lon, g, l, c, t, b))
    return results


def find_design_jd(birth_jd_ut: float) -> float:
    """Design = moment when Sun was 88° earlier than at birth (solar arc).

    Iteratively refined: Sun moves ~0.9856°/day, so the design instant is
    roughly 88 days earlier. We Newton-iterate until the Sun's longitude
    exactly matches birth_sun − 88°.
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    birth_sun, _ = swe.calc_ut(birth_jd_ut, swe.SUN, flags)
    target = (birth_sun[0] - 88) % 360
    jd = birth_jd_ut - 88.0
    for _ in range(50):
        sun, _ = swe.calc_ut(jd, swe.SUN, flags)
        speed = max(0.5, sun[3])            # deg/day (always positive for Sun)
        diff = ((sun[0] - target + 540) % 360) - 180
        if abs(diff) < 1e-8:
            break
        jd -= diff / speed
    return jd


# ---------- Body graph / synthesis ----------
def analyze(personality: List[Activation], design: List[Activation]) -> Dict:
    """Return full analysis: activated gates, channels, centers, type, profile, authority."""
    p_gates = {a.gate for a in personality}
    d_gates = {a.gate for a in design}
    all_gates = p_gates | d_gates

    gate_sources: Dict[int, Dict[str, bool]] = {}
    for g in all_gates:
        gate_sources[g] = {"p": g in p_gates, "d": g in d_gates}

    # Defined channels = both gates activated (either source)
    defined_channels = []
    for a, b, name in CHANNELS:
        if a in all_gates and b in all_gates:
            # Classify color: only-design, only-personality, mixed
            a_src = gate_sources[a]
            b_src = gate_sources[b]
            both_only_d = (a_src["d"] and not a_src["p"]) and (b_src["d"] and not b_src["p"])
            both_only_p = (a_src["p"] and not a_src["d"]) and (b_src["p"] and not b_src["d"])
            if both_only_d:
                channel_type = "design"
            elif both_only_p:
                channel_type = "personality"
            else:
                channel_type = "mixed"
            defined_channels.append({"gate_a": a, "gate_b": b, "name": name, "type": channel_type})

    # Defined centers = any center that has BOTH ends of a defined channel touching it
    # (a center is defined if at least one of its gates is on an activated channel)
    defined_centers = set()
    for ch in defined_channels:
        defined_centers.add(GATE_TO_CENTER[ch["gate_a"]])
        defined_centers.add(GATE_TO_CENTER[ch["gate_b"]])

    # ---------- Type ----------
    sacral_def = "Sacral" in defined_centers
    throat_def = "Throat" in defined_centers
    # A center is "connected" to another center via a chain of defined channels.
    # Build center-adjacency via defined channels.
    adj: Dict[str, set] = {c: set() for c in CENTER_GATES}
    for ch in defined_channels:
        ca = GATE_TO_CENTER[ch["gate_a"]]
        cb = GATE_TO_CENTER[ch["gate_b"]]
        if ca != cb:
            adj[ca].add(cb)
            adj[cb].add(ca)

    def reachable_from(start: str) -> set:
        """BFS through defined centers only."""
        seen = {start}
        stack = [start]
        while stack:
            n = stack.pop()
            for m in adj[n]:
                if m in defined_centers and m not in seen:
                    seen.add(m)
                    stack.append(m)
        return seen

    throat_reaches_motor = False
    if throat_def:
        reach = reachable_from("Throat")
        throat_reaches_motor = any(m in reach for m in MOTORS)

    if not defined_centers:
        hd_type = "Reflector"
    elif sacral_def and throat_reaches_motor:
        hd_type = "Manifesting Generator"
    elif sacral_def:
        hd_type = "Generator"
    elif throat_reaches_motor:
        hd_type = "Manifestor"
    else:
        hd_type = "Projector"

    # ---------- Strategy ----------
    strategy_map = {
        "Manifestor": "To Inform",
        "Generator": "To Respond",
        "Manifesting Generator": "To Respond, then Inform",
        "Projector": "Wait for the Invitation",
        "Reflector": "Wait a Lunar Cycle (28 days)",
    }
    not_self = {
        "Manifestor": "Anger",
        "Generator": "Frustration",
        "Manifesting Generator": "Anger & Frustration",
        "Projector": "Bitterness",
        "Reflector": "Disappointment",
    }
    signature = {
        "Manifestor": "Peace",
        "Generator": "Satisfaction",
        "Manifesting Generator": "Peace & Satisfaction",
        "Projector": "Success",
        "Reflector": "Surprise",
    }

    # ---------- Authority ----------
    if "Solar Plexus" in defined_centers:
        authority = "Emotional (Solar Plexus)"
    elif sacral_def:
        authority = "Sacral"
    elif "Spleen" in defined_centers:
        authority = "Splenic"
    elif "Heart" in defined_centers:
        authority = "Ego (Heart)"
    elif "G" in defined_centers:
        authority = "Self-Projected (G)"
    elif hd_type == "Reflector":
        authority = "Lunar"
    else:
        authority = "Mental / Environmental (no inner authority)"

    # ---------- Profile = Personality Sun line / Design Sun line ----------
    p_sun_line = next(a.line for a in personality if a.planet == "Sun")
    d_sun_line = next(a.line for a in design if a.planet == "Sun")
    profile = f"{p_sun_line}/{d_sun_line}"

    # ---------- Incarnation Cross ----------
    p_sun  = next(a for a in personality if a.planet == "Sun")
    p_earth = next(a for a in personality if a.planet == "Earth")
    d_sun  = next(a for a in design if a.planet == "Sun")
    d_earth = next(a for a in design if a.planet == "Earth")
    cross = f"{p_sun.gate}/{p_earth.gate} | {d_sun.gate}/{d_earth.gate}"

    return {
        "gate_sources": gate_sources,             # {gate: {p,d}}
        "defined_channels": defined_channels,
        "defined_centers": sorted(defined_centers),
        "type": hd_type,
        "strategy": strategy_map[hd_type],
        "not_self": not_self[hd_type],
        "signature": signature[hd_type],
        "authority": authority,
        "profile": profile,
        "incarnation_cross": cross,
    }


# ---------- Geocoding ----------
_tf = TimezoneFinder()


def geocode(place: str) -> Tuple[float, float, str, str]:
    """Return (lat, lon, display_name, tz_name).

    Tries geopy's Nominatim first, then falls back to a direct HTTP call
    to nominatim.openstreetmap.org (same fallback the main /geocode
    endpoint uses — works reliably on Railway).
    """
    import urllib.request, urllib.parse, json as _json

    lat = lon = None
    display = place

    # 1) try geopy​
    try:
        q = urllib.parse.urlencode({"q": place, "limit": 1})
        req = urllib.request.Request(
            f"https://photon.komoot.io/api/?{q}",
            headers={"User-Agent": "astro-app/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            res = _json.loads(r.read())
        if res.get("features"):
            coords = res["features"][0]["geometry"]["coordinates"]
            lon = coords[0]
            lat = coords[1]
            display = place
        else:
            raise ValueError(f"Could not find location: {place!r}")
    except Exception as e:
        raise ValueError(f"Geocoding service error: {e}")
    if lat is None or lon is None:
        raise ValueError(f"Could not find location: {place!r}")

    tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
    return lat, lon, display, tz


# ---------- Top-level entry point ----------
def calculate_chart(date_str: str, time_str: str, place: str) -> Dict:
    """Inputs are strings: 'YYYY-MM-DD', 'HH:MM', 'City, Country'.

    Returns a dict ready for jsonify.
    """
    lat, lon_loc, addr, tz_name = geocode(place)

    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    try:
        local_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.UTC
    local_aware = local_tz.localize(local_dt)
    utc_dt = local_aware.astimezone(pytz.UTC)

    jd_ut = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600,
    )
    personality = calc_planets(jd_ut)
    design_jd  = find_design_jd(jd_ut)
    design     = calc_planets(design_jd)

    analysis = analyze(personality, design)
    design_utc = swe.revjul(design_jd)   # (y, m, d, frac_hour)

    # Integration cluster (gates 10, 57, 34, 20) — detail number 1..256.
    p_gate_set = {a.gate for a in personality}
    d_gate_set = {a.gate for a in design}
    integration = integration_condition(p_gate_set, d_gate_set)

    return {
        "input": {
            "date": date_str, "time": time_str, "place": place,
            "resolved_place": addr,
            "lat": lat, "lon": lon_loc,
            "tz": tz_name,
            "utc_time": utc_dt.strftime("%Y-%m-%d %H:%M UTC"),
        },
        "design_time_utc": "%04d-%02d-%02d %02d:%02d UTC" % (
            design_utc[0], design_utc[1], design_utc[2],
            int(design_utc[3]), int((design_utc[3] % 1) * 60),
        ),
        "personality": [asdict(a) for a in personality],
        "design":      [asdict(a) for a in design],
        "integration": integration,
        **analysis,
    }
