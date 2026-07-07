"""
Dhanvi — Gemini-powered conversational wealth advisor engine.

Design goal: the REST API must stay fully usable and testable even when
GEMINI_API_KEY is missing/invalid. Every Gemini call is wrapped so failures
raise GeminiUnavailable with a clear, actionable message instead of bubbling
up as an unhandled 500. Callers (app/main.py) catch this and return a
graceful, informative payload (HTTP 200 with ai_powered=false) rather than a
crash, so the rest of the product (portfolio, goals, suitability, etc.) keeps
working for demos before the team has a live key.
"""
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"

ESCALATION_KEYWORDS = [
    "estate plan", "inheritance", "will", "nominee dispute", "trust fund",
    "insurance claim", "claim rejected", "surrender my policy", "surrender value",
    "rebalance my entire portfolio", "restructure my entire portfolio",
    "tax dispute", "legal notice", "loan settlement", "large withdrawal",
    "complaint", "fraud", "mis-sold", "mis sold", "grievance",
]

REGULATED_PRODUCT_KEYWORDS = [
    "insurance", "ulip", "endowment", "lic", "term plan", "specific fund", "which stock",
]


class GeminiUnavailable(Exception):
    """Raised whenever Gemini cannot be used — missing key, bad key, network/API error."""
    pass


