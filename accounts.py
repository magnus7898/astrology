"""accounts.py — MAGNUS user accounts, saved data, activity tracking and plans.

Registered from app.py with one line:  init_accounts(app, db, User, Event, Payment, admin_required)
(before db.create_all(), so the new tables are created on start).

Only NEW tables are added — the existing `user` table is not altered (create_all cannot add
columns to an existing Postgres table):
  account_meta   per-user extras: email verified, plan (free/pro) + expiry, last seen
  person         "ჩემი ხალხი" — saved birth data (name, date, time, place, tz)
  saved_item     a saved page state: every input on a page (id → value), reopenable on any device
  activity       every step on the site: page views, tab switches, button presses, form values
  plan_feature   which pages/features need Pro (edited from the admin panel)

Email (verification, password reset) uses SMTP from env: SMTP_HOST, SMTP_PORT, SMTP_USER,
SMTP_PASS, MAIL_FROM, and SITE_URL (the frontend base, e.g. https://magnus7898.github.io/astrologia).
Without SMTP the links are printed to the Railway log and verification is not required.
"""
import os
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage

from flask import jsonify, request
from flask_jwt_extended import (create_access_token, get_jwt_identity, jwt_required,
                                verify_jwt_in_request, decode_token)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

LIMITS = {'free': {'people': 10, 'saved': 30}, 'pro': {'people': 1000, 'saved': 5000}}
MAX_STATE_BYTES = 200_000          # one saved page state
MAX_TRACK_BATCH = 60               # events per /api/track call
MAX_DETAIL_BYTES = 4_000           # one activity detail


