"""Trading analyst agent - main orchestrator."""

from dataclasses import dataclass
from google import genai
from google.genai import types

from api.config import get_settings
from api.agent.executor import CodeExecutor
from api.agent.prompts import SYSTEM_PROMPT, CODE_GENERATION_PROMPT, EXPLANATION_PROMPT


@dataclass
class AnalysisResult:
    """Result of analysis."""
    answer: str
    code: str | None = None
    data: dict | list | None = None


class TradingAnalyst:
    """AI-powered trading data analyst."""

    def __init__(self):
        self.settings = get_settings()
        self.executor = CodeExecutor()
        self.client = genai.Client(api_key=self.settings.gemini_api_key)

    async def analyze(self, question: str) -> AnalysisResult:
        """Analyze a trading question and return results."""

        # Step 1: Generate code
        code = await self._generate_code(question)

        if code is None:
            return AnalysisResult(
                answer="Не удалось сгенерировать код для анализа. Попробуйте переформулировать вопрос."
            )

        # Step 2: Execute code
        execution_result = self.executor.execute(code)

        if not execution_result.success:
            # Try to fix the code once
            code = await self._fix_code(question, code, execution_result.error)
            if code:
                execution_result = self.executor.execute(code)

        if not execution_result.success:
            return AnalysisResult(
                answer=f"Ошибка выполнения анализа: {execution_result.error}",
                code=code,
            )

        # Step 3: Explain results
        answer = await self._explain_results(question, code, execution_result.output)

        return AnalysisResult(
            answer=answer,
            code=code,
            data=execution_result.output,
        )

    async def _generate_code(self, question: str) -> str | None:
        """Generate Polars code for the question."""
        prompt = CODE_GENERATION_PROMPT.format(question=question)

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )

        # Extract code from response
        text = response.text
        if "```python" in text:
            code = text.split("```python")[1].split("```")[0].strip()
            return code
        elif "```" in text:
            code = text.split("```")[1].split("```")[0].strip()
            return code

        return None

    async def _fix_code(self, question: str, code: str, error: str) -> str | None:
        """Try to fix broken code."""
        prompt = f"""The following code failed with error: {error}

Original question: {question}

Code that failed:
```python
{code}
```

Please fix the code. Return only the corrected Python code."""

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )

        text = response.text
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()

        return None

    async def _explain_results(self, question: str, code: str, data: any) -> str:
        """Generate human-readable explanation of results."""
        prompt = EXPLANATION_PROMPT.format(
            question=question,
            code=code,
            data=str(data)[:5000],  # Limit data size
        )

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )

        return response.text
