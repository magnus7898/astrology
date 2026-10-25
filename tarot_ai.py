"""AI reading for a finished tarot spread (tarot.html → POST /api/tarot/ai).

The Anthropic API key lives ONLY in the server environment (Railway → Variables):
    ANTHROPIC_API_KEY   required — without it the feature is off and the button stays hidden
    TAROT_AI_MODEL      optional, default claude-sonnet-5-5
    TAROT_AI_WAIT       optional, seconds between readings of the same spread per device/IP (default 600)
    TAROT_AI_IP_DAILY   optional, readings per IP per day (default 20)
    TAROT_AI_DAILY      optional, readings per day for the whole site (default 300) — caps the cost
The key is never sent to the browser and never written to logs.
Limits are kept in the database, so they hold across restarts and when a visitor clears the browser.
"""
import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

_ID = re.compile(r'^[A-Za-z0-9_\-]{1,64}$')

SYSTEM = (
    "შენ ხარ გამოცდილი, თბილი და პატიოსანი ტაროს მკითხველი ქართულ ეზოთერულ პლატფორმა MAGNUS-ზე. "
    "მოგეცემა გაშლის სახელი, კითხვა (თუ არის) და ბარათები თავიანთ პოზიციებზე. "
    "დაწერე ერთიანი ინტერპრეტაცია ქართულად: ბარათები ერთმანეთთან დააკავშირე, პოზიციების აზრი გაითვალისწინე, "
    "შებრუნებული ბარათი წაიკითხე როგორც დაბლოკილი, შინაგანი ან ჯერ დაუმუშავებელი ენერგია. "
    "ნუ ჩამოთვლი თითოეული ბარათის სახელმძღვანელოს მნიშვნელობას — აჩვენე, რას ამბობს გაშლა მთლიანად. "
    "დაასრულე მოკლე, პრაქტიკული რჩევით. 3–6 მოკლე აბზაცი, სულ არაუმეტეს 350 სიტყვისა. "
    "სათაურები და მარკდაუნი არ გამოიყენო, გარდა **მსხვილისა** ბარათის სახელებისთვის. "
    "ჯანმრთელობის, სამართლის ან ფინანსების საკითხებში ნუ მისცემ კატეგორიულ პროგნოზს — ურჩიე სპეციალისტთან კონსულტაცია. "
    "ნუ იწინასწარმეტყველებ სიკვდილს ან უბედურებას."
)


def init_tarot_ai(app, db):
    from flask import request, jsonify

    class TarotAICall(db.Model):
        """One AI reading request — used only for rate limits."""
        id = db.Column(db.Integer, primary_key=True)
        device = db.Column(db.String(64), index=True)
        ip = db.Column(db.String(64), index=True)
        spread = db.Column(db.String(64), index=True)
        created = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def env_int(name, default):
        try:
            return max(0, int(os.environ.get(name, default)))
        except ValueError:
            return default

    def key():
        return (os.environ.get('ANTHROPIC_API_KEY') or '').strip()

    def client_ip():
        fwd = request.headers.get('X-Forwarded-For', '')
        return (fwd.split(',')[0].strip() or request.remote_addr or '?')[:64]

    def clip(v, n):
        return re.sub(r'\s+', ' ', str(v or '')).strip()[:n]

    @app.route('/api/tarot/ai/status', methods=['GET'])
    def tarot_ai_status():
        return jsonify(enabled=bool(key()), wait=env_int('TAROT_AI_WAIT', 600))

    @app.route('/api/tarot/ai', methods=['POST'])
    def tarot_ai():
        api_key = key()
        if not api_key:
            return jsonify(error='off'), 503
        d = request.get_json(silent=True) or {}
        spread = str(d.get('spread') or '')
        device = str(d.get('device') or '')
        if not _ID.match(spread) or not _ID.match(device):
            return jsonify(error='bad request'), 400
        cards = d.get('cards')
        if not isinstance(cards, list) or not 1 <= len(cards) <= 26:
            return jsonify(error='bad cards'), 400
        lines = []
        for i, c in enumerate(cards):
            if not isinstance(c, dict):
                return jsonify(error='bad cards'), 400
            name = clip(c.get('name'), 80)
            if not name:
                return jsonify(error='bad cards'), 400
            pos, desc = clip(c.get('pos'), 80), clip(c.get('desc'), 200)
            lines.append(f"{i + 1}. {pos}{' — ' + desc if desc else ''}: {name}"
                         f"{' (შებრუნებული)' if c.get('rev') else ''}")
        title = clip(d.get('title'), 120)
        question = clip(d.get('question'), 300)

        ip, now = client_ip(), datetime.utcnow()
        wait = env_int('TAROT_AI_WAIT', 600)
        if wait:
            since = now - timedelta(seconds=wait)
            last = (TarotAICall.query
                    .filter(TarotAICall.spread == spread, TarotAICall.created > since,
                            db.or_(TarotAICall.device == device, TarotAICall.ip == ip))
                    .order_by(TarotAICall.created.desc()).first())
            if last:
                left = int(wait - (now - last.created).total_seconds()) + 1
                return jsonify(error='wait', retry_after=max(1, left)), 429
        day0 = now - timedelta(days=1)
        if TarotAICall.query.filter(TarotAICall.ip == ip, TarotAICall.created > day0).count() >= env_int('TAROT_AI_IP_DAILY', 20):
            return jsonify(error='daily'), 429
        if TarotAICall.query.filter(TarotAICall.created > day0).count() >= env_int('TAROT_AI_DAILY', 300):
            return jsonify(error='site daily'), 429

        row = TarotAICall(device=device, ip=ip, spread=spread, created=now)
        db.session.add(row)
        db.session.commit()

        user = (f"გაშლა: {title or spread}\n"
                f"კითხვა: {question or '— (კითხვა არ დაუსვამს)'}\n\nბარათები:\n" + "\n".join(lines))
        body = json.dumps({
            'model': os.environ.get('TAROT_AI_MODEL') or 'claude-sonnet-5-5',
            'max_tokens': 1400,
            'system': SYSTEM,
            'messages': [{'role': 'user', 'content': user}],
        }).encode('utf-8')
        req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, method='POST', headers={
            'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.loads(r.read().decode('utf-8'))
            text = ''.join(b.get('text', '') for b in out.get('content', []) if b.get('type') == 'text').strip()
            if not text:
                raise ValueError('empty answer')
        except Exception as e:  # do not count a failed call against the visitor
            code = e.code if isinstance(e, urllib.error.HTTPError) else type(e).__name__
            print('tarot ai error:', code)
            db.session.delete(row)
            db.session.commit()
            return jsonify(error='upstream'), 502
        return jsonify(text=text, wait=wait)

    return TarotAICall
