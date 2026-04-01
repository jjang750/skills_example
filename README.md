# langgraph-skills

LangGraph 기반 스킬 오케스트레이션 라이브러리 (멀티 LLM 지원)

## 특징

- **멀티 LLM 지원** — Gemini, OpenAI, Anthropic 또는 커스텀 Provider
- **파일 기반 스킬 로딩** — `SKILLS.md` 마크다운으로 스킬 정의, 재시작 없이 동적 로드
- **LangGraph 워크플로우** — 의도 파악 → 스킬 실행 → 응답 생성 상태 머신
- **병렬 스킬 실행** — asyncio 기반 동시 실행
- **내장 스킬 3종** — 파일 읽기, 터미널 실행, 디렉토리 조회

## 설치

```bash
# Gemini만 사용
pip install langgraph-skills[gemini]

# OpenAI만 사용
pip install langgraph-skills[openai]

# Anthropic만 사용
pip install langgraph-skills[anthropic]

# 모든 Provider
pip install langgraph-skills[all]
```


## 빠른 시작

### Gemini

```python
import asyncio
from google import genai
from langgraph_skills import FileBasedSkillOrchestrator
from langgraph_skills.providers.gemini import GeminiProvider

async def main():
    client = genai.Client(api_key="YOUR_API_KEY")
    provider = GeminiProvider(client, model_name="gemini-2.0-flash-exp")

    orchestrator = FileBasedSkillOrchestrator(provider=provider, skills_root="./skills")
    await orchestrator.initialize()

    response = await orchestrator.process_request("현재 디렉토리의 파일 목록을 보여줘")
    print(response)

asyncio.run(main())
```

### OpenAI

```python
from openai import OpenAI
from langgraph_skills import FileBasedSkillOrchestrator
from langgraph_skills.providers.openai import OpenAIProvider

async def main():
    client = OpenAI(api_key="YOUR_API_KEY")
    provider = OpenAIProvider(client, model_name="gpt-4o")

    orchestrator = FileBasedSkillOrchestrator(provider=provider, skills_root="./skills")
    await orchestrator.initialize()

    response = await orchestrator.process_request("README.md 파일을 읽어줘")
    print(response)
```

### Anthropic

```python
from anthropic import Anthropic
from langgraph_skills import FileBasedSkillOrchestrator
from langgraph_skills.providers.anthropic import AnthropicProvider

async def main():
    client = Anthropic(api_key="YOUR_API_KEY")
    provider = AnthropicProvider(client, model_name="claude-sonnet-4-20250514")

    orchestrator = FileBasedSkillOrchestrator(provider=provider, skills_root="./skills")
    await orchestrator.initialize()

    response = await orchestrator.process_request("터미널에서 git status를 실행해줘")
    print(response)
```

## 동작 흐름

```
사용자 입력
    ↓
parse_intent (LLM이 의도 분석 + Function/Tool Calling)
    ↓
[조건부 라우팅]
    ├→ execute_skills (스킬 실행 필요 시 → 병렬 실행)
    └→ generate_response (스킬 불필요 시 → 직접 응답)
    ↓
generate_response (결과 종합 → 최종 응답 생성)
    ↓
사용자에게 응답 반환
```

## 내장 스킬

| 스킬 | 이름 | 설명 |
|------|------|------|
| FileReadSkill | `read_file` | 파일 내용 읽기 |
| TerminalSkill | `run_terminal` | 터미널 명령어 실행 (30초 타임아웃) |
| ListDirectorySkill | `list_directory` | 디렉토리 파일/폴더 목록 조회 |

## 커스텀 스킬 추가

`skills/` 디렉토리에 새 폴더를 만들고 `SKILLS.md` 파일을 작성합니다:

```markdown
---
name: my_skill
description: 스킬 설명
version: 1.0.0
author: 작성자
---

# My Skill

스킬에 대한 설명

```python
class MySkill(BaseSkill):
    def __init__(self):
        super().__init__(name="my_skill", description="스킬 설명")

    async def execute(self, param1: str, **kwargs) -> str:
        return f"결과: {param1}"

    def _get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "파라미터 설명"
                }
            },
            "required": ["param1"]
        }
