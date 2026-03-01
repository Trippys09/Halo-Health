"""
HALO Health – Orchestrator Agent (Master Intelligence)

Routes user requests to specialist agents via A2A (Agent-to-Agent) calls.
Synthesises multi-domain responses. Handles general medical queries directly.
"""
import logging
from typing import List, Optional

from backend.agents.base_agent import BaseAgent
from backend.agents.wellbeing_agent import wellbeing_agent
from backend.agents.diagnostic_agent import diagnostic_agent
from backend.agents.virtual_doctor_agent import virtual_doctor_agent
from backend.agents.dietary_agent import dietary_agent
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are HALO — the central intelligence of the HALO Health AI Healthcare Platform.
You coordinate a team of specialist AI agents and can handle any health-related query.

## Specialist Team (A2A)
- **SAGE** — Mental wellness, stress, anxiety, depression, emotional support
- **COMPASS** — US health insurance, ACA plans, Medicare/Medicaid guidance
- **PRISM** — Medical imaging analysis: X-rays, MRIs, CT scans, retinal scans
- **APOLLO** — Medical consultation, symptoms, diagnoses, prescriptions, first aid, emergencies
- **NORA** — Nutrition, meal plans, dietary advice, weight management

## Communication Style
- Professional, concise, and highly humanized.
- **CRISP & SHORT**: Your responses MUST be extremely crisp and concise. Mirror a succinct human coordinator. Do not output long introductory or concluding essays.
- Do not use filler phrases ("Great!", "Of course!"). Start directly with the content.
- When routing to a specialist, briefly state which agent is handling this and deliver their full response.
- Handle multi-domain queries by addressing each domain in turn with clear section headers.

## Output Format (when routing)
```
**Consulting: [AgentName] — [specialty]**

[Full agent response]
```

For general queries you handle directly, respond without any routing header.
"""

# Keyword routing map — priority order
AGENT_ROUTING = {
    "diagnostic": [
        "scan", "x-ray", "xray", "mri", "ct scan", "image", "retinal",
        "ultrasound", "radiology", "pathology", "biopsy", "ecg", "ekg",
        "report", "film", "imaging",
    ],
    "virtual_doctor": [
        "symptom", "pain", "fever", "sick", "ill", "nausea", "vomit",
        "headache", "cough", "breathe", "breathing", "chest", "heart attack",
        "doctor", "emergency", "hospital", "clinic", "medicine", "ache",
        "bleed", "rash", "swollen", "dizzy", "faint", "infection",
        "prescription", "medication", "antibiotic", "painkiller", "diagnos",
        "nearest", "urgent care", "first aid",
    ],
    "wellbeing": [
        "stress", "anxious", "anxiety", "depress", "depression", "sad",
        "lonely", "overwhelm", "panic", "burnout", "mental", "mood",
        "therapist", "counsel", "mindful", "meditat", "sleep problem",
        "emotional", "feeling", "grief", "trauma", "ptsd",
    ],
    "dietary": [
        "diet", "meal", "nutrition", "calorie", "eat", "food", "weight",
        "protein", "carb", "fat", "vegan", "vegetarian", "supplement",
        "recipe", "snack", "breakfast", "lunch", "dinner", "macro",
    ],
    "insurance": [
        "insurance", "coverage", "medicare", "medicaid", "deductible",
        "premium", "health plan", "marketplace", "copay", "out of pocket",
        "aca", "cobra", "employer plan", "subsidy",
    ],
}


def _score_routing(message: str) -> dict:
    """Score each agent by keyword matches in the message."""
    msg_lower = message.lower()
    scores = {agent: 0 for agent in AGENT_ROUTING}
    for agent, keywords in AGENT_ROUTING.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[agent] += 1
    return scores


def _detect_agents(message: str, multi: bool = False) -> list:
    """Return ordered list of agents to route to (multi=True for multi-domain)."""
    scores = _score_routing(message)
    sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if multi:
        # Return all agents with score > 0
        return [a for a, s in sorted_agents if s > 0]

    best_agent, best_score = sorted_agents[0]
    return [best_agent] if best_score > 0 else ["orchestrator"]


class OrchestratorAgent(BaseAgent):
    model_name = settings.pro_model
    system_prompt = SYSTEM_PROMPT
    agent_type = "orchestrator"

    def respond(
        self,
        user_message: str,
        history: list,
        user_id: int,
        image_data: Optional[bytes] = None,
        mime_type: str = "image/jpeg",
        user_location: str = "",
    ) -> str:
        # Force diagnostic if image is attached
        if image_data:
            targets = ["diagnostic"]
        else:
            targets = _detect_agents(user_message, multi=False)

        logger.info("Orchestrator → routing to: %s", targets)

        past_context = self.recall(user_id, user_message)
        parts = []

        for target in targets:
            if target == "wellbeing":
                # A2A: call SAGE
                reply = wellbeing_agent.respond(user_message, history, user_id)
                parts.append(
                    f"**Consulting: SAGE — Mental Wellness Counsellor**\n\n{reply}"
                )

            elif target == "diagnostic":
                # A2A: call PRISM
                reply = diagnostic_agent.respond(
                    user_message, history, user_id,
                    image_data=image_data, mime_type=mime_type,
                )
                parts.append(
                    f"**Consulting: PRISM — Diagnostic Imaging Analyst**\n\n{reply}"
                )

            elif target == "virtual_doctor":
                # A2A: call APOLLO
                reply = virtual_doctor_agent.respond(
                    user_message, history, user_id, user_location=user_location
                )
                parts.append(
                    f"**Consulting: APOLLO — Virtual Doctor**\n\n{reply}"
                )

            elif target == "dietary":
                # A2A: call NORA
                reply = dietary_agent.respond(user_message, history, user_id)
                parts.append(
                    f"**Consulting: NORA — Dietary & Nutrition Advisor**\n\n{reply}"
                )

            elif target == "insurance":
                # A2A: call COMPASS (lightweight respond path)
                from backend.agents.insurance_agent import get_gemini_insurance
                ins_agent = get_gemini_insurance()
                reply = ins_agent.respond(user_message, history, user_id)
                parts.append(
                    f"**Consulting: COMPASS — Health Insurance Advisor**\n\n{reply}"
                )

            else:
                # Handle general queries directly
                extra = past_context or ""
                search_res = self.search(f"health medical {user_message[:80]}")
                if search_res:
                    extra += f"\n\n[Relevant medical reference:]\n{search_res}"
                reply = self.chat(user_message, history=history, extra_context=extra)
                parts.append(reply)

        final_reply = "\n\n---\n\n".join(parts) if len(parts) > 1 else (parts[0] if parts else "")

        self.remember(
            user_id,
            f"User: {user_message[:200]}\nRouted: {targets}\nReply: {final_reply[:300]}",
            {"agent": "orchestrator", "routed_to": ",".join(targets), "user_id": str(user_id)},
        )
        return final_reply


orchestrator_agent = OrchestratorAgent()
