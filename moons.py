<!DOCTYPE html>
<html lang="ka">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>პლანეტარული ასტროლოგია</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400&family=Cinzel:wght@300;400;600&family=IM+Fell+English:ital@0;1&family=Noto+Sans+Georgian:wght@300;400;600&display=swap" rel="stylesheet">
<script src="constellations.js"></script>
<style>
:root{--void:#05040c;--acc:#7c9ad0;--acc-l:#a8c4ea;--dust:#c8d4e8;
  --txt:#e6ecf8;--dim:rgba(190,205,230,0.55)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--void);color:var(--txt);font-family:'Noto Sans Georgian',sans-serif;
  min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:0 0 80px;position:relative}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:
  radial-gradient(1px 1px at 12% 18%,rgba(255,255,255,.5) 0,transparent 100%),
  radial-gradient(1px 1px at 31% 42%,rgba(255,255,255,.3) 0,transparent 100%),
  radial-gradient(1px 1px at 58% 11%,rgba(255,255,255,.4) 0,transparent 100%),
  radial-gradient(1px 1px at 79% 33%,rgba(255,255,255,.45) 0,transparent 100%),
  radial-gradient(1px 1px at 44% 77%,rgba(255,255,255,.3) 0,transparent 100%)}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 700px 420px at 25% 15%,rgba(124,154,208,.09) 0,transparent 70%)}
.hero{position:relative;z-index:1;text-align:center;padding:34px 24px 14px;width:100%}
.orb{width:56px;height:56px;margin:0 auto 12px;border-radius:50%;transition:background .4s;
  box-shadow:0 0 26px rgba(124,154,208,.35),inset -5px -5px 12px rgba(0,0,0,.55)}
.hero-eyebrow{font-size:9px;letter-spacing:7px;text-transform:uppercase;color:var(--acc-l);opacity:.6;margin-bottom:9px;font-family:'Cinzel',serif}
.hero-title{font-family:'Cinzel Decorative',serif;font-size:clamp(19px,4vw,34px);letter-spacing:3px;
  background:linear-gradient(160deg,#dce8ff 0%,var(--acc-l) 35%,#4a6a9a 62%,#c8dcf8 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-family:'IM Fell English',serif;font-style:italic;font-size:12px;color:var(--dim);margin-top:7px}
.panel{position:relative;z-index:1;width:100%;max-width:880px;padding:0 16px;margin-top:16px}
.card{background:rgba(10,12,26,.78);border:1px solid rgba(124,154,208,.22);border-radius:14px;padding:18px;margin-bottom:14px}
.card-title{font-family:'Cinzel',serif;font-size:10px;letter-spacing:3px;text-transform:uppercase;
  color:var(--acc-l);opacity:.85;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid rgba(124,154,208,.15)}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}
.field{display:flex;flex-direction:column;gap:4px;flex:1;min-width:96px}
label{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--acc-l);opacity:.7;font-family:'Cinzel',serif}
input,select{background:rgba(8,10,22,.8);border:1px solid rgba(124,154,208,.3);border-radius:8px;
  color:var(--txt);padding:9px 12px;font-size:13px;font-family:'Noto Sans Georgian',sans-serif;width:100%}
