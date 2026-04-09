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


# ── 27 NAKSHATRAS ────────────────────────────────────────────────
NAKSHATRAS = [
    {'name':'Ashwini',              'ka':'აშვინი',              'ruler':'Ketu',    'deity':'Ashwins',       'symbol':'Horse head'},
    {'name':'Bharani',              'ka':'ბჰარანი',             'ruler':'Venus',   'deity':'Yama',          'symbol':'Yoni'},
    {'name':'Krittika',             'ka':'კრიტიკა',             'ruler':'Sun',     'deity':'Agni',          'symbol':'Razor/Flame'},
    {'name':'Rohini',               'ka':'როჰინი',              'ruler':'Moon',    'deity':'Brahma',        'symbol':'Chariot'},
    {'name':'Mrigashira',           'ka':'მრიგაშირა',           'ruler':'Mars',    'deity':'Soma',          'symbol':'Deer head'},
    {'name':'Ardra',                'ka':'არდრა',               'ruler':'Rahu',    'deity':'Rudra',         'symbol':'Teardrop'},
    {'name':'Punarvasu',            'ka':'პუნარვასუ',           'ruler':'Jupiter', 'deity':'Aditi',         'symbol':'Bow/Quiver'},
    {'name':'Pushya',               'ka':'პუშია',               'ruler':'Saturn',  'deity':'Brihaspati',    'symbol':'Flower'},
    {'name':'Ashlesha',             'ka':'აშლეშა',              'ruler':'Mercury', 'deity':'Nagas',         'symbol':'Serpent'},
    {'name':'Magha',                'ka':'მაღა',                'ruler':'Ketu',    'deity':'Pitrs',         'symbol':'Throne'},
    {'name':'Purva Phalguni',       'ka':'პ. ფალგუნი',         'ruler':'Venus',   'deity':'Bhaga',         'symbol':'Hammock'},
    {'name':'Uttara Phalguni',      'ka':'უ. ფალგუნი',         'ruler':'Sun',     'deity':'Aryaman',       'symbol':'Bed'},
    {'name':'Hasta',                'ka':'ჰასტა',               'ruler':'Moon',    'deity':'Savitar',       'symbol':'Hand'},
    {'name':'Chitra',               'ka':'ჩიტრა',               'ruler':'Mars',    'deity':'Vishwakarma',   'symbol':'Pearl'},
    {'name':'Swati',                'ka':'სვატი',               'ruler':'Rahu',    'deity':'Vayu',          'symbol':'Coral'},
    {'name':'Vishakha',             'ka':'ვიშახა',              'ruler':'Jupiter', 'deity':'Indra-Agni',    'symbol':'Arch'},
    {'name':'Anuradha',             'ka':'ანურადჰა',            'ruler':'Saturn',  'deity':'Mitra',         'symbol':'Lotus'},
    {'name':'Jyeshtha',             'ka':'ჯიეშთა',             'ruler':'Mercury', 'deity':'Indra',         'symbol':'Umbrella'},
    {'name':'Mula',                 'ka':'მულა',                'ruler':'Ketu',    'deity':'Nirriti',       'symbol':'Root'},
    {'name':'Purva Ashadha',        'ka':'პ. აშადჰა',          'ruler':'Venus',   'deity':'Apas',          'symbol':'Fan'},
    {'name':'Uttara Ashadha',       'ka':'უ. აშადჰა',          'ruler':'Sun',     'deity':'Vishwadevas',   'symbol':'Elephant tusk'},
    {'name':'Shravana',             'ka':'შრავანა',             'ruler':'Moon',    'deity':'Vishnu',        'symbol':'Ear'},
    {'name':'Dhanishtha',           'ka':'დჰანიშთა',           'ruler':'Mars',    'deity':'Ashta Vasus',   'symbol':'Drum'},
    {'name':'Shatabhisha',          'ka':'შატაბჰიშა',          'ruler':'Rahu',    'deity':'Varuna',        'symbol':'Empty circle'},
    {'name':'Purva Bhadrapada',     'ka':'პ. ბჰადრაპადა',      'ruler':'Jupiter', 'deity':'Aja Ekapada',   'symbol':'Sword'},
    {'name':'Uttara Bhadrapada',    'ka':'უ. ბჰადრაპადა',      'ruler':'Saturn',  'deity':'Ahir Budhnya',  'symbol':'Twins'},
    {'name':'Revati',               'ka':'რევატი',              'ruler':'Mercury', 'deity':'Pushan',        'symbol':'Fish'},
]

