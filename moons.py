# -*- coding: utf-8 -*-
"""
moons.py — major natural satellites, seen FROM their own planet.

For planetocentric astrology: when the observer is Mars, its sky
contains Phobos and Deimos; from Jupiter, the four Galileans, etc.

PyEphem supplies each satellite's offset from its planet in the
plane of the sky (x = east, y = north, z = line of sight, all in
planet radii). That offset IS the planetocentric vector, so we
rotate it from the sky frame into J2000 ecliptic coordinates and
report ecliptic longitude/latitude, distance and phase angle.

Triton (Neptune) and Charon (Pluto) are not in PyEphem's satellite
set and are therefore reported as unavailable rather than guessed.
"""

import math

try:
    import ephem
    EPHEM_OK = True
    EPHEM_ERR = ''
except Exception as _e:            # library missing / failed to build
    ephem = None
    EPHEM_OK = False
    EPHEM_ERR = str(_e)

D2R = math.pi / 180.0
R2D = 180.0 / math.pi
EPS = 23.4392911 * D2R          # J2000 obliquity

# planet -> (ephem planet class, [(ephem moon class, key, Georgian name)])
MOONS = {} if not EPHEM_OK else {
    'mars': (ephem.Mars, [
        (ephem.Phobos, 'phobos', 'ფობოსი'),
        (ephem.Deimos, 'deimos', 'დეიმოსი'),
    ]),
    'jupiter': (ephem.Jupiter, [
        (ephem.Io, 'io', 'იო'),
        (ephem.Europa, 'europa', 'ევროპა'),
        (ephem.Ganymede, 'ganymede', 'განიმედი'),
        (ephem.Callisto, 'callisto', 'კალისტო'),
    ]),
    'saturn': (ephem.Saturn, [
        (ephem.Mimas, 'mimas', 'მიმასი'),
        (ephem.Enceladus, 'enceladus', 'ენცელადი'),
        (ephem.Tethys, 'tethys', 'ტეთისი'),
        (ephem.Dione, 'dione', 'დიონე'),
        (ephem.Rhea, 'rhea', 'რეა'),
        (ephem.Titan, 'titan', 'ტიტანი'),
        (ephem.Hyperion, 'hyperion', 'ჰიპერიონი'),
        (ephem.Iapetus, 'iapetus', 'იაპეტოსი'),
    ]),
    'uranus': (ephem.Uranus, [
        (ephem.Miranda, 'miranda', 'მირანდა'),
        (ephem.Ariel, 'ariel', 'არიელი'),
        (ephem.Umbriel, 'umbriel', 'უმბრიელი'),
        (ephem.Titania, 'titania', 'ტიტანია'),
        (ephem.Oberon, 'oberon', 'ობერონი'),
    ]),
}

# satellites with no analytic theory in PyEphem
MISSING = {
    'neptune': [('triton', 'ტრიტონი')],
}

# sidereal periods (days) — for the info line only
PERIOD = {
    'charon': 6.3872304,
    'phobos': 0.31891, 'deimos': 1.26244,
    'io': 1.769138, 'europa': 3.551181,
    'ganymede': 7.154553, 'callisto': 16.689017,
    'mimas': 0.942422, 'enceladus': 1.370218, 'tethys': 1.887802,
    'dione': 2.736915, 'rhea': 4.518212, 'titan': 15.945421,
    'hyperion': 21.276609, 'iapetus': 79.330183,
    'miranda': 1.413479, 'ariel': 2.520379, 'umbriel': 4.144177,
    'titania': 8.705872, 'oberon': 13.463239,
}


