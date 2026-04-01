from typing import Dict, List, Optional, Any
import asyncio
from .base import BaseSkill

class SkillRegistry:
    """스킬 등록 및 관리 시스템"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_status: Dict[str, Dict] = {}
        
    async def register_skill(self, skill: BaseSkill) -> bool:
        """스킬 등록"""
        try:
            self.skills[skill.name] = skill
            self.skill_status[skill.name] = {
                'status': 'registered',
                'registered_at': asyncio.get_event_loop().time(),
                'last_used': None,
                'use_count': 0
            }
            return True
        except Exception as e:
            print(f"스킬 등록 실패 {skill.name}: {e}")
            return False
    
    def get_skill_list(self, detailed: bool = False) -> List[Dict]:
        """등록된 스킬 목록 반환"""
        if detailed:
            return [
                {
                    'name': name,
                    'description': skill.description,
                    'status': self.skill_status[name]['status'],
                    'use_count': self.skill_status[name]['use_count']
                }
                for name, skill in self.skills.items()
            ]
        else:
            return [{'name': name} for name in self.skills.keys()]
    
    def print_skill_list(self):
        """스킬 목록을 보기 좋게 출력"""
        if not self.skills:
            print("📦 등록된 스킬이 없습니다.")
            return
        
        print("\n" + "="*50)
        print("📋 등록된 스킬 목록")
        print("="*50)
        
        for i, (name, skill) in enumerate(self.skills.items(), 1):
            status = self.skill_status[name]
            print(f"\n{i}. 🛠️  {name}")
            print(f"   📝 설명: {skill.description}")
            print(f"   📊 사용 횟수: {status['use_count']}회")
            print(f"   ✅ 상태: {status['status']}")
        
        print("\n" + "="*50)
        print(f"총 {len(self.skills)}개 스킬 등록됨")
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """이름으로 스킬 조회"""
        return self.skills.get(name)
    
    async def unregister_skill(self, name: str) -> bool:
        """스킬 등록 해제"""
        if name in self.skills:
            del self.skills[name]
            del self.skill_status[name]
            return True
        return False