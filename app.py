<!DOCTYPE html>
<html lang="ka">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ნამდვილი სიდერული ასტროლოგია</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400&family=Cinzel:wght@300;400;600&family=IM+Fell+English:ital@0;1&family=Noto+Sans+Georgian:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{
  --void:#04030a;--gold:#c9a84c;--gold-l:#f0d080;--gold-d:#8a6a20;
  --purple:#a78bfa;--purple-d:#2d1f6e;--txt:#e0d8ff;--dim:rgba(155,168,184,0.6);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--void);color:var(--txt);font-family:'Noto Sans Georgian',sans-serif;
  min-height:100vh;display:flex;flex-direction:column;align-items:center;
  padding:0 0 80px;overflow-x:hidden;position:relative;}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:
  radial-gradient(1px 1px at 8% 12%,rgba(255,255,255,.55) 0,transparent 100%),
  radial-gradient(1px 1px at 23% 35%,rgba(255,255,255,.35) 0,transparent 100%),
  radial-gradient(1px 1px at 41% 8%,rgba(255,255,255,.45) 0,transparent 100%),
  radial-gradient(1px 1px at 60% 25%,rgba(255,255,255,.3) 0,transparent 100%),
  radial-gradient(1px 1px at 77% 13%,rgba(255,255,255,.5) 0,transparent 100%),
  radial-gradient(1px 1px at 88% 44%,rgba(255,255,255,.35) 0,transparent 100%),
  radial-gradient(1px 1px at 15% 68%,rgba(255,255,255,.3) 0,transparent 100%),
  radial-gradient(1px 1px at 50% 75%,rgba(255,255,255,.4) 0,transparent 100%),
  radial-gradient(1.5px 1.5px at 34% 51%,rgba(167,139,250,.25) 0,transparent 100%),
  radial-gradient(1.5px 1.5px at 66% 44%,rgba(201,168,76,.18) 0,transparent 100%);}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:
  radial-gradient(ellipse 600px 400px at 20% 20%,rgba(100,40,200,.08) 0,transparent 70%),
  radial-gradient(ellipse 500px 500px at 80% 70%,rgba(40,80,200,.06) 0,transparent 70%),
  radial-gradient(ellipse 400px 300px at 50% 90%,rgba(120,50,180,.05) 0,transparent 70%);}
.hero{position:relative;z-index:1;text-align:center;padding:56px 24px 40px;width:100%}
.hero-eyebrow{font-size:9px;letter-spacing:7px;text-transform:uppercase;color:var(--gold);opacity:.5;margin-bottom:12px;font-family:'Cinzel',serif}
.hero-title{font-family:'Cinzel Decorative',serif;font-size:clamp(18px,3.5vw,38px);font-weight:400;letter-spacing:3px;line-height:1.2;
  background:linear-gradient(160deg,#f5e8ba 0%,var(--gold) 35%,#9a7028 60%,#e8d5a0 80%,#c09040 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 28px rgba(201,168,76,.25));}
.hero-sub{font-family:'IM Fell English',serif;font-style:italic;font-size:13px;color:var(--dim);margin-top:10px}
.hero-divider{display:flex;align-items:center;gap:14px;margin:24px auto 0;max-width:300px}
.hero-line{flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(201,168,76,.35),transparent)}
.hero-gem{width:5px;height:5px;background:var(--gold);transform:rotate(45deg);opacity:.5;flex-shrink:0}
.form-card{position:relative;z-index:1;background:rgba(8,6,20,.75);border:1px solid rgba(45,31,110,.6);
  border-radius:16px;padding:24px;width:100%;max-width:620px;margin:32px auto;backdrop-filter:blur(12px);
  box-shadow:0 8px 40px rgba(0,0,0,.5),inset 0 1px 0 rgba(167,139,250,.08);}
.form-card::before{content:'';position:absolute;top:0;left:20%;right:20%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(167,139,250,.4),transparent);}
.form-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.field{display:flex;flex-direction:column;gap:5px}
.field.wide{grid-column:span 3}
label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);opacity:.7;font-family:'Cinzel',serif}
input{background:rgba(10,8,30,.7);border:1px solid rgba(61,42,138,.6);border-radius:8px;
  color:var(--txt);padding:9px 12px;font-size:13px;font-family:'Noto Sans Georgian',sans-serif;
  width:100%;transition:border-color .2s,box-shadow .2s;}
