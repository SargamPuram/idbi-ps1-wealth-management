"""
PS1 — Digital Wealth Management: "Dhanvi" AI Wealth Advisor (backend)
FastAPI serving layer. Run with:
    ./venv/Scripts/python -m uvicorn app.main:app --reload --port 8003
"""
import random
import string
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from advisory import data_store, finance
from advisory.engine import DhanviEngine, GeminiUnavailable, detect_escalation
from advisory.tts_engine import TTSUnavailable, tts_engine
from app.schemas import ChatRequest, EscalateRequest, GoalPlanRequest, SuitabilityRequest, TTSRequest

app = FastAPI(
    title="PS1 — Dhanvi Wealth Advisory API",
    description="AI-powered Financial Digital Twin + Wealth Coach for IDBI Bank",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DhanviEngine()

# in-memory escalation ticket store (prototype only)
_escalation_tickets = []
RM_NAMES = ["Rohan Mehta", "Priya Nair", "Arjun Kapoor", "Sneha Iyer", "Vikram Singh", "Anjali Rao"]


def _customer_or_404(customer_id: str) -> dict:
    customer = data_store.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return customer


# Gemini's free-tier quota is shared across every AI-backed endpoint, and both
# /market-pulse and /insights fire automatically on page load (not user-
# initiated like /chat) -- so simply browsing between pages was silently
# burning requests. A short TTL cache keeps repeated page visits within a
# few minutes from re-hitting Gemini for what's effectively the same content.
_AI_CACHE: dict[tuple, tuple[float, object]] = {}
_AI_CACHE_TTL_SECONDS = 600


def _cached_ai_call(cache_key: tuple, fn):
    now = time.time()
    cached = _AI_CACHE.get(cache_key)
    if cached is not None and now - cached[0] < _AI_CACHE_TTL_SECONDS:
        return cached[1]
    value = fn()
    _AI_CACHE[cache_key] = (now, value)
    return value


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "PS1 Dhanvi Wealth Advisory API",
        "customers_loaded": data_store.count(),
        "gemini": engine.status(),
        "tts": tts_engine.status(),
        "sample_customer_ids": data_store.sample_ids(5),
    }


# ---------------------------------------------------------------------------
# Chat (Gemini-powered, graceful degradation)
# ---------------------------------------------------------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    customer = _customer_or_404(req.customer_id)
    language = req.language or customer.get("language_preference", "English")
    history = [h.model_dump() for h in (req.conversation_history or [])]

    if not engine.is_available:
        escalation_needed, escalation_reason = detect_escalation(req.message, "")
        return {
            "response": (
                "Namaste! I'm Dhanvi. My AI reasoning engine isn't connected yet — the bank's tech team needs to "
                "set the DEEPSEEK_API_KEY environment variable before I can chat freely. In the meantime, you can "
                "still explore your Portfolio, Goal Planner, Market Pulse and Product Catalog — those work fully "
                "without me. Once the team plugs in the key, just retry this chat."
            ),
            "ai_powered": False,
            "gemini_status_message": engine.init_error,
            "product_recommendations": finance.recommend_products(customer)[:2],
            "escalation_needed": escalation_needed,
            "escalation_reason": escalation_reason,
            "language": language,
        }

    try:
        reply_text = engine.chat(customer, req.message, language, history=history)
    except GeminiUnavailable as e:
        return {
            "response": (
                "I'm having trouble reaching my AI reasoning engine right now. Please try again shortly, or "
                "explore Portfolio / Goals / Market Pulse / Products in the meantime."
            ),
            "ai_powered": False,
            "gemini_status_message": str(e),
            "product_recommendations": [],
            "escalation_needed": False,
            "escalation_reason": None,
            "language": language,
        }

    escalation_needed, escalation_reason = detect_escalation(req.message, reply_text)
    recs = finance.recommend_products(customer)[:2]

    return {
        "response": reply_text,
        "ai_powered": True,
        "gemini_status_message": None,
        "product_recommendations": recs,
        "escalation_needed": escalation_needed,
        "escalation_reason": escalation_reason,
        "language": language,
    }


