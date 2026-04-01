import logging
from datetime import datetime
from pathlib import Path

class SkillLogger:
    """스킬 실행 로깅 유틸리티"""
    
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 로거 설정
        self.logger = logging.getLogger('skill_system')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_file = self.log_dir / f"skills_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
    
    def log_skill_execution(self, skill_name: str, args: dict, result: any):
        """스킬 실행 로그 기록"""
        self.logger.info(f"스킬 실행: {skill_name}, 인자: {args}, 결과: {str(result)[:200]}")
    
    def log_error(self, skill_name: str, error: Exception):
        """에러 로그 기록"""
        self.logger.error(f"스킬 오류: {skill_name}, 에러: {str(error)}")