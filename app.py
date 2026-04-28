"""
Unified astrology site.

Combines the existing astrology backend (/chart, /vedic, /true_sidereal,
/moon, /geocode) with a new Human Design module (/hd, /api/hd_chart).

Sub-pages served:
    /                  - landing page (astro.html if present, else index)
    /astro             - western chart         (astro.html)
    /moon              - lunar day             (moon.html)
    /vedic             - vedic chart           (vedic.html)
    /true_sidereal     - true sidereal chart   (true_sidereal.html)
    /hd                - Human Design chart    (hd.html)

HD-specific:
    /api/hd_chart      - POST {date, time, place}  returns the HD chart JSON
    /static/...        - served the merged human_prepared.svg and assets
"""

import os
import math
import subprocess
import sys
import urllib.request
import urllib.parse
import json as _json
from datetime import datetime
from pathlib import Path

# ── EPHE PATH ──────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, 'ephe')
os.makedirs(EPHE_PATH, exist_ok=True)
os.environ['SE_EPHE_PATH'] = EPHE_PATH

import swisseph as swe
swe.set_ephe_path(EPHE_PATH)

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# HD module
from hd_calc import calculate_chart as hd_calculate_chart


# ────────────────────────────────────────────────────────────────
# HD SVG PRE-FLIGHT: run prepare_svg.py once if human_prepared.svg
# is missing (merges human.svg + details.svg).
# ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
def _ensure_hd_svg():
    prepared  = ROOT / "static" / "human_prepared.svg"
    positions = ROOT / "static" / "gate_positions.json"
    if prepared.exists() and positions.exists():
        return
    human   = ROOT / "static" / "human.svg"
    details = ROOT / "static" / "detail.svg"
    if not human.exists() or not details.exists():
        print("[hd] skipping SVG prep — human.svg or details.svg missing",
              file=sys.stderr)
        return
    print(f"[hd] preparing merged SVG from {human.name} + {details.name} ...")
    try:
        subprocess.check_call(
            [sys.executable, str(ROOT / "prepare_svg.py")],
            cwd=str(ROOT),
        )
    except subprocess.CalledProcessError as e:
        print(f"[hd] prepare_svg failed: {e}", file=sys.stderr)

_ensure_hd_svg()


app = Flask(__name__)
CORS(app, origins="*")
tf = TimezoneFinder()

# ── JSON error handlers — ensure Flask never returns HTML for API errors ──
@app.errorhandler(404)
def e404(e): return jsonify(error="Not found", detail=str(e)), 404
@app.errorhandler(405)
def e405(e): return jsonify(error="Method not allowed"), 405
@app.errorhandler(500)
def e500(e): return jsonify(error="Internal server error", detail=str(e)), 500

# ════════════════════════════════════════════════════════════════
# SHARED HELPERS  (unchanged from original app.py)
# ════════════════════════════════════════════════════════════════

def to_jd(year, month, day, hour, minute, second, tz_name):
    try:
        tz = pytz.timezone(tz_name)
        local_dt = tz.localize(datetime(year, month, day, hour, minute, second), is_dst=None)
        u = local_dt.utctimetuple()
        utc_h = u.tm_hour + u.tm_min/60 + u.tm_sec/3600
        return swe.julday(u.tm_year, u.tm_mon, u.tm_mday, utc_h)
    except:
        return swe.julday(year, month, day, hour + minute/60 + second/3600)

def deg_to_display(degree):
    d = int(degree % 30)
    m = (degree % 30 - d) * 60
    return d, round(m / 60 * 100)

def fmtDMS(deg):
    d = int(deg % 30)
    m = int((deg % 30 - d) * 60)
    s = int(((deg % 30 - d) * 60 - m) * 60)
    return f"{d}\u00b0{m:02d}'{s:02d}\""

TROPICAL_SIGNS = [
    'ვერძი','კურო','ტყუპები','კირჩხიბი',
    'ლომი','ქალწული','სასწორი','მორიელი',
    'მშვილდოსანი','თხის რქა','მერწყული','თევზები'
]
VEDIC_SIGNS = [
    'Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya',
    'Tula','Vrischika','Dhanu','Makara','Kumbha','Mina'
]

def trop_sign(deg): return TROPICAL_SIGNS[int(deg/30)%12]
def ved_sign(deg):  return VEDIC_SIGNS[int(deg/30)%12]
def ved_si(deg):    return int(deg/30)%12

def get_house(degree, cusps):
    for i in range(12):
        s, e = cusps[i], cusps[(i+1)%12]
        if s <= e:
            if s <= degree < e: return i+1
        else:
            if degree >= s or degree < e: return i+1
    return 1

# ════════════════════════════════════════════════════════════════
# LUNAR DAY
# ════════════════════════════════════════════════════════════════

def _elongation(jd):
    sun,  _ = swe.calc_ut(jd, swe.SUN)
    moon, _ = swe.calc_ut(jd, swe.MOON)
    return (moon[0] - sun[0]) % 360

