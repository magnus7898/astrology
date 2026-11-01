"""numcalc.py — Matrix of Destiny and Pythagorean square, computed on the server.

Exact ports of the formulas in matrix.html (calculate, calculateCompat, draw's age points,
renderChakra, the line panels) and pythagoras.html (computeModes, computeCurves, renderVedic).
Cross-validated against the browser code on every date (see the commit message).

Registered from app.py:  init_numcalc(app, ACC)   (ACC = the dict init_accounts returns)

  POST /api/matrix          {dd, mm, yyyy, method: 1|2|3, names?: {gvari, saxeli, mamis, dedis}}
  POST /api/matrix/compat   {p1: {dd,mm,yyyy}, p2: {dd,mm,yyyy}}
  POST /api/matrix/names    {gvari, saxeli, mamis, dedis}  → Georgian letter numbers (method 3 preview)
  POST /api/pythagoras      {dd, mm, yyyy}            (numbers or zero-padded strings)
  POST /api/matrix/batch    {dates: [{dd,mm,yyyy}…], method}         ≤ 200 dates
  POST /api/pythagoras/batch {dates: [{dd,mm,yyyy}…]}                 ≤ 200 dates

Pro pages: when the admin marks matrix.html / pythagoras.html as Pro (plan_feature), a free
account gets 402 with {pro: true}; the page shows the lock.
"""
from flask import jsonify, request

# ───────────────────────── Matrix of Destiny ─────────────────────────
GEO = {'ა': 1, 'ბ': 2, 'გ': 3, 'დ': 4, 'ე': 5, 'ვ': 6, 'ზ': 7, 'ჱ': 8, 'თ': 9, 'ი': 1, 'კ': 2, 'ლ': 3, 'მ': 4,
       'ნ': 5, 'ჲ': 6, 'ო': 7, 'პ': 8, 'ჟ': 9, 'რ': 1, 'ს': 2, 'ტ': 3, 'უ': 4, 'ფ': 5, 'ქ': 6, 'ღ': 7, 'ყ': 8,
       'შ': 9, 'ჩ': 1, 'ც': 2, 'ძ': 3, 'წ': 4, 'ჭ': 5, 'ხ': 6, 'ჯ': 7, 'ჰ': 8}


def r22(n):
    while n > 22:
        n = sum(int(c) for c in str(n))
    return n


def geo_num(s):
    if not s:
        return 0
    return r22(sum(GEO.get(c, 0) for c in s))


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def validate_date(dd, mm, yyyy):
    if not isinstance(yyyy, int) or yyyy < 1000 or yyyy > 2100:
        return 'წელი უნდა იყოს 1000–2100'
    if not isinstance(mm, int) or mm < 1 or mm > 12:
        return 'თვე უნდა იყოს 1–12'
    dim = [31, 29 if _leap(yyyy) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mm - 1]
    if not isinstance(dd, int) or dd < 1 or dd > dim:
        return f'დღე უნდა იყოს 1–{dim} ({mm} თვისთვის)'
    return None


def _fmt_age(n):
    return str(int(n)) if n == int(n) else f'{n:.1f}'.replace('.', ',')


def _sub_energies(a, b):
    d4 = r22(a + b); d2 = r22(a + d4); d1 = r22(a + d2); d3 = r22(d2 + d4)
    d6 = r22(d4 + b); d5 = r22(d4 + d6); d7 = r22(d6 + b)
    return [d1, d2, d3, d4, d5, d6, d7]


def _sub_labels(s):
    f = _fmt_age
    return [f(s) + '-' + f(s + 1.5), f(s + 1.5) + '-' + f(s + 2.5), f(s + 2.5) + '-' + f(s + 3), f(s + 4),
            f(s + 5) + '-' + f(s + 6.5), f(s + 6.5) + '-' + f(s + 7.5), f(s + 7.5) + '-' + f(s + 8)]


SUB_MID = [0.75, 2, 2.75, 4, 5.75, 7, 7.75]


def age_points(v):
    """The 8 × 7 points on the age circle + the 8 decade anchors, as draw() builds them."""
    anch = [(v['L3'], v['TL3']), (v['TL3'], v['T3']), (v['T3'], v['TR3']), (v['TR3'], v['R3']),
            (v['R3'], v['BR3']), (v['BR3'], v['B3']), (v['B3'], v['BL3']), (v['BL3'], v['L3'])]
    starts = [1, 11, 21, 31, 41, 51, 61, 71]
    pts = []
    for sec in range(8):
        labels, ens = _sub_labels(starts[sec]), _sub_energies(*anch[sec])
        for d in range(7):
            pts.append({'sec': sec, 'd': d, 'label': labels[d], 'energy': ens[d],
                        'age': starts[sec] - 1 + SUB_MID[d], 'mid': d == 3})
    corner = [v['L3'], v['TL3'], v['T3'], v['TR3'], v['R3'], v['BR3'], v['B3'], v['BL3']]
    anchors = [{'sec': i, 'label': str(i * 10), 'energy': corner[i], 'age': i * 10} for i in range(8)]
    return pts, anchors


