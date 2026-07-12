# Disclaimer

**PS1 — Digital Wealth Management ("Dhanvi") is a hackathon proof-of-concept
built for IDBI Innovate 2026.** It is not a production banking product. Please
read this before evaluating, demoing, or building on top of it.

## Synthetic data only

Every customer, portfolio, transaction, and holding in this app is
**synthetically generated** by `backend/scripts/generate_data.py` using the
`Faker` library with a fixed random seed. It produces 5,000 fictitious Indian
customer profiles — demographics, fixed deposits, mutual funds, insurance
policies, NPS/PPF balances, stocks, gold holdings, financial goals, and six
months of simulated income/spending transactions (`data/customers.json`,
`data/customers_summary.csv`). No real customer, account, or transaction data
from IDBI Bank or any other institution is used anywhere in this repository.
Market data shown on the Market page (Sensex/Nifty/gold movement) is also
simulated — deterministically seeded per calendar day, not fetched from any
live market data provider.

## Not investment advice, not a registered adviser

Dhanvi is an AI chat interface built on a third-party LLM (DeepSeek), plus a
set of rule-based calculators (goal SIP math, suitability scoring, product
gap-analysis). **Dhanvi is not a SEBI-registered Investment Adviser or
Research Analyst, and nothing it outputs constitutes investment, tax, legal,
or insurance advice.** Return figures, "recommended" SIP amounts, and product
suggestions are illustrative, formula-driven estimates based on generic
assumptions (see `backend/advisory/finance.py`) — they are not guarantees,
promises, or projections of actual future performance. Past or assumed
returns do not guarantee future results. Anyone using this prototype for a
real financial decision would be relying on synthetic data and an
unregistered AI assistant — don't do that.

## No guarantee of returns

Nothing in this application guarantees, implies, or promises any specific
rate of return, capital protection, or investment outcome, including figures
labeled "historical," "assumed," or "projected." All such figures are
prototype placeholders for demonstration purposes.

## "IDBI Bank" usage

References to "IDBI Bank," "IDBI Federal," specific scheme names (e.g. "IDBI
Focused Equity Fund," "IDBI Bank FD"), and the IDBI brand throughout this
codebase and UI are used **descriptively, for a hackathon problem-statement
submission only** (IDBI Innovate 2026, PS1 — Digital Wealth Management). This
project has no affiliation with, endorsement from, or authorization by IDBI
Bank Ltd. It is not an official IDBI Bank product and must not be presented,
deployed, or distributed as one.

## Known limitations

Documented honestly so nothing here is discovered by surprise:

- **The input-safety guardrail is heuristic, not foolproof.** `assess_input_safety()`
  in `backend/advisory/engine.py` uses a regex bank plus Jaccard word-set
  similarity against a small set of hardcoded jailbreak anchor phrases. It
  runs before every LLM call and catches known/paraphrased jailbreak
  patterns quickly and without a network call, but it is not a trained
  classifier or moderation model — a sufficiently novel or obfuscated prompt
  injection could still get through, and a legitimate message could in
  theory be over-blocked. It is a first line of defense, not the only one.
- **No persistent audit trail.** Chat transcripts, escalation tickets, and
  guardrail triggers are not written to a database; they exist only in
  server process memory (`_escalation_tickets` in `app/main.py`) and
  whatever appears in `backend/server.log`. Restarting the server loses all
  of it. A real deployment would need durable, queryable logging for
  compliance review.
- **No authentication or authorization layer.** Any client can call the API
  for any `customer_id` in the synthetic dataset — there is no login,
  session, OTP, or access-control check anywhere in `backend/app/main.py`.
  This is acceptable for a local demo, not for handling real accounts.
- **Escalation detection is keyword-based, not semantic.** `detect_escalation()`
  matches a fixed list of phrases (e.g. "estate plan," "insurance claim,"
  "mis-sold") plus a couple of regex patterns for "talk to a human." A
  paraphrased or differently-worded request touching the same sensitive
  topic can be missed, meaning a query that should be routed to a human
  Relationship Manager might instead get an AI-only answer.
- **Voice output (text-to-speech) is currently limited to two languages.**
  A self-hosted Piper TTS engine (`backend/advisory/tts_engine.py`) speaks
  Dhanvi's replies aloud, but only English and Hindi voice models are
  bundled. The UI offers six languages (English, Hindi, Tamil, Telugu,
  Bengali, Marathi); for the other four, Dhanvi still replies in-language
  via text, but does not speak.
- **DeepSeek dependency.** All conversational responses depend on a
  third-party LLM API and a valid `DEEPSEEK_API_KEY`. If the key is missing
  or the API is unreachable, `/chat` degrades gracefully to a fixed message
  (by design — see `backend/advisory/engine.py`), but no AI-generated advice
  is available in that state.
- **No cross-institution visibility.** Suitability and recommendations are
  computed only from the synthetic IDBI-side portfolio; the prototype has no
  way to factor in a customer's holdings at other banks or brokers.

## Questions

This is a hackathon submission for evaluation purposes. For any questions
about scope or intent, contact the team via the hackathon submission
channel.
