import pytest
from langgraph_skills.core.registry import SkillRegistry
from langgraph_skills.core.base import BaseSkill


class DummySkill(BaseSkill):
    def __init__(self, name="dummy", description="A dummy skill"):
        super().__init__(name=name, description=description)

    async def execute(self, **kwargs):
        return "dummy result"


@pytest.mark.asyncio
async def test_register_and_get_skill():
    registry = SkillRegistry()
    skill = DummySkill()
    result = await registry.register_skill(skill)

    assert result is True
    assert registry.get_skill("dummy") is skill


@pytest.mark.asyncio
async def test_unregister_skill():
    registry = SkillRegistry()
    await registry.register_skill(DummySkill())

    assert await registry.unregister_skill("dummy") is True
    assert registry.get_skill("dummy") is None


@pytest.mark.asyncio
async def test_get_skill_list():
    registry = SkillRegistry()
    await registry.register_skill(DummySkill("a", "Skill A"))
    await registry.register_skill(DummySkill("b", "Skill B"))

    simple = registry.get_skill_list()
    assert len(simple) == 2

    detailed = registry.get_skill_list(detailed=True)
    assert detailed[0]["use_count"] == 0
    assert detailed[1]["status"] == "registered"
