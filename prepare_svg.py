"""prepare_svg.py — preprocess human.svg + details.svg for the HD bodygraph.

New human.svg layout (viewBox 0 0 1421.8 827):
  LEFT  (x=0-542):   human silhouette (st0 teal) — untouched
  RIGHT (x=537-932+): bodygraph — channels, centers, gate circles/texts

Steps:
  1. Parse 60 non-integration gate color rules (dark + light per gate).
  2. Tag every matching path/rect with data-gate="N" data-type="dark|light".
  3. Tag 9 center shapes (st124) with data-center="Name".
  4. Tag gate circles (st125) and texts with data-gate="N".
  5. Put details.svg content in <defs> once, reference via <use>+clipPath
     for each of the 256 integration artboards (keeps file small).
  6. Inject activation CSS.

Outputs:
  static/human_prepared.svg   (~3-5 MB, not 355 MB)
  static/gate_positions.json
  static/gate_colors.json
  static/detail_positions.json
"""

import json, re
from pathlib import Path

ROOT        = Path(__file__).parent
HUMAN_SRC   = ROOT / "static" / "human.svg"
DETAILS_SRC = ROOT / "static" / "details.svg"
DST         = ROOT / "static" / "human_prepared.svg"
POS_JSON    = ROOT / "static" / "gate_positions.json"
COL_JSON    = ROOT / "static" / "gate_colors.json"
DET_JSON    = ROOT / "static" / "detail_positions.json"

PERSONALITY_BLUE = "#292562"   # matches details.svg st1
DESIGN_PURPLE    = "#67308F"
WHITE            = "#FFFFFF"

# ── 60 gate color rules ───────────────────────────────────────
GATE_RULES_RAW = [
    (36,"#FF0000","#FF3333"), (35,"#E60000","#FF4D4D"), (22,"#CC0000","#FF6666"),
    (12,"#B30000","#FF8080"), (37,"#990000","#FF9999"), (40,"#FF8000","#FF9933"),
    (21,"#E67300","#FFA34D"), (45,"#CC6600","#FFAD66"), (51,"#B35900","#FFB880"),
    (25,"#994D00","#FFC299"), ( 6,"#FFFF00","#FFFF33"), (59,"#E6E600","#FFFF4D"),
    (27,"#CCCC00","#FFFF66"), (50,"#B3B300","#FFFF80"), (26,"#999900","#FFFF99"),
    (44,"#00FF00","#33FF33"), (48,"#00E600","#4DFF4D"), (16,"#00CC00","#66FF66"),
    (30,"#00B300","#80FF80"), (41,"#009900","#99FF99"), (55,"#00FFFF","#33FFFF"),
    (39,"#00E6E6","#4DFFFF"), (49,"#00CCCC","#66FFFF"), (19,"#00B3B3","#80FFFF"),
    (58,"#009999","#99FFFF"), (18,"#0000FF","#3333FF"), (38,"#0000E6","#4D4DFF"),
    (28,"#0000CC","#6666FF"), (54,"#0000B3","#8080FF"), (32,"#000099","#9999FF"),
    (52,"#800080","#9933FF"), ( 9,"#730073","#A34DFF"), (60,"#660066","#AD66FF"),
    ( 3,"#590059","#B880FF"), (53,"#4D004D","#C299FF"), (42,"#FF00FF","#FF33FF"),
    (29,"#E600E6","#FF4DFF"), (14,"#CC00CC","#FF66FF"), ( 5,"#B300B3","#FF80FF"),
    (46,"#990099","#FF99FF"), ( 2,"#8B4513","#A0522D"), (15,"#7A3C12","#B05A2F"),
    (13,"#693310","#C06231"), ( 1,"#582A0E","#D06A33"), ( 7,"#47210C","#E07235"),
    (33,"#808080","#999999"), ( 8,"#737373","#A6A6A6"), (31,"#666666","#B3B3B3"),
    (56,"#595959","#BFBFBF"), (23,"#4D4D4D","#CCCCCC"), (62,"#FAD0C4","#C1E1C1"),
    (11,"#F8C8DC","#B39EB5"), (43,"#F3E5AB","#AED9E0"), (17,"#E6E6FA","#98D8C8"),
    ( 4,"#D4F1F4","#88C5B9"), (63,"#2C3E50","#F1C40F"), (24,"#34495E","#F39C12"),
    (61,"#2980B9","#E67E22"), (64,"#1ABC9C","#D35400"), (47,"#16A085","#E74C3C"),
]

