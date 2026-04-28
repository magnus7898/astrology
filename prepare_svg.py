"""prepare_svg.py — build human_prepared.svg.

Key behaviours
──────────────
• st19 (#454545) — the integration silhouette "e-shape" — is HIDDEN.
  Its place is taken by the correct detail artboard from detail.svg,
  chosen by the CSV lookup (gates 10/57/34/20 states → row number).
• 256 clipPaths are in root <defs> (not inside visibility:hidden groups).
• detail.svg classes prefixed "det-" to prevent colour collisions.
• Gate 25 uses the G-centre diamond as its visual indicator.
  Gate-25 CSS comes AFTER centre rules to win the cascade.
• Circle proximity threshold 15 px prevents mis-assigning circles to
  side-gates like 25, 10, 57.
"""

import csv, json, re
from pathlib import Path

ROOT        = Path(__file__).parent
HUMAN_SRC   = ROOT / "static" / "human.svg"
DETAILS_SRC = ROOT / "static" / "detail.svg"          # ← updated filename
CSV_SRC     = ROOT / "static" / "integration_conditions.csv"
DST         = ROOT / "static" / "human_prepared.svg"
POS_JSON    = ROOT / "static" / "gate_positions.json"
COL_JSON    = ROOT / "static" / "gate_colors.json"
DET_JSON    = ROOT / "static" / "detail_positions.json"

P_BLUE = "#292562"   # personality  (= detail.svg st1)
D_PURP = "#67308F"   # design       (= detail.svg st2)

# ── 60 gate colour rules ─────────────────────────────────────
GATE_RULES = [
    (36,"#FF0000","#FF3333"),(35,"#E60000","#FF4D4D"),(22,"#CC0000","#FF6666"),
    (12,"#B30000","#FF8080"),(37,"#990000","#FF9999"),(40,"#FF8000","#FF9933"),
    (21,"#E67300","#FFA34D"),(45,"#CC6600","#FFAD66"),(51,"#B35900","#FFB880"),
    (25,"#994D00","#FFC299"),( 6,"#FFFF00","#FFFF33"),(59,"#E6E600","#FFFF4D"),
    (27,"#CCCC00","#FFFF66"),(50,"#B3B300","#FFFF80"),(26,"#999900","#FFFF99"),
    (44,"#00FF00","#33FF33"),(48,"#00E600","#4DFF4D"),(16,"#00CC00","#66FF66"),
    (30,"#00B300","#80FF80"),(41,"#009900","#99FF99"),(55,"#00FFFF","#33FFFF"),
    (39,"#00E6E6","#4DFFFF"),(49,"#00CCCC","#66FFFF"),(19,"#00B3B3","#80FFFF"),
    (58,"#009999","#99FFFF"),(18,"#0000FF","#3333FF"),(38,"#0000E6","#4D4DFF"),
    (28,"#0000CC","#6666FF"),(54,"#0000B3","#8080FF"),(32,"#000099","#9999FF"),
    (52,"#800080","#9933FF"),( 9,"#730073","#A34DFF"),(60,"#660066","#AD66FF"),
    ( 3,"#590059","#B880FF"),(53,"#4D004D","#C299FF"),(42,"#FF00FF","#FF33FF"),
    (29,"#E600E6","#FF4DFF"),(14,"#CC00CC","#FF66FF"),( 5,"#B300B3","#FF80FF"),
    (46,"#990099","#FF99FF"),( 2,"#8B4513","#A0522D"),(15,"#7A3C12","#B05A2F"),
    (13,"#693310","#C06231"),( 1,"#582A0E","#D06A33"),( 7,"#47210C","#E07235"),
    (33,"#808080","#999999"),( 8,"#737373","#A6A6A6"),(31,"#666666","#B3B3B3"),
    (56,"#595959","#BFBFBF"),(23,"#4D4D4D","#CCCCCC"),(62,"#FAD0C4","#C1E1C1"),
    (11,"#F8C8DC","#B39EB5"),(43,"#F3E5AB","#AED9E0"),(17,"#E6E6FA","#98D8C8"),
    ( 4,"#D4F1F4","#88C5B9"),(63,"#2C3E50","#F1C40F"),(24,"#34495E","#F39C12"),
    (61,"#2980B9","#E67E22"),(64,"#1ABC9C","#D35400"),(47,"#16A085","#E74C3C"),
]
C2G = {}
for g, d, l in GATE_RULES:
    C2G[d.upper()] = (g, "dark")
    C2G[l.upper()] = (g, "light")

