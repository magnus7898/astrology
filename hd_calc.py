<!doctype html>
<html lang="ka">
<head>
<meta charset="utf-8">
<title>ადამიანის დიზაინი</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Cinzel:wght@400;500;600&family=Noto+Serif+Georgian:wght@300;400;500&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{
  --void:#04030a;--deep:#07050f;--surface:#0e0b1c;--raised:#161228;--card:#120f22;
  --border:rgba(160,120,70,.15);--border-h:rgba(200,160,90,.45);
  --gold:#c49550;--gold-lt:#e8c47a;--gold-dim:#7a5c28;--gold-glow:rgba(196,149,80,.12);
  --ink:#f0e8d8;--ink-mid:#a8998a;--ink-dim:#584e44;
  --violet:#6d28d9;--violet-lt:#a78bfa;--indigo-lt:#818cf8;--r:4px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100vh;background:var(--void);color:var(--ink);font-family:'Noto Serif Georgian',serif;font-weight:400;line-height:1.6;font-size:15px;}
body{background:
  radial-gradient(ellipse 100% 60% at 50% -5%,rgba(109,40,217,.1),transparent 55%),
  radial-gradient(ellipse 70% 50% at 5% 50%,rgba(109,40,217,.06),transparent 50%),
  radial-gradient(ellipse 60% 70% at 95% 90%,rgba(196,149,80,.05),transparent 50%),
  var(--void);}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;
  background-image:
    radial-gradient(1px 1px at 15% 20%,rgba(255,255,255,.4),transparent),
    radial-gradient(1px 1px at 80% 10%,rgba(255,255,255,.3),transparent),
    radial-gradient(1px 1px at 45% 75%,rgba(255,255,255,.25),transparent),
    radial-gradient(1px 1px at 90% 40%,rgba(255,255,255,.35),transparent),
    radial-gradient(1px 1px at 25% 90%,rgba(255,255,255,.2),transparent),
    radial-gradient(1.5px 1.5px at 60% 30%,rgba(255,255,255,.3),transparent),
    radial-gradient(2px 2px at 35% 50%,rgba(196,149,80,.25),transparent);}
body::after{content:"";position:fixed;top:-20%;left:50%;transform:translateX(-50%);
  width:800px;height:400px;border-radius:50%;
  background:radial-gradient(ellipse,rgba(196,149,80,.06) 0%,transparent 70%);
  pointer-events:none;z-index:0;}

.page{position:relative;z-index:1;max-width:1600px;margin:0 auto;padding:52px 44px 120px;}

/* HEADER */
header{text-align:center;padding-bottom:28px;margin-bottom:28px;position:relative;}
header::before{content:"✦  ✦  ✦";display:block;font-size:.65rem;letter-spacing:.5em;color:var(--gold-dim);margin-bottom:18px;}
.brand{font-family:'Cinzel Decorative',serif;font-size:2.4rem;font-weight:400;letter-spacing:.08em;
  background:linear-gradient(180deg,var(--gold-lt) 0%,var(--gold) 50%,var(--gold-dim) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1.2;margin-bottom:10px;}
.brand-sub{font-family:'Cinzel',serif;font-size:.6rem;letter-spacing:.5em;text-transform:uppercase;color:var(--ink-dim);}
header::after{content:"";display:block;width:320px;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold-dim),transparent);margin:22px auto 0;}

/* FORM */
.form-shell{max-width:900px;margin:0 auto 28px;
  background:linear-gradient(145deg,rgba(22,18,40,.9),rgba(7,5,15,.95));
  border:1px solid var(--border);border-radius:8px;padding:38px 40px 32px;
  position:relative;overflow:hidden;}
.form-shell::before{content:"";position:absolute;top:0;left:10%;right:10%;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);}
.form-shell::after{content:"";position:absolute;inset:0;
  background:radial-gradient(ellipse 60% 40% at 50% 0%,rgba(196,149,80,.04),transparent);pointer-events:none;}