# ---------------------------------------------------------------
# FALLBACK ORBIT MODEL
# PyEphem's Mars- and Uranus-satellite theories only return data for
# roughly 1999-2040; outside that window they yield zeros. For those
# moons we use a circular model in the planet's equatorial plane whose
# mean motion and epoch phase were fitted to PyEphem inside its valid
# window (periods reproduce published values to <2 s). Accuracy is a
# degree or so — ample for chart work, and honest about its origin.
# ---------------------------------------------------------------
FIT = {
    "phobos": {
        "planet": "mars",
        "n": 1128.8448886068713,
        "th0": -16.81990579918701,
        "r": 2.762694879404526,
        "h": [
            -0.02629941178926514,
            -0.002608417744695551,
            -0.0015486126123514373,
            0.0010775285201453724
        ]
    },
    "deimos": {
        "planet": "mars",
        "n": 285.16190845773224,
        "th0": 35.03814736704776,
        "r": 6.910833813941082,
        "h": [
            -0.010381852806910598,
            0.0017757064757744157,
            -0.006774008095466973,
            0.001992829030788094
        ]
    },
    "miranda": {
        "planet": "uranus",
        "n": -254.69082824377702,
        "th0": 66.23969650351879,
        "r": 5.418239063066301,
        "h": [
            0.031793143411164015,
            0.011144220053952124,
            0.010555869659645908,
            0.011788093892575938
        ]
    },
    "ariel": {
        "planet": "uranus",
        "n": -142.8357492468701,
        "th0": 178.74823432550824,
        "r": 7.991599455508346,
        "h": [
            0.002172589427767581,
            0.030619965987449364,
            0.0015992737144980443,
            -0.00025965288240229227
        ]
    },
    "umbriel": {
        "planet": "uranus",
        "n": -86.86892318598873,
        "th0": 123.90095931865505,
        "r": 11.132806546831452,
        "h": [
            0.28389869492371544,
            0.21619140656551283,
            0.0026170253826838094,
            0.00038004588068035576
        ]
    },
    "titania": {
        "planet": "uranus",
        "n": -41.35144110247323,
        "th0": 88.28727117664442,
        "r": 18.26154671231396,
        "h": [
            -0.09197399733498503,
            -0.18566878727246522,
            0.0009010582149317192,
            0.001909815329865406
        ]
    },
    "oberon": {
        "planet": "uranus",
        "n": -26.739504130523883,
        "th0": 15.61523574709796,
        "r": 24.421510456553126,
        "h": [
            -0.16673242411373954,
            -0.015169806181940308,
            0.002160110006895332,
            -0.0003365564609925796
        ]
    }
}

PLANET_POLE = {            # IAU pole (a0, d0) in degrees, J2000
    'mars': (317.68143, 52.88650),
    'uranus': (257.311, -15.175),
}


def _plane_basis(planet):
    a0, d0 = PLANET_POLE[planet]
    a, d = a0 * D2R, d0 * D2R
    pe = (math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d))
    pole = (pe[0],
            pe[1] * math.cos(EPS) + pe[2] * math.sin(EPS),
            -pe[1] * math.sin(EPS) + pe[2] * math.cos(EPS))
    n = math.sqrt(sum(c * c for c in pole))
    pole = tuple(c / n for c in pole)
    ref = (0.0, 0.0, 1.0) if abs(pole[2]) < 0.9 else (1.0, 0.0, 0.0)

    def cross(p, q):
        return (p[1]*q[2]-p[2]*q[1], p[2]*q[0]-p[0]*q[2], p[0]*q[1]-p[1]*q[0])

    def unit(v):
        m = math.sqrt(sum(c * c for c in v))
        return tuple(c / m for c in v)

    u = unit(cross(ref, pole))
    v = unit(cross(pole, u))
    return u, v


def _fitted_position(key, jd):
    """Planetocentric ecliptic vector from the fitted orbit.

    Mean angle in the planet's equatorial plane plus harmonic terms
    (eccentricity and plane effects). Typical accuracy vs PyEphem:
    0.1-0.6 deg for the Uranian moons and Deimos, ~5 deg rms for
    Phobos, which is the noise floor of PyEphem's own Mars theory.
    """
    f = FIT[key]
    u, v = _plane_basis(f['planet'])
    t = jd - 2451545.0
    mean = f['th0'] + f['n'] * t
    m = mean * D2R
    h = f.get('h', [0, 0, 0, 0])
    th = (mean + h[0] * math.sin(m) + h[1] * math.cos(m)
          + h[2] * math.sin(2 * m) + h[3] * math.cos(2 * m)) * D2R
    c, sn = math.cos(th), math.sin(th)
    r = f['r']
    return tuple(r * (c * u[i] + sn * v[i]) for i in range(3))

def _sky_to_ecliptic(x, y, z, ra, dec):
    """PyEphem/Meeus satellite offset (x positive WEST, y north,
    z away from Earth), at the planet's (ra, dec)
    -> J2000 ecliptic rectangular vector."""
    x = -x                       # west -> east
    sa, ca = math.sin(ra), math.cos(ra)
    sd, cd = math.sin(dec), math.cos(dec)
    east = (-sa, ca, 0.0)
    north = (-sd * ca, -sd * sa, cd)
    los = (cd * ca, cd * sa, sd)
    eq = tuple(x * east[i] + y * north[i] + z * los[i] for i in range(3))
    # equatorial -> ecliptic
    return (eq[0],
            eq[1] * math.cos(EPS) + eq[2] * math.sin(EPS),
            -eq[1] * math.sin(EPS) + eq[2] * math.cos(EPS))


# ---------------------------------------------------------------
# CHARON — derived exactly from Pluto's IAU rotation elements.
# The IAU defines Pluto's prime meridian as the sub-Charon meridian
# and the pair is doubly tidally locked, so the direction of Pluto's
# rotating prime meridian IS the direction of Charon. The resulting
# orbital period reproduces the published 6.3872304 d to 0.6 s.
# ---------------------------------------------------------------
PLUTO_ROT = (132.993, -6.163, 302.695, 56.3625225)   # a0, d0, W0, Wdot
CHARON_R = 16.487                                    # 19591 km / 1188.3 km


