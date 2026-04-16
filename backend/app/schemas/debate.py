from pydantic import BaseModel, Field

class StartSessionRequest(BaseModel):
    topic: str = Field(..., example="Có nên cấm học sinh dùng điện thoại trong lớp học?")
    stance: str = Field(..., example="Ủng hộ")
    difficulty: str = Field(..., example="Trung bình")
    input_mode: str = Field(default="text", example="text")

class StartSessionResponse(BaseModel):
    session_id: str
    topic: str
    stance: str
    difficulty: str
    input_mode: str
    status: str

class DebateTurnRequest(BaseModel):
    session_id: str
    user_argument: str = Field(..., example="Em cho rằng nên cấm vì điện thoại làm mất tập trung trong giờ học.")

class DebateTurnResponse(BaseModel):
    session_id: str
    user_argument: str
    ai_rebuttal: str
    status: str
class SessionInfoResponse(BaseModel):
    session_id: str
    topic: str
    stance: str
    difficulty: str
    input_mode: str
    status: str