# ---------------------------------------------------------------------------
# Text-to-speech (Piper, self-hosted, CPU-only — decoupled from /chat so text
# generation never waits on audio synthesis; the frontend calls /chat first,
# then fires a separate /tts request for the returned text).
# ---------------------------------------------------------------------------
@app.post("/tts")
def tts(req: TTSRequest):
    try:
        audio_bytes = tts_engine.synthesize(req.text, req.language)
    except TTSUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return Response(content=audio_bytes, media_type="audio/wav")


# ---------------------------------------------------------------------------
# Portfolio overview
# ---------------------------------------------------------------------------
@app.get("/portfolio/{customer_id}")
def get_portfolio(customer_id: str):
    customer = _customer_or_404(customer_id)
    portfolio = customer["portfolio"]
    breakdown = portfolio["asset_breakdown"]
    total = max(portfolio["total_net_worth"], 1)
    allocation_pct = {k: round(v / total * 100, 2) for k, v in breakdown.items()}

    mf_invested = sum(m["invested_amount"] for m in portfolio["mutual_funds"])
    mf_current = sum(m["current_value"] for m in portfolio["mutual_funds"])
    mf_returns_pct = round((mf_current - mf_invested) / mf_invested * 100, 2) if mf_invested else 0

    stock_invested = sum(s["quantity"] * s["avg_price"] for s in portfolio["stocks"])
    stock_current = sum(s["quantity"] * s["current_price"] for s in portfolio["stocks"])
    stock_returns_pct = round((stock_current - stock_invested) / stock_invested * 100, 2) if stock_invested else 0

    num_asset_classes = sum(1 for v in breakdown.values() if v > 0)
    diversification_score = min(round(num_asset_classes / 7 * 100), 100)

    return {
        "customer_id": customer_id,
        "name": customer["name"],
        "customer_segment": customer["customer_segment"],
        "risk_profile": customer["risk_profile"],
        "total_net_worth": portfolio["total_net_worth"],
        "asset_breakdown": breakdown,
        "asset_allocation_pct": allocation_pct,
        "holdings": {
            "fixed_deposits": portfolio["fixed_deposits"],
            "mutual_funds": portfolio["mutual_funds"],
            "insurance": portfolio["insurance"],
            "nps": portfolio["nps"],
            "stocks": portfolio["stocks"],
            "gold": portfolio["gold"],
            "ppf": portfolio["ppf"],
        },
        "analytics": {
            "mutual_funds_returns_pct": mf_returns_pct,
            "stocks_returns_pct": stock_returns_pct,
            "diversification_score": diversification_score,
            "monthly_sip_total": customer["financials"]["monthly_sip_total"],
        },
        "goals": customer["goals"],
    }


# ---------------------------------------------------------------------------
# Suitability assessment
# ---------------------------------------------------------------------------
@app.get("/suitability/questions")
def suitability_questions():
    return {"questions": finance.SUITABILITY_QUESTIONS}


@app.post("/suitability")
def suitability(req: SuitabilityRequest):
    if req.customer_id:
        _customer_or_404(req.customer_id)
    result = finance.score_suitability(req.answers)
    return result


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
@app.get("/recommendations/{customer_id}")
def recommendations(customer_id: str):
    customer = _customer_or_404(customer_id)
    recs = finance.recommend_products(customer)
    return {"customer_id": customer_id, "recommendations": recs}