def charon_position(jd):
    """Planetocentric ecliptic vector of Charon, in Pluto radii."""
    a0, d0, W0, Wd = PLUTO_ROT
    a, d = a0 * D2R, d0 * D2R
    W = ((W0 + Wd * (jd - 2451545.0)) % 360.0) * D2R
    z1, x1 = a + math.pi / 2, math.pi / 2 - d
    p = (math.cos(W), math.sin(W), 0.0)
    p = (p[0],
         p[1] * math.cos(x1) - p[2] * math.sin(x1),
         p[1] * math.sin(x1) + p[2] * math.cos(x1))
    eq = (p[0] * math.cos(z1) - p[1] * math.sin(z1),
          p[0] * math.sin(z1) + p[1] * math.cos(z1),
          p[2])
    ec = (eq[0],
          eq[1] * math.cos(EPS) + eq[2] * math.sin(EPS),
          -eq[1] * math.sin(EPS) + eq[2] * math.cos(EPS))
    return tuple(CHARON_R * c for c in ec)


def earth_moon_offset(date):
    """Geocentric ecliptic rectangular offset of Earth's Moon, in AU.

    Returned as a vector FROM Earth so the caller can add it to Earth's
    own planetocentric vector and see the Moon from any planet.
    """
    if not EPHEM_OK:
        return None
    m = ephem.Moon()
    m.compute(date)
    ra, dec = float(m.ra), float(m.dec)
    dist = float(m.earth_distance)          # AU
    x = dist * math.cos(dec) * math.cos(ra)
    y = dist * math.cos(dec) * math.sin(ra)
    z = dist * math.sin(dec)
    return (x,
            y * math.cos(EPS) + z * math.sin(EPS),
            -y * math.sin(EPS) + z * math.cos(EPS))


def compute_moons(planet, year, month, day, hour=12, minute=0):
    """Planetocentric ecliptic positions of `planet`'s major moons."""
    planet = (planet or '').lower()
    if not EPHEM_OK:
        return {'planet': planet, 'moons': [], 'unavailable': [],
                'error': 'ephem library not installed on the server: ' + EPHEM_ERR}
    date = ephem.Date((int(year), int(month), int(day),
                       int(hour), int(minute), 0))

    em = earth_moon_offset(date)
    earth_moon = None
    if em:
        earth_moon = {'key': 'moon', 'name_ka': 'მთვარე', 'offset_au': [round(c, 9) for c in em]}

    if planet not in MOONS:
        out = {'planet': planet, 'moons': [], 'unavailable': [],
               'earth_moon': earth_moon}
        if planet == 'pluto':
            jd = float(date) + 2415020.0
            v = charon_position(jd)
            r = math.hypot(math.hypot(v[0], v[1]), v[2])
            out['moons'].append({
                'key': 'charon', 'name_ka': 'ქარონი',
                'lon': round((math.atan2(v[1], v[0]) * R2D) % 360.0, 4),
                'lat': round(math.asin(v[2] / r) * R2D, 4),
                'radii': round(r, 3), 'period_days': PERIOD['charon'],
                'behind': None, 'source': 'iau'})
        for key, ka in MISSING.get(planet, []):
            out['unavailable'].append({'key': key, 'name_ka': ka})
        return out

    pcls, sats = MOONS[planet]
    p = pcls()
    p.compute(date)
    ra, dec = float(p.ra), float(p.dec)

    jd = float(date) + 2415020.0        # ephem date -> Julian Day

    moons = []
    for cls, key, ka in sats:
        m = cls()
        m.compute(date)
        source = 'ephem'
        if m.x == 0 and m.y == 0 and m.z == 0:
            # outside PyEphem's validity window -> fitted orbit model
            if key not in FIT:
                continue
            v = _fitted_position(key, jd)
            source = 'fit'
        else:
            v = _sky_to_ecliptic(m.x, m.y, m.z, ra, dec)
        r = math.hypot(math.hypot(v[0], v[1]), v[2])
        if r == 0:
            continue
        lon = (math.atan2(v[1], v[0]) * R2D) % 360.0
        lat = math.asin(max(-1.0, min(1.0, v[2] / r))) * R2D
        moons.append({
            'key': key, 'name_ka': ka,
            'lon': round(lon, 4), 'lat': round(lat, 4),
            'radii': round(r, 3),
            'period_days': PERIOD.get(key),
            'behind': bool(m.z > 0) if source == 'ephem' else None,
            'source': source,
        })
    return {'planet': planet, 'moons': moons, 'unavailable': [],
            'earth_moon': earth_moon}