input:focus{outline:none;border-color:var(--purple);box-shadow:0 0 0 3px rgba(124,58,237,.15)}
input::placeholder{color:rgba(155,168,184,.35)}
.coords-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.coords input{background:rgba(6,5,18,.7);color:rgba(155,168,184,.6)}
#city-hint{font-size:11px;color:var(--purple);margin-top:3px;min-height:15px;padding-left:2px}
#tz-display{font-size:11px;color:var(--gold);margin-bottom:16px;background:rgba(6,5,18,.5);border-radius:6px;padding:6px 10px;border-left:2px solid rgba(201,168,76,.3)}
.gen-btn{width:100%;background:linear-gradient(135deg,#6d28d9,#4c1d95);color:#fff;
  border:1px solid rgba(124,58,237,.4);border-radius:10px;padding:13px;font-size:13px;
  cursor:pointer;letter-spacing:2px;font-family:'Cinzel',serif;transition:all .3s;
  box-shadow:0 4px 20px rgba(109,40,217,.3);}
.gen-btn:hover{background:linear-gradient(135deg,#7c3aed,#5b21b6);transform:translateY(-1px)}
.time-disabled input{opacity:.3;pointer-events:none}
#chart-area{position:relative;z-index:1;width:100%;max-width:800px;padding:0 16px}
svg#wheel{width:100%;height:auto;display:block;overflow:visible}
.sec-title{font-family:'Cinzel',serif;font-size:11px;letter-spacing:4px;color:var(--gold);
  text-transform:uppercase;text-align:center;margin:32px 0 16px;display:flex;align-items:center;gap:14px;}
.sec-title::before,.sec-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(201,168,76,.3),transparent)}
.tables-wrap{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px}
@media(max-width:600px){.tables-wrap{grid-template-columns:1fr}}
.data-card{background:rgba(8,6,20,.75);border:1px solid rgba(45,31,110,.5);border-radius:12px;overflow:hidden;backdrop-filter:blur(8px)}
.data-card-title{background:rgba(167,139,250,.07);padding:10px 16px;font-family:'Cinzel',serif;font-size:10px;letter-spacing:3px;color:var(--purple);text-transform:uppercase;border-bottom:1px solid rgba(45,31,110,.5)}
table{width:100%;border-collapse:collapse;font-size:12px}
th{color:rgba(155,168,184,.5);padding:7px 12px;text-align:left;font-weight:400;font-size:9px;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid rgba(45,31,110,.4)}
td{padding:6px 12px;border-bottom:1px solid rgba(15,13,40,.8);vertical-align:middle;font-size:12px}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(19,16,58,.6)}
.retro{color:#f87171;font-size:9px;margin-left:2px}
.house-badge{display:inline-block;background:rgba(26,21,69,.8);border:1px solid rgba(61,42,138,.6);border-radius:4px;padding:1px 6px;font-size:10px;color:var(--purple);font-family:'Cinzel',serif}
.deg-val{font-family:'Cinzel',serif;font-size:11px;color:#c8d8f0;white-space:nowrap}
.moon-sym{color:#b8d8ff;text-shadow:0 0 8px rgba(100,160,255,.9),0 0 16px rgba(80,130,255,.5);font-size:20px;font-family:serif}
.p-sym{font-family:serif;font-size:18px;line-height:1;display:inline-block}
.pct-bar{display:inline-block;width:48px;height:3px;background:rgba(255,255,255,.08);border-radius:2px;vertical-align:middle;margin-left:5px;position:relative}
.pct-fill{position:absolute;left:0;top:0;height:100%;border-radius:2px;background:linear-gradient(90deg,var(--purple),var(--gold))}
@media(max-width:480px){td{padding:5px 8px;font-size:10px}th{font-size:9px;padding:5px 8px}}
</style>
</head>
<body>
<div class="hero">
  <svg width="56" height="56" viewBox="0 0 56 56" fill="none" style="margin:0 auto 20px;display:block;opacity:.7">
    <circle cx="28" cy="28" r="26.5" stroke="rgba(201,168,76,.25)" stroke-width=".5"/>
    <circle cx="28" cy="28" r="17" stroke="rgba(201,168,76,.18)" stroke-width=".5"/>
    <polygon points="28,3 51,43 5,43" stroke="rgba(201,168,76,.38)" stroke-width=".5" fill="none"/>
    <polygon points="28,53 5,13 51,13" stroke="rgba(201,168,76,.38)" stroke-width=".5" fill="none"/>
    <circle cx="28" cy="28" r="2.5" fill="rgba(201,168,76,.7)"/>
  </svg>
  <div class="hero-eyebrow">ასტრონომიული · IAU კონსტელაციები · ოფიუქუსი</div>
  <h1 class="hero-title">ნამდვილი სიდერული ასტროლოგია</h1>
  <p class="hero-sub">True Sidereal · 13 Constellations · IAU Boundaries · Ophiuchus ⛎</p>
  <div class="hero-divider"><div class="hero-line"></div><div class="hero-gem"></div><div class="hero-line"></div></div>
</div>

<div class="form-card">
  <div class="field wide" style="margin-bottom:12px">
    <label>სახელი</label><input id="name" placeholder="შეიყვანეთ სახელი">
  </div>
  <div class="form-grid">
    <div class="field"><label>დღე</label><input type="number" id="day" value="1" min="1" max="31"></div>
    <div class="field"><label>თვე</label><input type="number" id="month" value="1" min="1" max="12"></div>
    <div class="field"><label>წელი</label><input type="number" id="year" value="1990"></div>
  </div>
  <div class="form-grid" id="time-fields">
    <div class="field"><label>საათი</label><input type="number" id="hour" value="12" min="0" max="23"></div>
    <div class="field"><label>წუთი</label><input type="number" id="minute" value="0" min="0" max="59"></div>
    <div class="field"><label>წამი</label><input type="number" id="second" value="0" min="0" max="59"></div>
  </div>
  <div style="margin-bottom:12px;display:flex;align-items:center;gap:10px">
    <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:11px;color:rgba(167,139,250,0.7);letter-spacing:1px;text-transform:none">
      <input type="checkbox" id="time-unknown" onchange="toggleTimeUnknown()" style="width:16px;height:16px;accent-color:#7c3aed;cursor:pointer">
      დრო უცნობია (time unknown)
    </label>
  </div>
  <div class="field wide" style="margin-bottom:8px">
    <label>ქალაქი</label>
    <input id="city" placeholder="მაგ. თბილისი, London, Paris..." oninput="searchCity()">
    <div id="city-hint"></div>
  </div>
  <div class="coords-row">
    <div class="field"><label>განედი (Lat)</label><input type="number" id="lat" step="0.0001" readonly></div>
    <div class="field"><label>გრძედი (Lon)</label><input type="number" id="lon" step="0.0001" readonly></div>
  </div>
  <div id="tz-display">⏳ ქალაქის შეყვანის შემდეგ სარტყელი განისაზღვრება</div>
  <input type="hidden" id="tz_name" value="UTC">
  <button class="gen-btn" onclick="generateChart()">✦ რუქის გენერაცია ✦</button>
</div>

<div id="chart-area" style="display:none">
  <div id="lunar-badge" style="display:none;text-align:center;margin-bottom:12px;padding:10px 20px;background:rgba(8,6,22,.8);border:1px solid rgba(100,70,200,.4);border-radius:12px;backdrop-filter:blur(8px)">
    <span style="font-size:20px;margin-right:8px">🌙</span>
    <span id="lunar-day" style="font-family:'Cinzel',serif;font-size:13px;color:#c8d8f0;font-weight:600"></span>
    <span style="color:rgba(150,120,220,.5);margin:0 6px">·</span>
    <span id="lunar-pct" style="font-size:11px;color:rgba(180,150,255,.65)"></span>
  </div>
  <div class="sec-title">სიდერული ბორბალი · 13 კონსტელაცია</div>
  <svg id="wheel" viewBox="0 0 700 700" xmlns="http://www.w3.org/2000/svg"></svg>

  <div class="sec-title">პლანეტები · Planets</div>
  <div class="tables-wrap">
    <div class="data-card">
      <div class="data-card-title">🪐 პლანეტები</div>
      <table><thead><tr><th></th><th>სახელი</th><th>პოზიცია</th><th>კონსტელაცია</th><th>სახ.</th><th>℞</th></tr></thead>
      <tbody id="planet-tbody"></tbody></table>
    </div>
    <div class="data-card">
      <div class="data-card-title">🏠 სახლები · Placidus Houses</div>
      <table><thead><tr><th>სახლი</th><th>კონსტელაცია</th><th>გრადუსი</th></tr></thead>
      <tbody id="house-tbody"></tbody></table>
    </div>
  </div>

  <div class="sec-title">ასპექტები · Aspects</div>
  <div class="data-card" style="margin-bottom:8px">
    <div class="data-card-title">⚡ მთავარი ასპექტები</div>
    <table><thead><tr><th>პლანეტა 1</th><th>ასპ.</th><th>პლანეტა 2</th><th>ტიპი</th><th>ორბი</th></tr></thead>
    <tbody id="aspect-tbody"></tbody></table>
  </div>

  <div class="sec-title">კონსტელაციების განაწილება</div>
  <div class="data-card" style="margin-bottom:8px">
    <div class="data-card-title">📐 IAU კონსტელაციები · ეკლიპტიკაზე</div>
    <table><thead><tr><th>კონსტელაცია</th><th>დასაწყისი</th><th>დასასრული</th><th>სიგანე</th><th>%</th></tr></thead>
    <tbody id="con-tbody"></tbody></table>
  </div>
</div>

<script>
const BACKEND='https://astrology-production-b165.up.railway.app';
const CX=350,CY=350,R1=270,R2=202,R3=135,R4=105;

// Planet info matching astro.html
const PI={
  'Sun':    {sym:'sun',  color:'#f9c646'},
  'Moon':   {sym:'\u263d',color:'#c8d8f0'},
  'Mercury':{sym:'\u263f',color:'#a0c8d0'},
  'Venus':  {sym:'\u2640',color:'#e87878'},
  'Mars':   {sym:'\u2642',color:'#e84040'},
  'Jupiter':{sym:'\u2643',color:'#e89040'},
  'Saturn': {sym:'\u2644',color:'#c8c840'},
  'Uranus': {sym:'\u2645',color:'#50c8d8'},
  'Neptune':{sym:'\u2646',color:'#6070d8'},
  'Pluto':  {sym:'\u2bd3',color:'#c050a0'},
  'Chiron': {sym:'\u26b7',color:'#d08040'},
  'Lilith': {sym:'\u26b8',color:'#904060'},
  'Selena': {sym:'\u2bdd\ufe0e',color:'#d0e8f8'},
  'Juno':   {sym:'\u26b5',color:'#c890d0'},
  'North Node':{sym:'\u260a',color:'#60c060'},
  'South Node':{sym:'\u260b',color:'#c06060'},
  'Vertex': {sym:'Vx',  color:'#8090d0'},
  'Fortune':{sym:'\u2295',color:'#f0c060'},
};
const PORDER=['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn',
  'Uranus','Neptune','Pluto','Chiron','Lilith','Selena','Juno',
  'North Node','South Node','Vertex','Fortune'];

// Element colors by constellation
const CON_COLORS={
  'Aries':'#e05252','Taurus':'#8aab6e','Gemini':'#89b4d4','Cancer':'#5b8ec4',
  'Leo':'#d4602e','Virgo':'#7a9e6a','Libra':'#7fb8d8','Scorpius':'#4a7ab0',
  'Ophiuchus':'#9060d0','Sagittarius':'#c84a32','Capricornus':'#6b9062',
  'Aquarius':'#90c0dc','Pisces':'#6688c0'
};
const CON_FILLS={
  'Aries':'#1a0808','Taurus':'#081008','Gemini':'#08101a','Cancer':'#08101a',
  'Leo':'#1a0a06','Virgo':'#081008','Libra':'#08101a','Scorpius':'#100818',
  'Ophiuchus':'#0e0818','Sagittarius':'#1a0808','Capricornus':'#081008',
  'Aquarius':'#08101a','Pisces':'#080c18'
};

// ROMAN numerals
const ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
const SIGN_KA={'Aries':'ვერძი','Taurus':'კურო','Gemini':'ტყუპები','Cancer':'კირჩხიბი',
  'Leo':'ლომი','Virgo':'ქალწული','Libra':'სასწორი','Scorpius':'მორიელი',
  'Ophiuchus':'გველმჭერი','Sagittarius':'მშვილდოსანი','Capricornus':'თხის რქა',
  'Aquarius':'მერწყული','Pisces':'თევზები'};

// Constellation data loaded from backend
let CONS=[];

function sunSVG(sz=22){
  return `<svg width="${sz}" height="${sz}" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;display:inline-block;overflow:visible">
    <defs><filter id="svf${sz}" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter></defs>
    <circle cx="11" cy="11" r="9" fill="none" stroke="#f9c646" stroke-width="1.8" filter="url(#svf${sz})"/>
    <circle cx="11" cy="11" r="9" fill="none" stroke="#ffe8a0" stroke-width="0.7"/>
    <circle cx="11" cy="11" r="2.5" fill="#f9c646" filter="url(#svf${sz})"/>
    <circle cx="11" cy="11" r="1.2" fill="#fff7d0"/>
  </svg>`;
}

function toggleTimeUnknown(){
  document.getElementById('time-fields').classList.toggle('time-disabled',
    document.getElementById('time-unknown').checked);
}

function displayLunarBadge(data){
  try{
    const L=data.lunar; if(!L) return;
    const hrs=L.hours_to_next, pct=L.pct_elapsed;
    let nextStr=hrs<1?`${Math.round(hrs*60)} წთ-ში`:`${Math.floor(hrs)} სთ ${Math.round((hrs%1)*60)} წთ-ში`;
    document.getElementById('lunar-day').textContent=`🌙 მთვარის მე-${L.lunar_day} დღე`;
    document.getElementById('lunar-pct').textContent=`შემდეგი ${nextStr} · ${pct}% გასული`;
    document.getElementById('lunar-badge').style.display='block';
  }catch(e){}
}

let cityTimer=null;
function searchCity(){
  clearTimeout(cityTimer);
  cityTimer=setTimeout(async()=>{
    const city=document.getElementById('city').value;
    if(city.length<2) return;
    const hint=document.getElementById('city-hint');
    hint.textContent='⏳ ძიება...';
    try{
      const r=await fetch(`${BACKEND}/geocode`,{method:'POST',
        headers:{'Content-Type':'application/json'},body:JSON.stringify({city})});
      const d=await r.json();
      if(d.error){hint.textContent='❌ '+d.error;return;}
      document.getElementById('lat').value=d.lat.toFixed(4);
      document.getElementById('lon').value=d.lon.toFixed(4);
      hint.textContent='📍 '+d.display;
      document.getElementById('tz_name').value=d.tz_name||'UTC';
      document.getElementById('tz-display').textContent='🕐 '+d.tz_name;
    }catch(e){hint.textContent='❌ '+e.message;}
  },600);
}

async function generateChart(){
  const lat=document.getElementById('lat').value;
  const lon=document.getElementById('lon').value;
  if(!lat||!lon){alert('პირველ შეიყვანეთ ქალაქი');return;}
  const btn=document.querySelector('.gen-btn');
  btn.textContent='⏳ გთხოვთ დაელოდოთ...';btn.disabled=true;
  const timeUnknown=document.getElementById('time-unknown').checked;
  const year=+document.getElementById('year').value;
  const month=+document.getElementById('month').value;
  const day=+document.getElementById('day').value;
  const tz_name=document.getElementById('tz_name').value;
  const hour=timeUnknown?12:+document.getElementById('hour').value;
  const minute=timeUnknown?0:+document.getElementById('minute').value;
  const second=timeUnknown?0:+document.getElementById('second').value;
  try{
    const r=await fetch(`${BACKEND}/true_sidereal`,{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({year,month,day,hour,minute,second,lat:+lat,lon:+lon,tz_name,time_unknown:timeUnknown})});
    const raw=await r.text();
    let data;
    try{data=JSON.parse(raw);}catch(e){throw new Error('Backend error ('+r.status+'): '+raw.slice(0,200));}
    if(data.error) throw new Error(data.error+(data.trace?'\n'+data.trace.slice(0,300):''));
    data._timeUnknown=timeUnknown;
    CONS=data.constellations;
    // Moon path for time-unknown
    if(timeUnknown){
      try{
        const lr=await fetch(`${BACKEND}/lunar`,{method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify({year,month,day,hour:12,minute:0,second:0,tz_name,time_unknown:true})});
        const ld=await lr.json();
        // Tropical moon path is correct for true sidereal (IAU uses tropical coords)
        if(ld.moon_path) data._moonPath=ld.moon_path;
      }catch(e){console.log('moon path error',e);}
    }
    document.getElementById('chart-area').style.display='block';
    drawWheel(data);
    drawPlanetTable(data);
    drawHouseTable(data);
    drawAspectTable(data);
    drawConTable(data);
    displayLunarBadge(data);
    document.getElementById('chart-area').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){alert('შეცდომა: '+e.message);}
  finally{btn.textContent='✦ რუქის გენერაცია ✦';btn.disabled=false;}
}

// ── SVG HELPERS ──
const NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){
  const e=document.createElementNS(NS,tag);
  for(const[k,v] of Object.entries(attrs)) e.setAttribute(k,v);
  if(parent) parent.appendChild(e);return e;
}
function txt(parent,s,x,y,attrs={}){
  const t=el('text',{'text-anchor':'middle','dominant-baseline':'central',x,y,...attrs},parent);
  t.textContent=s;return t;
}
function toRad(d){return d*Math.PI/180;}
// True sidereal: 0° = Aries start (29° tropical), wheel starts at left
// Tropical degree → angle on wheel
// Aries starts at 29° tropical = left (π)
const ARIES_START=29.0; // tropical (Aries IAU start)
function t2a(trop_deg, ref=ARIES_START){
  // Place ref degree at left (π), everything else rotates accordingly
  return toRad(-((trop_deg - ref + 360) % 360)) + Math.PI;
}
function ascConStart(asc_trop){
  // Find the IAU constellation containing asc, return its start degree
  // Use hardcoded boundaries (same as backend)
  const BOUNDS=[
    [29.0,53.5],[53.5,90.0],[90.0,118.5],[118.5,138.5],[138.5,174.0],
    [174.0,217.5],[217.5,241.0],[241.0,247.5],[247.5,266.5],[266.5,302.0],
    [302.0,327.0],[327.0,351.5],[351.5,389.0]
  ];
  const d=((asc_trop%360)+360)%360;
  for(const [s,e] of BOUNDS){
    const ss=s%360, ee=e%360;
    if(ss<ee?ss<=d&&d<ee:d>=ss||d<ee) return ss;
  }
  return ARIES_START;
}
function pxy(a,r){return{x:CX+Math.cos(a)*r,y:CY+Math.sin(a)*r};}

function drawWheel(data){
  const svg=document.getElementById('wheel');
  svg.innerHTML='';
  // Rising constellation start at left
  // ASC degree at left (9 o'clock position)
  const ascRef=data._timeUnknown?ARIES_START:data.asc;
  // ── DEFS ──
  const defs=el('defs',{},svg);
  const bgG=el('radialGradient',{id:'bgG',cx:'50%',cy:'50%',r:'50%'},defs);
  el('stop',{offset:'0%','stop-color':'#120e2a'},bgG);
  el('stop',{offset:'60%','stop-color':'#0a0820'},bgG);
  el('stop',{offset:'100%','stop-color':'#04030e'},bgG);
  const sf=el('filter',{id:'sunF',x:'-60%',y:'-60%',width:'220%',height:'220%'},defs);
  el('feGaussianBlur',{stdDeviation:'3',result:'blur'},sf);
  const sfm=el('feMerge',{},sf);el('feMergeNode',{in:'blur'},sfm);el('feMergeNode',{in:'SourceGraphic'},sfm);
  const mf=el('filter',{id:'moonF',x:'-60%',y:'-60%',width:'220%',height:'220%'},defs);
  el('feGaussianBlur',{stdDeviation:'2.5',result:'blur'},mf);
  const mfc=el('feFlood',{'flood-color':'#4090ff','flood-opacity':'0.45','result':'color'},mf);
  el('feComposite',{in:'color',in2:'blur',operator:'in','result':'cb'},mf);
  const mfmg=el('feMerge',{},mf);el('feMergeNode',{in:'cb'},mfmg);el('feMergeNode',{in:'SourceGraphic'},mfmg);
  el('rect',{width:700,height:700,fill:'url(#bgG)'},svg);

  // ── CONSTELLATION SEGMENTS (variable size!) ──
  for(const con of CONS){
    const color=CON_COLORS[con.name]||'#8888aa';
    const fill=CON_FILLS[con.name]||'#08081a';
    const a0=t2a(con.start,ascRef), a1=t2a(con.end%360,ascRef);
    // span > 180 needs large arc flag
    const span=con.span;
    const la=span>180?1:0;

    const p=(a,r)=>`${CX+Math.cos(a)*r},${CY+Math.sin(a)*r}`;

    // Outer zodiac ring R2→R1
    el('path',{
      d:`M${p(a0,R2)} L${p(a0,R1)} A${R1},${R1} 0 ${la},0 ${p(a1,R1)} L${p(a1,R2)} A${R2},${R2} 0 ${la},1 ${p(a0,R2)} Z`,
      fill
    },svg);
    // Colored inner edge arc
    el('path',{d:`M${p(a0,R2)} A${R2},${R2} 0 ${la},0 ${p(a1,R2)}`,
      fill:'none',stroke:color,'stroke-width':2,opacity:.6},svg);
    // House band R3→R2
    el('path',{
      d:`M${p(a0,R3)} L${p(a0,R2)} A${R2},${R2} 0 ${la},0 ${p(a1,R2)} L${p(a1,R3)} A${R3},${R3} 0 ${la},1 ${p(a0,R3)} Z`,
      fill:(CONS.indexOf(con)%2)?'rgba(6,5,18,1)':'rgba(10,8,26,1)'
    },svg);
    // Divider line at start
    el('line',{x1:CX+Math.cos(a0)*R1,y1:CY+Math.sin(a0)*R1,
      x2:CX+Math.cos(a0)*R2,y2:CY+Math.sin(a0)*R2,
      stroke:color,'stroke-width':1.2,opacity:.85},svg);

    // Symbol at midpoint of outer ring
    const midTrop=(con.start+(con.end%360))/2;
    // Handle Pisces wrap
    let mt=midTrop;
    if(con.name==='Pisces') mt=(con.start+29+360)/2;  // mid between 351.5 and 389(=29)
    const amid=t2a(mt%360,ascRef);
    const Rzs=(R1+R2)/2;
    const symText=el('text',{'text-anchor':'middle','dominant-baseline':'central',
      x:CX+Math.cos(amid)*Rzs,y:CY+Math.sin(amid)*Rzs,
      fill:color,'font-size':con.name==='Scorpius'?14:con.name==='Ophiuchus'?17:19,
      'font-family':'serif','font-weight':'bold'},svg);
    symText.textContent=con.sym+'\ufe0e';

    // No inner names
  }

  // ── MOON PATH (time-unknown) ──
  if(data._timeUnknown && data._moonPath){
    const mp=data._moonPath;
    const R_outer=R1-1, R_inner=R1-8;
    const span=((mp.end-mp.start)+360)%360;
    const la=span>180?1:0;
    const a0=t2a(mp.start,ascRef), a1e=t2a(mp.end,ascRef);
    const x0o=CX+Math.cos(a0)*R_outer, y0o=CY+Math.sin(a0)*R_outer;
    const x1o=CX+Math.cos(a1e)*R_outer,y1o=CY+Math.sin(a1e)*R_outer;
    const x1i=CX+Math.cos(a1e)*R_inner,y1i=CY+Math.sin(a1e)*R_inner;
    const x0i=CX+Math.cos(a0)*R_inner, y0i=CY+Math.sin(a0)*R_inner;
    el('path',{
      d:`M${x0o},${y0o} A${R_outer},${R_outer} 0 ${la},0 ${x1o},${y1o} L${x1i},${y1i} A${R_inner},${R_inner} 0 ${la},1 ${x0i},${y0i} Z`,
      fill:'rgba(100,160,255,0.35)',stroke:'none'},svg);
  }

  // ── INNERMOST FILL ──
  el('circle',{cx:CX,cy:CY,r:R4,fill:'rgba(4,3,14,1)'},svg);

  // ── DEGREE TICKS — all identical ──
  for(let deg=0;deg<360;deg++){
    const trop=(ARIES_START+deg)%360;
    const a=t2a(trop,ascRef);
    el('line',{x1:CX+Math.cos(a)*R1,y1:CY+Math.sin(a)*R1,
      x2:CX+Math.cos(a)*(R1-7),y2:CY+Math.sin(a)*(R1-7),
      stroke:'rgba(90,60,155,0.6)','stroke-width':0.6},svg);
  }

  // ── CIRCLES ──
  el('circle',{cx:CX,cy:CY,r:R1,fill:'none',stroke:'rgba(140,90,230,.85)','stroke-width':1.8},svg);
  el('circle',{cx:CX,cy:CY,r:R2,fill:'none',stroke:'rgba(100,65,200,.8)','stroke-width':1.5},svg);
  el('circle',{cx:CX,cy:CY,r:R3,fill:'none',stroke:'rgba(70,45,160,.75)','stroke-width':1.2},svg);
  el('circle',{cx:CX,cy:CY,r:R4,fill:'none',stroke:'rgba(50,32,120,.7)','stroke-width':1},svg);

  // ── PLACIDUS HOUSE LINES + NUMBERS + ASC/MC ──
  if(!data._timeUnknown){
    const angCol='#e8c06e';
    const Rhn=(R2+R3)/2;
    const ROMAN12=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
    for(let i=0;i<12;i++){
      const ha=t2a(data.houses[i],ascRef);
      const isAngle=[0,3,6,9].includes(i);
      el('line',{x1:CX+Math.cos(ha)*R2,y1:CY+Math.sin(ha)*R2,
        x2:CX+Math.cos(ha)*R3,y2:CY+Math.sin(ha)*R3,
        stroke:isAngle?angCol:'rgba(100,65,200,.55)',
        'stroke-width':isAngle?2:.7},svg);
      const next=data.houses[(i+1)%12];
      let mid=data.houses[i]+((next-data.houses[i]+360)%360)/2;
      if(mid>=360) mid-=360;
      const ma=t2a(mid,ascRef);
      txt(svg,ROMAN12[i],CX+Math.cos(ma)*Rhn,CY+Math.sin(ma)*Rhn,
        {fill:'rgba(180,150,255,0.8)','font-size':11,'font-family':'Cinzel,serif','font-weight':'bold'});
    }
    // ASC line
    const ascA=t2a(data.asc,ascRef);
    el('line',{x1:CX+Math.cos(ascA)*R1,y1:CY+Math.sin(ascA)*R1,
      x2:CX+Math.cos(ascA)*(R1+28),y2:CY+Math.sin(ascA)*(R1+28),
      stroke:angCol,'stroke-width':2.5},svg);
    txt(svg,'AC',CX+Math.cos(ascA)*(R1+42),CY+Math.sin(ascA)*(R1+42),
      {fill:angCol,'font-size':12,'font-weight':'bold','font-family':'Cinzel,serif'});
    // MC circle
    const mcA=t2a(data.mc,ascRef);
    const mcDist=R1+52,mcR=19;
    const mcCX=CX+Math.cos(mcA)*mcDist,mcCY=CY+Math.sin(mcA)*mcDist;
    el('line',{x1:CX+Math.cos(mcA)*R1,y1:CY+Math.sin(mcA)*R1,
      x2:CX+Math.cos(mcA)*(mcDist-mcR-2),y2:CY+Math.sin(mcA)*(mcDist-mcR-2),
      stroke:angCol,'stroke-width':2.5},svg);
    el('circle',{cx:mcCX,cy:mcCY,r:mcR,fill:'rgba(10,8,20,.95)',stroke:angCol,'stroke-width':2},svg);
    txt(svg,'MC',mcCX,mcCY,{fill:angCol,'font-size':11,'font-weight':'bold','font-family':'Cinzel,serif'});
  }

  // ── ASPECT LINES — inside center circle ──
  if(data.aspects){
    for(const asp of data.aspects){
      if(!data.planets[asp.p1]||!data.planets[asp.p2]) continue;
      const a1=t2a(data.planets[asp.p1].tropical,ascRef);
      const a2=t2a(data.planets[asp.p2].tropical,ascRef);
      const p1=pxy(a1,R4-4),p2=pxy(a2,R4-4);
      const isDash=asp.angle===90||asp.angle===180;
      el('line',{x1:p1.x,y1:p1.y,x2:p2.x,y2:p2.y,
        stroke:asp.color,'stroke-width':isDash?0.7:0.9,
        opacity:isDash?.4:.6,'stroke-dasharray':isDash?'3 3':''},svg);
    }
  }

  // ── PLANETS outside wheel ──
  const present=PORDER.filter(n=>data.planets[n]);
  const trueA={};
  for(const n of present) trueA[n]=t2a(data.planets[n].tropical,ascRef);
  const sorted=[...present].sort((a,b)=>trueA[a]-trueA[b]);
  const dispA={};
  for(const n of present) dispA[n]=trueA[n];
  const Rg=R1+30, MINGAP=24/Rg;

  for(let it=0;it<600;it++){
    let moved=false;
    for(let i=0;i<sorted.length;i++){
      for(let j=i+1;j<sorted.length;j++){
        const a=sorted[i],b=sorted[j];
        let d=dispA[b]-dispA[a];
        while(d>Math.PI) d-=2*Math.PI; while(d<-Math.PI) d+=2*Math.PI;
        if(Math.abs(d)<MINGAP&&Math.abs(d)>0.0001){
          const push=(MINGAP-Math.abs(d))/2,dir=d>0?1:-1;
          dispA[a]-=push*dir;dispA[b]+=push*dir;moved=true;
        }
      }
    }
    if(!moved) break;
  }

  for(const name of present){
    const info=PI[name]||{sym:'?',color:'#fff'};
    const p=data.planets[name];
    const tA=trueA[name],color=info.color;
    let diff=dispA[name]-tA;
    while(diff>Math.PI) diff-=2*Math.PI; while(diff<-Math.PI) diff+=2*Math.PI;
    const wasMoved=Math.abs(diff)>0.015;
    const gxy=pxy(wasMoved?dispA[name]:tA,Rg);
    el('line',{x1:CX+Math.cos(tA)*(R1+1),y1:CY+Math.sin(tA)*(R1+1),
      x2:CX+Math.cos(tA)*(R1+9),y2:CY+Math.sin(tA)*(R1+9),stroke:color,'stroke-width':1.5},svg);
    el('circle',{cx:CX+Math.cos(tA)*(R1+1),cy:CY+Math.sin(tA)*(R1+1),r:1.8,fill:color},svg);
    if(wasMoved) el('line',{x1:CX+Math.cos(tA)*(R1+10),y1:CY+Math.sin(tA)*(R1+10),
      x2:gxy.x,y2:gxy.y,stroke:color,'stroke-width':.5,opacity:.45,'stroke-dasharray':'2 2'},svg);
    if(name==='Sun'){
      const sg=el('g',{},svg);
      el('circle',{cx:gxy.x,cy:gxy.y,r:12,fill:'rgba(249,198,70,.12)'},sg);
      el('circle',{cx:gxy.x,cy:gxy.y,r:9,fill:'none',stroke:'#f9c646','stroke-width':'2',filter:'url(#sunF)'},sg);
      el('circle',{cx:gxy.x,cy:gxy.y,r:9,fill:'none',stroke:'#ffe8a0','stroke-width':'.8'},sg);
      el('circle',{cx:gxy.x,cy:gxy.y,r:2.5,fill:'#f9c646',filter:'url(#sunF)'},sg);
      el('circle',{cx:gxy.x,cy:gxy.y,r:1.2,fill:'#fff7d0'},sg);
    } else if(name==='Moon'){
      const mg=el('g',{filter:'url(#moonF)'},svg);
      txt(mg,'\u263d',gxy.x,gxy.y,{fill:'#b8d8ff','font-size':22,'font-family':'serif'});
    } else {
      txt(svg,info.sym,gxy.x,gxy.y,{fill:color,'font-size':20,'font-family':'serif'});
    }
    if(p.retrograde) txt(svg,'\u211e',gxy.x+11,gxy.y-9,{fill:'#f87171','font-size':8,'font-family':'serif'});
  }
}

// ── PLANET TABLE ──
function drawPlanetTable(data){
  const tbody=document.getElementById('planet-tbody');
  tbody.innerHTML='';
  for(const name of PORDER){
    if(!data.planets[name]) continue;
    const info=PI[name]||{sym:'?',color:'#aaa'};
    const p=data.planets[name];
    const color=CON_COLORS[p.constellation]||'#8888aa';
    let symCell=name==='Sun'?sunSVG(20)
      :name==='Moon'?'<span class="moon-sym">\u263d</span>'
      :name==='Selena'?`<svg width="18" height="18" viewBox="0 0 18 18" style="vertical-align:middle"><path d="M11,2 A7,7 0 1,0 11,16 A5,5 0 1,1 11,2 Z" fill="${info.color}" opacity="0.9"/></svg>`
      :`<span class="p-sym" style="color:${info.color}">${info.sym}</span>`;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${symCell}</td>
      <td style="color:${info.color};font-size:11px;white-space:nowrap">${name}</td>
      <td class="deg-val">${p.dms}</td>
      <td><span style="font-size:16px;font-family:serif;color:${color}">${p.sym}\ufe0e</span> <span style="font-size:10px;color:${color}">${p.constellation_ka||p.constellation}</span></td>
      <td><span class="house-badge">${p.house||'?'}</span></td>
      <td>${p.retrograde?'<span class="retro">\u211e</span>':''}</td>`;
    tbody.appendChild(tr);
  }
}

// ── HOUSE TABLE ──
function drawHouseTable(data){
  const tbody=document.getElementById('house-tbody');
  tbody.innerHTML='';
  const ANG={0:'AC',3:'IC',6:'DC',9:'MC'};
  for(let i=0;i<12;i++){
    const deg=data.houses[i];
    // Find which constellation this tropical degree falls in
    let conName='?',conSym='?',conColor='#aaa',conKa='?';
    for(const con of CONS){
      const s=con.start%360, e=con.end%360;
      const d=deg%360;
      if(s<e?s<=d&&d<e:d>=s||d<e){
        conName=con.name;conSym=con.sym;conColor=CON_COLORS[con.name]||'#aaa';conKa=con.ka||con.name;break;
      }
    }
    const ang=ANG[i];
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td style="color:${ang?'#e8c06e':'rgba(180,150,255,.7)'};font-family:'Cinzel',serif;font-size:11px;font-weight:${ang?600:400}">${ROMAN[i]}${ang?` <span style="font-size:9px">${ang}</span>`:''}</td>
      <td><span style="font-size:14px;font-family:serif;color:${conColor}">${conSym}\ufe0e</span> <span style="font-size:10px;color:${conColor}">${conKa}</span></td>
      <td class="deg-val">${Math.floor(deg%30)}°${String(Math.floor((deg%30-Math.floor(deg%30))*60)).padStart(2,'0')}'</td>`;
    tbody.appendChild(tr);
  }
}

// ── ASPECT TABLE ──
function drawAspectTable(data){
  const tbody=document.getElementById('aspect-tbody');
  tbody.innerHTML='';
  if(!data.aspects||!data.aspects.length){
    tbody.innerHTML='<tr><td colspan="5" style="color:rgba(100,80,150,.5);text-align:center;padding:16px">ასპექტები არ მოიძებნა</td></tr>';
    return;
  }
  for(const asp of data.aspects){
    const i1=PI[asp.p1]||{sym:'?',color:'#aaa'};
    const i2=PI[asp.p2]||{sym:'?',color:'#aaa'};
    const s1=asp.p1==='Sun'?sunSVG(16):`<span style="color:${i1.color};font-size:15px;font-family:serif">${i1.sym}</span>`;
    const s2=asp.p2==='Sun'?sunSVG(16):`<span style="color:${i2.color};font-size:15px;font-family:serif">${i2.sym}</span>`;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${s1} <span style="font-size:10px;color:${i1.color}">${asp.p1}</span></td>
      <td><span style="font-size:16px;font-family:serif;color:${asp.color}">${asp.sym}</span></td>
      <td>${s2} <span style="font-size:10px;color:${i2.color}">${asp.p2}</span></td>
      <td style="color:${asp.color};font-size:10px;white-space:nowrap">${asp.type}</td>
      <td style="color:rgba(140,100,200,.7);font-size:10px">${asp.orb}°</td>`;
    tbody.appendChild(tr);
  }
}

// ── CONSTELLATION TABLE ──
function drawConTable(data){
  const tbody=document.getElementById('con-tbody');
  tbody.innerHTML='';
  for(const con of CONS){
    const color=CON_COLORS[con.name]||'#8888aa';
    const pct=(con.span/360*100).toFixed(1);
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td><span style="font-size:18px;font-family:serif;color:${color}">${con.sym}\ufe0e</span> <span style="font-size:11px;color:${color}">${con.ka||con.name}</span></td>
      <td class="deg-val">${con.start}°</td>
      <td class="deg-val">${con.end%360}°</td>
      <td class="deg-val">${con.span}°</td>
      <td><span style="font-size:10px;color:var(--gold)">${pct}%</span>
          <span class="pct-bar"><span class="pct-fill" style="width:${pct}%"></span></span></td>`;
    tbody.appendChild(tr);
  }
}
</script>
</body>
</html>
