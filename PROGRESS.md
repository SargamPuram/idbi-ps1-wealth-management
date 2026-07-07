# PS1 — Digital Wealth Management ("Dhanvi") — Build Progress

Last updated: 2026-07-07 (backend complete + Gemini live-verified by orchestrating session, frontend in progress)

## UPDATE (orchestrating session, same day): Gemini key added and live-tested

The team's real `GEMINI_API_KEY` has been added to `backend/.env` (already gitignored) and
`/chat` was smoke-tested with a real customer — full, complete, contextually-grounded response
came back (not truncated, not the fallback message), citing the customer's actual holdings and
goals. **Do not treat "Gemini not live-tested" below as current — it is now live and working.**

Two things were fixed along the way, in case any other PS also integrates Gemini:
1. **`google-genai` was pinned to `0.7.0`** (a very early SDK release) in `requirements.txt` —
   upgraded to `2.10.0` (latest) and reinstalled in the venv. `requirements.txt` updated.
2. **`gemini-2.5-flash` truncated responses mid-sentence** (e.g. cut off after ~20 words) because
   the model spends its `max_output_tokens` budget on internal "thinking" by default, starving the
   visible answer. Fixed in `advisory/engine.py`'s `_generate()` by adding
   `thinking_config=genai_types.ThinkingConfig(thinking_budget=0)` to `GenerateContentConfig` —
   disables thinking, which this fast wealth-advisory chat use case doesn't need. This only works
   on the upgraded SDK (0.7.0's `ThinkingConfig` doesn't have a `thinking_budget` field at all).

