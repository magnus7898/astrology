# -*- coding: utf-8 -*-
"""
asteroid_nbody.py — free, local, accurate positions for ANY numbered asteroid.

Why: Swiss Ephemeris needs one data file per asteroid (se#####s.se1).
Astrodienst moved those files to Dropbox, so the old automatic download
URLs return 404, and asking NASA/JPL Horizons for every asteroid on every
chart is slow and rate-limited.

How:
  1. ONCE (first start, or never if asteroid_state.json is committed):
     one heliocentric state vector per asteroid at a fixed epoch, from
     JPL Horizons (or JPL SBDB elements as a fallback). One request per
     asteroid, ever.
  2. Locally, numerically integrate all of them together in the real
     solar system: Sun + Mercury..Neptune + Earth + Moon + Ceres, Pallas,
     Vesta, whose positions come from the Swiss Ephemeris files that are
     already in ephe/. (DOP853, 8th order, adaptive step.)
  3. A background thread fills a checkpoint table 1900-2100 (every 40
     days). A chart then only integrates <= 20 days from the nearest
     checkpoint: milliseconds.
  4. Geocentric apparent tropical position: light time, aberration,
     precession and nutation, the same reduction as Swiss Ephemeris.

Validated against the Swiss Ephemeris (JPL-based) files for Ceres,
Pallas, Juno, Vesta, Chiron and Pholus 1900-2100: worst error < 1 arcmin.
"""

import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request

import numpy as np
import swisseph as swe

try:
    from scipy.integrate import solve_ivp
    SCIPY_OK = True
except Exception:                       # pragma: no cover
    SCIPY_OK = False

EPHE_DIR = os.environ.get('SE_EPHE_PATH') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'ephe')
STATE_FILE = os.path.join(EPHE_DIR, 'asteroid_state.json')
CKPT_FILE = os.path.join(EPHE_DIR, 'asteroid_ckpt.npz')

EPOCH = 2461000.5                      # TDB, 2025-Nov-21 — all states here
SPAN = (2415020.5, 2488069.5)          # 1900-01-01 .. 2100-01-01 (TT)
STEP = 40.0                            # checkpoint spacing, days
K2 = 0.000295912208285591100           # GM_sun, AU^3/day^2
C_AU_D = 173.1446326846693             # speed of light, AU/day
LOG = []                               # diagnostics (see /api/asteroids/diag)

FL = (swe.FLG_SWIEPH | swe.FLG_HELCTR | swe.FLG_J2000 | swe.FLG_NONUT |
      swe.FLG_TRUEPOS | swe.FLG_NOABERR | swe.FLG_NOGDEFL | swe.FLG_XYZ)

# perturbers: Swiss Ephemeris body, mass as a fraction of the Sun (DE440)
PERT = [(swe.MERCURY, 1 / 6023600.0), (swe.VENUS, 1 / 408523.719),
        (swe.EARTH, 1 / 332946.0487),
        (swe.MOON, 1 / (332946.0487 * 81.30056907)),
        (swe.MARS, 1 / 3098703.59), (swe.JUPITER, 1 / 1047.348644),
        (swe.SATURN, 1 / 3497.901768), (swe.URANUS, 1 / 22902.981613),
        (swe.NEPTUNE, 1 / 19412.237346),
        (swe.CERES, 4.72e-10), (swe.PALLAS, 1.03e-10), (swe.VESTA, 1.30e-10)]
PERT_NUM = {swe.CERES: 1, swe.PALLAS: 2, swe.VESTA: 4}
GMP = np.array([m for _, m in PERT]) * K2


# ─────────────────────────── initial states ───────────────────────────
_STATES = {}          # num -> [x,y,z,vx,vy,vz] at EPOCH (AU, AU/day, J2000 ecl)
_lock = threading.RLock()


def _load_states():
    try:
        with open(STATE_FILE) as f:
            d = json.load(f)
        if abs(float(d.get('epoch', 0)) - EPOCH) < 1e-6:
            for k, v in d['states'].items():
                _STATES[int(k)] = [float(x) for x in v]
    except Exception:
        pass


