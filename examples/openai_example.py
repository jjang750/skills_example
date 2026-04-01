"""OpenAI Provider 사용 예시"""
import os
import asyncio
from openai import OpenAI
from langgraph_skills import FileBasedSkillOrchestrator
from langgraph_skills.providers.openai import OpenAIProvider


async def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    provider = OpenAIProvider(client, model_name="gpt-4o")

    orchestrator = FileBasedSkillOrchestrator(
        provider=provider,
        skills_root="./skills",
    )
    await orchestrator.initialize()

    response = await orchestrator.process_request("현재 디렉토리의 파일 목록을 보여줘")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