GATE_RULES    = {g: {"dark": d, "light": l} for g, d, l in GATE_RULES_RAW}
COLOR_TO_GATE = {}
for g, d, l in GATE_RULES_RAW:
    COLOR_TO_GATE[d.upper()] = (g, "dark")
    COLOR_TO_GATE[l.upper()] = (g, "light")

print(f"[info] {len(GATE_RULES)} gate rules, {len(COLOR_TO_GATE)} color→gate mappings")

# ── Load SVG ─────────────────────────────────────────────────
svg = HUMAN_SRC.read_text(encoding="utf-8")
print(f"[info] loaded human.svg ({len(svg):,} chars)")

# Parse style: class → fill color
style_m = re.search(r'<style[^>]*>(.*?)</style>', svg, re.DOTALL)
class_to_color = {}
for m in re.finditer(r'\.(st\d+)\s*\{[^}]*fill:\s*(#[0-9A-Fa-f]{6})', style_m.group(1)):
    class_to_color[m.group(1)] = m.group(2).upper()

# ── 1. Tag gate line elements ─────────────────────────────────
tagged = 0
def _tag_channel(m):
    global tagged
    tag = m.group(0)
    cm = re.search(r'class="(st\d+)"', tag)
    if not cm:
        return tag
    color = class_to_color.get(cm.group(1), "")
    if color not in COLOR_TO_GATE:
        return tag
    gate, gtype = COLOR_TO_GATE[color]
    tagged += 1
    return re.sub(r'class="(st\d+)"',
                  f'class="\\1 gate-line" data-gate="{gate}" data-type="{gtype}"',
                  tag, count=1)

svg = re.sub(r'<(?:rect|path|line)\b[^>]*/>', _tag_channel, svg)
print(f"[info] tagged {tagged} gate-line elements")

# ── 2. Tag gate circles & texts ───────────────────────────────
text_pos = {}
for m in re.finditer(
        r'transform="matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)"[^>]*>([\d]+)</text>', svg):
    text_pos[int(m.group(3))] = (float(m.group(1)), float(m.group(2)))

gate_positions = {}

def _nearest(cx, cy):
    best, bd = None, 1e9
    for g, (tx, ty) in text_pos.items():
        d = (cx-tx)**2 + (cy-ty)**2
        if d < bd:
            bd, best = d, g
    return best

def _tag_circle(m):
    tag = m.group(0)
    cxm = re.search(r'cx="([\d.]+)"', tag)
    cym = re.search(r'cy="([\d.]+)"', tag)
    if not cxm or not cym:
        return tag
    cx, cy = float(cxm.group(1)), float(cym.group(1))
    gate = _nearest(cx, cy)
    if gate is None:
        return tag
    # Only assign if the circle is genuinely close to the gate text (< 15px)
    # Prevents mis-assigning distant circles to side gates like gate 25
    tx, ty = text_pos[gate]
    dist = ((cx - tx)**2 + (cy - ty)**2) ** 0.5
    if dist > 15:
        return tag  # skip — no real circle for this gate position
    gate_positions[gate] = {"cx": round(cx,1), "cy": round(cy,1)}
    return re.sub(r'class="(st128)"',
                  f'class="\\1 gate-circle" data-gate="{gate}"', tag, count=1)

svg = re.sub(r'<circle\b[^>]+class="st128"[^>]*/>', _tag_circle, svg)

