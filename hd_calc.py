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
    "Root":         [19, 38, 39, 41, 52, 53, 54, 58, 60],
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
    """Load the 256-row CSV. Each row index (1-256) = the detail artboard number.
    Columns: 10, 57, 34, 20 — each cell is 'None', 'A', 'B', or 'Both'.
    """
    path = Path(__file__).parent / "static" / "integration_conditions.csv"
    if not path.exists():
        alt = Path("/mnt/user-data/uploads/Book_Sheet1___1_.csv")
        if alt.exists():
            path = alt
        else:
            return []
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)          # skip header ["10","57","34","20", ...]
        for r_idx, row in enumerate(reader, start=1):
            if len(row) < 4:
                continue
            rows.append({
                "n": r_idx,
                "states": {
                    "10": row[0].strip(),
                    "57": row[1].strip(),
                    "34": row[2].strip(),
                    "20": row[3].strip(),
                },
            })
    return rows


INTEGRATION_CONDITIONS = _load_integration_csv()

# Build reverse lookup: (state10, state57, state34, state20) → detail_n
_INTEGRATION_LOOKUP: Dict[tuple, int] = {}
for _row in INTEGRATION_CONDITIONS:
    s = _row["states"]
    _INTEGRATION_LOOKUP[(s["10"], s["57"], s["34"], s["20"])] = _row["n"]


def gate_state_label(gate: int, p_gates: set, d_gates: set) -> str:
    """Return 'None', 'A' (personality), 'B' (design), or 'Both'."""
    in_p = gate in p_gates
    in_d = gate in d_gates
    if in_p and in_d:  return "Both"
    if in_p:           return "A"
    if in_d:           return "B"
    return "None"


def gate_state(gate: int, p_gates: set, d_gates: set) -> int:
    """Return 0 (None), 1 (A=P-only), 2 (B=D-only), 3 (Both)."""
    in_p = gate in p_gates
    in_d = gate in d_gates
    if in_p and in_d: return 3
    if in_p:          return 1
    if in_d:          return 2
    return 0