def init_accounts(app, db, User, Event, Payment, admin_required):
    # ───────────────────────── models ─────────────────────────
    class AccountMeta(db.Model):
        __tablename__ = 'account_meta'
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
        verified = db.Column(db.Boolean, default=False)
        plan = db.Column(db.String(10), default='free')            # free | pro
        plan_until = db.Column(db.DateTime, nullable=True)           # None = no expiry
        last_seen = db.Column(db.DateTime, nullable=True)
        pw_changed = db.Column(db.DateTime, nullable=True)           # tokens issued before are void

    class Person(db.Model):
        __tablename__ = 'person'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        name = db.Column(db.String(80), default='')
        is_self = db.Column(db.Boolean, default=False)
        year = db.Column(db.Integer); month = db.Column(db.Integer); day = db.Column(db.Integer)
        hour = db.Column(db.Integer, default=12); minute = db.Column(db.Integer, default=0)
        second = db.Column(db.Integer, default=0)
        time_unknown = db.Column(db.Boolean, default=False)
        city = db.Column(db.String(160), default='')
        lat = db.Column(db.Float); lon = db.Column(db.Float)
        tz = db.Column(db.String(64), default='UTC')
        note = db.Column(db.String(500), default='')
        created = db.Column(db.DateTime, server_default=db.func.now())
        updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

        def as_dict(self):
            return {k: getattr(self, k) for k in (
                'id', 'name', 'is_self', 'year', 'month', 'day', 'hour', 'minute', 'second',
                'time_unknown', 'city', 'lat', 'lon', 'tz', 'note')} | {'updated': str(self.updated)}

    class SavedItem(db.Model):
        __tablename__ = 'saved_item'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
        page = db.Column(db.String(80), nullable=False)               # astro.html
        tab = db.Column(db.String(80), default='')                    # active tab / mode
        title = db.Column(db.String(200), default='')
        state = db.Column(db.JSON)                                     # {input id: value}
        result = db.Column(db.JSON, nullable=True)                     # optional summary
        created = db.Column(db.DateTime, server_default=db.func.now())
        updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

        def as_dict(self, full=False):
            d = {'id': self.id, 'page': self.page, 'tab': self.tab, 'title': self.title,
                 'created': str(self.created), 'updated': str(self.updated)}
            if full:
                d.update(state=self.state, result=self.result)
            return d

    class Activity(db.Model):
        __tablename__ = 'activity'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
        device = db.Column(db.String(40), index=True)                 # anonymous browser id
        session = db.Column(db.String(40))
        page = db.Column(db.String(80))
        action = db.Column(db.String(40))                              # view | click | tab | calc | save | ...
        target = db.Column(db.String(200))
        detail = db.Column(db.JSON)
        t_client = db.Column(db.BigInteger)                            # ms, browser clock
        ip = db.Column(db.String(45))
        created = db.Column(db.DateTime, server_default=db.func.now(), index=True)

        def as_dict(self):
            return {'id': self.id, 'user_id': self.user_id, 'device': self.device,
                    'session': self.session, 'page': self.page, 'action': self.action,
                    'target': self.target, 'detail': self.detail, 't': str(self.created)}

    class PlanFeature(db.Model):
        __tablename__ = 'plan_feature'
        id = db.Column(db.Integer, primary_key=True)
        key = db.Column(db.String(80), unique=True, nullable=False)    # page file or page#feature
        title = db.Column(db.String(160), default='')
        pro_only = db.Column(db.Boolean, default=True)

        def as_dict(self):
            return {'id': self.id, 'key': self.key, 'title': self.title, 'pro_only': self.pro_only}

    # ───────────────────────── helpers ─────────────────────────
    ser = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'], salt='magnus-accounts')
    site = lambda: (os.environ.get('SITE_URL') or 'https://magnus7898.github.io/astrologia').rstrip('/')
    smtp_on = lambda: bool(os.environ.get('SMTP_HOST') and os.environ.get('MAIL_FROM'))

    def meta(uid):
        m = db.session.get(AccountMeta, uid)
        if not m:
            m = AccountMeta(user_id=uid, verified=not smtp_on())
            db.session.add(m)
            db.session.flush()
        return m

    def plan_of(m):
        if m.plan == 'pro' and (m.plan_until is None or m.plan_until > datetime.utcnow()):
            return 'pro'
        return 'free'

    def send_mail(to, subject, text):
        if not smtp_on():
            print(f'[mail] SMTP not set — to {to}: {subject}\n{text}', flush=True)
            return False
        msg = EmailMessage()
        msg['From'], msg['To'], msg['Subject'] = os.environ['MAIL_FROM'], to, subject
        msg.set_content(text)
        host, port = os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT') or 587)
        try:
            if port == 465:
                s = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=20)
            else:
                s = smtplib.SMTP(host, port, timeout=20)
                s.starttls(context=ssl.create_default_context())
            if os.environ.get('SMTP_USER'):
                s.login(os.environ['SMTP_USER'], os.environ.get('SMTP_PASS', ''))
            s.send_message(msg)
            s.quit()
            return True
        except Exception as e:
            print('[mail] send failed:', e, flush=True)
            return False

    def send_verify(u):
        tok = ser.dumps({'uid': u.id, 'k': 'verify'})
        send_mail(u.email, 'MAGNUS — ელფოსტის დადასტურება',
                  f'გამარჯობა{", " + u.name if u.name else ""}!\n\nდაადასტურეთ ელფოსტა ამ ბმულით:\n'
                  f'{site()}/account.html#verify={tok}\n\nთუ ეს თქვენ არ ყოფილხართ, უბრალოდ დააიგნორეთ.')

    def me_dict(u, m):
        p = plan_of(m)
        return {'id': u.id, 'email': u.email, 'name': u.name, 'role': u.role,
                'created': str(u.created), 'verified': bool(m.verified), 'plan': p,
                'plan_until': str(m.plan_until) if (p == 'pro' and m.plan_until) else None,
                'limits': LIMITS[p], 'smtp': smtp_on(),
                'people': Person.query.filter_by(user_id=u.id).count(),
                'saved': SavedItem.query.filter_by(user_id=u.id).count()}

    def current_user():
        """(User, AccountMeta) for the bearer token, or (None, None). Tokens issued before the
        last password change are refused."""
        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            return None, None
        ident = get_jwt_identity()
        if not ident:
            return None, None
        u = db.session.get(User, int(ident))
        if not u:
            return None, None
        m = meta(u.id)
        if m.pw_changed:
            from flask_jwt_extended import get_jwt
            iat = get_jwt().get('iat')
            if iat and datetime.utcfromtimestamp(iat) < m.pw_changed - timedelta(seconds=1):
                return None, None
        return u, m

    def need_user():
        u, m = current_user()
        if not u:
            return None, None, (jsonify(error='გთხოვთ შეხვიდეთ ანგარიშზე'), 401)
        m.last_seen = datetime.utcnow()
        return u, m, None

    def token_for(u):
        return create_access_token(identity=str(u.id), additional_claims={'role': u.role})

    def claim_device(uid, device):
        if device:
            Activity.query.filter_by(device=device[:40], user_id=None).update({'user_id': uid})

    def clean_person(d, p):
        def num(k, lo, hi, dflt=None):
            try:
                v = int(d.get(k))
                return v if lo <= v <= hi else dflt
            except (TypeError, ValueError):
                return dflt
        p.name = str(d.get('name') or '')[:80]
        p.is_self = bool(d.get('is_self'))
        p.year = num('year', -5000, 9999); p.month = num('month', 1, 12); p.day = num('day', 1, 31)
        p.hour = num('hour', 0, 23, 12); p.minute = num('minute', 0, 59, 0); p.second = num('second', 0, 59, 0)
        p.time_unknown = bool(d.get('time_unknown'))
        p.city = str(d.get('city') or '')[:160]
        for k in ('lat', 'lon'):
            try:
                setattr(p, k, float(d.get(k)) if d.get(k) not in (None, '') else None)
            except (TypeError, ValueError):
                setattr(p, k, None)
        p.tz = str(d.get('tz') or d.get('tz_name') or 'UTC')[:64]
        p.note = str(d.get('note') or '')[:500]
        if p.year is None or p.month is None or p.day is None:
            return 'შეიყვანეთ დაბადების თარიღი'
        return None

    # ───────────────────────── auth ─────────────────────────
    # The original /api/register and /api/login stay as they are (admin.html uses them);
    # these wrap them with verification, device linking and the full profile.
    @app.route('/api/account/register', methods=['POST'])
    def acc_register():
        d = request.json or {}
        email = (d.get('email') or '').strip().lower()
        pw = d.get('password') or ''
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify(error='ელფოსტა არასწორია'), 400
        if len(pw) < 8:
            return jsonify(error='პაროლი მინიმუმ 8 სიმბოლო'), 400
        if User.query.filter(db.func.lower(db.func.trim(User.email)) == email).first():
            return jsonify(error='ეს ელფოსტა უკვე რეგისტრირებულია'), 409
        first = User.query.count() == 0
        u = User(email=email, name=str(d.get('name') or '').strip()[:80],
                 pw_hash=generate_password_hash(pw), role='admin' if first else 'user')
        db.session.add(u)
        db.session.flush()
        m = meta(u.id)
        claim_device(u.id, d.get('device'))
        db.session.add(Event(user_id=u.id, action='register', detail={'email': email}, ip=request.remote_addr))
        db.session.commit()
        if smtp_on():
            send_verify(u)
        return jsonify(token=token_for(u), user=me_dict(u, m))

    @app.route('/api/account/login', methods=['POST'])
    def acc_login():
        d = request.json or {}
        em = (d.get('email') or '').strip().lower()
        pw = d.get('password') or ''
        u = next((x for x in User.query.filter(db.func.lower(db.func.trim(User.email)) == em).all()
                  if check_password_hash(x.pw_hash, pw)), None)
        if not u:
            return jsonify(error='არასწორი ელფოსტა ან პაროლი'), 401
        m = meta(u.id)
        m.last_seen = datetime.utcnow()
        claim_device(u.id, d.get('device'))
        db.session.add(Event(user_id=u.id, action='login', detail=None, ip=request.remote_addr))
        db.session.commit()
        return jsonify(token=token_for(u), user=me_dict(u, m))

    @app.route('/api/account/me', methods=['GET'])
    def acc_me():
        u, m, err = need_user()
        if err:
            return err
        db.session.commit()
        return jsonify(me_dict(u, m))

    @app.route('/api/account/me', methods=['PATCH'])
    def acc_me_update():
        u, m, err = need_user()
        if err:
            return err
        d = request.json or {}
        if 'name' in d:
            u.name = str(d.get('name') or '').strip()[:80]
        if d.get('new_password'):
            if not check_password_hash(u.pw_hash, d.get('password') or ''):
                return jsonify(error='ძველი პაროლი არასწორია'), 400
            if len(d['new_password']) < 8:
                return jsonify(error='ახალი პაროლი მინიმუმ 8 სიმბოლო'), 400
            u.pw_hash = generate_password_hash(d['new_password'])
            m.pw_changed = datetime.utcnow()
        db.session.commit()
        return jsonify(token=token_for(u), user=me_dict(u, m))

    @app.route('/api/account/me', methods=['DELETE'])
    def acc_delete():
        u, m, err = need_user()
        if err:
            return err
        if not check_password_hash(u.pw_hash, (request.json or {}).get('password') or ''):
            return jsonify(error='პაროლი არასწორია'), 400
        if u.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
            return jsonify(error='ბოლო ადმინის წაშლა არ შეიძლება'), 400
        Person.query.filter_by(user_id=u.id).delete()
        SavedItem.query.filter_by(user_id=u.id).delete()
        Activity.query.filter_by(user_id=u.id).delete()
        db.session.delete(m)
        db.session.add(Event(user_id=None, action='account_deleted', detail={'id': u.id}, ip=request.remote_addr))
        db.session.delete(u)
        db.session.commit()
        return jsonify(ok=True)

    @app.route('/api/account/verify/send', methods=['POST'])
    def acc_verify_send():
        u, m, err = need_user()
        if err:
            return err
        if m.verified:
            return jsonify(ok=True, already=True)
        send_verify(u)
        db.session.commit()
        return jsonify(ok=True, smtp=smtp_on())

    @app.route('/api/account/verify', methods=['POST'])
    def acc_verify():
        try:
            data = ser.loads((request.json or {}).get('token') or '', max_age=7 * 86400)
        except SignatureExpired:
            return jsonify(error='ბმულს ვადა გაუვიდა — მოითხოვეთ ახალი'), 400
        except BadSignature:
            return jsonify(error='ბმული არასწორია'), 400
        if data.get('k') != 'verify':
            return jsonify(error='ბმული არასწორია'), 400
        u = db.session.get(User, int(data['uid']))
        if not u:
            return jsonify(error='ანგარიში ვერ მოიძებნა'), 404
        meta(u.id).verified = True
        db.session.commit()
        return jsonify(ok=True)

    @app.route('/api/account/password/forgot', methods=['POST'])
    def acc_forgot():
        em = ((request.json or {}).get('email') or '').strip().lower()
        u = User.query.filter(db.func.lower(db.func.trim(User.email)) == em).first()
        if u:   # same answer either way, so emails cannot be probed
            tok = ser.dumps({'uid': u.id, 'k': 'reset', 'h': u.pw_hash[-12:]})
            send_mail(u.email, 'MAGNUS — პაროლის აღდგენა',
                      f'პაროლის შესაცვლელად გახსენით ბმული (მოქმედებს 2 საათი):\n'
                      f'{site()}/account.html#reset={tok}\n\nთუ ეს თქვენ არ მოგითხოვიათ, დააიგნორეთ.')
        return jsonify(ok=True, smtp=smtp_on())

    @app.route('/api/account/password/reset', methods=['POST'])
    def acc_reset():
        d = request.json or {}
        try:
            data = ser.loads(d.get('token') or '', max_age=2 * 3600)
        except SignatureExpired:
            return jsonify(error='ბმულს ვადა გაუვიდა — მოითხოვეთ ახალი'), 400
        except BadSignature:
            return jsonify(error='ბმული არასწორია'), 400
        u = db.session.get(User, int(data.get('uid', 0)))
        if not u or data.get('k') != 'reset' or u.pw_hash[-12:] != data.get('h'):
            return jsonify(error='ბმული უკვე გამოყენებულია ან არასწორია'), 400
        if len(d.get('password') or '') < 8:
            return jsonify(error='პაროლი მინიმუმ 8 სიმბოლო'), 400
        u.pw_hash = generate_password_hash(d['password'])
        m = meta(u.id)
        m.verified = True              # the link proves the mailbox
        m.pw_changed = datetime.utcnow()
        db.session.add(Event(user_id=u.id, action='password_reset', detail=None, ip=request.remote_addr))
        db.session.commit()
        return jsonify(token=token_for(u), user=me_dict(u, m))

    # ───────────────────────── people ─────────────────────────
    @app.route('/api/people', methods=['GET'])
    def people_list():
        u, m, err = need_user()
        if err:
            return err
        db.session.commit()
        q = Person.query.filter_by(user_id=u.id).order_by(Person.is_self.desc(), Person.name).all()
        return jsonify([p.as_dict() for p in q])

    @app.route('/api/people', methods=['POST'])
    def people_add():
        u, m, err = need_user()
        if err:
            return err
        if Person.query.filter_by(user_id=u.id).count() >= LIMITS[plan_of(m)]['people']:
            return jsonify(error=f'ლიმიტი: {LIMITS[plan_of(m)]["people"]} ადამიანი (Pro — მეტი)', limit=True), 403
        p = Person(user_id=u.id)
        bad = clean_person(request.json or {}, p)
        if bad:
            return jsonify(error=bad), 400
        if p.is_self:
            Person.query.filter_by(user_id=u.id, is_self=True).update({'is_self': False})
        db.session.add(p)
        db.session.commit()
        return jsonify(p.as_dict())

    @app.route('/api/people/<int:pid>', methods=['PUT'])
    def people_edit(pid):
        u, m, err = need_user()
        if err:
            return err
        p = Person.query.filter_by(id=pid, user_id=u.id).first()
        if not p:
            return jsonify(error='ვერ მოიძებნა'), 404
        bad = clean_person(request.json or {}, p)
        if bad:
            return jsonify(error=bad), 400
        if p.is_self:
            Person.query.filter(Person.user_id == u.id, Person.id != p.id).update({'is_self': False})
        db.session.commit()
        return jsonify(p.as_dict())

    @app.route('/api/people/<int:pid>', methods=['DELETE'])
    def people_del(pid):
        u, m, err = need_user()
        if err:
            return err
        n = Person.query.filter_by(id=pid, user_id=u.id).delete()
        db.session.commit()
        return jsonify(ok=bool(n))

    # ───────────────────────── saved page states ─────────────────────────
    @app.route('/api/saved', methods=['GET'])
    def saved_list():
        u, m, err = need_user()
        if err:
            return err
        db.session.commit()
        q = SavedItem.query.filter_by(user_id=u.id)
        if request.args.get('page'):
            q = q.filter_by(page=request.args['page'][:80])
        return jsonify([s.as_dict() for s in q.order_by(SavedItem.updated.desc()).limit(500).all()])

    @app.route('/api/saved/<int:sid>', methods=['GET'])
    def saved_get(sid):
        u, m, err = need_user()
        if err:
            return err
        s = SavedItem.query.filter_by(id=sid, user_id=u.id).first()
        return jsonify(s.as_dict(full=True)) if s else (jsonify(error='ვერ მოიძებნა'), 404)

    def _state_ok(d):
        import json
        st = d.get('state')
        if not isinstance(st, dict):
            return 'state must be an object'
        if len(json.dumps(st, ensure_ascii=False)) > MAX_STATE_BYTES:
            return 'ძალიან დიდი მონაცემი'
        res = d.get('result')
        if res is not None and len(json.dumps(res, ensure_ascii=False)) > MAX_STATE_BYTES:
            return 'ძალიან დიდი შედეგი'
        return None

    @app.route('/api/saved', methods=['POST'])
    def saved_add():
        u, m, err = need_user()
        if err:
            return err
        d = request.json or {}
        bad = _state_ok(d)
        if bad:
            return jsonify(error=bad), 400
        if SavedItem.query.filter_by(user_id=u.id).count() >= LIMITS[plan_of(m)]['saved']:
            return jsonify(error=f'ლიმიტი: {LIMITS[plan_of(m)]["saved"]} შენახვა (Pro — მეტი)', limit=True), 403
        s = SavedItem(user_id=u.id, page=str(d.get('page') or '')[:80], tab=str(d.get('tab') or '')[:80],
                      title=str(d.get('title') or '')[:200], state=d['state'], result=d.get('result'))
        db.session.add(s)
        db.session.commit()
        return jsonify(s.as_dict())

    @app.route('/api/saved/<int:sid>', methods=['PUT'])
    def saved_edit(sid):
        u, m, err = need_user()
        if err:
            return err
        s = SavedItem.query.filter_by(id=sid, user_id=u.id).first()
        if not s:
            return jsonify(error='ვერ მოიძებნა'), 404
        d = request.json or {}
        if 'title' in d:
            s.title = str(d.get('title') or '')[:200]
        if 'state' in d:
            bad = _state_ok(d)
            if bad:
                return jsonify(error=bad), 400
            s.state, s.result = d['state'], d.get('result')
        db.session.commit()
        return jsonify(s.as_dict())

    @app.route('/api/saved/<int:sid>', methods=['DELETE'])
    def saved_del(sid):
        u, m, err = need_user()
        if err:
            return err
        n = SavedItem.query.filter_by(id=sid, user_id=u.id).delete()
        db.session.commit()
        return jsonify(ok=bool(n))

    # ───────────────────────── activity tracking ─────────────────────────
    @app.route('/api/track', methods=['POST'])
    def track():
        import json
        d = request.get_json(silent=True) or {}
        u, m = current_user()
        if u:
            m.last_seen = datetime.utcnow()
        device = str(d.get('device') or '')[:40] or None
        session = str(d.get('session') or '')[:40] or None
        evs = d.get('events') or []
        if not isinstance(evs, list):
            return jsonify(error='events must be a list'), 400
        for e in evs[:MAX_TRACK_BATCH]:
            if not isinstance(e, dict):
                continue
            det = e.get('detail')
            if det is not None and len(json.dumps(det, ensure_ascii=False)) > MAX_DETAIL_BYTES:
                det = {'truncated': True}
            try:
                tc = int(e.get('t')) if e.get('t') is not None else None
            except (TypeError, ValueError):
                tc = None
            db.session.add(Activity(user_id=u.id if u else None, device=device, session=session,
                                    page=str(e.get('page') or '')[:80], action=str(e.get('action') or '?')[:40],
                                    target=str(e.get('target') or '')[:200], detail=det, t_client=tc,
                                    ip=request.remote_addr))
        db.session.commit()
        return jsonify(ok=True, n=min(len(evs), MAX_TRACK_BATCH))

    @app.route('/api/account/activity', methods=['GET'])
    def my_activity():
        u, m, err = need_user()
        if err:
            return err
        db.session.commit()
        q = Activity.query.filter_by(user_id=u.id).order_by(Activity.id.desc()).limit(300).all()
        return jsonify([a.as_dict() for a in q])

    # ───────────────────────── plans ─────────────────────────
    @app.route('/api/plans', methods=['GET'])
    def plans_public():
        return jsonify(limits=LIMITS, features=[f.as_dict() for f in PlanFeature.query.order_by(PlanFeature.key).all()])

    # ───────────────────────── admin ─────────────────────────
    @app.route('/api/admin/accounts', methods=['GET'])
    @admin_required
    def adm_accounts():
        qs = (request.args.get('q') or '').strip().lower()
        q = User.query
        if qs:
            q = q.filter(db.or_(db.func.lower(User.email).contains(qs), db.func.lower(User.name).contains(qs)))
        users = q.order_by(User.id.desc()).limit(500).all()
        ids = [u.id for u in users]
        metas = {x.user_id: x for x in AccountMeta.query.filter(AccountMeta.user_id.in_(ids)).all()} if ids else {}
        cnt = lambda M: dict(db.session.query(M.user_id, db.func.count()).filter(M.user_id.in_(ids)).group_by(M.user_id).all()) if ids else {}
        np, ns, na = cnt(Person), cnt(SavedItem), cnt(Activity)
        out = []
        for u in users:
            mm = metas.get(u.id)
            out.append({'id': u.id, 'email': u.email, 'name': u.name, 'role': u.role, 'created': str(u.created),
                        'verified': bool(mm and mm.verified), 'plan': plan_of(mm) if mm else 'free',
                        'plan_until': str(mm.plan_until) if mm and mm.plan_until else None,
                        'last_seen': str(mm.last_seen) if mm and mm.last_seen else None,
                        'people': np.get(u.id, 0), 'saved': ns.get(u.id, 0), 'activity': na.get(u.id, 0)})
        return jsonify(out)

    @app.route('/api/admin/accounts/<int:uid>', methods=['GET'])
    @admin_required
    def adm_account(uid):
        u = db.session.get(User, uid)
        if not u:
            return jsonify(error='not found'), 404
        m = meta(uid)
        db.session.commit()
        lim = min(int(request.args.get('limit') or 500), 3000)
        acts = Activity.query.filter_by(user_id=uid).order_by(Activity.id.desc()).limit(lim).all()
        pays = Payment.query.filter_by(user_id=uid).order_by(Payment.id.desc()).all()
        return jsonify(user=me_dict(u, m), last_seen=str(m.last_seen) if m.last_seen else None,
                       people=[p.as_dict() for p in Person.query.filter_by(user_id=uid).all()],
                       saved=[s.as_dict() for s in SavedItem.query.filter_by(user_id=uid).order_by(SavedItem.id.desc()).all()],
                       activity=[a.as_dict() for a in acts],
                       payments=[{'id': p.id, 'amount': float(p.amount or 0), 'currency': p.currency, 'product': p.product,
                                  'status': p.status, 't': str(p.created)} for p in pays])

    @app.route('/api/admin/accounts/<int:uid>', methods=['PATCH'])
    @admin_required
    def adm_account_edit(uid):
        u = db.session.get(User, uid)
        if not u:
            return jsonify(error='not found'), 404
        d = request.json or {}
        m = meta(uid)
        if d.get('plan') in ('free', 'pro'):
            m.plan = d['plan']
            days = d.get('days')
            m.plan_until = (datetime.utcnow() + timedelta(days=int(days))) if (d['plan'] == 'pro' and days) else None
        if 'verified' in d:
            m.verified = bool(d['verified'])
        if d.get('role') in ('user', 'admin'):
            if u.role == 'admin' and d['role'] == 'user' and User.query.filter_by(role='admin').count() <= 1:
                return jsonify(error='ბოლო ადმინი'), 400
            u.role = d['role']
        db.session.add(Event(user_id=uid, action='admin_edit', detail={k: d[k] for k in d if k != 'password'}, ip=request.remote_addr))
        db.session.commit()
        return jsonify(user=me_dict(u, m))

    @app.route('/api/admin/activity', methods=['GET'])
    @admin_required
    def adm_activity():
        q = Activity.query
        if request.args.get('device'):
            q = q.filter_by(device=request.args['device'][:40])
        if request.args.get('page'):
            q = q.filter_by(page=request.args['page'][:80])
        if request.args.get('anon') == '1':
            q = q.filter(Activity.user_id.is_(None))
        lim = min(int(request.args.get('limit') or 300), 3000)
        return jsonify([a.as_dict() for a in q.order_by(Activity.id.desc()).limit(lim).all()])

    @app.route('/api/admin/activity/stats', methods=['GET'])
    @admin_required
    def adm_activity_stats():
        since = datetime.utcnow() - timedelta(days=int(request.args.get('days') or 30))
        base = Activity.query.filter(Activity.created >= since)
        pages = db.session.query(Activity.page, db.func.count()).filter(Activity.created >= since, Activity.action == 'view')\
            .group_by(Activity.page).order_by(db.func.count().desc()).limit(50).all()
        actions = db.session.query(Activity.action, db.func.count()).filter(Activity.created >= since)\
            .group_by(Activity.action).order_by(db.func.count().desc()).all()
        devices = db.session.query(db.func.count(db.distinct(Activity.device))).filter(Activity.created >= since).scalar()
        users = db.session.query(db.func.count(db.distinct(Activity.user_id))).filter(Activity.created >= since).scalar()
        return jsonify(events=base.count(), devices=devices, users=users,
                       pages=[{'page': p, 'n': n} for p, n in pages],
                       actions=[{'action': a, 'n': n} for a, n in actions])

    @app.route('/api/admin/features', methods=['GET'])
    @admin_required
    def adm_features():
        return jsonify([f.as_dict() for f in PlanFeature.query.order_by(PlanFeature.key).all()])

    @app.route('/api/admin/features', methods=['POST'])
    @admin_required
    def adm_feature_set():
        d = request.json or {}
        key = str(d.get('key') or '').strip()[:80]
        if not key:
            return jsonify(error='key'), 400
        f = PlanFeature.query.filter_by(key=key).first() or PlanFeature(key=key)
        f.title = str(d.get('title') or f.title or '')[:160]
        f.pro_only = bool(d.get('pro_only', True))
        db.session.add(f)
        db.session.commit()
        return jsonify(f.as_dict())

    @app.route('/api/admin/features/<int:fid>', methods=['DELETE'])
    @admin_required
    def adm_feature_del(fid):
        n = PlanFeature.query.filter_by(id=fid).delete()
        db.session.commit()
        return jsonify(ok=bool(n))

    return dict(AccountMeta=AccountMeta, Person=Person, SavedItem=SavedItem, Activity=Activity,
                PlanFeature=PlanFeature, plan_of=plan_of, current_user=current_user)
