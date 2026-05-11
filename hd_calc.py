"""Human Design calculations."""

import csv
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

GATE_ORDER = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
GATE_START = 302.0
GATE_WIDTH = 360.0 / 64

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

CHANNELS: List[Tuple[int, int, str]] = [
    (1, 8, "შთაგონება"),
    (2, 14, "განმეორებითი რიტმი"),
    (3, 60, "მუტაცია"),
    (4, 63, "ლოგიკა"),
    (5, 15, "რიტმი"),
    (6, 59, "შეწყვილება"),
    (7, 31, "ალფა"),
    (9, 52, "კონცენტრაცია"),
    (10, 20, "გამოღვიძება"),
    (10, 34, "შესწავლა"),
    (10, 57, "სრულყოფილი ფორმა"),
    (11, 56, "ცნობისმოყვარეობა"),
    (12, 22, "გახსნილობა"),
    (13, 33, "უძღები"),
    (16, 48, "ტალღა"),
    (17, 62, "მიმღებლობა"),
    (18, 58, "განსჯა"),
    (19, 49, "სინთეზი"),
    (20, 34, "ქარიზმა"),
    (20, 57, "ნეიროტალღები"),
    (21, 45, "ფული"),
    (23, 43, "სტრუქტურირება"),
    (24, 61, "გაცნობიერება"),
    (25, 51, "ინიციაცია"),
    (26, 44, "დანებება"),
    (27, 50, "შენარჩუნება"),
    (28, 38, "ბრძოლა"),
    (29, 46, "აღმოჩენა"),
    (30, 41, "ცნობადობა"),
    (32, 54, "ტრანსფორმაცია"),
    (34, 57, "ძალაუფელა"),
    (35, 36, "გარდამავლობა"),
    (37, 40, "კავშირი"),
    (39, 55, "ემოციურობა"),
    (42, 53, "ჩამოყალიბება"),
    (47, 64, "აბსტრაქცია"),
]

MOTORS = {"Heart", "Sacral", "Solar Plexus", "Root"}

INTEGRATION_GATES = (10, 57, 34, 20)
INTEGRATION_STATE_VAL = {"None": 0, "A": 1, "B": 2, "Both": 3}


def _load_integration_csv() -> List[Dict]:
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
        next(reader, None)
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

_INTEGRATION_LOOKUP: Dict[tuple, int] = {}
for _row in INTEGRATION_CONDITIONS:
    s = _row["states"]
    _INTEGRATION_LOOKUP[(s["10"], s["57"], s["34"], s["20"])] = _row["n"]


def gate_state_label(gate: int, p_gates: set, d_gates: set) -> str:
    in_p = gate in p_gates
    in_d = gate in d_gates
    if in_p and in_d:  return "Both"
    if in_p:           return "A"
    if in_d:           return "B"
    return "None"


def gate_state(gate: int, p_gates: set, d_gates: set) -> int:
    in_p = gate in p_gates
    in_d = gate in d_gates
    if in_p and in_d: return 3
    if in_p:          return 1
    if in_d:          return 2
    return 0


def integration_condition(p_gates: set, d_gates: set) -> Dict:
    s10 = gate_state(10, p_gates, d_gates)
    s57 = gate_state(57, p_gates, d_gates)
    s34 = gate_state(34, p_gates, d_gates)
    s20 = gate_state(20, p_gates, d_gates)
    n = s10 * 64 + s57 * 16 + s34 * 4 + s20 + 1
    label = {0: "Not Design Not personal planet",
             1: "Personal planet",
             2: "Design",
             3: "Both"}
    return {
        "n": n,
        "states": {"10": label[s10], "57": label[s57],
                   "34": label[s34], "20": label[s20]},
    }


@dataclass
class Activation:
    planet: str
    glyph: str
    longitude: float
    gate: int
    line: int
    color: int
    tone: int
    base: int


