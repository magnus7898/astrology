<!DOCTYPE html>
<html lang="ka">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ნატალური რუქა</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400&family=Cinzel:wght@300;400;600&family=IM+Fell+English:ital@0;1&family=Noto+Sans+Georgian:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{
  --void:#04030a;--deep:#07071a;--surface:rgba(15,13,42,0.85);
  --gold:#c9a84c;--gold-l:#f0d080;--gold-d:#8a6a20;
  --purple:#a78bfa;--purple-d:#2d1f6e;
  --txt:#e0d8ff;--dim:rgba(155,168,184,0.6);
  --brd:rgba(45,31,110,0.8);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  background:var(--void);color:var(--txt);
  font-family:'Noto Sans Georgian',sans-serif;
  min-height:100vh;display:flex;flex-direction:column;align-items:center;
  padding:0 0 80px;overflow-x:hidden;position:relative;
}

/* ── STARFIELD ── */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(1px 1px at 8% 12%,rgba(255,255,255,.55) 0,transparent 100%),
    radial-gradient(1px 1px at 23% 35%,rgba(255,255,255,.35) 0,transparent 100%),
    radial-gradient(1px 1px at 41% 8%,rgba(255,255,255,.45) 0,transparent 100%),
    radial-gradient(1px 1px at 60% 25%,rgba(255,255,255,.3) 0,transparent 100%),
    radial-gradient(1px 1px at 77% 13%,rgba(255,255,255,.5) 0,transparent 100%),
    radial-gradient(1px 1px at 88% 44%,rgba(255,255,255,.35) 0,transparent 100%),
    radial-gradient(1px 1px at 15% 68%,rgba(255,255,255,.3) 0,transparent 100%),
    radial-gradient(1px 1px at 50% 75%,rgba(255,255,255,.4) 0,transparent 100%),
    radial-gradient(1px 1px at 82% 80%,rgba(255,255,255,.35) 0,transparent 100%),
    radial-gradient(1px 1px at 33% 90%,rgba(255,255,255,.25) 0,transparent 100%),
    radial-gradient(1px 1px at 67% 58%,rgba(255,255,255,.3) 0,transparent 100%),
    radial-gradient(1.5px 1.5px at 34% 51%,rgba(167,139,250,.25) 0,transparent 100%),
    radial-gradient(1.5px 1.5px at 66% 44%,rgba(201,168,76,.18) 0,transparent 100%);
}
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(ellipse 600px 400px at 20% 20%,rgba(100,40,200,.08) 0,transparent 70%),
    radial-gradient(ellipse 500px 500px at 80% 70%,rgba(40,80,200,.06) 0,transparent 70%),
    radial-gradient(ellipse 400px 300px at 50% 90%,rgba(120,50,180,.05) 0,transparent 70%);
}

/* ── HEADER SECTION ── */
.hero{
  position:relative;z-index:1;text-align:center;
  padding:56px 24px 40px;width:100%;
}
.hero-sigil{width:56px;height:56px;margin:0 auto 20px;display:block;opacity:.7}
.hero-eyebrow{font-size:9px;letter-spacing:7px;text-transform:uppercase;color:var(--gold);opacity:.5;margin-bottom:12px;font-weight:300;font-family:'Cinzel',serif}
.hero-title{
  font-family:'Cinzel Decorative',serif;
  font-size:clamp(22px,4vw,42px);font-weight:400;letter-spacing:3px;line-height:1.2;
  background:linear-gradient(160deg,#f5e8ba 0%,var(--gold) 35%,#9a7028 60%,#e8d5a0 80%,#c09040 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 28px rgba(201,168,76,.25));
}
.hero-sub{font-family:'IM Fell English',serif;font-style:italic;font-size:13px;color:var(--dim);margin-top:10px}
.hero-divider{display:flex;align-items:center;gap:14px;margin:24px auto 0;max-width:300px}
.hero-line{flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(201,168,76,.35),transparent)}
.hero-gem{width:5px;height:5px;background:var(--gold);transform:rotate(45deg);opacity:.5;flex-shrink:0}

