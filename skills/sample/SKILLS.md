---
name: weather_checker
description: 현재 날씨 정보를 제공합니다
version: 1.0.0
author: Sample
dependencies: requests
---

# Weather Checker Skill

현재 날씨를 확인하는 스킬입니다.

## Parameters

- `city`: 날씨를 확인할 도시 이름
- `country`: 국가 코드 (선택사항)

```python
from typing import Dict, Any

class WeatherCheckerSkill(BaseSkill):
    def __init__(self):
        super().__init__(
            name="weather_checker",
            description="현재 날씨 정보를 제공합니다"
        )

    async def execute(self, city: str, country: str = "KR", **kwargs) -> str:
        # 실제 구현시 날씨 API 호출
        # 여기서는 샘플 데이터 반환
        return f"{city}의 현재 날씨: 맑음, 22°C"

    def _get_parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "날씨를 확인할 도시 이름"
                },
                "country": {
                    "type": "string",
                    "description": "국가 코드 (예: KR, US, JP)"
                }
            },
            "required": ["city"]
        }
```

## Example

서울의 날씨를 알려줘
도쿄 날씨 어때?
