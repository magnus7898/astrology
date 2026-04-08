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
    """
    Convert decimal degree to display format.
    Returns degrees and centesimal minutes (0-99 scale, not 0-59).
    e.g. 15.5 degrees = 15 degrees 50 centesimals
    """
    d = int(degree % 30)
    minutes_decimal = (degree % 30 - d) * 60  # real minutes 0-59
    centesimal = round(minutes_decimal / 60 * 100)  # convert to 0-99 scale
    return d, centesimal

def sign_degree_centesimal(degree):
    """Return degree within sign in centesimal format as float for display"""
    d, c = deg_to_display(degree)
    return float(f"{d}.{c:02d}")

tf = TimezoneFinder()

# Aspect definitions
ASPECTS_DEF = [
    {'name': 'კონიუნქცია',      'angle': 0,   'orb': 8,  'sym': '☌', 'color': '#f9c646'},
    {'name': 'სექსტილი',        'angle': 60,  'orb': 6,  'sym': '⚹', 'color': '#30c890'},
    {'name': 'კვადრატი',        'angle': 90,  'orb': 8,  'sym': '□', 'color': '#e84040'},
    {'name': 'ტრინი',           'angle': 120, 'orb': 8,  'sym': '△', 'color': '#a078f0'},
    {'name': 'ოპოზიცია',        'angle': 180, 'orb': 8,  'sym': '☍', 'color': '#e89040'},
    {'name': 'კვინკუნქსი',      'angle': 150, 'orb': 3,  'sym': '⚻', 'color': '#9ba8b8'},
    {'name': 'ნახევარ-სექსტილი','angle': 30,  'orb': 2,  'sym': '⚺', 'color': '#7080a0'},
    {'name': 'ნახევარ-კვადრატი','angle': 45,  'orb': 2,  'sym': '∠', 'color': '#c06060'},
    {'name': 'სესკვიკვადრატი',  'angle': 135, 'orb': 2,  'sym': '⚼', 'color': '#c08040'},
    {'name': 'ბიკვინტილი',      'angle': 144, 'orb': 2,  'sym': 'bQ', 'color': '#60a0c0'},
    {'name': 'კვინტილი',        'angle': 72,  'orb': 2,  'sym': 'Q',  'color': '#50b0d0'},
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
                        'p1':    p1,
                        'p2':    p2,
                        'type':  asp['name'],
                        'sym':   asp['sym'],
                        'color': asp['color'],
                        'orb':   round(orb, 2),
                        'angle': asp['angle']
                    })
                    break  # one aspect per pair
    # Sort by orb tightness
    aspects.sort(key=lambda x: x['orb'])
    return aspects

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Matrix Destiny API running'})

@app.route('/test')
def test():
    swe.set_ephe_path(EPHE_PATH)
    jd = swe.julday(1990, 1, 1, 12.0)
    result = {
        'ephe_path': EPHE_PATH,
        'ephe_files': os.listdir(EPHE_PATH)
    }
    try:
        pos, _ = swe.calc_ut(jd, swe.CHIRON)
        result['chiron'] = round(pos[0], 2)
    except Exception as e:
        result['chiron_error'] = str(e)
    try:
        pos, _ = swe.calc_ut(jd, 56)
        result['selena'] = round(pos[0], 2)
    except Exception as e:
        result['selena_error'] = str(e)
    return jsonify(result)