/* ── FORM CARD ── */
.form-card{
  position:relative;z-index:1;
  background:rgba(8,6,20,.75);border:1px solid rgba(45,31,110,.6);
  border-radius:16px;padding:24px;width:100%;max-width:620px;
  margin:32px auto;backdrop-filter:blur(12px);
  box-shadow:0 8px 40px rgba(0,0,0,.5),inset 0 1px 0 rgba(167,139,250,.08);
}
.form-card::before{
  content:'';position:absolute;top:0;left:20%;right:20%;height:1px;
  background:linear-gradient(90deg,transparent,rgba(167,139,250,.4),transparent);
}
.form-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.form-grid-2{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.field{display:flex;flex-direction:column;gap:5px}
.field.wide{grid-column:span 3}
label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--gold);opacity:.7;font-family:'Cinzel',serif}
input{
  background:rgba(10,8,30,.7);border:1px solid rgba(61,42,138,.6);
  border-radius:8px;color:var(--txt);padding:9px 12px;font-size:13px;
  font-family:'Noto Sans Georgian',sans-serif;
  width:100%;transition:border-color .2s,box-shadow .2s;
}
input:focus{outline:none;border-color:var(--purple);box-shadow:0 0 0 3px rgba(124,58,237,.15)}
input::placeholder{color:rgba(155,168,184,.35)}
.coords-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.coords input{background:rgba(6,5,18,.7);color:rgba(155,168,184,.6)}
#city-hint{font-size:11px;color:var(--purple);margin-top:3px;min-height:15px;padding-left:2px}
#tz-display{
  font-size:11px;color:var(--gold);margin-bottom:16px;
  background:rgba(6,5,18,.5);border-radius:6px;padding:6px 10px;
  border-left:2px solid rgba(201,168,76,.3);
}
.gen-btn{
  width:100%;background:linear-gradient(135deg,#6d28d9,#4c1d95);
  color:#fff;border:1px solid rgba(124,58,237,.4);border-radius:10px;
  padding:13px;font-size:13px;cursor:pointer;letter-spacing:2px;
  font-family:'Cinzel',serif;transition:all .3s;
  box-shadow:0 4px 20px rgba(109,40,217,.3);
}
.gen-btn:hover{background:linear-gradient(135deg,#7c3aed,#5b21b6);box-shadow:0 6px 28px rgba(124,58,237,.4);transform:translateY(-1px)}

/* ── CHART AREA ── */
#chart-area{position:relative;z-index:1;width:100%;max-width:800px;padding:0 16px}
svg#wheel{width:100%;height:auto;display:block;border-radius:50%;overflow:visible}

/* ── SECTION TITLE ── */
.sec-title{
  font-family:'Cinzel',serif;font-size:11px;letter-spacing:4px;
  color:var(--gold);text-transform:uppercase;text-align:center;
  margin:32px 0 16px;display:flex;align-items:center;gap:14px;
}
.sec-title::before,.sec-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(201,168,76,.3),transparent)}

/* ── TABLES ── */
.tables-wrap{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px}
@media(max-width:600px){.tables-wrap{grid-template-columns:1fr}}
.data-card{
  background:rgba(8,6,20,.75);border:1px solid rgba(45,31,110,.5);
  border-radius:12px;overflow:hidden;backdrop-filter:blur(8px);
}
.data-card-title{
  background:rgba(167,139,250,.07);padding:10px 16px;
  font-family:'Cinzel',serif;font-size:10px;letter-spacing:3px;
  color:var(--purple);text-transform:uppercase;
  border-bottom:1px solid rgba(45,31,110,.5);
}
table{width:100%;border-collapse:collapse;font-size:12px}
th{color:rgba(155,168,184,.5);padding:7px 12px;text-align:left;font-weight:400;font-size:9px;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid rgba(45,31,110,.4)}
td{padding:6px 12px;border-bottom:1px solid rgba(15,13,40,.8);vertical-align:middle;font-size:12px}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(19,16,58,.6)}
.retro{color:#f87171;font-size:9px;margin-left:2px}
.house-badge{display:inline-block;background:rgba(26,21,69,.8);border:1px solid rgba(61,42,138,.6);border-radius:4px;padding:1px 6px;font-size:10px;color:var(--purple);font-family:'Cinzel',serif}
.deg-val{font-family:'Cinzel',serif;font-size:11px;color:#c8d8f0;white-space:nowrap}
.moon-sym{color:#b8d8ff;text-shadow:0 0 8px rgba(100,160,255,0.9),0 0 16px rgba(80,130,255,0.5);font-size:20px;font-family:serif}
.p-sym{font-family:serif;font-size:18px;line-height:1;display:inline-block}
.asp-sym{font-size:16px;font-family:serif}

/* ── ELEMENT COLORS ── */
/* Fire */
.sign-fire{color:#e05252}
/* Earth */
.sign-earth{color:#8aab6e}
/* Air */
.sign-air{color:#89b4d4}
/* Water */
.sign-water{color:#5b8ec4}

/* ── TIME UNKNOWN ── */
.time-disabled input{opacity:.3;pointer-events:none}
#wheel-wrap{width:100%;max-width:800px;margin:0 auto}

/* ── MOBILE ── */
@media(max-width:480px){
  .form-grid{grid-template-columns:1fr 1fr 1fr}
  td{padding:5px 8px;font-size:11px}
  th{font-size:9px;padding:5px 8px}
  .p-sym{font-size:15px}
}
@media(max-width:380px){
  .form-grid{grid-template-columns:1fr 1fr}
  .form-grid .field:last-child{grid-column:span 2}
}
</style>
</head>
<body>

<!-- HERO -->
<div class="hero">
  <svg class="hero-sigil" viewBox="0 0 56 56" fill="none">
    <circle cx="28" cy="28" r="26.5" stroke="rgba(201,168,76,.25)" stroke-width=".5"/>
    <circle cx="28" cy="28" r="17" stroke="rgba(201,168,76,.18)" stroke-width=".5"/>
    <polygon points="28,3 51,43 5,43" stroke="rgba(201,168,76,.38)" stroke-width=".5" fill="none"/>
    <polygon points="28,53 5,13 51,13" stroke="rgba(201,168,76,.38)" stroke-width=".5" fill="none"/>
    <circle cx="28" cy="28" r="2.5" fill="rgba(201,168,76,.7)"/>
    <circle cx="28" cy="3" r="1.4" fill="rgba(201,168,76,.4)"/>
    <circle cx="51" cy="43" r="1.4" fill="rgba(201,168,76,.4)"/>
    <circle cx="5" cy="43" r="1.4" fill="rgba(201,168,76,.4)"/>
    <circle cx="28" cy="53" r="1.4" fill="rgba(201,168,76,.4)"/>
    <circle cx="5" cy="13" r="1.4" fill="rgba(201,168,76,.4)"/>
    <circle cx="51" cy="13" r="1.4" fill="rgba(201,168,76,.4)"/>
  </svg>
  <div class="hero-eyebrow">სულის მეცნიერება</div>
  <h1 class="hero-title">ნატალური რუქა</h1>
  <p class="hero-sub">Natal Chart · Placidus Houses · Tropical Zodiac</p>
  <div class="hero-divider"><div class="hero-line"></div><div class="hero-gem"></div><div class="hero-line"></div></div>
</div>

<!-- FORM -->
<div class="form-card">
  <div class="field wide" style="margin-bottom:12px">
    <label>სახელი</label>
    <input id="name" placeholder="შეიყვანეთ სახელი">
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

<!-- CHART -->
<div id="chart-area" style="display:none">
  <div class="sec-title">ნატალური ბორბალი</div>
  <div id="lunar-badge" style="display:none;text-align:center;margin-bottom:12px;padding:10px 20px;background:rgba(8,6,22,.8);border:1px solid rgba(100,70,200,.4);border-radius:12px;backdrop-filter:blur(8px)">
    <span class="lb-em" style="font-size:20px;margin-right:8px">🌙</span>
    <span class="lb-day" id="lunar-day" style="font-family:'Cinzel',serif;font-size:13px;color:#c8d8f0;font-weight:600"></span>
    <span style="color:rgba(150,120,220,.5);margin:0 6px">·</span>
    <span class="lb-pct" id="lunar-pct" style="font-size:11px;color:rgba(180,150,255,.65)"></span>
  </div>
  <div id="wheel-wrap">
    <svg id="wheel" viewBox="0 0 700 700" xmlns="http://www.w3.org/2000/svg"></svg>
  </div>

  <div class="sec-title">პლანეტები და სახლები</div>
  <div class="tables-wrap">
    <div class="data-card">
      <div class="data-card-title">🪐 პლანეტები</div>
      <table>
        <thead><tr><th></th><th>სახელი</th><th>გრადუსი</th><th>ნიშანი</th><th>სახ.</th><th>℞</th></tr></thead>
        <tbody id="planet-tbody"></tbody>
      </table>
    </div>
    <div class="data-card">
      <div class="data-card-title">🏠 სახლები (Placidus)</div>
      <table>
        <thead><tr><th>სახლი</th><th>ნიშანი</th><th>გრადუსი</th></tr></thead>
        <tbody id="house-tbody"></tbody>
      </table>
    </div>
  </div>

  <div class="sec-title">ასპექტები</div>
  <div class="data-card" style="margin-bottom:8px">
    <div class="data-card-title">⚡ მთავარი ასპექტები</div>
    <table>
      <thead><tr><th>პლანეტა 1</th><th>ასპ.</th><th>პლანეტა 2</th><th>ტიპი</th><th>ორბი</th></tr></thead>
      <tbody id="aspect-tbody"></tbody>
    </table>
  </div>
</div>

<script>
const BACKEND = 'https://astrology-production-b165.up.railway.app';
const CX=350,CY=350,R1=270,R2=202,R3=135,R4=105;

// ── SIGN DATA with element colors ──
const SIGN_KA=['ვერძი','კურო','ტყუპები','კირჩხიბი','ლომი','ქალწული',
               'სასწორი','მორიელი','მშვილდოსანი','თხის რქა','მერწყული','თევზები'];
const ZSYM=['♈︎','♉︎','♊︎','♋︎','♌︎','♍︎','♎︎','♏︎','♐︎','♑︎','♒︎','♓︎'];
// Fire=red, Earth=graygreen, Air=lightblue, Water=blue
const ZCOL=[
  '#e05252', // Aries - fire red
  '#8aab6e', // Taurus - earth green-gray
  '#89b4d4', // Gemini - air light blue-gray
  '#5b8ec4', // Cancer - water blue
  '#d4602e', // Leo - fire orange-red
  '#7a9e6a', // Virgo - earth gray-green
  '#7fb8d8', // Libra - air light blue
  '#4a7ab0', // Scorpio - water deep blue
  '#c84a32', // Sagittarius - fire red
  '#6b9062', // Capricorn - earth muted green-gray
  '#90c0dc', // Aquarius - air sky blue
  '#6688c0', // Pisces - water blue-purple
];
// Element for each sign index: F=fire E=earth A=air W=water
const ZELEMENT=['F','E','A','W','F','E','A','W','F','E','A','W'];

// ── PLANET DATA ──
const PI={
  'მზე':              {sym:'sun',  color:'#f9c646'},
  'მთვარე':           {sym:'☽',   color:'#c8d8f0'},
  'მერკური':          {sym:'☿',   color:'#a0c8d0'},
  'ვენერა':           {sym:'♀',   color:'#e87878'},
  'მარსი':            {sym:'♂',   color:'#e84040'},
  'იუპიტერი':         {sym:'♃',   color:'#e89040'},
  'სატურნი':          {sym:'♄',   color:'#c8c840'},
  'ურანი':            {sym:'♅',   color:'#50c8d8'},
  'ნეპტუნი':          {sym:'♆',   color:'#6070d8'},
  'პლუტონი':          {sym:'⯓',   color:'#c050a0'},
  'ქირონი':           {sym:'⚷',   color:'#d08040'},
  'ლილიტი':           {sym:'⚸',   color:'#904060'},
  'ჩრდ. კვანძი':      {sym:'☊',   color:'#60c060'},
  'სამხ. კვანძი':     {sym:'☋',   color:'#c06060'},
  'ვერტექსი':         {sym:'Vx',  color:'#8090d0'},
  'თეთრი მთვარე':     {sym:'⯝︎',   color:'#d0e8f8'},
  'ბედის ვარსკვლავი': {sym:'⊕',   color:'#f0c060'},
  'იუნო':             {sym:'⚵',   color:'#c890d0'},
};

const PORDER=['მზე','მთვარე','მერკური','ვენერა','მარსი',
  'იუპიტერი','სატურნი','ურანი','ნეპტუნი','პლუტონი',
  'ქირონი','ლილიტი','ჩრდ. კვანძი','სამხ. კვანძი',
  'ვერტექსი','თეთრი მთვარე','ბედის ვარსკვლავი','იუნო'];

// ── DEGREE FORMAT: D°MM' real 60-min ──
function fmtDeg(deg){
  const inSign=((deg%30)+30)%30;
  const d=Math.floor(inSign);
  const totalMin=(inSign-d)*60;
  const m=Math.floor(totalMin);
  return `${d}°${String(m).padStart(2,'0')}'`;
}

// ── SUN SVG (circle with dot + glow) ──
function sunSVG(sz=22){
  const h=sz/2;
  return `<svg width="${sz}" height="${sz}" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;display:inline-block;overflow:visible">
    <defs>
      <filter id="sg${sz}"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <circle cx="11" cy="11" r="8" fill="#f9c646"/>
    <circle cx="11" cy="11" r="8" 
    <circle cx="11" cy="11" r="1.8" fill="#f9c646" filter="url(#sg${sz})"/>
    <circle cx="11" cy="11" r="1.0" fill="#fff7d0"/>
  </svg>`;
}

// Sun SVG for wheel (inline, no defs — defs come from wheel defs block)
function sunWheelSVG(x,y,sz=11){
  return {x,y,sz};
}

function signClass(si){
  const el=ZELEMENT[si];
  return el==='F'?'sign-fire':el==='E'?'sign-earth':el==='A'?'sign-air':'sign-water';
}

// ── TIME UNKNOWN TOGGLE ──
function toggleTimeUnknown(){
  const unk=document.getElementById('time-unknown').checked;
  document.getElementById('time-fields').classList.toggle('time-disabled',unk);
}

// ── LUNAR DAY CALCULATION ──
// Uses the Moon's actual ecliptic longitude from the backend chart response
// Lunar day starts at each New Moon (Moon longitude == Sun longitude)
// We use the moon_age from the elongation (angular distance Moon-Sun)
// This is the most accurate approach using real swisseph data

function calcLunarDayFromPositions(moonDeg, sunDeg){
  // Elongation = angular distance from Sun to Moon (0=new, 180=full)
  let elong = ((moonDeg - sunDeg) + 360) % 360;
  // Each lunar day = 360/29.53058... ≈ 12.19° of elongation
  const degPerLunarDay = 360 / 29.53058868;
  const age = elong / degPerLunarDay; // 0..29.53
  const lunarDay = Math.floor(age) + 1; // 1..30
  // % through current lunar day (0=just started, 99=almost over)
  const pct = Math.round((age % 1) * 100);
  return {lunarDay, pct, age, elong};
}

function displayLunarBadge(data){
  try{
    const planets = data.planets;
    if(!planets || !planets['მთვარე'] || !planets['მზე']) return;
    const moonDeg = planets['მთვარე'].degree;
    const sunDeg  = planets['მზე'].degree;
    const {lunarDay, pct} = calcLunarDayFromPositions(moonDeg, sunDeg);
    // pct% elapsed means (100-pct)% remaining till next lunar day
    const remaining = 100 - pct;
    document.getElementById('lunar-day').textContent = `მთვარის მე-${lunarDay} დღე`;
    document.getElementById('lunar-pct').textContent  = `${remaining}% შემდეგ მთვარის დღემდე`;
    document.getElementById('lunar-badge').style.display = 'block';
  }catch(e){console.log('lunar calc error',e);}
}

// ── MOON PATH for "time unknown" mode ──
// Calculate moon degree at 00:00 and 23:59 of birth date
// Returns {start_deg, end_deg} ecliptic longitude
async function getMoonPathDegrees(year,month,day,lat,lon,tz_name){
  // Fetch moon at midnight and end of day
  const results=[];
  for(const [h,mn,s] of [[0,0,0],[23,59,59]]){
    try{
      const r=await fetch(`${BACKEND}/chart`,{method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({year,month,day,hour:h,minute:mn,second:s,lat,lon,tz_name})});
      const d=await r.json();
      if(d.planets && d.planets['მთვარე']){
        results.push(d.planets['მთვარე'].degree);
      }
    }catch(e){}
  }
  return results.length===2?results:null;
}

// ── GEOCODE ──
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

// ── GENERATE ──
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
  // Use noon for time-unknown
  const hour=timeUnknown?12:+document.getElementById('hour').value;
  const minute=timeUnknown?0:+document.getElementById('minute').value;
  const second=timeUnknown?0:+document.getElementById('second').value;
  try{
    const r=await fetch(`${BACKEND}/chart`,{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({year,month,day,hour,minute,second,lat:+lat,lon:+lon,tz_name})});
    const data=await r.json();
    data._timeUnknown=timeUnknown;
    document.getElementById('chart-area').style.display='block';
    drawWheel(data);
    drawPlanetTable(data);
    if(!timeUnknown){drawHouseTable(data);}
    else{document.getElementById('house-tbody').innerHTML='<tr><td colspan="3" style="color:rgba(120,100,180,.5);text-align:center;padding:12px;font-size:11px">დრო უცნობია — სახლები არ გამოითვლება</td></tr>';}
    drawAspectTable(data);
    // Lunar badge
    displayLunarBadge(data);
    // Moon path for time-unknown
    if(timeUnknown){
      const moonPath=await getMoonPathDegrees(year,month,day,+lat,+lon,tz_name);
      if(moonPath) drawMoonPath(moonPath[0],moonPath[1]);
    }
    document.getElementById('chart-area').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){alert('შეცდომა: '+e.message);}
  finally{btn.textContent='✦ რუქის გენერაცია ✦';btn.disabled=false;}
}

// ── MOON PATH (time-unknown mode) ──
// Draws a thin transparent white arc just inside R1 showing moon range for the day
function drawMoonPath(moonStart, moonEnd){
  const svg = document.getElementById('wheel');
  const asc = 0; // Aries rising for time-unknown
  const span = ((moonEnd - moonStart) + 360) % 360;
  // Arc just inside R1 — thin band only 6px wide, no stroke, transparent white
  const R_outer = R1 - 2;   // just inside the outer circle
  const R_inner = R1 - 10;  // thin band
  const steps = 40;
  const pts_outer = [], pts_inner = [];
  for(let i=0;i<=steps;i++){
    const deg = moonStart + (span * i / steps);
    const a = e2s(deg, asc);
    pts_outer.push(`${CX+Math.cos(a)*R_outer},${CY+Math.sin(a)*R_outer}`);
    pts_inner.unshift(`${CX+Math.cos(a)*R_inner},${CY+Math.sin(a)*R_inner}`);
  }
  // large-arc flag
  const la = span > 180 ? 1 : 0;
  const a0 = e2s(moonStart, asc);
  const a1e = e2s(moonEnd, asc);
  const pathD = `M${CX+Math.cos(a0)*R_outer},${CY+Math.sin(a0)*R_outer}`
    + ` A${R_outer},${R_outer} 0 ${la},0 ${CX+Math.cos(a1e)*R_outer},${CY+Math.sin(a1e)*R_outer}`
    + ` L${CX+Math.cos(a1e)*R_inner},${CY+Math.sin(a1e)*R_inner}`
    + ` A${R_inner},${R_inner} 0 ${la},1 ${CX+Math.cos(a0)*R_inner},${CY+Math.sin(a0)*R_inner}`
    + ` Z`;
  const moonPathEl = document.createElementNS('http://www.w3.org/2000/svg','path');
  moonPathEl.setAttribute('d', pathD);
  moonPathEl.setAttribute('fill','rgba(220,220,255,0.12)');
  moonPathEl.setAttribute('stroke','none');
  svg.appendChild(moonPathEl);
  // Small moon emoji at midpoint just outside the arc
  const midDeg = moonStart + span/2;
  const midA = e2s(midDeg, asc);
  const t = document.createElementNS('http://www.w3.org/2000/svg','text');
  t.setAttribute('x', CX+Math.cos(midA)*(R1+18));
  t.setAttribute('y', CY+Math.sin(midA)*(R1+18));
  t.setAttribute('text-anchor','middle');
  t.setAttribute('dominant-baseline','central');
  t.setAttribute('font-size','14');
  t.setAttribute('fill','rgba(200,220,255,0.7)');
  t.textContent='☽';
  svg.appendChild(t);
}

// ── SVG HELPERS ──
const NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){
  const e=document.createElementNS(NS,tag);
  for(const[k,v] of Object.entries(attrs)) e.setAttribute(k,v);
  if(parent) parent.appendChild(e);
  return e;
}
function txt(parent,s,x,y,attrs={}){
  const t=el('text',{'text-anchor':'middle','dominant-baseline':'central',x,y,...attrs},parent);
  t.textContent=s;return t;
}
function toRad(d){return d*Math.PI/180;}
function e2s(ecl,asc){return toRad(-(ecl-asc))+Math.PI;}
function pxy(a,r){return{x:CX+Math.cos(a)*r,y:CY+Math.sin(a)*r};}

// ── ZODIAC SYMBOL DRAWING (SVG paths, element-colored) ──
function drawZodiacSymbol(parent, idx, color){
  const s=el('g',{'text-anchor':'middle','dominant-baseline':'central'},parent);
  // Draw each sign as simple SVG path centered at 0,0
  const paths=[
    // 0 Aries ♈ - ram horns
    ()=>{el('path',{d:'M-7,2 Q-4,-8 0,-2 Q4,-8 7,2',fill:'none',stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('line',{x1:0,y1:-2,x2:0,y2:6,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);},
    // 1 Taurus ♉ - bull head
    ()=>{el('circle',{cx:0,cy:2,r:6,fill:'none',stroke:color,'stroke-width':'1.8'},s);
         el('path',{d:'M-6,-4 Q-6,-10 0,-10 Q6,-10 6,-4',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);},
    // 2 Gemini ♊ - twins
    ()=>{el('line',{x1:-5,y1:-8,x2:-5,y2:8,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('line',{x1:5,y1:-8,x2:5,y2:8,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('line',{x1:-6,y1:-8,x2:6,y2:-8,stroke:color,'stroke-width':'1.5','stroke-linecap':'round'},s);
         el('line',{x1:-6,y1:8,x2:6,y2:8,stroke:color,'stroke-width':'1.5','stroke-linecap':'round'},s);},
    // 3 Cancer ♋ - crab claws
    ()=>{el('path',{d:'M-7,-2 Q-7,-9 0,-6 Q7,-9 7,-2',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M-7,2 Q-7,9 0,6 Q7,9 7,2',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);},
    // 4 Leo ♌ - lion mane
    ()=>{el('circle',{cx:0,cy:4,r:5,fill:'none',stroke:color,'stroke-width':'1.8'},s);
         el('path',{d:'M0,-1 Q-8,-1 -8,-7 Q-8,-12 -3,-12 Q0,-12 0,-8',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('circle',{cx:5,cy:4,r:1.5,fill:color},s);},
    // 5 Virgo ♍ - maiden
    ()=>{el('line',{x1:-5,y1:-8,x2:-5,y2:4,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('path',{d:'M-5,-3 Q0,-8 5,-3 L5,4',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M3,4 Q5,9 3,9 Q-5,9 -5,4',fill:'none',stroke:color,'stroke-width':'1.6','stroke-linecap':'round'},s);},
    // 6 Libra ♎ - scales
    ()=>{el('line',{x1:-7,y1:2,x2:7,y2:2,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('line',{x1:0,y1:2,x2:0,y2:8,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('line',{x1:-6,y1:8,x2:6,y2:8,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('path',{d:'M-7,-6 Q0,-12 7,-6',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);},
    // 7 Scorpio ♏ - scorpion tail
    ()=>{el('line',{x1:-5,y1:-8,x2:-5,y2:4,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('path',{d:'M-5,-3 Q0,-8 5,-3 L5,4',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M5,4 Q8,4 8,7 Q8,10 5,10 L3,10',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M3,10 L5,8',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);},
    // 8 Sagittarius ♐ - arrow
    ()=>{el('line',{x1:-7,y1:7,x2:7,y2:-7,stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('path',{d:'M7,-7 L2,-7 M7,-7 L7,-2',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('line',{x1:-5,y1:-1,x2:1,y2:5,stroke:color,'stroke-width':'1.2','stroke-linecap':'round',opacity:'.5'},s);},
    // 9 Capricorn ♑ - sea-goat
    ()=>{el('path',{d:'M-6,-8 Q-6,2 0,2 Q6,2 6,-2',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M6,-2 Q8,4 4,8 Q-2,12 -6,8',fill:'none',stroke:color,'stroke-width':'1.6','stroke-linecap':'round'},s);},
    // 10 Aquarius ♒ - waves
    ()=>{el('path',{d:'M-7,-3 Q-3,-8 0,-3 Q3,2 7,-3',fill:'none',stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);
         el('path',{d:'M-7,4 Q-3,-1 0,4 Q3,9 7,4',fill:'none',stroke:color,'stroke-width':'2','stroke-linecap':'round'},s);},
    // 11 Pisces ♓ - fish
    ()=>{el('path',{d:'M0,-8 Q-8,-4 -8,0 Q-8,4 0,8',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('path',{d:'M0,-8 Q8,-4 8,0 Q8,4 0,8',fill:'none',stroke:color,'stroke-width':'1.8','stroke-linecap':'round'},s);
         el('line',{x1:-6,y1:0,x2:6,y2:0,stroke:color,'stroke-width':'1.5','stroke-linecap':'round'},s);},
  ];
  paths[idx]();
}

// ── SELENA SVG (white moon crescent) ──
function selenaSVG(color='#d0e8f8', sz=18){
  const h=sz/2;
  return `<svg width="${sz}" height="${sz}" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;display:inline-block">
    <path d="M9,2 Q15,5 15,9 Q15,13 9,16 Q13,13 13,9 Q13,5 9,2 Z" fill="${color}" opacity="0.9"/>
    <circle cx="7" cy="9" r="4.5" fill="none" stroke="${color}" stroke-width="1.2" opacity="0.5"/>
  </svg>`;
}

// ── DRAW WHEEL ──
function drawWheel(data){
  const svg=document.getElementById('wheel');
  svg.innerHTML='';
  const asc=data._timeUnknown?0:data.asc;

  // ── DEFS ──
  const defs=el('defs',{},svg);

  // Arrow marker
  const mk=el('marker',{id:'arr',viewBox:'0 0 10 10',refX:'8',refY:'5',
    markerWidth:'5',markerHeight:'5',orient:'auto-start-reverse'},defs);
  el('path',{d:'M2 1L8 5L2 9',fill:'none',stroke:'#c084fc',
    'stroke-width':'1.5','stroke-linecap':'round','stroke-linejoin':'round'},mk);

  // Sun gradient
  const sg=el('radialGradient',{id:'sunG',cx:'40%',cy:'38%',r:'60%'},defs);
  el('stop',{offset:'0%','stop-color':'#fff7d0'},sg);
  el('stop',{offset:'40%','stop-color':'#f9c646'},sg);
  el('stop',{offset:'100%','stop-color':'#c87010'},sg);

  // Sun glow filter
  const sf=el('filter',{id:'sunF',x:'-60%',y:'-60%',width:'220%',height:'220%'},defs);
  const fb=el('feGaussianBlur',{stdDeviation:'3',result:'blur'},sf);
  const fm=el('feMerge',{},sf);
  el('feMergeNode',{in:'blur'},fm);
  el('feMergeNode',{in:'SourceGraphic'},fm);

  // Glow filter for bright planets
  const gf=el('filter',{id:'glow',x:'-40%',y:'-40%',width:'180%',height:'180%'},defs);
  const gb=el('feGaussianBlur',{stdDeviation:'2',result:'blur'},gf);
  const gm=el('feMerge',{},gf);
  el('feMergeNode',{in:'blur'},gm);
  el('feMergeNode',{in:'SourceGraphic'},gm);

  // Moon blue glow filter
  const mf=el('filter',{id:'moonF',x:'-60%',y:'-60%',width:'220%',height:'220%'},defs);
  const mfb=el('feGaussianBlur',{stdDeviation:'3',result:'blur'},mf);
  const mfc=el('feFlood',{'flood-color':'#4090ff','flood-opacity':'0.5','result':'color'},mf);
  const mfm=el('feComposite',{in:'color',in2:'blur',operator:'in','result':'colorBlur'},mf);
  const mfmg=el('feMerge',{},mf);
  el('feMergeNode',{in:'colorBlur'},mfmg);
  el('feMergeNode',{in:'SourceGraphic'},mfmg);

  // Background
  const bgG=el('radialGradient',{id:'bgG',cx:'50%',cy:'50%',r:'50%'},defs);
  el('stop',{offset:'0%','stop-color':'#120e2a'},bgG);
  el('stop',{offset:'60%','stop-color':'#0a0820'},bgG);
  el('stop',{offset:'100%','stop-color':'#04030e'},bgG);

  el('rect',{width:700,height:700,fill:'url(#bgG)'},svg);

  // ── ELEMENT FILL COLORS for zodiac band ──
  const EFILL=[
    '#1a0808','#081008','#08101a','#08101a', // Aries,Tau,Gem,Can
    '#1a0808','#081008','#08101a','#081018', // Leo,Vir,Lib,Sco
    '#1a0808','#081008','#08101a','#081018'  // Sag,Cap,Aqu,Pis
  ];

  // ── ZODIAC BAND — solid element-tinted fills ──
  for(let i=0;i<12;i++){
    const p=(d,r)=>{const a=e2s(d,asc);return`${CX+Math.cos(a)*r},${CY+Math.sin(a)*r}`;};
    el('path',{
      d:`M${p(i*30,R1)} A${R1},${R1} 0 0,0 ${p((i+1)*30,R1)} L${p((i+1)*30,R2)} A${R2},${R2} 0 0,1 ${p(i*30,R2)} Z`,
      fill:EFILL[i]
    },svg);
    // Element-colored border on inner edge
    el('path',{
      d:`M${p(i*30,R2)} A${R2},${R2} 0 0,0 ${p((i+1)*30,R2)}`,
      fill:'none',stroke:ZCOL[i],'stroke-width':2,opacity:.6
    },svg);
  }

  // ── ZODIAC DIVIDER LINES ──
  for(let i=0;i<12;i++){
    const a=e2s(i*30,asc);
    el('line',{x1:CX+Math.cos(a)*R1,y1:CY+Math.sin(a)*R1,
      x2:CX+Math.cos(a)*R2,y2:CY+Math.sin(a)*R2,
      stroke:ZCOL[i],'stroke-width':1.2,opacity:.85},svg);
  }

  // ── HOUSE BAND — alternating dark fills ──
  for(let i=0;i<12;i++){
    const h1=data.houses[i],h2=data.houses[(i+1)%12];
    const span=((h2-h1)+360)%360,la=span>180?1:0;
    const p=(d,r)=>{const a=e2s(d,asc);return`${CX+Math.cos(a)*r},${CY+Math.sin(a)*r}`;};
    el('path',{
      d:`M${p(h1,R2)} A${R2},${R2} 0 ${la},0 ${p(h2,R2)} L${p(h2,R3)} A${R3},${R3} 0 ${la},1 ${p(h1,R3)} Z`,
      fill:i%2?'rgba(6,5,18,1)':'rgba(10,8,26,1)'
    },svg);
  }

  // ── INNERMOST CIRCLE fill ──
  el('circle',{cx:CX,cy:CY,r:R4,fill:'rgba(4,3,14,1)'},svg);

  // ── DEGREE TICKS — all 360, clearly visible ──
  for(let deg=0;deg<360;deg++){
    const a=e2s(deg,asc),co=Math.cos(a),si2=Math.sin(a);
    const is30=deg%30===0,is10=deg%10===0,is5=deg%5===0;
    const len=is30?20:is10?13:is5?8:5;
    const stroke=is30?'rgba(255,220,255,1)':is10?'rgba(180,130,255,0.95)':is5?'rgba(120,80,200,0.8)':'rgba(80,55,150,0.65)';
    const sw=is30?2:is10?1.4:is5?0.9:0.5;
    el('line',{x1:CX+co*R1,y1:CY+si2*R1,
      x2:CX+co*(R1-len),y2:CY+si2*(R1-len),
      stroke,'stroke-width':sw},svg);
  }

  // ── DEGREE NUMBERS every 10° ──
  for(let deg=0;deg<360;deg+=10){
    if(deg%30===0) continue;
    const a=e2s(deg,asc),nr=R1-33;
    const nx=CX+Math.cos(a)*nr,ny=CY+Math.sin(a)*nr;
    txt(svg,String(deg%30),nx,ny,{fill:'rgba(160,120,240,0.9)','font-size':7.5,
      'font-family':'serif',transform:`rotate(${(a*180/Math.PI)+90},${nx},${ny})`});
  }

  // ── CIRCLES — bright solid strokes ──
  el('circle',{cx:CX,cy:CY,r:R1,fill:'none',stroke:'rgba(140,90,230,0.85)','stroke-width':1.8},svg);
  el('circle',{cx:CX,cy:CY,r:R2,fill:'none',stroke:'rgba(100,65,200,0.8)','stroke-width':1.5},svg);
  el('circle',{cx:CX,cy:CY,r:R3,fill:'none',stroke:'rgba(70,45,160,0.75)','stroke-width':1.2},svg);
  el('circle',{cx:CX,cy:CY,r:R4,fill:'none',stroke:'rgba(50,32,120,0.7)','stroke-width':1},svg);

  // ── ZODIAC SYMBOLS — text with FE0E selector, element colored, upright ──
  const Rzs=(R1+R2)/2;
  for(let i=0;i<12;i++){
    const a=e2s(i*30+15,asc);
    const zx=CX+Math.cos(a)*Rzs, zy=CY+Math.sin(a)*Rzs;
    // text stays upright (no rotation), colored by element
    const zt=el('text',{'text-anchor':'middle','dominant-baseline':'central',
      x:zx,y:zy,fill:ZCOL[i],'font-size':20,'font-family':'serif',
      'font-weight':'bold'},svg);
    zt.textContent=ZSYM[i];
  }

  // ── HOUSE LINES + NUMBERS (hidden for time-unknown) ──
  if(!data._timeUnknown){
    const Rhn=(R2+R3)/2;
    for(let i=0;i<12;i++){
      const a=e2s(data.houses[i],asc);
      const isAngle=[0,3,6,9].includes(i);
      el('line',{x1:CX+Math.cos(a)*R2,y1:CY+Math.sin(a)*R2,
        x2:CX+Math.cos(a)*R3,y2:CY+Math.sin(a)*R3,
        stroke:isAngle?'#e8c06e':'rgba(100,65,200,.6)',
        'stroke-width':isAngle?2:.8},svg);
      const next=data.houses[(i+1)%12];
      let mid=data.houses[i]+((next-data.houses[i]+360)%360)/2;
      if(mid>=360) mid-=360;
      const ma=e2s(mid,asc);
      txt(svg,String(i+1),CX+Math.cos(ma)*Rhn,CY+Math.sin(ma)*Rhn,
        {fill:'rgba(180,150,255,0.85)','font-size':11,'font-family':'Cinzel,serif','font-weight':'bold'});
    }
  }

  // ── ASPECT LINES ──
  if(data.aspects){
    for(const asp of data.aspects){
      if(!data.planets[asp.p1]||!data.planets[asp.p2]) continue;
      const a1=e2s(data.planets[asp.p1].degree,asc);
      const a2=e2s(data.planets[asp.p2].degree,asc);
      const p1=pxy(a1,R4-2),p2=pxy(a2,R4-2);
      const isDash=asp.angle===90||asp.angle===180;
      el('line',{x1:p1.x,y1:p1.y,x2:p2.x,y2:p2.y,
        stroke:asp.color,'stroke-width':0.9,opacity:.6,
        'stroke-dasharray':isDash?'':'4 4'},svg);
    }
  }

  // ── PLANETS ──
  const present=Object.keys(data.planets);
  const trueA={};
  for(const n of present) trueA[n]=e2s(data.planets[n].degree,asc);
  const sorted=[...present].sort((a,b)=>trueA[a]-trueA[b]);
  const dispA={};
  for(const n of present) dispA[n]=trueA[n];
  const Rg=R1+30;
  const MINGAP=24/Rg;

  for(let it=0;it<600;it++){
    let moved=false;
    for(let i=0;i<sorted.length;i++){
      for(let j=i+1;j<sorted.length;j++){
        const a=sorted[i],b=sorted[j];
        let d=dispA[b]-dispA[a];
        while(d>Math.PI) d-=2*Math.PI;
        while(d<-Math.PI) d+=2*Math.PI;
        if(Math.abs(d)<MINGAP&&Math.abs(d)>0.0001){
          const push=(MINGAP-Math.abs(d))/2;
          const dir=d>0?1:-1;
          dispA[a]-=push*dir;dispA[b]+=push*dir;moved=true;
        }
      }
    }
    if(!moved) break;
  }

  const ascAngle=Math.PI,mcAngle=e2s(data.mc,asc);
  for(let pass=0;pass<100;pass++){
    let moved=false;
    for(const n of present){
      for(const blocked of [ascAngle,mcAngle]){
        let d=dispA[n]-blocked;
        while(d>Math.PI) d-=2*Math.PI;
        while(d<-Math.PI) d+=2*Math.PI;
        if(Math.abs(d)<MINGAP&&Math.abs(d)>0.0001){
          dispA[n]=blocked+MINGAP*(d>0?1:-1);moved=true;
        }
      }
    }
    if(moved){
      for(let i=0;i<sorted.length;i++){
        for(let j=i+1;j<sorted.length;j++){
          const a=sorted[i],b=sorted[j];
          let d=dispA[b]-dispA[a];
          while(d>Math.PI) d-=2*Math.PI;
          while(d<-Math.PI) d+=2*Math.PI;
          if(Math.abs(d)<MINGAP&&Math.abs(d)>0.0001){
            const push=(MINGAP-Math.abs(d))/2;
            const dir=d>0?1:-1;
            dispA[a]-=push*dir;dispA[b]+=push*dir;
          }
        }
      }
    }
  }

  for(const name of present){
    const info=PI[name]||{sym:'?',color:'#fff'};
    const tA=trueA[name],color=info.color;
    let diff=dispA[name]-tA;
    while(diff>Math.PI) diff-=2*Math.PI;
    while(diff<-Math.PI) diff+=2*Math.PI;
    const wasMoved=Math.abs(diff)>0.015;
    const gxy=pxy(wasMoved?dispA[name]:tA,Rg);

    // true position tick
    el('line',{x1:CX+Math.cos(tA)*(R1+1),y1:CY+Math.sin(tA)*(R1+1),
      x2:CX+Math.cos(tA)*(R1+9),y2:CY+Math.sin(tA)*(R1+9),
      stroke:color,'stroke-width':1.5},svg);
    el('circle',{cx:CX+Math.cos(tA)*(R1+1),cy:CY+Math.sin(tA)*(R1+1),r:1.8,fill:color},svg);

    if(wasMoved){
      el('line',{x1:CX+Math.cos(tA)*(R1+10),y1:CY+Math.sin(tA)*(R1+10),
        x2:gxy.x,y2:gxy.y,stroke:color,'stroke-width':.5,opacity:.45,'stroke-dasharray':'2 2'},svg);
    }

    if(name==='მზე'){
      // Sun: circle + center dot + glow (astrological symbol ☉)
      const sg2=el('g',{},svg);
      // outer glow
      el('circle',{cx:gxy.x,cy:gxy.y,r:12,fill:'rgba(249,198,70,0.12)'},sg2);
      // main circle
      el('circle',{cx:gxy.x,cy:gxy.y,r:9,fill:'none',stroke:'#f9c646','stroke-width':'2',filter:'url(#sunF)'},sg2);
      el('circle',{cx:gxy.x,cy:gxy.y,r:9,fill:'none',stroke:'#ffe8a0','stroke-width':'0.8'},sg2);
      // center dot
      el('circle',{cx:gxy.x,cy:gxy.y,r:2.5,fill:'#f9c646',filter:'url(#sunF)'},sg2);
      el('circle',{cx:gxy.x,cy:gxy.y,r:1.2,fill:'#fff7d0'},sg2);
    } else if(name==='მთვარე'){
      // Moon — glowing crescent ☽
      const mg=el('g',{filter:'url(#moonF)'},svg);
      txt(mg,'☽',gxy.x,gxy.y,{fill:'#b8d8ff','font-size':22,'font-family':'serif'});
    } else {
      const fsz=name==='პლუტონი'?18:20;
      txt(svg,info.sym,gxy.x,gxy.y,{fill:color,'font-size':fsz,'font-family':'serif'});
    }

    if(data.planets[name].retrograde){
      txt(svg,'℞',gxy.x+11,gxy.y-9,{fill:'#f87171','font-size':8,'font-family':'serif'});
    }
  }

    // ── ASC / MC — only shown when time is known ──
  if(!data._timeUnknown){
    const angCol='#e8c06e';
    const ascA=e2s(asc,asc);
    el('line',{x1:CX+Math.cos(ascA)*R1,y1:CY+Math.sin(ascA)*R1,
      x2:CX+Math.cos(ascA)*(R1+28),y2:CY+Math.sin(ascA)*(R1+28),
      stroke:angCol,'stroke-width':2.5},svg);
    txt(svg,'AC',CX+Math.cos(ascA)*(R1+42),CY+Math.sin(ascA)*(R1+42),
      {fill:angCol,'font-size':12,'font-weight':'bold','font-family':'Cinzel,serif'});
    const mcA=e2s(data.mc,asc);
    const mcDist=R1+52,mcR=19;
    const mcCX=CX+Math.cos(mcA)*mcDist,mcCY=CY+Math.sin(mcA)*mcDist;
    el('line',{x1:CX+Math.cos(mcA)*R1,y1:CY+Math.sin(mcA)*R1,
      x2:CX+Math.cos(mcA)*(mcDist-mcR-2),y2:CY+Math.sin(mcA)*(mcDist-mcR-2),
      stroke:angCol,'stroke-width':2.5},svg);
    el('circle',{cx:mcCX,cy:mcCY,r:mcR,fill:'rgba(10,8,20,.95)',stroke:angCol,'stroke-width':2},svg);
    txt(svg,'MC',mcCX,mcCY,{fill:angCol,'font-size':11,'font-weight':'bold','font-family':'Cinzel,serif'});
  }

}

// ── PLANET TABLE ──
function drawPlanetTable(data){
  const tbody=document.getElementById('planet-tbody');
  tbody.innerHTML='';
  const shown=new Set();
  const order=[...PORDER,...Object.keys(data.planets).filter(k=>!PORDER.includes(k))];
  for(const name of order){
    if(!data.planets[name]||shown.has(name)) continue;
    shown.add(name);
    const info=PI[name]||{sym:'★',color:'#aaa'};
    const d=data.planets[name];
    const si=SIGN_KA.indexOf(d.sign);
    const sCol=si>=0?ZCOL[si]:'#aaa';
    const sc=si>=0?signClass(si):'';
    const symCell=name==='მზე'
      ? sunSVG(20)
      : name==='მთვარე'
      ? '<span class="moon-sym">☽</span>'
      : `<span class="p-sym" style="color:${info.color};font-size:18px;font-family:serif">${info.sym}</span>`;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${symCell}</td>
      <td style="color:${info.color};font-size:11px;white-space:nowrap">${name}</td>
      <td class="deg-val">${fmtDeg(d.degree)}</td>
      <td><span class="${sc}" style="font-size:14px;font-family:serif">${si>=0?ZSYM[si]:''}</span> <span style="font-size:10px;color:${sCol}">${d.sign}</span></td>
      <td><span class="house-badge">${d.house||'?'}</span></td>
      <td>${d.retrograde?'<span class="retro">℞</span>':''}</td>`;
    tbody.appendChild(tr);
  }
}

// ── HOUSE TABLE ──
function drawHouseTable(data){
  const tbody=document.getElementById('house-tbody');
  tbody.innerHTML='';
  const ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
  const ANG={0:'AC',3:'IC',6:'DC',9:'MC'};
  for(let i=0;i<12;i++){
    const deg=data.houses[i];
    const si=Math.floor(deg/30)%12;
    const ang=ANG[i];
    const sc=signClass(si);
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td style="color:${ang?'#c084fc':'rgba(155,168,184,.7)'};font-family:'Cinzel',serif;font-size:11px;font-weight:${ang?'600':'400'}">
        ${ROMAN[i]}${ang?` <span style="font-size:9px;opacity:.7">${ang}</span>`:''}
      </td>
      <td><span class="${sc}" style="font-size:14px;font-family:serif">${ZSYM[si]||''}</span> <span style="font-size:10px;color:${ZCOL[si]}">${SIGN_KA[si]||''}</span></td>
      <td class="deg-val">${fmtDeg(deg)}</td>`;
    tbody.appendChild(tr);
  }
}

// ── ASPECT TABLE ──
function drawAspectTable(data){
  const tbody=document.getElementById('aspect-tbody');
  tbody.innerHTML='';
  if(!data.aspects||!data.aspects.length){
    tbody.innerHTML='<tr><td colspan="5" style="color:rgba(100,80,150,.5);text-align:center;padding:16px;font-size:12px">ასპექტები არ მოიძებნა</td></tr>';
    return;
  }
  for(const asp of data.aspects){
    const i1=PI[asp.p1]||{sym:'?',color:'#aaa'};
    const i2=PI[asp.p2]||{sym:'?',color:'#aaa'};
    const s1=asp.p1==='მზე'?sunSVG(16):`<span style="color:${i1.color};font-size:15px;font-family:serif">${i1.sym}</span>`;
    const s2=asp.p2==='მზე'?sunSVG(16):`<span style="color:${i2.color};font-size:15px;font-family:serif">${i2.sym}</span>`;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td>${s1} <span style="font-size:10px;color:${i1.color}">${asp.p1}</span></td>
      <td><span class="asp-sym" style="color:${asp.color}">${asp.sym}</span></td>
      <td>${s2} <span style="font-size:10px;color:${i2.color}">${asp.p2}</span></td>
      <td style="color:${asp.color};font-size:10px;white-space:nowrap">${asp.type}</td>
      <td style="color:rgba(140,100,200,.7);font-size:10px">${asp.orb}°</td>`;
    tbody.appendChild(tr);
  }
}
</script>
</body>
</html>
