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
        out = []
        for x in (d.get('dates') or [])[:200]:
            dd, mm, yyyy = _date(x if isinstance(x, dict) else {})
            if validate_date(dd, mm, yyyy) or method not in (1, 2):
                out.append(None)
            else:
                out.append(matrix_values(dd, mm, yyyy, method))
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