PADA_SIGNS   = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PADA_RULERS  = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
                'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

VEDIC_SIGNS  = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya',
                'Tula','Vrischika','Dhanu','Makara','Kumbha','Mina']

def get_nakshatra(sid_deg):
    deg      = sid_deg % 360
    nak_size = 360.0 / 27.0
    pad_size = nak_size / 4.0
    nak_idx  = int(deg / nak_size)
    nak_pos  = deg - nak_idx * nak_size
    pada     = int(nak_pos / pad_size) + 1
    pada_si  = (nak_idx * 4 + pada - 1) % 12
    nak      = NAKSHATRAS[nak_idx]
    return {
        'nakshatra':       nak['name'],
        'nakshatra_ka':    nak['ka'],
        'nakshatra_ruler': nak['ruler'],
        'deity':           nak['deity'],
        'symbol':          nak['symbol'],
        'pada':            pada,
        'pada_sign':       PADA_SIGNS[pada_si],
        'pada_ruler':      PADA_RULERS[pada_si],
        'nak_idx':         nak_idx,
        'nak_pos':         round(nak_pos, 4),
        'pct':             round(nak_pos / nak_size * 100, 1),
    }

def vedic_sign(sid): return VEDIC_SIGNS[int(sid / 30) % 12]
def vedic_si(sid):   return int(sid / 30) % 12

# ── ROUTES ───────────────────────────────────────────────────────

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Vedic Astrology API running'})

