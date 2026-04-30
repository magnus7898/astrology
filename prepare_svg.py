"""prepare_svg.py — build human_prepared.svg."""
import csv, json, re
from pathlib import Path

ROOT        = Path(__file__).parent
HUMAN_SRC   = ROOT / "static" / "human.svg"
DETAILS_SRC = ROOT / "static" / "detail.svg"
DST         = ROOT / "static" / "human_prepared.svg"
POS_JSON    = ROOT / "static" / "gate_positions.json"
COL_JSON    = ROOT / "static" / "gate_colors.json"
DET_JSON    = ROOT / "static" / "detail_positions.json"

P_BLUE = "#292562"
D_PURP = "#67308F"

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
    C2G[d.upper()] = (g, "dark"); C2G[l.upper()] = (g, "light")

# ── Load human.svg ────────────────────────────────────────────
svg  = HUMAN_SRC.read_text(encoding="utf-8")
sblk = re.search(r'<style[^>]*>(.*?)</style>', svg, re.DOTALL).group(1)
c2col= {m.group(1): m.group(2).upper()
        for m in re.finditer(r'\.(st\d+)\s*\{[^}]*fill:\s*(#[0-9A-Fa-f]+)', sblk)}
print(f"[info] human.svg {len(svg):,} chars  classes:{len(c2col)}")
svg = re.sub(r'(<path[^>]+class="st19")', r'\1 style="display:none"', svg)
print('[info] st19 hidden')

# ── 1. Tag channel lines ──────────────────────────────────────
n_tag = 0
def _ch(m):
    global n_tag
    t = m.group(0); cm = re.search(r'class="(st\d+)"', t)
    if not cm: return t
    col = c2col.get(cm.group(1), "")
    if col not in C2G: return t
    g, tp = C2G[col]; n_tag += 1
    return re.sub(r'class="(st\d+)"', f'class="\\1 gate-line" data-gate="{g}" data-type="{tp}"', t, count=1)
svg = re.sub(r'<(?:rect|path|line)\b[^>]*/>', _ch, svg)
print(f"[info] channel lines tagged: {n_tag}/120")

# ── 2. Gate text positions ────────────────────────────────────
tpos = {}
for m in re.finditer(r'matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)[^>]*>(\d+)</text>', svg):
    tpos[int(m.group(3))] = (float(m.group(1)), float(m.group(2)))

gpos = {}
def _nearest(cx, cy):
    best, bd = None, 1e9
    for g, (tx, ty) in tpos.items():
        d = (cx-tx)**2+(cy-ty)**2
        if d < bd: bd, best = d, g
    return best, bd**0.5

# ── 3. Tag gate circles ───────────────────────────────────────
def _circ(m):
    t = m.group(0)
    cxm = re.search(r'cx="([\d.]+)"', t); cym = re.search(r'cy="([\d.]+)"', t)
    if not cxm or not cym: return t
    cx, cy = float(cxm.group(1)), float(cym.group(1))
    g, dist = _nearest(cx, cy)
    if g is None or dist > 15: return t
    gpos[g] = {"cx": round(cx,1), "cy": round(cy,1)}
    return re.sub(r'class="(st127)"', f'class="\\1 gate-circle" data-gate="{g}"', t, count=1)
svg = re.sub(r'<circle\b[^>]+class="st127"[^>]*/>', _circ, svg)

# ── 4. Tag gate texts ─────────────────────────────────────────
def _txt(m):
    t = m.group(0); gm = re.search(r'>(\d+)</text>', t)
    if not gm: return t
    g = int(gm.group(1))
    if g not in tpos: return t
    return re.sub(r'class="(st128 st129)"', f'class="\\1 gate-text" data-gate="{g}"', t, count=1)
svg = re.sub(r'<text\b[^>]+class="st128 st129"[^>]*>\d+</text>', _txt, svg)
for g, (tx, ty) in tpos.items():
    if g not in gpos: gpos[g] = {"cx": round(tx,1), "cy": round(ty,1)}
POS_JSON.write_text(json.dumps(gpos, indent=2))
print(f"[info] gate positions saved ({len(gpos)} gates)")

# ── 5. Tag centre shapes ──────────────────────────────────────
def _cname(sx, sy):
    if sy < 220: return "Head"
    if sy < 310: return "Ajna"
    if sy < 390: return "Throat"
    if sy < 480: return "G"
    if sy < 540: return "Heart"
    if sy < 700: return "Spleen" if sx < 600 else ("Solar Plexus" if sx > 900 else "Sacral")
    return "Root"

def _ctr(m):
    t = m.group(0); dm = re.search(r'd="([^"]+)"', t)
    if not dm: return t
    pm = re.search(r'M\s*([\d.]+),([\d.]+)', dm.group(1))
    if not pm: return t
    name = _cname(float(pm.group(1)), float(pm.group(2)))
    return re.sub(r'class="st126"', f'class="st126 chakra" data-center="{name}"', t, count=1)
svg = re.sub(r'<path\b[^>]+class="st126"[^>]*/>', _ctr, svg)

# ── 6. st19 bounding box ──────────────────────────────────────
TX, TY, CW, CH = 553.40, 311.40, 152.70, 279.40
print(f"[info] st19 bbox: ({TX},{TY}) {CW}x{CH}")

# ── 7. Load detail.svg ────────────────────────────────────────
dsvg = DETAILS_SRC.read_text(encoding="utf-8")
print(f"[info] detail.svg {len(dsvg):,} chars")

