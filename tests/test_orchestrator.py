import pytest
from langgraph_skills.core.base import BaseSkill
from langgraph_skills.core.orchestrator import FileBasedSkillOrchestrator
from langgraph_skills.providers.base import BaseLLMProvider, IntentResult, SkillCall


class EchoSkill(BaseSkill):
    def __init__(self):
        super().__init__(name="echo", description="Echoes input")

    async def execute(self, text: str = "", **kwargs):
        return f"echo: {text}"

    def _get_parameters(self):
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to echo"}},
            "required": ["text"],
        }


class DirectResponseProvider(BaseLLMProvider):
    async def parse_intent(self, user_message, skill_schemas):
        return IntentResult(skill_calls=[], direct_response=f"direct: {user_message}")

    async def generate_response(self, user_message, skill_results):
        return "should not be called"


class SkillCallingProvider(BaseLLMProvider):
    async def parse_intent(self, user_message, skill_schemas):
        return IntentResult(
            skill_calls=[SkillCall(name="echo", args={"text": user_message})]
        )

    async def generate_response(self, user_message, skill_results):
        return f"result: {skill_results[0]['result']}"


@pytest.mark.asyncio
async def test_direct_response_flow():
    provider = DirectResponseProvider()
    orchestrator = FileBasedSkillOrchestrator(provider=provider, skills_root="./nonexistent")
    # 수동 초기화 (builtin 스킬 로드 건너뛰기)
    orchestrator.registry.skills.clear()
    orchestrator.graph = orchestrator._build_graph()

    response = await orchestrator.process_request("hello")
    assert response == "direct: hello"


@pytest.mark.asyncio
async def test_skill_execution_flow():
    provider = SkillCallingProvider()
    orchestrator = FileBasedSkillOrchestrator(provider=provider, skills_root="./nonexistent")
    # 수동으로 echo 스킬만 등록
    await orchestrator.registry.register_skill(EchoSkill())
    orchestrator.graph = orchestrator._build_graph()

    response = await orchestrator.process_request("world")
    assert response == "result: echo: world"
