# -*- coding: utf-8 -*-
"""
numerology_routes.py — MAGNUS Flask blueprint for the 5 esoteric numerology methods.

Register in app.py:

    from numerology_routes import numerology_bp
    app.register_blueprint(numerology_bp)

Endpoints (all GET, all return JSON):

  /api/numerology/ninestarki?date=1988-03-23
  /api/numerology/arrows?date=1988-03-23[&extra=5,23]     # extra working numbers
  /api/numerology/ank?date=1988-03-23[&name=Alex]
  /api/numerology/ank/compat?date1=...&date2=...
  /api/numerology/gematria?text=שלום&system=hebrew|greek|arabic[&sofit=0]
  /api/numerology/chaldean?name=Alex
  /api/numerology/all?date=...&name=...                    # everything at once

Errors: {"error": "..."} with 400.
"""

from datetime import date, datetime
from flask import Blueprint, jsonify, request

from esoteric_numerology import (
    nine_star_ki, pythagoras_arrows, ank_jyotish, ank_compatibility,
    gematria, chaldean_name,
)

numerology_bp = Blueprint("numerology", __name__, url_prefix="/api/numerology")


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _require_date(param="date") -> date:
    s = request.args.get(param, "")
    if not s:
        raise ValueError(f"missing '{param}' (YYYY-MM-DD)")
    try:
        return _parse_date(s)
    except ValueError:
        raise ValueError(f"bad '{param}': expected YYYY-MM-DD, got '{s}'")

def _err(msg, code=400):
    return jsonify({"error": str(msg)}), code

def _lines_jsonable(arrow_result: dict) -> dict:
    """tuples -> lists for JSON."""
    out = dict(arrow_result)
    for key in ("strength_arrows", "lesson_arrows"):
        out[key] = [{**a, "line": list(a["line"])} for a in out[key]]
    return out


# ── endpoints ────────────────────────────────────────────────────────────────

@numerology_bp.get("/ninestarki")
def api_ninestarki():
    try:
        d = _require_date()
    except ValueError as e:
        return _err(e)
    return jsonify(nine_star_ki(d))


@numerology_bp.get("/arrows")
def api_arrows():
    try:
        d = _require_date()
        extra_raw = request.args.get("extra", "").strip()
        extra = [int(x) for x in extra_raw.split(",") if x.strip()] if extra_raw else None
    except ValueError as e:
        return _err(e)
    return jsonify(_lines_jsonable(pythagoras_arrows(d, extra)))


@numerology_bp.get("/ank")
def api_ank():
    try:
        d = _require_date()
    except ValueError as e:
        return _err(e)
    name = request.args.get("name", "")
    return jsonify(ank_jyotish(d, name))


@numerology_bp.get("/ank/compat")
def api_ank_compat():
    try:
        d1 = _require_date("date1")
        d2 = _require_date("date2")
    except ValueError as e:
        return _err(e)
    return jsonify(ank_compatibility(d1, d2))


@numerology_bp.get("/gematria")
def api_gematria():
    text = request.args.get("text", "")
    system = request.args.get("system", "hebrew").lower()
    use_sofit = request.args.get("sofit", "1") not in ("0", "false", "no")
    if not text:
        return _err("missing 'text'")
    if system not in ("hebrew", "greek", "arabic", "abjad"):
        return _err("system must be hebrew | greek | arabic")
    return jsonify(gematria(text, system, use_sofit=use_sofit))


@numerology_bp.get("/chaldean")
def api_chaldean():
    name = request.args.get("name", "")
    if not name.strip():
        return _err("missing 'name'")
    return jsonify(chaldean_name(name))


@numerology_bp.get("/all")
def api_all():
    try:
        d = _require_date()
    except ValueError as e:
        return _err(e)
    name = request.args.get("name", "")
    out = {
        "nine_star_ki": nine_star_ki(d),
        "arrows": _lines_jsonable(pythagoras_arrows(d)),
        "ank_jyotish": ank_jyotish(d, name),
        "chaldean": chaldean_name(name) if name.strip() else None,
    }
    return jsonify(out)