def _tag_text(m):
    tag = m.group(0)
    gm = re.search(r'>([\d]+)</text>', tag)
    if not gm:
        return tag
    g = int(gm.group(1))
    if g not in text_pos:
        return tag
    return re.sub(r'class="(st129 st130)"',
                  f'class="\\1 gate-text" data-gate="{g}"', tag, count=1)

svg = re.sub(r'<text\b[^>]+class="st129 st130"[^>]*>[\d]+</text>', _tag_text, svg)

for g, (tx, ty) in text_pos.items():
    if g not in gate_positions:
        gate_positions[g] = {"cx": round(tx,1), "cy": round(ty,1)}

POS_JSON.write_text(json.dumps(gate_positions, indent=2))
print(f"wrote {POS_JSON}  ({len(gate_positions)} gates)")

# Add synthetic circles for gates that have no real st128 circle
tagged_circle_gates = set(
    int(m.group(1))
    for m in re.finditer(r'class="st128 gate-circle" data-gate="(\d+)"', svg)
)

# ── 3. Tag center shapes (st124) ─────────────────────────────
def _center_name(sx, sy):
    if sy < 220:    return "Head"
    if sy < 310:    return "Ajna"
    if sy < 390:    return "Throat"
    if sy < 480:    return "G"
    if sy < 540:    return "Heart"
    if sy < 700:
        if sx < 600:   return "Spleen"
        if sx > 900:   return "Solar Plexus"
        return "Sacral"
    return "Root"

def _tag_center(m):
    tag = m.group(0)
    dm = re.search(r'd="([^"]+)"', tag)
    if not dm:
        return tag
    pm = re.search(r'M\s*([\d.]+),([\d.]+)', dm.group(1))
    if not pm:
        return tag
    name = _center_name(float(pm.group(1)), float(pm.group(2)))
    print(f"[info] center {name:15} start=({pm.group(1)},{pm.group(2)})")
    return re.sub(r'class="st127"',
                  f'class="st127 chakra" data-center="{name}"', tag, count=1)

svg = re.sub(r'<path\b[^>]+class="st127"[^>]*/>', _tag_center, svg)

# Gate 25 (Initiation) sits on the G-center diamond — no separate backing circle.
# Tag the G-center chakra shape ALSO as gate-25's gate-circle indicator.
# When gate 25 is activated: the G-center diamond darkens and text turns white.
svg = svg.replace(
    'class="st127 chakra" data-center="G"',
    'class="st127 chakra gate-circle" data-center="G" data-gate="25"',
)
if 'class="st127 chakra gate-circle" data-center="G" data-gate="25"' in svg:
    print("[info] gate 25: G-center diamond tagged as gate-circle ✓")
else:
    print("[warn] gate 25: G-center tagging failed")

# ── 4. Integration anchor ─────────────────────────────────────
# Cell size matches the details.svg viewBox exactly
CELL_W = 152.6
CELL_H = 279.0

# Anchor: right edge = rightmost gate (20), bottom edge = lowest gate (34)
# This guarantees all 4 integration gates are inside the artboard cell.
int_gates_pos = {g: gate_positions[g] for g in [10, 20, 34, 57] if g in gate_positions}
if len(int_gates_pos) == 4:
    xs = [p["cx"] for p in int_gates_pos.values()]
    ys = [p["cy"] for p in int_gates_pos.values()]
    TARGET_X = round(max(xs) - CELL_W, 2)   # right edge lands on rightmost gate
    TARGET_Y = round(max(ys) - CELL_H, 2)   # bottom edge lands on lowest gate
else:
    TARGET_X, TARGET_Y = 554.7, 307.4
print(f"[info] integration anchor: ({TARGET_X:.1f}, {TARGET_Y:.1f})")
print(f"[info] cell size: {CELL_W} × {CELL_H}")
print(f"[info] cell covers: x={TARGET_X:.1f}–{TARGET_X+CELL_W:.1f}, y={TARGET_Y:.1f}–{TARGET_Y+CELL_H:.1f}")

