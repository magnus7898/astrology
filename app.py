import os, math, urllib.request, urllib.parse, json as _json

# ── EPHE PATH ──────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
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

app = Flask(__name__)
CORS(app, origins="*")
tf = TimezoneFinder()

# ════════════════════════════════════════════════════════════════
# SHARED HELPERS
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
# GEOCODE
# ════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return jsonify({'status':'ok','message':'Astrology API — Western + Vedic'})

@app.route('/geocode', methods=['POST'])
def geocode():
    try:
        city = request.json.get('city','').strip()
        if not city:
            return jsonify({'error':'City name is empty'}), 400
        # Try geopy first
        try:
            geo = Nominatim(user_agent="astro-api-v3", timeout=10)
            loc = geo.geocode(city, language='en', exactly_one=True)
        except:
            loc = None
        # Fallback: direct HTTP
        if not loc:
            try:
                q = urllib.parse.urlencode({'q':city,'format':'json','limit':1})
                req = urllib.request.Request(
                    f'https://nominatim.openstreetmap.org/search?{q}',
                    headers={'User-Agent':'astro-api-v3'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    res = _json.loads(r.read())
                if res:
                    lat,lon = float(res[0]['lat']),float(res[0]['lon'])
                    tz = tf.timezone_at(lat=lat,lng=lon) or 'UTC'
                    return jsonify({'lat':lat,'lon':lon,'tz_name':tz,'display':res[0].get('display_name',city)})
            except: pass
            return jsonify({'error':'City not found: '+city}), 404
        lat,lon = loc.latitude, loc.longitude
        tz = tf.timezone_at(lat=lat,lng=lon) or 'UTC'
        return jsonify({'lat':lat,'lon':lon,'tz_name':tz,'display':loc.address})
    except Exception as e:
        return jsonify({'error':str(e)}), 500

# ════════════════════════════════════════════════════════════════
# WESTERN CHART
# ════════════════════════════════════════════════════════════════

ASPECTS_DEF = [
    {'name':'შეერთება',      'angle':0,   'orb':8, 'sym':'☌','color':'#f9c646'},
    {'name':'სექსტილი',      'angle':60,  'orb':6, 'sym':'⚹','color':'#30c890'},
    {'name':'კვადრატი',      'angle':90,  'orb':8, 'sym':'□','color':'#e84040'},
    {'name':'ტრინი',         'angle':120, 'orb':8, 'sym':'△','color':'#a078f0'},
    {'name':'ოპოზიცია',      'angle':180, 'orb':8, 'sym':'☍','color':'#e89040'},
    {'name':'კვინკუნქსი',    'angle':150, 'orb':3, 'sym':'⚻','color':'#9ba8b8'},
    {'name':'ნახ.-სექსტ.',   'angle':30,  'orb':2, 'sym':'⚺','color':'#7080a0'},
    {'name':'ნახ.-კვად.',    'angle':45,  'orb':2, 'sym':'∠','color':'#c06060'},
    {'name':'სესკვიკვად.',   'angle':135, 'orb':2, 'sym':'⚼','color':'#c08040'},
    {'name':'კვინტილი',      'angle':72,  'orb':2, 'sym':'Q', 'color':'#50b0d0'},
    {'name':'ბიკვინტილი',    'angle':144, 'orb':2, 'sym':'bQ','color':'#60a0c0'},
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
            p1,p2 = names[i],names[j]
            diff = abs(planets[p1]['degree'] - planets[p2]['degree'])
            if diff > 180: diff = 360 - diff
            for asp in ASPECTS_DEF:
                orb = abs(diff - asp['angle'])
                if orb <= asp['orb']:
                    aspects.append({'p1':p1,'p2':p2,'type':asp['name'],
                        'sym':asp['sym'],'color':asp['color'],'orb':round(orb,2),'angle':asp['angle']})
                    break
    aspects.sort(key=lambda x: x['orb'])
    return aspects

def calc_lunar_day(jd_ut, tz_offset=0.0):
    swe.set_ephe_path(EPHE_PATH)
    sun,_  = swe.calc_ut(jd_ut, swe.SUN)
    moon,_ = swe.calc_ut(jd_ut, swe.MOON)
    elong  = (moon[0] - sun[0] + 360) % 360
    deg_per_day = 12.0
    age = elong / deg_per_day
    lunar_day = int(age) + 1
    pct_elapsed = round((age % 1) * 100, 2)
    rel_speed = 360.0 / (29.53058868 * 24.0)
    hours_to_next = round((deg_per_day - elong % deg_per_day) / rel_speed, 2)
    if elong < 45:    phase = 'ახალი მთვარე'
    elif elong < 90:  phase = 'მზარდი'
    elif elong < 135: phase = 'I მეოთხედი'
    elif elong < 180: phase = 'მზარდი სავსე'
    elif elong < 225: phase = 'სავსე მთვარე'
    elif elong < 270: phase = 'კლება'
    elif elong < 315: phase = 'III მეოთხედი'
    else:             phase = 'კლება'
    return {
        'lunar_day':lunar_day,'pct_elapsed':pct_elapsed,
        'pct_remaining':round(100-pct_elapsed,2),
        'hours_to_next':hours_to_next,'elongation':round(elong,2),
        'phase':phase,'moon_deg':round(moon[0],4),'sun_deg':round(sun[0],4),
    }

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

    for name,pid,key in [
        ('ქირონი',swe.CHIRON,'chiron'),
        ('ლილიტი',swe.MEAN_APOG,'lilith')]:
        try:
            pos,_ = swe.calc_ut(jd,pid); deg=pos[0]; dv,c=deg_to_display(deg)
            planets[name]={'degree':round(deg,4),'sign':trop_sign(deg),
                'sign_degree':dv,'centesimal':c,'retrograde':bool(pos[3]<0) if len(pos)>3 else False}
        except: pass

    try:
        pos,_ = swe.calc_ut(jd,swe.AST_OFFSET+1181); deg=pos[0]; dv,c=deg_to_display(deg)
        planets['თეთრი მთვარე']={'degree':round(deg,4),'sign':trop_sign(deg),
            'sign_degree':dv,'centesimal':c,'retrograde':False}
    except:
        try:
            pos,_ = swe.calc_ut(jd,56); deg=pos[0]; dv,c=deg_to_display(deg)
            planets['თეთრი მთვარე']={'degree':round(deg,4),'sign':trop_sign(deg),
                'sign_degree':dv,'centesimal':c,'retrograde':False}
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
            # Tropical positions
            result['moon_path']={'start':round(m0[0],4),'end':round(m1[0],4)}
            # Sidereal positions (Lahiri) for Vedic chart
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
        return jsonify({'planets':planets,'asc':round(asc_sid,4),'mc':round(mc_sid,4),
            'asc_sign':ved_sign(asc_sid),'asc_sign_idx':lagna_si,'mc_sign':ved_sign(mc_sid),
            'ayanamsa':round(ayanamsa,4),'lagna_nak':get_nakshatra(asc_sid),
            'lat':lat,'lon':lon,'tz_name':tz_name})
    except Exception as e:
        import traceback
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500
    finally:
        try: swe.set_sid_mode(swe.SIDM_TROPICAL, 0, 0)
        except: pass


if __name__ == '__main__':
    port=int(os.environ.get("PORT",8080))
    app.run(host='0.0.0.0',port=port)
