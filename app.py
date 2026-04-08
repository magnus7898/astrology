import os

# ── EPHE PATH ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, 'ephe')
os.makedirs(EPHE_PATH, exist_ok=True)
os.environ['SE_EPHE_PATH'] = EPHE_PATH

import swisseph as swe
swe.set_ephe_path(EPHE_PATH)

from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import math

app = Flask(__name__)
CORS(app, origins="*")

ZODIAC_SIGNS = [
    'ვერძი','კურო','ტყუპები','კირჩხიბი',
    'ლომი','ქალწული','სასწორი','მორიელი',
    'მშვილდოსანი','თხის რქა','მერწყული','თევზები'
]

def get_zodiac(degree):
    return ZODIAC_SIGNS[int(degree / 30) % 12]

def get_house(degree, cusps):
    for i in range(12):
        start = cusps[i]
        end   = cusps[(i + 1) % 12]
        if start <= end:
            if start <= degree < end:
                return i + 1
        else:
            if degree >= start or degree < end:
                return i + 1
    return 1

def deg_to_display(degree):
    d = int(degree % 30)
    minutes_decimal = (degree % 30 - d) * 60
    centesimal = round(minutes_decimal / 60 * 100)
    return d, centesimal

def to_jd(year, month, day, hour, minute, second, tz_name):
    """Convert local time to Julian Day (UTC)"""
    try:
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(datetime(year, month, day, hour, minute, second), is_dst=None)
        utc_t = local_dt.utctimetuple()
        utc_h = utc_t.tm_hour + utc_t.tm_min / 60 + utc_t.tm_sec / 3600
        return swe.julday(utc_t.tm_year, utc_t.tm_mon, utc_t.tm_mday, utc_h)
    except:
        utc_h = hour + minute / 60 + second / 3600
        return swe.julday(year, month, day, utc_h)

tf = TimezoneFinder()

ASPECTS_DEF = [
    {'name': 'შეერთება',       'angle': 0,   'orb': 8,  'sym': '☌', 'color': '#f9c646'},
    {'name': 'სექსტილი',       'angle': 60,  'orb': 6,  'sym': '⚹', 'color': '#30c890'},
    {'name': 'კვადრატი',       'angle': 90,  'orb': 8,  'sym': '□', 'color': '#e84040'},
    {'name': 'ტრინი',          'angle': 120, 'orb': 8,  'sym': '△', 'color': '#a078f0'},
    {'name': 'ოპოზიცია',       'angle': 180, 'orb': 8,  'sym': '☍', 'color': '#e89040'},
    {'name': 'კვინკუნქსი',     'angle': 150, 'orb': 3,  'sym': '⚻', 'color': '#9ba8b8'},
    {'name': 'ნახევარ-სექსტ.', 'angle': 30,  'orb': 2,  'sym': '⚺', 'color': '#7080a0'},
    {'name': 'ნახევარ-კვად.',  'angle': 45,  'orb': 2,  'sym': '∠', 'color': '#c06060'},
    {'name': 'სესკვიკვადრ.',   'angle': 135, 'orb': 2,  'sym': '⚼', 'color': '#c08040'},
    {'name': 'კვინტილი',       'angle': 72,  'orb': 2,  'sym': 'Q',  'color': '#50b0d0'},
    {'name': 'ბიკვინტილი',     'angle': 144, 'orb': 2,  'sym': 'bQ', 'color': '#60a0c0'},
]

MAIN_PLANETS_FOR_ASPECTS = [
    'მზე','მთვარე','მერკური','ვენერა','მარსი',
    'იუპიტერი','სატურნი','ურანი','ნეპტუნი','პლუტონი',
    'ქირონი','ჩრდ. კვანძი'
]

def calculate_aspects(planets):
    aspects = []
    names = [n for n in MAIN_PLANETS_FOR_ASPECTS if n in planets]
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            d1 = planets[p1]['degree']
            d2 = planets[p2]['degree']
            diff = abs(d1 - d2)
            if diff > 180:
                diff = 360 - diff
            for asp in ASPECTS_DEF:
                orb = abs(diff - asp['angle'])
                if orb <= asp['orb']:
                    aspects.append({
                        'p1': p1, 'p2': p2,
                        'type': asp['name'], 'sym': asp['sym'],
                        'color': asp['color'],
                        'orb': round(orb, 2), 'angle': asp['angle']
                    })
                    break
    aspects.sort(key=lambda x: x['orb'])
    return aspects