# ── 5. Load details.svg, embed paths directly per artboard ──────
# Direct embedding (not <use>) for maximum browser compatibility.
# Each artboard gets only its own paths → ~1.5 MB total (same as <use> approach).
details_svg = DETAILS_SRC.read_text(encoding="utf-8")
print(f"[info] loaded details.svg ({len(details_svg):,} chars)")

# Extract and prefix style from details.svg
det_style = ""
ds = re.search(r'<style[^>]*>(.*?)</style>', details_svg, re.DOTALL)
if ds:
    det_style = re.sub(r'\.(st\d+)\b', r'.det-\1', ds.group(1).strip())

# Find grid bounds — artboard origins are at (col*CELL_W, row*CELL_H)
# (no need to recalculate from path ranges — we know the cell size from viewBox)
DX_MIN = 0.0
DY_MIN = 0.0
print(f"[info] details grid: 16×16 artboards, each {CELL_W}×{CELL_H}, origin (0,0)")

# Extract all paths from details.svg with their M start coordinates
det_all_paths = []
for m in re.finditer(r'<path class="([^"]+)" d="([^"]+)"/>', details_svg):
    cls = m.group(1)
    d   = m.group(2)
    pm  = re.search(r'M\s*([\d.]+),([\d.]+)', d)
    if pm:
        det_all_paths.append((float(pm.group(1)), float(pm.group(2)),
                              f'class="det-{cls}"', d))

detail_groups = []
det_pos_data  = {}

for n in range(1, 257):
    idx  = n - 1
    row  = idx // 16
    col  = idx % 16
    ax   = DX_MIN + col * CELL_W
    ay   = DY_MIN + row * CELL_H
    # translate: moves cell origin (ax,ay) to TARGET
    tx   = TARGET_X - ax
    ty   = TARGET_Y - ay

    # Collect paths belonging to this cell (with ±5 tolerance)
    cell_paths = [
        f'<path {cls_str} d="{d}"/>'
        for (px, py, cls_str, d) in det_all_paths
        if ax - 5 <= px <= ax + CELL_W + 5
        and ay - 5 <= py <= ay + CELL_H + 5
    ]

    path_block = "\n".join(cell_paths)
    g = (
        f'<g class="detail-part" data-detail="{n}" style="visibility:hidden">'
        f'<clipPath id="cdp{n}">'
        f'<rect x="{TARGET_X:.2f}" y="{TARGET_Y:.2f}" '
        f'width="{CELL_W:.2f}" height="{CELL_H:.2f}"/>'
        f'</clipPath>'
        f'<g transform="translate({tx:.2f},{ty:.2f})" clip-path="url(#cdp{n})">'
        f'{path_block}'
        f'</g>'
        f'</g>'
    )
    detail_groups.append(g)
    det_pos_data[str(n)] = {
        "row": row, "col": col,
        "src_x": round(ax, 2), "src_y": round(ay, 2),
        "dst_x": round(TARGET_X, 2), "dst_y": round(TARGET_Y, 2),
    }

DET_JSON.write_text(json.dumps(det_pos_data, indent=2))
print(f"wrote {DET_JSON}  (256 detail cells)")

# ── 6. gate_colors.json ──────────────────────────────────────
col_data = {str(g): {"dark": r["dark"], "light": r["light"],
                      "p_blue": PERSONALITY_BLUE, "design": DESIGN_PURPLE}
            for g, r in GATE_RULES.items()}
COL_JSON.write_text(json.dumps(col_data, indent=2))
print(f"wrote {COL_JSON}  ({len(col_data)} gate color rules)")

# ── 7. Activation CSS ─────────────────────────────────────────
CENTER_ACTIVE_COLORS = {
    "Head":         "#AA88EE",
    "Ajna":         "#9B59B6",
    "Throat":       "#F39C12",
    "G":            "#FFD700",
    "Heart":        "#E74C3C",
    "Solar Plexus": "#E67E22",
    "Spleen":       "#27AE60",
    "Sacral":       "#E74C3C",
    "Root":         "#8B4513",
}