@app.route('/geocode', methods=['POST'])
def geocode():
    try:
        city = request.json.get('city', '').strip()
        if not city:
            return jsonify({'error': 'City name is empty'}), 400
        try:
            geolocator = Nominatim(user_agent="vedic-chart-v1", timeout=10)
            location = geolocator.geocode(city, language='en', exactly_one=True)
        except:
            location = None
        if not location:
            try:
                q = urllib.parse.urlencode({'q': city, 'format': 'json', 'limit': 1})
                req = urllib.request.Request(
                    f'https://nominatim.openstreetmap.org/search?{q}',
                    headers={'User-Agent': 'vedic-chart-v1'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    results = _json.loads(resp.read())
                if results:
                    r0 = results[0]
                    lat = float(r0['lat']); lon = float(r0['lon'])
                    tz_name = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
                    return jsonify({'lat':lat,'lon':lon,'tz_name':tz_name,'display':r0.get('display_name',city)})
            except Exception as e2:
                return jsonify({'error': f'City not found: {city}'}), 404
        if not location:
            return jsonify({'error': 'City not found'}), 404
        lat, lon = location.latitude, location.longitude
        tz_name = tf.timezone_at(lat=lat, lng=lon) or 'UTC'
        return jsonify({'lat':lat,'lon':lon,'tz_name':tz_name,'display':location.address})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/vedic', methods=['POST'])
def vedic():
    swe.set_ephe_path(EPHE_PATH)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    data    = request.json
    year    = int(data['year']);   month  = int(data['month'])
    day     = int(data['day']);    hour   = int(data['hour'])
    minute  = int(data['minute']); second = int(data['second'])
    lat     = float(data['lat']); lon    = float(data['lon'])
    tz_name = data.get('tz_name', 'UTC')

    jd       = to_jd(year, month, day, hour, minute, second, tz_name)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

    planets = {}
    MAIN = {
        'Sun':     swe.SUN,    'Moon':    swe.MOON,
        'Mars':    swe.MARS,   'Mercury': swe.MERCURY,
        'Jupiter': swe.JUPITER,'Venus':   swe.VENUS,
        'Saturn':  swe.SATURN,
    }

    for name, pid in MAIN.items():
        pos, _ = swe.calc_ut(jd, pid, FLAGS)
        trop   = pos[0]
        sid    = (trop - ayanamsa) % 360
        nak    = get_nakshatra(sid)
        planets[name] = {
            'tropical':    round(trop, 4),
            'sidereal':    round(sid, 4),
            'sign':        vedic_sign(sid),
            'sign_idx':    vedic_si(sid),
            'sign_degree': round(sid % 30, 4),
            'dms':         fmtDMS(sid),
            'retrograde':  pos[3] < 0,
            'nakshatra':   nak,
        }

    # Rahu & Ketu
    try:
        pos, _ = swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)
        trop = pos[0]; sid = (trop - ayanamsa) % 360
        planets['Rahu'] = {
            'tropical':round(trop,4),'sidereal':round(sid,4),
            'sign':vedic_sign(sid),'sign_idx':vedic_si(sid),
            'sign_degree':round(sid%30,4),'dms':fmtDMS(sid),
            'retrograde':True,'nakshatra':get_nakshatra(sid),
        }
        k_sid = (sid + 180) % 360
        planets['Ketu'] = {
            'tropical':round((trop+180)%360,4),'sidereal':round(k_sid,4),
            'sign':vedic_sign(k_sid),'sign_idx':vedic_si(k_sid),
            'sign_degree':round(k_sid%30,4),'dms':fmtDMS(k_sid),
            'retrograde':True,'nakshatra':get_nakshatra(k_sid),
        }
    except: pass

    # Lagna (Ascendant)
    _, ascmc   = swe.houses(jd, lat, lon, b'W')
    asc_trop   = float(ascmc[0])
    mc_trop    = float(ascmc[1])
    asc_sid    = (asc_trop - ayanamsa) % 360
    mc_sid     = (mc_trop  - ayanamsa) % 360
    lagna_si   = int(asc_sid / 30)

    # Whole-sign houses
    for name in planets:
        p_si   = planets[name]['sign_idx']
        planets[name]['house'] = ((p_si - lagna_si) % 12) + 1

    return jsonify({
        'planets':      planets,
        'asc':          round(asc_sid, 4),
        'mc':           round(mc_sid, 4),
        'asc_sign':     vedic_sign(asc_sid),
        'asc_sign_idx': lagna_si,
        'mc_sign':      vedic_sign(mc_sid),
        'ayanamsa':     round(ayanamsa, 4),
        'lagna_nak':    get_nakshatra(asc_sid),
        'lat':lat,'lon':lon,'tz_name':tz_name
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# ════════════════════════════════════════════════════════════════
# VEDIC ASTROLOGY (JYOTISH) — /vedic endpoint
# ════════════════════════════════════════════════════════════════

# 27 Nakshatras — each spans 13°20' (800 arcmin)
NAKSHATRAS = [
    {'name':'Ashwini',     'ka':'აშვინი',      'ruler':'Ketu',    'symbol':'Horse head',   'deity':'Ashwins'},
    {'name':'Bharani',     'ka':'ბჰარანი',     'ruler':'Venus',   'symbol':'Yoni',         'deity':'Yama'},
    {'name':'Krittika',    'ka':'კრიტიკა',     'ruler':'Sun',     'symbol':'Razor/Flame',  'deity':'Agni'},
    {'name':'Rohini',      'ka':'როჰინი',      'ruler':'Moon',    'symbol':'Chariot',      'deity':'Brahma'},
    {'name':'Mrigashira',  'ka':'მრიგაშირა',   'ruler':'Mars',    'symbol':'Deer head',    'deity':'Soma'},
    {'name':'Ardra',       'ka':'არდრა',       'ruler':'Rahu',    'symbol':'Teardrop',     'deity':'Rudra'},
    {'name':'Punarvasu',   'ka':'პუნარვასუ',   'ruler':'Jupiter', 'symbol':'Bow/Quiver',   'deity':'Aditi'},
    {'name':'Pushya',      'ka':'პუშია',       'ruler':'Saturn',  'symbol':'Flower',       'deity':'Brihaspati'},
    {'name':'Ashlesha',    'ka':'აშლეშა',      'ruler':'Mercury', 'symbol':'Serpent',      'deity':'Nagas'},
    {'name':'Magha',       'ka':'მაღა',        'ruler':'Ketu',    'symbol':'Throne',       'deity':'Pitrs'},
    {'name':'Purva Phalguni','ka':'პურვა ფალგუნი','ruler':'Venus','symbol':'Hammock',     'deity':'Bhaga'},
    {'name':'Uttara Phalguni','ka':'უტარა ფალგუნი','ruler':'Sun', 'symbol':'Bed',          'deity':'Aryaman'},
    {'name':'Hasta',       'ka':'ჰასტა',       'ruler':'Moon',    'symbol':'Hand',         'deity':'Savitar'},
    {'name':'Chitra',      'ka':'ჩიტრა',       'ruler':'Mars',    'symbol':'Pearl',        'deity':'Vishwakarma'},
    {'name':'Swati',       'ka':'სვატი',       'ruler':'Rahu',    'symbol':'Coral/Sword',  'deity':'Vayu'},
    {'name':'Vishakha',    'ka':'ვიშახა',      'ruler':'Jupiter', 'symbol':'Arch/Potter wheel','deity':'Indra-Agni'},
    {'name':'Anuradha',    'ka':'ანურადჰა',    'ruler':'Saturn',  'symbol':'Lotus',        'deity':'Mitra'},
    {'name':'Jyeshtha',    'ka':'ჯიეშთა',     'ruler':'Mercury', 'symbol':'Umbrella',     'deity':'Indra'},
    {'name':'Mula',        'ka':'მულა',        'ruler':'Ketu',    'symbol':'Root/Tail',    'deity':'Nirriti'},
    {'name':'Purva Ashadha','ka':'პურვა აშადჰა','ruler':'Venus',  'symbol':'Fan/Tusk',     'deity':'Apas'},
    {'name':'Uttara Ashadha','ka':'უტარა აშადჰა','ruler':'Sun',   'symbol':'Elephant tusk','deity':'Vishwadevas'},
    {'name':'Shravana',    'ka':'შრავანა',     'ruler':'Moon',    'symbol':'Ear/Trident',  'deity':'Vishnu'},
    {'name':'Dhanishtha',  'ka':'დჰანიშთა',   'ruler':'Mars',    'symbol':'Drum',         'deity':'Ashta Vasus'},
    {'name':'Shatabhisha', 'ka':'შატაბჰიშა',  'ruler':'Rahu',    'symbol':'Empty circle', 'deity':'Varuna'},
    {'name':'Purva Bhadrapada','ka':'პურვა ბჰადრაპადა','ruler':'Jupiter','symbol':'Sword/Funeral cot','deity':'Aja Ekapada'},
    {'name':'Uttara Bhadrapada','ka':'უტარა ბჰადრაპადა','ruler':'Saturn','symbol':'Twins/Back legs','deity':'Ahir Budhnya'},
    {'name':'Revati',      'ka':'რევატი',      'ruler':'Mercury', 'symbol':'Fish/Drum',    'deity':'Pushan'},
]

# Pada rulers follow the sequence: Aries, Taurus, Gemini, Cancer (repeating)
# Sub-lord of each pada = the ruler of that navamsa sign
PADA_SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PADA_RULERS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
               'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

def get_nakshatra(sidereal_deg):
    """Get nakshatra, pada and their rulers from sidereal longitude."""
    deg = sidereal_deg % 360
    nak_size    = 360.0 / 27.0          # 13.3333°
    pada_size   = nak_size / 4.0        # 3.3333°

    nak_idx  = int(deg / nak_size)      # 0..26
    nak_pos  = deg - nak_idx * nak_size # 0..13.333°
    pada     = int(nak_pos / pada_size) + 1  # 1..4

    # Pada sign cycles through all 12 signs starting from Aries at Ashwini pada 1
    pada_sign_idx = (nak_idx * 4 + (pada - 1)) % 12

    nak = NAKSHATRAS[nak_idx]
    return {
        'nakshatra':      nak['name'],
        'nakshatra_ka':   nak['ka'],
        'nakshatra_ruler':nak['ruler'],
        'deity':          nak['deity'],
        'symbol':         nak['symbol'],
        'pada':           pada,
        'pada_sign':      PADA_SIGNS[pada_sign_idx],
        'pada_ruler':     PADA_RULERS[pada_sign_idx],
        'nak_idx':        nak_idx,
        'nak_pos':        round(nak_pos, 4),  # degrees within nakshatra
        'pct':            round(nak_pos / nak_size * 100, 1),  # % through nakshatra
    }

# Ayanamsa — Lahiri (most common in Jyotish)
def get_ayanamsa(jd):
    return swe.get_ayanamsa_ut(jd)  # Lahiri by default

VEDIC_SIGNS = [
    'მეშა','ვრიშაბჰა','მითჰუნა','კარკატა',
    'სიმჰა','კანია','თულა','ვრიშჩიკა',
    'დჰანუ','მაკარა','კუმბჰა','მინა'
]

def vedic_sign(sidereal_deg):
    return VEDIC_SIGNS[int(sidereal_deg / 30) % 12]

def vedic_sign_idx(sidereal_deg):
    return int(sidereal_deg / 30) % 12

def fmtDMS(deg):
    """Format degree as D°MM'SS\" """
    d = int(deg % 30)
    m = int((deg % 30 - d) * 60)
    s = int(((deg % 30 - d) * 60 - m) * 60)
    return f"{d}°{m:02d}'{s:02d}\""

@app.route('/vedic', methods=['POST'])
def vedic():
    swe.set_ephe_path(EPHE_PATH)
    # Use Lahiri ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)

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

    jd = to_jd(year, month, day, hour, minute, second, tz_name)
    ayanamsa = get_ayanamsa(jd)

    planets = {}

    MAIN = {
        'Sun':     swe.SUN,
        'Moon':    swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus':   swe.VENUS,
        'Mars':    swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn':  swe.SATURN,
    }

    FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

    for name, pid in MAIN.items():
        pos, _ = swe.calc_ut(jd, pid, FLAGS)
        trop   = pos[0]
        sid    = (trop - ayanamsa) % 360
        retro  = pos[3] < 0
        nak    = get_nakshatra(sid)
        planets[name] = {
            'tropical':    round(trop, 4),
            'sidereal':    round(sid, 4),
            'sign':        vedic_sign(sid),
            'sign_idx':    vedic_sign_idx(sid),
            'sign_degree': round(sid % 30, 4),
            'dms':         fmtDMS(sid),
            'retrograde':  retro,
            'nakshatra':   nak,
        }

    # Rahu & Ketu (True Node)
    try:
        pos, _ = swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)
        trop   = pos[0]
        sid    = (trop - ayanamsa) % 360
        nak    = get_nakshatra(sid)
        planets['Rahu'] = {
            'tropical': round(trop,4), 'sidereal': round(sid,4),
            'sign': vedic_sign(sid), 'sign_idx': vedic_sign_idx(sid),
            'sign_degree': round(sid%30,4), 'dms': fmtDMS(sid),
            'retrograde': True, 'nakshatra': nak,
        }
        ketu_sid = (sid + 180) % 360
        nak_k = get_nakshatra(ketu_sid)
        planets['Ketu'] = {
            'tropical': round((trop+180)%360,4), 'sidereal': round(ketu_sid,4),
            'sign': vedic_sign(ketu_sid), 'sign_idx': vedic_sign_idx(ketu_sid),
            'sign_degree': round(ketu_sid%30,4), 'dms': fmtDMS(ketu_sid),
            'retrograde': True, 'nakshatra': nak_k,
        }
    except: pass

    # Lagna (Ascendant) — whole sign house system most common in Jyotish
    cusps_w, ascmc = swe.houses(jd, lat, lon, b'W')  # Whole sign
    cusps_p, _     = swe.houses(jd, lat, lon, b'P')  # Placidus for reference

    asc_trop = float(ascmc[0])
    mc_trop  = float(ascmc[1])
    asc_sid  = (asc_trop - ayanamsa) % 360
    mc_sid   = (mc_trop  - ayanamsa) % 360

    lagna_sign_idx = int(asc_sid / 30)

    # Assign whole-sign houses
    for name in planets:
        p_sid   = planets[name]['sidereal']
        p_si    = planets[name]['sign_idx']
        house_n = ((p_si - lagna_sign_idx) % 12) + 1
        planets[name]['house'] = house_n

    # Whole sign house cusps (sidereal)
    houses_sid = [((lagna_sign_idx + i) * 30 - ayanamsa + ayanamsa) % 360
                  for i in range(12)]
    houses_sid = [lagna_sign_idx * 30 + i * 30 for i in range(12)]
    houses_sid = [(h % 360) for h in houses_sid]

    # Lagna nakshatra
    lagna_nak = get_nakshatra(asc_sid)

    return jsonify({
        'planets':     planets,
        'asc':         round(asc_sid, 4),
        'asc_trop':    round(asc_trop, 4),
        'mc':          round(mc_sid, 4),
        'mc_trop':     round(mc_trop, 4),
        'asc_sign':    vedic_sign(asc_sid),
        'asc_sign_idx':lagna_sign_idx,
        'mc_sign':     vedic_sign(mc_sid),
        'ayanamsa':    round(ayanamsa, 4),
        'lagna_nak':   lagna_nak,
        'houses':      houses_sid,
        'lat': lat, 'lon': lon, 'tz_name': tz_name
    })
