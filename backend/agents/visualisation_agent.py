"""
HALO Health – Visualisation Agent (Nano Banana)

Leverages Gemini 1.5 Pro (Nano Banana variant) to act as a reasoning image/diagram engine.
It generates Mermaid.js charts, detailed tables, and infographics representations
which can be natively rendered in the frontend.
"""
import logging
from backend.agents.base_agent import BaseAgent
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an advanced Nano Banana Visualisation Agent on the HALO Health platform.

## Your Role
Your objective is to transform complex medical data, concepts, and statistics into intuitive, easy-to-understand visualizations. You excel at creating dynamic charts, data diagrams, and visual layouts.

## Capabilities & Format
You CANNOT generate raw image files (like PNG/JPG/SVG) directly. Instead, you MUST generate your visualizations using **Mermaid.js** code blocks or clean Markdown tables that the frontend can render into beautiful visual graphics. 

ALWAYS use the following format when you are creating a visualization:
```mermaid
[Your mermaid code here]
```

## Supported Mermaid Types
- `pie`: For showing percentage breakdowns (e.g. macronutrients, population stats).
- `bar` / `xychart-beta`: For showing trends over time or comparative stats (e.g. blood pressure over a week).
- `graph TD` / `graph LR`: For flowcharts, decision trees, or showing biological processes / inheritance.
- `stateDiagram-v2`: For showing disease progression stages.

## Clinical Accuracy
- As a "reasoning engine", you must consider spatial layout and logic before answering.
- Ensure all medical data presented visually is highly accurate and clinically sound.
- If the user asks for a visualization that doesn't make sense medically, politely correct them and offer a more appropriate diagram.
- NEVER invent patient data. If asking for a general example, clearly label it as a "General Example" or "Reference Range".

## Tone & Explainability
- Professional, highly structured, and visually-focused.
- **Explainability**: You MUST explicitly explain the rationale behind your visualizations and highlight the clinical or statistical significance of the data shown.
- Keep text explanations before or after the chart concise but highly informative. Let the visualization and your sharp analysis do the talking.
"""

class VisualisationAgent(BaseAgent):
    """Generates Markdown and Mermaid visualizations of medical data."""
    # Nano Banana tasks require reasoning and complex structured output (Pro model)
    model_name = settings.pro_model
    system_prompt = SYSTEM_PROMPT
    agent_type = "visualisation"

    def respond(self, user_message: str, history: list, user_id: int) -> str:
        past_context = self.recall(user_id, user_message)
        
        # Give Nano Banana extra capability to pull facts for infographics
        search_query = user_message[:100] if user_message else "general medical statistics"
        factual_data = self.search(f"current clinical data statistics {search_query}")

        extra_context = ""
        if past_context:
            extra_context += f"[Previous context:]\n{past_context}\n\n"
        if factual_data:
            extra_context += f"[Search Data for Visualization Accuracy:]\n{factual_data}\n"

        reply = self.chat(user_message, history=history, extra_context=extra_context)
        
        self.remember(
            user_id,
            f"Visualisation requested: {user_message[:150]}\nGenerated Diagram.",
            {"agent": "visualisation", "user_id": str(user_id)},
        )
        return reply

visualisation_agent = VisualisationAgent()
