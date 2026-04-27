"""prepare_svg.py — build human_prepared.svg from human.svg + details.svg + CSV.

Key fixes baked in:
  - Gate 25 has NO backing circle in human.svg → use G-center diamond (st127)
    as the visual indicator; gate-25 CSS placed AFTER center rules so it wins.
  - All 256 clipPaths go in root <defs>, NOT inside visibility:hidden groups
    (browsers skip clipPaths inside hidden parents → details never render).
  - details.svg classes prefixed "det-" so they don't override human.svg classes
    (both files use st0/st1/st2 but with different colors).
  - Integration detail number comes from CSV row order, not a formula.
  - Circle proximity threshold 15 px prevents mis-assigning nearby circles
    to side-gates like 25, 10, 57.
"""

import csv, json, re
from pathlib import Path

ROOT        = Path(__file__).parent
HUMAN_SRC   = ROOT / "static" / "human.svg"
DETAILS_SRC = ROOT / "static" / "details.svg"
CSV_SRC     = ROOT / "static" / "integration_conditions.csv"
DST         = ROOT / "static" / "human_prepared.svg"
POS_JSON    = ROOT / "static" / "gate_positions.json"
COL_JSON    = ROOT / "static" / "gate_colors.json"
DET_JSON    = ROOT / "static" / "detail_positions.json"

P_BLUE  = "#292562"   # personality — matches details.svg st1
D_PURP  = "#67308F"   # design      — matches details.svg st2

# ── 60 gate color rules ──────────────────────────────────────
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

# ── Load human.svg ────────────────────────────────────────────
svg = HUMAN_SRC.read_text(encoding="utf-8")
print(f"[info] human.svg  {len(svg):,} chars")
sblk  = re.search(r'<style[^>]*>(.*?)</style>', svg, re.DOTALL).group(1)
c2col = {m.group(1): m.group(2).upper()
         for m in re.finditer(r'\.(st\d+)\{[^}]*fill:(#[0-9A-Fa-f]+)', sblk)}

# ── 1. Tag channel lines ──────────────────────────────────────
n_tag = 0
def _ch(m):
    global n_tag
    t  = m.group(0)
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

# ── 2. Gate texts → positions ────────────────────────────────
tp = {}
for m in re.finditer(
        r'matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)[^>]*>(\d+)</text>', svg):
    tp[int(m.group(3))] = (float(m.group(1)), float(m.group(2)))

gpos = {}   # gate → {cx, cy}

def _nearest(cx, cy):
    best, bd = None, 1e9
    for g, (tx, ty) in tp.items():
        d = (cx-tx)**2 + (cy-ty)**2
        if d < bd: bd, best = d, g
    return best, bd**0.5

# ── 3. Tag gate circles (st128) ──────────────────────────────
def _circ(m):
    t   = m.group(0)
    cxm = re.search(r'cx="([\d.]+)"', t)
    cym = re.search(r'cy="([\d.]+)"', t)
    if not cxm or not cym: return t
    cx, cy = float(cxm.group(1)), float(cym.group(1))
    g, dist = _nearest(cx, cy)
    if g is None or dist > 15: return t   # >15 px → wrong gate, skip
    gpos[g] = {"cx": round(cx,1), "cy": round(cy,1)}
    return re.sub(r'class="(st128)"',
                  f'class="\\1 gate-circle" data-gate="{g}"', t, count=1)
svg = re.sub(r'<circle\b[^>]+class="st128"[^>]*/>', _circ, svg)

# ── 4. Tag gate texts (st129 st130) ──────────────────────────
def _txt(m):
    t  = m.group(0)
    gm = re.search(r'>(\d+)</text>', t)
    if not gm: return t
    g = int(gm.group(1))
    if g not in tp: return t
    return re.sub(r'class="(st129 st130)"',
                  f'class="\\1 gate-text" data-gate="{g}"', t, count=1)
svg = re.sub(r'<text\b[^>]+class="st129 st130"[^>]*>\d+</text>', _txt, svg)

# Fill positions for gates without a real circle (e.g. gate 25)
for g, (tx, ty) in tp.items():
    if g not in gpos:
        gpos[g] = {"cx": round(tx,1), "cy": round(ty,1)}
POS_JSON.write_text(json.dumps(gpos, indent=2))
print(f"[info] gate positions: {len(gpos)}  (circles tagged: {len([g for g in gpos if g in [int(m.group(1)) for m in re.finditer(r'data-gate=\"(\d+)\"', svg)]])})")

