"""
HALO Health – Diagnostic Reporting Agent (PRISM)

Multimodal medical scan analysis. Accepts text descriptions AND/OR
base64-encoded medical images. Returns structured diagnostic reports.
Uses gemini-1.5-pro which fully supports multimodal input.
"""
import logging
from backend.agents.base_agent import BaseAgent
from backend.config import settings
import google.generativeai as genai
import tempfile
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are Dr. PRISM, a senior Clinical Radiologist and Pathologist at HALO Health.
Provide your expert clinical interpretation with the authority and thoroughness of a human specialist.

## Operational Approach
- **Context-Aware Responses**: If the user asks a general question (e.g., "What is a CT scan?"), answer conversationally, CRISP, and CONCISE. Speak like a real human doctor. Never sound like an AI.
- **Image/Case Analysis**: ONLY generate the **full structured report** if the user provides a medical scan (image) or describes a specific patient case for diagnosis.
- Infer scan type, body region, and clinical context from the image and any text provided — do NOT ask a series of clarifying questions.
- If critical information is genuinely absent AND prevents meaningful analysis, ask ONE specific question.
- Always remain highly realistic, humanized, and professional.

## Report Structure (ONLY use when diagnosing a scan or patient case)
```
## 🔬 Preliminary Diagnostic Report — PRISM

**Scan Type:** [X-ray / MRI / CT Scan / Retinal Image / Ultrasound / Pathology Slide / Other — inferred or specified]
**Region of Interest:** [anatomical region]
**Clinical Context:** [from user description, or "Not provided — analysis based on imaging only"]
**Report Date:** [current date]

---
### Key Findings
[Detailed bullet list: location, size, density, morphology, signal characteristics]
[Mark critical findings with ⚠️]

### Differential Diagnoses
| Rank | Diagnosis | Likelihood | Supporting Evidence |
|---|---|---|---|
| 1 | [primary] | High | [specific imaging features] |
| 2 | [alternative] | Moderate | [rationale] |
| 3 | [alternative] | Low | [rationale] |

### Severity Assessment
🟢 Normal/Incidental  🟡 Mild — Monitor  🟠 Moderate — Follow-up Required  🔴 Severe — Urgent Attention

### Recommended Next Steps
[Specific investigations, specialist referrals, timeframe]
```

## Communication Style
- Clinical, precise, and highly analytical.
- **Explainability**: You MUST explicitly explain the rationale behind your findings. Link specific features seen in the retinal scan (or described in text) directly to the clinical outcomes and predictive risk factors. 
- Explain the significance of the visual biomarkers in relation to the diagnosis.
- State clearly when image quality limits interpretation.
- Never fabricate findings — report only what can be reasonably inferred.
- **IMPORTANT**: If the Ocular AI Pipeline Analysis is provided in the prompt context, you MUST incorporate its findings (predictions, probabilities) explicitly in your report. You can use markdown image syntax `![Attention Map](/gradcam/<filename>)` to embed the attention maps into your report if the path is provided.
"""


class DiagnosticAgent(BaseAgent):
    model_name = settings.pro_model
    system_prompt = SYSTEM_PROMPT
    agent_type = "diagnostic"

    def respond(
        self,
        user_message: str,
        history: list,
        user_id: int,
        image_data: bytes = None,
        mime_type: str = "image/jpeg",
    ) -> str:
        past_context = self.recall(user_id, user_message)

        # Search for relevant clinical guidelines
        search_query = user_message[:80] if user_message else "medical imaging analysis guidelines"
        guidelines = self.search(f"clinical radiology guidelines {search_query}")

        extra_context = ""
        if past_context:
            extra_context += f"[Previous session context:]\n{past_context}\n\n"
        if guidelines:
            extra_context += f"[Relevant clinical guidelines:]\n{guidelines}\n"

        if image_data:
            # 1) Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name

            try:
                # 2) Run Ocular Pipeline (lazy import to prevent startup crashes if torch/grad-cam missing)
                from backend.oculomics.inference import get_ocular_api
                ocular_api = get_ocular_api()
                if ocular_api:
                    ocular_results = ocular_api.run_full_profile(tmp_path)
                    if ocular_results:
                        extra_context += "\n[M-BRSET Ocular AI Pipeline Output Predictions]\n"
                        for task, data in ocular_results.items():
                            pred = data['prediction']
                            map_path = data['attention_map']
                            map_filename = os.path.basename(map_path)
                            # Convert dict predictions format (for classification)
                            if isinstance(pred, dict):
                                extra_context += f"- **{task}**: Class {pred.get('class')} (Confidence: {pred.get('probability', 0):.2f}) —— GradCAM Output Image URL: `/gradcam/{map_filename}`\n"
                            else:
                                extra_context += f"- **{task}**: Predicted Value = {pred:.2f} —— GradCAM Output Image URL: `/gradcam/{map_filename}`\n"
            except Exception as e:
                logger.error(f"Oculomics pipeline failed: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            # Build a rich prompt that includes system context + extra context + user message
            full_prompt = self.system_prompt
            if extra_context:
                full_prompt += f"\n\n{extra_context}"
            full_prompt += f"\n\nUser says: {user_message or 'Please analyse this medical scan.'}"
            full_prompt += "\n\nProvide a full structured diagnostic report using the template above."

            reply = self._generate_with_image(image_data, mime_type, full_prompt)
        else:
            # Text-only mode — use chat with history
            reply = self.chat(user_message, history=history, extra_context=extra_context)

        self.remember(
            user_id,
            f"Diagnostic request: {user_message[:200]}\nReport: {reply[:400]}",
            {"agent": "diagnostic", "user_id": str(user_id)},
        )
        return reply

    def _generate_with_image(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        """Direct generate_content call with inline image data using the resolved model."""
        try:
            # self._model already has the dynamically selected model from BaseAgent.__init__
            response = self._model.generate_content(
                [
                    {"mime_type": mime_type, "data": image_data},
                    prompt,
                ]
            )
            return response.text
        except Exception as exc:
            logger.error("DiagnosticAgent image error: %s", exc)
            return (
                "I wasn't able to process your image. This could be due to:\n"
                "- Unsupported image format (try JPG or PNG)\n"
                "- Image too large\n"
                "- Temporary API issue\n\n"
                "Please try again or describe the scan in text and I'll help from your description."
            )


diagnostic_agent = DiagnosticAgent()
