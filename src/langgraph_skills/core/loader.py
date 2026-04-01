import os
import glob
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import importlib.util
import inspect
import json

from .base import BaseSkill

class FileBasedSkillLoader:
    """파일 시스템에서 스킬을 동적으로 로드하는 로더"""
    
    def __init__(self, skills_root: str = "./skills"):
        self.skills_root = Path(skills_root)
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_metadata: Dict[str, Dict] = {}
        
    async def discover_skills(self) -> List[str]:
        """skills 디렉토리에서 모든 스킬 폴더를 찾음"""
        if not self.skills_root.exists():
            self.skills_root.mkdir(parents=True)
            return []
        
        skip_dirs = {'__pycache__', '.git', '.venv', 'venv'}
        skill_dirs = [d for d in self.skills_root.iterdir() if d.is_dir() and d.name not in skip_dirs]
        return [d.name for d in skill_dirs]
    
    async def load_skill_from_md(self, skill_name: str) -> Optional[BaseSkill]:
        """특정 스킬의 SKILLS.md 파일을 읽어 스킬 인스턴스 생성"""
        skill_path = self.skills_root / skill_name
        md_file = skill_path / "SKILLS.md"
        
        if not md_file.exists():
            print(f"경고: {skill_name} 스킬에 SKILLS.md 파일이 없습니다.")
            return None
        
        # SKILLS.md 파일 읽기
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 메타데이터와 구현 파싱
        metadata = self._parse_skill_metadata(content, skill_name)
        
        # 스킬 인스턴스 생성
        skill = await self._create_skill_instance(metadata, skill_path)
        
        if skill:
            self.skill_metadata[skill_name] = metadata
            self.skills[skill_name] = skill
            
        return skill
    
    def _parse_skill_metadata(self, content: str, skill_name: str) -> Dict:
        """SKILLS.md 파일에서 메타데이터 파싱"""
        metadata = {
            'name': skill_name,
            'description': '',
            'version': '1.0.0',
            'author': '',
            'dependencies': [],
            'parameters': {},
            'implementation': '',
            'examples': []
        }
        
        lines = content.split('\n')
        current_section = None
        in_metadata = False
        
        for line in lines:
            # YAML 형식의 메타데이터 파싱 (--- 로 구분된 부분)
            if line.strip() == '---':
                in_metadata = not in_metadata
                continue
            
            if in_metadata:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key in metadata:
                        if key == 'dependencies':
                            metadata[key] = [d.strip() for d in value.split(',')]
                        else:
                            metadata[key] = value
                continue
            
            # 구현 코드 섹션 (```python 으로 둘러싸인 부분)
            if line.strip().startswith('```python'):
                current_section = 'implementation'
                continue
            elif current_section == 'implementation' and line.strip().startswith('```'):
                current_section = None
            elif current_section == 'implementation':
                metadata['implementation'] += line + '\n'
            
            # 예제 섹션
            elif line.strip().startswith('## Example') or line.strip().startswith('### Example'):
                current_section = 'example'
                continue
            elif current_section == 'example' and line.strip() and not line.strip().startswith('##'):
                if '```' not in line:
                    metadata['examples'].append(line.strip())
        
        return metadata
    
    async def _create_skill_instance(self, metadata: Dict, skill_path: Path) -> Optional[BaseSkill]:
        """메타데이터와 구현 코드로 스킬 인스턴스 생성"""
        try:
            # 구현 코드가 있으면 동적으로 실행
            if metadata['implementation']:
                # 임시 모듈 생성
                module_name = f"dynamic_skill_{metadata['name']}"
                spec = importlib.util.spec_from_loader(module_name, loader=None)
                module = importlib.util.module_from_spec(spec)
                
                # BaseSkill을 네임스페이스에 추가
                module.__dict__['BaseSkill'] = BaseSkill
                
                # 구현 코드 실행
                exec(metadata['implementation'], module.__dict__)
                
                # 모듈에서 Skill 클래스 찾기
                skill_class = None
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if inspect.isclass(item) and issubclass(item, BaseSkill) and item != BaseSkill:
                        skill_class = item
                        break
                
                if skill_class:
                    # 스킬 인스턴스 생성
                    skill_instance = skill_class()
                    
                    # 추가 파일 리소스 로드
                    await self._load_skill_resources(skill_instance, skill_path)
                    
                    return skill_instance
            
            return None
            
        except Exception as e:
            print(f"스킬 생성 중 오류: {metadata['name']} - {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _load_skill_resources(self, skill: BaseSkill, skill_path: Path):
        """스킬 관련 추가 리소스 로드 (설정 파일, 데이터 등)"""
        # config.json 로드
        config_file = skill_path / "config.json"
        if config_file.exists():
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if hasattr(skill, 'load_config'):
                    await skill.load_config(config)
        
        # data 디렉토리 로드
        data_dir = skill_path / "data"
        if data_dir.exists() and hasattr(skill, 'load_data'):
            await skill.load_data(data_dir)