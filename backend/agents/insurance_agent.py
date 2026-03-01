"""
HALO Health – Insurance Agent (Gemini-powered with COMPASS API fallback)

Primary: Uses COMPASS live API for authentic insurance guidance.
Fallback: When API is unavailable, uses Gemini + web search to answer
          US health insurance questions directly.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import settings
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

BASE_URL = settings.insurance_api_base_url.rstrip("/")

INSURANCE_SYSTEM_PROMPT = """\
You are COMPASS, a licensed US health insurance advisor on the HALO Health platform.

## Your Expertise
- ACA Marketplace plans (Bronze/Silver/Gold/Platinum)
- Medicare (Parts A, B, C, D) and Medicaid eligibility
- COBRA, short-term health plans, employer coverage
- Understanding deductibles, premiums, copays, out-of-pocket maximums
- Subsidy/tax credit eligibility based on income and household size

## Your Style
- Speak plainly — insurance is confusing enough.
- **CRISP & SHORT**: Your responses MUST be extremely crisp and concise. Mirror the professional, succinct tone of human experts. Do not be overly verbose unless generating a table.
- Ask ONE clarifying question at a time before giving recommendations.
- Always note that plan availability varies by state/county and the user should verify on healthcare.gov.

## Key Questions to Ask (over multiple turns)
1. What state/ZIP are you in?
2. How many people are on your plan?
3. What is your approximate annual household income?
4. Current employment and insurance situation?
5. Any critical medications or conditions that require specific coverage?

## Response Format for Plan Recommendations
```
### 🧭 Insurance Recommendation

**Your Situation:** [summary]

**Best Plan Types for You:**
| Plan | Why It Fits | Est. Monthly Premium |
|---|---|---|
| [plan] | [reason] | $[range] |

**Key Subsidies/Programs You May Qualify For:**
[list]

**Next Steps:**
1. Visit healthcare.gov during open enrollment (Nov 1 – Jan 15)
2. Compare plans using your specific ZIP code
3. [specific action]
3. [specific action]
```
"""


class InsuranceGeminiAgent(BaseAgent):
    """Gemini-powered fallback insurance advisor."""
    model_name = settings.flash_model
    system_prompt = INSURANCE_SYSTEM_PROMPT
    agent_type = "insurance"

    def respond(self, user_message: str, history: list, user_id: int) -> str:
        past_context = self.recall(user_id, user_message)
        extra_context = ""
        if past_context:
            extra_context += f"[Previous insurance questions from this user:]\n{past_context}\n\n"

        search_results = self.search(f"US health insurance 2024 2025 ACA Medicare Medicaid {user_message[:80]}")
        if search_results:
            extra_context += f"[Current insurance information from Web Search:]\n{search_results}\n"

        reply = self.chat(user_message, history=history, extra_context=extra_context)
        self.remember(
            user_id,
            f"Insurance query: {user_message[:200]}\nReply: {reply[:300]}",
            {"agent": "insurance", "user_id": str(user_id)},
        )
        return reply


# Gemini fallback singleton (used when COMPASS API is down)
_gemini_insurance = None


def get_gemini_insurance() -> InsuranceGeminiAgent:
    global _gemini_insurance
    if _gemini_insurance is None:
        _gemini_insurance = InsuranceGeminiAgent()
    return _gemini_insurance


class InsuranceAgent:
    """
    Primary: Proxies COMPASS live API.
    Fallback: Gemini-powered insurance Q&A when API is unavailable.
    """
    agent_type = "insurance"

    # ── Phase 1: ZIP Lookup ────────────────────────────────────────────────────
    async def get_geodata(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Try COMPASS geodata endpoint; return None on failure."""
        endpoints_to_try = [
            f"{BASE_URL}/geodata/{zip_code}",
            f"{BASE_URL}/geo/{zip_code}",
            f"{BASE_URL}/geocode/{zip_code}",
        ]
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints_to_try:
                try:
                    resp = await client.get(endpoint)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
                    continue

        # Fallback: return basic info so the flow can continue
        logger.warning("InsuranceAgent.get_geodata: all endpoints failed for ZIP %s. Using fallback.", zip_code)
        return {"zip_code": zip_code, "state": "Unknown", "county": "Unknown", "fallback": True}

    # ── Phase 3: Chat ──────────────────────────────────────────────────────────
    async def chat(
        self,
        thread_id: str,
        user_profile: Dict[str, Any],
        message: str,
        conversation_history: List[str],
        is_profile_complete: bool,
        user_id: int = 0,
        history: list = None,
    ) -> Optional[Dict[str, Any]]:
        """Forward to COMPASS API; fall back to Gemini on failure."""
        payload = {
            "thread_id": thread_id,
            "user_profile": user_profile,
            "message": message,
            "conversation_history": conversation_history,
            "is_profile_complete": is_profile_complete,
        }

        # Try COMPASS API first
        async with httpx.AsyncClient(timeout=60.0) as client:
            for endpoint in [f"{BASE_URL}/chat", f"{BASE_URL}/ask"]:
                try:
                    resp = await client.post(endpoint, json=payload)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
                    continue

        # ── Gemini fallback ─────────────────────────────────────────────────
        logger.warning("InsuranceAgent: API unavailable. Using Gemini fallback.")
        gemini = get_gemini_insurance()

        # Build profile context for Gemini
        profile_ctx = ""
        if user_profile:
            zip_code = user_profile.get("zip_code", "")
            state = user_profile.get("state", "")
            age = user_profile.get("age", "")
            income = user_profile.get("income", "")
            household = user_profile.get("household_size", "")
            employment = user_profile.get("employment_status", "")
            if any([zip_code, state, age, income]):
                profile_ctx = (
                    f"[User Profile: ZIP={zip_code}, State={state}, "
                    f"Age={age}, Income=${income}/yr, "
                    f"Household={household}, Employment={employment}]\n\n"
                )

        full_message = profile_ctx + message if profile_ctx else message
        gemini_history = history or []
        reply = gemini.respond(full_message, gemini_history, user_id)

        # Return in COMPASS-compatible format
        new_history = list(conversation_history) + [f"User: {message}", f"Assistant: {reply}"]
        return {
            "updated_profile": user_profile,
            "updated_history": new_history,
            "is_profile_complete": is_profile_complete,
            "_gemini_fallback": True,
        }


# Singleton
insurance_agent = InsuranceAgent()
