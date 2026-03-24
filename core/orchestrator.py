from typing import Dict, Any, List, TypedDict
import asyncio
from langgraph.graph import StateGraph, END
from .loader import FileBasedSkillLoader
from .registry import SkillRegistry
from .base import BaseSkill


class SkillState(TypedDict):
    """LangGraph 상태 정의"""
    messages: List[Dict[str, Any]]
    skills: Dict[str, Any]
    skill_calls: List[Dict[str, Any]]
    context: Dict[str, Any]


class FileBasedSkillOrchestrator:
    """파일 기반 스킬 시스템 통합 오케스트레이터"""

    def __init__(self, genai_client, model_name: str, skills_root: str = "./skills"):
        self.client = genai_client
        self.model_name = model_name
        self.loader = FileBasedSkillLoader(skills_root)
        self.registry = SkillRegistry()
        self.graph = None

    async def initialize(self):
        """초기화: 모든 스킬 로드 및 등록"""
        print("🔄 스킬 시스템 초기화 중...")

        # Built-in 스킬 등록
        await self._register_builtin_skills()

        # 스킬 폴더 탐색
        skill_names = await self.loader.discover_skills()
        print(f"📁 발견된 스킬 폴더: {len(skill_names)}개")

        # 각 스킬 로드 및 등록
        loaded_count = 0
        for skill_name in skill_names:
            skill = await self.loader.load_skill_from_md(skill_name)
            if skill:
                await self.registry.register_skill(skill)
                loaded_count += 1
                print(f"  ✅ {skill_name} 스킬 로드 완료")
            else:
                print(f"  ⚠️ {skill_name} 스킬 로드 실패 (SKILLS.md 형식 확인 필요)")

        print(f"\n✨ 총 {len(self.registry.skills)}개 스킬이 등록되었습니다.")

        # 등록된 스킬 목록 출력
        self.registry.print_skill_list()

        # LangGraph 워크플로우 빌드
        self.graph = self._build_graph()

        return self

    async def _register_builtin_skills(self):
        """Built-in 스킬 등록"""
        from skills.builtin import FileReadSkill, TerminalSkill, ListDirectorySkill

        builtin_skills = [
            FileReadSkill(),
            TerminalSkill(),
            ListDirectorySkill(),
        ]

        for skill in builtin_skills:
            await self.registry.register_skill(skill)
            print(f"  🔧 Built-in 스킬 등록: {skill.name}")

    def _build_graph(self):
        """LangGraph 워크플로우 구성"""

        # 상태 그래프 생성
        workflow = StateGraph(SkillState)

        # 노드 정의
        workflow.add_node("parse_intent", self._parse_intent)
        workflow.add_node("execute_skills", self._execute_skills)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)

        # 엣지 정의 (조건부 라우팅)
        workflow.set_entry_point("parse_intent")

        workflow.add_conditional_edges(
            "parse_intent",
            self._should_execute_skills,
            {
                "execute": "execute_skills",
                "direct_response": "generate_response",
                "error": "handle_error"
            }
        )

        workflow.add_edge("execute_skills", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _build_tools_for_gemini(self):
        """Gemini Function Calling을 위한 tools 구성"""
        from google.genai import types

        function_declarations = []
        for skill in self.registry.skills.values():
            schema = skill.get_schema()
            fd = types.FunctionDeclaration(
                name=schema["name"],
                description=schema["description"],
                parameters=schema["parameters"],
            )
            function_declarations.append(fd)

        if not function_declarations:
            return None

        return [types.Tool(function_declarations=function_declarations)]

    async def _parse_intent(self, state: SkillState) -> SkillState:
        """Gemini를 사용해 의도 파악 및 스킬 호출 결정"""

        # Function Calling을 위한 tools 구성
        tools = self._build_tools_for_gemini()

        try:
            from google.genai import types

            config_kwargs = {}
            if tools:
                config_kwargs["tools"] = tools

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=state['messages'][-1]['content'],
                config=types.GenerateContentConfig(**config_kwargs)
            )

            # Function Call 파싱
            has_function_call = (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
                and any(
                    hasattr(part, 'function_call') and part.function_call
                    for part in response.candidates[0].content.parts
                )
            )

            if has_function_call:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        state['skill_calls'].append({
                            'name': fc.name,
                            'args': dict(fc.args) if fc.args else {}
                        })
                state['context']['needs_skill_execution'] = True
            else:
                state['context']['direct_response'] = response.text or ""
                state['context']['needs_skill_execution'] = False

        except Exception as e:
            print(f"Gemini API 호출 오류: {e}")
            state['context']['direct_response'] = f"죄송합니다. API 호출 중 오류가 발생했습니다: {e}"
            state['context']['needs_skill_execution'] = False

        return state

    async def _execute_skills(self, state: SkillState) -> SkillState:
        """스킬들을 병렬 또는 순차적으로 실행"""

        tasks = []
        for skill_call in state['skill_calls']:
            skill = self.registry.get_skill(skill_call['name'])
            if skill:
                tasks.append(skill.execute(**skill_call['args']))

        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 저장
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                state['skill_calls'][i]['result'] = f"Error: {str(result)}"
            else:
                state['skill_calls'][i]['result'] = result

        return state

    async def _generate_response(self, state: SkillState) -> SkillState:
        """스킬 실행 결과를 바탕으로 최종 응답 생성"""

        if 'direct_response' in state['context']:
            final_response = state['context']['direct_response']
        else:
            skill_results = "\n".join([
                f"스킬 '{call['name']}' 실행 결과:\n{call.get('result', '결과 없음')}"
                for call in state['skill_calls']
            ])

            prompt = f"""
            사용자 요청: {state['messages'][-1]['content']}

            실행된 스킬 결과:
            {skill_results}

            위 결과를 바탕으로 사용자에게 친절하게 응답해주세요.
            """

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            final_response = response.text

        state['messages'].append({
            'role': 'assistant',
            'content': final_response
        })

        return state

    async def _handle_error(self, state: SkillState) -> SkillState:
        """에러 처리"""
        error_msg = "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다."
        state['messages'].append({
            'role': 'assistant',
            'content': error_msg
        })
        return state

    def _should_execute_skills(self, state: SkillState) -> str:
        """조건부 라우팅 로직"""
        if 'error' in state:
            return "error"
        elif state['context'].get('needs_skill_execution', False):
            return "execute"
        else:
            return "direct_response"

    async def process_request(self, user_message: str) -> str:
        """사용자 요청 처리"""
        if not self.graph:
            await self.initialize()

        skill_list = self.registry.get_skill_list(detailed=True)

        initial_state: SkillState = {
            'messages': [
                {'role': 'user', 'content': user_message}
            ],
            'skills': {s['name']: self.registry.get_skill(s['name']) for s in skill_list},
            'skill_calls': [],
            'context': {
                'available_skills': skill_list
            }
        }

        final_state = await self.graph.ainvoke(initial_state)

        # 사용 횟수 업데이트
        for call in final_state['skill_calls']:
            if call['name'] in self.registry.skill_status:
                self.registry.skill_status[call['name']]['use_count'] += 1
                self.registry.skill_status[call['name']]['last_used'] = asyncio.get_event_loop().time()

        return final_state['messages'][-1]['content']

    async def reload_skills(self):
        """스킬 재로드 (개발 중 유용)"""
        print("🔄 스킬 재로드 중...")
        self.loader.skills.clear()
        self.registry.skills.clear()
        await self.initialize()
