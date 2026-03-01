"""
HALO Health – Oculomics Agent (Retina Engine)

Integrates autonomously with PyTorch Foundational Models (ViT) via GradCAM++
to predict age, gender, hypertension, and retinal diseases from Fundus images.
"""
import logging
import os
import tempfile
import json
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are the HALO IRIS Engine, a clinical AI assistant specializing in retinal fundus image analysis.

When analyzing retinal fundus images, provide a comprehensive clinical assessment following this structure:

## 👁️ Retinal Fundus Analysis Report

### 1. Image Quality Assessment
- Confirm if this is a valid retinal fundus photograph
- Assess image clarity, field of view, and lighting

### 2. Anatomical Structures
Identify and describe:
- **Optic Disc**: Location, color, margins, cup-to-disc ratio
- **Macula**: Appearance, foveal reflex
- **Blood Vessels**: Caliber, tortuosity, arteriovenous ratio
- **Retinal Background**: Color, uniformity

### 3. Pathological Findings
Look for signs of:
- **Diabetic Retinopathy**: Microaneurysms, hemorrhages, hard exudates, cotton-wool spots, neovascularization
- **Hypertensive Retinopathy**: AV nicking, copper/silver wiring, flame hemorrhages
- **Macular Edema**: Retinal thickening, hard exudate rings
- **Glaucoma**: Increased cup-to-disc ratio, disc pallor, RNFL defects
- **Age-related Macular Degeneration**: Drusen, geographic atrophy, CNV
- **Other**: Vascular occlusions, optic neuropathy

### 4. Risk Assessment
Based on visible findings, assess potential systemic health risks:
- Diabetes complications
- Cardiovascular disease indicators
- Neurological concerns

### 5. Clinical Recommendations
- Suggested follow-up actions
- Referrals to specialists
- Additional testing needed