.form-title{font-family:'Cinzel',serif;font-size:.58rem;letter-spacing:.4em;text-transform:uppercase;
  color:var(--gold-dim);text-align:center;margin-bottom:28px;}
.form-grid{display:grid;grid-template-columns:1fr 1fr 2fr auto;gap:20px;align-items:end;position:relative;z-index:1;}
.field label{display:block;font-size:.55rem;letter-spacing:.3em;text-transform:uppercase;
  color:var(--ink-dim);margin-bottom:8px;font-family:'Cinzel',serif;}
.field input{width:100%;padding:12px 15px;background:rgba(255,255,255,.03);color:var(--ink);
  border:1px solid var(--border);border-radius:var(--r);font:inherit;font-size:.88rem;
  transition:border-color .2s,background .2s;outline:none;}
.field input:focus{border-color:var(--gold);background:rgba(196,149,80,.04);}
.field input::placeholder{color:var(--ink-dim);}
.city-hint{font-size:.68rem;color:var(--indigo-lt);margin-top:5px;min-height:13px;}
.btn-calc{padding:12px 26px;background:linear-gradient(145deg,#c49550,#8a6030);
  color:#110800;border:0;border-radius:var(--r);font-family:'Cinzel',serif;font-weight:600;
  font-size:.65rem;letter-spacing:.22em;text-transform:uppercase;cursor:pointer;white-space:nowrap;
  box-shadow:0 4px 24px rgba(196,149,80,.25),0 0 0 1px rgba(196,149,80,.2);
  transition:opacity .2s,box-shadow .2s,transform .1s;}
.btn-calc:hover{opacity:.9;box-shadow:0 6px 32px rgba(196,149,80,.35),0 0 0 1px rgba(196,149,80,.3);}
.btn-calc:active{transform:translateY(1px);}
.btn-calc:disabled{opacity:.35;cursor:wait;}
.coords-row{grid-column:span 4;font-size:.68rem;color:var(--ink-dim);display:flex;gap:18px;margin-top:-8px;}
.status{font-size:.85rem;color:var(--ink-dim);margin-bottom:10px;text-align:center;min-height:16px;}
.status.error{color:#e06060;}
.hidden{display:none!important}

/* SECTION DIVIDER */
.sec-head{display:flex;align-items:center;gap:16px;margin-bottom:16px;}
.sec-head span{font-family:'Cinzel',serif;font-size:.55rem;letter-spacing:.4em;text-transform:uppercase;color:var(--gold-dim);white-space:nowrap;}
.sec-head::before,.sec-head::after{content:"";flex:1;height:1px;}
.sec-head::before{background:linear-gradient(90deg,transparent,var(--border));}
.sec-head::after{background:linear-gradient(90deg,var(--border),transparent);}

/* MAIN LAYOUT — bodygraph left, cards right */
.main-layout{display:grid;grid-template-columns:1fr 360px 220px;gap:20px;margin-bottom:36px;align-items:start;}
.left-col{display:flex;flex-direction:column;gap:0;}
.right-col{display:flex;flex-direction:column;gap:0;}
.gifts-col{display:flex;flex-direction:column;gap:0;}
.gifts-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:14px 13px 12px;position:relative;overflow:hidden;flex:1;}
.gifts-card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold-dim),transparent);}
.gifts-card .k{font-size:.6rem;letter-spacing:.25em;text-transform:uppercase;color:var(--ink-dim);margin-bottom:7px;font-family:'Cinzel',serif;}
.gifts-card .gift-item{font-size:.78rem;font-family:'Noto Serif Georgian',serif;color:var(--ink);
  padding:4px 0;border-bottom:1px solid rgba(180,140,90,.08);line-height:1.4;}
.gifts-card .gift-item:last-child{border-bottom:none;}

/* CARDS — 2 columns in right sidebar */
.summary{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:0;grid-auto-rows:1fr;}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:14px 13px 12px;position:relative;overflow:hidden;
  transition:border-color .25s,transform .25s,box-shadow .25s;cursor:default;
  display:flex;flex-direction:column;}