input:focus,select:focus{outline:none;border-color:var(--acc-l);box-shadow:0 0 0 3px rgba(124,154,208,.15)}
.btn{background:linear-gradient(135deg,#3a5a8a,#7c9ad0);color:#0a0c18;border:none;border-radius:9px;
  padding:11px 22px;font-size:12px;cursor:pointer;letter-spacing:2px;font-family:'Cinzel',serif;font-weight:600;width:100%;margin-top:10px}
.btn:hover{filter:brightness(1.15)}
.btn.ghost{background:none;border:1px solid rgba(124,154,208,.4);color:var(--acc-l)}
svg#wheel{width:100%;height:auto;display:block;overflow:visible}
.sec{font-family:'Cinzel',serif;font-size:10px;letter-spacing:4px;color:var(--acc-l);text-transform:uppercase;
  text-align:center;margin:22px 0 12px;display:flex;align-items:center;gap:12px}
.sec::before,.sec::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(124,154,208,.3),transparent)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:620px){.grid2{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:12px}
th{color:rgba(190,205,230,.5);padding:6px 10px;text-align:left;font-weight:400;font-size:9px;
  text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid rgba(124,154,208,.18)}
td{padding:5px 10px;border-bottom:1px solid rgba(16,18,34,.9);font-size:12px}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(30,40,70,.45)}
.deg{font-family:'Cinzel',serif;font-size:11px;color:#cfe0f5;white-space:nowrap}
.lat{font-size:9px;color:rgba(190,205,230,.42)}
.badge{display:inline-block;background:rgba(30,40,70,.8);border:1px solid rgba(124,154,208,.35);
  border-radius:4px;padding:1px 6px;font-size:10px;color:var(--dust);font-family:'Cinzel',serif}
.retro{color:#f87171;font-size:9px}
.note{font-size:10px;color:rgba(190,205,230,.45);line-height:1.7;margin-top:10px}
.hl{background:rgba(124,154,208,.10);border-left:3px solid var(--acc);border-radius:8px;padding:12px 14px;margin-top:12px;font-size:12px;line-height:1.9}
.odd{background:rgba(176,120,64,.12);border-left:3px solid #b07840;border-radius:8px;padding:10px 14px;margin-top:10px;font-size:12px;line-height:1.8}
.err{background:rgba(200,40,40,.15);border:1px solid rgba(220,60,60,.4);border-radius:8px;
  color:#f87171;font-size:12px;padding:10px 14px;margin-top:10px}
</style>
</head>
<body>

<div class="hero">
  <div class="orb" id="orb"></div>
  <div class="hero-eyebrow">სხვა სამყაროს ზოდიაქო</div>
  <h1 class="hero-title">პლანეტარული ასტროლოგია</h1>
  <p class="hero-sub" id="hsub">Planetocentric charts &middot; every planet has its own zodiac</p>
</div>

<div class="panel">
  <div class="card">
    <div class="card-title">🪐 დამკვირვებელი პლანეტა</div>
    <div class="row">
      <div class="field" style="min-width:150px"><label>პლანეტა</label>
        <select id="i-obs">
          <option value="mercury">☿ მერკური</option>
          <option value="venus">♀ ვენერა</option>
          <option value="mars" selected>♂ მარსი</option>
          <option value="jupiter">♃ იუპიტერი</option>
          <option value="saturn">♄ სატურნი</option>
          <option value="uranus">♅ ურანი</option>
          <option value="neptune">♆ ნეპტუნი</option>
          <option value="pluto">⯓ პლუტონი</option>
        </select></div>
      <div class="field" style="min-width:180px"><label>ზოდიაქო</label>
        <select id="i-mode">
          <option value="iau" selected>✦ IAU თანავარსკვლავედები</option>
          <option value="ptrop">☉ ტროპიკული (12) — ამ პლანეტის ბუნიობა</option>
          <option value="psid">★ სიდერიული (12) — სპიკა</option>
        </select></div>
      <div class="field"><label>სახელი</label><input id="i-name" placeholder="სახელი"></div>
    </div>
    <div class="row" style="margin-top:10px">
      <div class="field"><label>დღე</label><input type="number" id="i-day" value="1" min="1" max="31"></div>
      <div class="field"><label>თვე</label><input type="number" id="i-month" value="1" min="1" max="12"></div>
      <div class="field"><label>წელი</label><input type="number" id="i-year" value="1990"></div>
      <div class="field"><label>საათი</label><input type="number" id="i-hour" value="12" min="0" max="23"></div>
      <div class="field"><label>წუთი</label><input type="number" id="i-min" value="0" min="0" max="59"></div>
    </div>
    <div style="border-top:1px solid rgba(124,154,208,.15);margin:14px 0 10px;padding-top:12px">
      <div class="card-title" style="margin-bottom:10px">🌍 დედამიწის დაბადების ადგილი → პლანეტაზე</div>
      <div class="row">
        <div class="field" style="min-width:150px"><label>ქალაქი</label>
          <input id="i-city" placeholder="თბილისი, London..." autocomplete="off">
          <div id="i-cityhint" style="font-size:11px;color:var(--acc-l);min-height:14px;margin-top:2px"></div></div>
        <div class="field"><label>განედი</label><input type="number" id="i-elat" step="0.0001" value="41.7151"></div>
        <div class="field"><label>გრძედი</label><input type="number" id="i-elon" step="0.0001" value="44.8271"></div>
      </div>
      <div id="i-derived" style="font-size:11px;color:var(--dust);margin-top:8px;line-height:1.7"></div>
    </div>
    <button class="btn" id="btn-gen">✦ რუქის გენერაცია ✦</button>
    <button class="btn ghost" id="btn-now">🕐 ახლა</button>
    <div id="err"></div>
  </div>

  <div id="out" style="display:none">
    <div class="sec" id="lbl"></div>
    <svg id="wheel" viewBox="-45 -45 790 790" xmlns="http://www.w3.org/2000/svg"></svg>
    <div id="oddbox"></div>
    <div id="moonbox"></div>
    <div id="innerbox"></div>
    <div class="sec">სხეულები</div>
    <div class="grid2">
      <div class="card" style="padding:0;overflow:hidden">
        <div class="card-title" id="ptitle" style="padding:9px 14px;margin:0;border-bottom:1px solid rgba(124,154,208,.18)">🪐 პლანეტოცენტრული</div>
        <table><thead><tr><th></th><th>სხეული</th><th>გრადუსი ნიშანში</th><th>ნიშანი</th><th>სახ.</th><th>℞ / დაშ.</th></tr></thead>
        <tbody id="ptb"></tbody></table>
      </div>
      <div class="card" style="padding:0;overflow:hidden">
        <div class="card-title">🏠 სახლები</div>
        <table><thead><tr><th>სახლი</th><th>ნიშანი</th><th>გრადუსი</th></tr></thead>
        <tbody id="htb"></tbody></table>
      </div>
    </div>
    <div class="sec">ასპექტები</div>
    <div class="card" style="padding:0 0 8px;overflow:hidden">
      <div class="card-title" id="atitle" style="padding:9px 14px;margin:0;border-bottom:1px solid rgba(124,154,208,.18)">⚡ ასპექტები</div>
      <table><thead><tr><th>სხეული 1</th><th>ასპ.</th><th>სხეული 2</th><th>ტიპი</th><th>ორბი</th></tr></thead>
      <tbody id="atb"></tbody></table>
    </div>
    <div class="card">
      <div class="card-title">🌐 პლანეტის მონაცემები</div>
      <div id="info" style="font-size:12px;line-height:2"></div>
    </div>
  </div>
</div>

<script>
/* ═══ PLANETOCENTRIC ASTROLOGY ════════════════════════════════
   Positions : JPL Keplerian elements → heliocentric J2000 ecliptic,
               subtracted from the observer planet.
   Moons     : /api/moons (PyEphem satellite theories) — the observer
               planet's own major moons, seen from that planet.
   IAU mode  : real 2-D constellation lookup (constellations.js).
   Tropical  : 12 equal signs from the OBSERVER PLANET's own vernal
               equinox (its orbit ∩ its equator, IAU pole).
   Sidereal  : 12 equal signs anchored on Spica in the planet's plane.
   Poles/W verified against known axial tilts and rotation periods.
   ════════════════════════════════════════════════════════════ */
const $=function(id){return document.getElementById(id);};
const D2R=Math.PI/180,R2D=180/Math.PI,EPS=23.4392911*D2R;
const norm=function(x){return((x%360)+360)%360;};
const SPICA_LON=203.8375,SPICA_LAT=-2.0545;

const SIGN_KA=['ვერძი','კურო','ტყუპები','კირჩხიბი','ლომი','ქალწული','სასწორი','მორიელი','მშვილდოსანი','თხის რქა','მერწყული','თევზები'];
const ZSYM=['♈︎','♉︎','♊︎','♋︎','♌︎','♍︎','♎︎','♏︎','♐︎','♑︎','♒︎','♓︎'];
const ZCOL=['#e05252','#8aab6e','#89b4d4','#5b8ec4','#d4602e','#7a9e6a','#7fb8d8','#4a7ab0','#c84a32','#6b9062','#90c0dc','#6688c0'];

/* Keplerian elements: a,e,I,L,varpi,Omega + rates per century */
const KEP={
 'mercury':[0.38709927,0.20563593,7.00497902,252.25032350,77.45779628,48.33076593,
            0.00000037,0.00001906,-0.00594749,149472.67411175,0.16047689,-0.12534081],
 'venus':[0.72333566,0.00677672,3.39467605,181.97909950,131.60246718,76.67984255,
          0.00000390,-0.00004107,-0.00078890,58517.81538729,0.00268329,-0.27769418],
 'earth':[1.00000261,0.01671123,-0.00001531,100.46457166,102.93768193,0.0,
          0.00000562,-0.00004392,-0.01294668,35999.37244981,0.32327364,0.0],
 'mars':[1.52371034,0.09339410,1.84969142,-4.55343205,-23.94362959,49.55953891,
         0.00001847,0.00007882,-0.00813131,19140.30268499,0.44441088,-0.29257343],
 'jupiter':[5.20288700,0.04838624,1.30439695,34.39644051,14.72847983,100.47390909,
            -0.00011607,-0.00013253,-0.00183714,3034.74612775,0.21252668,0.20469106],
 'saturn':[9.53667594,0.05386179,2.48599187,49.95424423,92.59887831,113.66242448,
           -0.00125060,-0.00050991,0.00193609,1222.49362201,-0.41897216,-0.28867794],
 'uranus':[19.18916464,0.04725744,0.77263783,313.23810451,170.95427630,74.01692503,
           -0.00196176,-0.00004397,-0.00242939,428.48202785,0.40805281,0.04240589],
 'neptune':[30.06992276,0.00859048,1.77004347,-55.12002969,44.96476227,131.78422574,
            0.00026291,0.00005105,0.00035372,218.45945325,-0.32241464,-0.00508664],
 'pluto':[39.48211675,0.24882730,17.14001206,238.92903833,224.06891629,110.30393684,
          -0.00031596,0.00005170,0.00004818,145.20780515,-0.04062942,-0.01183482]
};
/* IAU WGCCRE rotation elements: a0,a0dot,d0,d0dot,W0,Wdot  (verified) */
const ROT={
 'mercury':[281.0103,-0.0328,61.4155,-0.0049,329.5988,6.1385108],
 'venus':[272.76,0,67.16,0,160.20,-1.4813688],
 'earth':[0.00,-0.641,90.00,-0.557,190.147,360.9856235],
 'mars':[317.68143,-0.1061,52.88650,-0.0609,176.630,350.89198226],
 'jupiter':[268.056595,-0.006499,64.495303,0.002413,284.95,870.5360000],
 'saturn':[40.589,-0.036,83.537,-0.004,38.90,810.7939024],
 'uranus':[257.311,0,-15.175,0,203.81,-501.1600928],
 'neptune':[299.36,0,43.46,0,253.18,536.3128492],
 'pluto':[132.993,0,-6.163,0,302.695,56.3625225]
};
const PLA={
 'mercury':{ka:'მერკური',sym:'☿',col:'#a0c8d0',day:58.646,yr:87.97,g1:'#c8d8e0',g2:'#5a6a72'},
 'venus':{ka:'ვენერა',sym:'♀',col:'#e8c878',day:-243.02,yr:224.70,g1:'#f8e8b0',g2:'#8a7030'},
 'earth':{ka:'დედამიწა',sym:'⊕',col:'#5b9ec4',day:0.997,yr:365.26,g1:'#a0d0f0',g2:'#204060'},
 'mars':{ka:'მარსი',sym:'♂',col:'#e07050',day:1.026,yr:686.98,g1:'#f0a070',g2:'#6a2410'},
 'jupiter':{ka:'იუპიტერი',sym:'♃',col:'#e0a060',day:0.4135,yr:4332.6,g1:'#f0d0a0',g2:'#8a5820'},
 'saturn':{ka:'სატურნი',sym:'♄',col:'#e0d090',day:0.4440,yr:10759,g1:'#f0e8c0',g2:'#8a7840'},
 'uranus':{ka:'ურანი',sym:'♅',col:'#80d0e0',day:-0.7183,yr:30685,g1:'#b0e8f0',g2:'#306870'},
 'neptune':{ka:'ნეპტუნი',sym:'♆',col:'#6090f0',col2:'#6090f0',day:0.6713,yr:60190,g1:'#90b0f8',g2:'#203070'},
 'pluto':{ka:'პლუტონი',sym:'⯓',col:'#c090b0',day:6.3872,yr:90560,g1:'#e0c0d0',g2:'#604050'}
};
const PI_={
 'მზე':{sym:'☉',color:'#f9c646'},'დედამიწა':{sym:'⊕',color:'#5b9ec4'},
 'მერკური':{sym:'☿',color:'#a0c8d0'},'ვენერა':{sym:'♀',color:'#e8c878'},
 'მარსი':{sym:'♂',color:'#e07050'},'იუპიტერი':{sym:'♃',color:'#e0a060'},
 'სატურნი':{sym:'♄',color:'#e0d090'},'ურანი':{sym:'♅',color:'#80d0e0'},
 'ნეპტუნი':{sym:'♆',color:'#6090f0'},'პლუტონი':{sym:'⯓',color:'#c090b0'},
 'AC':{sym:'AC',color:'#a8c4ea'},'MC':{sym:'MC',color:'#a8c4ea'}
};
const ORDER=['მზე','მერკური','ვენერა','დედამიწა','მარსი','იუპიტერი','სატურნი','ურანი','ნეპტუნი','პლუტონი','AC','MC'];
const EN2KA={mercury:'მერკური',venus:'ვენერა',earth:'დედამიწა',mars:'მარსი',jupiter:'იუპიტერი',
             saturn:'სატურნი',uranus:'ურანი',neptune:'ნეპტუნი',pluto:'პლუტონი'};

/* ── major moons of the observer planet (positions from /api/moons) ── */
const MOON_I={
 phobos:{sym:'Ph',color:'#d09070'},   deimos:{sym:'De',color:'#c08060'},
 io:{sym:'Io',color:'#f0d060'},       europa:{sym:'Eu',color:'#e8e0d0'},
 ganymede:{sym:'Ga',color:'#c0b090'}, callisto:{sym:'Ca',color:'#907868'},
 mimas:{sym:'Mi',color:'#d8d8e0'},    enceladus:{sym:'En',color:'#f0f4f8'},
 tethys:{sym:'Te',color:'#d0d8e0'},   dione:{sym:'Di',color:'#c8ccd4'},
 rhea:{sym:'Rh',color:'#d4d0c8'},     titan:{sym:'Ti',color:'#e8a850'},
 hyperion:{sym:'Hy',color:'#b09878'}, iapetus:{sym:'Ia',color:'#a09088'},
 miranda:{sym:'Mr',color:'#b8c8d0'},  ariel:{sym:'Ar',color:'#c8d4dc'},
 umbriel:{sym:'Um',color:'#8898a0'},  titania:{sym:'Tt',color:'#c0ccd8'},
 oberon:{sym:'Ob',color:'#a8b4c0'},
 moon:{sym:'☾',color:'#dfe6f2'}
};
const MOON_CACHE={};
function getMoons(o,y,m,d,h,mi){
  const k=o+'|'+y+'-'+m+'-'+d+'-'+h+'-'+mi;
  if(MOON_CACHE[k])return Promise.resolve(MOON_CACHE[k]);
  return fetch(BACKEND+'/api/moons',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({planet:o,year:y,month:m,day:d,hour:h,minute:mi})})
    .then(function(r){return r.json();})
    .then(function(j){MOON_CACHE[k]=j;return j;})
    .catch(function(e){return{moons:[],unavailable:[],
      error:'სერვერთან კავშირი ვერ დამყარდა ('+e.message+')'};});
}

/* constellation sectors along each planet's own ecliptic
   (measured from that planet's J2000 ascending node) */
const SECT={"mercury":[[-15.98,5.3,"Ari"],[5.3,5.7,"Tau"],[5.7,6.57,"Ari"],[6.57,42.07,"Tau"],[42.07,50.67,"Aur"],[50.67,68.54,"Gem"],[68.54,87.52,"Cnc"],[87.52,122.79,"Leo"],[122.79,168.93,"Vir"],[168.93,191.1,"Lib"],[191.1,199.87,"Sco"],[199.87,203.08,"Oph"],[203.08,206.7,"Sco"],[206.7,218.3,"Oph"],[218.3,250.13,"Sgr"],[250.13,276.61,"Cap"],[276.61,308.09,"Aqr"],[308.09,308.28,"Cet"],[308.28,316.57,"Psc"],[316.57,327.16,"Cet"],[327.16,344.02,"Psc"]],"venus":[[-23.67,13.49,"Tau"],[13.49,40.93,"Gem"],[40.93,60.47,"Cnc"],[60.47,95.71,"Leo"],[95.71,140.32,"Vir"],[140.32,165.77,"Lib"],[165.77,170.85,"Sco"],[170.85,189.6,"Oph"],[189.6,222.57,"Sgr"],[222.57,249.7,"Cap"],[249.7,280.88,"Aqr"],[280.88,289.1,"Psc"],[289.1,297.13,"Cet"],[297.13,316.33,"Psc"],[316.33,316.81,"Cet"],[316.81,336.33,"Ari"]],"earth":[[-8.35,28.69,"Psc"],[28.69,53.41,"Ari"],[53.41,90.13,"Tau"],[90.13,117.98,"Gem"],[117.98,138.03,"Cnc"],[138.03,173.85,"Leo"],[173.85,217.81,"Vir"],[217.81,241.05,"Lib"],[241.05,247.64,"Sco"],[247.64,266.24,"Oph"],[266.24,299.66,"Sgr"],[299.66,327.49,"Cap"],[327.49,351.65,"Aqr"]],"mars":[[-20.49,3.89,"Ari"],[3.89,40.6,"Tau"],[40.6,68.1,"Gem"],[68.1,87.9,"Cnc"],[87.9,123.62,"Leo"],[123.62,168.11,"Vir"],[168.11,190.07,"Lib"],[190.07,198.2,"Sco"],[198.2,216.75,"Oph"],[216.75,249.76,"Sgr"],[249.76,277.27,"Cap"],[277.27,305.58,"Aqr"],[305.58,317.07,"Psc"],[317.07,319.97,"Cet"],[319.97,339.51,"Psc"]],"jupiter":[[-10.34,17.44,"Gem"],[17.44,37.32,"Cnc"],[37.32,72.85,"Leo"],[72.85,116.93,"Vir"],[116.93,141.99,"Lib"],[141.99,147.04,"Sco"],[147.04,165.75,"Oph"],[165.75,199.11,"Sgr"],[199.11,226.69,"Cap"],[226.69,254.11,"Aqr"],[254.11,266.16,"Psc"],[266.16,269.34,"Cet"],[269.34,290.11,"Psc"],[290.11,312.67,"Ari"],[312.67,349.66,"Tau"]],"saturn":[[-23.56,4.29,"Gem"],[4.29,24.07,"Cnc"],[24.07,59.29,"Leo"],[59.29,103.29,"Vir"],[103.29,128.55,"Lib"],[128.55,133.64,"Sco"],[133.64,152.51,"Oph"],[152.51,185.95,"Sgr"],[185.95,213.37,"Cap"],[213.37,243.17,"Aqr"],[243.17,252.52,"Psc"],[252.52,258.82,"Cet"],[258.82,279.35,"Psc"],[279.35,280.21,"Cet"],[280.21,299.14,"Ari"],[299.14,333.89,"Tau"],[333.89,336.44,"Ori"]],"uranus":[[-20.68,16.12,"Tau"],[16.12,43.87,"Gem"],[43.87,63.8,"Cnc"],[63.8,99.51,"Leo"],[99.51,143.63,"Vir"],[143.63,167.78,"Lib"],[167.78,173.61,"Sco"],[173.61,192.24,"Oph"],[192.24,225.54,"Sgr"],[225.54,253.21,"Cap"],[253.21,279.42,"Aqr"],[279.42,292.87,"Psc"],[292.87,294.4,"Cet"],[294.4,314.8,"Psc"],[314.8,339.32,"Ari"]],"neptune":[[-13.73,6.19,"Cnc"],[6.19,41.58,"Leo"],[41.58,85.41,"Vir"],[85.41,110.5,"Lib"],[110.5,115.57,"Sco"],[115.57,134.39,"Oph"],[134.39,167.95,"Sgr"],[167.95,195.55,"Cap"],[195.55,222.68,"Aqr"],[222.68,234.8,"Psc"],[234.8,238.52,"Cet"],[238.52,260.19,"Psc"],[260.19,281.16,"Ari"],[281.16,315.77,"Tau"],[315.77,318.32,"Ori"],[318.32,346.27,"Gem"]],"pluto":[[-16.16,7.58,"Gem"],[7.58,26.38,"Cnc"],[26.38,63.51,"Leo"],[63.51,75.0,"Com"],[75.0,88.8,"Vir"],[88.8,91.55,"Boo"],[91.55,111.62,"Vir"],[111.62,114.59,"Lib"],[114.59,119.65,"Ser"],[119.65,128.19,"Lib"],[128.19,131.69,"Oph"],[131.69,133.83,"Sco"],[133.83,148.01,"Oph"],[148.01,154.43,"Ser"],[154.43,154.64,"Oph"],[154.64,189.21,"Sgr"],[189.21,214.89,"Cap"],[214.89,243.02,"Aqr"],[243.02,297.86,"Cet"],[297.86,319.39,"Tau"],[319.39,332.83,"Ori"],[332.83,337.15,"Tau"],[337.15,343.84,"Ori"]]};

/* which sector of this planet's zodiac holds a given longitude,
   and how many degrees into it we are */
function sectorAt(obs,lon){
  const S=SECT[obs];
  for(let i=0;i<S.length;i++){
    let a=S[i][0],b=S[i][1],x=norm(lon);
    if(a<0){ if(x>=norm(a)||x<b) return{abbr:S[i][2],s:a,e:b,w:b-a,
      deg:(x>=norm(a)?x-360-a:x-a)}; }
    else if(x>=a&&x<b) return{abbr:S[i][2],s:a,e:b,w:b-a,deg:x-a};
  }
  return null;
}
/* degrees into the constellation, preferring the sector that matches
   the true 2-D lookup (a body off the plane can sit in a different one) */
function degInConst(obs,lon,abbr){
  const S=SECT[obs],x=norm(lon);
  for(let pass=0;pass<2;pass++){
    for(let i=0;i<S.length;i++){
      if(pass===0&&S[i][2]!==abbr)continue;
      let a=S[i][0],b=S[i][1];
      if(a<0){ if(x>=norm(a))return{deg:x-360-a,w:b-a};
               if(x<b)return{deg:x-a,w:b-a}; }
      else if(x>=a&&x<b)return{deg:x-a,w:b-a};
    }
  }
  return{deg:x%30,w:30};
}

const jd=function(dt){return dt.getTime()/86400000+2440587.5;};
const sub=function(a,b){return[a[0]-b[0],a[1]-b[1],a[2]-b[2]];};
const crossV=function(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];};
const dot=function(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];};
const unit=function(v){const n=Math.hypot(v[0],v[1],v[2]);return[v[0]/n,v[1]/n,v[2]/n];};
const lonOf=function(v){return norm(Math.atan2(v[1],v[0])*R2D);};
const vecOf=function(lon,lat){const l=lon*D2R,b=(lat||0)*D2R;
  return[Math.cos(b)*Math.cos(l),Math.cos(b)*Math.sin(l),Math.sin(b)];};

function helio(k,T){
  const e0=KEP[k];
  const a=e0[0]+e0[6]*T,e=e0[1]+e0[7]*T,I=(e0[2]+e0[8]*T)*D2R,
        L=e0[3]+e0[9]*T,vp=e0[4]+e0[10]*T,Om=(e0[5]+e0[11]*T)*D2R;
  let M=norm(L-vp)*D2R; if(M>Math.PI)M-=2*Math.PI;
  let E=M; for(let i=0;i<10;i++)E=E-(E-e*Math.sin(E)-M)/(1-e*Math.cos(E));
  const xp=a*(Math.cos(E)-e),yp=a*Math.sqrt(1-e*e)*Math.sin(E);
  const w=(vp*D2R)-Om,cw=Math.cos(w),sw=Math.sin(w),
        cO=Math.cos(Om),sO=Math.sin(Om),ci=Math.cos(I),si=Math.sin(I);
  return[(cw*cO-sw*sO*ci)*xp+(-sw*cO-cw*sO*ci)*yp,
         (cw*sO+sw*cO*ci)*xp+(-sw*sO+cw*cO*ci)*yp,
         (sw*si)*xp+(cw*si)*yp];
}
/* all bodies as seen from the observer planet: ecliptic lon + lat */
function planetoCentric(obs,J){
  const T=(J-2451545.0)/36525,o=helio(obs,T),out={};
  const ll=function(v){const r=Math.hypot(v[0],v[1],v[2]);
    return{lon:norm(Math.atan2(v[1],v[0])*R2D),lat:Math.asin(v[2]/r)*R2D,d:r};};
  out['მზე']=ll([-o[0],-o[1],-o[2]]);
  for(const k in KEP){ if(k===obs)continue; out[EN2KA[k]]=ll(sub(helio(k,T),o)); }
  return out;
}
/* observer planet's own ecliptic frame */
function planetFrame(obs,T){
  const e0=KEP[obs];
  const i=(e0[2]+e0[8]*T)*D2R,Om=(e0[5]+e0[11]*T)*D2R;
  const n=[Math.sin(i)*Math.sin(Om),-Math.sin(i)*Math.cos(Om),Math.cos(i)];
  const node=[Math.cos(Om),Math.sin(Om),0];              /* ascending node */
  const r=ROT[obs];
  const a0=(r[0]+r[1]*T)*D2R,d0=(r[2]+r[3]*T)*D2R;
  const pe=[Math.cos(d0)*Math.cos(a0),Math.cos(d0)*Math.sin(a0),Math.sin(d0)];
  const p=[pe[0],pe[1]*Math.cos(EPS)+pe[2]*Math.sin(EPS),
                 -pe[1]*Math.sin(EPS)+pe[2]*Math.cos(EPS)];
  const eq=unit(crossV(p,n));                            /* vernal equinox */
  return{n:n,node:unit(node),nodeY:unit(crossV(n,unit(node))),
         eq:eq,eqY:unit(crossV(n,eq)),pole:unit(p)};
}
const inPlane=function(fr,x,y,lon,lat){
  const v=vecOf(lon,lat);
  return norm(Math.atan2(dot(v,y),dot(v,x))*R2D);
};
function ayanamsa(fr){
  return norm(inPlane(fr,fr.eq,fr.eqY,SPICA_LON,SPICA_LAT)-180);
}
/* body-fixed axes for surface coordinates */
function bodyAxes(obs,J){
  const T=(J-2451545.0)/36525,d=J-2451545.0,r=ROT[obs];
  const a0=(r[0]+r[1]*T)*D2R,d0=(r[2]+r[3]*T)*D2R,W=norm(r[4]+r[5]*d)*D2R;
  const bf2eq=function(v){
    const z1=a0+Math.PI/2,x1=Math.PI/2-d0;
    let p=[v[0]*Math.cos(W)-v[1]*Math.sin(W),v[0]*Math.sin(W)+v[1]*Math.cos(W),v[2]];
    p=[p[0],p[1]*Math.cos(x1)-p[2]*Math.sin(x1),p[1]*Math.sin(x1)+p[2]*Math.cos(x1)];
    return[p[0]*Math.cos(z1)-p[1]*Math.sin(z1),p[0]*Math.sin(z1)+p[1]*Math.cos(z1),p[2]];
  };
  const eq2ec=function(v){return[v[0],v[1]*Math.cos(EPS)+v[2]*Math.sin(EPS),
                                 -v[1]*Math.sin(EPS)+v[2]*Math.cos(EPS)];};
  return{x:bf2eq([1,0,0]),y:bf2eq([0,1,0]),z:bf2eq([0,0,1]),
         xe:eq2ec(bf2eq([1,0,0])),ye:eq2ec(bf2eq([0,1,0])),ze:eq2ec(bf2eq([0,0,1]))};
}
function gmst(J){
  const T=(J-2451545.0)/36525;
  return norm(280.46061837+360.98564736629*(J-2451545.0)+0.000387933*T*T-T*T*T/38710000.0);
}
function precessToJ2000(ra,dec,J){
  const T=(J-2451545.0)/36525;
  const ze=(2306.2181*T+0.30188*T*T)/3600*D2R,z=(2306.2181*T+1.09468*T*T)/3600*D2R,
        th=(2004.3109*T-0.42665*T*T)/3600*D2R;
  const a=ra*D2R,d=dec*D2R;
  const A=Math.cos(d)*Math.sin(a-z);
  const B=Math.cos(th)*Math.cos(d)*Math.cos(a-z)+Math.sin(th)*Math.sin(d);
  const C=-Math.sin(th)*Math.cos(d)*Math.cos(a-z)+Math.cos(th)*Math.sin(d);
  return{ra:norm(Math.atan2(A,B)*R2D-ze*R2D),dec:Math.asin(C)*R2D};
}
/* Earth birthplace -> corresponding point on the observer planet */
function earthPlaceTo(obs,J,elat,elon){
  const lst=norm(gmst(J)+elon);
  const p=precessToJ2000(lst,elat,J);
  const a=p.ra*D2R,dd=p.dec*D2R;
  const dir=[Math.cos(dd)*Math.cos(a),Math.cos(dd)*Math.sin(a),Math.sin(dd)];
  const ax=bodyAxes(obs,J);
  return{lat:Math.asin(dot(dir,ax.z))*R2D,
         lon:norm(Math.atan2(dot(dir,ax.y),dot(dir,ax.x))*R2D),
         ra:p.ra,dec:p.dec};
}
/* ASC / MC on the observer planet, expressed in its own orbital plane */
function angles(obs,J,lat,lonE,fr){
  const ax=bodyAxes(obs,J);
  const f=lat*D2R,l=lonE*D2R;
  const Zb=[Math.cos(f)*Math.cos(l),Math.cos(f)*Math.sin(l),Math.sin(f)];
  const Z=unit([ax.xe[0]*Zb[0]+ax.ye[0]*Zb[1]+ax.ze[0]*Zb[2],
                ax.xe[1]*Zb[0]+ax.ye[1]*Zb[1]+ax.ze[1]*Zb[2],
                ax.xe[2]*Zb[0]+ax.ye[2]*Zb[1]+ax.ze[2]*Zb[2]]);
  const E=unit(crossV(fr.pole,Z)),n=fr.n;
  let mc=unit(crossV(E,n)); if(dot(mc,Z)<0)mc=[-mc[0],-mc[1],-mc[2]];
  let asc=unit(crossV(Z,n)); if(dot(asc,E)<0)asc=[-asc[0],-asc[1],-asc[2]];
  return{ascV:asc,mcV:mc,tilt:Math.acos(Math.abs(dot(fr.pole,n)))*R2D};
}

const ASP=[{n:'შეერთება',a:[0],o:10,s:'☌',c:'#f9c646'},{n:'ოპოზიცია',a:[180],o:10,s:'☍',c:'#f08050'},
 {n:'ტრინი',a:[120,240],o:8,s:'△',c:'#a078f0'},{n:'კვადრატი',a:[90,270],o:8,s:'□',c:'#e84040'},
 {n:'სექსტილი',a:[60,300],o:6,s:'⚹',c:'#30c890'}];

/* ═══ WHEEL ═══ */
const CX=350,CY=350,R1=268,R2=200,R3=132,R4=100;
const NS='http://www.w3.org/2000/svg';
const el=function(t,at,p){const e=document.createElementNS(NS,t);
  for(const k in at)e.setAttribute(k,at[k]); if(p)p.appendChild(e); return e;};
const txt=function(p,s,x,y,at){
  const e=el('text',Object.assign({'text-anchor':'middle','dominant-baseline':'central',x:x,y:y},at||{}),p);
  e.textContent=s; return e;};
const e2s=function(ec,asc){return(-(ec-asc))*D2R+Math.PI;};
const fmt2=function(d){const x=Math.floor(d);
  return x+'°'+String(Math.floor((d-x)*60)).padStart(2,'0')+"'";};

function drawWheel(P,asc,mc,houses,asps,bands,MO){
  const svg=$('wheel');svg.innerHTML='';
  const RO=272;                 /* the big outer circle              */
  const RSi=196;                /* inner edge of the sign band       */
  const RPl=302;                /* planet glyph ring, outside        */
  const defs=el('defs',{},svg);
  const g=el('radialGradient',{id:'bg',cx:'50%',cy:'50%',r:'50%'},defs);
  el('stop',{offset:'0%','stop-color':'#141830'},g);
  el('stop',{offset:'100%','stop-color':'#05040c'},g);
  el('rect',{width:700,height:700,fill:'url(#bg)'},svg);

  /* ── sign / constellation band, filling the big circle ── */
  bands.forEach(function(b){
    const p=function(d,r){const a=e2s(d,asc);
      return(CX+Math.cos(a)*r)+','+(CY+Math.sin(a)*r);};
    const span=b.e-b.s,la=span>180?1:0;
    el('path',{d:'M'+p(b.s,RO)+' A'+RO+','+RO+' 0 '+la+',0 '+p(b.e,RO)+
                 ' L'+p(b.e,RSi)+' A'+RSi+','+RSi+' 0 '+la+',1 '+p(b.s,RSi)+' Z',
      fill:'rgba(14,18,38,.85)',stroke:b.col,'stroke-width':.8,opacity:.9},svg);
    if(span>2.2){
      const a=e2s(b.s+span/2,asc);
      txt(svg,b.sym,CX+Math.cos(a)*(RSi+24),CY+Math.sin(a)*(RSi+24),
        {fill:b.col,'font-size':span<11?13:19,'font-family':'serif'});
    }
  });

  /* ── the degree scale: little lines INSIDE the big circle ── */
  for(let d=0;d<360;d++){
    const a=e2s(d,asc),co=Math.cos(a),si=Math.sin(a);
    el('line',{x1:CX+co*RO,y1:CY+si*RO,x2:CX+co*(RO-7),y2:CY+si*(RO-7),
      stroke:'rgba(150,178,220,.5)','stroke-width':.7},svg);
  }
  /* ── circles, angles, aspect web ── */
  el('circle',{cx:CX,cy:CY,r:RO,fill:'none',stroke:'rgba(190,214,248,.7)','stroke-width':1.7},svg);
  el('circle',{cx:CX,cy:CY,r:RSi,fill:'none',stroke:'rgba(124,154,208,.5)','stroke-width':1.2},svg);
  [0,3,6,9].forEach(function(i){
    const a=e2s(houses[i],asc);
    el('line',{x1:CX+Math.cos(a)*R4,y1:CY+Math.sin(a)*R4,
      x2:CX+Math.cos(a)*RSi,y2:CY+Math.sin(a)*RSi,
      stroke:'rgba(168,196,234,.5)','stroke-width':1.1},svg);
  });
  el('circle',{cx:CX,cy:CY,r:R4,fill:'rgba(6,8,18,.95)',stroke:'rgba(60,80,130,.6)','stroke-width':1},svg);
  asps.forEach(function(a){
    const a1=e2s(P[a.p1].lon,asc),a2=e2s(P[a.p2].lon,asc);
    el('line',{x1:CX+Math.cos(a1)*R4,y1:CY+Math.sin(a1)*R4,
      x2:CX+Math.cos(a2)*R4,y2:CY+Math.sin(a2)*R4,
      stroke:a.color,'stroke-width':1,opacity:.45},svg);
  });

  /* ── planets and the observer planet's moons, one ring outside ── */
  const items=[];
  Object.keys(P).forEach(function(n){
    const info=PI_[n]||{sym:'?',color:'#fff'};
    items.push({id:'p:'+n,lon:P[n].lon,sym:info.sym,color:info.color,
                size:17,retro:P[n].retro,moon:false});
  });
  if(MO&&MO.length)MO.forEach(function(m){
    const info=MOON_I[m.key]||{sym:'?',color:'#cfd8e8'};
    items.push({id:'m:'+m.key,lon:m.lon,sym:info.sym,color:info.color,
                size:m.key==='moon'?15:10,retro:false,moon:true});
  });
  const disp={};
  items.forEach(function(it){disp[it.id]=e2s(it.lon,asc);});
  const GAP=20/RPl;
  for(let it=0;it<400;it++){
    let mv=false;
    for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){
      let d=disp[items[j].id]-disp[items[i].id];
      while(d>Math.PI)d-=2*Math.PI;
      while(d<-Math.PI)d+=2*Math.PI;
      if(Math.abs(d)<GAP&&Math.abs(d)>1e-4){
        const p=(GAP-Math.abs(d))/2,s=d>0?1:-1;
        disp[items[i].id]-=p*s;disp[items[j].id]+=p*s;mv=true;
      }
    }
    if(!mv)break;
  }
  items.forEach(function(it){
    const tA=e2s(it.lon,asc);
    el('line',{x1:CX+Math.cos(tA)*(RO+1),y1:CY+Math.sin(tA)*(RO+1),
      x2:CX+Math.cos(tA)*(RO+(it.moon?6:9)),y2:CY+Math.sin(tA)*(RO+(it.moon?6:9)),
      stroke:it.color,'stroke-width':it.moon?1:1.5,opacity:it.moon?.75:1},svg);
    el('circle',{cx:CX+Math.cos(tA)*(RO+1),cy:CY+Math.sin(tA)*(RO+1),
      r:it.moon?1.2:1.7,fill:it.color},svg);
    const gx=CX+Math.cos(disp[it.id])*RPl,gy=CY+Math.sin(disp[it.id])*RPl;
    let df=disp[it.id]-tA;
    while(df>Math.PI)df-=2*Math.PI;
    while(df<-Math.PI)df+=2*Math.PI;
    if(Math.abs(df)>0.012)
      el('line',{x1:CX+Math.cos(tA)*(RO+9),y1:CY+Math.sin(tA)*(RO+9),x2:gx,y2:gy,
        stroke:it.color,'stroke-width':.5,opacity:.4,'stroke-dasharray':'2 2'},svg);
    txt(svg,it.sym,gx,gy,{fill:it.color,'font-size':it.size,
      'font-family':it.moon?'Cinzel,serif':'serif',
      'font-weight':it.moon?'600':'normal'});
    if(it.retro)txt(svg,'℞',gx+10,gy-8,{fill:'#f87171','font-size':7,'font-family':'serif'});
  });

  [['AC',asc],['MC',mc]].forEach(function(pair){
    const a=e2s(pair[1],asc);
    el('line',{x1:CX+Math.cos(a)*RO,y1:CY+Math.sin(a)*RO,
      x2:CX+Math.cos(a)*(RO+16),y2:CY+Math.sin(a)*(RO+16),stroke:'#a8c4ea','stroke-width':2.4},svg);
    txt(svg,pair[0],CX+Math.cos(a)*(RO+34),CY+Math.sin(a)*(RO+34),
      {fill:'#a8c4ea','font-size':12,'font-weight':'bold','font-family':'Cinzel,serif'});
  });
}

