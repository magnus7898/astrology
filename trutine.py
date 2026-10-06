"""
Trutine of Hermes (ჰერმესის ტრუტინა) -- birth-time rectification.

Hermes / Ptolemy rule, reciprocal:
    Moon at conception (epoch)  = Ascendant at birth
    Ascendant at conception     = Moon at birth

Two schools are supported:

  mode="bailey"  (Prenatal Epoch, E.H. Bailey -- the standard modern form)
      Moon waxing at birth  -> epoch Moon = birth AC
      Moon waning at birth  -> epoch Moon = birth DC
      Gestation = 273 days  +/- (Moon's distance from that angle) / 13
          + when the birth Moon is above the horizon (houses 7-12)
          - when it is below the horizon (houses 1-6)
      Reciprocal: epoch AC or DC = birth Moon

  mode="classic" (Hermes as given by Ptolemy -- AC only)
      epoch Moon = birth AC, epoch AC = birth Moon

For every candidate birth moment in the search window the epoch is solved
exactly (the instant the Moon reaches the index angle near the expected
gestation), and the residual  epoch-angle minus birth-Moon  is driven to
zero by bisection. Each zero is a valid rectified birth time; they recur
roughly every 25 min (Bailey) / 50 min (classic), so the list is returned
ordered by distance from the time the user entered.

Angles only need AC/MC, which do not depend on the house system, so
Porphyry is used in the scan (it never fails at polar latitudes).
"""

from datetime import datetime, timedelta

import pytz
import swisseph as swe

MOON_MEAN = 13.176358          # deg/day, mean lunar motion (Bailey's "13")
GESTATION = 273.0              # days, Bailey's mean period

SIGNS_KA = ['ვერძი', 'კურო', 'ტყუპები', 'კირჩხიბი', 'ლომი', 'ქალწული',
            'სასწორი', 'მორიელი', 'მშვილდოსანი', 'თხის რქა', 'მერწყული', 'თევზები']


# ── small helpers ──────────────────────────────────────────────
def _w180(x):
    return (x + 180.0) % 360.0 - 180.0


def _sep(a, b):
    return abs(_w180(a - b))


def _fmt(deg):
    deg %= 360.0
    s = int(deg // 30)
    d = deg - s * 30
    di = int(d)
    m = int(round((d - di) * 60))
    if m == 60:
        di, m = di + 1, 0
    return {'deg': round(deg, 4), 'sign_ka': SIGNS_KA[s],
            'text': "%d°%02d' %s" % (di, m, SIGNS_KA[s])}


def _moon(jd):
    xx = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    return xx[0], xx[3]


def _sun(jd):
    return swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]


def _angles(jd, lat, lon):
    _, ascmc = swe.houses(jd, lat, lon, b'O')
    return float(ascmc[0]), float(ascmc[1])


def _moon_cross(target, jd_guess):
    """Instant nearest jd_guess (within +/-13.6 d) when the Moon is at target."""
    jd = jd_guess
    for _ in range(40):
        m, sp = _moon(jd)
        d = _w180(target - m)
        if abs(d) < 1e-7:
            break
        jd += d / (sp if sp > 9.0 else MOON_MEAN)
    return jd


def _local(jd, tz_name):
    y, mo, d, h = swe.revjul(jd)
    dt = datetime(y, mo, d, tzinfo=pytz.utc) + timedelta(hours=h)
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.utc
    dt = (dt + timedelta(microseconds=500000)).replace(microsecond=0)
    return dt.astimezone(tz)


# ── one birth-moment evaluation ────────────────────────────────
def _state(jd, lat, lon, mode):
    asc, mc = _angles(jd, lat, lon)
    moon, _ = _moon(jd)
    sun = _sun(jd)
    waxing = ((moon - sun) % 360.0) < 180.0
    above = ((moon - asc) % 360.0) >= 180.0        # houses 7..12
    if mode == 'classic':
        idx, idx_name = asc, 'AC'
    else:
        idx, idx_name = (asc, 'AC') if waxing else ((asc + 180.0) % 360.0, 'DC')
    dist = _sep(moon, idx)
    expected = GESTATION + (dist / MOON_MEAN if above else -dist / MOON_MEAN)
    jd_c = _moon_cross(idx, jd - expected)
    asc_c, mc_c = _angles(jd_c, lat, lon)
    return {'jd': jd, 'asc': asc, 'mc': mc, 'moon': moon, 'waxing': waxing,
            'above': above, 'idx': idx, 'idx_name': idx_name,
            'expected': expected, 'jd_c': jd_c, 'asc_c': asc_c, 'mc_c': mc_c}


