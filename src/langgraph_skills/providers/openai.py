import json
from typing import Any, Dict, List

from .base import BaseLLMProvider, IntentResult, SkillCall


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider (openai SDK)"""

    def __init__(self, client, model_name: str = "gpt-4o"):
        self.client = client
        self.model_name = model_name

    def _schemas_to_tools(self, skill_schemas: List[Dict]) -> List[Dict]:
        """스킬 스키마를 OpenAI tools 포맷으로 변환"""
        return [
            {
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s["description"],
                    "parameters": s["parameters"],
                },
            }
            for s in skill_schemas
        ]

    async def parse_intent(
        self,
        user_message: str,
        skill_schemas: List[Dict[str, Any]],
    ) -> IntentResult:
        tools = self._schemas_to_tools(skill_schemas) if skill_schemas else None

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": user_message}],
        }
        if tools:
            kwargs["tools"] = tools

        # AsyncOpenAI와 OpenAI 모두 지원
        completions = self.client.chat.completions
        if hasattr(completions, "acreate"):
            response = await completions.acreate(**kwargs)
        else:
            response = completions.create(**kwargs)

        message = response.choices[0].message

        if message.tool_calls:
            skill_calls = [
                SkillCall(
                    name=tc.function.name,
                    args=json.loads(tc.function.arguments) if tc.function.arguments else {},
                )
                for tc in message.tool_calls
            ]
            return IntentResult(skill_calls=skill_calls)

        return IntentResult(skill_calls=[], direct_response=message.content or "")

    async def generate_response(
        self,
        user_message: str,
        skill_results: List[Dict[str, Any]],
    ) -> str:
        results_text = "\n".join(
            f"스킬 '{r['name']}' 실행 결과:\n{r.get('result', '결과 없음')}"
            for r in skill_results
        )

        completions = self.client.chat.completions
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": user_message},
                {
                    "role": "assistant",
                    "content": f"실행된 스킬 결과:\n{results_text}",
                },
                {
                    "role": "user",
                    "content": "위 결과를 바탕으로 사용자에게 친절하게 응답해주세요.",
                },
            ],
        }

        if hasattr(completions, "acreate"):
            response = await completions.acreate(**kwargs)
        else:
            response = completions.create(**kwargs)

        return response.choices[0].message.content
