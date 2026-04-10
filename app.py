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

# Aspect definitions — angles covers BOTH directions
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
    """
    Check every planet pair. Compute raw angle A→B (0-360°).
    Match against ALL target angles (both directions):
      conjunction: 0°          orb ±8°
      opposition:  180°        orb ±8°
      trine:       120° or 240° orb ±7°
      square:      90°  or 270° orb ±6°
      sextile:     60°  or 300° orb ±5°
      inconjunction: 150° or 210° orb ±3°
    """
    aspects = []
    names = [n for n in ASPECT_PLANETS if n in planets]
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            d1 = planets[p1]['degree']
            d2 = planets[p2]['degree']
            raw = (d2 - d1 + 360) % 360  # 0–360°
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
        # Aspects using sidereal degrees, map Eng→Georgian for calc_aspects
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
            'aspects':aspects,
            'lat':lat,'lon':lon,'tz_name':tz_name})
    except Exception as e:
        import traceback
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500
    finally:
        try: swe.set_sid_mode(swe.SIDM_TROPICAL, 0, 0)
        except: pass


# ════════════════════════════════════════════════════════════════
# TRUE SIDEREAL ASTROLOGY — /true_sidereal endpoint
# 13 constellations with IAU boundaries, Ophiuchus included
# ════════════════════════════════════════════════════════════════

# IAU ecliptic constellation boundaries (tropical degrees)
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
    {'name':'Pisces',      'ka':'თევზები',     'sym':'♓',  'start':351.5, 'end':389.0},  # wraps
]

def get_true_constellation(trop_deg):
    """Get true IAU constellation from tropical degree."""
    deg = trop_deg % 360
    for con in TRUE_CONSTELLATIONS:
        s = con['start'] % 360
        e = con['end'] % 360
        if s < e:
            if s <= deg < e:
                pos = deg - s
                return con, round(pos, 4)
        else:  # wraps around 0 (Pisces: 351.5-29.0)
            if deg >= s or deg < e:
                pos = (deg - s) % 360
                return con, round(pos, 4)
    # fallback: Aries
    return TRUE_CONSTELLATIONS[0], round(deg - 29.0, 4)

def true_sid_fmtDMS(con, pos_in_con):
    d = int(pos_in_con)
    m = int((pos_in_con - d) * 60)
    s = int(((pos_in_con - d) * 60 - m) * 60)
    return str(d) + chr(176) + str(m).zfill(2) + "'" + str(s).zfill(2) + '"' 

