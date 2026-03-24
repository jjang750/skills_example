#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LangGraph Skills System 실행 스크립트 (Updated for new google.genai SDK)
"""
import os
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

# --- UPDATED IMPORT ---
from google import genai
# --- END OF UPDATE ---

from dotenv import load_dotenv
# Make sure your orchestrator is also updated (see instructions below)
from core.orchestrator import FileBasedSkillOrchestrator

# 환경 변수 로드
load_dotenv()

async def main():
    """메인 실행 함수"""
    
    # 1. Gemini API 초기화 (Updated)
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일에 GEMINI_API_KEY=your_key_here 형식으로 추가하세요.")
        return
    
    # --- UPDATED INITIALIZATION ---
    # Create a client instance
    client = genai.Client(api_key=api_key)
    # Specify the model name as a string when calling
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp') # Updated default model
    # --- END OF UPDATE ---
    
    # 2. 스킬 시스템 초기화
    skills_root = os.getenv('SKILLS_ROOT', './skills')
    # Pass the client and model name to the orchestrator
    orchestrator = FileBasedSkillOrchestrator(
        genai_client=client, # Pass the client
        model_name=model_name, # Pass the model name
        skills_root=skills_root
    )
    
    # ... (rest of your main function remains the same) ...
    print("\n" + "="*60)
    print("🚀 LangGraph Skills System 시작")
    print("="*60)
    
    try:
        await orchestrator.initialize()
        print("\n" + "="*60)
        print("💬 대화를 시작합니다. (종료: 'quit', 'exit', 'bye')")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n👤 > ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye', '종료']:
                    print("\n👋 시스템을 종료합니다.")
                    break
                if not user_input:
                    continue
                print("\n🤔 처리 중...")
                response = await orchestrator.process_request(user_input)
                print(f"\n🤖 > {response}")
            except KeyboardInterrupt:
                print("\n\n👋 사용자에 의해 중단되었습니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
    except Exception as e:
        print(f"\n❌ 초기화 오류: {e}")
        print("📋 자세한 내용은 로그 파일을 확인하세요.")

if __name__ == "__main__":
    asyncio.run(main())