CHAKRA_NAMES = {
    'row-sahasrara': 'საჰასრარა (გვირგვინი)', 'row-ajna': 'აჯნა (მესამე თვალი)', 'row-vishudha': 'ვიშუდჰა (ყელის ჩაკრა)',
    'row-lelia': 'დალი (ქალის ხაზი)', 'row-lada': 'კოპალა (მამაკაცის ხაზი)', 'row-anahata': 'ანაჰატა (გულის ჩაკრა)',
    'row-manipura': 'მანიპურა (მზის წნული)', 'row-svadhistana': 'სვადჰისტანა (საკრალური)', 'row-muladhara': 'მულადჰარა (ფუძის ჩაკრა)'}


def chakra_table(v, method):
    if method == 3:
        rows = [('row-sahasrara', v['T3'], v['L3']), ('row-ajna', v['T2'], v['L2']), ('row-vishudha', v['T1'], v['L1']),
                ('row-lelia', v['TR3'], v['BL3']), ('row-lada', v['TL3'], v['BR3']), ('row-anahata', v['Cv'], v['m3Cv2']),
                ('row-manipura', v['B1'], v['R1']), ('row-svadhistana', v['B2'], v['R2']), ('row-muladhara', v['B3'], v['R3'])]
    else:
        rows = [('row-sahasrara', v['T3'], v['L3']), ('row-ajna', v['T2'], v['L2']), ('row-vishudha', v['T1'], v['L1']),
                ('row-anahata', v['G2'], v['G1']), ('row-manipura', v['Cv'], v['Cv']),
                ('row-svadhistana', v['B1'], v['R1']), ('row-muladhara', v['B3'], v['R3'])]
    out, se, sl, ss = [], 0, 0, 0
    for cls, e, l in rows:
        e, l = e or 0, l or 0
        sm = r22(e + l)
        se += e; sl += l; ss += sm
        out.append({'cls': cls, 'name': CHAKRA_NAMES[cls], 'e': e, 'l': l, 'sum': sm})
    return {'rows': out, 'total': [r22(se), r22(sl), r22(ss)]}


def line_panels(v):
    sT, sB = r22(v['T3'] + v['B3']), r22(v['R3'] + v['L3'])
    sM = r22(sT + sB)
    oT, oB = r22(v['TL3'] + v['BR3']), r22(v['TR3'] + v['BL3'])
    oM = r22(oT + oB)
    return {'tl3': v['TL3'], 'br3': v['BR3'], 'male_sum': r22(v['TL3'] + v['BR3']),
            'tr3': v['TR3'], 'bl3': v['BL3'], 'fem_sum': r22(v['TR3'] + v['BL3']),
            'soul_top': sT, 'soul_bot': sB, 'soul_mid': sM, 'soc_top': oT, 'soc_bot': oB, 'soc_mid': oM,
            'misia': r22(sM + oM)}


def matrix_values(dd, mm, yyyy, method=1, names=None):
    """calculate() for methods 1–3. names (method 3): {gvari, saxeli, mamis, dedis}."""
    L3, T3, R3 = r22(dd), r22(mm), r22(yyyy)
    B3 = r22(L3 + T3 + R3)
    Cv = r22(L3 + T3 + R3 + B3)
    TL3, TR3, BR3, BL3 = r22(L3 + T3), r22(T3 + R3), r22(R3 + B3), r22(B3 + L3)
    m3Cv2 = 0
    if method == 3:
        n = names or {}
        gv, sx, ma, de = (geo_num(n.get(k) or '') for k in ('gvari', 'saxeli', 'mamis', 'dedis'))
        if not (gv or sx or ma or de):
            raise ValueError('გთხოვთ შეიყვანოთ სახელი, გვარი ან სხვა მონაცემი')
        if gv: TL3 = gv
        if sx: TR3 = sx
        if ma: BR3 = ma
        if de: BL3 = de
        m3Cv2 = r22(TL3 + TR3 + BR3 + BL3)
    RC1 = r22(TL3 + TR3 + BR3 + BL3)
    RC2 = r22(RC1 + Cv)
    B1 = r22(Cv + B3); B2 = r22(B1 + B3); R1 = r22(Cv + R3); R2 = r22(R1 + R3)
    L1 = r22(Cv + L3); L2 = r22(L1 + L3); T1 = r22(Cv + T3); T2 = r22(T1 + T3)
    G1 = r22(L1 + Cv); G2 = r22(T1 + Cv)
    dCv = RC1 if method == 1 else Cv
    TL1 = r22(TL3 + dCv); TL2 = r22(TL1 + TL3); TR1 = r22(TR3 + dCv); TR2 = r22(TR1 + TR3)
    BR1 = r22(BR3 + dCv); BR2 = r22(BR1 + BR3); BL1 = r22(BL3 + dCv); BL2 = r22(BL1 + BL3)
    W2 = r22(B1 + R1); W1 = r22(B1 + W2); W3 = r22(R1 + W2)
    return dict(L3=L3, T3=T3, R3=R3, B3=B3, Cv=Cv, B1=B1, B2=B2, R1=R1, R2=R2, L1=L1, L2=L2, T1=T1, T2=T2,
                G1=G1, G2=G2, TL3=TL3, TR3=TR3, BR3=BR3, BL3=BL3, RC1=RC1, RC2=RC2, TL1=TL1, TL2=TL2,
                TR1=TR1, TR2=TR2, BR1=BR1, BR2=BR2, BL1=BL1, BL2=BL2, W1=W1, W2=W2, W3=W3, m3Cv2=m3Cv2)