@app.route('/true_sidereal', methods=['POST'])
def true_sidereal():
    swe.set_ephe_path(EPHE_PATH)
    # Use tropical positions — constellation determined by IAU boundaries
    d = request.json
    year    = int(d['year']);   month  = int(d['month'])
    day     = int(d['day']);    hour   = int(d['hour'])
    minute  = int(d['minute']); second = int(d['second'])
    lat     = float(d['lat']); lon    = float(d['lon'])
    tz_name = d.get('tz_name','UTC')
    time_unknown = d.get('time_unknown', False)

    try:
        jd = to_jd(year,month,day,hour,minute,second,tz_name)
        planets = {}

        MAIN = {
            'მზე':     swe.SUN,    'მთვარე':    swe.MOON,
            'მერკური': swe.MERCURY,'ვენერა':   swe.VENUS,
            'მარსი':    swe.MARS,   'იუპიტერი': swe.JUPITER,
            'სატურნი':  swe.SATURN, 'ურანი':  swe.URANUS,
            'ნეპტუნი': swe.NEPTUNE,'პლუტონი':   swe.PLUTO,
        }
        FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

        for name, pid in MAIN.items():
            pos,_ = swe.calc_ut(jd, pid, FLAGS)
            trop  = pos[0]
            con, pos_in_con = get_true_constellation(trop)
            span = (con['end'] - con['start']) % 360 or 360
            pct  = round(pos_in_con / span * 100, 1)
            planets[name] = {
                'tropical':     round(trop, 4),
                'constellation':con['name'],
                'constellation_ka': con['ka'],
                'sym':          con['sym'],
                'pos_in_con':   round(pos_in_con, 4),
                'dms':          true_sid_fmtDMS(con, pos_in_con),
                'span':         round(span, 1),
                'pct':          pct,
                'retrograde':   pos[3] < 0,
            }

        # Chiron
        try:
            pos,_ = swe.calc_ut(jd, swe.CHIRON, FLAGS)
            trop = pos[0]; con,pic = get_true_constellation(trop)
            span = (con['end']-con['start'])%360 or 360
            planets['Chiron'] = {'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':pos[3]<0}
        except: pass

        # Lilith
        try:
            pos,_ = swe.calc_ut(jd, swe.MEAN_APOG, FLAGS)
            trop = pos[0]; con,pic = get_true_constellation(trop)
            span = (con['end']-con['start'])%360 or 360
            planets['Lilith'] = {'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':False}
        except: pass

        # Selena (White Moon)
        try:
            pos,_ = swe.calc_ut(jd, swe.AST_OFFSET+1181, FLAGS)
            trop = pos[0]; con,pic = get_true_constellation(trop)
            span = (con['end']-con['start'])%360 or 360
            planets['Selena'] = {'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':False}
        except: pass

        # Juno
        try:
            pos,_ = swe.calc_ut(jd, swe.AST_OFFSET+3, FLAGS)
            trop = pos[0]; con,pic = get_true_constellation(trop)
            span = (con['end']-con['start'])%360 or 360
            planets['Juno'] = {'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':bool(pos[3]<0)}
        except: pass

        # Nodes
        try:
            pos,_ = swe.calc_ut(jd, swe.MEAN_NODE, FLAGS)
            trop = pos[0]; con,pic = get_true_constellation(trop)
            span = (con['end']-con['start'])%360 or 360
            planets['North Node'] = {'tropical':round(trop,4),'constellation':con['name'],
                'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),'retrograde':True}
            trop2=(trop+180)%360; con2,pic2=get_true_constellation(trop2)
            span2=(con2['end']-con2['start'])%360 or 360
            planets['South Node'] = {'tropical':round(trop2,4),'constellation':con2['name'],
                'constellation_ka':con2['ka'],'sym':con2['sym'],'pos_in_con':round(pic2,4),
                'dms':true_sid_fmtDMS(con2,pic2),'span':round(span2,1),'pct':round(pic2/span2*100,1),'retrograde':True}
        except: pass

        # Houses + ASC/MC (tropical, Placidus)
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        asc_trop = float(ascmc[0]); mc_trop = float(ascmc[1])
        asc_con, asc_pic = get_true_constellation(asc_trop)
        mc_con,  mc_pic  = get_true_constellation(mc_trop)

        # Assign house to each planet
        for name in planets:
            planets[name]['house'] = get_house(planets[name]['tropical'], cusps)

        # Vertex + Fortuna (time known only)
        if not time_unknown:
            try:
                vx = float(ascmc[3]); con,pic = get_true_constellation(vx)
                span=(con['end']-con['start'])%360 or 360
                planets['Vertex'] = {'tropical':round(vx,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),
                    'retrograde':False,'house':get_house(vx,cusps)}
            except: pass
            try:
                f=(asc_trop+planets['Moon']['tropical']-planets['Sun']['tropical'])%360
                con,pic=get_true_constellation(f); span=(con['end']-con['start'])%360 or 360
                planets['Fortune'] = {'tropical':round(f,4),'constellation':con['name'],
                    'constellation_ka':con['ka'],'sym':con['sym'],'pos_in_con':round(pic,4),
                    'dms':true_sid_fmtDMS(con,pic),'span':round(span,1),'pct':round(pic/span*100,1),
                    'retrograde':False,'house':get_house(f,cusps)}
            except: pass

        # Lunar day
        try:
            lunar = calc_lunar_day(jd)
        except:
            lunar = None

        # Aspects — use tropical degrees with English names mapped to Georgian for calc_aspects
        # calc_aspects uses Georgian planet names, so map English→Georgian
        ENG_TO_KA = {
            'Sun':'მზე','Moon':'მთვარე','Mercury':'მერკური','Venus':'ვენერა',
            'Mars':'მარსი','Jupiter':'იუპიტერი','Saturn':'სატურნი',
            'Uranus':'ურანი','Neptune':'ნეპტუნი','Pluto':'პლუტონი',
            'Chiron':'ქირონი','North Node':'ჩრდ. კვანძი',
        }
        trop_planets = {}
        for name,p in planets.items():
            if 'tropical' in p:
                ka = ENG_TO_KA.get(name, name)
                trop_planets[ka] = {'degree': p['tropical']}
        aspects = calc_aspects(trop_planets)
        # Map aspect planet names back to English for frontend
        KA_TO_ENG = {v:k for k,v in ENG_TO_KA.items()}
        for asp in aspects:
            asp['p1'] = KA_TO_ENG.get(asp['p1'], asp['p1'])
            asp['p2'] = KA_TO_ENG.get(asp['p2'], asp['p2'])

        return jsonify({
            'planets':  planets,
            'houses':   [round(x,4) for x in cusps],
            'asc':      round(asc_trop,4),
            'mc':       round(mc_trop,4),
            'asc_con':  asc_con['name'],
            'asc_con_ka': asc_con['ka'],
            'mc_con':   mc_con['name'],
            'lunar':    lunar,
            'aspects':  aspects,
            'lat':lat,'lon':lon,'tz_name':tz_name,
            'constellations': [{'name':x['name'],'ka':x['ka'],'sym':x['sym'],
                'start':x['start'],'end':x['end'],'span':round((x['end']-x['start'])%360 or 360,1)}
                for x in TRUE_CONSTELLATIONS],
        })
    except Exception as e:
        import traceback
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500


if __name__ == '__main__':
    port=int(os.environ.get("PORT",8080))
    app.run(host='0.0.0.0',port=port)
