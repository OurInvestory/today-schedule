from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any, Dict, List, Literal, Optional, Union

# 1) Missing field item
class MissingField(BaseModel):
    field: str
    reason: str = ""
    question: str = ""
    choices: List[str] = Field(default_factory=list)

# 2) Action item
class Action(BaseModel):
    op: Literal["CREATE", "UPDATE", "DELETE"]
    target: str = "SCHEDULE"
    schedule_id: Optional[str] = Field(None, alias="scheduleId") # JSON: scheduleId
    payload: Dict[str, Any] = Field(default_factory=dict)

# 3) Parsed payload
class AIChatParsed(BaseModel):
    intent: Literal["SCHEDULE_MUTATION", "SCHEDULE_QUERY", "CLARIFY"]
    type: Literal["EVENT", "TASK", "UNKNOWN"] = "UNKNOWN"
    confidence: float = 0.0
    actions: List[Action] = Field(default_factory=list)
    missingFields: List[MissingField] = Field(default_factory=list)
    reasoning: Optional[str] = None
    preserved_info: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('missingFields', mode='before')
    @classmethod
    def convert_missing_fields(cls, v):
        """문자열 리스트를 MissingField 객체 리스트로 변환"""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                # 문자열인 경우 MissingField로 변환
                result.append({
                    "field": item,
                    "reason": f"{item} 정보가 필요합니다.",
                    "question": f"{item}을(를) 알려주세요.",
                    "choices": []
                })
            elif isinstance(item, dict):
                result.append(item)
            else:
                result.append(item)
        return result

# 4) Request 
class ChatRequest(BaseModel):
    text: str
    base_date: Optional[str] = Field(None, alias="baseDate") 
    timezone: str = "Asia/Seoul"
    selected_schedule_id: Optional[str] = Field(None, alias="selectedScheduleId")
    user_context: Optional[Dict[str, Any]] = Field(None, alias="userContext")
    model_config = ConfigDict(populate_by_name=True)

# 5) Lecture 형식 (Vision API용)
class LectureItem(BaseModel):
    title: str
    start_time: str = Field(alias="startTime")  # "09:00"
    end_time: str = Field(alias="endTime")      # "10:30"
    week: int                                    # 단일 값 (0=월 ~ 6=일)
    
    model_config = ConfigDict(populate_by_name=True, by_alias=True)

# 6) Response Wrapper
class ChatResponseData(BaseModel):
    parsed_result: AIChatParsed = Field(alias="parsedResult")
    assistant_message: Optional[str] = Field(None, alias="assistantMessage")
    lectures: Optional[List[LectureItem]] = None  # 시간표 분석 시 Lecture 형식으로 반환

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

class APIResponse(BaseModel):
    status: int = 200
    message: str
    data: Optional[ChatResponseData] = None