def matrix_full(dd, mm, yyyy, method=1, names=None):
    v = matrix_values(dd, mm, yyyy, method, names)
    pts, anchors = age_points(v)
    return {'method': method, 'values': v, 'showRC': method != 2, 'compat': False,
            'lines': line_panels(v), 'chakra': chakra_table(v, method), 'ages': pts, 'anchors': anchors}


def _base(dd, mm, yyyy):
    L3, T3, R3 = r22(dd), r22(mm), r22(yyyy)
    return {'L3': L3, 'T3': T3, 'R3': R3, 'B3': r22(L3 + T3 + R3)}


def matrix_compat(p1, p2):
    v1, v2 = _base(*p1), _base(*p2)
    cv1 = r22(v1['L3'] + v1['T3'] + v1['R3'] + v1['B3'])
    cv2 = r22(v2['L3'] + v2['T3'] + v2['R3'] + v2['B3'])
    L3 = r22(v1['L3'] + v2['L3']); T3 = r22(v1['T3'] + v2['T3']); R3 = r22(v1['R3'] + v2['R3'])
    B3 = r22(v1['B3'] + v2['B3']); Cv = r22(cv1 + cv2)
    TL3 = r22(r22(v1['T3'] + v1['L3']) + r22(v2['T3'] + v2['L3']))
    TR3 = r22(r22(v1['T3'] + v1['R3']) + r22(v2['T3'] + v2['R3']))
    BR3 = r22(r22(v1['B3'] + v1['R3']) + r22(v2['B3'] + v2['R3']))
    BL3 = r22(r22(v1['B3'] + v1['L3']) + r22(v2['B3'] + v2['L3']))
    RC1 = r22(TL3 + TR3 + BR3 + BL3); RC2 = r22(RC1 + Cv)
    B1 = r22(Cv + B3); B2 = r22(B1 + B3); R1 = r22(Cv + R3); R2 = r22(R1 + R3)
    L1 = r22(Cv + L3); L2 = r22(L1 + L3); T1 = r22(Cv + T3); T2 = r22(T1 + T3)
    G1 = r22(L1 + Cv); G2 = r22(T1 + Cv)
    W2 = r22(B1 + R1); W1 = r22(B1 + W2); W3 = r22(R1 + W2)
    v = dict(L3=L3, T3=T3, R3=R3, B3=B3, Cv=Cv, B1=B1, B2=B2, R1=R1, R2=R2, L1=L1, L2=L2, T1=T1, T2=T2,
             G1=G1, G2=G2, TL3=TL3, TR3=TR3, BR3=BR3, BL3=BL3, RC1=RC1, RC2=RC2,
             TL1=0, TL2=0, TR1=0, TR2=0, BR1=0, BR2=0, BL1=0, BL2=0, W1=W1, W2=W2, W3=W3, m3Cv2=0)
    pts, anchors = age_points(v)
    return {'method': 4, 'values': v, 'showRC': False, 'compat': True, 'ages': pts, 'anchors': anchors}


# ───────────────────────── Pythagorean square ─────────────────────────
def _digits(n):
    return [int(c) for c in str(abs(n))]


def _sumd(n):
    return sum(_digits(n))