def decompose(longitude: float) -> Tuple[int, int, int, int, int]:
    lon = longitude % 360
    offset = (lon - GATE_START) % 360
    gate_idx = int(offset // GATE_WIDTH)
    gate = GATE_ORDER[gate_idx]
    rem = offset - gate_idx * GATE_WIDTH
    line_w = GATE_WIDTH / 6
    line = int(rem // line_w) + 1
    rem -= (line - 1) * line_w
    color_w = line_w / 6
    color = int(rem // color_w) + 1
    rem -= (color - 1) * color_w
    tone_w = color_w / 6
    tone = int(rem // tone_w) + 1
    rem -= (tone - 1) * tone_w
    base_w = tone_w / 5
    base = min(5, int(rem // base_w) + 1)
    return gate, max(1, min(6, line)), max(1, min(6, color)), max(1, min(6, tone)), base


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
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    birth_sun, _ = swe.calc_ut(birth_jd_ut, swe.SUN, flags)
    target = (birth_sun[0] - 88) % 360
    jd = birth_jd_ut - 88.0
    for _ in range(50):
        sun, _ = swe.calc_ut(jd, swe.SUN, flags)
        speed = max(0.5, sun[3])
        diff = ((sun[0] - target + 540) % 360) - 180
        if abs(diff) < 1e-8:
            break
        jd -= diff / speed
    return jd


GATE_GIFTS = {
    1:"სიახლე", 2:"ორიენტაცია", 3:"ინოვაცია", 4:"გაგება", 5:"მოთმინება",
    6:"დიპლომატია", 7:"ლიდერობა", 8:"სტილი", 9:"ერთგულება", 10:"ბუნებრიობა",
    11:"იდეალიზმი", 12:"განრჩევა", 13:"თანაგრძნობა", 14:"კომპეტენტურობა",
    15:"მაგნეტიზმი", 16:"მრავალმხრიობა", 17:"შორსმჭვრეტელობა", 18:"მთლიანობა",
    19:"სენსიტიურობა", 20:"სიღრმე", 21:"ავტორიტეტი", 22:"გრაციოზულობა",
    23:"სიმარტივე", 24:"გამოგონება", 25:"მიღება", 26:"ეშმაკობა", 27:"ალტრუიზმი",
    28:"სისრულე", 29:"ვალდებულება", 30:"სიმსუბუქე", 31:"ლიდერობა", 32:"შენარჩუნება",
    33:"გაცნობიერება", 34:"ძალა", 35:"თავგადასავალი", 36:"ჰუმანურობა",
    37:"სინაზე", 38:"პატივი", 39:"დინამიზმი", 40:"გადაწყვეტილება", 41:"მოლოდინი",
    42:"განდგომა", 43:"ინსაიტი", 44:"სიფხიზლე", 45:"სინთეზი", 46:"სიხარული",
    47:"ტრანსმუტაცია", 48:"მდიდარი რესურსი", 49:"რევოლუცია", 50:"წონასწორობა",
    51:"ინიციატივა", 52:"თავშეკავება", 53:"ზრდა", 54:"სწრაფვა", 55:"თავისუფლება",
    56:"გამდიდრება", 57:"სიცხადე", 58:"სიცოცხლისუნარიანობა", 59:"გამჭვირვალობა",
    60:"რეალიზმი", 61:"შთაგონება", 62:"სიზუსტე", 63:"კვლევა", 64:"წარმოსახვა",
}

DIGESTION = {
    (1, "right"): "მადა — თანმიმდევრული",
    (1, "left"):  "მადა — მონაცვლეობითი",
    (2, "right"): "გემო — დახურული",
    (2, "left"):  "გემო — ღია",
    (3, "right"): "წყურვილი — ცხელი",
    (3, "left"):  "წყურვილი — ცივი",
    (4, "right"): "შეხება — მშვიდი",
    (4, "left"):  "შეხება — ნერვული",
    (5, "right"): "ხმა — მაღალი",
    (5, "left"):  "ხმა — დაბალი",
    (6, "right"): "სინათლე — პირდაპირი",
    (6, "left"):  "სინათლე — ირიბი",
}

SENSE = {
    1: "ყნოსვა",
    2: "გემო",
    3: "გარეგანი ხედვა",
    4: "შინაგანი ხედვა",
    5: "გრძნობა",
    6: "შეხება",
}

ENVIRONMENT = {
    (1, "right"): "მღვიმეები — შერჩევითი",
    (1, "left"):  "მღვიმეები — შერწყმული",
    (2, "right"): "ბაზრები — შიდა",
    (2, "left"):  "ბაზრები — გარე",
    (3, "right"): "სამზარეულო — გემო",
    (3, "left"):  "სამზარეულო — შეხება",
    (4, "right"): "მთები — დაბალი",
    (4, "left"):  "მთები — მაღალი",
    (5, "right"): "ველები — ბუნებრივი",
    (5, "left"):  "ველები — ხელოვნური",
    (6, "right"): "სანაპირო — ფოკუსირებული",
    (6, "left"):  "სანაპირო — გაფანტული",
}

MOTIVATION = {
    (1, "right"): "შიში — კონდიციონირება",
    (1, "left"):  "შიში — სურვილი",
    (2, "right"): "იმედი — კონდიციონირება",
    (2, "left"):  "იმედი — სურვილი",
    (3, "right"): "სურვილი — კონდიციონირება",
    (3, "left"):  "სურვილი — სურვილი",
    (4, "right"): "საჭიროება — კონდიციონირება",
    (4, "left"):  "საჭიროება — სურვილი",
    (5, "right"): "დანაშაული — კონდიციონირება",
    (5, "left"):  "დანაშაული — სურვილი",
    (6, "right"): "უდანაშაულობა — კონდიციონირება",
    (6, "left"):  "უდანაშაულობა — სურვილი",
}

PERSPECTIVE = {
    (1, "right"): "გადარჩენა — ფოკუსირებული",
    (1, "left"):  "გადარჩენა — პერიფერიული",
    (2, "right"): "მორალი — ფოკუსირებული",
    (2, "left"):  "მორალი — პერიფერიული",
    (3, "right"): "სენსიტიურობა — ფოკუსირებული",
    (3, "left"):  "სენსიტიურობა — პერიფერიული",
    (4, "right"): "სურვილი — ფოკუსირებული",
    (4, "left"):  "სურვილი — პერიფერიული",
    (5, "right"): "სურვილები — ფოკუსირებული",
    (5, "left"):  "სურვილები — პერიფერიული",
    (6, "right"): "გადაწყვეტილება — ფოკუსირებული",
    (6, "left"):  "გადაწყვეტილება — პერიფერიული",
}

PROFILE_NAMES = {
    "1/3": "1/3 — ცოდნისა და სიმართლის დამამკვიდრებელი",
    "1/4": "1/4 — ყოვლისმცოდნე მასწავლებელი",
    "2/4": "2/4 — ადვილი გენიოსი",
    "2/5": "2/5 — უნებლიე გმირი",
    "3/5": "3/5 — ცხოვრების დიდი ექსპერიმენტატორი",
    "3/6": "3/6 — ცოცხალი კონტრასტი",
    "4/1": "4/1 — ლაღი ცხოვრება",
    "4/2": "4/2 — მეგობრობის საფუძველი",
    "4/6": "4/6 — სამეფო ავტორიტეტი",
    "5/1": "5/1 — გამოწვევების გადამჭრელი",
    "5/2": "5/2 — თვითმოტივირებული გმირი",
    "6/2": "6/2 — სანიმუშო ადამიანი",
    "6/3": "6/3 — პასუხისმგებელი მოგზაური",
}


def get_definition(defined_centers: set, adj: Dict) -> str:
    if not defined_centers:
        return "განსაზღვრება არ არის"
    unvisited = set(defined_centers)
    groups = []
    while unvisited:
        start = next(iter(unvisited))
        group = set()
        stack = [start]
        while stack:
            n = stack.pop()
            if n in unvisited:
                unvisited.remove(n)
                group.add(n)
                for m in adj.get(n, set()):
                    if m in unvisited:
                        stack.append(m)
        groups.append(group)
    return {
        1: "ერთი მთლიანი განსაზღვრება",
        2: "გაყოფილი განსაზღვრება",
        3: "სამად გაყოფილი განსაზღვრება",
        4: "ოთხად გაყოფილი განსაზღვრება",
    }.get(len(groups), f"{len(groups)}-ჯერადი გაყოფა")


def analyze(personality: List[Activation], design: List[Activation]) -> Dict:
    p_gates = {a.gate for a in personality}
    d_gates = {a.gate for a in design}
    all_gates = p_gates | d_gates

    gate_sources: Dict[int, Dict[str, bool]] = {}
    for g in all_gates:
        gate_sources[g] = {"p": g in p_gates, "d": g in d_gates}

    defined_channels = []
    for a, b, name in CHANNELS:
        if a in all_gates and b in all_gates:
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

    defined_centers = set()
    for ch in defined_channels:
        ca = GATE_TO_CENTER.get(ch["gate_a"])
        cb = GATE_TO_CENTER.get(ch["gate_b"])
        if ca: defined_centers.add(ca)
        if cb: defined_centers.add(cb)

    sacral_def = "Sacral" in defined_centers
    throat_def = "Throat" in defined_centers

    adj: Dict[str, set] = {c: set() for c in CENTER_GATES}
    for ch in defined_channels:
        ca = GATE_TO_CENTER[ch["gate_a"]]
        cb = GATE_TO_CENTER[ch["gate_b"]]
        if ca != cb:
            adj[ca].add(cb)
            adj[cb].add(ca)

    def reachable_from(start: str) -> set:
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

    strategy_map = {
        "Manifestor": "To Inform",
        "Generator": "To Respond",
        "Manifesting Generator": "To Respond, then Inform",
        "Projector": "Wait for the Invitation",
        "Reflector": "Wait a Lunar Cycle (28 days)",
    }
    not_self = {
        "Manifestor": "რისხვა",
        "Generator": "იმედგაცრუება",
        "Manifesting Generator": "რისხვა და იმედგაცრუება",
        "Projector": "სიმწარე",
        "Reflector": "იმედგაცრუება",
    }
    signature = {
        "Manifestor": "სიმშვიდე",
        "Generator": "კმაყოფილება",
        "Manifesting Generator": "სიმშვიდე და კმაყოფილება",
        "Projector": "წარმატება",
        "Reflector": "სასიამოვნო გაკვირვება",
    }

    if "Solar Plexus" in defined_centers:
        authority = "ემოციური (მზის წნული)"
    elif sacral_def:
        authority = "საკრალური"
    elif "Spleen" in defined_centers:
        authority = "სპლენური (ელენთა)"
    elif "Heart" in defined_centers:
        authority = "ეგო (გული)"
    elif "G" in defined_centers:
        authority = "თვით-პროექცია (G)"
    elif hd_type == "Reflector":
        authority = "მთვარე"
    else:
        authority = "მენტალური / გარემო"

    p_sun_line = next(a.line for a in personality if a.planet == "Sun")
    d_sun_line = next(a.line for a in design if a.planet == "Sun")
    profile_key = f"{p_sun_line}/{d_sun_line}"
    profile = PROFILE_NAMES.get(profile_key, profile_key)

    p_sun   = next(a for a in personality if a.planet == "Sun")
    p_earth = next(a for a in personality if a.planet == "Earth")
    d_sun   = next(a for a in design if a.planet == "Sun")
    d_earth = next(a for a in design if a.planet == "Earth")
    cross = get_incarnation_cross_name(p_sun.gate, p_earth.gate, d_sun.gate, d_earth.gate, profile)

    return {
        "gate_sources": gate_sources,
        "defined_channels": defined_channels,
        "defined_centers": sorted(defined_centers),
        "type": hd_type,
        "strategy": strategy_map[hd_type],
        "not_self": not_self[hd_type],
        "signature": signature[hd_type],
        "authority": authority,
        "profile": profile,
        "definition": get_definition(defined_centers, adj),
        "incarnation_cross": cross,
    }


# ── GEOCODING ──────────────────────────────────────────────────
_tf = TimezoneFinder()


def _normalize(s: str) -> str:
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().strip()


def _load_geonames() -> dict:
    path = Path(__file__).parent / "cities500.txt"
    if not path.exists():
        return {}
    print("[geonames] loading cities500.txt ...", flush=True)
    db = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            row = line.rstrip('\n').split('\t')
            if len(row) < 18:
                continue
            try:
                name       = row[1]
                ascii_name = row[2]
                lat        = float(row[4])
                lon        = float(row[5])
                country    = row[8]
                tz         = row[17]
                if not tz or not name:
                    continue
                val = (lat, lon, f"{name}, {country}", tz)
                for key in {
                    name.lower(),
                    ascii_name.lower(),
                    _normalize(name),
                    f"{name.lower()}, {country.lower()}",
                    f"{ascii_name.lower()}, {country.lower()}",
                }:
                    if key and key not in db:
                        db[key] = val
            except (ValueError, IndexError):
                continue
    print(f"[geonames] {len(db)} keys loaded", flush=True)
    return db


_GEONAMES_DB: Dict[str, tuple] = _load_geonames()

_CITY_CACHE = {
    "tbilisi": (41.7151, 44.8271, "Tbilisi, Georgia", "Asia/Tbilisi"),
    "tbilisi, georgia": (41.7151, 44.8271, "Tbilisi, Georgia", "Asia/Tbilisi"),
    "kutaisi": (42.2679, 42.7181, "Kutaisi, Georgia", "Asia/Tbilisi"),
    "batumi": (41.6417, 41.6378, "Batumi, Georgia", "Asia/Tbilisi"),
    "rustavi": (41.5490, 44.9999, "Rustavi, Georgia", "Asia/Tbilisi"),
    "gori": (41.9851, 44.1086, "Gori, Georgia", "Asia/Tbilisi"),
    "zugdidi": (42.5082, 41.8707, "Zugdidi, Georgia", "Asia/Tbilisi"),
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
    "tokyo": (35.6762, 139.6503, "Tokyo, Japan", "Asia/Tokyo"),
    "beijing": (39.9042, 116.4074, "Beijing, China", "Asia/Shanghai"),
    "sydney": (-33.8688, 151.2093, "Sydney, Australia", "Australia/Sydney"),
}


def geocode(place: str) -> Tuple[float, float, str, str]:
    import urllib.request, urllib.parse, json as _json, os

    key = place.strip().lower()
    city_only = key.split(",")[0].strip()
    norm_key = _normalize(place)
    norm_city = _normalize(city_only)

    # 1. GeoNames database
    for k in (key, norm_key, city_only, norm_city):
        if k in _GEONAMES_DB:
            return _GEONAMES_DB[k]

    # 2. Fallback cache
    for k in (key, city_only):
        if k in _CITY_CACHE:
            lat, lon, display, tz = _CITY_CACHE[k]
            return lat, lon, display, tz

    # 3. OpenCage API
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
            raise ValueError(f"OpenCage error: {e}")

    cache_sample = ", ".join(list(_CITY_CACHE.keys())[:8]) + "..."
    raise ValueError(
        f"City '{place}' not found. "
        f"Add cities500.txt to app root for full world coverage, "
        f"or set OPENCAGE_API_KEY env var."
    )


# ── INCARNATION CROSSES ────────────────────────────────────────
_CROSS_RIGHT_ANGLE = {
    (1, 2, 7, 13): "სფინქსის მარჯვენა კუთხის ჯვარი 4",
    (2, 1, 13, 7): "სფინქსის მარჯვენა კუთხის ჯვარი 2",
    (3, 50, 60, 56): "კანონების მარჯვენა კუთხის ჯვარი",
    (4, 49, 23, 43): "განმარტების მარჯვენა კუთხის ჯვარი 3",
    (5, 35, 64, 63): "ცნობიერების მარჯვენა კუთხის ჯვარი 4",
    (6, 36, 12, 11): "ედემის მარჯვენა კუთხის ჯვარი 3",
    (7, 13, 2, 1): "სფინქსის მარჯვენა კუთხის ჯვარი 3",
    (8, 14, 30, 29): "გადადების მარჯვენა კუთხის ჯვარი 2",
    (9, 16, 40, 37): "დაგეგმვის მარჯვენა კუთხის ჯვარი 4",
    (10, 15, 46, 25): "სიყვარულის ჭურჭლის მარჯვენა კუთხის ჯვარი 4",
    (11, 12, 6, 36): "ედემის მარჯვენა კუთხის ჯვარი 4",
    (12, 11, 36, 6): "ედემის მარჯვენა კუთხის ჯვარი 2",
    (13, 7, 1, 2): "სფინქსის მარჯვენა კუთხის ჯვარი",
    (14, 8, 29, 30): "გადადების მარჯვენა კუთხის ჯვარი 4",
    (15, 10, 25, 46): "სიყვარულის ჭურჭლის მარჯვენა კუთხის ჯვარი 2",
    (16, 9, 37, 40): "დაგეგმვის მარჯვენა კუთხის ჯვარი 2",
    (17, 18, 58, 52): "სამსახურის მარჯვენა კუთხის ჯვარი",
    (18, 17, 52, 58): "სამსახურის მარჯვენა კუთხის ჯვარი 3",
    (19, 33, 44, 24): "ოთხი გზის მარჯვენა კუთხის ჯვარი 4",
    (20, 34, 55, 59): "მძინარე ფენიქსის მარჯვენა კუთხის ჯვარი 2",
    (21, 48, 38, 39): "დაძაბულობის მარჯვენა კუთხის ჯვარი",
    (22, 47, 26, 45): "მმართველობის მარჯვენა კუთხის ჯვარი",
    (23, 43, 49, 4): "განმარტების მარჯვენა კუთხის ჯვარი 2",
    (24, 44, 19, 33): "ოთხი გზის მარჯვენა კუთხის ჯვარი",
    (25, 46, 10, 15): "სიყვარულის ჭურჭლის მარჯვენა კუთხის ჯვარი",
    (26, 45, 47, 22): "მმართველობის მარჯვენა კუთხის ჯვარი 4",
    (27, 28, 41, 31): "მოულოდნელობის მარჯვენა კუთხის ჯვარი",
    (28, 27, 31, 41): "მოულოდნელობის მარჯვენა კუთხის ჯვარი 3",
    (29, 30, 8, 14): "გადადების მარჯვენა კუთხის ჯვარი 3",
    (30, 29, 14, 8): "გადადების მარჯვენა კუთხის ჯვარი",
    (31, 41, 27, 28): "მოულოდნელობის მარჯვენა კუთხის ჯვარი 2",
    (32, 42, 62, 61): "მაიას მარჯვენა კუთხის ჯვარი 3",
    (33, 19, 24, 44): "ოთხი გზის მარჯვენა კუთხის ჯვარი 2",
    (34, 20, 59, 55): "მძინარე ფენიქსის მარჯვენა კუთხის ჯვარი 4",
    (35, 5, 63, 64): "ცნობიერების მარჯვენა კუთხის ჯვარი 2",
    (36, 6, 11, 12): "ედემის მარჯვენა კუთხის ჯვარი",
    (37, 40, 9, 16): "დაგეგმვის მარჯვენა კუთხის ჯვარი",
    (38, 39, 48, 21): "დაძაბულობის მარჯვენა კუთხის ჯვარი 4",
    (39, 38, 21, 48): "დაძაბულობის მარჯვენა კუთხის ჯვარი 2",
    (40, 37, 16, 9): "დაგეგმვის მარჯვენა კუთხის ჯვარი 3",
    (41, 31, 28, 27): "მოულოდნელობის მარჯვენა კუთხის ჯვარი 4",
    (42, 32, 61, 62): "მაიას მარჯვენა კუთხის ჯვარი",
    (43, 23, 4, 49): "განმარტების მარჯვენა კუთხის ჯვარი 4",
    (44, 24, 33, 19): "ოთხი გზის მარჯვენა კუთხის ჯვარი 3",
    (45, 26, 22, 47): "მმართველობის მარჯვენა კუთხის ჯვარი 2",
    (46, 25, 15, 10): "სიყვარულის ჭურჭლის მარჯვენა კუთხის ჯვარი 3",
    (47, 22, 45, 26): "მმართველობის მარჯვენა კუთხის ჯვარი 3",
    (48, 21, 39, 38): "დაძაბულობის მარჯვენა კუთხის ჯვარი 3",
    (49, 4, 43, 23): "განმარტების მარჯვენა კუთხის ჯვარი",
    (50, 3, 56, 60): "კანონების მარჯვენა კუთხის ჯვარი 3",
    (51, 57, 54, 53): "შეღწევის მარჯვენა კუთხის ჯვარი",
    (52, 58, 17, 18): "სამსახურის მარჯვენა კუთხის ჯვარი 2",
    (53, 54, 51, 57): "შეღწევის მარჯვენა კუთხის ჯვარი 2",
    (54, 53, 57, 51): "შეღწევის მარჯვენა კუთხის ჯვარი 4",
    (55, 59, 34, 20): "მძინარე ფენიქსის მარჯვენა კუთხის ჯვარი",
    (56, 60, 3, 50): "კანონების მარჯვენა კუთხის ჯვარი 2",
    (57, 51, 53, 54): "შეღწევის მარჯვენა კუთხის ჯვარი 3",
    (58, 52, 18, 17): "სამსახურის მარჯვენა კუთხის ჯვარი 4",
    (59, 55, 20, 34): "მძინარე ფენიქსის მარჯვენა კუთხის ჯვარი 3",
    (60, 56, 50, 3): "კანონების მარჯვენა კუთხის ჯვარი 4",
    (61, 62, 32, 42): "მაიას მარჯვენა კუთხის ჯვარი 4",
    (62, 61, 42, 32): "მაიას მარჯვენა კუთხის ჯვარი 2",
    (63, 64, 5, 35): "ცნობიერების მარჯვენა კუთხის ჯვარი",
    (64, 63, 35, 5): "ცნობიერების მარჯვენა კუთხის ჯვარი 3",
}

_CROSS_JUXTAPOSITION = {
    (1, 2, 4, 49): "თვითგამოხატვის მიმდებარე კუთხის ჯვარი",
    (2, 1, 49, 4): "მძღოლის მიმდებარე კუთხის ჯვარი",
    (3, 50, 41, 31): "მუტაციის მიმდებარე კუთხის ჯვარი",
    (4, 49, 8, 14): "ფორმულირების მიმდებარე კუთხის ჯვარი",
    (5, 35, 47, 22): "ჩვევების მიმდებარე კუთხის ჯვარი",
    (6, 36, 15, 10): "კონფლიქტის მიმდებარე კუთხის ჯვარი",
    (7, 13, 23, 43): "ურთიერთქმედების მიმდებარე კუთხის ჯვარი",
    (8, 14, 55, 59): "წვლილის მიმდებარე კუთხის ჯვარი",
    (9, 16, 64, 63): "ფოკუსის მიმდებარე კუთხის ჯვარი",
    (10, 15, 18, 17): "ქცევის მიმდებარე კუთხის ჯვარი",
    (11, 12, 46, 25): "იდეების მიმდებარე კუთხის ჯვარი",
    (12, 11, 25, 46): "არტიკულაციის მიმდებარე კუთხის ჯვარი",
    (13, 7, 43, 23): "მოსმენის მიმდებარე კუთხის ჯვარი",
    (14, 8, 59, 55): "გაძლიერების მიმდებარე კუთხის ჯვარი",
    (15, 10, 17, 18): "უკიდურესობების მიმდებარე კუთხის ჯვარი",
    (16, 9, 63, 64): "ექსპერიმენტირების მიმდებარე კუთხის ჯვარი",
    (17, 18, 38, 39): "მოსაზრებების მიმდებარე კუთხის ჯვარი",
    (18, 17, 39, 38): "კორექტირების მიმდებარე კუთხის ჯვარი",
    (19, 33, 1, 2): "საჭიროების მიმდებარე კუთხის ჯვარი",
    (20, 34, 37, 40): "აწმყოს მიმდებარე კუთხის ჯვარი",
    (21, 48, 54, 53): "კონტროლის მიმდებარე კუთხის ჯვარი",
    (22, 47, 11, 12): "მადლის მიმდებარე კუთხის ჯვარი",
    (23, 43, 30, 29): "ასიმილაციის მიმდებარე კუთხის ჯვარი",
    (24, 44, 13, 7): "რაციონალიზაციის მიმდებარე კუთხის ჯვარი",
    (25, 46, 58, 52): "უმანკოების მიმდებარე კუთხის ჯვარი",
    (26, 45, 6, 36): "მატყუარას მიმდებარე კუთხის ჯვარი",
    (27, 28, 19, 33): "ზრუნვის მიმდებარე კუთხის ჯვარი",
    (28, 27, 33, 19): "რისკების მიმდებარე კუთხის ჯვარი",
    (29, 30, 20, 34): "ერთგულების მიმდებარე კუთხის ჯვარი",
    (30, 29, 34, 20): "ბედისწერის მიმდებარე კუთხის ჯვარი",
    (31, 41, 24, 44): "გავლენის მიმდებარე კუთხის ჯვარი",
    (32, 42, 56, 60): "კონსერვაციის მიმდებარე კუთხის ჯვარი",
    (33, 19, 2, 1): "განმარტოების მიმდებარე კუთხის ჯვარი",
    (34, 20, 40, 37): "ძალის მიმდებარე კუთხის ჯვარი",
    (35, 5, 22, 47): "გამოცდილების მიმდებარე კუთხის ჯვარი",
    (36, 6, 10, 15): "კრიზისის მიმდებარე კუთხის ჯვარი",
    (37, 40, 5, 35): "გარიგებების მიმდებარე კუთხის ჯვარი",
    (38, 39, 57, 51): "ოპოზიციის მიმდებარე კუთხის ჯვარი",
    (39, 38, 51, 57): "პროვოკაციის მიმდებარე კუთხის ჯვარი",
    (40, 37, 35, 5): "უარყოფის მიმდებარე კუთხის ჯვარი",
    (41, 31, 44, 24): "ფანტაზიის მიმდებარე კუთხის ჯვარი",
    (42, 32, 60, 56): "დასრულების მიმდებარე კუთხის ჯვარი",
    (43, 23, 29, 30): "ინსაიტის მიმდებარე კუთხის ჯვარი",
    (44, 24, 7, 13): "სიფხიზლის მიმდებარე კუთხის ჯვარი",
    (45, 26, 36, 6): "ფლობის მიმდებარე კუთხის ჯვარი",
    (46, 25, 52, 58): "იღბლიანობის მიმდებარე კუთხის ჯვარი",
    (47, 22, 12, 11): "ჩაგვრის მიმდებარე კუთხის ჯვარი",
    (48, 21, 53, 54): "სიღრმის მიმდებარე კუთხის ჯვარი",
    (49, 4, 14, 8): "პრინციპების მიმდებარე კუთხის ჯვარი",
    (50, 3, 31, 41): "ღირებულებების მიმდებარე კუთხის ჯვარი",
    (51, 57, 61, 62): "შოკის მიმდებარე კუთხის ჯვარი",
    (52, 58, 21, 48): "სიმშვიდის მიმდებარე კუთხის ჯვარი",
    (53, 54, 42, 32): "დასაწყისების მიმდებარე კუთხის ჯვარი",
    (54, 53, 32, 42): "ამბიციის მიმდებარე კუთხის ჯვარი",
    (55, 59, 9, 16): "განწყობების მიმდებარე კუთხის ჯვარი",
    (56, 60, 27, 28): "სტიმულაციის მიმდებარე კუთხის ჯვარი",
    (57, 51, 62, 61): "ინტუიციის მიმდებარე კუთხის ჯვარი",
    (58, 52, 48, 21): "სიცოცხლისუნარიანობის მიმდებარე კუთხის ჯვარი",
    (59, 55, 16, 9): "სტრატეგიის მიმდებარე კუთხის ჯვარი",
    (60, 56, 28, 27): "შეზღუდვის მიმდებარე კუთხის ჯვარი",
    (61, 62, 50, 3): "აზროვნების მიმდებარე კუთხის ჯვარი",
    (62, 61, 3, 50): "დეტალების მიმდებარე კუთხის ჯვარი",
    (63, 64, 26, 45): "ეჭვების მიმდებარე კუთხის ჯვარი",
    (64, 63, 45, 26): "დაბნეულობის მიმდებარე კუთხის ჯვარი",
}

_CROSS_LEFT_ANGLE = {
    (1, 2, 4, 49): "დაუმორჩილებლობის მარცხენა კუთხის ჯვარი 2",
    (2, 1, 49, 4): "დაუმორჩილებლობის მარცხენა კუთხის ჯვარი",
    (3, 50, 41, 31): "სურვილების მარცხენა კუთხის ჯვარი",
    (4, 49, 8, 14): "რევოლუციის მარცხენა კუთხის ჯვარი 2",
    (5, 35, 47, 22): "განცალკევების მარცხენა კუთხის ჯვარი 2",
    (6, 36, 15, 10): "მატერიალური პლანის მარცხენა კუთხის ჯვარი 2",
    (7, 13, 23, 43): "ნიღბების მარცხენა კუთხის ჯვარი 2",
    (8, 14, 55, 59): "გაურკვევლობის მარცხენა კუთხის ჯვარი",
    (9, 16, 64, 63): "იდენტიფიკაციის მარცხენა კუთხის ჯვარი 2",
    (10, 15, 18, 17): "პრევენციის მარცხენა კუთხის ჯვარი 2",
    (11, 12, 46, 25): "განათლების მარცხენა კუთხის ჯვარი 2",
    (12, 11, 25, 46): "განათლების მარცხენა კუთხის ჯვარი",
    (13, 7, 43, 23): "ნიღბების მარცხენა კუთხის ჯვარი",
    (14, 8, 59, 55): "გაურკვევლობის მარცხენა კუთხის ჯვარი 2",
    (15, 10, 17, 18): "პრევენციის მარცხენა კუთხის ჯვარი",
    (16, 9, 63, 64): "იდენტიფიკაციის მარცხენა კუთხის ჯვარი",
    (17, 18, 38, 39): "აღზევების მარცხენა კუთხის ჯვარი",
    (18, 17, 39, 38): "აღზევების მარცხენა კუთხის ჯვარი 2",
    (19, 33, 1, 2): "დახვეწის მარცხენა კუთხის ჯვარი 2",
    (20, 34, 37, 40): "დუალობის მარცხენა კუთხის ჯვარი",
    (21, 48, 54, 53): "მცდელობის მარცხენა კუთხის ჯვარი",
    (22, 47, 11, 12): "ინფორმირების მარცხენა კუთხის ჯვარი",
    (23, 43, 30, 29): "თავდადების მარცხენა კუთხის ჯვარი",
    (24, 44, 13, 7): "ინკარნაციის მარცხენა კუთხის ჯვარი",
    (25, 46, 58, 52): "განკურნების მარცხენა კუთხის ჯვარი",
    (26, 45, 6, 36): "კონფრონტაციის მარცხენა კუთხის ჯვარი 2",
    (27, 28, 19, 33): "ალიანსის მარცხენა კუთხის ჯვარი",
    (28, 27, 33, 19): "ალიანსის მარცხენა კუთხის ჯვარი 2",
    (29, 30, 20, 34): "ინდუსტრიის მარცხენა კუთხის ჯვარი 2",
    (30, 29, 34, 20): "ინდუსტრიის მარცხენა კუთხის ჯვარი",
    (31, 41, 24, 44): "ალფას მარცხენა კუთხის ჯვარი",
    (32, 42, 56, 60): "შეზღუდვის მარცხენა კუთხის ჯვარი 2",
    (33, 19, 2, 1): "დახვეწის მარცხენა კუთხის ჯვარი",
    (34, 20, 40, 37): "დუალობის მარცხენა კუთხის ჯვარი 2",
    (35, 5, 22, 47): "განცალკევების მარცხენა კუთხის ჯვარი",
    (36, 6, 10, 15): "მატერიალური პლანის მარცხენა კუთხის ჯვარი",
    (37, 40, 5, 35): "მიგრაციის მარცხენა კუთხის ჯვარი",
    (38, 39, 57, 51): "ინდივიდუალიზმის მარცხენა კუთხის ჯვარი 2",
    (39, 38, 51, 57): "ინდივიდუალიზმის მარცხენა კუთხის ჯვარი",
    (40, 37, 35, 5): "მიგრაციის მარცხენა კუთხის ჯვარი 2",
    (41, 31, 44, 24): "ალფას მარცხენა კუთხის ჯვარი 2",
    (42, 32, 60, 56): "შეზღუდვის მარცხენა კუთხის ჯვარი",
    (43, 23, 29, 30): "თავდადების მარცხენა კუთხის ჯვარი 2",
    (44, 24, 7, 13): "ინკარნაციის მარცხენა კუთხის ჯვარი 2",
    (45, 26, 36, 6): "კონფრონტაციის მარცხენა კუთხის ჯვარი",
    (46, 25, 52, 58): "განკურნების მარცხენა კუთხის ჯვარი 2",
    (47, 22, 12, 11): "ინფორმირების მარცხენა კუთხის ჯვარი 2",
    (48, 21, 53, 54): "მცდელობის მარცხენა კუთხის ჯვარი 2",
    (49, 4, 14, 8): "რევოლუციის მარცხენა კუთხის ჯვარი",
    (50, 3, 31, 41): "სურვილების მარცხენა კუთხის ჯვარი 2",
    (51, 57, 61, 62): "საყვირის მარცხენა კუთხის ჯვარი",
    (52, 58, 21, 48): "მოთხოვნების მარცხენა კუთხის ჯვარი",
    (53, 54, 42, 32): "ციკლების მარცხენა კუთხის ჯვარი",
    (54, 53, 32, 42): "ციკლების მარცხენა კუთხის ჯვარი 2",
    (55, 59, 9, 16): "სულის მარცხენა კუთხის ჯვარი",
    (56, 60, 27, 28): "ყურადღების გაფანტვის მარცხენა კუთხის ჯვარი",
    (57, 51, 62, 61): "საყვირის მარცხენა კუთხის ჯვარი 2",
    (58, 52, 48, 21): "მოთხოვნების მარცხენა კუთხის ჯვარი 2",
    (59, 55, 16, 9): "სულის მარცხენა კუთხის ჯვარი 2",
    (60, 56, 28, 27): "ყურადღების გაფანტვის მარცხენა კუთხის ჯვარი 2",
    (61, 62, 50, 3): "ობსკურაციის მარცხენა კუთხის ჯვარი 2",
    (62, 61, 3, 50): "ობსკურაციის მარცხენა კუთხის ჯვარი",
    (63, 64, 26, 45): "სამფლობელოს მარცხენა კუთხის ჯვარი",
    (64, 63, 45, 26): "სამფლობელოს მარცხენა კუთხის ჯვარი 2",
}


def get_incarnation_cross_name(p_sun, p_earth, d_sun, d_earth, profile="") -> str:
    key = (p_sun, p_earth, d_sun, d_earth)
    if profile in {"4/1", "4/2"} or "4/1" in profile or "4/2" in profile:
        name = _CROSS_JUXTAPOSITION.get(key, "")
    elif profile.split("/")[0] in {"5", "6"}:
        name = _CROSS_LEFT_ANGLE.get(key, "")
    else:
        name = _CROSS_RIGHT_ANGLE.get(key, "")
    if name:
        return f"{p_sun}/{p_earth} | {d_sun}/{d_earth} — {name}"
    return f"{p_sun}/{p_earth} | {d_sun}/{d_earth}"


# ── MAIN CALCULATION ───────────────────────────────────────────
def calculate_chart_from_coords(
    date_str: str, time_str: str,
    lat: float, lon: float, tz_name: str,
    resolved_place: str = ""
) -> Dict:
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

    analysis    = analyze(personality, design)
    design_utc  = swe.revjul(design_jd)

    p_gate_set = {a.gate for a in personality}
    d_gate_set = {a.gate for a in design}
    integration = integration_condition(p_gate_set, d_gate_set)

    # Variable calculations
    d_sun = next(a for a in design if a.planet == "Sun")
    d_sun_arrow = "left" if d_sun.line >= 4 else "right"
    digestion = DIGESTION.get((d_sun.color, d_sun_arrow), "")
    sense = SENSE.get(d_sun.tone, "")

    d_north_node = next(a for a in design if a.planet == "North Node")
    d_nn_arrow = "left" if d_north_node.line >= 4 else "right"
    environment = ENVIRONMENT.get((d_north_node.tone, d_nn_arrow), "")

    p_sun = next(a for a in personality if a.planet == "Sun")
    p_sun_arrow = "left" if p_sun.line >= 4 else "right"
    motivation = MOTIVATION.get((p_sun.color, p_sun_arrow), "")

    p_north_node = next(a for a in personality if a.planet == "North Node")
    p_nn_arrow = "left" if p_north_node.line >= 4 else "right"
    perspective = PERSPECTIVE.get((p_north_node.tone, p_nn_arrow), "")

    p_sun_gate = p_sun.gate
    all_active_gates = {a.gate for a in personality} | {a.gate for a in design}
    other_gifts = [
        f"{g} — {GATE_GIFTS[g]}"
        for g in sorted(all_active_gates)
        if g != p_sun_gate and g in GATE_GIFTS
    ]

    return {
        "input": {
            "date": date_str, "time": time_str,
            "place": resolved_place or f"{lat:.4f}, {lon:.4f}",
            "resolved_place": resolved_place or f"{lat:.4f}, {lon:.4f}",
            "lat": lat, "lon": lon,
            "tz": tz_name,
            "utc_time": utc_dt.strftime("%Y-%m-%d %H:%M UTC"),
        },
        "sun_gift": f"{p_sun_gate} — {GATE_GIFTS.get(p_sun_gate, '')}",
        "digestion": digestion,
        "sense": sense,
        "environment": environment,
        "motivation": motivation,
        "perspective": perspective,
        "other_gifts": other_gifts,
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
    lat, lon_loc, addr, tz_name = geocode(place)
    return calculate_chart_from_coords(date_str, time_str, lat, lon_loc, tz_name, addr)