.card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold-dim),transparent);transition:left .3s,right .3s;}
.card:hover{border-color:var(--border-h);transform:translateY(-2px);box-shadow:0 6px 24px rgba(0,0,0,.4),0 0 16px var(--gold-glow);}
.card:hover::before{left:5%;right:5%;}
.card.hi{border-color:rgba(196,149,80,.3);}
.card.hi::before{background:linear-gradient(90deg,transparent,var(--gold),transparent);}
.card .k{font-size:.6rem;letter-spacing:.25em;text-transform:uppercase;color:var(--ink-dim);margin-bottom:7px;font-family:'Cinzel',serif;}
.card .v{font-family:'Cormorant Garamond',serif;font-size:.88rem;font-weight:400;color:var(--ink);line-height:1.4;}
.card .v.sm{font-size:.88rem;}
.card .v.xs{font-size:.82rem;font-family:'Noto Serif Georgian',serif;line-height:1.5;}

/* CHART AREA */
.chart-area{display:grid;grid-template-columns:130px 1fr 130px;
  background:var(--surface);border:1px solid var(--border);border-radius:6px;
  padding:18px;min-height:660px;align-items:start;position:relative;overflow:hidden;}
.chart-area::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold-dim) 30%,var(--gold) 50%,var(--gold-dim) 70%,transparent);}
.planet-col{padding:6px 0px;font-family:'JetBrains Mono',monospace;font-size:.63rem;}
.planet-col h3{font-family:'Cinzel',serif;font-size:.55rem;font-weight:500;letter-spacing:.2em;
  text-transform:uppercase;margin-bottom:10px;padding-bottom:7px;border-bottom:1px solid var(--border);text-align:center;}
.planet-col.design h3{color:var(--violet-lt);}
.planet-col.personality h3{color:var(--indigo-lt);}
.prow{display:grid;grid-template-columns:16px 1fr auto;gap:3px;align-items:center;
  padding:3px 2px;border-bottom:1px solid rgba(255,255,255,.02);}
.prow:hover{background:rgba(255,255,255,.025);border-radius:2px;}
.prow .g{font-family:'Cormorant Garamond',serif;font-size:.95rem;color:var(--gold-dim);text-align:center;}
.prow .nm{color:var(--ink-dim);font-size:.58rem;}
.prow .gl{font-variant-numeric:tabular-nums;font-size:.7rem;}
.prow .gl .gate{color:var(--ink);}
.prow .gl .line{color:var(--gold-dim);}
#bodygraph{display:flex;align-items:center;justify-content:center;}
#bodygraph svg{width:100%;height:auto;max-height:660px;display:block;}

/* DETAILS */
.details{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:6px;
  padding:24px 26px;position:relative;overflow:hidden;}
.panel::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--gold-dim),transparent);}
.panel h2{font-family:'Cinzel',serif;font-size:.7rem;font-weight:500;letter-spacing:.25em;
  text-transform:uppercase;color:var(--gold);margin-bottom:16px;display:flex;align-items:center;gap:10px;}
.panel h2 small{font-size:.55rem;letter-spacing:.2em;color:var(--ink-dim);font-weight:400;}
.channel-list{display:flex;flex-direction:column;gap:5px;}
.ch-item{display:grid;grid-template-columns:64px 1fr auto;gap:8px;align-items:center;
  padding:7px 10px;background:var(--raised);border-left:2px solid var(--border);
  border-radius:0 var(--r) var(--r) 0;}
.ch-item.design{border-left-color:var(--violet);}
.ch-item.personality{border-left-color:var(--indigo-lt);}
.ch-item.mixed{border-left-color:var(--gold-dim);}
.ch-item .pair{font-family:'Cormorant Garamond',serif;font-size:.95rem;color:var(--ink);font-weight:500;}
.ch-item .cname{color:var(--ink-mid);font-style:italic;font-size:.75rem;}
.ch-item .ctag{font-size:.48rem;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-dim);font-family:'Cinzel',serif;}
.ch-item.design .ctag{color:var(--violet-lt);}
.ch-item.personality .ctag{color:var(--indigo-lt);}
.ch-item.mixed .ctag{color:var(--gold);}
.centers-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:16px;}
.center-chip{padding:7px 8px;text-align:center;background:var(--raised);border:1px solid transparent;
  border-radius:var(--r);font-size:.7rem;color:var(--ink-dim);transition:all .2s;}