def pyth_modes(day, month, year):
    """computeModes(day, month, year) with zero-padded strings 'DD', 'MM', 'YYYY'."""
    birth = [int(c) for c in day + month + year]
    A = sum(birth)
    fd = int(day[0]) if day[0] != '0' else int(day[1])
    cB, cC = _sumd(A), abs(A - 2 * fd)
    cD = _sumd(cC)
    classic = {'disp': [str(A), str(cB), str(cC), str(cD)], 'extra': _digits(A) + _digits(cB) + _digits(cC) + _digits(cD), 'note': ''}
    if int(year) >= 2000:
        C = A + 19; D = _sumd(C)
        corrected = {'disp': [str(A), '+19', str(C), str(D)], 'extra': _digits(A) + [1, 9] + _digits(C) + _digits(D), 'note': 'XXI საუკუნე · +19'}
    else:
        C = A - 2; D = _sumd(C)
        corrected = {'disp': [str(A), '−2', str(C), str(D)], 'extra': _digits(A) + [2] + _digits(C) + _digits(D), 'note': 'XX საუკუნე · −2'}
    kA = abs(A - 9); kB = _sumd(kA); kC = abs(kA - 2 * fd); kD = _sumd(kC)
    crisis = {'disp': [str(kA), str(kB), str(kC), str(kD)], 'extra': _digits(kA) + _digits(kB) + _digits(kC) + _digits(kD),
              'note': f'|{A}−9| = {kA} · |{kA}−{2 * fd}| = {kC}'}
    for m in (classic, corrected, crisis):
        cnt = {str(k): 0 for k in range(1, 10)}
        for d in birth + m['extra']:
            if 1 <= d <= 9:
                cnt[str(d)] += 1
        m['count'] = cnt
    return {'classic': classic, 'corrected': corrected, 'crisis': crisis}


def _pad7(ds):
    o, i = list(ds), 0
    while len(o) < 7:
        o.append(ds[i % len(ds)]); i += 1
    return o


def pyth_curves(dd, mm, yyyy):
    z = lambda s: s.replace('0', '1')
    life = int(dd + mm) * int(yyyy)
    will = int(z(dd + mm)) * int(z(yyyy))
    fate = int(dd) * int(mm) * int(yyyy)
    dig = lambda n: _pad7([int(c) for c in str(n)])
    return {'life': {'n': life, 'f': f'{dd + mm} × {yyyy}', 'd': dig(life)},
            'will': {'n': will, 'f': f'{z(dd + mm)} × {z(yyyy)}', 'd': dig(will)},
            'fate': {'n': fate, 'f': f'{int(dd)} × {int(mm)} × {yyyy}', 'd': dig(fate)},
            'year0': int(yyyy)}


def _vdsum(s):
    n = sum(int(c) for c in s)
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


def pyth_full(dd, mm, yyyy):
    return {'modes': pyth_modes(dd, mm, yyyy), 'curves': pyth_curves(dd, mm, yyyy),
            'vedic': {'psychic': _vdsum(dd), 'destiny': _vdsum(dd + mm + yyyy)}}


# ───────────────────────── HTTP ─────────────────────────
def _int(x):
    try:
        return int(str(x).strip())
    except (TypeError, ValueError):
        return None


def _date(d):
    return _int(d.get('dd')), _int(d.get('mm')), _int(d.get('yyyy'))