class DhanviEngine:
    def __init__(self):
        self.api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        self.model_name = (os.getenv("GEMINI_MODEL") or DEFAULT_MODEL).strip()
        self.client = None
        self.init_error = None

        if not self.api_key:
            self.init_error = (
                "GEMINI_API_KEY is not set. Dhanvi's AI responses are disabled until the team "
                "adds a valid key. Copy .env.example to .env, set GEMINI_API_KEY=<your key>, and "
                "restart the server. All non-AI endpoints (portfolio, suitability, goal-plan, "
                "products, insights, recommendations) work normally without it."
            )
            return

        try:
            from google import genai  # imported lazily so missing package doesn't crash app import
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:  # pragma: no cover - defensive
            self.init_error = f"Failed to initialize Gemini client: {type(e).__name__}: {e}"
            self.client = None

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def status(self) -> dict:
        return {
            "ai_powered": self.is_available,
            "model": self.model_name,
            "message": "Gemini client ready." if self.is_available else self.init_error,
        }

    def _generate(self, system_prompt: str, user_message: str, history: list | None = None,
                   temperature: float = 0.7, max_output_tokens: int = 1024) -> str:
        if not self.is_available:
            raise GeminiUnavailable(self.init_error or "Gemini client not initialized.")

        from google.genai import types as genai_types

        contents = []
        for turn in (history or []):
            role = "user" if turn.get("role") == "user" else "model"
            text = turn.get("content") or turn.get("message") or ""
            if text:
                contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=text)]))
        contents.append(genai_types.Content(role="user", parts=[genai_types.Part(text=user_message)]))

        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            # gemini-2.5-flash spends its token budget on internal "thinking" by default,
            # which can starve the visible answer and truncate it mid-sentence. Disabled
            # here since wealth-advisory chat doesn't need multi-step reasoning.
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config,
            )
            text = getattr(response, "text", None)
            if not text:
                raise GeminiUnavailable("Gemini returned an empty response.")
            return text
        except GeminiUnavailable:
            raise
        except Exception as e:
            raise GeminiUnavailable(
                f"Gemini API call failed ({type(e).__name__}: {e}). Check that GEMINI_API_KEY is "
                f"valid and GEMINI_MODEL ('{self.model_name}') is a model your key can access."
            )

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------
    @staticmethod
    def build_system_prompt(customer: dict, language: str) -> str:
        profile_json = json.dumps({
            "name": customer["name"],
            "age": customer["age"],
            "city": customer["city"],
            "occupation": customer["occupation"],
            "annual_income": customer["annual_income"],
            "risk_profile": customer["risk_profile"],
            "customer_segment": customer["customer_segment"],
            "net_worth": customer["portfolio"]["total_net_worth"],
            "asset_breakdown": customer["portfolio"]["asset_breakdown"],
            "goals": customer["goals"],
            "monthly_income": customer["financials"]["monthly_income"],
            "monthly_sip_total": customer["financials"]["monthly_sip_total"],
            "avg_savings_rate": customer["financials"]["avg_savings_rate"],
            "fixed_deposits_count": len(customer["portfolio"]["fixed_deposits"]),
            "mutual_funds": [{"scheme": m["scheme_name"], "type": m["type"], "current_value": m["current_value"]}
                             for m in customer["portfolio"]["mutual_funds"]],
            "insurance": [{"type": i["type"], "provider": i["provider"], "sum_assured": i["sum_assured"]}
                          for i in customer["portfolio"]["insurance"]],
            "nps_balance": customer["portfolio"]["nps"]["tier1_balance"],
            "ppf_balance": customer["portfolio"]["ppf"]["balance"],
        }, ensure_ascii=False)

        return f"""You are "Dhanvi", IDBI Bank's AI Wealth Advisor — a warm, knowledgeable digital wealth coach.
You are speaking with {customer["name"]}, a {customer["customer_segment"]} segment customer, age {customer["age"]}, from {customer["city"]}.
Respond in {language}. Keep replies conversational, concise (roughly 80-160 words unless the user asks for detail), and free of jargon.

Customer's Financial Profile (JSON):
{profile_json}

Your role:
- Give personalized wealth advisory grounded in the customer's ACTUAL portfolio and goals above — reference real numbers.
- For vanilla/non-regulated products (FDs, SIPs into existing MF schemes, RBI Bonds, PPF, NPS): give direct, actionable recommendations.
- For regulated products (Insurance policies, specific new MF scheme purchases, ULIPs): explain options clearly but note that a certified IDBI Relationship Manager (RM) must complete the suitability check and paperwork — flag for hybrid escalation.
- Always mention relevant Indian tax implications when relevant (Section 80C, 80D, 80CCD(1B) for NPS, LTCG/STCG on equity & debt funds, etc.).
- Reference IDBI Bank products/schemes by name where natural (e.g. IDBI Bank FDs, IDBI Federal Life Insurance, IDBI Focused Equity Fund).
- Recommend goal-based investing over speculation.
- If the query involves estate planning, inheritance, large portfolio restructuring, insurance claims/grievances, or anything legally/tax complex, clearly say you are flagging this for a human RM.

Hard rules (never break):
- NEVER give a specific stock buy/sell tip or price target.
- ALWAYS mention at least one risk factor when recommending a market-linked product.
- Comply with SEBI suitability norms — do not recommend products clearly unsuitable for the stated risk profile.
- Do not guarantee returns; use words like "historically", "typically", "may".
"""

    def chat(self, customer: dict, message: str, language: str, history: list | None = None) -> str:
        system_prompt = self.build_system_prompt(customer, language)
        return self._generate(system_prompt, message, history=history, temperature=0.7, max_output_tokens=768)

    def market_commentary(self, snapshot: dict, language: str = "English") -> str:
        prompt = (
            "You are Dhanvi, IDBI Bank's AI wealth advisor. Write a brief (40-70 word), reassuring, "
            "jargon-free market commentary in " + language + " for retail investors, given today's simulated "
            "market snapshot (JSON): " + json.dumps(snapshot) + ". "
            "Mention Sensex/Nifty direction and one practical takeaway (e.g. stay invested, don't time the market). "
            "Never give specific stock tips."
        )
        return self._generate(
            "You are Dhanvi, a warm and precise financial market commentator for IDBI Bank customers.",
            prompt, temperature=0.6, max_output_tokens=200,
        )

    def spending_tip(self, insights_summary: dict, language: str = "English") -> str:
        prompt = (
            "Given this customer's spending/savings summary (JSON): " + json.dumps(insights_summary) +
            f", write one short (30-50 word), encouraging, actionable tip in {language}."
        )
        return self._generate(
            "You are Dhanvi, IDBI Bank's AI wealth coach giving a quick, warm spending insight.",
            prompt, temperature=0.6, max_output_tokens=150,
        )


# ------------------------------------------------------------------
# Escalation + lightweight product-recommendation extraction (no Gemini needed)
# ------------------------------------------------------------------
def detect_escalation(user_message: str, ai_response: str) -> tuple[bool, str | None]:
    text = (user_message + " " + ai_response).lower()
    for kw in ESCALATION_KEYWORDS:
        if kw in text:
            return True, f"Query touches a sensitive/complex area ('{kw}') that needs a certified RM."
    if re.search(r"\brm\b|relationship manager|human advisor|talk to (a|an) (person|advisor|human)", text):
        return True, "Customer explicitly requested human assistance."
    for kw in REGULATED_PRODUCT_KEYWORDS:
        if kw in user_message.lower():
            return True, f"Query involves a regulated product ('{kw}') requiring RM-assisted suitability check."
    return False, None