# ── LUNAR DAY CALCULATION ─────────────────────────────────────
# Pure elongation system: 360°/30 = 12° per lunar day
# New moon  (  0°) = day  1, 0%
# Quarter   ( 90°) = day  8, 50%
# Full moon (180°) = day 16, 0%
# Quarter   (270°) = day 23, 50%

def calc_lunar_day(jd_ut, tz_offset_hours=0.0):
    swe.set_ephe_path(EPHE_PATH)

    sun,  _ = swe.calc_ut(jd_ut, swe.SUN)
    moon, _ = swe.calc_ut(jd_ut, swe.MOON)

    # True elongation: angular distance Moon - Sun (0=New, 180=Full, 360=back to New)
    elong = (moon[0] - sun[0] + 360) % 360

    # Each lunar day = exactly 12° of elongation (360°/30 days)
    deg_per_day = 12.0

    age      = elong / deg_per_day          # 0..30
    lunar_day = int(age) + 1                # 1..30
    pct_elapsed   = round((age % 1) * 100, 2)
    pct_remaining = round(100 - pct_elapsed, 2)

    # Hours to next lunar day — Moon moves ~0.5°/hour relative to Sun
    # Relative speed Moon-Sun ≈ (360°/29.53days)/24h = 0.5085°/h
    rel_speed_deg_per_hour = 360.0 / (29.53058868 * 24.0)
    deg_to_next    = deg_per_day - (elong % deg_per_day)
    hours_to_next  = round(deg_to_next / rel_speed_deg_per_hour, 2)

    # Phase name
    if elong < 30:    phase = 'ახალი მთვარე'
    elif elong < 90:  phase = 'მზარდი'
    elif elong < 150: phase = 'I მეოთხედი'
    elif elong < 180: phase = 'მზარდი სავსე'
    elif elong < 210: phase = 'სავსე მთვარე'
    elif elong < 270: phase = 'კლება'
    elif elong < 330: phase = 'III მეოთხედი'
    else:             phase = 'კლება'

    return {
        'lunar_day':     lunar_day,
        'pct_elapsed':   pct_elapsed,
        'pct_remaining': pct_remaining,
        'hours_to_next': hours_to_next,
        'elongation':    round(elong, 2),
        'phase':         phase,
        'moon_deg':      round(moon[0], 4),
        'sun_deg':       round(sun[0], 4),
    }


# ── MOON PATH for a full day ──────────────────────────────────
def calc_moon_path(year, month, day, tz_name):
    """
    Returns moon degree at start and end of the given day (local midnight to midnight).
    Used for time-unknown mode to show where moon could be.
    """
    jd_start = to_jd(year, month, day, 0, 0, 0, tz_name)
    jd_end   = to_jd(year, month, day, 23, 59, 59, tz_name)
    moon_start, _ = swe.calc_ut(jd_start, swe.MOON)
    moon_end,   _ = swe.calc_ut(jd_end,   swe.MOON)
    return round(moon_start[0], 4), round(moon_end[0], 4)

# ── ROUTES ───────────────────────────────────────────────────

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Matrix Destiny API running'})

@app.route('/test')
def test():
    swe.set_ephe_path(EPHE_PATH)
    jd = swe.julday(1990, 1, 1, 12.0)
    result = {'ephe_path': EPHE_PATH, 'ephe_files': os.listdir(EPHE_PATH)}
    try:
        pos, _ = swe.calc_ut(jd, swe.CHIRON)
        result['chiron'] = round(pos[0], 2)
    except Exception as e:
        result['chiron_error'] = str(e)
    try:
        lunar = calc_lunar_day(jd)
        result['lunar_test'] = lunar
    except Exception as e:
        result['lunar_error'] = str(e)
    return jsonify(result)