def _save_states():
    try:
        os.makedirs(EPHE_DIR, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({'epoch': EPOCH, 'frame': 'heliocentric ecliptic J2000, AU, AU/day, TDB',
                       'source': 'JPL Horizons / SBDB',
                       'states': {str(k): v for k, v in sorted(_STATES.items())}}, f)
    except Exception as e:
        LOG.append('save states: %s' % e)


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': 'magnus-astro/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def _horizons_state(num):
    """Heliocentric J2000-ecliptic state at EPOCH from JPL Horizons."""
    for cmd in ("'DES=%d;'" % num, "'%d;'" % num):
        q = {'format': 'text', 'COMMAND': cmd, 'OBJ_DATA': 'NO',
             'MAKE_EPHEM': 'YES', 'EPHEM_TYPE': 'VECTORS',
             'CENTER': "'500@10'", 'REF_PLANE': "'ECLIPTIC'",
             'REF_SYSTEM': "'ICRF'", 'VEC_TABLE': "'2'",
             'VEC_CORR': "'NONE'", 'TIME_TYPE': "'TDB'",
             'TLIST': '%.6f' % EPOCH, 'CSV_FORMAT': 'YES',
             'OUT_UNITS': "'AU-D'"}
        try:
            txt = _get('https://ssd.jpl.nasa.gov/api/horizons.api?' + urllib.parse.urlencode(q))
        except Exception as e:
            LOG.append('horizons %d: %s' % (num, e))
            continue
        if '$$SOE' not in txt:
            continue
        line = txt.split('$$SOE', 1)[1].split('$$EOE', 1)[0].strip().splitlines()
        if not line:
            continue
        vals = []
        for p in line[0].split(','):
            try:
                vals.append(float(p.strip()))
            except ValueError:
                pass
        # JDTDB, X, Y, Z, VX, VY, VZ  (calendar text column is skipped)
        if len(vals) >= 7 and abs(vals[0] - EPOCH) < 1e-4:
            return vals[1:7]
    return None


def elements_to_state(a, e, inc, om, w, ma, epoch, t):
    """Osculating heliocentric elements (deg) -> state at time t."""
    i, Om, wr = math.radians(inc), math.radians(om), math.radians(w)
    n = math.sqrt(K2 / abs(a) ** 3)
    M = math.radians(ma) + n * (t - epoch)
    M = math.fmod(M, 2 * math.pi)
    E = M if e < 0.8 else math.pi
    for _ in range(60):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    cE, sE = math.cos(E), math.sin(E)
    fac = math.sqrt(1 - e * e)
    xp, yp = a * (cE - e), a * fac * sE
    r = a * (1 - e * cE)
    vxp, vyp = -a * n * sE * a / r, a * n * fac * cE * a / r
    cw, sw, cO, sO, ci, si = (math.cos(wr), math.sin(wr), math.cos(Om),
                              math.sin(Om), math.cos(i), math.sin(i))
    R = [[cw * cO - sw * sO * ci, -sw * cO - cw * sO * ci],
         [cw * sO + sw * cO * ci, -sw * sO + cw * cO * ci],
         [sw * si, cw * si]]
    return [R[k][0] * xp + R[k][1] * yp for k in range(3)] + \
           [R[k][0] * vxp + R[k][1] * vyp for k in range(3)]


def _sbdb_state(num):
    """Fallback: JPL SBDB osculating elements -> state at EPOCH."""
    try:
        d = json.loads(_get('https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=%d' % num))
        orb = d['orbit']
        el = {x['name']: float(x['value']) for x in orb['elements'] if x.get('value') is not None}
        ep = float(orb['epoch'])
        if el['e'] >= 1:
            return None
        s0 = elements_to_state(el['a'], el['e'], el['i'], el['om'], el['w'], el['ma'], ep, ep)
        if abs(ep - EPOCH) < 0.01:
            return s0
        # move from the SBDB epoch to ours with the full force model
        y = _integrate(np.array([s0]), ep, EPOCH, [num])
        return list(y[0]) if y is not None else None
    except Exception as e:
        LOG.append('sbdb %d: %s' % (num, e))
        return None


_FAILED = {}          # num -> time of the last failed fetch (retry after 1 h)


def ensure_states(nums, workers=8, deadline=None):
    """Make sure every requested asteroid has an epoch state (network, once).
    Returns the asteroids still without a state. With `deadline` (seconds)
    it stops waiting then; unfinished fetches complete in the background."""
    now = time.time()
    with _lock:
        todo = [n for n in nums if n not in _STATES
                and now - _FAILED.get(n, 0) > 3600]
    if todo:
        from concurrent.futures import ThreadPoolExecutor, wait

        def one(n):
            s = _horizons_state(n) or _sbdb_state(n)
            with _lock:
                if s:
                    _STATES[n] = s
                    _save_states()
                else:
                    _FAILED[n] = time.time()

        ex = ThreadPoolExecutor(max_workers=workers)
        futs = [ex.submit(one, n) for n in todo]
        wait(futs, timeout=deadline)
        ex.shutdown(wait=False)
    return [n for n in nums if n not in _STATES]


# ─────────────────────────── integrator ───────────────────────────
def _pert_pos(t):
    return np.array([swe.calc(t, b, FL)[0][:3] for b, _ in PERT])


def _integrate(Y0, t0, t1, nums, t_eval=None, rtol=1e-11):
    """Integrate states Y0 (N,6) from t0 to t1 (TT/TDB, days)."""
    if not SCIPY_OK:
        raise RuntimeError('scipy not installed')
    N = len(Y0)
    mask = np.ones((N, len(PERT)))
    for j, (b, _) in enumerate(PERT):
        if b in PERT_NUM:
            for i, n in enumerate(nums):
                if n == PERT_NUM[b]:
                    mask[i, j] = 0.0
    g = GMP[None, :] * mask

    def f(t, y):
        s = y.reshape(N, 6)
        r = s[:, :3]
        P = _pert_pos(t)
        d = P[None, :, :] - r[:, None, :]
        dn = np.linalg.norm(d, axis=2) ** 3
        dn = np.where(mask > 0, dn, 1.0)
        pn = np.linalg.norm(P, axis=1) ** 3
        acc = -K2 * r / (np.linalg.norm(r, axis=1) ** 3)[:, None]
        acc += np.einsum('np,npk->nk', g / dn, d) - g @ (P / pn[:, None])
        return np.hstack([s[:, 3:], acc]).ravel()

    if t1 == t0:
        return Y0.copy() if t_eval is None else [Y0.copy()]
    sol = solve_ivp(f, (t0, t1), np.asarray(Y0, float).ravel(), method='DOP853',
                    rtol=rtol, atol=1e-14, t_eval=t_eval)
    if not sol.success:
        LOG.append('integrate: ' + sol.message)
        return None
    if t_eval is not None:
        return [sol.y[:, k].reshape(N, 6) for k in range(sol.y.shape[1])]
    return sol.y[:, -1].reshape(N, 6)


# ───────────────────── checkpoint table (background) ─────────────────────
_CK = {'nums': [], 't': None, 'Y': None}      # Y: (T, N, 6)
_WARM = {'running': False, 'done': False, 'seconds': None}


def _grid():
    back = np.arange(EPOCH, SPAN[0] - STEP, -STEP)
    fwd = np.arange(EPOCH, SPAN[1] + STEP, STEP)
    return back, fwd


def _load_ckpt():
    try:
        z = np.load(CKPT_FILE)
        if abs(float(z['epoch']) - EPOCH) < 1e-6:
            _CK.update(nums=[int(x) for x in z['nums']], t=z['t'], Y=z['Y'])
            _WARM['done'] = True
    except Exception:
        pass


def _groups(nums):
    """Split fast NEAs (small perihelion) from the rest so that their tiny
    steps do not slow down the others."""
    slow, fast = [], []
    for n in nums:
        s = np.array(_STATES[n])
        r, v2 = np.linalg.norm(s[:3]), float(np.dot(s[3:], s[3:]))
        a = 1.0 / (2.0 / r - v2 / K2)
        h = np.cross(s[:3], s[3:])
        e = math.sqrt(max(0.0, 1 - float(np.dot(h, h)) / (K2 * a))) if a > 0 else 1.0
        q = a * (1 - e) if a > 0 else r
        (fast if q < 1.3 else slow).append(n)
    return [g for g in (slow, fast) if g]


def build_checkpoints(nums):
    """Integrate every asteroid 1900-2100 and keep a state every STEP days."""
    nums = sorted(n for n in nums if n in _STATES)
    if not nums:
        return
    tic = time.time()
    back, fwd = _grid()
    t_all = np.concatenate([back[::-1], fwd[1:]])
    Y = np.zeros((len(t_all), len(nums), 6))
    for grp in _groups(nums):
        idx = [nums.index(n) for n in grp]
        Y0 = np.array([_STATES[n] for n in grp])
        yb = _integrate(Y0, EPOCH, float(back[-1]), grp, t_eval=back)
        yf = _integrate(Y0, EPOCH, float(fwd[-1]), grp, t_eval=fwd)
        if yb is None or yf is None:
            continue
        seq = yb[::-1] + yf[1:]
        for k, yk in enumerate(seq):
            Y[k, idx, :] = yk
    with _lock:
        _CK.update(nums=nums, t=t_all, Y=Y)
    _WARM['seconds'] = round(time.time() - tic, 1)
    try:
        np.savez_compressed(CKPT_FILE, epoch=EPOCH, nums=np.array(nums), t=t_all, Y=Y)
    except Exception as e:
        LOG.append('save ckpt: %s' % e)


def warm(nums):
    """Fetch any missing epoch states and (re)build the checkpoint table
    in a background thread. Safe to call on every request."""
    now = time.time()
    with _lock:
        need_states = [n for n in nums if n not in _STATES
                       and now - _FAILED.get(n, 0) > 3600]
        need_ck = (not _WARM['done']) or any(
            n in _STATES and n not in _CK['nums'] for n in nums)
        if _WARM['running'] or not (need_states or need_ck):
            return
        _WARM['running'] = True

    def work():
        try:
            ensure_states(nums)
            build_checkpoints(sorted(set(_CK['nums']) | set(nums)))
            _WARM['done'] = True
        except Exception as e:
            LOG.append('warm: %s' % e)
        finally:
            _WARM['running'] = False

    threading.Thread(target=work, daemon=True).start()


def states_at(nums, t):
    """Heliocentric J2000 states at TT time t for the given asteroids."""
    nums = [n for n in nums if n in _STATES]
    out = {}
    if not nums:
        return out
    with _lock:
        ck_nums, ck_t, ck_Y = list(_CK['nums']), _CK['t'], _CK['Y']
    from_ck = [n for n in nums if n in ck_nums and ck_t is not None
               and ck_t[0] - STEP <= t <= ck_t[-1] + STEP]
    rest = [n for n in nums if n not in from_ck]
    if from_ck:
        k = int(np.argmin(np.abs(ck_t - t)))
        for grp in _groups(from_ck):
            Y0 = np.array([ck_Y[k, ck_nums.index(n)] for n in grp])
            y = _integrate(Y0, float(ck_t[k]), t, grp)
            if y is not None:
                out.update({n: y[i] for i, n in enumerate(grp)})
    if rest:                               # table not ready yet: from epoch
        for grp in _groups(rest):
            Y0 = np.array([_STATES[n] for n in grp])
            y = _integrate(Y0, EPOCH, t, grp, rtol=1e-10)
            if y is not None:
                out.update({n: y[i] for i, n in enumerate(grp)})
    return out


# ───────────────────── apparent geocentric position ─────────────────────
def _prec_matrix(t):
    """J2000 mean equator -> mean equator of date (IAU 1976)."""
    T = (t - 2451545.0) / 36525.0
    z_ = (2306.2181 * T + 0.30188 * T * T + 0.017998 * T ** 3) / 3600.0
    zz = (2306.2181 * T + 1.09468 * T * T + 0.018203 * T ** 3) / 3600.0
    th = (2004.3109 * T - 0.42665 * T * T - 0.041833 * T ** 3) / 3600.0
    cz, sz = math.cos(math.radians(z_)), math.sin(math.radians(z_))
    cZ, sZ = math.cos(math.radians(zz)), math.sin(math.radians(zz))
    ct, st = math.cos(math.radians(th)), math.sin(math.radians(th))
    return np.array([[cz * ct * cZ - sz * sZ, -sz * ct * cZ - cz * sZ, -st * cZ],
                     [cz * ct * sZ + sz * cZ, -sz * ct * sZ + cz * cZ, -st * sZ],
                     [cz * st, -sz * st, ct]])


EPS0 = math.radians(23.4392911111)


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def apparent(state, t):
    """(lon, lat, dist, speed_deg_per_day) tropical, apparent, of date."""
    nut = swe.calc(t, swe.ECL_NUT)[0]       # true eps, mean eps, dpsi, deps
    eps_m, dpsi = math.radians(nut[1]), nut[2]
    M = _rx(-eps_m) @ _prec_matrix(t) @ _rx(EPS0)   # J2000 ecl -> ecl of date
    E = np.array(swe.calc(t, swe.EARTH, FL | swe.FLG_SPEED)[0])

    def lonlat(dt):
        tt = t + dt
        Et = E[:3] + E[3:] * dt
        r, v = state[:3] + state[3:] * dt, state[3:]
        g = r - Et
        for _ in range(3):                    # light time
            tau = np.linalg.norm(g) / C_AU_D
            g = r - v * tau - Et
        dist = np.linalg.norm(g)
        g = g / dist + E[3:] / C_AU_D         # annual aberration
        x, y, z = M @ g
        lon = (math.degrees(math.atan2(y, x)) + dpsi) % 360.0
        lat = math.degrees(math.asin(z / math.sqrt(x * x + y * y + z * z)))
        return lon, lat, dist

    l0, b0, d0 = lonlat(0.0)
    l1, _, _ = lonlat(0.5)
    sp = ((l1 - l0 + 540.0) % 360.0 - 180.0) / 0.5
    return l0, b0, d0, sp


def positions(nums, jd_ut):
    """Apparent tropical lon/lat/dist/speed for asteroids, keyed by number.
    Asteroids without an epoch state yet are simply absent."""
    t = jd_ut + swe.deltat(jd_ut)
    st = states_at(nums, t)
    return {n: apparent(np.asarray(s), t) for n, s in st.items()}


# the asteroid list of asteroid.html (Ceres..Vesta, Chiron, Pholus come
# from seas_18.se1 and need no integration)
DEFAULT_IDS = [10, 433, 16, 5, 6, 7, 8, 9, 11, 12, 14, 15, 17, 18, 19, 24, 36, 40,
               42, 46, 52, 57, 65, 76, 78, 97, 99, 120, 129, 130, 168, 201, 216,
               306, 446, 511, 584, 617, 624, 704, 1036, 1566, 1862, 1866, 2001,
               3200, 7066, 8405, 10199, 90377, 90482, 136199, 136472, 50000,
               225088, 1181, 1437, 94, 107, 164, 174, 175, 196, 259, 451, 491,
               532, 664, 1009, 4179, 2000, 3174, 3753, 4341, 174567]


def prebuild(ids=None):
    """Docker build step: fetch the epoch states and build the 1900-2100
    table into the image, so the server never waits at runtime.
        RUN python -c "import asteroid_nbody as A; A.prebuild()" || true
    """
    swe.set_ephe_path(EPHE_DIR)
    ids = list(ids or DEFAULT_IDS)
    tic = time.time()
    failed = ensure_states(ids)
    build_checkpoints(sorted(_STATES))
    print('asteroid_nbody: %d states, %d failed %s, table %s, %.0fs'
          % (len(_STATES), len(failed), failed[:10],
             None if _CK['Y'] is None else _CK['Y'].shape, time.time() - tic))
    for line in LOG[-10:]:
        print('  ', line)


def status():
    return {'states': len(_STATES), 'checkpoints': None if _CK['t'] is None else len(_CK['t']),
            'asteroids_in_table': len(_CK['nums']), 'warming': _WARM['running'],
            'ready': _WARM['done'], 'build_seconds': _WARM['seconds'],
            'scipy': SCIPY_OK, 'epoch': EPOCH, 'log': LOG[-20:]}


_load_states()
_load_ckpt()