.center-chip.on{color:var(--ink);border-color:rgba(196,149,80,.25);background:rgba(196,149,80,.05);}
.center-chip.on::before{content:"◆ ";color:var(--gold);font-size:.42rem;vertical-align:middle;}
.meta-info{font-size:.7rem;color:var(--ink-dim);line-height:2.1;}
.meta-info strong{color:var(--ink-mid);}
.loading{text-align:center;padding:80px 20px;color:var(--ink-dim);font-style:italic;letter-spacing:.12em;font-size:.88rem;}

@media(max-width:1300px){
  .main-layout{grid-template-columns:1fr 340px 200px;}}
@media(max-width:1100px){
  .main-layout{grid-template-columns:1fr;}
  .summary{grid-template-columns:repeat(3,1fr);}
  .chart-area{grid-template-columns:1fr;}
  .planet-col{order:2;}#bodygraph{order:1;}
  .details{grid-template-columns:1fr;}
  .page{padding:32px 20px 80px;}
}
@media(max-width:700px){
  .summary{grid-template-columns:repeat(2,1fr);}
  .form-grid{grid-template-columns:1fr 1fr;}
  .coords-row{grid-column:span 2;}
  .brand{font-size:1.6rem;}
}
</style>
</head>
<body>
<div class="page">

<header>
  <div class="brand">ადამიანის დიზაინი</div>
  <div class="brand-sub">Human Design Chart System</div>
</header>

<div class="form-shell">
  <div class="form-title">სხეულის გრაფიკის გამოთვლა</div>
  <form class="form-grid" id="birth-form">
    <div class="field">
      <label>დაბადების თარიღი</label>
      <input id="date" type="date" required value="1948-04-09">
    </div>
    <div class="field">
      <label>დაბადების დრო</label>
      <input id="time" type="text" required value="10:00" placeholder="მაგ. 14:30">
    </div>
    <div class="field">
      <label>ქალაქი</label>
      <input id="city" type="text" placeholder="თბილისი, London, Paris…" oninput="searchCity()">
      <div class="city-hint" id="city-hint"></div>
    </div>
    <div>
      <button type="submit" class="btn-calc" id="submit-btn">გამოთვლა</button>
    </div>
    <input type="hidden" id="lat">
    <input type="hidden" id="lon">
    <input type="hidden" id="tz_name" value="UTC">
    <div class="coords-row">
      <span id="coords-display"></span>
      <span id="tz-display"></span>
    </div>
  </form>
</div>

<div class="status" id="status"></div>

<section id="results" class="hidden">

  <div class="main-layout">
    <!-- LEFT: bodygraph -->
    <div class="left-col">
      <div class="sec-head"><span>სხეულის გრაფიკა</span></div>
      <div class="chart-area">
        <div class="planet-col design" id="col-design"><h3>დიზაინი</h3></div>
        <div id="bodygraph"><div class="loading">იტვირთება…</div></div>
        <div class="planet-col personality" id="col-personality"><h3>პიროვნება</h3></div>
      </div>
    </div>
    <!-- RIGHT: cards -->
    <div class="right-col">
      <div class="sec-head"><span>სულის ბარათი</span></div>
      <div class="summary" id="summary-cards"></div>
    </div>
    <!-- THIRD: other gifts -->
    <div class="gifts-col">
      <div class="sec-head"><span>სხვა ნიჭები</span></div>
      <div class="gifts-card" id="gifts-card">
        <div class="k">ყველა აქტიური კარი</div>
        <div id="gifts-list"></div>
      </div>
    </div>
  </div>

  <div class="details">
    <div class="panel">
      <h2>არხები <small id="channel-count"></small></h2>
      <div class="channel-list" id="channel-list"></div>
    </div>
    <div class="panel">
      <h2>ცენტრები</h2>
      <div class="centers-grid" id="centers-list"></div>
      <div class="meta-info" id="meta"></div>
    </div>
  </div>