@app.route('/geocode', methods=['POST'])
def geocode():
    try:
        city = request.json.get('city', '').strip()
        if not city:
            return jsonify({'error': 'City name is empty'}), 400

        # Primary: Nominatim via geopy
        try:
            geolocator = Nominatim(user_agent="astro-natal-chart-v3", timeout=10)
            location = geolocator.geocode(city, language='en', exactly_one=True)
        except Exception:
            location = None

        # Fallback: direct Nominatim HTTP call
        if not location:
            try:
                import urllib.request, urllib.parse, json as _json
                q = urllib.parse.urlencode({'q': city, 'format': 'json', 'limit': 1})
                req = urllib.request.Request(
                    f'https://nominatim.openstreetmap.org/search?{q}',
                    headers={'User-Agent': 'astro-natal-chart-v3'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    results = _json.loads(resp.read())
                if results:
                    r0 = results[0]
                    lat = float(r0['lat'])
                    lon = float(r0['lon'])
                    display = r0.get('display_name', city)
                    tz_name = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
                    return jsonify({'lat': lat, 'lon': lon, 'tz_name': tz_name, 'display': display})
            except Exception as e2:
                return jsonify({'error': f'City not found: {city} ({e2})'}), 404

        if not location:
            return jsonify({'error': 'City not found: ' + city}), 404

        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
        return jsonify({'lat': lat, 'lon': lon, 'tz_name': tz_name, 'display': location.address})

    except Exception as e:
        return jsonify({'error': 'Geocode error: ' + str(e)}), 500

@app.route('/lunar', methods=['POST'])
def lunar():
    """
    Calculate lunar day for a given date/time/location.
    Also returns moon path for time-unknown mode.
    """
    swe.set_ephe_path(EPHE_PATH)
    data     = request.json
    year     = int(data['year'])
    month    = int(data['month'])
    day      = int(data['day'])
    hour     = int(data.get('hour', 12))
    minute   = int(data.get('minute', 0))
    second   = int(data.get('second', 0))
    tz_name  = data.get('tz_name', 'UTC')
    time_unknown = data.get('time_unknown', False)

    jd = to_jd(year, month, day, hour, minute, second, tz_name)

    try:
        tz_offset = 0.0
        try:
            tz_obj = pytz.timezone(tz_name)
            import datetime as dt_mod
            local_dt = tz_obj.localize(dt_mod.datetime(year, month, day, hour, minute, second))
            tz_offset = local_dt.utcoffset().total_seconds() / 3600.0
        except: pass
        lunar_data = calc_lunar_day(jd, tz_offset)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    result = {'lunar': lunar_data}

    # For time-unknown: also return moon path (start and end of day)
    if time_unknown:
        try:
            moon_start, moon_end = calc_moon_path(year, month, day, tz_name)
            result['moon_path'] = {'start': moon_start, 'end': moon_end}
        except Exception as e:
            result['moon_path_error'] = str(e)

    return jsonify(result)

@app.route('/chart', methods=['POST'])
def chart():
    swe.set_ephe_path(EPHE_PATH)
    data    = request.json
    year    = int(data['year'])
    month   = int(data['month'])
    day     = int(data['day'])
    hour    = int(data['hour'])
    minute  = int(data['minute'])
    second  = int(data['second'])
    lat     = float(data['lat'])
    lon     = float(data['lon'])
    tz_name = data.get('tz_name', 'UTC')
    time_unknown = data.get('time_unknown', False)

    jd = to_jd(year, month, day, hour, minute, second, tz_name)
    planets = {}

    MAIN = {
        'მზე':      swe.SUN,
        'მთვარე':   swe.MOON,
        'მერკური':  swe.MERCURY,
        'ვენერა':   swe.VENUS,
        'მარსი':    swe.MARS,
        'იუპიტერი': swe.JUPITER,
        'სატურნი':  swe.SATURN,
        'ურანი':    swe.URANUS,
        'ნეპტუნი':  swe.NEPTUNE,
        'პლუტონი':  swe.PLUTO,
    }

    for name, pid in MAIN.items():
        pos, _ = swe.calc_ut(jd, pid)
        deg = pos[0]
        d, c = deg_to_display(deg)
        planets[name] = {
            'degree': round(deg, 4), 'sign': get_zodiac(deg),
            'sign_degree': d, 'centesimal': c,
            'retrograde': bool(pos[3] < 0) if len(pos) > 3 else False
        }

    try:
        pos, _ = swe.calc_ut(jd, swe.CHIRON)
        deg = pos[0]; d, c = deg_to_display(deg)
        planets['ქირონი'] = {'degree': round(deg,4), 'sign': get_zodiac(deg), 'sign_degree': d, 'centesimal': c, 'retrograde': bool(pos[3]<0)}
    except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_APOG)
        deg = pos[0]; d, c = deg_to_display(deg)
        planets['ლილიტი'] = {'degree': round(deg,4), 'sign': get_zodiac(deg), 'sign_degree': d, 'centesimal': c, 'retrograde': False}
    except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + 1181)
        deg = pos[0]; d, c = deg_to_display(deg)
        planets['თეთრი მთვარე'] = {'degree': round(deg,4), 'sign': get_zodiac(deg), 'sign_degree': d, 'centesimal': c, 'retrograde': False}
    except:
        try:
            pos, _ = swe.calc_ut(jd, 56)
            deg = pos[0]; d, c = deg_to_display(deg)
            planets['თეთრი მთვარე'] = {'degree': round(deg,4), 'sign': get_zodiac(deg), 'sign_degree': d, 'centesimal': c, 'retrograde': False}
        except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        nn = pos[0]; d, c = deg_to_display(nn)
        planets['ჩრდ. კვანძი'] = {'degree': round(nn,4), 'sign': get_zodiac(nn), 'sign_degree': d, 'centesimal': c, 'retrograde': True}
        sn = (nn + 180) % 360; d, c = deg_to_display(sn)
        planets['სამხ. კვანძი'] = {'degree': round(sn,4), 'sign': get_zodiac(sn), 'sign_degree': d, 'centesimal': c, 'retrograde': True}
    except: pass

    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = float(ascmc[0])
    mc  = float(ascmc[1])

    # Vertex and Fortune only when time is known
    if not time_unknown:
        try:
            vertex = float(ascmc[3])
            d, c = deg_to_display(vertex)
            planets['ვერტექსი'] = {'degree': round(vertex,4), 'sign': get_zodiac(vertex), 'sign_degree': d, 'centesimal': c, 'retrograde': False}
        except: pass

        try:
            sun_deg  = planets['მზე']['degree']
            moon_deg = planets['მთვარე']['degree']
            fortuna  = (asc + moon_deg - sun_deg) % 360
            d, c = deg_to_display(fortuna)
            planets['ბედის ვარსკვლავი'] = {'degree': round(fortuna,4), 'sign': get_zodiac(fortuna), 'sign_degree': d, 'centesimal': c, 'retrograde': False}
        except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + 3)
        deg = pos[0]; d, c = deg_to_display(deg)
        planets['იუნო'] = {'degree': round(deg,4), 'sign': get_zodiac(deg), 'sign_degree': d, 'centesimal': c, 'retrograde': bool(pos[3]<0) if len(pos)>3 else False}
    except: pass

    for name in planets:
        planets[name]['house'] = get_house(planets[name]['degree'], cusps)

    aspects = calculate_aspects(planets)

    # Include lunar day in chart response
    try:
        tz_offset = 0.0
        try:
            tz_obj = pytz.timezone(tz_name)
            import datetime as dt_mod
            local_dt = tz_obj.localize(dt_mod.datetime(year, month, day, hour, minute, second))
            tz_offset = local_dt.utcoffset().total_seconds() / 3600.0
        except: pass
        lunar_data = calc_lunar_day(jd, tz_offset)
    except Exception as e:
        lunar_data = None

    return jsonify({
        'planets':  planets,
        'houses':   [round(c, 4) for c in cusps],
        'asc':      round(asc, 4),
        'mc':       round(mc, 4),
        'asc_sign': get_zodiac(asc),
        'mc_sign':  get_zodiac(mc),
        'aspects':  aspects,
        'lunar':    lunar_data,
        'lat': lat, 'lon': lon, 'tz_name': tz_name
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
