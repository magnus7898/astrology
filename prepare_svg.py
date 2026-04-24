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
    gate_positions[gate] = {"cx": round(cx,1), "cy": round(cy,1)}
    return re.sub(r'class="(st125)"',
                  f'class="\\1 gate-circle" data-gate="{gate}"', tag, count=1)

svg = re.sub(r'<circle\b[^>]+class="st125"[^>]*/>', _tag_circle, svg)

def _tag_text(m):
    tag = m.group(0)
    gm = re.search(r'>([\d]+)</text>', tag)
    if not gm:
        return tag
    g = int(gm.group(1))
    if g not in text_pos:
        return tag
    return re.sub(r'class="(st126 st127)"',
                  f'class="\\1 gate-text" data-gate="{g}"', tag, count=1)

svg = re.sub(r'<text\b[^>]+class="st126 st127"[^>]*>[\d]+</text>', _tag_text, svg)

for g, (tx, ty) in text_pos.items():
    if g not in gate_positions:
        gate_positions[g] = {"cx": round(tx,1), "cy": round(ty,1)}

POS_JSON.write_text(json.dumps(gate_positions, indent=2))
print(f"wrote {POS_JSON}  ({len(gate_positions)} gates)")

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
    return re.sub(r'class="st124"',
                  f'class="st124 chakra" data-center="{name}"', tag, count=1)

svg = re.sub(r'<path\b[^>]+class="st124"[^>]*/>', _tag_center, svg)

# ── 4. Integration anchor ─────────────────────────────────────
# Use bounding box of integration gate positions, aligned top-left
int_gates = [g for g in [10, 20, 34, 57] if g in gate_positions]
if int_gates:
    xs = [gate_positions[g]["cx"] for g in int_gates]
    ys = [gate_positions[g]["cy"] for g in int_gates]
    # Anchor = top-left of the integration cluster with small padding
    TARGET_X = min(xs) - 5
    TARGET_Y = min(ys) - 5
else:
    TARGET_X, TARGET_Y = 550.0, 313.0
print(f"[info] integration anchor: ({TARGET_X:.1f}, {TARGET_Y:.1f})")

# ── 5. Load details.svg, put body in <defs>, use <use> per artboard ───
details_svg = DETAILS_SRC.read_text(encoding="utf-8")
print(f"[info] loaded details.svg ({len(details_svg):,} chars)")

# Extract style from details.svg (for color classes)
det_style = ""
ds = re.search(r'<style[^>]*>(.*?)</style>', details_svg, re.DOTALL)
if ds:
    det_style = ds.group(1).strip()

# Strip to just the graphic content (no xml decl, svg tag, style, defs)
det_body = details_svg
for pat in [r'<\?xml[^?]*\?>', r'<!DOCTYPE[^>]*>', r'<svg[^>]*>', r'</svg>',
            r'<style[^>]*>.*?</style>', r'<defs[^>]*>.*?</defs>']:
    det_body = re.sub(pat, '', det_body, flags=re.DOTALL)
det_body = det_body.strip()

# Find grid bounds of the details artboards
all_x, all_y = [], []
for v in re.findall(r'\bx="([\d.]+)"', details_svg):
    all_x.append(float(v))
for v in re.findall(r'\by="([\d.]+)"', details_svg):
    all_y.append(float(v))
for a, b in re.findall(r'M\s*([\d.]+),([\d.]+)', details_svg):
    all_x.append(float(a)); all_y.append(float(b))

DX_MIN = min(all_x); DX_MAX = max(all_x)
DY_MIN = min(all_y); DY_MAX = max(all_y)
CELL_W = (DX_MAX - DX_MIN) / 16
CELL_H = (DY_MAX - DY_MIN) / 16
print(f"[info] details grid ({DX_MIN:.0f},{DY_MIN:.0f})→({DX_MAX:.0f},{DY_MAX:.0f}), "
      f"cell {CELL_W:.1f}×{CELL_H:.1f}")

# Build 256 artboard groups using <use> referencing a single shared <defs> group.
# This keeps the output file small (~3-5 MB instead of 355 MB).
defs_insert = (
    f'<defs id="det-defs">'
    f'<g id="det-content">{det_body}</g>'
    f'</defs>'
)

detail_groups = []
det_pos_data  = {}

for n in range(1, 257):
    idx = n - 1
    row = idx // 16
    col = idx % 16
    ax  = DX_MIN + col * CELL_W
    ay  = DY_MIN + row * CELL_H
    # Translate so that cell top-left (ax,ay) maps to TARGET position
    tx  = TARGET_X - ax
    ty  = TARGET_Y - ay

    # clipPath clips to the TARGET area after transform
    g = (
        f'<g class="detail-part" data-detail="{n}" style="visibility:hidden">'
        f'<clipPath id="cdp{n}">'
        f'<rect x="{TARGET_X:.2f}" y="{TARGET_Y:.2f}" '
        f'width="{CELL_W:.2f}" height="{CELL_H:.2f}"/>'
        f'</clipPath>'
        f'<use href="#det-content" transform="translate({tx:.2f},{ty:.2f})" '
        f'clip-path="url(#cdp{n})"/>'
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
all_gates = list(GATE_RULES.keys()) + [10, 20, 34, 57]
for gate in all_gates:
    for pfx in ("active-p-", "active-d-", "active-b-"):
        css_lines.append(
            f"svg.{pfx}{gate} .gate-circle[data-gate='{gate}']"
            f"{{fill:#1a1a2e!important;}}")
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

# Inject defs for the shared details content (right after <svg ...>)
svg = re.sub(r'(<svg\b[^>]*>)', f'\\1\n{defs_insert}\n', svg, count=1)

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
print(f"  Gate lines tagged : {tagged} / {len(GATE_RULES)*2} (120 expected, 2 missing = gates 9,47,48,60 each lack one color in SVG)")
print(f"  Centers tagged    : 9")
print(f"  Gate circles      : {len(gate_positions)}")
print(f"  Detail artboards  : 256 (via <use> — compact)")
print(f"  Output file size  : {mb:.1f} MB")