def init_numcalc(app, ACC):
    PlanFeature, plan_of, current_user = ACC['PlanFeature'], ACC['plan_of'], ACC['current_user']

    def pro_block(page):
        """402 if the admin marked this page Pro and the caller is not Pro / admin."""
        f = PlanFeature.query.filter(PlanFeature.key.ilike(page), PlanFeature.pro_only.is_(True)).first()
        if not f:
            return None
        u, m = current_user()
        if u and (u.role == 'admin' or plan_of(m) == 'pro'):
            return None
        return jsonify(error='ეს გამოთვლა ხელმისაწვდომია Pro ანგარიშით', pro=True), 402

    @app.route('/api/matrix', methods=['POST'])
    def api_matrix():
        blk = pro_block('matrix.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        dd, mm, yyyy = _date(d)
        err = validate_date(dd, mm, yyyy)
        if err:
            return jsonify(error='თარიღი არასწორია: ' + err), 400
        method = _int(d.get('method')) or 1
        if method not in (1, 2, 3):
            return jsonify(error='method'), 400
        try:
            return jsonify(matrix_full(dd, mm, yyyy, method, d.get('names')))
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.route('/api/matrix/names', methods=['POST'])
    def api_matrix_names():
        d = request.get_json(silent=True) or {}
        return jsonify({k: geo_num(str(d.get(k) or '')[:120]) for k in ('gvari', 'saxeli', 'mamis', 'dedis')})

    @app.route('/api/matrix/compat', methods=['POST'])
    def api_matrix_compat():
        blk = pro_block('matrix.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        p1, p2 = _date(d.get('p1') or {}), _date(d.get('p2') or {})
        for i, p in enumerate((p1, p2)):
            err = validate_date(*p)
            if err:
                return jsonify(error=('პირველი' if i == 0 else 'მეორე') + ' პიროვნების თარიღი არასწორია: ' + err), 400
        return jsonify(matrix_compat(p1, p2))

    @app.route('/api/matrix/batch', methods=['POST'])
    def api_matrix_batch():
        blk = pro_block('matrix.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        method = _int(d.get('method')) or 1
        me = _date(d['me']) if isinstance(d.get('me'), dict) else None
        out = []
        for x in (d.get('dates') or [])[:200]:
            dd, mm, yyyy = _date(x if isinstance(x, dict) else {})
            if validate_date(dd, mm, yyyy) or method not in (1, 2):
                out.append(None)
                continue
            v = matrix_values(dd, mm, yyyy, method)
            v['MISSION'] = line_panels(v)['misia']
            if me and not validate_date(*me):
                cv = matrix_compat(me, (dd, mm, yyyy))['values']
                v['compat'] = {k: cv[k] for k in ('Cv', 'B3', 'B2', 'B1')}
            out.append(v)
        return jsonify(out)

    def pyth_args(x):
        dd, mm, yyyy = _date(x)
        if dd is None or mm is None or yyyy is None or not (1 <= mm <= 12) or not (1 <= dd <= 31) or not (1 <= yyyy <= 9999):
            return None
        return f'{dd:02d}', f'{mm:02d}', f'{yyyy:04d}'

    @app.route('/api/pythagoras', methods=['POST'])
    def api_pythagoras():
        blk = pro_block('pythagoras.html')
        if blk:
            return blk
        a = pyth_args(request.get_json(silent=True) or {})
        if not a:
            return jsonify(error='შეიყვანე თარიღი ფორმატით: DD/MM/YYYY'), 400
        return jsonify(pyth_full(*a))

    init_numcalc_stats(app, pro_block)

    @app.route('/api/pythagoras/batch', methods=['POST'])
    def api_pythagoras_batch():
        blk = pro_block('pythagoras.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        out = []
        for x in (d.get('dates') or [])[:200]:
            a = pyth_args(x if isinstance(x, dict) else {})
            out.append({k: v['count'] for k, v in pyth_modes(*a).items()} if a else None)
        return jsonify(out)


# ═══════════════════ statistics engines (moved from the browser) ═══════════════════
import gzip as _gzip
import json as _json
from functools import lru_cache

try:
    import numpy as np
except ImportError:          # numpy is in requirements.txt; keep import errors readable
    np = None

# ── Pythagoras: every date of a year span at once (mirrors pythagoras_plus.js scanYears) ──
_DIM_LEAP = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
LINE_DIG = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (1, 4, 7), (2, 5, 8), (3, 6, 9), (3, 5, 7), (1, 5, 9)]


def _digit_counts(n):
    e = [0] * 10
    n = abs(n)
    while n:
        e[n % 10] += 1
        n //= 10
    return e


@lru_cache(maxsize=1)
def _dm_tables():
    C, S, F, L = [], [], [], []
    for m in range(1, 13):
        for d in range(1, _DIM_LEAP[m - 1] + 1):
            e = _digit_counts(d)
            for i, x in enumerate(_digit_counts(m)):
                e[i] += x
            C.append(e); S.append(_sumd(d) + _sumd(m)); F.append(d if d < 10 else d // 10)
            L.append(1 if (m == 2 and d == 29) else 0)
    return np.array(C, np.int16), np.array(S, np.int32), np.array(F, np.int32), np.array(L, bool)


@lru_cache(maxsize=4)
def _ex_table(mode):
    T = np.zeros((80, 10, 2, 10), np.int16)
    for A in range(80):
        for fd in range(10):
            for x in range(2):
                e = [0] * 10
                def add(n):
                    for i, v in enumerate(_digit_counts(n)):
                        e[i] += v
                if mode == 'classic':
                    C = abs(A - 2 * fd); add(A); add(_sumd(A)); add(C); add(_sumd(C))
                elif mode == 'corrected':
                    if x:
                        C = A + 19; add(A); e[1] += 1; e[9] += 1; add(C); add(_sumd(C))
                    else:
                        C = A - 2; add(A); e[2] += 1; add(C); add(_sumd(C))
                else:
                    kA = abs(A - 9); kC = abs(kA - 2 * fd); add(kA); add(_sumd(kA)); add(kC); add(_sumd(kC))
                T[A, fd, x] = e
    return T


def pyth_span(y0, y1, mode):
    """(counts N×10 int16, year of each date) for every date of years y0..y1."""
    CC, S, F, L = _dm_tables()
    T = _ex_table(mode)
    years = np.arange(y0, y1 + 1)
    leap = (years % 4 == 0) & ((years % 100 != 0) | (years % 400 == 0))
    keep = ~L[None, :] | leap[:, None]                      # Feb 29 only in leap years
    yi, di = np.nonzero(keep)
    y = years[yi]
    YC = np.array([_digit_counts(int(v)) for v in years], np.int16)[yi]
    YS = np.array([_sumd(int(v)) for v in years], np.int32)[yi]
    A = S[di] + YS
    x = (y >= 2000).astype(np.int32)
    c = CC[di] + YC + T[A, F[di], x]
    return c, y


def pyth_stats(y0, y1, mode, conds):
    """The S object of pythagoras_plus.js runStats(), computed on the server."""
    KM, LM = 16, 28
    c, y = pyth_span(y0, y1, mode)
    ny = y1 - y0 + 1
    yi = y - y0
    D = c[:, 1:10]
    empt = (D == 0).sum(1)
    lt = np.stack([c[:, a] + c[:, b] + c[:, d] for a, b, d in LINE_DIG], 1)

    def hist(sub_c, sub_e, sub_lt):
        H = np.zeros(10 * KM, np.int64); SB = np.zeros(10, np.int64); LB = np.zeros(8 * LM, np.int64)
        for d in range(1, 10):
            H[d * KM:(d + 1) * KM] = np.bincount(np.minimum(sub_c[:, d], KM - 1), minlength=KM)
            SB[d] = int(sub_c[:, d].sum())
        for l in range(8):
            LB[l * LM:(l + 1) * LM] = np.bincount(np.minimum(sub_lt[:, l], LM - 1), minlength=LM)
        EB = np.bincount(sub_e, minlength=10)[:10]
        return H, SB, EB, LB

    def per_year(mask_c, mask_yi):
        E = np.zeros(ny * 10, np.int64); Sm = np.zeros(ny * 10, np.int64)
        for d in range(1, 10):
            E[d::10] = np.bincount(mask_yi, weights=(mask_c[:, d] == 0), minlength=ny)[:ny]
            Sm[d::10] = np.bincount(mask_yi, weights=mask_c[:, d], minlength=ny)[:ny]
        return E, Sm

    HB, SB, EB, LB = hist(c, empt, lt)
    BN = np.bincount(yi, minlength=ny)[:ny]
    BE, BS = per_year(c, yi)
    mask = np.ones(len(y), bool)
    for q in conds or []:
        t, k, op = q.get('t'), int(q.get('k', 0)), q.get('op')
        v = c[:, int(q['d'])] if t == 'd' else lt[:, int(q['d'])] if t == 'l' else empt
        mask &= (v == k) if op == '=' else (v >= k) if op == '≥' else (v <= k)
    has = bool(conds)
    mc, my = c[mask], yi[mask]
    YN = np.bincount(my, minlength=ny)[:ny]
    YE, YS = per_year(mc, my)
    weights = np.array([16 ** (d - 1) for d in range(1, 10)], np.int64)
    keys = (np.minimum(mc[:, 1:10], 15).astype(np.int64) * weights).sum(1)
    uk, first, un = np.unique(keys, return_index=True, return_counts=True)
    order = np.argsort(first, kind='stable')                 # first-appearance order, as the browser Map had it
    uk, un = uk[order], un[order]
    out = {'y0': y0, 'y1': y1, 'mode': mode, 'has': has, 'N': int(len(y)), 'NC': int(mask.sum()), 'KM': KM, 'LM': LM,
           'HB': HB.tolist(), 'SB': SB.tolist(), 'EB': EB.tolist(), 'LB': LB.tolist(),
           'BN': BN.tolist(), 'BE': BE.astype(int).tolist(), 'BS': BS.astype(int).tolist(),
           'YN': YN.tolist(), 'YE': YE.astype(int).tolist(), 'YS': YS.astype(int).tolist(),
           'SQ': [uk.tolist(), un.tolist()]}
    if has:
        HC, SC, EC, LC = hist(mc, empt[mask], lt[mask])
        out.update(HC=HC.tolist(), SC=SC.tolist(), EC=EC.tolist(), LC=LC.tolist())
    return out


# ── Matrix statistics (mirrors matrix_stats.js): year-type tables ──
def m1_ext(dd, mm, R3):
    L3, T3 = r22(dd), r22(mm)
    B3 = r22(L3 + T3 + R3); Cv = r22(L3 + T3 + R3 + B3)
    TL3, TR3, BR3, BL3 = r22(L3 + T3), r22(T3 + R3), r22(R3 + B3), r22(B3 + L3)
    RC1 = r22(TL3 + TR3 + BR3 + BL3); RC2 = r22(RC1 + Cv)
    B1 = r22(Cv + B3); B2 = r22(B1 + B3); R1 = r22(Cv + R3); R2 = r22(R1 + R3)
    L1 = r22(Cv + L3); L2 = r22(L1 + L3); T1 = r22(Cv + T3); T2 = r22(T1 + T3)
    G1 = r22(L1 + Cv); G2 = r22(T1 + Cv)
    TL1 = r22(TL3 + RC1); TL2 = r22(TL1 + TL3); TR1 = r22(TR3 + RC1); TR2 = r22(TR1 + TR3)
    BR1 = r22(BR3 + RC1); BR2 = r22(BR1 + BR3); BL1 = r22(BL3 + RC1); BL2 = r22(BL1 + BL3)
    W2 = r22(B1 + R1); W1 = r22(B1 + W2); W3 = r22(R1 + W2)
    v = dict(L3=L3, T3=T3, R3=R3, B3=B3, Cv=Cv, B1=B1, B2=B2, R1=R1, R2=R2, L1=L1, L2=L2, T1=T1, T2=T2, G1=G1, G2=G2,
             TL3=TL3, TR3=TR3, BR3=BR3, BL3=BL3, RC1=RC1, RC2=RC2, TL1=TL1, TL2=TL2, TR1=TR1, TR2=TR2,
             BR1=BR1, BR2=BR2, BL1=BL1, BL2=BL2, W1=W1, W2=W2, W3=W3)
    se = sp = ss = 0
    for k, e, p in (('sahasrara', T3, L3), ('ajna', T2, L2), ('vishudha', T1, L1), ('anahata', G2, G1),
                    ('manipura', Cv, Cv), ('svadhistana', B1, R1), ('muladhara', B3, R3)):
        s = r22(e + p)
        v['CHE_' + k] = e; v['CHP_' + k] = p; v['CHS_' + k] = s
        se += e; sp += p; ss += s
    v['CHE_total'] = r22(se); v['CHP_total'] = r22(sp); v['CHS_total'] = r22(ss)
    v['S6'] = v['CHS_svadhistana']
    v['MALE'] = r22(TL3 + BR3); v['FEM'] = r22(TR3 + BL3)
    v['SOUL'] = r22(r22(T3 + B3) + r22(R3 + L3))
    v['SOC'] = r22(r22(TL3 + BR3) + r22(TR3 + BL3))
    v['MISSION'] = r22(v['SOUL'] + v['SOC'])
    return v


def _code(keys, exact, v):
    n = [str(v[k]) for k in keys]
    if len(n) == 1:
        return n[0]
    f = '-'.join(n)
    if exact:
        return f
    r = '-'.join(reversed(n))
    return f if f <= r else r


TIE = '='
_MXT = {}


def mx_type_table(R3, leap, aspects, akey):
    k = (R3, leap, akey)
    if k in _MXT:
        return _MXT[k]
    t = {a['id']: {} for a in aspects}
    for m in range(1, 13):
        dm = 29 if (m == 2 and leap) else [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        for d in range(1, dm + 1):
            v = m1_ext(d, m, R3)
            for a in aspects:
                o = t[a['id']]
                c = _code(a['keys'], a['exact'], v)
                o[c] = o.get(c, 0) + 1
    dom = {}
    for a in aspects:
        best, bc, tie = None, -1, 0
        for c, n in t[a['id']].items():          # insertion order = JS for…in order (string keys, not integer-like)
            if n > bc:
                best, bc, tie = c, n, 1
            elif n == bc:
                tie += 1
        dom[a['id']] = [TIE, bc, tie] if tie > 1 else [best, bc, 1]
    res = {'t': t, 'dom': dom, 'n': 366 if leap else 365}
    if len(_MXT) > 400:
        _MXT.clear()
    _MXT[k] = res
    return res


def _sorted_counts(o):
    """JS: Object.entries(o).sort((p,q)=>q[1]-p[1]) — stable, by count desc, in JS key order."""
    def js_order(keys):
        ints = sorted((k for k in keys if k.isdigit() and str(int(k)) == k), key=int)
        return ints + [k for k in keys if k not in set(ints)]
    ks = js_order(list(o.keys()))
    return sorted(((k, o[k]) for k in ks), key=lambda kv: -kv[1])


def mx_stats(y0, y1, aspects, sel):
    akey = _json.dumps(aspects, sort_keys=True)
    yr3 = lambda y: 22 if y == 0 else r22(y)
    types = {}
    for y in range(y0, y1 + 1):
        k = (yr3(y), 1 if _leap(y) else 0)
        types[k] = types.get(k, 0) + 1
    cnt = {a['id']: {} for a in aspects}
    dom_years = {}
    days = 0
    tabs = {}
    for (r3, l), w in types.items():
        tb = mx_type_table(r3, l, aspects, akey)
        tabs[(r3, l)] = tb
        days += tb['n'] * w
        for a in aspects:
            o, s = cnt[a['id']], tb['t'][a['id']]
            for c, n in s.items():
                o[c] = o.get(c, 0) + n * w
        dsel = tb['dom'][sel][0]
        dom_years[dsel] = dom_years.get(dsel, 0) + w
    summary = {}
    for a in aspects:
        lst = _sorted_counts(cnt[a['id']])
        if lst:
            n0 = lst[0][1]
            summary[a['id']] = {'top': list(lst[0]), 'bot': list(lst[-1]), 'ties': sum(1 for e in lst if e[1] == n0)}
    t1 = mx_type_table(1, 0, aspects, akey)['t']; t2 = mx_type_table(13, 0, aspects, akey)['t']
    free = {a['id']: _sorted_counts(t1[a['id']]) == _sorted_counts(t2[a['id']]) for a in aspects}
    return {'y0': y0, 'y1': y1, 'years': y1 - y0 + 1, 'days': days, 'sel': sel,
            'cnt': [list(e) for e in _sorted_counts(cnt[sel])],
            'domYears': [list(e) for e in _sorted_counts(dom_years)],
            'summary': summary, 'free': free,
            'types': {f'{r3}_{l}': {'n': tb['n'], 'dom': tb['dom'], 'top': [list(e) for e in _sorted_counts(tb['t'][sel])[:5]]}
                      for (r3, l), tb in tabs.items()}}


@lru_cache(maxsize=8)
def mx_people_baseline(keys):
    """Share of all dates 1930–2010 whose profile (the set of energies on `keys`) holds each energy."""
    c = [0] * 23
    N = 0
    for y in range(1930, 2011):
        for m in range(1, 13):
            dm = 29 if (m == 2 and _leap(y)) else [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
            for d in range(1, dm + 1):
                v = matrix_values(d, m, y, 1)
                v['MISSION'] = line_panels(v)['misia']
                for n in {v[k] for k in keys}:
                    c[n] += 1
                N += 1
    return [x / N for x in c]


def _gz(obj):
    """JSON, gzipped when the browser accepts it (the per-year series are large)."""
    from flask import Response
    raw = _json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode()
    if 'gzip' in (request.headers.get('Accept-Encoding') or '') and len(raw) > 2000:
        return Response(_gzip.compress(raw, 5), mimetype='application/json', headers={'Content-Encoding': 'gzip', 'Vary': 'Accept-Encoding'})
    return Response(raw, mimetype='application/json')


def init_numcalc_stats(app, pro_block):
    MODES = ('classic', 'corrected', 'crisis')

    @app.route('/api/pythagoras/stats', methods=['POST'])
    def api_pyth_stats():
        blk = pro_block('pythagoras.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        y0, y1 = _int(d.get('y0')), _int(d.get('y1'))
        mode = d.get('mode') if d.get('mode') in MODES else 'classic'
        if y0 is None or y1 is None:
            return jsonify(error='y0, y1'), 400
        y0, y1 = max(1, min(y0, y1)), min(9999, max(y0, y1))
        conds = [q for q in (d.get('conds') or [])[:12] if isinstance(q, dict) and q.get('t') in ('d', 'l', 'e')]
        return _gz(pyth_stats(y0, y1, mode, conds))

    @app.route('/api/matrix/stats', methods=['POST'])
    def api_mx_stats():
        blk = pro_block('matrix.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        y0, y1 = _int(d.get('y0')), _int(d.get('y1'))
        if y0 is None or y1 is None:
            return jsonify(error='y0, y1'), 400
        y0, y1 = max(0, min(y0, y1)), min(9999, max(y0, y1))
        aspects = []
        for a in (d.get('aspects') or [])[:200]:
            ks = [str(k)[:20] for k in (a.get('keys') or [])][:3]
            if a.get('id') and ks:
                aspects.append({'id': str(a['id'])[:40], 'keys': ks, 'exact': bool(a.get('exact'))})
        ok_keys = set(m1_ext(1, 1, 1))
        if not aspects or any(k not in ok_keys for a in aspects for k in a['keys']):
            return jsonify(error='aspects'), 400
        sel = d.get('sel') if any(a['id'] == d.get('sel') for a in aspects) else aspects[0]['id']
        return _gz(mx_stats(y0, y1, aspects, sel))

    @app.route('/api/matrix/people_baseline', methods=['POST'])
    def api_mx_baseline():
        blk = pro_block('matrix.html')
        if blk:
            return blk
        d = request.get_json(silent=True) or {}
        keys = tuple(str(k) for k in (d.get('keys') or ['L3', 'T3', 'R3', 'B3', 'Cv', 'B2', 'B1', 'W2', 'MISSION'])[:20])
        ok = set(matrix_values(1, 1, 2000, 1)) | {'MISSION'}
        if any(k not in ok for k in keys):
            return jsonify(error='keys'), 400
        return jsonify(mx_people_baseline(keys))
