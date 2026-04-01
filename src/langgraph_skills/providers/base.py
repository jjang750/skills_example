from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillCall:
    """LLM이 반환한 tool/function call의 정규화된 표현"""
    name: str
    args: Dict[str, Any]


@dataclass
class IntentResult:
    """의도 파싱 결과 — skill call 목록 또는 직접 텍스트 응답"""
    skill_calls: List[SkillCall] = field(default_factory=list)
    direct_response: Optional[str] = None

    @property
    def needs_skill_execution(self) -> bool:
        return len(self.skill_calls) > 0


class BaseLLMProvider(ABC):
    """LLM Provider 추상 베이스 클래스.

    각 provider는 두 가지 기능을 구현해야 합니다:
    1. 사용자 의도를 파악하여 어떤 스킬을 호출할지 결정 (function/tool calling)
    2. 스킬 실행 결과를 바탕으로 최종 텍스트 응답 생성
    """

    @abstractmethod
    async def parse_intent(
        self,
        user_message: str,
        skill_schemas: List[Dict[str, Any]],
    ) -> IntentResult:
        """사용자 메시지를 분석하여 호출할 스킬을 결정합니다.

        Args:
            user_message: 사용자 입력 문자열.
            skill_schemas: BaseSkill.get_schema()의 출력 리스트.
                각 dict는 name, description, parameters 키를 가짐.

        Returns:
            skill_calls가 채워지거나 direct_response가 설정된 IntentResult.
        """
        ...

    @abstractmethod
    async def generate_response(
        self,
        user_message: str,
        skill_results: List[Dict[str, Any]],
    ) -> str:
        """스킬 실행 결과를 포함한 최종 응답을 생성합니다.

        Args:
            user_message: 원래 사용자 입력.
            skill_results: 'name'과 'result' 키를 가진 dict 리스트.

        Returns:
            사용자에게 전달할 최종 응답 텍스트.
        """
        ...
