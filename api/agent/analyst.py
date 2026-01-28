"""Barb trading analyst agent."""

from dataclasses import dataclass
from google import genai
from google.genai import types

from api.config import get_settings
from api.agent.executor import CodeExecutor
from api.agent.prompts import build_system_prompt, build_code_prompt, build_explanation_prompt
from config.models import get_model


@dataclass
class AnalysisResult:
    """Result of analysis."""
    answer: str
    code: str | None = None
    data: dict | list | None = None


class TradingAnalyst:
    """Trading data analyst agent."""

    def __init__(self, instrument: str = "NQ"):
        self.instrument = instrument
        self.settings = get_settings()
        self.executor = CodeExecutor()
        self.client = genai.Client(api_key=self.settings.gemini_api_key)
        self.model = get_model()
        self.system_prompt = build_system_prompt(instrument)

    def analyze(self, question: str) -> AnalysisResult:
        """Analyze a trading question."""
        code = self._generate_code(question)
        if not code:
            return AnalysisResult(answer="Failed to generate code.")

        result = self.executor.execute(code)
        if not result.success:
            return AnalysisResult(answer=f"Error: {result.error}", code=code)

        answer = self._explain(question, code, result.output)
        return AnalysisResult(answer=answer, code=code, data=result.output)

    def _generate_code(self, question: str) -> str | None:
        """Generate Polars code."""
        response = self.client.models.generate_content(
            model=self.model.id,
            contents=build_code_prompt(question),
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
            ),
        )

        text = response.text
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        if "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return None

    def _explain(self, question: str, code: str, data) -> str:
        """Explain results in Russian."""
        response = self.client.models.generate_content(
            model=self.model.id,
            contents=build_explanation_prompt(question, code, str(data)[:5000]),
        )
        return response.text
