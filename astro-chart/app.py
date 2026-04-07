
import os

# ── EPHE PATH (CRITICAL) ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, 'ephe')

os.makedirs(EPHE_PATH, exist_ok=True)
os.environ['SE_EPHE_PATH'] = EPHE_PATH

import swisseph as swe
swe.set_ephe_path(EPHE_PATH)

# ── IMPORTS ─────────────────────────────────────────────────────
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS   # 👈 ADD THIS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz


app = Flask(__name__)
CORS(app)

# ── CONSTANTS ───────────────────────────────────────────────────
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

tf = TimezoneFinder()

# ── ROUTES ──────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('astro.html')  # ✅ renamed

@app.route('/astro')
def astro():
    return render_template('astro.html')

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

    data = request.json

    year    = int(data['year'])
    month   = int(data['month'])
    day     = int(data['day'])
    hour    = int(data['hour'])
    minute  = int(data['minute'])
    second  = int(data['second'])
    lat     = float(data['lat'])
    lon     = float(data['lon'])
    tz_name = data.get('tz_name', 'UTC')

    # ── TIMEZONE FIX ─────────────────────────────────────────
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

    # ── PLANETS ─────────────────────────────────────────────
    MAIN = {
        'მზე': swe.SUN,
        'მთვარე': swe.MOON,
        'მერკური': swe.MERCURY,
        'ვენერა': swe.VENUS,
        'მარსი': swe.MARS,
        'იუპიტერი': swe.JUPITER,
        'სატურნი': swe.SATURN,
        'ურანი': swe.URANUS,
        'ნეპტუნი': swe.NEPTUNE,
        'პლუტონი': swe.PLUTO,
    }

    for name, pid in MAIN.items():
        pos, _ = swe.calc_ut(jd, pid)
        deg = pos[0]

        planets[name] = {
            'degree': round(deg, 4),
            'sign': get_zodiac(deg),
            'sign_degree': round(deg % 30, 2),
            'retrograde': bool(pos[3] < 0) if len(pos) > 3 else False
        }

    # ── EXTRA OBJECTS ───────────────────────────────────────
    try:
        pos, _ = swe.calc_ut(jd, swe.CHIRON)
        deg = pos[0]
        planets['ქირონი'] = {
            'degree': round(deg, 4),
            'sign': get_zodiac(deg),
            'sign_degree': round(deg % 30, 2),
            'retrograde': bool(pos[3] < 0)
        }
    except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_APOG)
        deg = pos[0]
        planets['ლილიტი'] = {
            'degree': round(deg, 4),
            'sign': get_zodiac(deg),
            'sign_degree': round(deg % 30, 2),
            'retrograde': False
        }
    except: pass

    try:
        pos, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        nn = pos[0]
        planets['ჩრდ. კვანძი'] = {
            'degree': round(nn, 4),
            'sign': get_zodiac(nn),
            'sign_degree': round(nn % 30, 2),
            'retrograde': True
        }
        sn = (nn + 180) % 360
        planets['სამხ. კვანძი'] = {
            'degree': round(sn, 4),
            'sign': get_zodiac(sn),
            'sign_degree': round(sn % 30, 2),
            'retrograde': True
        }
    except: pass

    # ── HOUSES ─────────────────────────────────────────────
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')

    asc = float(ascmc[0])
    mc  = float(ascmc[1])

    for name in planets:
        planets[name]['house'] = get_house(planets[name]['degree'], cusps)

    return jsonify({
        'planets': planets,
        'houses': [round(c, 4) for c in cusps],
        'asc': round(asc, 4),
        'mc': round(mc, 4),
        'asc_sign': get_zodiac(asc),
        'mc_sign': get_zodiac(mc),
        'lat': lat,
        'lon': lon,
        'tz_name': tz_name
    })

# ── RUN (RAILWAY) ─────────────────────────────────────────
if __name__ == '__main__':
    print(f"EPHE PATH: {EPHE_PATH}")
    print(f"FILES: {os.listdir(EPHE_PATH)}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
