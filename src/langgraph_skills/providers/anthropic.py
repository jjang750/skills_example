import json
from typing import Any, Dict, List

from .base import BaseLLMProvider, IntentResult, SkillCall


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider (anthropic SDK)"""

    def __init__(self, client, model_name: str = "claude-sonnet-4-20250514"):
        self.client = client
        self.model_name = model_name
        self.max_tokens = 4096

    def _schemas_to_tools(self, skill_schemas: List[Dict]) -> List[Dict]:
        """스킬 스키마를 Anthropic tools 포맷으로 변환"""
        return [
            {
                "name": s["name"],
                "description": s["description"],
                "input_schema": s["parameters"],
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
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": user_message}],
        }
        if tools:
            kwargs["tools"] = tools

        # AsyncAnthropic과 Anthropic 모두 지원
        messages_api = self.client.messages
        if hasattr(messages_api, "acreate"):
            response = await messages_api.acreate(**kwargs)
        else:
            response = messages_api.create(**kwargs)

        skill_calls = []
        direct_text_parts = []

        for block in response.content:
            if block.type == "tool_use":
                skill_calls.append(
                    SkillCall(
                        name=block.name,
                        args=block.input if isinstance(block.input, dict) else {},
                    )
                )
            elif block.type == "text":
                direct_text_parts.append(block.text)

        if skill_calls:
            return IntentResult(skill_calls=skill_calls)

        return IntentResult(
            skill_calls=[],
            direct_response="\n".join(direct_text_parts) if direct_text_parts else "",
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

        messages_api = self.client.messages
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
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

        if hasattr(messages_api, "acreate"):
            response = await messages_api.acreate(**kwargs)
        else:
            response = messages_api.create(**kwargs)

        text_parts = [
            block.text for block in response.content if block.type == "text"
        ]
        return "\n".join(text_parts)
