"""
Rule-based / formula-driven financial calculations that do NOT require Gemini:
goal planning (SIP math), suitability scoring, product recommendations,
spending insights, and simulated market data. Keeping these Gemini-free means
the majority of the API stays fully testable even without an API key.
"""
import hashlib
import math
import random
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Assumed nominal annual returns by risk profile (used across goal planning &
# recommendations). Realistic long-run Indian market assumptions for a demo.
# ---------------------------------------------------------------------------
RETURN_ASSUMPTIONS = {
    "Conservative": {"equity": 0.11, "debt": 0.075, "gold": 0.08, "blended": 0.075},
    "Moderate": {"equity": 0.12, "debt": 0.07, "gold": 0.08, "blended": 0.095},
    "Aggressive": {"equity": 0.13, "debt": 0.065, "gold": 0.08, "blended": 0.115},
}

ASSET_ALLOCATION_MODEL = {
    "Conservative": {"Equity": 20, "Debt": 55, "Gold": 10, "Cash/FD": 15},
    "Moderate": {"Equity": 45, "Debt": 35, "Gold": 10, "Cash/FD": 10},
    "Aggressive": {"Equity": 70, "Debt": 15, "Gold": 10, "Cash/FD": 5},
}

GOAL_INSTRUMENT_MAP = {
    "Retirement": ["NPS Tier 1", "Equity Mutual Funds (SIP)", "PPF"],
    "Child Education": ["Equity Mutual Funds (SIP)", "Sukanya Samriddhi (if girl child)", "Child ULIP"],
    "Home Purchase": ["Debt Mutual Funds", "Recurring Deposit", "IDBI Home Loan (pre-approved)"],
    "Emergency Fund": ["Liquid Mutual Funds", "Sweep-in Fixed Deposit"],
    "Wealth Growth": ["Equity Mutual Funds (SIP)", "Direct Equity", "Sovereign Gold Bonds"],
    "Vacation": ["Recurring Deposit", "Short-term Debt Fund"],
    "Wedding": ["Debt Mutual Funds", "Recurring Deposit", "Gold (SGB)"],
}


def months_between(target_date_str: str) -> int:
    target = datetime.fromisoformat(target_date_str).date()
    today = date.today()
    months = (target.year - today.year) * 12 + (target.month - today.month)
    return max(months, 1)


def future_value_of_lumpsum(present_value: float, annual_rate: float, years: float) -> float:
    return present_value * (1 + annual_rate) ** years


def sip_required_for_target(target_amount: float, current_progress: float, years: float, annual_rate: float) -> float:
    """Standard SIP future-value-of-annuity-due formula, solved for monthly payment."""
    months = max(int(round(years * 12)), 1)
    monthly_rate = annual_rate / 12
    fv_of_existing = future_value_of_lumpsum(current_progress, annual_rate, years)
    remaining_target = max(target_amount - fv_of_existing, 0)
    if remaining_target <= 0:
        return 0.0
    if monthly_rate == 0:
        return remaining_target / months
    # FV of annuity due: FV = P * [((1+r)^n - 1) / r] * (1+r)
    factor = (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    monthly_sip = remaining_target / factor
    return round(monthly_sip, -1)


def projected_growth_series(current_progress: float, monthly_sip: float, years: float, annual_rate: float):
    """Year-by-year projected corpus value assuming monthly_sip continues."""
    monthly_rate = annual_rate / 12
    months_total = max(int(round(years * 12)), 1)
    series = []
    balance = current_progress
    for m in range(1, months_total + 1):
        balance = balance * (1 + monthly_rate) + monthly_sip
        if m % 12 == 0 or m == months_total:
            series.append({"year": math.ceil(m / 12), "projected_value": round(balance, -2)})
    return series


def goal_plan(goal_type: str, target_amount: float, target_date: str, current_progress: float, risk_profile: str):
    months = months_between(target_date)
    years = months / 12
    profile = risk_profile if risk_profile in RETURN_ASSUMPTIONS else "Moderate"
    rate = RETURN_ASSUMPTIONS[profile]["blended"]

    scenarios = {}
    for label, rp in [("conservative", "Conservative"), ("moderate", "Moderate"), ("aggressive", "Aggressive")]:
        r = RETURN_ASSUMPTIONS[rp]["blended"]
        sip = sip_required_for_target(target_amount, current_progress, years, r)
        scenarios[label] = {
            "assumed_annual_return_pct": round(r * 100, 1),
            "monthly_sip_needed": sip,
            "growth_projection": projected_growth_series(current_progress, sip, years, r),
        }

    profile_label = {"Conservative": "conservative", "Moderate": "moderate", "Aggressive": "aggressive"}[profile]
    recommended_sip = scenarios[profile_label]["monthly_sip_needed"]

    instruments = GOAL_INSTRUMENT_MAP.get(goal_type, ["Balanced Mutual Funds", "Fixed Deposit"])

    return {
        "goal_type": goal_type,
        "target_amount": target_amount,
        "target_date": target_date,
        "years_to_goal": round(years, 1),
        "current_progress": current_progress,
        "risk_profile_used": profile,
        "recommended_monthly_sip": recommended_sip,
        "recommended_instruments": instruments,
        "scenarios": scenarios,
    }


# ---------------------------------------------------------------------------
# Suitability / risk-profiling questionnaire
# ---------------------------------------------------------------------------
SUITABILITY_QUESTIONS = [
    {"id": 1, "question": "What is your age group?",
     "options": ["Below 30", "30-45", "46-55", "56-65", "Above 65"]},
    {"id": 2, "question": "What is your primary investment objective?",
     "options": ["Capital protection", "Regular income", "Balanced growth", "Wealth creation", "Aggressive growth"]},
    {"id": 3, "question": "How long can you stay invested before needing this money?",
     "options": ["Less than 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"]},
    {"id": 4, "question": "If your portfolio fell 20% in a month, what would you do?",
     "options": ["Sell everything immediately", "Sell a portion", "Do nothing", "Invest a little more", "Invest significantly more"]},
    {"id": 5, "question": "How much investment experience do you have?",
     "options": ["None", "FDs/savings only", "Some mutual funds", "Mutual funds + stocks", "Active trader"]},
    {"id": 6, "question": "What % of your monthly income can you invest regularly?",
     "options": ["Less than 5%", "5-10%", "10-20%", "20-30%", "More than 30%"]},
    {"id": 7, "question": "Do you have an emergency fund covering 6 months of expenses?",
     "options": ["No emergency fund", "1-2 months covered", "3-4 months covered", "5-6 months covered", "More than 6 months"]},
    {"id": 8, "question": "How would you describe your income stability?",
     "options": ["Highly uncertain", "Somewhat uncertain", "Stable", "Very stable", "Guaranteed (govt/pension)"]},
    {"id": 9, "question": "What return would satisfy you, accepting the matching risk?",
     "options": ["6-7% (very safe)", "7-9% (safe)", "9-12% (moderate)", "12-15% (higher risk)", "15%+ (high risk)"]},
    {"id": 10, "question": "How do you feel about investing in equity markets?",
     "options": ["Very uncomfortable", "Somewhat uncomfortable", "Neutral", "Comfortable", "Very comfortable"]},
]


def score_suitability(answers: dict) -> dict:
    """answers: {question_id (1-10): option_index (0-4)}"""
    total = 0
    max_total = len(SUITABILITY_QUESTIONS) * 4
    for q in SUITABILITY_QUESTIONS:
        idx = answers.get(str(q["id"]), answers.get(q["id"], 2))
        idx = max(0, min(4, int(idx)))
        total += idx
    pct = total / max_total

    if pct < 0.35:
        profile = "Conservative"
    elif pct < 0.65:
        profile = "Moderate"
    else:
        profile = "Aggressive"

    allocation = ASSET_ALLOCATION_MODEL[profile]
    rationale = {
        "Conservative": "Your responses indicate low risk tolerance and/or a short investment horizon. "
                         "We recommend capital protection first, with a modest equity allocation for inflation-beating growth.",
        "Moderate": "Your responses indicate a balanced risk appetite with a medium-to-long horizon. "
                    "A diversified mix of equity and debt should help you grow wealth while managing volatility.",
        "Aggressive": "Your responses indicate high risk tolerance, investment experience, and a long horizon. "
                      "A growth-oriented, equity-heavy portfolio is suitable, provided you stay invested through volatility.",
    }[profile]

    return {
        "score": total,
        "max_score": max_total,
        "score_pct": round(pct * 100, 1),
        "risk_profile": profile,
        "recommended_asset_allocation": allocation,
        "rationale": rationale,
    }


# ---------------------------------------------------------------------------
# Product recommendations (rule-based, portfolio-gap driven)
# ---------------------------------------------------------------------------
def recommend_products(customer: dict) -> list:
    recs = []
    portfolio = customer["portfolio"]
    segment = customer["customer_segment"]
    risk = customer["risk_profile"]
    age = customer["age"]

    # 1. No emergency fund / low liquid buffer
    monthly_income = customer["financials"]["monthly_income"]
    fd_total = portfolio["asset_breakdown"]["fixed_deposits"]
    if fd_total < monthly_income * 3:
        recs.append({
            "product": "IDBI Bank Liquid Fund / Sweep-in FD",
            "category": "Emergency Fund",
            "reason": "Your liquid buffer covers less than 3 months of income. Building an emergency fund reduces "
                       "the need to break long-term investments during a crisis.",
            "regulated": False,
            "priority": "High",
        })

    # 2. No NPS despite being under 55
    if age < 55 and portfolio["nps"]["monthly_contribution"] == 0:
        recs.append({
            "product": "NPS Tier 1 (National Pension System)",
            "category": "Retirement",
            "reason": "You have no active NPS contribution. NPS offers an additional ₹50,000 tax deduction under "
                       "Section 80CCD(1B), over and above the ₹1.5L Section 80C limit.",
            "regulated": False,
            "priority": "Medium",
        })

    # 3. Under-insured (sum assured < 10x annual income) — term insurance
    term_cover = sum(p["sum_assured"] for p in portfolio["insurance"] if p["type"] == "Term")
    if term_cover < customer["annual_income"] * 10:
        recs.append({
            "product": "IDBI Federal iSurance Term Plan",
            "category": "Insurance",
            "reason": "Your term life cover is below the recommended 10x annual income. Pure term insurance gives "
                       "maximum cover at the lowest premium.",
            "regulated": True,
            "priority": "High",
        })

    # 4. Equity allocation mismatch vs risk profile
    total_worth = max(portfolio["total_net_worth"], 1)
    equity_value = portfolio["asset_breakdown"]["mutual_funds"] * 0.6 + portfolio["asset_breakdown"]["stocks"]
    equity_pct = equity_value / total_worth * 100
    target_equity_pct = ASSET_ALLOCATION_MODEL.get(risk, ASSET_ALLOCATION_MODEL["Moderate"])["Equity"]
    if equity_pct < target_equity_pct - 15:
        recs.append({
            "product": "IDBI Focused Equity Fund (SIP)",
            "category": "Mutual Funds",
            "reason": f"Your equity exposure (~{equity_pct:.0f}%) is well below the {target_equity_pct}% suggested "
                      f"for your {risk} risk profile. A staggered SIP can help you rebalance without market timing risk.",
            "regulated": False,
            "priority": "Medium",
        })

    # 5. No PPF and in a tax bracket where it matters
    if portfolio["ppf"]["yearly_contribution"] == 0 and customer["annual_income"] > 500000:
        recs.append({
            "product": "Public Provident Fund (PPF)",
            "category": "Tax Saving",
            "reason": "PPF offers tax-free, sovereign-guaranteed returns and qualifies for Section 80C deduction — "
                       "a strong complement to market-linked investments.",
            "regulated": False,
            "priority": "Low",
        })

    # 6. HNI without gold/SGB diversification
    if segment in ("Affluent", "HNI") and portfolio["gold"]["sgb_units"] == 0:
        recs.append({
            "product": "Sovereign Gold Bonds (SGB)",
            "category": "Gold",
            "reason": "Sovereign Gold Bonds offer gold-linked returns plus 2.5% annual interest, with no GST or "
                       "storage cost — more tax-efficient than physical gold.",
            "regulated": False,
            "priority": "Low",
        })

    if not recs:
        recs.append({
            "product": "Portfolio Review with RM",
            "category": "Advisory",
            "reason": "Your portfolio looks well-diversified for your profile. Consider an annual review with an "
                       "IDBI Relationship Manager to fine-tune allocations.",
            "regulated": True,
            "priority": "Low",
        })

    return recs


# ---------------------------------------------------------------------------
# Spending insights
# ---------------------------------------------------------------------------
def spending_insights(customer: dict) -> dict:
    txns = customer["financials"]["transactions_last_6m"]
    categories_totals = {}
    for t in txns:
        for cat, amt in t["spending_categories"].items():
            categories_totals[cat] = categories_totals.get(cat, 0) + amt
    n = len(txns)
    avg_categories = {k: round(v / n, -1) for k, v in categories_totals.items()}
    avg_income = sum(t["income"] for t in txns) / n
    avg_spend = sum(t["total_spending"] for t in txns) / n
    avg_savings_rate = sum(t["savings_rate"] for t in txns) / n

    needs_categories = {"housing", "food", "transport", "utility", "health"}
    wants_categories = {"shopping", "entertainment"}
    needs_total = sum(v for k, v in avg_categories.items() if k in needs_categories)
    wants_total = sum(v for k, v in avg_categories.items() if k in wants_categories)
    savings_total = avg_income - avg_spend

    rule_50_30_20 = {
        "needs_actual_pct": round(needs_total / avg_income * 100, 1) if avg_income else 0,
        "wants_actual_pct": round(wants_total / avg_income * 100, 1) if avg_income else 0,
        "savings_actual_pct": round(savings_total / avg_income * 100, 1) if avg_income else 0,
        "needs_target_pct": 50, "wants_target_pct": 30, "savings_target_pct": 20,
    }

    trend = [{"month": t["month"], "savings_rate": t["savings_rate"], "total_spending": t["total_spending"],
              "income": t["income"]} for t in txns]

    tips = []
    if rule_50_30_20["wants_actual_pct"] > 35:
        tips.append("Discretionary spending (shopping + entertainment) is higher than the recommended 30% of income — "
                     "small cuts here can meaningfully boost your SIP capacity.")
    if avg_savings_rate < 0.20:
        tips.append("Your average savings rate is below 20%. Consider automating a higher SIP right after salary credit.")
    if avg_savings_rate >= 0.30:
        tips.append("Excellent savings discipline — you're saving over 30% of income. Consider deploying the surplus "
                     "toward your longest-horizon goal for compounding benefit.")
    if not tips:
        tips.append("Your spending is broadly balanced. Keep tracking discretionary categories to sustain this.")

    return {
        "avg_monthly_income": round(avg_income, -1),
        "avg_monthly_spending": round(avg_spend, -1),
        "avg_savings_rate": round(avg_savings_rate, 3),
        "category_breakdown": avg_categories,
        "rule_50_30_20": rule_50_30_20,
        "trend_last_6_months": trend,
        "tips": tips,
    }


# ---------------------------------------------------------------------------
# Simulated market data (deterministic per-day seed so it's stable within a day
# but changes daily; no external market data API used in the prototype)
# ---------------------------------------------------------------------------
def _day_seed(extra: str = "") -> random.Random:
    key = date.today().isoformat() + extra
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


def simulated_market_snapshot() -> dict:
    rnd = _day_seed("market")
    sensex_base, nifty_base = 82150.35, 25010.60
    sensex_change_pct = round(rnd.uniform(-1.8, 1.8), 2)
    nifty_change_pct = round(sensex_change_pct + rnd.uniform(-0.3, 0.3), 2)
    sensex_value = round(sensex_base * (1 + sensex_change_pct / 100), 2)
    nifty_value = round(nifty_base * (1 + nifty_change_pct / 100), 2)

    sparkline_sensex = []
    sparkline_nifty = []
    s, n = sensex_base, nifty_base
    for i in range(30):
        s = s * (1 + rnd.uniform(-0.9, 0.9) / 100)
        n = n * (1 + rnd.uniform(-0.9, 0.9) / 100)
        sparkline_sensex.append(round(s, 2))
        sparkline_nifty.append(round(n, 2))
    sparkline_sensex[-1] = sensex_value
    sparkline_nifty[-1] = nifty_value

    gold_change_pct = round(rnd.uniform(-0.8, 0.8), 2)

    return {
        "date": date.today().isoformat(),
        "sensex": {"value": sensex_value, "change_pct": sensex_change_pct, "sparkline": sparkline_sensex},
        "nifty": {"value": nifty_value, "change_pct": nifty_change_pct, "sparkline": sparkline_nifty},
        "gold_change_pct": gold_change_pct,
    }


def fallback_market_commentary(snapshot: dict) -> str:
    s = snapshot["sensex"]["change_pct"]
    n = snapshot["nifty"]["change_pct"]
    direction = "higher" if n >= 0 else "lower"
    magnitude = "sharply" if abs(n) > 1 else "modestly"
    return (
        f"Markets closed {magnitude} {direction} today — Sensex {'+' if s >= 0 else ''}{s}%, "
        f"Nifty {'+' if n >= 0 else ''}{n}%. Gold moved {snapshot['gold_change_pct']}%. "
        f"As always, short-term market swings shouldn't change a long-term, goal-based investment plan — "
        f"stay invested and continue your SIPs."
    )


def portfolio_market_impact(customer: dict, snapshot: dict) -> dict:
    portfolio = customer["portfolio"]
    equity_exposure = portfolio["asset_breakdown"]["mutual_funds"] * 0.6 + portfolio["asset_breakdown"]["stocks"]
    gold_exposure = portfolio["asset_breakdown"]["gold"]
    equity_impact = equity_exposure * (snapshot["nifty"]["change_pct"] / 100)
    gold_impact = gold_exposure * (snapshot["gold_change_pct"] / 100)
    total_impact = round(equity_impact + gold_impact, -1)
    return {
        "estimated_portfolio_change": total_impact,
        "equity_exposure_considered": round(equity_exposure, -1),
        "gold_exposure_considered": round(gold_exposure, -1),
    }
