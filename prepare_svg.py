"""Preprocessing for the new human.svg + details.svg combo.

New SVG design:
    - Every non-integration gate's two channel-lines use UNIQUE marker
      colors (dark and light). When that gate is activated, we find/replace
      those marker colors with blue/purple to show personality/design state.
    - The 4 integration gates (10, 20, 34, 57) are handled by swapping one
      of 256 detail artboards.

This script:
    1. Parses the 60 gate → (dark, light, p_blue) rules.
    2. Tags each colored channel-line with data-line-gate="N" and
       data-line-side="dark|light" so the frontend can recolor them.
    3. Tags all 64 gate circles + texts with data-gate="N".
    4. Re-orders the SVG so z-order is:
           channel-lines < centers < gate-circles < gate-digits
       regardless of their original order in the source file.
    5. Deletes the default integration silhouette (st64 paths in the
       integration-cluster bbox).
    6. Extracts the 256 artboards from details.svg, translates each to
       the integration anchor, and injects them as hidden <g data-detail="N">.
    7. Injects activation CSS + Georgian-friendly class names.

Outputs:
    static/human_prepared.svg
    static/gate_positions.json
    static/gate_colors.json
    static/detail_positions.json
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
HUMAN_SRC = ROOT / "static" / "human.svg"
DETAILS_SRC = ROOT / "static" / "details.svg"
DST = ROOT / "static" / "human_prepared.svg"
POS = ROOT / "static" / "gate_positions.json"
COL = ROOT / "static" / "gate_colors.json"
DET = ROOT / "static" / "detail_positions.json"

# ---------- The 60 non-integration gate color rules ----------
# gate → {dark, light, p_blue} (p_blue is the unique shade of #2925xx)
RULES_RAW = """
36	#FF0000	#FF3333	#292562
35	#E60000	#FF4D4D	#292563
22	#CC0000	#FF6666	#292564
12	#B30000	#FF8080	#292565
37	#990000	#FF9999	#292566
40	#FF8000	#FF9933	#292572
21	#E67300	#FFA34D	#292573
45	#CC6600	#FFAD66	#292574
51	#B35900	#FFB880	#292575
25	#994D00	#FFC299	#292576
6	#FFFF00	#FFFF33	#292582
59	#E6E600	#FFFF4D	#292583
27	#CCCC00	#FFFF66	#292584
50	#B3B300	#FFFF80	#292585
26	#999900	#FFFF99	#292586
44	#00FF00	#33FF33	#292592
48	#00E600	#4DFF4D	#292593
16	#00CC00	#66FF66	#292594
30	#00B300	#80FF80	#292595
41	#009900	#99FF99	#292596
55	#00FFFF	#33FFFF	#292602
39	#00E6E6	#4DFFFF	#292603
49	#00CCCC	#66FFFF	#292604
19	#00B3B3	#80FFFF	#292605
58	#009999	#99FFFF	#292606
18	#0000FF	#3333FF	#292612
38	#0000E6	#4D4DFF	#292613
28	#0000CC	#6666FF	#292614
54	#0000B3	#8080FF	#292615
32	#000099	#9999FF	#292616
52	#800080	#9933FF	#292622
9	#730073	#A34DFF	#292623
60	#660066	#AD66FF	#292624
3	#590059	#B880FF	#292625
53	#4D004D	#C299FF	#292626
42	#FF00FF	#FF33FF	#292632
29	#E600E6	#FF4DFF	#292633
14	#CC00CC	#FF66FF	#292634
5	#B300B3	#FF80FF	#292635
46	#990099	#FF99FF	#292636
2	#8B4513	#A0522D	#292642
15	#7A3C12	#B05A2F	#292643
13	#693310	#C06231	#292644
1	#582A0E	#D06A33	#292645
7	#47210C	#E07235	#292646
33	#808080	#999999	#292652
8	#737373	#A6A6A6	#292653
31	#666666	#B3B3B3	#292654
56	#595959	#BFBFBF	#292655
23	#4D4D4D	#CCCCCC	#292656
62	#FAD0C4	#C1E1C1	#292662
11	#F8C8DC	#B39EB5	#292663
43	#F3E5AB	#AED9E0	#292664
17	#E6E6FA	#98D8C8	#292665
4	#D4F1F4	#88C5B9	#292666
63	#2C3E50	#F1C40F	#292672
24	#34495E	#F39C12	#292673
61	#2980B9	#E67E22	#292674
64	#1ABC9C	#D35400	#292675
47	#16A085	#E74C3C	#292676
"""

DESIGN_PURPLE = "#67308F"

RULES = {}
for line in RULES_RAW.strip().split("\n"):
    parts = line.strip().split("\t")
    if len(parts) == 4:
        gate = int(parts[0])
        RULES[gate] = {
            "dark":   parts[1].upper(),
            "light":  parts[2].upper(),
            "p_blue": parts[3].upper(),
        }

# ---------- Load SVG ----------
svg = HUMAN_SRC.read_text()

# Parse style block: class → fill color
style_block = re.search(r'<style[^>]*>(.*?)</style>', svg, re.DOTALL).group(1)
class_to_color = {}
for cls, color in re.findall(r'\.(st\d+)\s*\{[^}]*fill:\s*(#[0-9A-Fa-f]+)', style_block):
    class_to_color[cls] = color.upper()

# Build color → list of classes
color_to_classes = {}
for cls, color in class_to_color.items():
    color_to_classes.setdefault(color, []).append(cls)

# ---------- Gate positions ----------
# Gate circles: class st122. Gate 63 uses an <ellipse> instead.
circles = []
for m in re.finditer(r'<circle class="st122" cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"\s*/>', svg):
    circles.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), m.group(0)))
# Ellipse (rotated gate, likely gate 63)
for m in re.finditer(r'<ellipse[^>]*class="st122"[^>]*/>', svg):
    cx_m = re.search(r'\bcx="([\d.]+)"', m.group(0))
    cy_m = re.search(r'\bcy="([\d.]+)"', m.group(0))
    if cx_m and cy_m:
        # transform may rotate it — use the cx,cy attribute for mapping
        circles.append((float(cx_m.group(1)), float(cy_m.group(1)), 6.9, m.group(0)))

# Gate texts: class "st123 st124"
text_re = re.compile(r'<text transform="matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)" class="st123 st124">(\d+)</text>')
texts = text_re.findall(svg)

gate_to_idx = {}
used = set()
for tx, ty, num in texts:
    tx, ty = float(tx), float(ty)
    best_i, best_d = None, 1e9
    for i, (cx, cy, _, _) in enumerate(circles):
        if i in used: continue
        d = (cx - (tx + 3.5)) ** 2 + (cy - (ty - 3)) ** 2
        if d < best_d:
            best_d, best_i = d, i
    if best_i is not None:
        used.add(best_i)
        gate_to_idx[int(num)] = best_i

idx_to_gate = {i: g for g, i in gate_to_idx.items()}
gate_positions = {
    g: {"cx": circles[i][0], "cy": circles[i][1]}
    for g, i in gate_to_idx.items()
}

# ---------- Tag channel-line elements ----------
# For each gate rule, find its dark-color elements and light-color elements
# (using the class → color map) and inject data-line-gate + data-line-side.
# Since multiple gates can share a class (5 of them do), we need to split
# shared-class elements by nearness to the gate circle.

# Build a list of every path/rect/polygon element and its class.
element_pattern = re.compile(
    r'<(path|rect|polygon|circle|ellipse|line)\b[^>]*?class="(st\d+)"[^>]*?/>'
)

# Pre-compute: for each class, list all its elements with their approximate
# position (first M coord for paths, centre for rect, cx for circle, etc.)
def elem_position(text):
    """Return approximate (x, y) centre for an element."""
    tag = re.match(r'<(\w+)', text).group(1)
    if tag == "circle" or tag == "ellipse":
        cx = re.search(r'\bcx="([-\d.]+)"', text)
        cy = re.search(r'\bcy="([-\d.]+)"', text)
        if cx and cy: return (float(cx.group(1)), float(cy.group(1)))
    if tag == "rect":
        x = re.search(r'\bx="([-\d.]+)"', text)
        y = re.search(r'\by="([-\d.]+)"', text)
        w = re.search(r'\bwidth="([-\d.]+)"', text)
        h = re.search(r'\bheight="([-\d.]+)"', text)
        if x and y and w and h:
            return (float(x.group(1)) + float(w.group(1))/2,
                    float(y.group(1)) + float(h.group(1))/2)
    if tag == "line":
        x1 = re.search(r'\bx1="([-\d.]+)"', text)
        y1 = re.search(r'\by1="([-\d.]+)"', text)
        x2 = re.search(r'\bx2="([-\d.]+)"', text)
        y2 = re.search(r'\by2="([-\d.]+)"', text)
        if x1 and y1 and x2 and y2:
            return ((float(x1.group(1))+float(x2.group(1)))/2,
                    (float(y1.group(1))+float(y2.group(1)))/2)
    if tag == "path":
        d_m = re.search(r'\bd="([^"]+)"', text)
        if d_m:
            # Trace the path with proper relative-command handling.
            pts = _trace_path_points(d_m.group(1))
            if pts:
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                # Use the bbox centre of the full path.
                return ((min(xs)+max(xs))/2, (min(ys)+max(ys))/2)
    return None


def _trace_path_points(d):
    """Walk a path-d string and return every absolute (x, y) anchor point."""
    x = y = 0.0
    out = []
    for cm in re.finditer(r'([MmLlCcSsQqTtAaHhVvZz])([^MmLlCcSsQqTtAaHhVvZz]*)', d):
        cmd = cm.group(1)
        args = [float(n) for n in re.findall(r'-?\d+\.?\d*', cm.group(2))]
        rel = cmd.islower() and cmd != 'z'
        C = cmd.upper(); k = 0
        if C == 'M' and args:
            x = (x + args[0]) if rel else args[0]
            y = (y + args[1]) if rel else args[1]
            out.append((x, y)); k = 2; C = 'L'
        while k < len(args):
            if C == 'L':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'H':
                x = (x + args[k]) if rel else args[k]
                out.append((x, y)); k += 1
            elif C == 'V':
                y = (y + args[k]) if rel else args[k]
                out.append((x, y)); k += 1
            elif C == 'C':
                x = (x + args[k+4]) if rel else args[k+4]
                y = (y + args[k+5]) if rel else args[k+5]
                out.append((x, y)); k += 6
            elif C in ('S', 'Q'):
                x = (x + args[k+2]) if rel else args[k+2]
                y = (y + args[k+3]) if rel else args[k+3]
                out.append((x, y)); k += 4
            elif C == 'T':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'Z':
                k = len(args) + 1
            else:
                break
    return out

# Collect all element info
elements = []   # list of {text, class, pos, start, end}
for m in element_pattern.finditer(svg):
    text = m.group(0)
    cls = m.group(2)
    pos = elem_position(text)
    if pos is None: continue
    elements.append({"text": text, "class": cls, "pos": pos,
                     "start": m.start(), "end": m.end()})

# Index by class
class_elements = {}
for e in elements:
    class_elements.setdefault(e["class"], []).append(e)

# For each gate rule, find the one dark-element and one light-element closest
# to the gate's circle position.
gate_colors_info = {}   # gate → {dark_class, light_class, p_blue, chosen indices}
gate_line_tags = []     # list of (element index in `elements`, gate, side)

for gate, rule in RULES.items():
    if gate not in gate_positions:
        print(f"WARN: gate {gate} has no position; skipping")
        continue
    gx, gy = gate_positions[gate]["cx"], gate_positions[gate]["cy"]
    dark_classes = color_to_classes.get(rule["dark"], [])
    light_classes = color_to_classes.get(rule["light"], [])

    dark_elems = [e for c in dark_classes for e in class_elements.get(c, [])]
    light_elems = [e for c in light_classes for e in class_elements.get(c, [])]

    d_elem = None; l_elem = None
    if dark_elems:
        dark_elems.sort(key=lambda e: (e["pos"][0]-gx)**2 + (e["pos"][1]-gy)**2)
        d_elem = dark_elems[0]
    if light_elems:
        light_elems.sort(key=lambda e: (e["pos"][0]-gx)**2 + (e["pos"][1]-gy)**2)
        l_elem = light_elems[0]

    # Fallback for missing side: find a paired element by column-adjacency.
    # Channel-line rects sit in PAIRS 4.1 px apart along x, same y.
    # If only one side was found by color, look for a UNTAGGED rect right
    # next to it (+/- 4.1 px on x, same y) with the same dimensions.
    CENTER_CLASSES = {"st12", "st64", "st121", "st122", "st123", "st124", "st18", "st17"}
    already_tagged_ids = set()
    for dd, _, _ in gate_line_tags:
        already_tagged_ids.add(id(dd))

    # Track already-chosen-in-this-iteration
    if d_elem is not None: already_tagged_ids.add(id(d_elem))
    if l_elem is not None: already_tagged_ids.add(id(l_elem))

    if (d_elem is None) or (l_elem is None):
        anchor = d_elem or l_elem   # the side we already have
        # Try column-adjacent fallback first if anchor is a rect
        if anchor is not None:
            anchor_text = anchor["text"]
            x_m = re.search(r'\bx="([\d.]+)"', anchor_text)
            y_m = re.search(r'\by="([\d.]+)"', anchor_text)
            w_m = re.search(r'\bwidth="([\d.]+)"', anchor_text)
            h_m = re.search(r'\bheight="([\d.]+)"', anchor_text)
            if x_m and y_m and w_m and h_m:
                ax = float(x_m.group(1)); ay = float(y_m.group(1))
                aw = float(w_m.group(1)); ah = float(h_m.group(1))
                # Look for another rect at ax±4.1, same y, same size
                for e in elements:
                    if e["class"] in CENTER_CLASSES: continue
                    if id(e) in already_tagged_ids: continue
                    et = e["text"]
                    if not et.startswith("<rect"): continue
                    ex_m = re.search(r'\bx="([\d.]+)"', et)
                    ey_m = re.search(r'\by="([\d.]+)"', et)
                    ew_m = re.search(r'\bwidth="([\d.]+)"', et)
                    eh_m = re.search(r'\bheight="([\d.]+)"', et)
                    if not all([ex_m, ey_m, ew_m, eh_m]): continue
                    ex = float(ex_m.group(1)); ey = float(ey_m.group(1))
                    ew = float(ew_m.group(1)); eh = float(eh_m.group(1))
                    if abs(ey - ay) > 1: continue
                    if abs(ew - aw) > 0.5 or abs(eh - ah) > 0.5: continue
                    dx = abs(ex - ax)
                    if 3 < dx < 6:   # ~4.1 px column spacing
                        if d_elem is None:
                            d_elem = e; already_tagged_ids.add(id(e)); break
                        if l_elem is None:
                            l_elem = e; already_tagged_ids.add(id(e)); break

        # Generic fallback (widest-radius search) if column-adjacent didn't work
        if (d_elem is None) or (l_elem is None):
            candidates = []
            for e in elements:
                if e["class"] in CENTER_CLASSES: continue
                if id(e) in already_tagged_ids: continue
                d = math.hypot(e["pos"][0] - gx, e["pos"][1] - gy)
                if d < 120:
                    candidates.append((d, e))
            candidates.sort(key=lambda kv: kv[0])
            for _, cand in candidates:
                if d_elem is None:
                    d_elem = cand; already_tagged_ids.add(id(cand)); continue
                if l_elem is None:
                    l_elem = cand; already_tagged_ids.add(id(cand)); continue
                break

    if d_elem is None or l_elem is None:
        gate_colors_info[gate] = {**rule, "dark_class": None, "light_class": None}
        continue
    gate_colors_info[gate] = {
        **rule,
        "dark_class": d_elem["class"],
        "light_class": l_elem["class"],
    }
    gate_line_tags.append((d_elem, gate, "dark"))
    gate_line_tags.append((l_elem, gate, "light"))

# Apply tags by rewriting element strings
# Build replacement map: elem_start → new_text
replacements = {}
for elem, gate, side in gate_line_tags:
    txt = elem["text"]
    # Inject data-line-gate and data-line-side + add "gate-line" class
    new_txt = re.sub(
        r'class="(st\d+)"',
        lambda m: f'class="{m.group(1)} gate-line" data-line-gate="{gate}" data-line-side="{side}"',
        txt, count=1,
    )
    replacements[elem["start"]] = (elem["end"], new_txt)

# Apply replacements to svg (scan in reverse to keep offsets valid)
for start in sorted(replacements.keys(), reverse=True):
    end, new_txt = replacements[start]
    svg = svg[:start] + new_txt + svg[end:]

# ---------- Tag gate circles + texts ----------
# Need to re-parse because svg was modified above.
# Circles (st122)
def _tag_circle(m):
    cx = float(m.group(1)); cy = float(m.group(2))
    # find gate at this position
    best_g = None; best_d = 9.0  # px threshold
    for g, p in gate_positions.items():
        d = math.hypot(p["cx"] - cx, p["cy"] - cy)
        if d < best_d: best_d, best_g = d, g
    if best_g is None:
        return m.group(0)
    return (f'<circle class="st122 gate-circle" data-gate="{best_g}" '
            f'cx="{m.group(1)}" cy="{m.group(2)}" r="{m.group(3)}"/>')
svg = re.sub(
    r'<circle class="st122" cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"\s*/>',
    _tag_circle, svg,
)

# Ellipses (gate 63)
def _tag_ellipse(m):
    attrs = m.group(0)
    cx = float(re.search(r'\bcx="([\d.]+)"', attrs).group(1))
    cy = float(re.search(r'\bcy="([\d.]+)"', attrs).group(1))
    best_g = None; best_d = 9.0
    for g, p in gate_positions.items():
        d = math.hypot(p["cx"] - cx, p["cy"] - cy)
        if d < best_d: best_d, best_g = d, g
    if best_g is None:
        return attrs
    return attrs.replace(
        'class="st122"',
        f'class="st122 gate-circle" data-gate="{best_g}"', 1,
    )
svg = re.sub(r'<ellipse[^>]*class="st122"[^>]*/>', _tag_ellipse, svg)

# Texts
def _tag_text(m):
    tx = float(m.group(1)); ty = float(m.group(2))
    num = int(m.group(3))
    return (f'<text transform="matrix(1 0 0 1 {m.group(1)} {m.group(2)})" '
            f'class="st123 st124 gate-text" data-gate="{num}">{num}</text>')
svg = re.sub(
    r'<text transform="matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)" class="st123 st124">(\d+)</text>',
    _tag_text, svg,
)

# ---------- Handle integration silhouette ----------
# Capture the EXACT bbox of the default silhouette (st17 white + st18 gold)
# BEFORE deleting, so we can place detail artboards at the same position.

def _trace_default_silhouette_bbox(svg_text):
    xs, ys = [], []
    for cls in ("st17", "st18"):
        m = re.search(f'<path class="{cls}" d="([^"]+)"', svg_text)
        if m:
            # Quick trace of absolute points
            x = y = 0.0
            for cm in re.finditer(r'([MmLlCcSsQqTtAaHhVvZz])([^MmLlCcSsQqTtAaHhVvZz]*)', m.group(1)):
                cmd = cm.group(1)
                args = [float(n) for n in re.findall(r'-?\d+\.?\d*', cm.group(2))]
                rel = cmd.islower() and cmd != 'z'; C = cmd.upper(); k = 0
                if C == 'M' and args:
                    x = (x + args[0]) if rel else args[0]
                    y = (y + args[1]) if rel else args[1]
                    xs.append(x); ys.append(y); k = 2; C = 'L'
                while k < len(args):
                    if C == 'L':
                        x = (x + args[k]) if rel else args[k]
                        y = (y + args[k+1]) if rel else args[k+1]
                        xs.append(x); ys.append(y); k += 2
                    elif C == 'H':
                        x = (x + args[k]) if rel else args[k]; xs.append(x); ys.append(y); k += 1
                    elif C == 'V':
                        y = (y + args[k]) if rel else args[k]; xs.append(x); ys.append(y); k += 1
                    elif C == 'C':
                        x = (x + args[k+4]) if rel else args[k+4]
                        y = (y + args[k+5]) if rel else args[k+5]
                        xs.append(x); ys.append(y); k += 6
                    elif C in ('S', 'Q'):
                        x = (x + args[k+2]) if rel else args[k+2]
                        y = (y + args[k+3]) if rel else args[k+3]
                        xs.append(x); ys.append(y); k += 4
                    elif C == 'T':
                        x = (x + args[k]) if rel else args[k]
                        y = (y + args[k+1]) if rel else args[k+1]
                        xs.append(x); ys.append(y); k += 2
                    elif C == 'Z': k = len(args) + 1
                    else: break
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None

_sil_bbox = _trace_default_silhouette_bbox(svg)
if _sil_bbox is None:
    raise RuntimeError("Could not find the default integration silhouette in human.svg")
SIL_X_MIN, SIL_Y_MIN, SIL_X_MAX, SIL_Y_MAX = _sil_bbox
print(f"[info] default silhouette bbox: "
      f"({SIL_X_MIN:.1f}, {SIL_Y_MIN:.1f}) to ({SIL_X_MAX:.1f}, {SIL_Y_MAX:.1f})  "
      f"size {SIL_X_MAX-SIL_X_MIN:.1f} × {SIL_Y_MAX-SIL_Y_MIN:.1f}")

# Now delete the original silhouette paths.
svg = re.sub(r'<path class="st17"[^>]*d="[^"]+"\s*/>\s*', '', svg)
svg = re.sub(r'<path class="st18"[^>]*d="[^"]+"\s*/>\s*', '', svg)

# Set detail placement target to the silhouette bbox top-left.
TARGET_X = SIL_X_MIN
TARGET_Y = SIL_Y_MIN

# Integration area bbox (for reference / chakra centroids etc.)
g10 = gate_positions[10]; g20 = gate_positions[20]
g34 = gate_positions[34]; g57 = gate_positions[57]
INTG_X_MIN = min(g10["cx"], g20["cx"], g34["cx"], g57["cx"]) - 20
INTG_X_MAX = max(g10["cx"], g20["cx"], g34["cx"], g57["cx"]) + 20
INTG_Y_MIN = min(g10["cy"], g20["cy"], g34["cy"], g57["cy"]) - 20
INTG_Y_MAX = max(g10["cy"], g20["cy"], g34["cy"], g57["cy"]) + 20
ANCHOR_X = (INTG_X_MIN + INTG_X_MAX) / 2
ANCHOR_Y = (INTG_Y_MIN + INTG_Y_MAX) / 2

# ---------- Tag chakras/centers with data-center ----------
# The 9 centers use class st121 (white fill + gold stroke). Match them to
# HD center names by bounding-box position.
# Order by y (top→bottom), then x, to identify:
#   Head (highest, small), Ajna, Throat, G, Heart (small, right of G),
#   Spleen (left), Solar Plexus (right), Sacral (below G), Root (bottom)

def _trace_path_points_local(d):
    x = y = 0.0; out = []
    for cm in re.finditer(r'([MmLlCcSsQqTtAaHhVvZz])([^MmLlCcSsQqTtAaHhVvZz]*)', d):
        cmd = cm.group(1)
        args = [float(n) for n in re.findall(r'-?\d+\.?\d*', cm.group(2))]
        rel = cmd.islower() and cmd != 'z'
        C = cmd.upper(); k = 0
        if C == 'M' and args:
            x = (x + args[0]) if rel else args[0]
            y = (y + args[1]) if rel else args[1]
            out.append((x, y)); k = 2; C = 'L'
        while k < len(args):
            if C == 'L':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'H':
                x = (x + args[k]) if rel else args[k]; out.append((x, y)); k += 1
            elif C == 'V':
                y = (y + args[k]) if rel else args[k]; out.append((x, y)); k += 1
            elif C == 'C':
                x = (x + args[k+4]) if rel else args[k+4]
                y = (y + args[k+5]) if rel else args[k+5]
                out.append((x, y)); k += 6
            elif C in ('S','Q'):
                x = (x + args[k+2]) if rel else args[k+2]
                y = (y + args[k+3]) if rel else args[k+3]
                out.append((x, y)); k += 4
            elif C == 'T':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'Z': k = len(args) + 1
            else: break
    return out

chakra_paths = []
for m in re.finditer(r'<path class="st121"[^>]*d="([^"]+)"[^>]*/>', svg):
    d = m.group(1)
    pts = _trace_path_points_local(d)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    if xs:
        chakra_paths.append({
            "full": m.group(0),
            "cx": (min(xs) + max(xs)) / 2,
            "cy": (min(ys) + max(ys)) / 2,
            "minx": min(xs), "maxx": max(xs),
            "miny": min(ys), "maxy": max(ys),
        })

# Assign each chakra by position (use gate positions as references)
# Build a scorer: for each of 9 centers, pick the chakra whose bbox best contains a known gate.
CENTER_REF_GATE = {
    "Head": 64,           # Head gate
    "Ajna": 47,           # Ajna gate
    "Throat": 23,         # Throat gate
    "G": 1,               # G-center gate
    "Heart": 51,          # Heart gate (Ego)
    "Spleen": 48,         # Spleen gate
    "Solar Plexus": 49,   # Solar Plexus gate
    "Sacral": 5,          # Sacral gate (non-integration, unambiguously Sacral)
    "Root": 60,           # Root gate
}
center_to_chakra = {}
for center, ref_gate in CENTER_REF_GATE.items():
    if ref_gate not in gate_positions: continue
    gx, gy = gate_positions[ref_gate]["cx"], gate_positions[ref_gate]["cy"]
    # Pick chakra whose bbox contains (gx, gy), else nearest by center distance
    best = None; best_dist = 1e9
    for i, cp in enumerate(chakra_paths):
        if cp["minx"] <= gx <= cp["maxx"] and cp["miny"] <= gy <= cp["maxy"]:
            best = i; best_dist = 0; break
        d = math.hypot(cp["cx"] - gx, cp["cy"] - gy)
        if d < best_dist:
            best_dist = d; best = i
    if best is not None:
        center_to_chakra[center] = best

# Rewrite st121 chakras with data-center attr
# (Note: by this point, some st121 elements may have additional classes from
# the gate-line fallback pass — e.g., the Spleen chakra got tagged as a
# gate-48 line. We must match st121 wherever it appears in the class attr,
# and carefully inject "chakra" + data-center without disturbing other tags.)
def _tag_chakra(m):
    full = m.group(0)
    d_m = re.search(r'\bd="([^"]+)"', full)
    if not d_m: return full
    pts = _trace_path_points_local(d_m.group(1))
    if not pts: return full
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx = (min(xs)+max(xs))/2; cy = (min(ys)+max(ys))/2
    # Match to the closest chakra in center_to_chakra
    best_name = None; best_dist = 1e9
    for name, idx in center_to_chakra.items():
        cp = chakra_paths[idx]
        d = math.hypot(cp["cx"] - cx, cp["cy"] - cy)
        if d < best_dist:
            best_dist = d; best_name = name
    if best_name is None:
        return full
    # Drop any accidentally-assigned gate-line class + data attrs (chakras are
    # NOT channel lines), then add chakra + data-center.
    new_cls = 'class="st121 chakra"'
    new = re.sub(r'class="[^"]*"', new_cls, full, count=1)
    new = re.sub(r'\s*data-line-gate="[^"]*"', '', new)
    new = re.sub(r'\s*data-line-side="[^"]*"', '', new)
    # Add data-center attribute after the class
    new = new.replace(new_cls, f'{new_cls} data-center="{best_name}"', 1)
    return new

# Match any <path> element whose class attribute contains "st121"
svg = re.sub(
    r'<path[^>]*\bclass="[^"]*\bst121\b[^"]*"[^>]*d="[^"]+"[^>]*/>',
    _tag_chakra, svg,
)
details_svg = DETAILS_SRC.read_text()
details_body = details_svg[details_svg.find('</style>')+len('</style>'):]
details_body = details_body[:details_body.rfind('</svg>')].strip()

# Rename classes st0..st4 → ds0..ds4 to avoid conflict with human.svg
for i in range(10):
    details_body = re.sub(f'class="st{i}"', f'class="ds{i}"', details_body)

# Walk top-level <g> groups
depth = 0
groups = []
i = 0
current_start = None
while i < len(details_body):
    if details_body[i:i+3] in ('<g>', '<g '):
        if depth == 0: current_start = i
        depth += 1
        i = details_body.find('>', i) + 1
    elif details_body[i:i+4] == '</g>':
        depth -= 1
        if depth == 0 and current_start is not None:
            groups.append(details_body[current_start:i+4])
            current_start = None
        i += 4
    else:
        i += 1

artboards = [g for g in groups if len(g) > 1000]
assert len(artboards) == 256, f"expected 256 artboards, got {len(artboards)}"

COL_CENTERS = [
    14.6, 186.9, 359.8, 532.8, 705.0, 877.9, 1050.4, 1223.2,
    1395.9, 1568.3, 1741.2, 1913.8, 2082.5, 2258.8, 2431.5, 2603.8,
]
ROW_CENTERS = [44.2 + i * 299.0 for i in range(16)]

def assign_cell(min_x, min_y):
    c = min(range(16), key=lambda i: abs(COL_CENTERS[i] - min_x))
    r = min(range(16), key=lambda i: abs(ROW_CENTERS[i] - min_y))
    return r, c

def extract_abs_points(d):
    x = y = 0.0
    out = []
    for cm in re.finditer(r'([MmLlCcSsQqTtAaHhVvZz])([^MmLlCcSsQqTtAaHhVvZz]*)', d):
        cmd = cm.group(1)
        args = [float(n) for n in re.findall(r'-?\d+\.?\d*', cm.group(2))]
        rel = cmd.islower() and cmd != 'z'
        C = cmd.upper(); k = 0
        if C == 'M' and args:
            x = (x + args[0]) if rel else args[0]
            y = (y + args[1]) if rel else args[1]
            out.append((x, y)); k = 2; C = 'L'
        while k < len(args):
            if C == 'L':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'H':
                x = (x + args[k]) if rel else args[k]
                out.append((x, y)); k += 1
            elif C == 'V':
                y = (y + args[k]) if rel else args[k]
                out.append((x, y)); k += 1
            elif C == 'C':
                x = (x + args[k+4]) if rel else args[k+4]
                y = (y + args[k+5]) if rel else args[k+5]
                out.append((x, y)); k += 6
            elif C in ('S', 'Q'):
                x = (x + args[k+2]) if rel else args[k+2]
                y = (y + args[k+3]) if rel else args[k+3]
                out.append((x, y)); k += 4
            elif C == 'T':
                x = (x + args[k]) if rel else args[k]
                y = (y + args[k+1]) if rel else args[k+1]
                out.append((x, y)); k += 2
            elif C == 'Z': k = len(args) + 1
            else: break
    return out

def artboard_bbox_min(g_text):
    xs, ys = [], []
    for m in re.finditer(r'd="([^"]+)"', g_text):
        for x, y in extract_abs_points(m.group(1)):
            xs.append(x); ys.append(y)
    return (min(xs), min(ys)) if xs else (0, 0)

# ab_info holds each artboard's bbox-min in details.svg coordinates.
# TARGET_X / TARGET_Y were set earlier from the original st17+st18 silhouette
# bbox-min in human.svg. Do NOT override them here.
ab_info = []
for idx, ab in enumerate(artboards):
    bb_x, bb_y = artboard_bbox_min(ab)
    r, c = assign_cell(bb_x, bb_y)
    ab_info.append({"idx": idx, "bb_x": bb_x, "bb_y": bb_y, "row": r, "col": c, "text": ab})

cell_to_artboard = {}
for a in ab_info:
    dx = TARGET_X - a["bb_x"]
    dy = TARGET_Y - a["bb_y"]
    n = a["row"] * 16 + a["col"] + 1
    cell_to_artboard[n] = {
        "row": a["row"], "col": a["col"], "dx": dx, "dy": dy,
        "group": a["text"],
    }

# Build injection block
injection = ['<g id="details-layer">']
for n in range(1, 257):
    info = cell_to_artboard.get(n)
    if info is None: continue
    inner = info["group"]
    inner_stripped = re.sub(r'^<g[^>]*>\s*', '', inner, count=1)
    inner_stripped = re.sub(r'\s*</g>$', '', inner_stripped, count=1)
    injection.append(
        f'<g class="detail-part" data-detail="{n}" '
        f'transform="translate({info["dx"]:.2f} {info["dy"]:.2f})">'
        f'{inner_stripped}</g>'
    )
injection.append('</g>')
injection_text = '\n'.join(injection)

# ---------- Reorder for proper z-stack ----------
# Desired z-order (bottom → top):
#   channel-lines < chakras (centers) < details-layer < gate-circles < gate-digits
#
# Approach: extract chakras, gate-circles, gate-texts in that order.
# Then inject back: chakras → details-layer → gate-circles → gate-digits.

chakra_matches = list(re.finditer(
    r'<path[^>]*class="st121 chakra"[^>]*/>', svg,
))
chakra_html = [m.group(0) for m in chakra_matches]
for m in reversed(chakra_matches):
    svg = svg[:m.start()] + svg[m.end():]

gate_circle_matches = list(re.finditer(
    r'<(?:circle|ellipse)[^>]*class="st122 gate-circle"[^>]*/>',
    svg,
))
gate_circle_html = [m.group(0) for m in gate_circle_matches]
for m in reversed(gate_circle_matches):
    svg = svg[:m.start()] + svg[m.end():]

gate_text_matches = list(re.finditer(
    r'<text[^>]*class="st123 st124 gate-text"[^>]*>\d+</text>',
    svg,
))
gate_text_html = [m.group(0) for m in gate_text_matches]
for m in reversed(gate_text_matches):
    svg = svg[:m.start()] + svg[m.end():]

layered = (
    # Integration detail layer goes FIRST (bottom of stack) so the Spleen,
    # Throat, G-center, Sacral chakras can render ON TOP of it, not below.
    injection_text
    + '\n<g id="chakras-layer">' + "".join(chakra_html) + '</g>'
    + '\n<g id="gate-circles-layer">' + "".join(gate_circle_html) + '</g>'
    + '\n<g id="gate-texts-layer">'   + "".join(gate_text_html)   + '</g>'
)
svg = svg.replace('</svg>', layered + '\n</svg>', 1)

# ---------- Extend gate-line tagging: same-column continuations ----------
# Each channel line often has a SHORT upper rect (marker color) plus a LONGER
# lower rect (continuation) in the exact same x column. Tag the continuation
# rects with the same gate/side as their column-partner upper rect.

# Collect tagged rects: (x, gate, side)
tagged_columns = []  # list of {x: float, gate: int, side: str}
for m in re.finditer(
    r'<rect[^>]*?\bclass="st\d+[^"]*gate-line[^"]*"[^>]*?data-line-gate="(\d+)"[^>]*?data-line-side="(dark|light)"[^>]*?/>',
    svg,
):
    attrs = m.group(0)
    x_m = re.search(r'\bx="([\d.]+)"', attrs)
    if not x_m: continue
    tagged_columns.append({
        "x": float(x_m.group(1)),
        "gate": int(m.group(1)),
        "side": m.group(2),
    })

def _tag_continuation(m):
    full = m.group(0)
    if "gate-line" in full: return full
    # Must be a potentially-colored rule-color rect. Check class.
    cls_m = re.search(r'class="(st\d+)([^"]*)"', full)
    if not cls_m: return full
    cls = cls_m.group(1)
    # Also match st71 (#662D91 design purple) and st114 (#262262 personality blue)
    # because the ROOT column lower-segments use these as "default already activated" colors.
    ROOT_CONT_CLASSES = {"st71", "st114"}
    rule_colors = set()
    for rule in RULES.values():
        rule_colors.add(rule["dark"].upper())
        rule_colors.add(rule["light"].upper())
    color = class_to_color.get(cls, "").upper()
    if color not in rule_colors and cls not in ROOT_CONT_CLASSES:
        return full

    x_m = re.search(r'\bx="([\d.]+)"', full)
    y_m = re.search(r'\by="([\d.]+)"', full)
    if not (x_m and y_m): return full
    x = float(x_m.group(1)); y = float(y_m.group(1))

    # Find any column-match from tagged_columns within 1 px of x
    best = None; best_dx = 1.5
    for col in tagged_columns:
        dx = abs(col["x"] - x)
        if dx < best_dx:
            best_dx = dx; best = col
    if best is None: return full

    # Add data-line-gate + data-line-side to this continuation rect
    return full.replace(
        f'class="{cls}{cls_m.group(2)}"',
        f'class="{cls}{cls_m.group(2)} gate-line" '
        f'data-line-gate="{best["gate"]}" data-line-side="{best["side"]}"',
        1,
    )

svg = re.sub(r'<rect[^>]*?/>', _tag_continuation, svg)

# Tag untagged "leftover" elements: any rect/path still using a gate-rule color
# but not already a .gate-line or .chakra. These were extra elements from
# shared classes in the SVG export. Adding .leftover-line makes them render
# white like other inactive channel lines.
rule_colors = set()
for rule in RULES.values():
    rule_colors.add(rule["dark"].upper())
    rule_colors.add(rule["light"].upper())

def _tag_leftover(m):
    full = m.group(0)
    cls_m = re.search(r'class="(st\d+)([^"]*)"', full)
    if not cls_m: return full
    cls = cls_m.group(1)
    rest = cls_m.group(2)
    if "gate-line" in rest or "chakra" in rest:
        return full
    color = class_to_color.get(cls, "").upper()
    if color not in rule_colors:
        return full
    return full.replace(
        f'class="{cls}{rest}"',
        f'class="{cls}{rest} leftover-line"', 1,
    )

svg = re.sub(r'<(?:rect|path|polygon)[^>]*class="st\d+[^"]*"[^>]*/>', _tag_leftover, svg)
rule_colors = set()
for rule in RULES.values():
    rule_colors.add(rule["dark"].upper())
    rule_colors.add(rule["light"].upper())

def _tag_leftover(m):
    full = m.group(0)
    cls_m = re.search(r'class="(st\d+)([^"]*)"', full)
    if not cls_m: return full
    cls = cls_m.group(1)
    rest = cls_m.group(2)
    if "gate-line" in rest or "chakra" in rest:
        return full
    color = class_to_color.get(cls, "").upper()
    if color not in rule_colors:
        return full
    # Add leftover-line class
    return full.replace(
        f'class="{cls}{rest}"',
        f'class="{cls}{rest} leftover-line"', 1,
    )

svg = re.sub(r'<(?:rect|path|polygon)[^>]*class="st\d+[^"]*"[^>]*/>', _tag_leftover, svg)

# ---------- CSS injection ----------
activation_css = f"""
    /* ── channel-line per-gate recoloring ──
       Default state: ALL inactive gate-lines render WHITE (#FFFFFF).
       The source SVG assigns unique dark/light marker colors per gate, but
       those are used only to identify which elements belong to which gate.
       Once tagged, they render white until their gate is activated.

       Activation overrides (see per-gate rules further below):
         .active-p-N  -> both lines become gate N's personality-blue
         .active-d-N  -> both lines become design purple (#67308F)
         .active-b-N  -> dark line blue, light line purple  */
    .gate-line       {{ fill: #FFFFFF !important; transition: fill .25s; }}
    /* Also white-out any stray leftover rule-color elements (from shared
       classes where only one of the pair got tagged). */
    .leftover-line   {{ fill: #FFFFFF !important; }}

    /* details.svg classes */
    .ds0 {{ fill:#FFFFFF; }}
    .ds1 {{ fill:#292562; }}   /* personality (blue) */
    .ds2 {{ fill:#67308F; }}   /* design (purple) */
    .ds3 {{ fill:#C3996C; }}   /* gold */
    .ds4 {{ fill:#010101; }}

    /* gate activation */
    circle.gate-circle.active,
    ellipse.gate-circle.active {{ fill: #111; transition: fill .2s; }}
    text.gate-text.active     {{ fill: #ffffff; }}

    /* chakras / centers: default white, activate via .center-active-* classes */
    .chakra {{ transition: fill .25s; }}
    svg.center-active-Head          .chakra[data-center="Head"]         {{ fill: #FFFF00; }}
    svg.center-active-Ajna          .chakra[data-center="Ajna"]         {{ fill: #A7DC2A; }}
    svg.center-active-Throat        .chakra[data-center="Throat"]       {{ fill: #8B4513; }}
    svg.center-active-G             .chakra[data-center="G"]            {{ fill: #FFFF99; }}
    svg.center-active-Heart         .chakra[data-center="Heart"]        {{ fill: #FF0000; }}
    svg.center-active-Spleen        .chakra[data-center="Spleen"]       {{ fill: #8B5A3C; }}
    svg.center-active-SolarPlexus   .chakra[data-center="Solar Plexus"] {{ fill: #C17A3B; }}
    svg.center-active-Sacral        .chakra[data-center="Sacral"]       {{ fill: #FF0000; }}
    svg.center-active-Root          .chakra[data-center="Root"]         {{ fill: #8B5A3C; }}

    /* detail variations */
    .detail-part  {{ visibility: hidden; }}
"""
detail_rules = "\n".join(
    f'    svg.detail-on-{n} .detail-part[data-detail="{n}"] {{ visibility: visible; }}'
    for n in range(1, 257)
)

# Per-gate channel-line recoloring: for each rule, add selectors that
# change the fill of its dark and light elements when .active-p / .active-d / .active-both
per_gate_css = []
for gate, rule in RULES.items():
    p_blue = rule["p_blue"]
    purple = DESIGN_PURPLE
    # Personality only: both lines → p_blue
    per_gate_css.append(
        f'    .active-p-{gate}  .gate-line[data-line-gate="{gate}"] '
        f'{{ fill: {p_blue} !important; }}'
    )
    # Design only: both lines → purple
    per_gate_css.append(
        f'    .active-d-{gate}  .gate-line[data-line-gate="{gate}"] '
        f'{{ fill: {purple} !important; }}'
    )
    # Both: dark line → p_blue, light line → purple
    per_gate_css.append(
        f'    .active-b-{gate}  .gate-line[data-line-gate="{gate}"][data-line-side="dark"]  '
        f'{{ fill: {p_blue} !important; }}'
    )
    per_gate_css.append(
        f'    .active-b-{gate}  .gate-line[data-line-gate="{gate}"][data-line-side="light"] '
        f'{{ fill: {purple} !important; }}'
    )

per_gate_block = "\n".join(per_gate_css)

full_css = activation_css + "\n" + detail_rules + "\n" + per_gate_block
svg = svg.replace("</style>", full_css + "\n</style>", 1)

# ---------- Write outputs ----------
DST.write_text(svg)
POS.write_text(json.dumps(gate_positions, indent=2))
COL.write_text(json.dumps({str(g): rule for g, rule in gate_colors_info.items()}, indent=2))

detail_positions = {}
for n, info in cell_to_artboard.items():
    detail_positions[n] = {
        "row": info["row"], "col": info["col"],
        "dx": info["dx"], "dy": info["dy"],
    }
DET.write_text(json.dumps({str(k): v for k, v in sorted(detail_positions.items())}, indent=2))

print(f"wrote {DST} ({len(svg):,} chars)")
print(f"wrote {POS}  ({len(gate_positions)} gates)")
print(f"wrote {COL}  ({len(gate_colors_info)} gate color rules)")
print(f"wrote {DET}  ({len(detail_positions)} detail cells)")

covered = sum(1 for v in gate_colors_info.values() if v.get("dark_class"))
print(f"Gate lines tagged: {covered}/60")
