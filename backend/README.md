# PS1 — Dhanvi: AI Wealth Advisor (Backend)

FastAPI backend for IDBI Bank's "Financial Digital Twin + AI Wealth Coach" — a conversational,
avatar-based wealth advisor ("Dhanvi") powered by Google Gemini, plus a full rules/formula-driven
advisory engine (goal planning, suitability, recommendations, spending insights, simulated market
pulse) that works completely independent of Gemini.

## Architecture

```
scripts/generate_data.py  -> synthetic 5,000 customer wealth profile generator (data/customers.json)
advisory/data_store.py    -> loads customers.json into memory, lookup by customer_id
advisory/finance.py       -> Gemini-free math & rules: goal SIP planning, suitability scoring,
                              product recommendations, spending insights, simulated market data
advisory/engine.py        -> DhanviEngine: Gemini client wrapper, system-prompt builder, chat/
                              market-commentary/spending-tip calls, escalation keyword detector
app/schemas.py             -> Pydantic request models
app/main.py                -> FastAPI app, all 10 endpoints
```

## Setup & Run

Requires Python 3.11 (kept consistent with the rest of the IDBI Innovate 2026 monorepo).

```bash
cd ps1-wealth-management/backend
py -3.11 -m venv venv
./venv/Scripts/pip install -r requirements.txt      # venv/bin/pip on macOS/Linux

# 1. Generate synthetic wealth profiles (5,000 customers)
./venv/Scripts/python scripts/generate_data.py

# 2. (Optional but recommended) plug in your Gemini key — see below

# 3. Serve the API
./venv/Scripts/python -m uvicorn app.main:app --reload --port 8003
```

Interactive API docs: http://127.0.0.1:8003/docs

## Plugging in the Gemini API key (once the team has generated one)

1. Copy `.env.example` to `.env` in this `backend/` folder.
2. Set `GEMINI_API_KEY=<your key>` (get one free at https://aistudio.google.com/apikey).
3. Leave `GEMINI_MODEL=gemini-2.5-flash` as-is, or change it if that model name doesn't work
   for your key — list the models your key can access with:
   ```bash
   ./venv/Scripts/python -c "from google import genai; c=genai.Client(api_key='YOUR_KEY'); [print(m.name) for m in c.models.list()]"
   ```
4. Restart uvicorn. `GET /` will report `"gemini": {"ai_powered": true, ...}` once it's picked up.

**Nothing else needs to change** — `python-dotenv` auto-loads `.env` at import time, and
`DhanviEngine` reads `GEMINI_API_KEY` / `GEMINI_MODEL` from the environment.

### What was and wasn't live-tested

This backend was built and fully tested **without** a live Gemini key (the team had not generated
one yet at build time). Every endpoint that doesn't need Gemini was verified with real responses.
For the three Gemini-touching code paths (`/chat`, market commentary in `/market-pulse`, AI tip in
`/customer/{id}/insights`), only the **graceful-degradation path** was verified: with no key set,
each returns HTTP 200 (never a 500/crash) with `ai_powered: false` and a clear, actionable message
in the response telling the caller exactly what to configure. The Gemini call itself (`DhanviEngine._generate`)
uses the current `google-genai` SDK (`Client.models.generate_content`) and mirrors the exact
system-prompt template from the spec — once a real key is set, no code changes should be required,
but the team should do one live smoke test of `/chat` before demo day to confirm the model name
(`gemini-2.5-flash`) is accepted by their key/quota, and adjust `GEMINI_MODEL` if not.

## Endpoints

| Method | Path | Purpose | Needs Gemini? |
|---|---|---|---|
| GET | `/` | Health check — customer count, Gemini status | No |
| POST | `/chat` | Conversational advisory with Dhanvi | Degrades gracefully |
| GET | `/portfolio/{customer_id}` | Full portfolio + analytics | No |
| GET | `/suitability/questions` | 10-question risk questionnaire | No |
| POST | `/suitability` | Score answers -> risk profile + allocation | No |
| GET | `/recommendations/{customer_id}` | Rule-based product recommendations | No |
| GET | `/market-pulse` | Simulated Sensex/Nifty + AI commentary + portfolio impact | Degrades gracefully |
| POST | `/goal-plan` | SIP-needed calculator + growth projection scenarios | No |
| GET | `/products` | Product catalog (FDs/MFs/Insurance/NPS/Gold/PPF/Bonds) | No |
| GET | `/customer/{customer_id}/insights` | Spending insights + 50/30/20 rule + AI tip | Degrades gracefully |
| POST | `/escalate` | Raise an RM escalation ticket | No |
| GET | `/escalate/tickets` | List escalation tickets raised this session (demo helper) | No |

Full request/response schemas are in the interactive docs (`/docs`) once the server is running.

## Data

`scripts/generate_data.py` generates 5,000 realistic Indian customer wealth profiles into
`data/customers.json` (~20 MB) — demographics, city-tier mix (metro/tier-2/tier-3), risk profile
(Conservative 30% / Moderate 40% / Aggressive 30%), customer segment (Mass 50% / Affluent 35% /
HNI 15%), full portfolio (FDs, mutual funds, insurance incl. LIC bancassurance, NPS, stocks, gold,
PPF), 2-4 financial goals each, and 6 months of income/spending transactions. Regenerate any time
with the same command — it's deterministic (seeded) so customer IDs stay stable across runs.

## Known limitations (prototype scope)

- Market data (Sensex/Nifty) is simulated (date-seeded pseudo-random walk), not a live feed —
  acceptable per hackathon rules (live sandbox/API access comes in Round 2).
- Escalation tickets are stored in-memory only (reset on server restart) — fine for a demo, would
  move to a real DB/ticketing system integration in production.
- `product_recommendations` inside `/chat` responses come from the same rule-based engine as
  `/recommendations`, not parsed out of Gemini's free-text reply — kept deliberately simple and
  reliable for a demo rather than asking Gemini for structured JSON output.
