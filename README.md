# LangGraph + Gemini Skills System

파일 기반 동적 스킬 로딩 시스템 for LangGraph and Gemini API

## 특징

- 📁 `/skills/스킬이름/SKILLS.md` 파일 기반 동적 스킬 로딩
- 🚀 LangGraph를 활용한 워크플로우 관리
- 🤖 Gemini API Function Calling 통합
- 📊 스킬 등록 현황 자동 표시
- 🔄 실시간 스킬 리로드 지원

## 프로젝트 구조

```
skills_example/
├── run.py                  # 메인 실행 스크립트 (진입점)
├── core/                   # 핵심 모듈
│   ├── base.py             # BaseSkill 추상 클래스
│   ├── loader.py           # 마크다운 기반 스킬 동적 로더
│   ├── registry.py         # 스킬 등록/관리 레지스트리
│   └── orchestrator.py     # LangGraph 워크플로우 오케스트레이터
├── skills/                 # 스킬 정의 디렉토리
│   ├── builtin.py          # 내장 스킬 (파일읽기, 터미널, 디렉토리조회)
│   └── sample/
│       └── SKILLS.md       # 샘플 스킬 (날씨 조회)
├── utils/
│   └── logger.py           # 스킬 실행 로깅 유틸리티
├── examples/
│   └── sample_skill.py     # 스킬 작성 예제
├── .env                    # 환경 변수 (API 키 등)
├── requirements.txt        # Python 의존성
└── setup.py                # 패키지 설정
```

## 동작 흐름

```
사용자 입력
    ↓
parse_intent (Gemini가 의도 분석 + Function Calling)
    ↓
[조건부 라우팅]
    ├→ execute_skills (스킬 실행 필요 시 → 병렬 실행)
    └→ generate_response (스킬 불필요 시 → 직접 응답)
    ↓
generate_response (결과 종합 → 최종 응답 생성)
    ↓
사용자에게 응답 출력
```

## 설치

```bash
uv pip install -r requirements.txt
```

## 환경 설정

`.env` 파일에 아래 항목을 설정합니다:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
SKILLS_ROOT=./skills
LOG_LEVEL=INFO
```

## 실행

```bash
venv/Scripts/activate
python run.py
```

실행 후 대화형 프롬프트가 나타나며, 자연어로 명령을 입력할 수 있습니다.
종료 시 `quit`, `exit`, `bye`, `종료` 중 하나를 입력합니다.

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
dependencies: 필요한패키지
---

# My Skill

스킬에 대한 설명

## Parameters

- `param1`: 파라미터 설명

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

## 기술 스택

- **Python** 3.8+
- **LangGraph** — 상태 기반 워크플로우 관리
- **Google Gemini API** (`google-genai` SDK) — 의도 분석 및 Function Calling
- **Pydantic** — 데이터 검증
