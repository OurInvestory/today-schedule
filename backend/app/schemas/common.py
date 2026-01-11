from pydantic import BaseModel
from typing import Any


# 공통 응답 포맷
class ResponseDTO(BaseModel):
    status: int
    message: str
    data: Any