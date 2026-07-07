"""
PS1 Digital Wealth Management — synthetic data generator.

Generates 5,000 realistic Indian customer wealth profiles: demographics,
existing portfolio holdings (FDs, mutual funds, insurance/LIC bancassurance,
NPS, stocks, gold, PPF), financial goals, and 6 months of spending/income
transactions. Output: data/customers.json (single source of truth consumed
by the FastAPI app) plus data/customers_summary.csv for quick inspection.

Run: ./venv/Scripts/python scripts/generate_data.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)

N_CUSTOMERS = 5000

CITIES = [
    # metros
    ("Mumbai", "Maharashtra", "Metro"), ("Delhi", "Delhi", "Metro"),
    ("Bengaluru", "Karnataka", "Metro"), ("Chennai", "Tamil Nadu", "Metro"),
    ("Kolkata", "West Bengal", "Metro"), ("Hyderabad", "Telangana", "Metro"),
    # tier 2
    ("Pune", "Maharashtra", "Tier2"), ("Ahmedabad", "Gujarat", "Tier2"),
    ("Jaipur", "Rajasthan", "Tier2"), ("Lucknow", "Uttar Pradesh", "Tier2"),
    ("Kochi", "Kerala", "Tier2"), ("Chandigarh", "Punjab", "Tier2"),
    ("Indore", "Madhya Pradesh", "Tier2"), ("Nagpur", "Maharashtra", "Tier2"),
    ("Coimbatore", "Tamil Nadu", "Tier2"), ("Bhopal", "Madhya Pradesh", "Tier2"),
    # tier 3
    ("Nashik", "Maharashtra", "Tier3"), ("Ranchi", "Jharkhand", "Tier3"),
    ("Guwahati", "Assam", "Tier3"), ("Varanasi", "Uttar Pradesh", "Tier3"),
    ("Madurai", "Tamil Nadu", "Tier3"), ("Raipur", "Chhattisgarh", "Tier3"),
    ("Dehradun", "Uttarakhand", "Tier3"), ("Siliguri", "West Bengal", "Tier3"),
]

OCCUPATIONS = [
    "Salaried - Private Sector", "Salaried - Government", "Salaried - PSU",
    "Self-Employed - Business Owner", "Self-Employed - Professional (Doctor/CA/Lawyer)",
    "Retired - Pensioner", "Homemaker (Independent Income)", "Freelancer/Consultant",
    "Farmer/Agriculturist", "NRI - Working Abroad",
]

LANGUAGES = ["English"] * 40 + ["Hindi"] * 35 + ["Tamil"] * 8 + ["Telugu"] * 7 + ["Bengali"] * 5 + ["Marathi"] * 5

MF_SCHEMES = [
    ("IDBI Focused Equity Fund", "Equity"), ("HDFC Top 100 Fund", "Equity"),
    ("SBI Bluechip Fund", "Equity"), ("Axis Midcap Fund", "Equity"),
    ("ICICI Pru Nifty Index Fund", "Equity"), ("Mirae Asset Large Cap Fund", "Equity"),
    ("Parag Parikh Flexi Cap Fund", "Equity"), ("Kotak Emerging Equity Fund", "Equity"),
    ("IDBI Short Term Bond Fund", "Debt"), ("HDFC Corporate Bond Fund", "Debt"),
    ("SBI Magnum Gilt Fund", "Debt"), ("Aditya Birla SL Liquid Fund", "Debt"),
    ("ICICI Pru Equity & Debt Fund", "Hybrid"), ("HDFC Balanced Advantage Fund", "Hybrid"),
    ("SBI Equity Hybrid Fund", "Hybrid"), ("IDBI Hybrid Advantage Fund", "Hybrid"),
]

INSURANCE_PRODUCTS = [
    ("Term", "LIC", "LIC Tech Term Plan"),
    ("Term", "IDBI Federal", "IDBI Federal iSurance Term"),
    ("Endowment", "LIC", "LIC New Jeevan Anand"),
    ("Endowment", "LIC", "LIC Jeevan Labh"),
    ("ULIP", "LIC", "LIC Nivesh Plus"),
    ("ULIP", "IDBI Federal", "IDBI Federal Growth Insurance Plan"),
    ("Health", "LIC", "LIC Health Protection Plus"),
    ("Endowment", "SBI Life", "SBI Life Smart Wealth Builder"),
]

STOCKS = [
    ("RELIANCE", 2800), ("TCS", 3900), ("HDFCBANK", 1650), ("INFY", 1550),
    ("ICICIBANK", 1150), ("IDBI", 95), ("ITC", 460), ("SBIN", 820),
    ("BHARTIARTL", 1550), ("LT", 3600), ("HINDUNILVR", 2400), ("TATAMOTORS", 950),
    ("MARUTI", 11500), ("ASIANPAINT", 2900), ("WIPRO", 480), ("SUNPHARMA", 1750),
]

GOAL_TYPES = ["Retirement", "Child Education", "Home Purchase", "Emergency Fund",
              "Wealth Growth", "Vacation", "Wedding"]

FDS_BANKS = ["IDBI Bank", "SBI", "HDFC Bank", "ICICI Bank", "Punjab National Bank", "Axis Bank"]

SPEND_CATEGORIES = ["food", "housing", "transport", "shopping", "health", "education",
                     "entertainment", "utility"]


def pick_segment():
    r = random.random()
    if r < 0.50:
        return "Mass"
    elif r < 0.85:
        return "Affluent"
    return "HNI"


def pick_risk_profile():
    r = random.random()
    if r < 0.30:
        return "Conservative"
    elif r < 0.70:
        return "Moderate"
    return "Aggressive"


def income_for_segment(segment):
    if segment == "Mass":
        return round(random.uniform(2, 5) * 100000, -3)
    if segment == "Affluent":
        return round(random.uniform(5, 25) * 100000, -3)
    return round(random.uniform(25, 100) * 100000, -3)


def gen_fds(segment):
    n = {"Mass": random.randint(0, 2), "Affluent": random.randint(1, 3), "HNI": random.randint(2, 5)}[segment]
    fds = []
    for _ in range(n):
        amount = round(random.uniform(0.5, 15) * 100000, -3) if segment != "Mass" else round(random.uniform(0.25, 3) * 100000, -3)
        tenure_months = random.choice([6, 12, 24, 36, 60])
        maturity = (date.today() + timedelta(days=tenure_months * 30)).isoformat()
        fds.append({
            "amount": amount,
            "rate": round(random.uniform(6.5, 7.75), 2),
            "tenure_months": tenure_months,
            "maturity_date": maturity,
            "bank": random.choice(FDS_BANKS),
        })
    return fds


def gen_mutual_funds(segment, risk_profile):
    n = {"Mass": random.randint(0, 2), "Affluent": random.randint(1, 4), "HNI": random.randint(3, 7)}[segment]
    funds = []
    weighted_types = {"Conservative": ["Debt"] * 5 + ["Hybrid"] * 4 + ["Equity"] * 1,
                       "Moderate": ["Debt"] * 2 + ["Hybrid"] * 4 + ["Equity"] * 4,
                       "Aggressive": ["Debt"] * 1 + ["Hybrid"] * 2 + ["Equity"] * 7}[risk_profile]
    for _ in range(n):
        want_type = random.choice(weighted_types)
        candidates = [s for s in MF_SCHEMES if s[1] == want_type] or MF_SCHEMES
        scheme_name, mtype = random.choice(candidates)
        invested = round(random.uniform(0.1, 8) * 100000, -3) if segment != "Mass" else round(random.uniform(0.05, 1.5) * 100000, -3)
        growth_factor = random.uniform(0.85, 1.65)
        current_value = round(invested * growth_factor, -2)
        sip_amount = random.choice([0, 500, 1000, 2000, 2500, 5000, 10000]) if random.random() < 0.7 else 0
        funds.append({
            "scheme_name": scheme_name,
            "type": mtype,
            "invested_amount": invested,
            "current_value": current_value,
            "sip_amount": sip_amount,
            "sip_date": random.randint(1, 28) if sip_amount > 0 else None,
        })
    return funds


def gen_insurance(segment):
    n = {"Mass": random.randint(1, 2), "Affluent": random.randint(1, 3), "HNI": random.randint(2, 4)}[segment]
    policies = []
    for _ in range(n):
        itype, provider, name = random.choice(INSURANCE_PRODUCTS)
        premium = {"Term": random.randint(8000, 25000), "Health": random.randint(10000, 35000),
                   "Endowment": random.randint(20000, 100000), "ULIP": random.randint(25000, 150000)}[itype]
        sum_assured = premium * random.randint(15, 60)
        maturity_year = date.today().year + random.randint(2, 30)
        policies.append({
            "type": itype,
            "provider": provider,
            "plan_name": name,
            "premium": premium,
            "premium_frequency": random.choice(["Annual", "Half-Yearly", "Monthly"]),
            "sum_assured": sum_assured,
            "maturity": f"{maturity_year}-{random.randint(1,12):02d}-01",
        })
    return policies


def gen_nps(age, segment):
    if segment == "Mass" and random.random() < 0.4:
        return {"tier1_balance": 0, "tier2_balance": 0, "monthly_contribution": 0}
    years_contributing = max(1, age - random.randint(22, 30))
    monthly = random.choice([1000, 2000, 3000, 5000, 8000, 10000])
    tier1 = round(monthly * 12 * years_contributing * random.uniform(1.1, 1.5), -2)
    tier2 = round(tier1 * random.uniform(0, 0.3), -2)
    return {"tier1_balance": max(tier1, 0), "tier2_balance": tier2, "monthly_contribution": monthly}


def gen_stocks(segment):
    if segment == "Mass":
        return []
    n = random.randint(2, 6) if segment == "Affluent" else random.randint(4, 12)
    chosen = random.sample(STOCKS, min(n, len(STOCKS)))
    holdings = []
    for symbol, price in chosen:
        qty = random.randint(5, 200) if segment == "Affluent" else random.randint(10, 500)
        avg_price = round(price * random.uniform(0.7, 1.1), 2)
        current_price = round(price * random.uniform(0.95, 1.2), 2)
        holdings.append({"symbol": symbol, "quantity": qty, "avg_price": avg_price, "current_price": current_price})
    return holdings


def gen_gold(segment):
    physical = round(random.uniform(0, 50) if segment != "Mass" else random.uniform(0, 15), 2)
    digital = round(random.uniform(0, 20), 2)
    sgb = random.randint(0, 40) if segment != "Mass" else random.randint(0, 5)
    return {"physical_grams": physical, "digital_grams": digital, "sgb_units": sgb}


def gen_ppf(age, segment):
    if segment == "HNI" and random.random() < 0.3:
        pass
    years = max(1, min(15, age - random.randint(22, 35)))
    yearly = random.choice([0, 12000, 25000, 50000, 100000, 150000])
    balance = round(yearly * years * random.uniform(1.1, 1.4), -2) if yearly > 0 else 0
    return {"balance": balance, "yearly_contribution": yearly}


def gen_goals(age, segment, net_worth):
    n = random.randint(2, 4)
    chosen = random.sample(GOAL_TYPES, n)
    goals = []
    for gtype in chosen:
        if gtype == "Retirement":
            target = round(net_worth * random.uniform(3, 8), -4) or 5000000
            years = max(60 - age, 3)
        elif gtype == "Child Education":
            target = random.choice([1500000, 2500000, 4000000, 6000000])
            years = random.randint(3, 15)
        elif gtype == "Home Purchase":
            target = random.choice([2500000, 4000000, 6000000, 9000000, 15000000])
            years = random.randint(2, 8)
        elif gtype == "Emergency Fund":
            target = random.choice([100000, 200000, 300000, 500000])
            years = random.randint(1, 2)
        elif gtype == "Wealth Growth":
            target = random.choice([2000000, 5000000, 10000000, 20000000])
            years = random.randint(5, 15)
        elif gtype == "Vacation":
            target = random.choice([100000, 200000, 400000, 800000])
            years = random.randint(1, 3)
        else:  # Wedding
            target = random.choice([500000, 1000000, 2000000, 3500000])
            years = random.randint(1, 6)
        progress_pct = round(random.uniform(0.05, 0.85), 3)
        current_progress = round(target * progress_pct, -2)
        target_date = (date.today() + timedelta(days=int(years * 365))).isoformat()
        remaining = max(target - current_progress, 0)
        months_left = max(years * 12, 1)
        monthly_needed = round(remaining / months_left, -1)
        goals.append({
            "type": gtype,
            "target_amount": target,
            "target_date": target_date,
            "current_progress": current_progress,
            "monthly_needed": monthly_needed,
        })
    return goals


def gen_transactions(monthly_income):
    months = []
    today = date.today()
    for i in range(6):
        m = today - timedelta(days=30 * (5 - i))
        base_spend_ratio = random.uniform(0.45, 0.85)
        total_spend = monthly_income * base_spend_ratio
        weights = {c: random.uniform(0.5, 1.5) for c in SPEND_CATEGORIES}
        wsum = sum(weights.values())
        categories = {c: round(total_spend * (w / wsum), -1) for c, w in weights.items()}
        actual_spend = sum(categories.values())
        savings_rate = round((monthly_income - actual_spend) / monthly_income, 3) if monthly_income else 0
        months.append({
            "month": m.strftime("%Y-%m"),
            "income": round(monthly_income, -1),
            "spending_categories": categories,
            "total_spending": round(actual_spend, -1),
            "savings_rate": savings_rate,
        })
    return months


def build_customer(cust_id):
    age = random.randint(22, 65)
    gender = random.choice(["Male", "Female"])
    name = fake.name_male() if gender == "Male" else fake.name_female()
    city, state, tier = random.choice(CITIES)
    segment = pick_segment()
    risk_profile = pick_risk_profile()
    occupation = random.choice(OCCUPATIONS)
    annual_income = income_for_segment(segment)
    language = random.choice(LANGUAGES)

    fds = gen_fds(segment)
    mfs = gen_mutual_funds(segment, risk_profile)
    insurance = gen_insurance(segment)
    nps = gen_nps(age, segment)
    stocks = gen_stocks(segment)
    gold = gen_gold(segment)
    ppf = gen_ppf(age, segment)

    fd_total = sum(f["amount"] for f in fds)
    mf_total = sum(f["current_value"] for f in mfs)
    insurance_value = sum(p["sum_assured"] * 0.05 for p in insurance)  # surrender-ish value proxy
    nps_total = nps["tier1_balance"] + nps["tier2_balance"]
    stock_total = sum(s["quantity"] * s["current_price"] for s in stocks)
    gold_price_per_gram = 7150
    gold_total = (gold["physical_grams"] + gold["digital_grams"] + gold["sgb_units"]) * gold_price_per_gram
    ppf_total = ppf["balance"]

    total_net_worth = round(fd_total + mf_total + insurance_value + nps_total + stock_total + gold_total + ppf_total, -2)

    goals = gen_goals(age, segment, total_net_worth)

    monthly_income = round(annual_income / 12, -2)
    transactions = gen_transactions(monthly_income)
    monthly_sip_total = sum(f["sip_amount"] for f in mfs)
    avg_savings_rate = round(sum(t["savings_rate"] for t in transactions) / len(transactions), 3)

    customer = {
        "customer_id": f"IDBI{cust_id:06d}",
        "name": name,
        "age": age,
        "gender": gender,
        "city": city,
        "state": state,
        "city_tier": tier,
        "occupation": occupation,
        "annual_income": annual_income,
        "risk_profile": risk_profile,
        "customer_segment": segment,
        "language_preference": language,
        "portfolio": {
            "fixed_deposits": fds,
            "mutual_funds": mfs,
            "insurance": insurance,
            "nps": nps,
            "stocks": stocks,
            "gold": gold,
            "ppf": ppf,
            "total_net_worth": total_net_worth,
            "asset_breakdown": {
                "fixed_deposits": round(fd_total, -2),
                "mutual_funds": round(mf_total, -2),
                "insurance": round(insurance_value, -2),
                "nps": round(nps_total, -2),
                "stocks": round(stock_total, -2),
                "gold": round(gold_total, -2),
                "ppf": round(ppf_total, -2),
            },
        },
        "goals": goals,
        "financials": {
            "monthly_income": monthly_income,
            "monthly_sip_total": monthly_sip_total,
            "avg_savings_rate": avg_savings_rate,
            "transactions_last_6m": transactions,
        },
    }
    return customer


def main():
    customers = [build_customer(i + 1) for i in range(N_CUSTOMERS)]

    out_path = OUT_DIR / "customers.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(customers, f, ensure_ascii=False)

    # quick CSV summary for eyeballing
    import csv
    csv_path = OUT_DIR / "customers_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "name", "age", "city", "segment", "risk_profile",
                          "annual_income", "total_net_worth", "num_goals"])
        for c in customers:
            writer.writerow([c["customer_id"], c["name"], c["age"], c["city"],
                              c["customer_segment"], c["risk_profile"], c["annual_income"],
                              c["portfolio"]["total_net_worth"], len(c["goals"])])

    print(f"Generated {len(customers)} customer profiles -> {out_path}")
    print(f"Summary CSV -> {csv_path}")
    seg_counts = {}
    for c in customers:
        seg_counts[c["customer_segment"]] = seg_counts.get(c["customer_segment"], 0) + 1
    print("Segment distribution:", seg_counts)


if __name__ == "__main__":
    main()