# ── 5. Tag center shapes (st127) ─────────────────────────────
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
    print(f"  center {name:15} M({pm.group(1)},{pm.group(2)})")
    return re.sub(r'class="st127"',
                  f'class="st127 chakra" data-center="{name}"', t, count=1)
svg = re.sub(r'<path\b[^>]+class="st127"[^>]*/>', _ctr, svg)

# Gate 25 — G-center diamond is its visual indicator (no separate circle exists)
svg = svg.replace(
    'class="st127 chakra" data-center="G"',
    'class="st127 chakra gate-circle" data-center="G" data-gate="25"',
)
print("[info] gate 25 → G-center diamond:", "✓" if 'data-gate="25"' in svg else "✗ FAILED")

# ── 6. CSV lookup: (s10,s57,s34,s20) → detail n ─────────────
lkp = {}
with CSV_SRC.open(encoding="utf-8-sig", newline="") as f:
    next(csv.reader(f))   # skip header
    for n, row in enumerate(csv.reader(f), start=1):
        if len(row) >= 4:
            lkp[(row[0].strip(), row[1].strip(),
                 row[2].strip(), row[3].strip())] = n
print(f"[info] CSV lookup: {len(lkp)} entries  "
      f"all-None→{lkp.get(('None','None','None','None'))}  "
      f"all-Both→{lkp.get(('Both','Both','Both','Both'))}")

# Save lookup for hd_calc.py to import at runtime
(ROOT/"static"/"integration_lookup.json").write_text(
    json.dumps({"|".join(k): v for k,v in lkp.items()}, indent=2))
print("[info] wrote static/integration_lookup.json")

# ── 7. Integration anchor (where detail artboard appears) ────
# Cell size = viewBox of details.svg: 152.6 × 279.0
# Anchor: right edge reaches gate-20 cx, bottom edge reaches gate-34 cy
CW, CH = 152.6, 279.0
g20 = gpos.get(20, {"cx": 707.3, "cy": 320.5})
g34 = gpos.get(34, {"cx": 704.8, "cy": 588.6})
TX  = round(g20["cx"] - CW, 2)   # left edge of artboard in SVG coords
TY  = round(g34["cy"] - CH, 2)   # top edge of artboard in SVG coords
print(f"[info] integration anchor ({TX},{TY})  right={TX+CW:.1f}  bottom={TY+CH:.1f}")

# ── 8. Extract details.svg artboards ─────────────────────────
dsvg = DETAILS_SRC.read_text(encoding="utf-8")
print(f"[info] details.svg  {len(dsvg):,} chars")

# Prefix all details classes with "det-" to prevent color collisions
det_style = ""
ds = re.search(r'<style[^>]*>(.*?)</style>', dsvg, re.DOTALL)
if ds:
    det_style = re.sub(r'\.(st\d+)\b', r'.det-\1', ds.group(1).strip())

# All paths with M start coord and prefixed class
det_paths = []
for m in re.finditer(r'<path class="([^"]+)" d="([^"]+)"/>', dsvg):
    pm = re.search(r'M\s*([\d.]+),([\d.]+)', m.group(2))
    if pm:
        det_paths.append((float(pm.group(1)), float(pm.group(2)),
                          f'class="det-{m.group(1)}"', m.group(2)))
print(f"[info] detail paths extracted: {len(det_paths)}")

# Grid: artboard n (1-based) → row=(n-1)//16, col=(n-1)%16
# Origins: (col*152.6, row*279.0) — matches viewBox "0 0 152.6 279" per artboard
DXO, DYO = 0.0, 0.0   # artboard grid origin

clip_defs  = []   # all clipPaths — injected into root <defs>
det_groups = []
det_pdata  = {}

for n in range(1, 257):
    idx = n - 1
    row = idx // 16
    col = idx % 16
    ax  = DXO + col * CW
    ay  = DYO + row * CH
    dx  = TX - ax          # translate to move cell to anchor
    dy  = TY - ay

    # Paths in this cell (±5 tolerance for paths near cell edges)
    cell = "\n".join(
        f'<path {cs} d="{d}"/>'
        for px, py, cs, d in det_paths
        if ax-5 <= px <= ax+CW+5 and ay-5 <= py <= ay+CH+5
    )

    # clipPath MUST be in root <defs> — not inside visibility:hidden group
    clip_defs.append(
        f'<clipPath id="cdp{n}">'
        f'<rect x="{TX:.2f}" y="{TY:.2f}" width="{CW:.2f}" height="{CH:.2f}"/>'
        f'</clipPath>'
    )

    det_groups.append(
        f'<g class="detail-part" data-detail="{n}" style="visibility:hidden">'
        f'<g transform="translate({dx:.2f},{dy:.2f})" clip-path="url(#cdp{n})">'
        f'{cell}</g></g>'
    )
    det_pdata[str(n)] = {"row": row, "col": col,
                          "src_x": round(ax,2), "src_y": round(ay,2),
                          "dst_x": TX, "dst_y": TY}