# ── Load human.svg ───────────────────────────────────────────
svg  = HUMAN_SRC.read_text(encoding="utf-8")
sblk = re.search(r'<style[^>]*>(.*?)</style>', svg, re.DOTALL).group(1)
c2col= {m.group(1): m.group(2).upper()
        for m in re.finditer(r'\.(st\d+)\s*\{[^}]*fill:\s*(#[0-9A-Fa-f]+)', sblk)}
print(f"[info] human.svg  {len(svg):,} chars  classes:{len(c2col)}")

svg = re.sub(r'(<path[^>]+class="st19")', r'\1 style="display:none"', svg)
print('[info] st19 (#454545) hidden — replaced by detail artboard')

# ── 1. Tag channel lines ─────────────────────────────────────
n_tag = 0
def _ch(m):
    global n_tag
    t = m.group(0)
    cm = re.search(r'class="(st\d+)"', t)
    if not cm: return t
    col = c2col.get(cm.group(1), "")
    if col not in C2G: return t
    g, tp = C2G[col]; n_tag += 1
    return re.sub(r'class="(st\d+)"',
                  f'class="\\1 gate-line" data-gate="{g}" data-type="{tp}"',
                  t, count=1)
svg = re.sub(r'<(?:rect|path|line)\b[^>]*/>', _ch, svg)
print(f"[info] channel lines tagged: {n_tag}/120")

# ── 2. Gate text positions ───────────────────────────────────
tpos = {}
for m in re.finditer(
        r'matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)[^>]*>(\d+)</text>', svg):
    tpos[int(m.group(3))] = (float(m.group(1)), float(m.group(2)))

gpos = {}   # gate → {cx, cy}

def _nearest(cx, cy):
    best, bd = None, 1e9
    for g, (tx, ty) in tpos.items():
        d = (cx-tx)**2+(cy-ty)**2
        if d < bd: bd, best = d, g
    return best, bd**0.5

# ── 3. Tag gate circles (st128) ──────────────────────────────
def _circ(m):
    t = m.group(0)
    cxm = re.search(r'cx="([\d.]+)"', t)
    cym = re.search(r'cy="([\d.]+)"', t)
    if not cxm or not cym: return t
    cx, cy = float(cxm.group(1)), float(cym.group(1))
    g, dist = _nearest(cx, cy)
    if g is None or dist > 15: return t
    gpos[g] = {"cx": round(cx,1), "cy": round(cy,1)}
    return re.sub(r'class="(st127)"',
                  f'class="\\1 gate-circle" data-gate="{g}"', t, count=1)
svg = re.sub(r'<circle\b[^>]+class="st127"[^>]*/>', _circ, svg)

# ── 4. Tag gate texts (st129 st130) ──────────────────────────
def _txt(m):
    t  = m.group(0)
    gm = re.search(r'>(\d+)</text>', t)
    if not gm: return t
    g = int(gm.group(1))
    if g not in tpos: return t
    return re.sub(r'class="(st128 st129)"',
                  f'class="\\1 gate-text" data-gate="{g}"', t, count=1)
svg = re.sub(r'<text\b[^>]+class="st128 st129"[^>]*>\d+</text>', _txt, svg)

for g, (tx, ty) in tpos.items():
    if g not in gpos:
        gpos[g] = {"cx": round(tx,1), "cy": round(ty,1)}
POS_JSON.write_text(json.dumps(gpos, indent=2))
print(f"[info] gate positions saved  ({len(gpos)} gates)")

# ── 5. Tag centre shapes (st127) ────────────────────────────
def _cname(sx, sy):
    if sy < 220: return "Head"
    if sy < 310: return "Ajna"
    if sy < 390: return "Throat"
    if sy < 480: return "G"
    if sy < 540: return "Heart"
    if sy < 700:
        return "Spleen" if sx < 600 else ("Solar Plexus" if sx > 900 else "Sacral")
    return "Root"

