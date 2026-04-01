import pytest
from langgraph_skills.providers.base import BaseLLMProvider, IntentResult, SkillCall


class MockProvider(BaseLLMProvider):
    """테스트용 Mock Provider"""

    def __init__(self, intent_result: IntentResult = None, response_text: str = "mock response"):
        self._intent_result = intent_result or IntentResult(skill_calls=[], direct_response="hello")
        self._response_text = response_text

    async def parse_intent(self, user_message, skill_schemas):
        return self._intent_result

    async def generate_response(self, user_message, skill_results):
        return self._response_text


def test_intent_result_needs_skill_execution():
    empty = IntentResult(skill_calls=[], direct_response="hi")
    assert empty.needs_skill_execution is False

    with_calls = IntentResult(
        skill_calls=[SkillCall(name="test", args={"a": 1})]
    )
    assert with_calls.needs_skill_execution is True


@pytest.mark.asyncio
async def test_mock_provider_parse_intent():
    provider = MockProvider()
    result = await provider.parse_intent("hello", [])

    assert result.direct_response == "hello"
    assert result.needs_skill_execution is False


@pytest.mark.asyncio
async def test_mock_provider_with_skill_calls():
    intent = IntentResult(
        skill_calls=[SkillCall(name="read_file", args={"file_path": "/tmp/test.txt"})]
    )
    provider = MockProvider(intent_result=intent)
    result = await provider.parse_intent("read a file", [{"name": "read_file", "description": "Read", "parameters": {}}])

    assert result.needs_skill_execution is True
    assert result.skill_calls[0].name == "read_file"


@pytest.mark.asyncio
async def test_mock_provider_generate_response():
    provider = MockProvider(response_text="결과입니다")
    result = await provider.generate_response("test", [{"name": "skill1", "result": "ok"}])

    assert result == "결과입니다"
