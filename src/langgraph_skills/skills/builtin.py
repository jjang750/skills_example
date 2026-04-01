import os
import subprocess
from pathlib import Path
from typing import Dict, Any

from ..core.base import BaseSkill

class FileReadSkill(BaseSkill):
    """파일 읽기 스킬"""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="파일 내용을 읽습니다"
        )
    
    async def execute(self, file_path: str, **kwargs) -> str:
        """파일 읽기 실행"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"파일 읽기 오류: {str(e)}"
    
    def _get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "읽을 파일의 경로"
                }
            },
            "required": ["file_path"]
        }

class TerminalSkill(BaseSkill):
    """터미널 명령어 실행 스킬"""
    
    def __init__(self):
        super().__init__(
            name="run_terminal",
            description="터미널 명령어를 실행합니다"
        )
    
    async def execute(self, command: str, **kwargs) -> str:
        """터미널 명령어 실행"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\n에러: {result.stderr}"
            return output
        except subprocess.TimeoutExpired:
            return "명령어 실행 시간이 초과되었습니다."
        except Exception as e:
            return f"명령어 실행 오류: {str(e)}"
    
    def _get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "실행할 터미널 명령어"
                }
            },
            "required": ["command"]
        }

class ListDirectorySkill(BaseSkill):
    """디렉토리 목록 조회 스킬"""
    
    def __init__(self):
        super().__init__(
            name="list_directory",
            description="디렉토리의 파일과 폴더 목록을 보여줍니다"
        )
    
    async def execute(self, path: str = ".", **kwargs) -> str:
        """디렉토리 목록 조회"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return f"경로가 존재하지 않습니다: {path}"
            
            items = list(path_obj.iterdir())
            files = [f.name for f in items if f.is_file()]
            dirs = [d.name for d in items if d.is_dir()]
            
            result = f"📁 디렉토리: {path}\n"
            if dirs:
                result += "\n📂 폴더:\n  " + "\n  ".join(dirs)
            if files:
                result += "\n\n📄 파일:\n  " + "\n  ".join(files)
            
            return result
        except Exception as e:
            return f"디렉토리 조회 오류: {str(e)}"
    
    def _get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "조회할 디렉토리 경로 (기본값: 현재 디렉토리)"
                }
            },
            "required": []
        }