@app.route('/geocode', methods=['POST'])
def geocode():
    city = request.json.get('city')
    geolocator = Nominatim(user_agent="astro-chart-geo")
    location = geolocator.geocode(city)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
        return jsonify({
            'lat': lat,
            'lon': lon,
            'tz_name': tz_name,
            'display': location.address
        })
    return jsonify({'error': 'City not found'}), 404

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

    try:
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(datetime(year, month, day, hour, minute, second), is_dst=None)
        utc_t = local_dt.utctimetuple()
        utc_h = utc_t.tm_hour + utc_t.tm_min / 60 + utc_t.tm_sec / 3600
        y2, m2, d2 = utc_t.tm_year, utc_t.tm_mon, utc_t.tm_mday
    except:
        y2, m2, d2 = year, month, day
        utc_h = hour + minute / 60 + second / 3600

    jd = swe.julday(y2, m2, d2, utc_h)
    planets = {}

    # ── MAIN PLANETS ─────────────────────────────────────────
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
            'degree':      round(deg, 4),
            'sign':        get_zodiac(deg),
            'sign_degree': d,
            'centesimal':  c,
            'retrograde':  bool(pos[3] < 0) if len(pos) > 3 else False
        }

    # ── CHIRON ───────────────────────────────────────────────
    try:
        pos, _ = swe.calc_ut(jd, swe.CHIRON)
        deg = pos[0]
        d, c = deg_to_display(deg)
        planets['ქირონი'] = {
            'degree': round(deg, 4), 'sign': get_zodiac(deg),
            'sign_degree': d, 'centesimal': c,
            'retrograde': bool(pos[3] < 0)
        }
    except: pass

    # ── LILITH (Black Moon) ───────────────────────────────────
    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_APOG)
        deg = pos[0]
        d, c = deg_to_display(deg)
        planets['ლილიტი'] = {
            'degree': round(deg, 4), 'sign': get_zodiac(deg),
            'sign_degree': d, 'centesimal': c,
            'retrograde': False
        }
    except: pass

    # ── WHITE MOON SELENA (asteroid 1181) ────────────────────
    try:
        pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + 1181)
        deg = pos[0]
        d, c = deg_to_display(deg)
        planets['თეთრი მთვარე'] = {
            'degree': round(deg, 4), 'sign': get_zodiac(deg),
            'sign_degree': d, 'centesimal': c,
            'retrograde': bool(pos[3] < 0) if len(pos) > 3 else False
        }
    except:
        # fallback: try body 56 (Selena in some ephemeris versions)
        try:
            pos, _ = swe.calc_ut(jd, 56)
            deg = pos[0]
            d, c = deg_to_display(deg)
            planets['თეთრი მთვარე'] = {
                'degree': round(deg, 4), 'sign': get_zodiac(deg),
                'sign_degree': d, 'centesimal': c,
                'retrograde': False
            }
        except: pass

    # ── NODES ────────────────────────────────────────────────
    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        nn = pos[0]
        d, c = deg_to_display(nn)
        planets['ჩრდ. კვანძი'] = {
            'degree': round(nn, 4), 'sign': get_zodiac(nn),
            'sign_degree': d, 'centesimal': c,
            'retrograde': True
        }
        sn = (nn + 180) % 360
        d, c = deg_to_display(sn)
        planets['სამხ. კვანძი'] = {
            'degree': round(sn, 4), 'sign': get_zodiac(sn),
            'sign_degree': d, 'centesimal': c,
            'retrograde': True
        }
    except: pass

    # ── HOUSES & ANGLES ──────────────────────────────────────
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = float(ascmc[0])
    mc  = float(ascmc[1])

    # ── VERTEX ───────────────────────────────────────────────
    try:
        vertex = float(ascmc[3])  # index 3 = Vertex
        d, c = deg_to_display(vertex)
        planets['ვერტექსი'] = {
            'degree': round(vertex, 4), 'sign': get_zodiac(vertex),
            'sign_degree': d, 'centesimal': c,
            'retrograde': False
        }
    except: pass

    # ── PART OF FORTUNE ──────────────────────────────────────
    try:
        sun_deg  = planets['მზე']['degree']
        moon_deg = planets['მთვარე']['degree']
        # Daytime: ASC + Moon - Sun  /  Nighttime: ASC + Sun - Moon
        # Simplified daytime formula:
        fortuna = (asc + moon_deg - sun_deg) % 360
        d, c = deg_to_display(fortuna)
        planets['ბედის ვარსკვლავი'] = {
            'degree': round(fortuna, 4), 'sign': get_zodiac(fortuna),
            'sign_degree': d, 'centesimal': c,
            'retrograde': False
        }
    except: pass

    # ── ASSIGN HOUSES ────────────────────────────────────────
    for name in planets:
        planets[name]['house'] = get_house(planets[name]['degree'], cusps)

    # ── ASPECTS ──────────────────────────────────────────────
    aspects = calculate_aspects(planets)

    return jsonify({
        'planets':  planets,
        'houses':   [round(c, 4) for c in cusps],
        'asc':      round(asc, 4),
        'mc':       round(mc, 4),
        'asc_sign': get_zodiac(asc),
        'mc_sign':  get_zodiac(mc),
        'aspects':  aspects,
        'lat':      lat,
        'lon':      lon,
        'tz_name':  tz_name
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
