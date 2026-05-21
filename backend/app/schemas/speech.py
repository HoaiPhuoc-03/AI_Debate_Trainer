from pydantic import BaseModel, Field


class SpeechTranscriptionResponse(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=10000)
    raw_transcript: str | None = None
    provider: str
    model: str


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
