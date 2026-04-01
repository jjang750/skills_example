from typing import Any, Dict, List

from .base import BaseLLMProvider, IntentResult, SkillCall


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider (google-genai SDK)"""

    def __init__(self, client, model_name: str = "gemini-2.0-flash-exp"):
        self.client = client
        self.model_name = model_name

    async def parse_intent(
        self,
        user_message: str,
        skill_schemas: List[Dict[str, Any]],
    ) -> IntentResult:
        from google.genai import types

        function_declarations = []
        for schema in skill_schemas:
            fd = types.FunctionDeclaration(
                name=schema["name"],
                description=schema["description"],
                parameters=schema["parameters"],
            )
            function_declarations.append(fd)

        config_kwargs = {}
        if function_declarations:
            config_kwargs["tools"] = [
                types.Tool(function_declarations=function_declarations)
            ]

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        skill_calls = []
        has_function_call = (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
            and any(
                hasattr(part, "function_call") and part.function_call
                for part in response.candidates[0].content.parts
            )
        )

        if has_function_call:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    skill_calls.append(
                        SkillCall(
                            name=fc.name,
                            args=dict(fc.args) if fc.args else {},
                        )
                    )
            return IntentResult(skill_calls=skill_calls)

        return IntentResult(
            skill_calls=[],
            direct_response=response.text or "",
        )

    async def generate_response(
        self,
        user_message: str,
        skill_results: List[Dict[str, Any]],
    ) -> str:
        results_text = "\n".join(
            f"스킬 '{r['name']}' 실행 결과:\n{r.get('result', '결과 없음')}"
            for r in skill_results
        )
        prompt = (
            f"사용자 요청: {user_message}\n\n"
            f"실행된 스킬 결과:\n{results_text}\n\n"
            f"위 결과를 바탕으로 사용자에게 친절하게 응답해주세요."
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text