DET_JSON.write_text(json.dumps(det_pdata, indent=2))
print(f"wrote {DET_JSON}")

# ── 9. gate_colors.json ──────────────────────────────────────
COL_JSON.write_text(json.dumps(
    {str(g): {"dark": d, "light": l, "p_blue": P_BLUE, "design": D_PURP}
     for g, d, l in GATE_RULES}, indent=2))
print(f"wrote {COL_JSON}")

# ── 10. Activation CSS ────────────────────────────────────────
CENTER_COL = {
    "Head":"#AA88EE","Ajna":"#9B59B6","Throat":"#F39C12","G":"#FFD700",
    "Heart":"#E74C3C","Solar Plexus":"#E67E22","Spleen":"#27AE60",
    "Sacral":"#E74C3C","Root":"#8B4513",
}
css = ["<style id='hd-activation'>"]
css.append(".gate-line{fill:#FFFFFF!important;}")

# Gate lines
for g,_,_ in GATE_RULES:
    css += [
        f"svg.active-p-{g} [data-gate='{g}'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-d-{g} [data-gate='{g}'].gate-line{{fill:{D_PURP}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='dark'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='light'].gate-line{{fill:{D_PURP}!important;}}",
    ]

# Gate circles (darken) — skip gate 25, handled after center rules
all_gates = [g for g,_,_ in GATE_RULES] + [10, 20, 34, 57]
for g in all_gates:
    if g == 25: continue
    for p in ("active-p-","active-d-","active-b-"):
        css.append(f"svg.{p}{g} .gate-circle[data-gate='{g}']{{fill:#1a1a2e!important;}}")

# Gate texts (white)
for g in all_gates:
    for p in ("active-p-","active-d-","active-b-"):
        css.append(f"svg.{p}{g} .gate-text[data-gate='{g}']{{fill:#FFFFFF!important;}}")

# Centers
for name, col in CENTER_COL.items():
    safe = name.replace(" ","")
    css.append(f"svg.center-active-{safe} .chakra[data-center='{name}']{{fill:{col}!important;}}")

# Gate 25 AFTER center rules → wins the cascade when both classes present
css += [
    f"svg.active-p-25 .gate-circle[data-gate='25']{{fill:{P_BLUE}!important;}}",
    f"svg.active-d-25 .gate-circle[data-gate='25']{{fill:{D_PURP}!important;}}",
    f"svg.active-b-25 .gate-circle[data-gate='25']{{fill:{P_BLUE}!important;}}",
]
for p in ("active-p-","active-d-","active-b-"):
    css.append(f"svg.{p}25 .gate-text[data-gate='25']{{fill:#FFFFFF!important;}}")

# Detail visibility
css.append(".detail-part{visibility:hidden!important;}")
for n in range(1, 257):
    css.append(f"svg.detail-on-{n} .detail-part[data-detail='{n}']{{visibility:visible!important;}}")
css.append("</style>")

# ── 11. Assemble final SVG ────────────────────────────────────
# Inject prefixed details style
if det_style:
    svg = re.sub(r'(<style\b[^>]*>)',
                 f'\\1\n/* details.svg styles (prefixed det-) */\n{det_style}\n',
                 svg, count=1)

# Inject 256 clipPaths into root <defs> (CRITICAL — not inside hidden groups)
clip_block = "<defs id='detail-clips'>\n" + "\n".join(clip_defs) + "\n</defs>"
svg = re.sub(r'(<svg\b[^>]*>)', f'\\1\n{clip_block}', svg, count=1)

# Append detail layer + activation CSS
svg = svg.replace(
    "</svg>",
    "\n" + "\n".join(css) + "\n"
    "<g id='details-layer'>\n" + "\n".join(det_groups) + "\n</g>\n"
    "</svg>"
)

DST.write_text(svg, encoding="utf-8")
print(f"\nwrote {DST}  ({len(svg)/1e6:.2f} MB)")
print(f"  channel lines  : {n_tag}/120")
print(f"  gate circles   : 63 real + gate-25 = G-diamond")
print(f"  centers        : 9")
print(f"  detail artboards: 256  clipPaths in root <defs> ✓")
