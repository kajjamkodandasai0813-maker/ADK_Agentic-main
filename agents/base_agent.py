"""
agents/base_agent.py - Base class for all agents with common ADK patterns
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import google.generativeai as genai
from config import GOOGLE_API_KEY, MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS


class BaseAgent(ABC):
    """
    Base class for all job application agents.
    Provides common LLM call infrastructure, retry logic, and logging helpers.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._setup_llm()

    def _setup_llm(self):
        """Initialize the Gemini LLM client."""
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=genai.GenerationConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )

    def _call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Gemini LLM with retry logic and error handling.

        Args:
            prompt: The prompt to send to the LLM
            max_retries: Number of retry attempts on failure

        Returns:
            LLM response text
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
                return ""
            except Exception as e:
                last_error = e
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    time.sleep(wait)

        raise RuntimeError(
            f"[{self.name}] LLM call failed after {max_retries} attempts: {last_error}"
        )

    def _build_system_context(self) -> str:
        """Return the system context/role for this agent."""
        return f"You are {self.name}. {self.description}"

    def _format_prompt(self, system_context: str, user_input: str) -> str:
        """Format a full prompt with system context + user input."""
        return f"""{system_context}

---
{user_input}
---

Provide a detailed, professional, and actionable response.
"""

    @abstractmethod
    def run(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary task.

        Args:
            session_data: Dict containing all session context

        Returns:
            Dict with agent output and metadata
        """
        pass