/* ═══ GENERATE ═══ */
async function gen(){
  $('err').innerHTML='';
  try{
    if(typeof iauFromEcliptic!=='function'){
      $('err').innerHTML='<div class="err">⚠ constellations.js არ ჩაიტვირთა</div>';return;}
    const obs=$('i-obs').value,pd=PLA[obs];
    const y=+$('i-year').value,m=+$('i-month').value,d=+$('i-day').value,
          h=+$('i-hour').value,mi=+$('i-min').value;
    const dt=new Date(Date.UTC(y,m-1,d,h,mi,0));
    if(isNaN(dt.getTime())){$('err').innerHTML='<div class="err">⚠ არასწორი თარიღი</div>';return;}
    const J=jd(dt),T=(J-2451545.0)/36525;
    const mode=$('i-mode').value,iau=(mode==='iau');
    const fr=planetFrame(obs,T),aya=ayanamsa(fr);

    const mp=earthPlaceTo(obs,J,+$('i-elat').value,+$('i-elon').value);
    $('i-derived').innerHTML='🪐 <b style="color:'+pd.col+'">'+
      Math.abs(mp.lat).toFixed(2)+'°'+(mp.lat>=0?'N':'S')+' '+mp.lon.toFixed(2)+'°E</b> — '+
      pd.ka+'ზე შესაბამისი წერტილი<br><span style="color:rgba(190,205,230,.5);font-size:10px">'+
      'ზენიტის მიმართულება RA '+mp.ra.toFixed(2)+'° Dec '+mp.dec.toFixed(2)+'°</span>';

    const F=planetoCentric(obs,J),F2=planetoCentric(obs,J+1);
    const ang=angles(obs,J,mp.lat,mp.lon,fr);

    /* display longitude in the chosen frame */
    const dispV=function(v){
      if(iau)return norm(Math.atan2(dot(v,fr.nodeY),dot(v,fr.node))*R2D);
      const L=norm(Math.atan2(dot(v,fr.eqY),dot(v,fr.eq))*R2D);
      return (mode==='psid')?norm(L-aya):L;
    };
    const disp=function(lon,lat){return dispV(vecOf(lon,lat));};
    const asc=dispV(ang.ascV),mc=dispV(ang.mcV);

    const P={};
    for(const k in F){
      let dl=F2[k].lon-F[k].lon; if(dl>180)dl-=360; if(dl<-180)dl+=360;
      P[k]={lon:disp(F[k].lon,F[k].lat),raw:F[k].lon,lat:F[k].lat,d:F[k].d,retro:dl<0};
    }

    /* moons of the observer planet, put into the same display frame */
    let MO=[],moonNA=[],moonErr='';
    try{
      const md=await getMoons(obs,y,m,d,h,mi);
      moonNA=md.unavailable||[];
      moonErr=md.error||'';
      MO=(md.moons||[]).map(function(mo){
        return{key:mo.key,name_ka:mo.name_ka,lon:disp(mo.lon,mo.lat),
               raw:mo.lon,lat:mo.lat,radii:mo.radii,
               period:mo.period_days,behind:mo.behind,source:mo.source};
      });
      /* Earth's Moon: Earth's own vector plus the geocentric offset,
         so it is seen correctly from whichever planet we observe from */
      if(md.earth_moon&&F['დედამიწა']){
        const E=F['დედამიწა'],ev=vecOf(E.lon,E.lat),o=md.earth_moon.offset_au;
        const mv=[ev[0]*E.d+o[0],ev[1]*E.d+o[1],ev[2]*E.d+o[2]];
        const mr=Math.hypot(mv[0],mv[1],mv[2]);
        const mlon=norm(Math.atan2(mv[1],mv[0])*R2D),
              mlat=Math.asin(mv[2]/mr)*R2D;
        /* separation from Earth as seen from here, in degrees */
        let sep=Math.acos(Math.max(-1,Math.min(1,
          (ev[0]*mv[0]+ev[1]*mv[1]+ev[2]*mv[2])/mr)))*R2D;
        MO.push({key:'moon',name_ka:'მთვარე (დედამიწის)',lon:disp(mlon,mlat),
                 raw:mlon,lat:mlat,radii:null,sep:sep,
                 period:27.321661,behind:null,source:'ephem',ofEarth:true});
      }
    }catch(e){MO=[];moonNA=[];moonErr=e.message;}

    const houses=[];for(let i=0;i<12;i++)houses.push(norm(asc+i*30));
    const hOf=function(L){return Math.floor(norm(L-asc)/30)+1;};

    const asps=[],ks=Object.keys(P);
    for(let i=0;i<ks.length;i++)for(let j=i+1;j<ks.length;j++){
      const raw=norm(P[ks[j]].lon-P[ks[i]].lon);
      let best=null,bo=999;
      for(let x=0;x<ASP.length;x++)for(let t=0;t<ASP[x].a.length;t++){
        let df=Math.abs(raw-ASP[x].a[t]); if(df>180)df=360-df;
        if(df<=ASP[x].o&&df<bo){bo=df;best=ASP[x];}
      }
      if(best)asps.push({p1:ks[i],p2:ks[j],type:best.n,sym:best.s,color:best.c,
                         orb:Math.round(bo*100)/100});
    }
    asps.sort(function(a,b){return a.orb-b.orb;});

    /* wheel bands */
    let bands;
    if(iau){
      bands=SECT[obs].map(function(b){
        const info=(typeof IAU_KA!=='undefined')?
          {ka:IAU_KA[b[2]]||b[2],sym:(IAU_SYM&&IAU_SYM[b[2]])||'✦',
           col:(IAU_COL&&IAU_COL[b[2]])||'#8898b8'}:{ka:b[2],sym:'✦',col:'#8898b8'};
        return{s:b[0],e:b[1],sym:info.sym,col:info.col,ka:info.ka};});
    }else{
      bands=ZSYM.map(function(sy,i){
        return{s:i*30,e:(i+1)*30,sym:sy,col:ZCOL[i],ka:SIGN_KA[i]};});
    }
    drawWheel(P,asc,mc,houses,asps,bands,MO);

    $('out').style.display='block';
    $('orb').style.background='radial-gradient(circle at 34% 30%,'+pd.g1+' 0%,'+pd.col+' 45%,'+pd.g2+' 80%,#0a0810 100%)';
    const MK={iau:'IAU თანავარსკვლავედები',ptrop:'ტროპიკული (12)',psid:'სიდერიული (12)'};
    const nm=$('i-name').value?$('i-name').value+' — ':'';
    $('lbl').textContent=nm+pd.ka+'ული რუქა · '+MK[mode];
    $('ptitle').textContent='🪐 '+pd.ka+'ოცენტრული — '+MK[mode];
    $('hsub').textContent=pd.sym+' '+pd.ka+' · '+SECT[obs].length+' sectors · incl '+
      (KEP[obs][2]).toFixed(2)+'°';

    const sigOf=function(v){
      if(iau){
        const r=iauFromEcliptic(v.rawEcl!=null?v.rawEcl:v.raw,v.lat||0);
        const d=degInConst(obs,v.lon,r.abbr);
        return{sym:r.sym,ka:r.ka,col:r.col,abbr:r.abbr,
               deg:d.deg,width:d.w,lat:v.lat};
      }
      const si=Math.floor(norm(v.lon)/30)%12;
      return{sym:ZSYM[si],ka:SIGN_KA[si],col:ZCOL[si],abbr:'',
             deg:norm(v.lon)%30,width:30,lat:v.lat};
    };
    const inWhat={};
    $('ptb').innerHTML=ORDER.filter(function(n){return P[n]||n==='AC'||n==='MC';}).map(function(n){
      const v=n==='AC'?{lon:asc,raw:lonOf(ang.ascV),lat:0}:
              n==='MC'?{lon:mc,raw:lonOf(ang.mcV),lat:0}:P[n];
      const s=sigOf(v),inf=PI_[n];
      if(s.abbr)inWhat[n]=s.abbr;
      return '<tr><td><span style="color:'+inf.color+';font-family:serif;font-size:16px">'+inf.sym+'</span></td>'+
        '<td style="color:'+inf.color+';font-size:11px">'+n+'</td>'+
        '<td class="deg">'+fmt2(s.deg)+
          (iau?' <span class="lat">/'+s.width.toFixed(1)+'°</span>':'')+
          (iau&&s.lat!=null?' <span class="lat">β'+(s.lat>=0?'+':'')+
            s.lat.toFixed(1)+'°</span>':'')+'</td>'+
        '<td><span style="color:'+s.col+';font-family:serif;font-size:13px">'+s.sym+'</span> '+
        '<span style="font-size:10px;color:'+s.col+'">'+s.ka+'</span></td>'+
        '<td><span class="badge">H'+hOf(v.lon)+'</span></td>'+
        '<td>'+(v.retro?'<span class="retro">℞</span>':'')+'</td></tr>';
    }).join('');

    /* moon rows, appended under the planets in the same table */
    if(MO.length){
      $('ptb').innerHTML+=MO.map(function(mo){
        const s=sigOf({lon:mo.lon,raw:mo.raw,lat:mo.lat}),
              info=MOON_I[mo.key]||{sym:'?',color:'#cfd8e8'};
        return '<tr style="background:rgba(124,154,208,.05)">'+
          '<td><span style="color:'+info.color+';font-family:Cinzel,serif;font-size:11px">'+info.sym+'</span></td>'+
          '<td style="color:'+info.color+';font-size:11px">'+mo.name_ka+
            ' <span class="lat">მთვარე</span></td>'+
          '<td class="deg">'+fmt2(s.deg)+
            (iau?' <span class="lat">/'+s.width.toFixed(1)+'°</span>':'')+'</td>'+
          '<td><span style="color:'+s.col+';font-family:serif;font-size:13px">'+s.sym+'</span> '+
          '<span style="font-size:10px;color:'+s.col+'">'+s.ka+'</span></td>'+
          '<td><span class="badge">H'+hOf(mo.lon)+'</span></td>'+
          '<td><span class="lat">'+
            (mo.radii!=null?mo.radii.toFixed(1)+'R':(mo.sep!=null?mo.sep.toFixed(2)+'°':'—'))+
            (mo.source==='fit'?' ~':'')+'</span></td></tr>';
      }).join('');
    }

    /* dedicated moon panel */
    if(moonErr){
      $('moonbox').innerHTML='<div class="card"><div class="card-title">🌙 მთვარეები</div>'+
        '<div style="color:#f87171;font-size:12px">⚠ '+moonErr+'</div>'+
        '<div class="note">შეამოწმეთ, რომ ბექენდზე დაყენებულია moons.py და ephem.</div></div>';
    }else if(MO.length||moonNA.length){
      const rows=MO.map(function(mo){
        const info=MOON_I[mo.key]||{sym:'?',color:'#cfd8e8'};
        const per=mo.period?(mo.period<1?(mo.period*24).toFixed(1)+' სთ':mo.period.toFixed(2)+' დღე'):'—';
        return '<span style="display:inline-block;margin:0 14px 6px 0">'+
          '<b style="color:'+info.color+'">'+info.sym+' '+mo.name_ka+'</b> '+
          '<span style="color:rgba(190,205,230,.55);font-size:11px">'+
          (mo.radii!=null?mo.radii.toFixed(1)+' რადიუსი':
           (mo.sep!=null?'დედამიწიდან '+mo.sep.toFixed(2)+'°':''))+' · '+per+
          (mo.behind===null?'':' · '+(mo.behind?'პლანეტის უკან':'პლანეტის წინ'))+
          (mo.source==='fit'?' · <span style="color:#b8a060">მოდელი</span>':'')+
          '</span></span>';
      }).join('');
      const na=moonNA.length?'<div style="margin-top:6px;color:rgba(190,205,230,.45);font-size:10px">'+
        moonNA.map(function(u){return u.name_ka;}).join(', ')+
        ' — ამ ბიბლიოთეკას მისთვის ანალიტიკური თეორია არ გააჩნია, ამიტომ არ ჩანს</div>':'';
      $('moonbox').innerHTML='<div class="card"><div class="card-title">🌙 '+pd.ka+'ის მთვარეები</div>'+
        '<div style="font-size:12px;line-height:2">'+(rows||'<span style="color:rgba(190,205,230,.5)">—</span>')+'</div>'+
        na+'<div class="note">მთვარეები ნაჩვენებია ისე, როგორც ისინი ჩანან '+pd.ka+'იდან — '+
        'პლანეტების გვერდით, იმავე გარე რგოლზე. მანძილი პლანეტის რადიუსებშია.'+
        (MO.some(function(x){return x.source==='fit';})?
         '<br>„მოდელი" — მარსისა და ურანის თანამგზავრებისთვის ბიბლიოთეკის თეორია მოქმედებს '+
         'მხოლოდ ~1999-2040 წლებში; სხვა თარიღებზე გამოიყენება მისივე მონაცემებზე მორგებული '+
         'ორბიტული მოდელი (სიზუსტე ~0.5°, ფობოსისთვის ~5°).':'')+
        '</div></div>';
    }else $('moonbox').innerHTML='';

    const ROM=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
    const ANG={0:'AC',3:'IC',6:'DC',9:'MC'};
    $('htb').innerHTML=houses.map(function(hh,i){
      const a=ANG[i];
      let sym,ka,col,dg;
      if(iau){
        const sc=sectorAt(obs,hh);
        if(sc){sym=(IAU_SYM&&IAU_SYM[sc.abbr])||'✦';ka=(IAU_KA&&IAU_KA[sc.abbr])||sc.abbr;
               col=(IAU_COL&&IAU_COL[sc.abbr])||'#8898b8';dg=sc.deg;}
        else{sym='✦';ka='—';col='#8898b8';dg=0;}
      }else{
        const si=Math.floor(norm(hh)/30)%12;
        sym=ZSYM[si];ka=SIGN_KA[si];col=ZCOL[si];dg=norm(hh)%30;
      }
      return '<tr><td style="color:'+(a?'#a8c4ea':'rgba(190,205,230,.7)')+';font-family:Cinzel,serif;font-size:11px">'+
        ROM[i]+(a?' <span style="font-size:9px;opacity:.7">'+a+'</span>':'')+'</td>'+
        '<td><span style="color:'+col+';font-family:serif;font-size:13px">'+sym+'</span> '+
        '<span style="font-size:10px;color:'+col+'">'+ka+'</span></td>'+
        '<td class="deg">'+fmt2(dg)+'</td></tr>';
    }).join('');

    $('atitle').textContent='⚡ ასპექტები — სულ '+asps.length;
    $('atb').innerHTML=asps.map(function(a){
      const i1=PI_[a.p1],i2=PI_[a.p2];
      return '<tr><td><span style="color:'+i1.color+';font-family:serif">'+i1.sym+'</span> '+
        '<span style="font-size:10px;color:'+i1.color+'">'+a.p1+'</span></td>'+
        '<td><span style="color:'+a.color+';font-size:15px;font-family:serif">'+a.sym+'</span></td>'+
        '<td><span style="color:'+i2.color+';font-family:serif">'+i2.sym+'</span> '+
        '<span style="font-size:10px;color:'+i2.color+'">'+a.p2+'</span></td>'+
        '<td style="color:'+a.color+';font-size:10px">'+a.type+'</td>'+
        '<td style="color:rgba(190,205,230,.6);font-size:10px">'+a.orb+'°</td></tr>';
    }).join('');

    /* non-zodiacal constellations present */
    if(iau){
      const zod=['Ari','Tau','Gem','Cnc','Leo','Vir','Lib','Sco','Sgr','Cap','Aqr','Psc'];
      const odd=[];
      for(const n in inWhat)if(zod.indexOf(inWhat[n])<0)
        odd.push(n+' — <b>'+(IAU_KA[inWhat[n]]||inWhat[n])+'</b>');
      const uniq={};SECT[obs].forEach(function(b){if(zod.indexOf(b[2])<0)uniq[b[2]]=1;});
      const list=Object.keys(uniq).map(function(k){return IAU_KA[k]||k;});
      $('oddbox').innerHTML='<div class="odd">✦ '+pd.ka+'ის ზოდიაქო — <b>'+
        SECT[obs].length+' სექტორი</b>, ეკლიპტიკის დახრა '+KEP[obs][2].toFixed(2)+'°'+
        (list.length?'<br>არაზოდიაქალური თანავარსკვლავედები ამ პლანეტის მზის გზაზე: <b style="color:#e0b080">'+
          list.join(' · ')+'</b>':'')+
        (odd.length?'<br>ამ რუქაში: '+odd.join(' · '):'')+'</div>';
    }else $('oddbox').innerHTML='';

    /* which bodies are "inner" from here */
    const aObs=KEP[obs][0];
    const inner=[];
    for(const k in KEP){
      if(k===obs)continue;
      if(KEP[k][0]<aObs){
        const e=Math.asin(Math.min(1,KEP[k][0]/aObs))*R2D;
        inner.push(EN2KA[k]+' ('+e.toFixed(0)+'°)');
      }
    }
    $('innerbox').innerHTML='<div class="hl"><b style="color:'+pd.col+'">'+pd.sym+' '+pd.ka+'იდან</b> — '+
      (inner.length?'შიდა პლანეტები (მაქს. ელონგაცია): <b>'+inner.join(' · ')+'</b><br>'+
       '<span style="color:rgba(190,205,230,.65);font-size:11px">ისინი მზეს არასოდეს შორდებიან — მხოლოდ დილის ან საღამოს ვარსკვლავები არიან.</span>'
       :'ყველა პლანეტა გარეთაა — ყველა შეიძლება ოპოზიციაში იყოს მზესთან.')+'</div>';

    const rp=PLA[obs].day,yr=PLA[obs].yr;
    $('info').innerHTML=
      '<span class="k" style="color:rgba(190,205,230,.55);font-size:11px">ბრუნვის პერიოდი:</span> <b>'+
      Math.abs(rp).toFixed(3)+' დღე'+(rp<0?' (რეტროგრადი)':'')+'</b>'+
      ' &nbsp;·&nbsp; <span style="color:rgba(190,205,230,.55);font-size:11px">წელი:</span> <b>'+
      yr.toLocaleString('ka-GE')+' დღე</b>'+
      ' &nbsp;·&nbsp; <span style="color:rgba(190,205,230,.55);font-size:11px">ღერძის დახრა ორბიტასთან:</span> <b>'+
      ang.tilt.toFixed(2)+'°</b><br>'+
      '<span style="color:rgba(190,205,230,.55);font-size:11px">ორბიტის დახრა ეკლიპტიკასთან:</span> <b>'+
      KEP[obs][2].toFixed(3)+'°</b>'+
      (mode==='psid'?' &nbsp;·&nbsp; <span style="color:rgba(190,205,230,.55);font-size:11px">აიანამსა:</span> <b>'+
        aya.toFixed(3)+'°</b>':'')+
      ' &nbsp;·&nbsp; <span style="color:rgba(190,205,230,.55);font-size:11px">მზე:</span> <b>'+
      P['მზე'].d.toFixed(3)+' AU</b><br>'+
      '<span style="color:rgba(190,205,230,.45);font-size:10px">'+
      (iau?'IAU საზღვრები Roman 1987 · B1875 · 2-D ძიება':
       mode==='ptrop'?'12 თანაბარი ნიშანი '+pd.ka+'ის ბუნიობის წერტილიდან':
       '12 თანაბარი ნიშანი · სპიკაზე მიბმული')+
      ' · ეფემერიდი: JPL Keplerian (1800–2100, ~1′)'+
      (MO.length?' · მთვარეები: PyEphem სატელიტური თეორიები':'')+'</span>';

    $('out').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){
    $('err').innerHTML='<div class="err">⚠ '+e.message+'</div>';
    console.error(e);
  }
}
function setNow(){
  const n=new Date();
  $('i-day').value=n.getUTCDate();$('i-month').value=n.getUTCMonth()+1;
  $('i-year').value=n.getUTCFullYear();$('i-hour').value=n.getUTCHours();
  $('i-min').value=n.getUTCMinutes();
}
const BACKEND='https://astrology-production-b165.up.railway.app';
let cityTimer=null;
$('i-city').addEventListener('input',function(){
  clearTimeout(cityTimer);
  const q=$('i-city').value;
  if(q.length<2){$('i-cityhint').textContent='';return;}
  cityTimer=setTimeout(function(){
    $('i-cityhint').textContent='⏳ ძიება...';
    fetch(BACKEND+'/geocode',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({city:q})})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.error){$('i-cityhint').textContent='❌ '+d.error;return;}
        $('i-elat').value=(+d.lat).toFixed(4);$('i-elon').value=(+d.lon).toFixed(4);
        $('i-cityhint').textContent='📍 '+(d.display||q);
        if($('out').style.display!=='none')gen();})
      .catch(function(){$('i-cityhint').textContent='❌ ხელით შეიყვანეთ განედი/გრძედი';});
  },600);
});
['i-obs','i-mode','i-elat','i-elon'].forEach(function(id){
  $(id).addEventListener('change',function(){if($('out').style.display!=='none')gen();});
});
$('btn-gen').addEventListener('click',gen);
$('btn-now').addEventListener('click',function(){setNow();gen();});
setNow();
</script>
</body>
</html>