`` `
```

시스템 재시작 없이 자동으로 로드됩니다.

## 커스텀 Provider 만들기

`BaseLLMProvider`를 상속하여 어떤 LLM이든 연결할 수 있습니다:

```python
from langgraph_skills import BaseLLMProvider, IntentResult, SkillCall

class MyCustomProvider(BaseLLMProvider):
    async def parse_intent(self, user_message, skill_schemas):
        # 사용자 메시지를 분석하여 호출할 스킬 결정
        # skill_schemas: [{"name": ..., "description": ..., "parameters": ...}]
        return IntentResult(
            skill_calls=[SkillCall(name="read_file", args={"file_path": "test.txt"})],
        )

    async def generate_response(self, user_message, skill_results):
        # 스킬 실행 결과를 바탕으로 최종 응답 생성
        # skill_results: [{"name": ..., "result": ...}]
        return f"결과: {skill_results[0]['result']}"
```

## 패키지 구조

```
src/langgraph_skills/
├── __init__.py           # Public API exports
├── core/
│   ├── base.py           # BaseSkill 추상 클래스
│   ├── loader.py         # SKILLS.md 기반 동적 스킬 로더
│   ├── registry.py       # 스킬 등록/관리 레지스트리
│   └── orchestrator.py   # LangGraph 워크플로우 오케스트레이터
├── providers/
│   ├── base.py           # BaseLLMProvider, IntentResult, SkillCall
│   ├── gemini.py         # Google Gemini Provider
│   ├── openai.py         # OpenAI Provider
│   └── anthropic.py      # Anthropic Claude Provider
├── skills/
│   └── builtin.py        # 내장 스킬 3종
└── utils/
    └── logger.py         # 실행 로깅 유틸리티
```

## API Reference

### Core

| 클래스 | 설명 |
|--------|------|
| `BaseSkill` | 스킬 추상 클래스. `execute()`, `get_schema()`, `_get_parameters()` |
| `FileBasedSkillLoader` | `SKILLS.md`에서 스킬을 동적 로드 |
| `SkillRegistry` | 스킬 등록, 조회, 사용 통계 관리 |
| `FileBasedSkillOrchestrator` | LangGraph 워크플로우를 통한 스킬 오케스트레이션 |

### Providers

| 클래스 | 설명 |
|--------|------|
| `BaseLLMProvider` | Provider 추상 클래스 (`parse_intent`, `generate_response`) |
| `IntentResult` | 의도 파싱 결과 (skill_calls 또는 direct_response) |
| `SkillCall` | 정규화된 tool/function call 표현 (name, args) |
| `GeminiProvider` | Google Gemini (`google-genai` SDK) |
| `OpenAIProvider` | OpenAI (`openai` SDK) |
| `AnthropicProvider` | Anthropic Claude (`anthropic` SDK) |

## 배포 (PyPI)

### 1. API 토큰 발급

1. [pypi.org](https://pypi.org) 로그인
2. **Account settings** → **API tokens** → **Add API token**
3. Token name 입력, Scope는 `Entire account` 선택 → **Create token**
4. `pypi-`로 시작하는 토큰을 복사

### 2. 빌드 및 업로드

```bash
pip install build twine
python -m build
twine upload dist/* -u __token__ -p pypi-YOUR_TOKEN_HERE
```

매번 토큰 입력이 번거로우면 `~/.pypirc`를 만들어두세요:

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

이후 `twine upload dist/*`만 실행하면 됩니다.

## 기술 스택

- **Python** 3.10+
- **LangGraph** — 상태 기반 워크플로우 관리
- **Pydantic** — 데이터 검증
- **google-genai** / **openai** / **anthropic** — LLM Provider SDK (선택)

## 라이선스

MIT