# ---------------------------------------------------------------------------
# Market pulse
# ---------------------------------------------------------------------------
@app.get("/market-pulse")
def market_pulse(customer_id: str | None = Query(default=None), language: str = Query(default="English")):
    snapshot = finance.simulated_market_snapshot()

    commentary = None
    ai_powered = False
    if engine.is_available:
        try:
            commentary = _cached_ai_call(
                ("market_commentary", snapshot["date"], language),
                lambda: engine.market_commentary(snapshot, language=language),
            )
            ai_powered = True
        except GeminiUnavailable:
            commentary = None
    if commentary is None:
        commentary = finance.fallback_market_commentary(snapshot)

    result = {
        "date": snapshot["date"],
        "sensex": snapshot["sensex"],
        "nifty": snapshot["nifty"],
        "gold_change_pct": snapshot["gold_change_pct"],
        "commentary": commentary,
        "commentary_ai_powered": ai_powered,
    }

    if customer_id:
        customer = _customer_or_404(customer_id)
        result["portfolio_impact"] = finance.portfolio_market_impact(customer, snapshot)

    return result


# ---------------------------------------------------------------------------
# Goal planner
# ---------------------------------------------------------------------------
@app.post("/goal-plan")
def goal_plan(req: GoalPlanRequest):
    risk_profile = req.risk_profile
    if req.customer_id:
        customer = _customer_or_404(req.customer_id)
        risk_profile = risk_profile or customer["risk_profile"]
    risk_profile = risk_profile or "Moderate"

    plan = finance.goal_plan(
        goal_type=req.goal_type,
        target_amount=req.target_amount,
        target_date=req.target_date,
        current_progress=req.current_progress,
        risk_profile=risk_profile,
    )
    return plan


# ---------------------------------------------------------------------------
# Product catalog
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = {
    "FDs": [
        {"name": "IDBI Bank Regular Fixed Deposit", "risk": "Low", "returns_range": "6.5% - 7.75%",
         "min_investment": 10000, "lock_in": "7 days - 10 years", "tags": ["Conservative", "Moderate", "Aggressive"]},
        {"name": "IDBI Bank Senior Citizen FD", "risk": "Low", "returns_range": "7.0% - 8.25%",
         "min_investment": 10000, "lock_in": "7 days - 10 years", "tags": ["Conservative"]},
        {"name": "IDBI Bank Tax Saver FD (80C)", "risk": "Low", "returns_range": "6.75% - 7.25%",
         "min_investment": 100, "lock_in": "5 years", "tags": ["Conservative", "Moderate"]},
    ],
    "MFs": [
        {"name": "IDBI Focused Equity Fund", "risk": "High", "returns_range": "11% - 15% (historical)",
         "min_investment": 500, "lock_in": "None (open-ended)", "tags": ["Aggressive"]},
        {"name": "IDBI Hybrid Advantage Fund", "risk": "Moderate", "returns_range": "9% - 12% (historical)",
         "min_investment": 500, "lock_in": "None (open-ended)", "tags": ["Moderate"]},
        {"name": "IDBI Short Term Bond Fund", "risk": "Low", "returns_range": "6.5% - 8% (historical)",
         "min_investment": 500, "lock_in": "None (open-ended)", "tags": ["Conservative"]},
        {"name": "IDBI Nifty Index Fund", "risk": "Moderate-High", "returns_range": "10% - 13% (historical)",
         "min_investment": 500, "lock_in": "None (open-ended)", "tags": ["Moderate", "Aggressive"]},
    ],
    "Insurance": [
        {"name": "LIC Tech Term Plan", "risk": "N/A (Protection)", "returns_range": "N/A",
         "min_investment": 6000, "lock_in": "Policy term", "tags": ["Conservative", "Moderate", "Aggressive"],
         "regulated": True, "provider": "LIC"},
        {"name": "LIC New Jeevan Anand (Endowment)", "risk": "Low", "returns_range": "5% - 6% (historical)",
         "min_investment": 15000, "lock_in": "Policy term", "tags": ["Conservative"],
         "regulated": True, "provider": "LIC"},
        {"name": "IDBI Federal Growth Insurance Plan (ULIP)", "risk": "Moderate-High",
         "returns_range": "8% - 12% (market-linked)", "min_investment": 25000, "lock_in": "5 years",
         "tags": ["Moderate", "Aggressive"], "regulated": True, "provider": "IDBI Federal"},
    ],
    "NPS": [
        {"name": "NPS Tier 1 (Auto Choice)", "risk": "Moderate", "returns_range": "9% - 11% (historical)",
         "min_investment": 500, "lock_in": "Till age 60", "tags": ["Conservative", "Moderate", "Aggressive"]},
        {"name": "NPS Tier 2 (Voluntary)", "risk": "Moderate", "returns_range": "9% - 11% (historical)",
         "min_investment": 250, "lock_in": "None", "tags": ["Moderate", "Aggressive"]},
    ],
    "Gold": [
        {"name": "Sovereign Gold Bonds (SGB)", "risk": "Moderate", "returns_range": "Gold price + 2.5% p.a.",
         "min_investment": 5000, "lock_in": "8 years (5 yr exit window)", "tags": ["Conservative", "Moderate"]},
        {"name": "IDBI Digital Gold", "risk": "Moderate", "returns_range": "Tracks gold price",
         "min_investment": 100, "lock_in": "None", "tags": ["Conservative", "Moderate", "Aggressive"]},
    ],
    "PPF": [
        {"name": "Public Provident Fund", "risk": "Low", "returns_range": "7.1% (govt set, tax-free)",
         "min_investment": 500, "lock_in": "15 years", "tags": ["Conservative", "Moderate"]},
    ],
    "Bonds": [
        {"name": "RBI Floating Rate Savings Bonds", "risk": "Low", "returns_range": "~8.05% (floating)",
         "min_investment": 1000, "lock_in": "7 years", "tags": ["Conservative"]},
        {"name": "IDBI Corporate Bonds (AAA)", "risk": "Low-Moderate", "returns_range": "7.5% - 8.5%",
         "min_investment": 10000, "lock_in": "3-10 years", "tags": ["Conservative", "Moderate"]},
    ],
}


