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

# 4) Request 
class ChatRequest(BaseModel):
    text: str
    base_date: Optional[str] = Field(None, alias="baseDate") 
    timezone: str = "Asia/Seoul"
    selected_schedule_id: Optional[str] = Field(None, alias="selectedScheduleId")
    user_context: Optional[Dict[str, Any]] = Field(None, alias="userContext")
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
