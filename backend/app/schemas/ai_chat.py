from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Literal, Optional

# 1) Missing field item
class MissingField(BaseModel):
    field: str
    reason: str
    question: str
    choices: List[str] = Field(default_factory=list)

# 2) Action item
class Action(BaseModel):
    op: Literal["CREATE", "UPDATE", "DELETE"]
    target: Literal["SCHEDULE"] = "SCHEDULE"
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

# 4) Request (여기가 문제였음: alias 추가)
class ChatRequest(BaseModel):
    text: str
    # JSON에서는 "baseDate"로 들어오면 자동으로 base_date에 매핑됨
    base_date: Optional[str] = Field(None, alias="baseDate") 
    timezone: str = "Asia/Seoul"
    selected_schedule_id: Optional[str] = Field(None, alias="selectedScheduleId")
    user_context: Optional[Dict[str, Any]] = Field(None, alias="userContext")

    # Pydantic V2 설정 (camelCase 입력을 허용)
    model_config = ConfigDict(populate_by_name=True)

# 5) Response Wrapper
class ChatResponseData(BaseModel):
    parsed_result: AIChatParsed = Field(alias="parsedResult")
    assistant_message: Optional[str] = Field(None, alias="assistantMessage")

    model_config = ConfigDict(populate_by_name=True)

class APIResponse(BaseModel):
    status: int = 200
    message: str
    data: Optional[ChatResponseData] = None