</section>
</div>

<script>
const API_BASE="https://astrology-production-b165.up.railway.app";
const PLANET_ORDER=["Sun","Earth","North Node","South Node","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"];
const PLANET_GLYPH={"Sun":"☉","Earth":"⊕","Moon":"☽","North Node":"☊","South Node":"☋","Mercury":"☿","Venus":"♀","Mars":"♂","Jupiter":"♃","Saturn":"♄","Uranus":"♅","Neptune":"♆","Pluto":"♇"};
const PLANET_KA={"Sun":"მზე","Earth":"დედამიწა","Moon":"მთვარე","North Node":"ჩრდ. კვანძი","South Node":"სამხ. კვანძი","Mercury":"მერკური","Venus":"ვენერა","Mars":"მარსი","Jupiter":"იუპიტერი","Saturn":"სატურნი","Uranus":"ურანი","Neptune":"ნეპტუნი","Pluto":"პლუტონი"};
const CENTER_ORDER=["Head","Ajna","Throat","G","Heart","Solar Plexus","Spleen","Sacral","Root"];
const CENTER_KA={"Head":"გვირგვინი","Ajna":"აჯნა","Throat":"ყელი","G":"G ცენტრი","Heart":"გული","Solar Plexus":"მზის წნული","Spleen":"ელენთა","Sacral":"საკრალური","Root":"ფუძე"};
const TYPE_KA={"Manifestor":"მანიფესტორი","Generator":"გენერატორი","Manifesting Generator":"მანიფ. გენერატორი","Projector":"პროექტორი","Reflector":"რეფლექტორი"};
const STRATEGY_KA={"To Inform":"ინფორმირება","To Respond":"პასუხი","To Respond, then Inform":"პასუხი → ინფორმირება","Wait for the Invitation":"მოიცადე მოწვევას","Wait a Lunar Cycle (28 days)":"ელოდე მთვარის ციკლს"};

let gatePositions=null,svgDoc=null;
let _ct=null;

function searchCity(){
  clearTimeout(_ct);
  _ct=setTimeout(async()=>{
    const city=document.getElementById("city").value.trim();
    const hint=document.getElementById("city-hint");
    if(city.length<2){hint.textContent="";return;}
    hint.textContent="⏳ ძიება…";
    try{
      const r=await fetch(API_BASE+"/geocode",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({city})});
      const raw=await r.text();let d;
      try{d=JSON.parse(raw);}catch(e){hint.textContent="❌ Server error";return;}
      if(d.error){hint.textContent="❌ "+d.error;return;}
      document.getElementById("lat").value=d.lat;
      document.getElementById("lon").value=d.lon;
      document.getElementById("tz_name").value=d.tz_name||"UTC";
      hint.textContent="📍 "+d.display;
      document.getElementById("coords-display").textContent=d.lat.toFixed(4)+"°, "+d.lon.toFixed(4)+"°";
      document.getElementById("tz-display").textContent="🕐 "+(d.tz_name||"UTC");
    }catch(e){hint.textContent="❌ "+e.message;}
  },600);
}

async function loadBodygraph(){
  const[svgText,posJson]=await Promise.all([
    fetch(API_BASE+"/static/human_prepared.svg").then(r=>r.text()),
    fetch(API_BASE+"/static/gate_positions.json").then(r=>r.json())
  ]);
  gatePositions=posJson;
  const wrap=document.getElementById("bodygraph");
  const parser=new DOMParser();
  const svgDom=parser.parseFromString(svgText,"image/svg+xml");
  const importedSvg=document.importNode(svgDom.documentElement,true);
  wrap.innerHTML="";wrap.appendChild(importedSvg);
  svgDoc=wrap.querySelector("svg");
  if(!svgDoc)throw new Error("SVG not found");
  svgDoc.setAttribute("preserveAspectRatio","xMidYMid meet");
  svgDoc.removeAttribute("width");svgDoc.removeAttribute("height");
  svgDoc.setAttribute("viewBox","480 80 500 660");
  const ss=svgDoc.querySelector("#hd-activation");
  if(ss){
    const old=document.getElementById("hd-activation-doc");
    if(old)old.remove();
    const ds=document.createElement("style");
    ds.id="hd-activation-doc";ds.textContent=ss.textContent;
    document.head.appendChild(ds);ss.remove();
  }
  svgDoc.querySelectorAll(".detail-part").forEach(el=>el.style.setProperty("display","none","important"));
}