If you're picking this up cold: backend is running on port 8003 with a live key, no further
Gemini setup needed. Just don't downgrade `google-genai` back below ~2.x or the thinking-budget
fix will break again (silent truncation, not a crash, so it's easy to miss).

## Status summary

- **Backend**: DONE. All 10 endpoints implemented and live-tested on port 8003 (see table below).
- **Frontend**: IN PROGRESS.
- **Gemini integration**: Built against `google-genai` SDK, exactly matches spec's system prompt
  template. ~~NOT live-tested with a real key~~ **NOW LIVE-TESTED — see update above.** The
  graceful-degradation path IS fully tested: with no `GEMINI_API_KEY` set, `/chat`, market
  commentary, and spending AI-tip all return HTTP 200 with `ai_powered: false` and a clear message
  — never a crash/500. See "Gemini — what the team needs to do" below.
- **Deployed**: NO (not in scope per instructions — local prototype only).

## Backend detail

Location: `ps1-wealth-management/backend/`. venv created with `py -3.11` (per repo convention).

```
scripts/generate_data.py   -> generates 5,000 synthetic customer wealth profiles -> data/customers.json
advisory/data_store.py     -> in-memory load + lookup of customers.json
advisory/finance.py        -> Gemini-FREE: goal SIP math, suitability scoring, product
                               recommendation rules, spending insights, simulated market data
advisory/engine.py         -> DhanviEngine (Gemini client wrapper), system prompt builder,
                               escalation keyword detector
app/schemas.py              -> Pydantic request models
app/main.py                 -> FastAPI app, all endpoints, CORS enabled
```

Data: `data/customers.json` (~20MB, 5,000 profiles) + `data/customers_summary.csv` for quick
eyeballing. Regenerate anytime with:
```
cd ps1-wealth-management/backend
./venv/Scripts/python scripts/generate_data.py
```
Segment split observed: Mass ~2418 (48%), Affluent ~1777 (36%), HNI ~805 (16%) — close to the
50/35/15 spec target (randomness-driven, will vary slightly run to run... actually it's seeded so
it's stable across regenerations).

### Endpoints — all tested live on http://127.0.0.1:8003

| Method | Path | Tested? | Notes |
|---|---|---|---|
| GET | `/` | YES — real response | health check, shows gemini status + sample customer ids |
| POST | `/chat` | YES — graceful-failure path only | see Gemini section below |
| GET | `/portfolio/{customer_id}` | YES — real response | full holdings + analytics + goals |
| GET | `/suitability/questions` | YES — real response | 10-question questionnaire |
| POST | `/suitability` | YES — real response | risk score -> profile + allocation + rationale |
| GET | `/recommendations/{customer_id}` | YES — real response | rule-based gap analysis |
| GET | `/market-pulse` | YES — real response (commentary uses rule-based fallback) | sensex/nifty sim + portfolio impact |
| POST | `/goal-plan` | YES — real response | SIP-needed + 3 scenario growth projections |
| GET | `/products` | YES — real response | catalog with personalization flag |
| GET | `/customer/{customer_id}/insights` | YES — real response (AI tip uses fallback) | 50/30/20 rule, 6mo trend |
| POST | `/escalate` | YES — real response | in-memory ticket, mock RM assignment |
| GET | `/escalate/tickets` | YES — real response | demo helper |

404 handling verified (`GET /portfolio/NOPE` -> 404 with clear detail message).

### Gemini — what the team needs to do once they have a key

1. `cd ps1-wealth-management/backend`
2. `cp .env.example .env` (or copy manually on Windows)
3. Edit `.env`, set `GEMINI_API_KEY=<the real key>`
4. Leave `GEMINI_MODEL=gemini-2.5-flash` unless that model name errors for their key/quota — if
   it does, list available models with:
   ```
   ./venv/Scripts/python -c "from google import genai; c=genai.Client(api_key='YOUR_KEY'); [print(m.name) for m in c.models.list()]"
   ```
   and set `GEMINI_MODEL` to a working name from that list.
5. Restart uvicorn. `GET /` should now show `"gemini": {"ai_powered": true, ...}`.
6. Do ONE live smoke test: `POST /chat` with a real customer_id + message, confirm a real
   Gemini-generated reply comes back (not the fallback message) and check `escalation_needed`
   triggers correctly on a complex query (e.g. mention "estate planning" or "insurance claim").

No code changes should be required — `DhanviEngine` reads `GEMINI_API_KEY`/`GEMINI_MODEL` from
env via `python-dotenv`, and the code path is identical whether the key is real or missing (only
`is_available` flips).

## Frontend detail — ✅ DONE (completed + verified by orchestrating session 2026-07-07)

Location: `ps1-wealth-management/frontend/`. All 5 pages built: Avatar Chat (`/`), Portfolio
(`/portfolio`), Goals (`/goals`), Market (`/market`), Products (`/products`).

The background agent was cut off by a session limit mid-build with a real bug: `App.jsx`
imported `./pages/Products` but that file didn't exist, which would have crashed the dev
server/build the moment anyone hit `/products` or on a production build (Vite doesn't always
surface a missing-module error at dev-server-startup time, only when that module is actually
requested). Fixed by writing `pages/Products.jsx` + `Products.css` from scratch, matching the
existing page conventions (`PageHeader`, `useFetch`, `StateViews`, `useCustomer` context,
`api.products()` which already existed in `api/client.js`): category tabs (FDs/MFs/
Insurance/NPS/Gold/PPF/Bonds from the real `/products` response), product cards with
risk/returns/min-investment/lock-in, a "Recommended for you" badge, a compare-up-to-3 checkbox
with a comparison table, and an "Invest via IDBI Bank" CTA.

Verified via headless Playwright across all 5 routes (`/`, `/portfolio`, `/goals`, `/market`,
`/products`) — **zero console/page errors** — plus visually reviewed screenshots. Avatar chat
hero screen (gradient orb avatar, particles, WhatsApp-style bubbles, quick-action chips, bottom
nav) and Products page both look genuinely polished, not placeholder-quality. Frontend dev
server confirmed running on port 5176, wired to the live backend on 8003 with the real Gemini
key already active.

## Next steps if picking this up cold

1. Read this file, then `CLAUDE_PROMPTS/04_PS1_WEALTH_MANAGEMENT.md` for full spec.
2. Backend is done — just `cd backend && ./venv/Scripts/python -m uvicorn app.main:app --port 8003`
   (data already generated, venv already set up, no need to redo those steps).
3. Build frontend per Prompt 2 in the spec file. Connect to `http://localhost:8003` (make base URL
   configurable via `VITE_API_URL` env var, frontend dev server on port 5176).
4. Once frontend is built, do full end-to-end browser test (see "Before declaring done" in the
   original task) and update this file's frontend section + the root `PROGRESS.md` PS1 row.