css_lines = ["<style id='hd-activation'>"]

# Default: all gate lines → white (inactive)
css_lines.append(".gate-line { fill: #FFFFFF !important; }")

for gate, rule in GATE_RULES.items():
    g = gate
    # personality only
    css_lines.append(
        f"svg.active-p-{g} [data-gate='{g}'].gate-line"
        f"{{fill:{PERSONALITY_BLUE}!important;}}")
    # design only
    css_lines.append(
        f"svg.active-d-{g} [data-gate='{g}'].gate-line"
        f"{{fill:{DESIGN_PURPLE}!important;}}")
    # both — dark=blue, light=purple
    css_lines.append(
        f"svg.active-b-{g} [data-gate='{g}'][data-type='dark'].gate-line"
        f"{{fill:{PERSONALITY_BLUE}!important;}}")
    css_lines.append(
        f"svg.active-b-{g} [data-gate='{g}'][data-type='light'].gate-line"
        f"{{fill:{DESIGN_PURPLE}!important;}}")

# Gate circles & texts — darken when activated
# Gate 25 is special: its "circle" is the G-center diamond (st127)
# Color it with personality blue / design purple instead of near-black
all_gates = list(GATE_RULES.keys()) + [10, 20, 34, 57]
for gate in all_gates:
    if gate == 25:
        # G-center diamond: personality=blue, design=purple, both=mix
        css_lines.append(
            f"svg.active-p-25 .gate-circle[data-gate='25']"
            f"{{fill:{PERSONALITY_BLUE}!important;}}")
        css_lines.append(
            f"svg.active-d-25 .gate-circle[data-gate='25']"
            f"{{fill:{DESIGN_PURPLE}!important;}}")
        css_lines.append(
            f"svg.active-b-25 .gate-circle[data-gate='25']"
            f"{{fill:{PERSONALITY_BLUE}!important;}}")
    else:
        for pfx in ("active-p-", "active-d-", "active-b-"):
            css_lines.append(
                f"svg.{pfx}{gate} .gate-circle[data-gate='{gate}']"
                f"{{fill:#1a1a2e!important;}}")
    for pfx in ("active-p-", "active-d-", "active-b-"):
        css_lines.append(
            f"svg.{pfx}{gate} .gate-text[data-gate='{gate}']"
            f"{{fill:#FFFFFF!important;}}")

# Centers
for name, color in CENTER_ACTIVE_COLORS.items():
    safe = name.replace(" ", "")
    css_lines.append(
        f"svg.center-active-{safe} .chakra[data-center='{name}']"
        f"{{fill:{color}!important;}}")

# Detail artboard visibility
css_lines.append(".detail-part{visibility:hidden!important;}")
for n in range(1, 257):
    css_lines.append(
        f"svg.detail-on-{n} .detail-part[data-detail='{n}']"
        f"{{visibility:visible!important;}}")

css_lines.append("</style>")
activation_css = "\n".join(css_lines)

# ── Assemble final SVG ────────────────────────────────────────
# Inject details.svg style into main style block
if det_style:
    svg = re.sub(r'(<style\b[^>]*>)',
                 f'\\1\n/* === details.svg styles === */\n{det_style}\n',
                 svg, count=1)

# Inject detail artboards + activation CSS before </svg>
details_layer = "\n".join(detail_groups)
svg = svg.replace(
    "</svg>",
    f"\n{activation_css}\n"
    f"<g id='details-layer'>\n{details_layer}\n</g>\n"
    f"</svg>"
)

DST.write_text(svg, encoding="utf-8")
mb = len(svg) / 1_000_000
print(f"wrote {DST}  ({mb:.1f} MB)")
print(f"\nSummary:")
print(f"  Gate lines tagged : {tagged}/120")
print(f"  Centers tagged    : 9")
print(f"  Gate circles      : {len(gate_positions)}")
print(f"  Detail artboards  : 256 (direct path embedding)")
print(f"  Output file size  : {mb:.1f} MB")