def calc_lunar_day(jd, tz_offset=0.0):
    elong = _elongation(jd)
    approx_age = elong / 360 * 29.53059
    search_start = jd - approx_age - 1.5
    prev_e = _elongation(search_start)
    nm_jd  = search_start
    step   = 1 / 24
    cur    = search_start
    for _ in range(int(32 * 24)):
        cur += step
        cur_e = _elongation(cur)
        if prev_e > 350 and cur_e < 10:
            nm_jd = cur - step
            break
        prev_e = cur_e
    lo, hi = nm_jd, nm_jd + step
    for _ in range(20):
        mid = (lo + hi) / 2
        if _elongation(mid) > 180: lo = mid
        else: hi = mid
    new_moon_jd   = (lo + hi) / 2
    age_days      = jd - new_moon_jd
    lunar_day     = max(1, min(30, int(age_days) + 1))
    next_nm_jd    = new_moon_jd + 29.53059
    hours_to_next = (next_nm_jd - jd) * 24
    illumination  = round((1 - math.cos(math.radians(elong))) / 2 * 100, 1)
    pct_elapsed   = round(age_days / 29.53059 * 100, 1)
    return {
        'lunar_day':        lunar_day,
        'elongation':       round(elong, 3),
        'age_days':         round(age_days, 4),
        'age_hours':        round(age_days * 24, 2),
        'illumination':     illumination,
        'pct_elapsed':      pct_elapsed,
        'new_moon_jd':      round(new_moon_jd, 5),
        'hours_to_next':    round(hours_to_next, 1),
        'hours_to_next_nm': round(hours_to_next, 1),
    }

# ════════════════════════════════════════════════════════════════
# MOON API
# ════════════════════════════════════════════════════════════════

def _utc_meta(date_str, time_str, tz_name):
    tz       = pytz.timezone(tz_name)
    naive_dt = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
    try:
        local_dt = tz.localize(naive_dt, is_dst=None)
    except Exception:
        local_dt = tz.localize(naive_dt, is_dst=False)
    utc_dt     = local_dt.astimezone(pytz.utc)
    offset_sec = local_dt.utcoffset().total_seconds()
    sign       = '+' if offset_sec >= 0 else '-'
    h, rem     = divmod(abs(int(offset_sec)), 3600)
    m          = rem // 60
    return (
        utc_dt.strftime('%Y-%m-%dT%H:%M:%S'),
        f'{sign}{h:02d}:{m:02d}',
        bool(local_dt.dst().total_seconds())
    )

def _phase_name(age):
    if   age < 1.85:  return 'New Moon'
    elif age < 7.38:  return 'Waxing Crescent'
    elif age < 9.22:  return 'First Quarter'
    elif age < 14.77: return 'Waxing Gibbous'
    elif age < 16.61: return 'Full Moon'
    elif age < 22.15: return 'Waning Gibbous'
    elif age < 23.99: return 'Last Quarter'
    else:             return 'Waning Crescent'