function clearActivations(){
  if(!svgDoc)return;
  const tr=[];
  svgDoc.classList.forEach(c=>{if(c.startsWith("active-p-")||c.startsWith("active-d-")||c.startsWith("active-b-")||c.startsWith("detail-on-")||c.startsWith("center-active-"))tr.push(c);});
  tr.forEach(c=>svgDoc.classList.remove(c));
  svgDoc.querySelectorAll(".detail-part").forEach(el=>el.style.setProperty("display","none","important"));
}

function activateGate(g,src){
  if(!src)return;
  let c=null;
  if(src.p&&src.d)c="active-b-"+g;
  else if(src.p)c="active-p-"+g;
  else if(src.d)c="active-d-"+g;
  if(c)svgDoc.classList.add(c);
}

function colorGateLines(g,src){
  if([10,20,34,57].includes(g))return;
  let c=null;
  if(src.p&&src.d)c="active-b-"+g;
  else if(src.p)c="active-p-"+g;
  else if(src.d)c="active-d-"+g;
  if(c)svgDoc.classList.add(c);
}

function render(chart){
  window._chart=chart;
  clearActivations();
  Object.entries(chart.gate_sources).forEach(([g,src])=>{
    const gi=parseInt(g,10);
    activateGate(gi,src);colorGateLines(gi,src);
  });
  chart.defined_centers.forEach(c=>svgDoc.classList.add("center-active-"+c.replace(/ /g,"")));
  if(chart.integration?.n){
    const n=chart.integration.n;
    svgDoc.classList.add("detail-on-"+n);
    const el=svgDoc.querySelector(`.detail-part[data-detail="${n}"]`);
    if(el)el.style.setProperty("display","block","important");
  }

  const cards=[
    {k:"ტიპი",           v:TYPE_KA[chart.type]||chart.type,              hi:true},
    {k:"სტრატეგია",      v:STRATEGY_KA[chart.strategy]||chart.strategy,  sm:true},
    {k:"ავტორიტეტი",     v:chart.authority||"",                          sm:true},
    {k:"პროფილი",        v:chart.profile||"",                            hi:true},
    {k:"არარეალ. 'მე'", v:chart.not_self||"",                           sm:true},
    {k:"რეალ. 'მე'",     v:chart.signature||"",                          sm:true},
    {k:"მთავარი ნიჭი",   v:chart.sun_gift||"",                           sm:true},
    {k:"განსაზღვრება",   v:chart.definition||"",                         sm:true},
    {k:"ინკარნ. ჯვარი",  v:chart.incarnation_cross||"",                  xs:true},
    {k:"საკვები",        v:chart.digestion||"",                          sm:true},
    {k:"გრძნობა",        v:chart.sense||"",                              sm:true},
    {k:"გარემო",         v:chart.environment||"",                        sm:true},
    {k:"მოტივაცია",      v:chart.motivation||"",                         sm:true},
    {k:"პერსპექტივა",    v:chart.perspective||"",                        sm:true},

  ];

  // Render gifts list in third column
  const giftsList = document.getElementById("gifts-list");
  if(giftsList){
    giftsList.innerHTML = (chart.other_gifts||[]).map(g=>
      `<div class="gift-item">${g}</div>`
    ).join("") || '<div class="gift-item" style="color:var(--ink-dim)">—</div>';
  }

  document.getElementById("summary-cards").innerHTML=cards.map(c=>
    `<div class="card${c.hi?' hi':''}">
      <div class="k">${c.k}</div>
      <div class="v${c.xs?' xs':c.sm?' sm':''}">${c.v||"—"}</div>
    </div>`
  ).join("");

  const planetRow=(a,t)=>`
    <div class="prow ${t}">
      <span class="g">${PLANET_GLYPH[a.planet]||""}</span>
      <span class="nm">${PLANET_KA[a.planet]||a.planet}</span>
      <span class="gl"><span class="gate">${a.gate}</span>.<span class="line">${a.line}</span></span>
    </div>`;
  const ordered=l=>PLANET_ORDER.map(p=>l.find(x=>x.planet===p)).filter(Boolean);
  document.getElementById("col-design").innerHTML=`<h3>დიზაინი</h3>`+ordered(chart.design).map(a=>planetRow(a,"d")).join("");
  document.getElementById("col-personality").innerHTML=`<h3>პიროვნება</h3>`+ordered(chart.personality).map(a=>planetRow(a,"p")).join("");

  const TKA={"design":"დიზაინი","personality":"პიროვნება","mixed":"შერეული"};
  document.getElementById("channel-count").textContent=`${chart.defined_channels.length} არხი`;
  document.getElementById("channel-list").innerHTML=chart.defined_channels.map(c=>
    `<div class="ch-item ${c.type}">
      <span class="pair">${c.gate_a}–${c.gate_b}</span>
      <span class="cname">${c.name}</span>
      <span class="ctag">${TKA[c.type]||c.type}</span>
    </div>`
  ).join("")||`<div style="color:var(--ink-dim);font-style:italic;font-size:.82rem">განსაზღვრული არხები არ არის</div>`;

  const defC=new Set(chart.defined_centers);
  document.getElementById("centers-list").innerHTML=CENTER_ORDER.map(c=>
    `<div class="center-chip${defC.has(c)?' on':''}">${CENTER_KA[c]||c}</div>`
  ).join("");

  const inp=chart.input;
  document.getElementById("meta").innerHTML=`
    <div><strong>დაბადება:</strong> ${inp.date} ${inp.time}</div>
    <div><strong>ადგილი:</strong> ${inp.resolved_place}</div>
    <div><strong>UTC:</strong> ${inp.utc_time}</div>
    <div><strong>დიზაინი:</strong> ${chart.design_time_utc}</div>`;

  document.getElementById("results").classList.remove("hidden");
}