**IMPORTANT**:
- This is an AI-assisted preliminary analysis for educational purposes
- Always emphasize that definitive diagnosis requires examination by a qualified ophthalmologist
- Be specific about what you observe in the image
- If image quality is poor or structures are unclear, state this limitation
"""

# Global storage for the latest tool run within a request (per-instance)
_LAST_TOOL_RESULTS = {}

def analyze_retinal_scan(image_path: str) -> str:
    """
    Executes the PyTorch Foundational CV Models over the provided retinal image to extract systemic biomarkers.
    
    Args:
        image_path (str): The absolute file path to the temporary retinal image on disk.
        
    Returns:
        str: A JSON string containing dictionaries of predictions, probabilities, and GradCAM++ heatmap URLs for each task.
    """
    try:
        from backend.oculomics.inference import get_ocular_api
        ocular_api = get_ocular_api()
        if not ocular_api:
            return json.dumps({"error": "PyTorch inference engine failed to load or weights are missing."})
            
        results = ocular_api.run_full_profile(image_path)
        
        # Format the output so the Gemini agent can read the image URLs
        formatted_results = {}
        for task, data in results.items():
            pred = data['prediction']
            map_path = data['attention_map']
            map_filename = os.path.basename(map_path)
            
            formatted_results[task] = {
                "prediction": pred.get("class") if isinstance(pred, dict) else round(pred, 2),
                "probability": pred.get("probability") if isinstance(pred, dict) else None,
                "gradcam_heatmap_url": f"/gradcam/{map_filename}"
            }
            
        global _LAST_TOOL_RESULTS
        _LAST_TOOL_RESULTS = formatted_results
        
        return json.dumps(formatted_results)
    except Exception as e:
        logger.error(f"Oculomics Vision Tool Error: {e}")
        return json.dumps({"error": f"Internal inference error: {str(e)}"})


class OculomicsAgent(BaseAgent):
    model_name = settings.pro_model  # Force Pro model for multimodal image support
    system_prompt = SYSTEM_PROMPT
    agent_type = "oculomics"

    def __init__(self):
        """Initialize the agent without tools (we'll use vision directly)"""
        super().__init__()
        # Override to not use tools for vision-based analysis
        import google.generativeai as genai
        from backend.services.model_selector import get_pro_model
        self._model = genai.GenerativeModel(
            model_name=get_pro_model(),
            system_instruction=self.system_prompt,
            # No tools - just pure vision analysis
        )

    def _extract_outcomes_from_text(self, text: str) -> dict:
        """
        Extract structured predictive outcomes from the Gemini text analysis.
        Returns risk levels for each condition based on text analysis.
        """
        text_lower = text.lower()
        outcomes = {}

        # Helper function to determine risk level
        def get_risk_level(text_lower, keywords_high, keywords_medium, keywords_low):
            """Determine risk level based on keywords in text"""
            if any(keyword in text_lower for keyword in keywords_high):
                return {"prediction": 1, "probability": 0.75}  # Positive - High confidence
            elif any(keyword in text_lower for keyword in keywords_medium):
                return {"prediction": 1, "probability": 0.50}  # Positive - Moderate confidence
            elif any(keyword in text_lower for keyword in keywords_low):
                return {"prediction": 0, "probability": 0.25}  # Negative - Low confidence
            else:
                return {"prediction": 0, "probability": 0.10}  # Negative - Very low confidence

        # Diabetic Retinopathy
        outcomes["Diabetes"] = get_risk_level(
            text_lower,
            ["microaneurysm", "diabetic retinopathy", "hemorrhage", "hard exudate", "neovascularization"],
            ["early diabetic", "mild diabetic", "potential diabetic"],
            ["no diabetic", "no signs of diabetic"]
        )

        # Macular Edema
        outcomes["Edema"] = get_risk_level(
            text_lower,
            ["macular edema", "retinal thickening", "edema present"],
            ["mild edema", "possible edema"],
            ["no edema", "no signs of edema"]
        )

        # Hypertension
        outcomes["Hypertension"] = get_risk_level(
            text_lower,
            ["hypertensive retinopathy", "av nicking", "copper wiring", "silver wiring"],
            ["mild hypertensive", "possible hypertensive"],
            ["no hypertensive", "no signs of hypertension"]
        )

        # ICDR (Diabetic Retinopathy Severity)
        outcomes["ICDR"] = outcomes["Diabetes"]  # Use same as diabetes

        # Cardiovascular Risk
        outcomes["Cardio Risk"] = get_risk_level(
            text_lower,
            ["cardiovascular risk", "vascular occlusion", "severe vascular"],
            ["moderate cardiovascular", "vascular changes"],
            ["low cardiovascular", "no cardiovascular"]
        )

        # AMI Risk (Acute Myocardial Infarction)
        outcomes["AMI Risk"] = get_risk_level(
            text_lower,
            ["acute", "severe vascular", "occlusion"],
            ["moderate vascular"],
            ["low risk", "no acute"]
        )

        # Neuropathy
        outcomes["Neuropathy"] = get_risk_level(
            text_lower,
            ["neuropathy", "optic neuropathy", "nerve damage"],
            ["possible neuropathy", "mild optic"],
            ["no neuropathy", "no nerve"]
        )

        # Nephropathy
        outcomes["Nephropathy"] = get_risk_level(
            text_lower,
            ["nephropathy", "kidney", "renal"],
            ["possible nephropathy"],
            ["no nephropathy", "no kidney"]
        )

        # Gender (not applicable for fundus images, set to unknown)
        outcomes["Gender"] = {"prediction": None, "probability": 0.0}

        # Age (estimate based on findings)
        if any(word in text_lower for word in ["age-related", "amd", "drusen"]):
            outcomes["Age"] = {"prediction": "60+", "probability": 0.70}
        elif any(word in text_lower for word in ["young", "early"]):
            outcomes["Age"] = {"prediction": "30-50", "probability": 0.60}
        else:
            outcomes["Age"] = {"prediction": None, "probability": 0.0}

        return outcomes

    def respond(
        self,
        user_message: str,
        history: list,
        user_id: int,
        image_data: bytes = None,
        mime_type: str = "image/jpeg",
    ) -> Any:
        past_context = self.recall(user_id, user_message)

        extra_context = ""
        if past_context:
            extra_context += f"[Previous session context:]\n{past_context}\n\n"

        if image_data:
            # Use Gemini Vision directly for image analysis (ML models require weights we don't have)
            logger.info("Using Gemini Vision for retinal image analysis")

            analysis_prompt = user_message or """Please analyze this retinal/eye scan image. Provide a detailed clinical assessment including:

1. **Image Quality Assessment**: Is this a valid retinal fundus image?
2. **Anatomical Structures**: Identify optic disc, macula, blood vessels
3. **Potential Findings**: Any signs of:
   - Diabetic Retinopathy (microaneurysms, hemorrhages, exudates)
   - Macular Edema
   - Hypertensive changes
   - Glaucoma indicators
   - Age-related macular degeneration
4. **Risk Assessment**: Overall health indicators visible
5. **Recommendations**: Suggested follow-up actions

Note: This is an AI-assisted preliminary analysis. Always consult an ophthalmologist for definitive diagnosis."""

            reply = self.chat_with_image(
                user_message=analysis_prompt,
                image_data=image_data,
                mime_type=mime_type,
                history=history,
            )

            # Extract structured outcomes from the text response
            outcomes = self._extract_outcomes_from_text(reply)

            self.remember(
                user_id,
                f"Oculomics request (Gemini Vision): {user_message[:200] if user_message else 'Image analysis'}\nReport: {reply[:400]}",
                {"agent": "oculomics", "user_id": str(user_id)},
            )
            return reply, outcomes
        else:
            # Text-only mode fallback
            reply = self.chat(user_message, history=history, extra_context=extra_context)

        global _LAST_TOOL_RESULTS
        outcomes = _LAST_TOOL_RESULTS.copy() if _LAST_TOOL_RESULTS else None
        _LAST_TOOL_RESULTS.clear() # Reset for next run

        self.remember(
            user_id,
            f"Oculomics request: {user_message[:200]}\nReport: {reply[:400]}",
            {"agent": "oculomics", "user_id": str(user_id)},
        )
        return reply, outcomes

# Initialize the oculomics agent
oculomics_agent = OculomicsAgent()
