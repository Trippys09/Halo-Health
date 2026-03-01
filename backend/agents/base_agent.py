"""
HALO Health – Base Agent
All specialist agents inherit from here and get:
  - A configured Gemini GenerativeModel
  - web_search() helper
  - remember() / recall() helpers via ChromaDB
  - chat() helper that sends messages and returns text
"""
import logging
import uuid
from typing import List, Optional, Dict, Any

import google.generativeai as genai

from backend.config import settings
from backend.services import search_service, vector_store
from backend.services.model_selector import get_pro_model, get_flash_model

logger = logging.getLogger(__name__)

# Configure Gemini SDK once at import time
genai.configure(api_key=settings.gemini_api_key)


class BaseAgent:
    """
    Base class for all HALO Health agents.

    Subclass and override:
      - model_name   : which Gemini model to use
      - system_prompt: persona / instructions for the agent
      - agent_type   : snake_case identifier matching the DB enum
    """

    model_name: str = settings.flash_model
    system_prompt: str = "You are a helpful AI assistant."
    agent_type: str = "base"

    def __init__(self):
        # Dynamically pick the best available model for this agent's tier
        model_resolver = get_pro_model if self.model_name == settings.pro_model else get_flash_model
        resolved_name = model_resolver()
        logger.info("%s initialised with model: %s", self.__class__.__name__, resolved_name)
        self._model = genai.GenerativeModel(
            model_name=resolved_name,
            system_instruction=self.system_prompt,
        )

    # ── Gemini Chat ────────────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        extra_context: str = "",
    ) -> str:
        """
        Send a message to Gemini with optional history.

        Args:
            user_message: The current user turn.
            history: List of prior turns in Gemini format
                     [{role: 'user'|'model', parts: [{text: '...'}]}]
            extra_context: Any additional context prepended to the user message.
        Returns:
            The assistant's text response.
        """
        try:
            full_message = (
                f"{extra_context}\n\n{user_message}" if extra_context else user_message
            )
            chat_session = self._model.start_chat(history=history or [])
            response = chat_session.send_message(full_message)
            return response.text
        except Exception as exc:
            logger.error("Gemini chat error in %s: %s", self.agent_type, exc)
            return (
                "I'm sorry, I encountered an error processing your request. "
                "Please try again."
            )

    def chat_with_image(
        self,
        user_message: str,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Send a multimodal message (text + image) to Gemini using generate_content."""
        try:
            from PIL import Image
            import io
            
            # Convert bytes to PIL Image (Gemini SDK works best with PIL)
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"Processing image: format={image.format}, size={image.size}, mode={image.mode}")
            
            # Send to Gemini with text and image
            response = self._model.generate_content([
                user_message,
                image
            ])
            return response.text
        except Exception as exc:
            error_str = str(exc)
            logger.error("Gemini multimodal error in %s: %s", self.agent_type, exc)
            
            # Provide more helpful error messages
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                return ("⚠️ **API Rate Limit Reached**\n\n"
                       "The Gemini API free tier quota has been temporarily exhausted. "
                       "Please wait a few minutes and try again.\n\n"
                       "Tip: Consider upgrading to a paid plan for higher limits.")
            elif "INVALID_ARGUMENT" in error_str:
                return ("⚠️ **Invalid Image**\n\n"
                       "The uploaded image could not be processed. "
                       "Please ensure you're uploading a valid retinal fundus image in JPEG or PNG format.")
            else:
                return "I'm sorry, I could not process the image. Please try again."

    # ── Agentic Search ─────────────────────────────────────────────────────────

    def search(self, query: str, max_results: int = 5) -> str:
        """Perform a web search and return formatted results as a string."""
        results = search_service.web_search(query, max_results=max_results)
        return search_service.format_search_results(results)

    # ── Vector Memory ─────────────────────────────────────────────────────────

    def remember(self, user_id: int, text: str, metadata: Optional[Dict] = None) -> None:
        """Store a text snippet in the agent's per-user ChromaDB collection."""
        doc_id = str(uuid.uuid4())
        # ChromaDB requires non-empty metadata dict
        safe_meta = metadata or {"agent": self.agent_type, "user_id": str(user_id)}
        if not safe_meta:
            safe_meta = {"agent": self.agent_type}
        vector_store.add_to_memory(
            agent_type=self.agent_type,
            user_id=user_id,
            doc_id=doc_id,
            text=text,
            metadata=safe_meta,
        )

    def recall(self, user_id: int, query: str, n_results: int = 3) -> str:
        """Retrieve relevant past context from ChromaDB for the current query."""
        docs = vector_store.query_memory(
            agent_type=self.agent_type,
            user_id=user_id,
            query=query,
            n_results=n_results,
        )
        if not docs:
            return ""
        return "Relevant past context:\n" + "\n---\n".join(docs)