@app.route('/api/moon', methods=['GET'])
def moon_api():
    date_str = request.args.get('date', '')
    time_str = request.args.get('time', '12:00')
    tz_name  = request.args.get('timezone', 'UTC')
    if not date_str:
        return jsonify({'error': 'date param required'}), 400
    try:
        pytz.timezone(tz_name)
    except Exception:
        return jsonify({'error': f'Unknown timezone: {tz_name}'}), 400
    try:
        utc_str, utc_offset, dst_active = _utc_meta(date_str, time_str, tz_name)
        dt  = datetime.strptime(utc_str, '%Y-%m-%dT%H:%M:%S')
        jd  = swe.julday(dt.year, dt.month, dt.day,
                         dt.hour + dt.minute/60 + dt.second/3600)
        elong    = _elongation(jd)
        age_days = elong / 360 * 29.53059
        lunar    = calc_lunar_day(jd)
        illum    = round((1 - math.cos(math.radians(elong))) / 2 * 100, 1)
        EMOJIS   = ['🌑','🌒','🌓','🌔','🌕','🌖','🌗','🌘']
        emoji    = EMOJIS[int(age_days / 29.53059 * 8) % 8]
        return jsonify({
            'input': {
                'local_date':   date_str,
                'local_time':   time_str,
                'timezone':     tz_name,
                'utc_offset':   utc_offset,
                'dst_active':   dst_active,
                'utc_datetime': utc_str,
            },
            'age_days':         round(age_days, 3),
            'elongation':       round(elong, 3),
            'illumination':     illum,
            'phase':            _phase_name(age_days),
            'emoji':            emoji,
            'lunar_day':        lunar['lunar_day'],
            'hours_to_next_nm': lunar['hours_to_next_nm'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/timezones')
def api_timezones():
    return jsonify(sorted(pytz.all_timezones))

# ════════════════════════════════════════════════════════════════
# PAGE ROUTES  ← sub-pages are served from templates/
# ════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Landing page. If templates/index.html exists use it; else show a
    minimal hub that links to all sub-pages."""
    tpl = ROOT / "templates" / "index.html"
    if tpl.exists():
        return render_template('index.html')
    return """
    <!doctype html>
    <html lang="ka"><head><meta charset="utf-8"><title>Astrology Hub</title>
    <style>
      body{font-family:system-ui;background:#0c0a1a;color:#eee;
           margin:0;min-height:100vh;display:flex;align-items:center;
           justify-content:center;flex-direction:column;gap:18px}
      h1{font-size:2rem;margin:0 0 1rem}
      a{color:#f9c646;text-decoration:none;padding:14px 28px;
        border:1px solid #f9c646;border-radius:10px;font-size:1.05rem}
      a:hover{background:#f9c646;color:#0c0a1a}
      nav{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;max-width:640px}
    </style></head><body>
      <h1>ასტროლოგია</h1>
      <nav>
        <a href="/astro">დასავლური</a>
        <a href="/vedic">ვედური</a>
        <a href="/true_sidereal">ჭეშმარიტი</a>
        <a href="/moon">მთვარის დღე</a>
        <a href="/hd">ადამიანის დიზაინი</a>
      </nav>
    </body></html>
    """

@app.route('/astro')
def page_astro():
    return render_template('astro.html')

@app.route('/moon')
def page_moon():
    return render_template('moon.html')

@app.route('/vedic')
def page_vedic():
    return render_template('vedic.html')

@app.route('/true_sidereal')
def page_true_sidereal():
    return render_template('true_sidereal.html')

@app.route('/hd')
def page_hd():
    return render_template('hd.html')

# ════════════════════════════════════════════════════════════════
# GEOCODE
# ════════════════════════════════════════════════════════════════

@app.route('/geocode', methods=['POST'])
def geocode():
    """Geocode a city name to (lat, lon, tz_name).

    Railway blocks all public Nominatim/Photon geocoders from cloud IPs.
    Strategy:
    1. Built-in city cache (instant, works offline)
    2. OpenCage API if OPENCAGE_API_KEY env var is set (free: 2500 req/day)
    """
    import os
    try:
        city = request.json.get('city', '').strip()
        if not city:
            return jsonify({'error': 'City name is empty'}), 400

        # Shared cache (same as hd_calc._CITY_CACHE — import it)
        from hd_calc import _CITY_CACHE, _tf as hd_tf

        key = city.lower()
        city_only = key.split(",")[0].strip()
        for k in (key, city_only):
            if k in _CITY_CACHE:
                lat, lon, display, tz = _CITY_CACHE[k]
                return jsonify({'lat': lat, 'lon': lon, 'tz_name': tz, 'display': display})

        # OpenCage API fallback
        api_key = os.environ.get('OPENCAGE_API_KEY', '').strip()
        if api_key:
            try:
                q = urllib.parse.urlencode({
                    'q': city, 'key': api_key, 'limit': 1,
                    'no_annotations': 1, 'language': 'en'
                })
                req = urllib.request.Request(
                    f'https://api.opencagedata.com/geocode/v1/json?{q}',
                    headers={'User-Agent': 'astro-api/1.0'},
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = _json.loads(r.read())
                if data.get('results'):
                    res = data['results'][0]
                    lat = float(res['geometry']['lat'])
                    lon = float(res['geometry']['lng'])
                    display = res.get('formatted', city)
                    tz_info = res.get('annotations', {}).get('timezone', {})
                    tz = tz_info.get('name') or hd_tf.timezone_at(lat=lat, lng=lon) or 'UTC'
                    return jsonify({'lat': lat, 'lon': lon, 'tz_name': tz, 'display': display})
                return jsonify({'error': f'City not found: {city}'}), 404
            except Exception as e:
                app.logger.error(f'OpenCage error: {e}')
                return jsonify({'error': f'Geocoding error: {e}'}), 502

        # Neither cache nor API key — tell user what to do
        cache_sample = ", ".join(list(_CITY_CACHE.keys())[:10])
        return jsonify({
            'error': (
                f"City '{city}' not in cache. Available cities include: {cache_sample}... "
                f"To geocode any city, set OPENCAGE_API_KEY in Railway environment variables "
                f"(free key at https://opencagedata.com — 2500 requests/day)."
            )
        }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ════════════════════════════════════════════════════════════════
# WESTERN CHART  (original /chart endpoint kept intact)
# ════════════════════════════════════════════════════════════════

ASPECTS_DEF = [
    {'name':'შეერთება',  'angles':[0],       'orb':8, 'sym':'☌','color':'#f9c646'},
    {'name':'ოპოზიცია',  'angles':[180],     'orb':8, 'sym':'☍','color':'#e89040'},
    {'name':'ტრინი',     'angles':[120,240], 'orb':7, 'sym':'△','color':'#a078f0'},
    {'name':'კვადრატი',  'angles':[90,270],  'orb':6, 'sym':'□','color':'#e84040'},
    {'name':'სექსტილი',  'angles':[60,300],  'orb':5, 'sym':'⚹','color':'#30c890'},
    {'name':'კვინკონსი', 'angles':[150,210], 'orb':3, 'sym':'⚻','color':'#9ba8b8'},
]

ASPECT_PLANETS = [
    'მზე','მთვარე','მერკური','ვენერა','მარსი',
    'იუპიტერი','სატურნი','ურანი','ნეპტუნი','პლუტონი',
    'ქირონი','ჩრდ. კვანძი'
]

def calc_aspects(planets):
    aspects = []
    names = [n for n in ASPECT_PLANETS if n in planets]
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            d1 = planets[p1]['degree']
            d2 = planets[p2]['degree']
            raw = (d2 - d1 + 360) % 360
            best_asp = None
            best_orb = 999
            for asp in ASPECTS_DEF:
                for target in asp['angles']:
                    orb = abs(raw - target)
                    if orb > 180: orb = 360 - orb
                    if orb <= asp['orb'] and orb < best_orb:
                        best_orb = orb
                        best_asp = asp
            if best_asp:
                aspects.append({
                    'p1':p1,'p2':p2,
                    'type':best_asp['name'],'sym':best_asp['sym'],
                    'color':best_asp['color'],
                    'orb':round(best_orb,2),
                    'angle':best_asp['angles'][0]
                })
    aspects.sort(key=lambda x: x['orb'])
    return aspects

@app.route('/chart', methods=['POST'])
def chart():
    swe.set_ephe_path(EPHE_PATH)
    d = request.json
    year,month,day = int(d['year']),int(d['month']),int(d['day'])
    hour,minute,second = int(d['hour']),int(d['minute']),int(d['second'])
    lat,lon = float(d['lat']),float(d['lon'])
    tz_name = d.get('tz_name','UTC')
    time_unknown = d.get('time_unknown', False)

    jd = to_jd(year,month,day,hour,minute,second,tz_name)
    planets = {}

    MAIN = {'მზე':swe.SUN,'მთვარე':swe.MOON,'მერკური':swe.MERCURY,
            'ვენერა':swe.VENUS,'მარსი':swe.MARS,'იუპიტერი':swe.JUPITER,
            'სატურნი':swe.SATURN,'ურანი':swe.URANUS,'ნეპტუნი':swe.NEPTUNE,'პლუტონი':swe.PLUTO}

    for name,pid in MAIN.items():
        pos,_ = swe.calc_ut(jd,pid)
        deg = pos[0]; dv,c = deg_to_display(deg)
        planets[name] = {'degree':round(deg,4),'sign':trop_sign(deg),
            'sign_degree':dv,'centesimal':c,'retrograde':bool(pos[3]<0) if len(pos)>3 else False}

    for name,pid in [('ქირონი',swe.CHIRON),('ლილიტი',swe.MEAN_APOG)]:
        try:
            pos,_ = swe.calc_ut(jd,pid); deg=pos[0]; dv,c=deg_to_display(deg)
            planets[name]={'degree':round(deg,4),'sign':trop_sign(deg),
                'sign_degree':dv,'centesimal':c,'retrograde':bool(pos[3]<0) if len(pos)>3 else False}
        except: pass

    for ast_id in [swe.AST_OFFSET+1181, 56]:
        try:
            pos,_ = swe.calc_ut(jd,ast_id); deg=pos[0]; dv,c=deg_to_display(deg)
            planets['თეთრი მთვარე']={'degree':round(deg,4),'sign':trop_sign(deg),
                'sign_degree':dv,'centesimal':c,'retrograde':False}
            break
        except: pass

    try:
        pos,_ = swe.calc_ut(jd,swe.MEAN_NODE); nn=pos[0]; dv,c=deg_to_display(nn)
        planets['ჩრდ. კვანძი']={'degree':round(nn,4),'sign':trop_sign(nn),'sign_degree':dv,'centesimal':c,'retrograde':True}
        sn=(nn+180)%360; dv,c=deg_to_display(sn)
        planets['სამხ. კვანძი']={'degree':round(sn,4),'sign':trop_sign(sn),'sign_degree':dv,'centesimal':c,'retrograde':True}
    except: pass

    try:
        pos,_ = swe.calc_ut(jd,swe.AST_OFFSET+3); deg=pos[0]; dv,c=deg_to_display(deg)
        planets['იუნო']={'degree':round(deg,4),'sign':trop_sign(deg),'sign_degree':dv,'centesimal':c,'retrograde':bool(pos[3]<0) if len(pos)>3 else False}
    except: pass

    cusps,ascmc = swe.houses(jd,lat,lon,b'P')
    asc=float(ascmc[0]); mc=float(ascmc[1])

    if not time_unknown:
        try:
            vx=float(ascmc[3]); dv,c=deg_to_display(vx)
            planets['ვერტექსი']={'degree':round(vx,4),'sign':trop_sign(vx),'sign_degree':dv,'centesimal':c,'retrograde':False}
        except: pass
        try:
            f=(asc+planets['მთვარე']['degree']-planets['მზე']['degree'])%360; dv,c=deg_to_display(f)
            planets['ბედის ვარსკვლავი']={'degree':round(f,4),'sign':trop_sign(f),'sign_degree':dv,'centesimal':c,'retrograde':False}
        except: pass

    for name in planets:
        planets[name]['house'] = get_house(planets[name]['degree'],cusps)

    try:
        tz_offset=0.0
        try:
            tz_obj=pytz.timezone(tz_name)
            ld=tz_obj.localize(datetime(year,month,day,hour,minute,second))
            tz_offset=ld.utcoffset().total_seconds()/3600
        except: pass
        lunar=calc_lunar_day(jd,tz_offset)
    except:
        lunar=None

    return jsonify({
        'planets':planets,'houses':[round(c,4) for c in cusps],
        'asc':round(asc,4),'mc':round(mc,4),
        'asc_sign':trop_sign(asc),'mc_sign':trop_sign(mc),
        'aspects':calc_aspects(planets),'lunar':lunar,
        'lat':lat,'lon':lon,'tz_name':tz_name
    })

@app.route('/lunar', methods=['POST'])
def lunar():
    swe.set_ephe_path(EPHE_PATH)
    d=request.json
    year,month,day=int(d['year']),int(d['month']),int(d['day'])
    hour,minute,second=int(d.get('hour',12)),int(d.get('minute',0)),int(d.get('second',0))
    tz_name=d.get('tz_name','UTC')
    time_unknown=d.get('time_unknown',False)
    jd=to_jd(year,month,day,hour,minute,second,tz_name)
    try:
        tz_offset=0.0
        try:
            tz_obj=pytz.timezone(tz_name)
            ld=tz_obj.localize(datetime(year,month,day,hour,minute,second))
            tz_offset=ld.utcoffset().total_seconds()/3600
        except: pass
        lunar_data=calc_lunar_day(jd,tz_offset)
    except Exception as e:
        return jsonify({'error':str(e)}),500
    result={'lunar':lunar_data}
    if time_unknown:
        try:
            jd0=to_jd(year,month,day,0,0,0,tz_name)
            jd1=to_jd(year,month,day,23,59,59,tz_name)
            m0,_=swe.calc_ut(jd0,swe.MOON)
            m1,_=swe.calc_ut(jd1,swe.MOON)
            result['moon_path']={'start':round(m0[0],4),'end':round(m1[0],4)}
            swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)
            ayan0=swe.get_ayanamsa_ut(jd0)
            ayan1=swe.get_ayanamsa_ut(jd1)
            result['moon_path_sid']={
                'start':round((m0[0]-ayan0)%360,4),
                'end':  round((m1[0]-ayan1)%360,4)
            }
            swe.set_sid_mode(swe.SIDM_TROPICAL,0,0)
        except: pass
    return jsonify(result)

@app.route('/test')
def test():
    swe.set_ephe_path(EPHE_PATH)
    return jsonify({'status':'ok','ephe_files':os.listdir(EPHE_PATH)})

# ════════════════════════════════════════════════════════════════
# VEDIC CHART
# ════════════════════════════════════════════════════════════════

NAKSHATRAS=[
    {'name':'Ashwini',          'ka':'აშვინი',         'ruler':'Ketu',   'deity':'Ashwins',     'symbol':'Horse head'},
    {'name':'Bharani',          'ka':'ბჰარანი',        'ruler':'Venus',  'deity':'Yama',         'symbol':'Yoni'},
    {'name':'Krittika',         'ka':'კრიტიკა',        'ruler':'Sun',    'deity':'Agni',         'symbol':'Flame'},
    {'name':'Rohini',           'ka':'როჰინი',         'ruler':'Moon',   'deity':'Brahma',       'symbol':'Chariot'},
    {'name':'Mrigashira',       'ka':'მრიგაშირა',      'ruler':'Mars',   'deity':'Soma',         'symbol':'Deer head'},
    {'name':'Ardra',            'ka':'არდრა',          'ruler':'Rahu',   'deity':'Rudra',        'symbol':'Teardrop'},
    {'name':'Punarvasu',        'ka':'პუნარვასუ',      'ruler':'Jupiter','deity':'Aditi',        'symbol':'Bow'},
    {'name':'Pushya',           'ka':'პუშია',          'ruler':'Saturn', 'deity':'Brihaspati',   'symbol':'Flower'},
    {'name':'Ashlesha',         'ka':'აშლეშა',         'ruler':'Mercury','deity':'Nagas',        'symbol':'Serpent'},
    {'name':'Magha',            'ka':'მაღა',           'ruler':'Ketu',   'deity':'Pitrs',        'symbol':'Throne'},
    {'name':'Purva Phalguni',   'ka':'პ. ფალგუნი',    'ruler':'Venus',  'deity':'Bhaga',        'symbol':'Hammock'},
    {'name':'Uttara Phalguni',  'ka':'უ. ფალგუნი',    'ruler':'Sun',    'deity':'Aryaman',      'symbol':'Bed'},
    {'name':'Hasta',            'ka':'ჰასტა',          'ruler':'Moon',   'deity':'Savitar',      'symbol':'Hand'},
    {'name':'Chitra',           'ka':'ჩიტრა',          'ruler':'Mars',   'deity':'Vishwakarma',  'symbol':'Pearl'},
    {'name':'Swati',            'ka':'სვატი',          'ruler':'Rahu',   'deity':'Vayu',         'symbol':'Coral'},
    {'name':'Vishakha',         'ka':'ვიშახა',         'ruler':'Jupiter','deity':'Indra-Agni',   'symbol':'Arch'},
    {'name':'Anuradha',         'ka':'ანურადჰა',       'ruler':'Saturn', 'deity':'Mitra',        'symbol':'Lotus'},
    {'name':'Jyeshtha',         'ka':'ჯიეშთა',        'ruler':'Mercury','deity':'Indra',        'symbol':'Umbrella'},
    {'name':'Mula',             'ka':'მულა',           'ruler':'Ketu',   'deity':'Nirriti',      'symbol':'Root'},
    {'name':'Purva Ashadha',    'ka':'პ. აშადჰა',     'ruler':'Venus',  'deity':'Apas',         'symbol':'Fan'},
    {'name':'Uttara Ashadha',   'ka':'უ. აშადჰა',     'ruler':'Sun',    'deity':'Vishwadevas',  'symbol':'Tusk'},
    {'name':'Shravana',         'ka':'შრავანა',        'ruler':'Moon',   'deity':'Vishnu',       'symbol':'Ear'},
    {'name':'Dhanishtha',       'ka':'დჰანიშთა',      'ruler':'Mars',   'deity':'Ashta Vasus',  'symbol':'Drum'},
    {'name':'Shatabhisha',      'ka':'შატაბჰიშა',     'ruler':'Rahu',   'deity':'Varuna',       'symbol':'Circle'},
    {'name':'Purva Bhadrapada', 'ka':'პ. ბჰადრაპადა', 'ruler':'Jupiter','deity':'Aja Ekapada',  'symbol':'Sword'},
    {'name':'Uttara Bhadrapada','ka':'უ. ბჰადრაპადა', 'ruler':'Saturn', 'deity':'Ahir Budhnya', 'symbol':'Twins'},
    {'name':'Revati',           'ka':'რევატი',         'ruler':'Mercury','deity':'Pushan',       'symbol':'Fish'},
]

PADA_SIGNS  =['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PADA_RULERS =['Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

def get_nakshatra(sid):
    deg=sid%360; sz=360/27; pz=sz/4
    ni=int(deg/sz); np2=deg-ni*sz; pada=int(np2/pz)+1
    psi=(ni*4+pada-1)%12
    n=NAKSHATRAS[ni]
    return {'nakshatra':n['name'],'nakshatra_ka':n['ka'],'nakshatra_ruler':n['ruler'],
            'deity':n['deity'],'symbol':n['symbol'],'pada':pada,
            'pada_sign':PADA_SIGNS[psi],'pada_ruler':PADA_RULERS[psi],
            'nak_idx':ni,'nak_pos':round(np2,4),'pct':round(np2/sz*100,1)}

@app.route('/vedic', methods=['POST'])
def vedic():
    try:
        swe.set_ephe_path(EPHE_PATH)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        d=request.json
        year,month,day=int(d['year']),int(d['month']),int(d['day'])
        hour,minute,second=int(d['hour']),int(d['minute']),int(d['second'])
        lat,lon=float(d['lat']),float(d['lon'])
        tz_name=d.get('tz_name','UTC')
        jd=to_jd(year,month,day,hour,minute,second,tz_name)
        ayanamsa=swe.get_ayanamsa_ut(jd)
        FLAGS=swe.FLG_SWIEPH|swe.FLG_SPEED
        planets={}
        MAIN={'Sun':swe.SUN,'Moon':swe.MOON,'Mars':swe.MARS,'Mercury':swe.MERCURY,
              'Jupiter':swe.JUPITER,'Venus':swe.VENUS,'Saturn':swe.SATURN,
              'Uranus':swe.URANUS,'Neptune':swe.NEPTUNE}
        for name,pid in MAIN.items():
            pos,_=swe.calc_ut(jd,pid,FLAGS); trop=pos[0]; sid=(trop-ayanamsa)%360
            planets[name]={'tropical':round(trop,4),'sidereal':round(sid,4),
                'sign':ved_sign(sid),'sign_idx':ved_si(sid),
                'sign_degree':round(sid%30,4),'dms':fmtDMS(sid),
                'retrograde':pos[3]<0,'nakshatra':get_nakshatra(sid)}
        try:
            pos,_=swe.calc_ut(jd,swe.TRUE_NODE,FLAGS); trop=pos[0]; sid=(trop-ayanamsa)%360
            planets['Rahu']={'tropical':round(trop,4),'sidereal':round(sid,4),
                'sign':ved_sign(sid),'sign_idx':ved_si(sid),
                'sign_degree':round(sid%30,4),'dms':fmtDMS(sid),
                'retrograde':True,'nakshatra':get_nakshatra(sid)}
            ks=(sid+180)%360
            planets['Ketu']={'tropical':round((trop+180)%360,4),'sidereal':round(ks,4),
                'sign':ved_sign(ks),'sign_idx':ved_si(ks),
                'sign_degree':round(ks%30,4),'dms':fmtDMS(ks),
                'retrograde':True,'nakshatra':get_nakshatra(ks)}
        except: pass
        _,ascmc=swe.houses(jd,lat,lon,b'W')
        asc_sid=(float(ascmc[0])-ayanamsa)%360
        mc_sid=(float(ascmc[1])-ayanamsa)%360
        lagna_si=int(asc_sid/30)
        for name in planets:
            planets[name]['house']=((planets[name]['sign_idx']-lagna_si)%12)+1
        ENG_TO_KA = {
            'Sun':'მზე','Moon':'მთვარე','Mercury':'მერკური','Venus':'ვენერა',
            'Mars':'მარსი','Jupiter':'იუპიტერი','Saturn':'სატურნი',
            'Uranus':'ურანი','Neptune':'ნეპტუნი',
            'Rahu':'ჩრდ. კვანძი','Ketu':'სამხ. კვანძი',
        }
        KA_TO_ENG = {v:k for k,v in ENG_TO_KA.items()}
        asp_planets = {}
        for name,p in planets.items():
            ka = ENG_TO_KA.get(name, name)
            asp_planets[ka] = {'degree': p['sidereal']}
        aspects = calc_aspects(asp_planets)
        for asp in aspects:
            asp['p1'] = KA_TO_ENG.get(asp['p1'], asp['p1'])
            asp['p2'] = KA_TO_ENG.get(asp['p2'], asp['p2'])
        return jsonify({'planets':planets,'asc':round(asc_sid,4),'mc':round(mc_sid,4),
            'asc_sign':ved_sign(asc_sid),'asc_sign_idx':lagna_si,'mc_sign':ved_sign(mc_sid),
            'ayanamsa':round(ayanamsa,4),'lagna_nak':get_nakshatra(asc_sid),
            'aspects':aspects,'lat':lat,'lon':lon,'tz_name':tz_name})
    except Exception as e:
        import traceback
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500
    finally:
        try: swe.set_sid_mode(swe.SIDM_TROPICAL, 0, 0)
        except: pass

# ════════════════════════════════════════════════════════════════
# TRUE SIDEREAL
# ════════════════════════════════════════════════════════════════

TRUE_CONSTELLATIONS = [
    {'name':'Aries',       'ka':'ვერძი',       'sym':'♈',  'start': 29.0, 'end': 53.5},
    {'name':'Taurus',      'ka':'კურო',        'sym':'♉',  'start': 53.5, 'end': 90.0},
    {'name':'Gemini',      'ka':'ტყუპები',     'sym':'♊',  'start': 90.0, 'end':118.5},
    {'name':'Cancer',      'ka':'კირჩხიბი',    'sym':'♋',  'start':118.5, 'end':138.5},
    {'name':'Leo',         'ka':'ლომი',        'sym':'♌',  'start':138.5, 'end':174.0},
    {'name':'Virgo',       'ka':'ქალწული',     'sym':'♍',  'start':174.0, 'end':217.5},
    {'name':'Libra',       'ka':'სასწორი',     'sym':'♎',  'start':217.5, 'end':241.0},
    {'name':'Scorpius',    'ka':'მორიელი',     'sym':'♏',  'start':241.0, 'end':247.5},
    {'name':'Ophiuchus',   'ka':'გველმჭერი',  'sym':'⛎',  'start':247.5, 'end':266.5},
    {'name':'Sagittarius', 'ka':'მშვილდოსანი', 'sym':'♐',  'start':266.5, 'end':302.0},
    {'name':'Capricornus', 'ka':'თხის რქა',   'sym':'♑',  'start':302.0, 'end':327.0},
    {'name':'Aquarius',    'ka':'მერწყული',    'sym':'♒',  'start':327.0, 'end':351.5},
    {'name':'Pisces',      'ka':'თევზები',     'sym':'♓',  'start':351.5, 'end':389.0},
]

def get_true_constellation(trop_deg):
    deg = trop_deg % 360
    for con in TRUE_CONSTELLATIONS:
        s = con['start'] % 360
        e = con['end'] % 360
        if s < e:
            if s <= deg < e:
                return con, round(deg - s, 4)
        else:
            if deg >= s or deg < e:
                return con, round((deg - s) % 360, 4)
    return TRUE_CONSTELLATIONS[0], round(deg - 29.0, 4)

def true_sid_fmtDMS(con, pos_in_con):
    d = int(pos_in_con)
    m = int((pos_in_con - d) * 60)
    s = int(((pos_in_con - d) * 60 - m) * 60)
    return str(d) + chr(176) + str(m).zfill(2) + "'" + str(s).zfill(2) + '"'

@app.route('/true_sidereal', methods=['POST'])
def true_sidereal():
    swe.set_ephe_path(EPHE_PATH)
    d = request.json
    year,month,day = int(d['year']),int(d['month']),int(d['day'])
    hour,minute,second = int(d['hour']),int(d['minute']),int(d['second'])
    lat,lon = float(d['lat']),float(d['lon'])
    tz_name = d.get('tz_name','UTC')
    time_unknown = d.get('time_unknown', False)
    try:
        jd = to_jd(year,month,day,hour,minute,second,tz_name)
        planets = {}
        MAIN = {
            'Sun':swe.SUN,'Moon':swe.MOON,'Mercury':swe.MERCURY,'Venus':swe.VENUS,
            'Mars':swe.MARS,'Jupiter':swe.JUPITER,'Saturn':swe.SATURN,
            'Uranus':swe.URANUS,'Neptune':swe.NEPTUNE,'Pluto':swe.PLUTO,
        }
        FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED
        for name, pid in MAIN.items():
            pos,_ = swe.calc_ut(jd, pid, FLAGS)
            trop  = pos[0]
            con, pic = get_true_constellation(trop)
            span = (con['end'] - con['start']) % 360 or 360
            planets[name] = {
                'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],
                'pos_in_con':round(pic,4),'dms':true_sid_fmtDMS(con,pic),
                'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':pos[3]<0,
            }
        for name,pid in [('Chiron',swe.CHIRON),('Lilith',swe.MEAN_APOG)]:
            try:
                pos,_ = swe.calc_ut(jd,pid,FLAGS); trop=pos[0]
                con,pic = get_true_constellation(trop)
                span=(con['end']-con['start'])%360 or 360
                planets[name]={'tropical':round(trop,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':pos[3]<0}
            except: pass
        for ast_name,ast_id in [('Selena',swe.AST_OFFSET+1181),('Juno',swe.AST_OFFSET+3)]:
            try:
                pos,_ = swe.calc_ut(jd,ast_id,FLAGS); trop=pos[0]
                con,pic = get_true_constellation(trop)
                span=(con['end']-con['start'])%360 or 360
                planets[ast_name]={'tropical':round(trop,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':bool(pos[3]<0)}
            except: pass
        try:
            pos,_ = swe.calc_ut(jd,swe.MEAN_NODE,FLAGS); trop=pos[0]
            con,pic = get_true_constellation(trop)
            span=(con['end']-con['start'])%360 or 360
            planets['North Node']={'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':True}
            trop2=(trop+180)%360; con2,pic2=get_true_constellation(trop2)
            span2=(con2['end']-con2['start'])%360 or 360
            planets['South Node']={'tropical':round(trop2,4),'constellation':con2['name'],
                'constellation_ka':con2['ka'],'sym':con2['sym'],'pos_in_con':round(pic2,4),
                'dms':true_sid_fmtDMS(con2,pic2),'span':round(span2,1),'pct':round(pic2/span2*100,1),'retrograde':True}
        except: pass
        cusps,ascmc = swe.houses(jd,lat,lon,b'P')
        asc_trop=float(ascmc[0]); mc_trop=float(ascmc[1])
        asc_con,asc_pic=get_true_constellation(asc_trop)
        mc_con,mc_pic=get_true_constellation(mc_trop)
        for name in planets:
            planets[name]['house']=get_house(planets[name]['tropical'],cusps)
        if not time_unknown:
            try:
                vx=float(ascmc[3]); con,pic=get_true_constellation(vx)
                span=(con['end']-con['start'])%360 or 360
                planets['Vertex']={'tropical':round(vx,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),
                    'retrograde':False,'house':get_house(vx,cusps)}
            except: pass
            try:
                f=(asc_trop+planets['Moon']['tropical']-planets['Sun']['tropical'])%360
                con,pic=get_true_constellation(f); span=(con['end']-con['start'])%360 or 360
                planets['Fortune']={'tropical':round(f,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),
                    'retrograde':False,'house':get_house(f,cusps)}
            except: pass
        try: lunar=calc_lunar_day(jd)
        except: lunar=None
        ENG_TO_KA={'Sun':'მზე','Moon':'მთვარე','Mercury':'მერკური','Venus':'ვენერა',
            'Mars':'მარსი','Jupiter':'იუპიტერი','Saturn':'სატურნი','Uranus':'ურანი',
            'Neptune':'ნეპტუნი','Pluto':'პლუტონი','Chiron':'ქირონი','North Node':'ჩრდ. კვანძი'}
        KA_TO_ENG={v:k for k,v in ENG_TO_KA.items()}
        trop_planets={ENG_TO_KA.get(n,n):{'degree':p['tropical']} for n,p in planets.items() if 'tropical' in p}
        aspects=calc_aspects(trop_planets)
        for asp in aspects:
            asp['p1']=KA_TO_ENG.get(asp['p1'],asp['p1'])
            asp['p2']=KA_TO_ENG.get(asp['p2'],asp['p2'])
        return jsonify({
            'planets':planets,'houses':[round(x,4) for x in cusps],
            'asc':round(asc_trop,4),'mc':round(mc_trop,4),
            'asc_con':asc_con['name'],'asc_con_ka':asc_con['ka'],'mc_con':mc_con['name'],
            'lunar':lunar,'aspects':aspects,'lat':lat,'lon':lon,'tz_name':tz_name,
            'constellations':[{'name':x['name'],'ka':x['ka'],'sym':x['sym'],
                'start':x['start'],'end':x['end'],'span':round((x['end']-x['start'])%360 or 360,1)}
                for x in TRUE_CONSTELLATIONS],
        })
    except Exception as e:
        import traceback
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500

# ════════════════════════════════════════════════════════════════
# HUMAN DESIGN
# ════════════════════════════════════════════════════════════════

@app.route('/api/hd_chart', methods=['POST'])
def hd_chart():
    """Human Design chart.

    Format A — coords from frontend geocoding (preferred):
      {date, time, lat, lon, tz_name, place}

    Format B — place string, geocoded on backend:
      {date, time, place}
    """
    try:
        data = request.get_json(force=True)
        date_str = data.get("date", "").strip()
        time_str = data.get("time", "").strip()
        if not date_str or not time_str:
            return jsonify({"error": "date and time are required"}), 400

        # Format A: lat/lon/tz_name already provided by frontend /geocode call
        if data.get("lat") is not None and data.get("lon") is not None and data.get("tz_name"):
            from hd_calc import calculate_chart_from_coords
            result = calculate_chart_from_coords(
                date_str, time_str,
                float(data["lat"]), float(data["lon"]),
                data["tz_name"],
                resolved_place=data.get("place", ""),
            )
            return jsonify(result)

        # Format B: place string — backend geocodes (uses cache or OpenCage)
        place = data.get("place", "").strip()
        if not place:
            return jsonify({"error": "Either lat/lon/tz_name or place is required"}), 400
        result = hd_calculate_chart(date_str, time_str, place)
        return jsonify(result)

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        import traceback
        app.logger.exception("hd_chart error")
        return jsonify({"error": f"{type(e).__name__}: {e}",
                        "trace": traceback.format_exc()}), 500


# ════════════════════════════════════════════════════════════════
# STATIC
# ════════════════════════════════════════════════════════════════

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
