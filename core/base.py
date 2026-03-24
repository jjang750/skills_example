from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

class BaseSkill(ABC):
    """파일 기반 로딩을 지원하는 BaseSkill"""
    
    def __init__(self, name: str = None, description: str = None):
        self.name = name or self.__class__.__name__.lower()
        self.description = description or self.__doc__ or "No description"
        self.resources = {}
        self.config = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """스킬 실행 로직"""
        pass
    
    def get_schema(self) -> Dict:
        """Gemini Function Calling을 위한 스키마"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters()
        }
    
    def _get_parameters(self) -> Dict:
        """파라미터 스키마 - 하위 클래스에서 오버라이드"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def load_config(self, config: Dict):
        """설정 로드"""
        self.config = config
    
    async def load_data(self, data_path: Path):
        """데이터 파일 로드"""
        for file_path in data_path.glob("*"):
            if file_path.suffix == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.resources[file_path.stem] = f.read()
            elif file_path.suffix == '.json':
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.resources[file_path.stem] = json.load(f)