@app.get("/products")
def products(customer_id: str | None = Query(default=None)):
    customer = data_store.get_customer(customer_id) if customer_id else None
    risk_profile = customer["risk_profile"] if customer else None

    catalog = {}
    for category, items in PRODUCT_CATALOG.items():
        enriched = []
        for item in items:
            item_copy = dict(item)
            item_copy["recommended_for_you"] = bool(risk_profile and risk_profile in item.get("tags", []))
            enriched.append(item_copy)
        catalog[category] = enriched

    return {"categories": catalog, "personalized_for": customer_id}


# ---------------------------------------------------------------------------
# Customer insights
# ---------------------------------------------------------------------------
@app.get("/customer/{customer_id}/insights")
def customer_insights(customer_id: str, language: str = Query(default="English")):
    customer = _customer_or_404(customer_id)
    insights = finance.spending_insights(customer)

    ai_tip = None
    ai_powered = False
    if engine.is_available:
        try:
            ai_tip = _cached_ai_call(
                ("spending_tip", customer_id, language),
                lambda: engine.spending_tip(insights, language=language),
            )
            ai_powered = True
        except GeminiUnavailable:
            ai_tip = None
    if ai_tip is None:
        ai_tip = insights["tips"][0]

    insights["ai_tip"] = ai_tip
    insights["ai_tip_ai_powered"] = ai_powered
    return insights


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------
@app.post("/escalate")
def escalate(req: EscalateRequest):
    customer = _customer_or_404(req.customer_id)
    ticket_id = "ESC-" + "".join(random.choices(string.digits, k=8))
    rm_name = random.choice(RM_NAMES)
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": req.customer_id,
        "customer_name": customer["name"],
        "reason": req.reason,
        "context_summary": req.context_summary,
        "conversation_snippet": req.conversation_snippet,
        "assigned_rm": rm_name,
        "status": "Open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sla_hours": 24,
    }
    _escalation_tickets.append(ticket)
    return {
        "message": f"Your query has been escalated to {rm_name}, an IDBI Relationship Manager, who will "
                   f"contact you within 24 hours.",
        "ticket": ticket,
    }


@app.get("/escalate/tickets")
def list_tickets():
    """Convenience endpoint for testing/demo — lists escalation tickets raised this session."""
    return {"tickets": _escalation_tickets}