def _resid(st, which):
    """Signed residual: epoch AC (or DC) minus birth Moon."""
    ang = st['asc_c'] if which == 'AC' else (st['asc_c'] + 180.0) % 360.0
    return _w180(ang - st['moon'])


# ── main ───────────────────────────────────────────────────────
def compute_trutine(jd0, lat, lon, tz_name='UTC', window=120, mode='bailey',
                    step_sec=30, limit=12):
    mode = 'classic' if mode == 'classic' else 'bailey'
    window = max(5, min(int(window), 720))
    whiches = ['AC'] if mode == 'classic' else ['AC', 'DC']
    n = int(window * 60 / step_sec)

    samples = [_state(jd0 + k * step_sec / 86400.0, lat, lon, mode)
               for k in range(-n, n + 1)]

    found = []
    for which in whiches:
        for s0, s1 in zip(samples, samples[1:]):
            # epoch jumped to another lunation, or index angle flipped AC<->DC:
            # the residual is discontinuous here, not a real root
            if abs(s1['jd_c'] - s0['jd_c']) > 1.0 or s0['idx_name'] != s1['idx_name']:
                continue
            f0, f1 = _resid(s0, which), _resid(s1, which)
            if abs(f1 - f0) > 90.0:                 # +/-180 wrap, not a root
                continue
            if f0 != 0.0 and (f0 < 0) == (f1 < 0):
                continue
            a, b, fa = s0['jd'], s1['jd'], f0
            for _ in range(25):
                m = (a + b) / 2.0
                fm = _resid(_state(m, lat, lon, mode), which)
                if (fm < 0) == (fa < 0):
                    a, fa = m, fm
                else:
                    b = m
            st = _state((a + b) / 2.0, lat, lon, mode)
            err = abs(_resid(st, which))
            if err < 0.05:
                found.append((st, which, err))

    # de-duplicate (AC and DC roots can land on the same second)
    found.sort(key=lambda t: t[0]['jd'])
    uniq = []
    for t in found:
        if not uniq or abs(t[0]['jd'] - uniq[-1][0]['jd']) * 86400 > 2:
            uniq.append(t)
    uniq.sort(key=lambda t: abs(t[0]['jd'] - jd0))

    out = []
    for st, which, err in uniq[:limit]:
        lt = _local(st['jd'], tz_name)
        ec = _local(st['jd_c'], tz_name)
        epoch_angle = st['asc_c'] if which == 'AC' else (st['asc_c'] + 180.0) % 360.0
        out.append({
            'year': lt.year, 'month': lt.month, 'day': lt.day,
            'hour': lt.hour, 'minute': lt.minute, 'second': lt.second,
            'time': lt.strftime('%H:%M:%S'),
            'date': lt.strftime('%d.%m.%Y'),
            'offset_min': round((st['jd'] - jd0) * 1440.0, 2),
            'asc': _fmt(st['asc']), 'mc': _fmt(st['mc']),
            'moon': _fmt(st['moon']),
            'moon_waxing': st['waxing'], 'moon_above': st['above'],
            'rule': 'ეპოქის ☽ = დაბადების ' + st['idx_name'],
            'reciprocal': 'ეპოქის ' + which + ' = დაბადების ☽',
            'epoch': {
                'date': ec.strftime('%d.%m.%Y'), 'time': ec.strftime('%H:%M'),
                'moon': _fmt(st['idx']), 'asc': _fmt(st['asc_c']),
                'angle_used': which, 'angle': _fmt(epoch_angle),
            },
            'gestation_days': round(st['jd'] - st['jd_c'], 2),
            'expected_days': round(st['expected'], 2),
            'residual_arcmin': round(err * 60.0, 3),
        })

    return {'method': mode, 'window_min': window,
            'entered_jd': round(jd0, 6), 'count': len(out), 'candidates': out}