def _ctr(m):
    t  = m.group(0)
    dm = re.search(r'd="([^"]+)"', t)
    if not dm: return t
    pm = re.search(r'M\s*([\d.]+),([\d.]+)', dm.group(1))
    if not pm: return t
    name = _cname(float(pm.group(1)), float(pm.group(2)))
    print(f"  centre {name:15} M({pm.group(1)},{pm.group(2)})")
    return re.sub(r'class="st126"',
                  f'class="st126 chakra" data-center="{name}"', t, count=1)
svg = re.sub(r'<path\b[^>]+class="st126"[^>]*/>', _ctr, svg)

print("[info] gate 25 circle: using real st127 circle (not G-diamond)")

# ── 6. CSV lookup ─────────────────────────────────────────────
lkp = {}
with CSV_SRC.open(encoding="utf-8-sig", newline="") as f:
    rdr = csv.reader(f)
    next(rdr)    # skip header
    for n, row in enumerate(rdr, start=1):
        if len(row) >= 4:
            lkp[(row[0].strip(), row[1].strip(),
                 row[2].strip(), row[3].strip())] = n
print(f"[info] CSV: {len(lkp)} entries  "
      f"all-None→{lkp.get(('None','None','None','None'))}  "
      f"all-Both→{lkp.get(('Both','Both','Both','Both'))}")

# ── 7. Integration artboard anchor ───────────────────────────
# Target area = bounding box of the hidden st19 shape in the bodygraph
CW, CH = 152.6, 279.0        # target width/height (bodygraph shape)
TX     = 553.3               # exact left edge of st19
TY     = 311.0               # exact top  edge of st19
print(f"[info] artboard target ({TX},{TY})  "
      f"right={TX+CW:.1f}  bottom={TY+CH:.1f}")

# ── 8. Load detail.svg ────────────────────────────────────────
dsvg = DETAILS_SRC.read_text(encoding="utf-8")
print(f"[info] detail.svg  {len(dsvg):,} chars")

ds = re.search(r'<style[^>]*>(.*?)</style>', dsvg, re.DOTALL)
det_style = re.sub(r'\.(st\d+)\b', r'.det-\1', ds.group(1).strip()) if ds else ""

# Source grid dimensions (new detail.svg: 16×16 artboards over 2974.7×5121.9)
CW_SRC = 2974.7 / 16   # 185.9187
CH_SRC = 5121.9 / 16   # 320.1187

# Scale factors: stretch each artboard to fill the target area exactly
SX = CW / CW_SRC        # ≈ 0.8208
SY = CH / CH_SRC        # ≈ 0.8716

# Extract all path + polygon elements, prefixing class names with "det-"
det_elems = []
for tag in re.findall(r'<path[^>]+/>|<polygon[^>]+/>', dsvg):
    m = re.search(r'd="M\s*([\d.]+),([\d.]+)', tag) or \
        re.search(r'points="([\d.]+),([\d.]+)', tag)
    if not m:
        continue
    x, y = float(m.group(1)), float(m.group(2))
    tag_prefixed = re.sub(r'class="(st\d+)"', r'class="det-\1"', tag)
    det_elems.append((x, y, tag_prefixed))

print(f"[info] detail elements: {len(det_elems)}  "
      f"(src cell {CW_SRC:.2f}×{CH_SRC:.2f}  scale {SX:.4f}×{SY:.4f})")

clip_defs  = []
det_groups = []
det_pdata  = {}

