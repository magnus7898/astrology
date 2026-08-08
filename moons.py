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
import ephem

D2R = math.pi / 180.0
R2D = 180.0 / math.pi
EPS = 23.4392911 * D2R          # J2000 obliquity

# planet -> (ephem planet class, [(ephem moon class, key, Georgian name)])
MOONS = {
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
    'pluto':   [('charon', 'ქარონი')],
}

# sidereal periods (days) — for the info line only
PERIOD = {
    'phobos': 0.31891, 'deimos': 1.26244,
    'io': 1.769138, 'europa': 3.551181,
    'ganymede': 7.154553, 'callisto': 16.689017,
    'mimas': 0.942422, 'enceladus': 1.370218, 'tethys': 1.887802,
    'dione': 2.736915, 'rhea': 4.518212, 'titan': 15.945421,
    'hyperion': 21.276609, 'iapetus': 79.330183,
    'miranda': 1.413479, 'ariel': 2.520379, 'umbriel': 4.144177,
    'titania': 8.705872, 'oberon': 13.463239,
}


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


def compute_moons(planet, year, month, day, hour=12, minute=0):
    """Planetocentric ecliptic positions of `planet`'s major moons."""
    planet = (planet or '').lower()
    date = ephem.Date((int(year), int(month), int(day),
                       int(hour), int(minute), 0))

    if planet not in MOONS:
        out = {'planet': planet, 'moons': [], 'unavailable': []}
        for key, ka in MISSING.get(planet, []):
            out['unavailable'].append({'key': key, 'name_ka': ka})
        return out

    pcls, sats = MOONS[planet]
    p = pcls()
    p.compute(date)
    ra, dec = float(p.ra), float(p.dec)

    moons = []
    for cls, key, ka in sats:
        m = cls()
        m.compute(date)
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
            'behind': bool(m.z > 0),     # farther than the planet
        })
    return {'planet': planet, 'moons': moons, 'unavailable': []}