document.getElementById("birth-form").addEventListener("submit",async ev=>{
  ev.preventDefault();
  const btn=document.getElementById("submit-btn");
  const stat=document.getElementById("status");
  const lat=document.getElementById("lat").value;
  const lon=document.getElementById("lon").value;
  const tz_name=document.getElementById("tz_name").value;
  const city=document.getElementById("city").value.trim();
  if(!lat||!lon){stat.className="status error";stat.textContent="⚠ პირველ შეიყვანეთ ქალაქი";return;}
  stat.className="status";stat.textContent="იტვირთება…";btn.disabled=true;
  try{
    if(!svgDoc)await loadBodygraph();
    const r=await fetch(API_BASE+"/api/hd_chart",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({date:document.getElementById("date").value,time:document.getElementById("time").value,lat:parseFloat(lat),lon:parseFloat(lon),tz_name,place:city})
    });
    const raw=await r.text();let chart;
    try{chart=JSON.parse(raw);}catch(_){throw new Error("Backend returned HTTP "+r.status);}
    if(!r.ok)throw new Error(chart.error||"HTTP "+r.status);
    render(chart);stat.textContent="";
  }catch(e){stat.className="status error";stat.textContent="შეცდომა: "+e.message;}
  finally{btn.disabled=false;}
});

loadBodygraph().catch(e=>{
  document.getElementById("bodygraph").innerHTML=`<div class="loading" style="color:#e06060">ვერ ჩაიტვირთა: ${e.message}</div>`;
});
</script>
</body>
</html>