for n in range(1, 257):
    idx = n - 1
    row = idx // 16
    col = idx % 16
    ax  = col * CW_SRC
    ay  = row * CH_SRC

    # Collect elements that belong to this artboard cell
    cell = "\n".join(
        tag for px, py, tag in det_elems
        if ax - 5 <= px <= ax + CW_SRC + 5 and ay - 5 <= py <= ay + CH_SRC + 5
    )

    # Transform: shift artboard to origin → scale → place at target
    transform = (f"translate({TX:.2f},{TY:.2f}) "
                 f"scale({SX:.6f},{SY:.6f}) "
                 f"translate({-ax:.2f},{-ay:.2f})")

    clip_defs.append(
        f'<clipPath id="cdp{n}">'
        f'<rect x="{TX:.2f}" y="{TY:.2f}" width="{CW:.2f}" height="{CH:.2f}"/>'
        f'</clipPath>'
    )
    det_groups.append(
        f'<g class="detail-part" data-detail="{n}" style="display:none">'
        f'<g clip-path="url(#cdp{n})">'
        f'<rect x="{TX:.2f}" y="{TY:.2f}" width="{CW:.2f}" height="{CH:.2f}" fill="#454545"/>'
        f'<g transform="{transform}">'
        f'{cell}</g></g></g>'
    )
    det_pdata[str(n)] = {
        "row": row, "col": col,
        "src_x": round(ax, 2), "src_y": round(ay, 2),
        "dst_x": TX, "dst_y": TY,
        "scale_x": round(SX, 6), "scale_y": round(SY, 6),
    }

DET_JSON.write_text(json.dumps(det_pdata, indent=2))

# ── gate_colors.json ─────────────────────────────────────────
COL_JSON.write_text(json.dumps(
    {str(g):{"dark":d,"light":l,"p_blue":P_BLUE,"design":D_PURP}
     for g,d,l in GATE_RULES}, indent=2))

# ── 9. Activation CSS ─────────────────────────────────────────
CCOL = {"Head":"#AA88EE","Ajna":"#9B59B6","Throat":"#F39C12","G":"#FFD700",
        "Heart":"#E74C3C","Solar Plexus":"#E67E22","Spleen":"#27AE60",
        "Sacral":"#E74C3C","Root":"#8B4513"}

css = ["<style id='hd-activation'>",
       ".gate-line{fill:#FFFFFF!important;}"]

for g,_,_ in GATE_RULES:
    css += [
        f"svg.active-p-{g} [data-gate='{g}'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-d-{g} [data-gate='{g}'].gate-line{{fill:{D_PURP}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='dark'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='light'].gate-line{{fill:{D_PURP}!important;}}",
    ]

for g in [g for g,_,_ in GATE_RULES]+[10,20,34,57]:
    for p in ("active-p-","active-d-","active-b-"):
        css.append(f"svg.{p}{g} .gate-circle[data-gate='{g}']{{fill:#1a1a2e!important;}}")

for g in [g for g,_,_ in GATE_RULES]+[10,20,34,57]:
    for p in ("active-p-","active-d-","active-b-"):
        css.append(f"svg.{p}{g} .gate-text[data-gate='{g}']{{fill:#FFFFFF!important;}}")

for name,col in CCOL.items():
    safe=name.replace(" ","")
    css.append(f"svg.center-active-{safe} .chakra[data-center='{name}']{{fill:{col}!important;}}")

css.append(".detail-part{display:none!important;}")
for n in range(1,257):
    css.append(f"svg.detail-on-{n} .detail-part[data-detail='{n}']{{display:block!important;}}")
css.append("</style>")

# ── 10. Assemble ──────────────────────────────────────────────
if det_style:
    svg = re.sub(r'(<style\b[^>]*>)',
                 f'\\1\n/* detail.svg styles (prefixed det-) */\n{det_style}\n',
                 svg, count=1)

clip_block = "<defs id='detail-clips'>\n"+"\n".join(clip_defs)+"\n</defs>"
svg = re.sub(r'(<svg\b[^>]*>)', f'\\1\n{clip_block}', svg, count=1)

svg = svg.replace(
    "</svg>",
    "\n"+"\n".join(css)+"\n"
    "<g id='details-layer'>\n"+"\n".join(det_groups)+"\n</g>\n"
    "</svg>"
)

DST.write_text(svg, encoding="utf-8")
mb = len(svg)/1e6
print(f"\nwrote {DST}  ({mb:.2f} MB)")
print(f"  channel lines  : {n_tag}/120")
print(f"  clipPaths in root <defs>: ✓")
print(f"  st19 (#454545) hidden: ✓")