CW_SRC = 2974.7 / 16   # 185.9187 — cell width in detail.svg coords
CH_SRC = 5121.9 / 16   # 320.1187 — cell height in detail.svg coords
CW_DISP, CH_DISP = 152.5, 278.9  # display size per cell (from viewBox)
sx = CW / CW_DISP   # ≈ 1.001 — scale to fit st19 target
sy = CH / CH_DISP   # ≈ 1.002

DET_COLORS = {'st0':'#FFFFFF','st1':'#292561','st2':'#67328F','st3':'#C3996C','st4':'#020202'}
det_elems = []
for tag in re.findall(r'<path[^>]+/>|<polygon[^>]+/>', dsvg):
    m = re.search(r'd="M\s*([\d.]+),([\d.]+)', tag) or \
        re.search(r'points="([\d.]+),([\d.]+)', tag)
    if not m: continue
    x, y = float(m.group(1)), float(m.group(2))
    cls_m = re.search(r'class="(st\d+)"', tag)
    color = DET_COLORS.get(cls_m.group(1) if cls_m else '', '#000000')
    tag = re.sub(r'class="st\d+"', f'style="fill:{color}"', tag)
    det_elems.append((x, y, tag))
print(f"[info] detail elements: {len(det_elems)}")

# ── 8. Build 256 detail groups ────────────────────────────────
det_groups = []
det_pdata  = {}

for n in range(1, 257):
    idx = n - 1
    row = idx // 16
    col = idx % 16
    ax = col * CW_SRC
    ay = row * CH_SRC

    cell_tags_list = [
        (px, py, tag) for px, py, tag in det_elems
        if ax - 5 <= px <= ax + CW_SRC + 5 and ay - 5 <= py <= ay + CH_SRC + 5
    ]
    cell_paths = "\n".join(tag for _, _, tag in cell_tags_list)

    if cell_tags_list:
        # Use actual content top-left as transform origin
        # so content aligns to target top-left corner (TX, TY)
        min_x = min(px for px, _, _ in cell_tags_list)
        min_y = min(py for _, py, _ in cell_tags_list)
    else:
        min_x, min_y = ax, ay

    TX_ADJ = TX -4
    TY_ADJ = TY -1
    transform = f"translate({TX_ADJ},{TY_ADJ}) scale({sx:.6f},{sy:.6f}) translate({-ax:.4f},{-ay:.4f})"
    
    det_groups.append(
        f'<g class="detail-part" data-detail="{n}" style="display:none">'
        f'<g transform="{transform}">{cell_paths}</g>'
        f'</g>'
    )
    det_pdata[str(n)] = {"row": row, "col": col, "src_x": round(ax,2), "src_y": round(ay,2)}

DET_JSON.write_text(json.dumps(det_pdata, indent=2))

# ── gate_colors.json ──────────────────────────────────────────
COL_JSON.write_text(json.dumps(
    {str(g):{"dark":d,"light":l,"p_blue":P_BLUE,"design":D_PURP} for g,d,l in GATE_RULES}, indent=2))

# ── 9. Activation CSS ─────────────────────────────────────────
CCOL = {"Head":"#AA88EE","Ajna":"#9B59B6","Throat":"#F39C12","G":"#FFD700",
        "Heart":"#E74C3C","Solar Plexus":"#E67E22","Spleen":"#27AE60",
        "Sacral":"#E74C3C","Root":"#8B4513"}

css = ["<style id='hd-activation'>", ".gate-line{fill:#FFFFFF!important;}"]
for g, _, _ in GATE_RULES:
    css += [
        f"svg.active-p-{g} [data-gate='{g}'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-d-{g} [data-gate='{g}'].gate-line{{fill:{D_PURP}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='dark'].gate-line{{fill:{P_BLUE}!important;}}",
        f"svg.active-b-{g} [data-gate='{g}'][data-type='light'].gate-line{{fill:{D_PURP}!important;}}",
    ]
for g in [g for g,_,_ in GATE_RULES] + [10, 20, 34, 57]:
    for p in ("active-p-", "active-d-", "active-b-"):
        css.append(f"svg.{p}{g} .gate-circle[data-gate='{g}']{{fill:#1a1a2e!important;}}")
        css.append(f"svg.{p}{g} .gate-text[data-gate='{g}']{{fill:#FFFFFF!important;}}")
for name, col in CCOL.items():
    css.append(f"svg.center-active-{name.replace(' ','')} .chakra[data-center='{name}']{{fill:{col}!important;}}")
css.append(".detail-part{display:none!important;}")
for n in range(1, 257):
    css.append(f"svg.detail-on-{n} .detail-part[data-detail='{n}']{{display:block!important;}}")
css.append("</style>")

# ── 10. Assemble ──────────────────────────────────────────────
details_html = "\n<g id='details-layer'>\n" + "\n".join(det_groups) + "\n</g>"

# Insert details BEFORE the first chakra (under chakras in z-order)
first_chakra = svg.find('class="st126 chakra"')
insert_at = svg.rfind('<path', 0, first_chakra)  # start of first chakra path
svg = svg[:insert_at] + details_html + svg[insert_at:]

# CSS at the very end
last_svg_close = svg.rfind("</svg>")
svg = svg[:last_svg_close] + "\n" + "\n".join(css) + "\n</svg>"

DST.write_text(svg, encoding="utf-8")
print(f"\nWrote {DST} ({len(svg)/1e6:.2f} MB)")
print(f"  st19 hidden: ✓  detail cells: 256 ✓  detail under chakras: ✓")