def integration_condition(p_gates: set, d_gates: set) -> Dict:
    s10 = gate_state(10, p_gates, d_gates)  # 0=None,1=A,2=B,3=Both
    s57 = gate_state(57, p_gates, d_gates)
    s34 = gate_state(34, p_gates, d_gates)
    s20 = gate_state(20, p_gates, d_gates)
    n = s10 * 64 + s57 * 16 + s34 * 4 + s20 + 1  # 1..256
    label = {0: "None", 1: "A", 2: "B", 3: "Both"}
    return {
        "n": n,
        "states": {"10": label[s10], "57": label[s57],
                   "34": label[s34], "20": label[s20]},
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

    # Defined centers = any center touched by a defined channel
    defined_centers = set()
    for ch in defined_channels:
        ca = GATE_TO_CENTER.get(ch["gate_a"])
        cb = GATE_TO_CENTER.get(ch["gate_b"])
        if ca: defined_centers.add(ca)
        if cb: defined_centers.add(cb)

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

# Built-in city cache — works without any network call.
# Railway blocks all public Nominatim/Photon geocoders from cloud IPs.
# Set the OPENCAGE_API_KEY environment variable for full geocoding support.
_CITY_CACHE = {
    "tbilisi": (41.7151, 44.8271, "Tbilisi, Georgia", "Asia/Tbilisi"),
    "tbilisi, georgia": (41.7151, 44.8271, "Tbilisi, Georgia", "Asia/Tbilisi"),
    "kutaisi": (42.2679, 42.7181, "Kutaisi, Georgia", "Asia/Tbilisi"),
    "batumi": (41.6417, 41.6378, "Batumi, Georgia", "Asia/Tbilisi"),
    "rustavi": (41.5490, 44.9999, "Rustavi, Georgia", "Asia/Tbilisi"),
    "gori": (41.9851, 44.1086, "Gori, Georgia", "Asia/Tbilisi"),
    "zugdidi": (42.5082, 41.8707, "Zugdidi, Georgia", "Asia/Tbilisi"),
    "sokhumi": (43.0010, 41.0184, "Sokhumi, Abkhazia", "Asia/Tbilisi"),
    "london": (51.5074, -0.1278, "London, UK", "Europe/London"),
    "paris": (48.8566, 2.3522, "Paris, France", "Europe/Paris"),
    "berlin": (52.5200, 13.4050, "Berlin, Germany", "Europe/Berlin"),
    "moscow": (55.7558, 37.6173, "Moscow, Russia", "Europe/Moscow"),
    "new york": (40.7128, -74.0060, "New York, USA", "America/New_York"),
    "istanbul": (41.0082, 28.9784, "Istanbul, Turkey", "Europe/Istanbul"),
    "kyiv": (50.4501, 30.5234, "Kyiv, Ukraine", "Europe/Kyiv"),
    "yerevan": (40.1872, 44.5152, "Yerevan, Armenia", "Asia/Yerevan"),
    "baku": (40.4093, 49.8671, "Baku, Azerbaijan", "Asia/Baku"),
    "tehran": (35.6892, 51.3890, "Tehran, Iran", "Asia/Tehran"),
    "dubai": (25.2048, 55.2708, "Dubai, UAE", "Asia/Dubai"),
    "delhi": (28.7041, 77.1025, "Delhi, India", "Asia/Kolkata"),
    "mumbai": (19.0760, 72.8777, "Mumbai, India", "Asia/Kolkata"),
    "tokyo": (35.6762, 139.6503, "Tokyo, Japan", "Asia/Tokyo"),
    "beijing": (39.9042, 116.4074, "Beijing, China", "Asia/Shanghai"),
    "sydney": (-33.8688, 151.2093, "Sydney, Australia", "Australia/Sydney"),
    "toronto": (43.6532, -79.3832, "Toronto, Canada", "America/Toronto"),
    "montreal": (45.5017, -73.5673, "Montreal, Canada", "America/Toronto"),
    "los angeles": (34.0522, -118.2437, "Los Angeles, USA", "America/Los_Angeles"),
    "chicago": (41.8781, -87.6298, "Chicago, USA", "America/Chicago"),
    "madrid": (40.4168, -3.7038, "Madrid, Spain", "Europe/Madrid"),
    "rome": (41.9028, 12.4964, "Rome, Italy", "Europe/Rome"),
    "amsterdam": (52.3676, 4.9041, "Amsterdam, Netherlands", "Europe/Amsterdam"),
    "vienna": (48.2082, 16.3738, "Vienna, Austria", "Europe/Vienna"),
    "warsaw": (52.2297, 21.0122, "Warsaw, Poland", "Europe/Warsaw"),
    "athens": (37.9755, 23.7348, "Athens, Greece", "Europe/Athens"),
    "bucharest": (44.4268, 26.1025, "Bucharest, Romania", "Europe/Bucharest"),
    "budapest": (47.4979, 19.0402, "Budapest, Hungary", "Europe/Budapest"),
    "sofia": (42.6977, 23.3219, "Sofia, Bulgaria", "Europe/Sofia"),
    "prague": (50.0755, 14.4378, "Prague, Czech Republic", "Europe/Prague"),
    "stockholm": (59.3293, 18.0686, "Stockholm, Sweden", "Europe/Stockholm"),
    "oslo": (59.9139, 10.7522, "Oslo, Norway", "Europe/Oslo"),
    "helsinki": (60.1699, 24.9384, "Helsinki, Finland", "Europe/Helsinki"),
    "seoul": (37.5665, 126.9780, "Seoul, South Korea", "Asia/Seoul"),
    "singapore": (1.3521, 103.8198, "Singapore", "Asia/Singapore"),
    "bangkok": (13.7563, 100.5018, "Bangkok, Thailand", "Asia/Bangkok"),
    "cairo": (30.0444, 31.2357, "Cairo, Egypt", "Africa/Cairo"),
    "nairobi": (-1.2921, 36.8219, "Nairobi, Kenya", "Africa/Nairobi"),
    "johannesburg": (-26.2041, 28.0473, "Johannesburg, South Africa", "Africa/Johannesburg"),
    "buenos aires": (-34.6037, -58.3816, "Buenos Aires, Argentina", "America/Argentina/Buenos_Aires"),
    "sao paulo": (-23.5505, -46.6333, "São Paulo, Brazil", "America/Sao_Paulo"),
    "mexico city": (19.4326, -99.1332, "Mexico City, Mexico", "America/Mexico_City"),
    "kyoto": (35.0116, 135.7681, "Kyoto, Japan", "Asia/Tokyo"),
    "osaka": (34.6937, 135.5023, "Osaka, Japan", "Asia/Tokyo"),
    "shanghai": (31.2304, 121.4737, "Shanghai, China", "Asia/Shanghai"),
    "hong kong": (22.3193, 114.1694, "Hong Kong", "Asia/Hong_Kong"),
    "jakarta": (-6.2088, 106.8456, "Jakarta, Indonesia", "Asia/Jakarta"),
    "lahore": (31.5497, 74.3436, "Lahore, Pakistan", "Asia/Karachi"),
    "karachi": (24.8607, 67.0011, "Karachi, Pakistan", "Asia/Karachi"),
    "dhaka": (23.8103, 90.4125, "Dhaka, Bangladesh", "Asia/Dhaka"),
    "colombo": (6.9271, 79.8612, "Colombo, Sri Lanka", "Asia/Colombo"),
    "kathmandu": (27.7172, 85.3240, "Kathmandu, Nepal", "Asia/Kathmandu"),
    "tashkent": (41.2995, 69.2401, "Tashkent, Uzbekistan", "Asia/Tashkent"),
    "almaty": (43.2220, 76.8512, "Almaty, Kazakhstan", "Asia/Almaty"),
    "baghdad": (33.3152, 44.3661, "Baghdad, Iraq", "Asia/Baghdad"),
    "riyadh": (24.6877, 46.7219, "Riyadh, Saudi Arabia", "Asia/Riyadh"),
    "tel aviv": (32.0853, 34.7818, "Tel Aviv, Israel", "Asia/Jerusalem"),
    "jerusalem": (31.7683, 35.2137, "Jerusalem, Israel", "Asia/Jerusalem"),
    "beirut": (33.8938, 35.5018, "Beirut, Lebanon", "Asia/Beirut"),
    "amman": (31.9539, 35.9106, "Amman, Jordan", "Asia/Amman"),
    "tunis": (36.8190, 10.1658, "Tunis, Tunisia", "Africa/Tunis"),
    "casablanca": (33.5731, -7.5898, "Casablanca, Morocco", "Africa/Casablanca"),
    "lagos": (6.5244, 3.3792, "Lagos, Nigeria", "Africa/Lagos"),
    "addis ababa": (9.0320, 38.7469, "Addis Ababa, Ethiopia", "Africa/Addis_Ababa"),
    "accra": (5.5600, -0.2057, "Accra, Ghana", "Africa/Accra"),
    "lima": (-12.0464, -77.0428, "Lima, Peru", "America/Lima"),
    "bogota": (4.7110, -74.0721, "Bogotá, Colombia", "America/Bogota"),
    "santiago": (-33.4489, -70.6693, "Santiago, Chile", "America/Santiago"),
    "caracas": (10.4806, -66.9036, "Caracas, Venezuela", "America/Caracas"),
    "havana": (23.1136, -82.3666, "Havana, Cuba", "America/Havana"),
    "miami": (25.7617, -80.1918, "Miami, USA", "America/New_York"),
    "houston": (29.7604, -95.3698, "Houston, USA", "America/Chicago"),
    "phoenix": (33.4484, -112.0740, "Phoenix, USA", "America/Phoenix"),
    "seattle": (47.6062, -122.3321, "Seattle, USA", "America/Los_Angeles"),
    "san francisco": (37.7749, -122.4194, "San Francisco, USA", "America/Los_Angeles"),
    "washington": (38.9072, -77.0369, "Washington DC, USA", "America/New_York"),
    "boston": (42.3601, -71.0589, "Boston, USA", "America/New_York"),
    "atlanta": (33.7490, -84.3880, "Atlanta, USA", "America/New_York"),
    "lisbon": (38.7223, -9.1393, "Lisbon, Portugal", "Europe/Lisbon"),
    "barcelona": (41.3851, 2.1734, "Barcelona, Spain", "Europe/Madrid"),
    "milan": (45.4654, 9.1859, "Milan, Italy", "Europe/Rome"),
    "zurich": (47.3769, 8.5417, "Zurich, Switzerland", "Europe/Zurich"),
    "brussels": (50.8503, 4.3517, "Brussels, Belgium", "Europe/Brussels"),
    "copenhagen": (55.6761, 12.5683, "Copenhagen, Denmark", "Europe/Copenhagen"),
    "riga": (56.9460, 24.1059, "Riga, Latvia", "Europe/Riga"),
    "tallinn": (59.4370, 24.7536, "Tallinn, Estonia", "Europe/Tallinn"),
    "vilnius": (54.6872, 25.2797, "Vilnius, Lithuania", "Europe/Vilnius"),
    "minsk": (53.9045, 27.5615, "Minsk, Belarus", "Europe/Minsk"),
    "chisinau": (47.0105, 28.8638, "Chișinău, Moldova", "Europe/Chisinau"),
    "skopje": (41.9973, 21.4280, "Skopje, North Macedonia", "Europe/Skopje"),
    "belgrade": (44.8176, 20.4633, "Belgrade, Serbia", "Europe/Belgrade"),
    "sarajevo": (43.8563, 18.4131, "Sarajevo, Bosnia", "Europe/Sarajevo"),
    "zagreb": (45.8150, 15.9819, "Zagreb, Croatia", "Europe/Zagreb"),
    "ljubljana": (46.0569, 14.5058, "Ljubljana, Slovenia", "Europe/Ljubljana"),
    "podgorica": (42.4411, 19.2636, "Podgorica, Montenegro", "Europe/Podgorica"),
    "tirana": (41.3275, 19.8187, "Tirana, Albania", "Europe/Tirane"),
    "nicosia": (35.1856, 33.3823, "Nicosia, Cyprus", "Asia/Nicosia"),
}


def geocode(place: str) -> Tuple[float, float, str, str]:
    """Return (lat, lon, display_name, tz_name).

    Strategy:
    1. Built-in city cache (instant, no network)
    2. OpenCage API if OPENCAGE_API_KEY env var is set (free tier: 2500/day)
    3. Raise ValueError with instructions

    Note: Railway blocks all public Nominatim/Photon geocoders from cloud IPs.
    To enable geocoding for cities not in the cache, set OPENCAGE_API_KEY.
    Free key at https://opencagedata.com (2500 req/day free).
    """
    import urllib.request, urllib.parse, json as _json, os

    # 1) Check built-in cache (case-insensitive, strip whitespace)
    key = place.strip().lower()
    if key in _CITY_CACHE:
        lat, lon, display, tz = _CITY_CACHE[key]
        return lat, lon, display, tz

    # Also try matching just the city name if "City, Country" format given
    city_only = key.split(",")[0].strip()
    if city_only in _CITY_CACHE:
        lat, lon, display, tz = _CITY_CACHE[city_only]
        return lat, lon, display, tz

    # 2) OpenCage API (cloud-friendly, requires free API key)
    api_key = os.environ.get("OPENCAGE_API_KEY", "").strip()
    if api_key:
        try:
            q = urllib.parse.urlencode({"q": place, "key": api_key, "limit": 1, "no_annotations": 1, "language": "en"})
            req = urllib.request.Request(
                f"https://api.opencagedata.com/geocode/v1/json?{q}",
                headers={"User-Agent": "astro-api/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = _json.loads(r.read())
            if data.get("results"):
                res = data["results"][0]
                lat = float(res["geometry"]["lat"])
                lon = float(res["geometry"]["lng"])
                display = res.get("formatted", place)
                tz_info = res.get("annotations", {}).get("timezone", {})
                tz = tz_info.get("name") or _tf.timezone_at(lat=lat, lng=lon) or "UTC"
                return lat, lon, display, tz
        except Exception as e:
            raise ValueError(f"OpenCage geocoding error: {e}")

    # 3) Nothing worked — give actionable instructions
    cache_sample = ", ".join(list(_CITY_CACHE.keys())[:8]) + "..."
    raise ValueError(
        f"City '{place}' not found in cache. "
        f"Cached cities include: {cache_sample}. "
        f"To geocode any city, add a free OpenCage API key: "
        f"set OPENCAGE_API_KEY in Railway environment variables "
        f"(get key at https://opencagedata.com — 2500 requests/day free)."
    )


# ---------- Top-level entry points ----------

def calculate_chart_from_coords(
    date_str: str, time_str: str,
    lat: float, lon: float, tz_name: str,
    resolved_place: str = ""
) -> Dict:
    """Like calculate_chart() but accepts coordinates directly.

    Used when the frontend has already geocoded the city via /geocode.
    No geocoding happens here — coordinates are used as-is.
    """
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
    design_jd   = find_design_jd(jd_ut)
    design      = calc_planets(design_jd)

    analysis   = analyze(personality, design)
    design_utc = swe.revjul(design_jd)

    p_gate_set = {a.gate for a in personality}
    d_gate_set = {a.gate for a in design}
    integration = integration_condition(p_gate_set, d_gate_set)

    return {
        "input": {
            "date": date_str, "time": time_str,
            "place": resolved_place or f"{lat:.4f}, {lon:.4f}",
            "resolved_place": resolved_place or f"{lat:.4f}, {lon:.4f}",
            "lat": lat, "lon": lon,
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


def calculate_chart(date_str: str, time_str: str, place: str) -> Dict:
    """Inputs are strings: 'YYYY-MM-DD', 'HH:MM', 'City, Country'.

    Geocodes the place first, then computes the chart.
    Prefer calculate_chart_from_coords() when coordinates are already known.
    """
    lat, lon_loc, addr, tz_name = geocode(place)
    return calculate_chart_from_coords(date_str, time_str, lat, lon_loc, tz_name, addr)
