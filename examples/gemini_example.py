"""Gemini Provider 사용 예시"""
import os
import asyncio
from google import genai
from langgraph_skills import FileBasedSkillOrchestrator
from langgraph_skills.providers.gemini import GeminiProvider


async def main():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    provider = GeminiProvider(client, model_name="gemini-2.0-flash-exp")

    orchestrator = FileBasedSkillOrchestrator(
        provider=provider,
        skills_root="./skills",
    )
    await orchestrator.initialize()

    response = await orchestrator.process_request("현재 디렉토리의 파일 목록을 보여줘")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
