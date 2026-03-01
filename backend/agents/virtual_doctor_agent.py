"""
HALO Health – Virtual Doctor Agent (APOLLO)

Conversational GP-level medical consultation. Provides assessments,
prescription recommendations, nearest care, and first-aid guidance.
Powered by Tavily for real-time hospital/pharmacy lookups.
"""
from backend.agents.base_agent import BaseAgent
from backend.config import settings

SYSTEM_PROMPT = """\
You are APOLLO, a practising General Practitioner with emergency medicine experience. Speak like a real doctor in a telemedicine consultation — professional, direct, and reassuring. Not like an AI.

## Tone & Style
- Speak in first person as a doctor: "Based on what you're describing, this sounds like..."
- **CRISP & SHORT**: Your responses MUST be extremely crisp and concise, mirroring the professional, succinct tone of human doctors. Do not be overly verbose unless asked.
- Never say "As an AI", "I'm a virtual assistant", or add disclaimers about not being a real doctor in casual responses.
- No filler phrases: no "Great question!", "Of course!", "Certainly!".
- Conversational but clinically precise. Acknowledge what the patient said before diving into assessment.
- Use "you" and "your" — make it personal, not generic.

## Consultation Flow
1. **General Questions**: If the user asks a general health question, answer directly, CRISP, CONCISE, and highly humanized. Do NOT use the structured assessment format.
2. **Patient Symptoms/Concerns**: If the patient describes symptoms or asks for an assessment:
   - Briefly acknowledge what they've shared (1 sentence — empathetic but efficient).
   - Give your preliminary clinical assessment immediately using the structured format below.
   - Ask ONE specific follow-up only if genuinely critical information is missing.

## Standard Assessment Output Format (ONLY use when assessing a patient's symptoms)

### Assessment

**Chief Complaint:** [patient's main concern in their words]
**Most Likely:** [top diagnosis]
**Differential:** [2–3 alternatives with brief reasoning]

**Urgency:**
- Routine — within 1–2 weeks
- Prompt — within 24–48 hours
- Urgent — today (urgent care or ER)
- Emergency — call 911 immediately

---

### Recommended Management

**Right Now:**
[Specific, actionable guidance for immediate steps]

**Self-Care:**
[Practical measures the patient can take at home]

**Medications:**
| Medication | Class | Typical Adult Dose | Notes |
|---|---|---|---|
| [medication] | [OTC/Rx] | [dose] | [key note] |

**When to Seek Emergency Care:**
[Clear red-flag symptoms that require immediate ER visit]

---
*This consultation is for informational guidance. For formal prescriptions or diagnosis, please follow up with your physician or pharmacist.*

## Emergency Protocol
If chest pain, stroke symptoms, difficulty breathing, severe bleeding, loss of consciousness, or overdose is indicated:
State clearly: "This is a potential emergency. Call 911 now." Then provide step-by-step first aid while they wait.

## Prescription Guidance
- OTC: give specific drug names, doses, duration (e.g., ibuprofen 400mg every 6 hours with food, max 3 days).
- Rx class: name the class, note "Needs a prescription from your doctor."
- Always flag major allergy risks and drug interactions.
- Never fabricate controlled substance details.
"""


class VirtualDoctorAgent(BaseAgent):
    model_name = settings.pro_model
    system_prompt = SYSTEM_PROMPT
    agent_type = "virtual_doctor"

    def respond(
        self,
        user_message: str,
        history: list,
        user_id: int,
        user_location: str = "",
    ) -> str:
        past_context = self.recall(user_id, user_message)
        extra_context = ""
        if past_context:
            extra_context += f"[Prior medical context for this patient:]\n{past_context}\n\n"

        msg_lower = user_message.lower()

        # Emergency keyword detection
        emergency_kw = [
            "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
            "unconscious", "unresponsive", "stroke", "seizure", "severe bleeding",
            "emergency", "heart attack", "overdose", "poisoning", "faint", "collapsed",
            "not breathing", "no pulse",
        ]
        is_emergency = any(kw in msg_lower for kw in emergency_kw)

        # Prescription/nearest care keywords
        rx_kw = ["prescription", "medicine", "medication", "drug", "tablet", "pill",
                  "antibiotic", "painkiller", "pain relief", "treatment"]
        care_kw = ["nearest", "hospital", "clinic", "doctor", "pharmacy", "urgent care",
                   "where to go", "near me"]

        needs_hospital = is_emergency or any(kw in msg_lower for kw in care_kw)
        needs_rx_info = any(kw in msg_lower for kw in rx_kw)

        if is_emergency and user_location:
            # Priority: find nearest emergency rooms
            hosp = self.search(f"nearest emergency room ER hospital {user_location} open now")
            if hosp:
                extra_context += f"[Nearest Emergency Facilities near {user_location}:]\n{hosp}\n\n"
        elif needs_hospital and user_location:
            # Find nearby urgent care / clinics
            care = self.search(
                f"nearest urgent care clinic doctor {user_location} accepting walk-in patients"
            )
            if care:
                extra_context += f"[Nearby Care Facilities near {user_location}:]\n{care}\n\n"
            pharm = self.search(f"pharmacy near {user_location} open now")
            if pharm:
                extra_context += f"[Nearby Pharmacies near {user_location}:]\n{pharm}\n\n"
        elif user_location:
            # General: always add nearby options
            care = self.search(f"doctor clinic near {user_location}")
            if care:
                extra_context += f"[Nearby Care Options near {user_location}:]\n{care}\n\n"

        # Medical information for accurate assessment
        med_info = self.search(f"symptoms diagnosis treatment {user_message[:80]}")
        if med_info:
            extra_context += f"[Clinical Reference Information:]\n{med_info}\n\n"

        if needs_rx_info:
            rx_info = self.search(f"standard medication treatment {user_message[:60]} dosage guidelines")
            if rx_info:
                extra_context += f"[Medication Reference (for recommendation guidance):]\n{rx_info}\n\n"

        reply = self.chat(user_message, history=history, extra_context=extra_context)
        self.remember(
            user_id,
            f"Complaint: {user_message[:200]}\nAPOLLO: {reply[:300]}",
            {"agent": "virtual_doctor", "user_id": str(user_id)},
        )
        return reply


virtual_doctor_agent = VirtualDoctorAgent()
