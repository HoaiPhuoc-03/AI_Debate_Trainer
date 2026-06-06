from pydantic import BaseModel, Field


class DebateTopicResponse(BaseModel):
    id: str
    title: str
    category: str
    difficulty: str
    tags: list[str]
    description: str
    suggested_stance: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: str | None = None


class DebateTopicsResponse(BaseModel):
    status: str
    topics: list[DebateTopicResponse]
    total: int


class DebateTopicCategoryResponse(BaseModel):
    id: str
    name: str
    description: str
    count: int


class DebateTopicCategoriesResponse(BaseModel):
    status: str
    categories: list[DebateTopicCategoryResponse]


class StartSessionRequest(BaseModel):
    topic: str = Field(..., example="Should phones be allowed in class?")
    topic_id: str | None = Field(default=None, example="edu_ai_homework")
    topic_category: str | None = Field(default=None, example="Education")
    topic_tags: list[str] | None = Field(default=None, example=["AI", "learning"])
    custom_topic: str | None = Field(default=None, example="Should AI tutors replace homework?")
    stance: str = Field(..., example="support")
    difficulty: str | None = Field(default=None, example="intermediate")
    input_mode: str = Field(default="text", example="text")
    age_group: str = Field(default="adult", example="adult")
    debate_level: str = Field(default="intermediate", example="intermediate")
    coach_model: str = Field(default="socratic_v3", example="socratic_v3")
    language: str = Field(default="vi", example="vi")
    mode: str = Field(default="free_debate", example="free_debate")
    response_time: str | None = Field(default=None, example="90 sec")
    max_turns: int | None = Field(default=5, ge=1, le=10, example=5)
    display_name: str | None = Field(default=None, example="Minh Nguyen")


class StartSessionResponse(BaseModel):
    session_id: str
    topic: str
    topic_id: str | None = None
    topic_category: str | None = None
    topic_tags: list[str] | None = None
    custom_topic: str | None = None
    stance: str
    difficulty: str
    input_mode: str
    age_group: str
    debate_level: str
    coach_model: str
    language: str
    mode: str = "free_debate"
    response_time: str | None = None
    max_turns: int
    turn_count: int
    status: str


class DebateTurnRequest(BaseModel):
    session_id: str
    user_argument: str = Field(..., example="Phones can support quick research.")
    practice_mode: str | None = Field(default=None, example="evidence_practice")
    practice_topic: str | None = Field(default=None, example="Should online learning replace homework?")
    practice_prompt: str | None = Field(default=None, example="Online learning helps students manage their own time.")
    practice_round: int | None = Field(default=None, ge=1, example=1)


class PracticePromptRequest(BaseModel):
    session_id: str | None = Field(default=None, example="abc123")
    mode: str = Field(..., example="evidence_practice")
    topic: str = Field(..., example="Should online learning replace homework?")
    difficulty: str | None = Field(default=None, example="intermediate")
    category: str | None = Field(default=None, example="Giáo dục")
    round: int = Field(default=1, ge=1, example=1)
    previous_prompts: list[str] = Field(default_factory=list)
    previous_topics: list[str] = Field(default_factory=list)
    avoid_repeating: bool = True


class PracticePromptResponse(BaseModel):
    status: str
    mode: str
    prompt_type: str
    prompt: str
    instruction: str
    warning: str | None = None
    topic: str | None = None
    scenario: str | None = None
    claim: str | None = None
    weak_argument: str | None = None
    topic_id: str | None = None
    category: str | None = None
    difficulty: str | None = None
    fallacy_hint: str | None = None


class CERScoreResponse(BaseModel):
    claim: float
    evidence: float
    reasoning: float
    overall: float = 0.0
    total: float


class ClaimBreakdownResponse(BaseModel):
    clarity: float = 0.0
    relevance: float = 0.0
    specificity: float = 0.0


class EvidenceBreakdownResponse(BaseModel):
    presence: float = 0.0
    specificity: float = 0.0
    relevance: float = 0.0


class ReasoningBreakdownResponse(BaseModel):
    logical_connection: float = 0.0
    causal_explanation: float = 0.0
    fallacy_control: float = 0.0


class CERBreakdownResponse(BaseModel):
    claim: ClaimBreakdownResponse
    evidence: EvidenceBreakdownResponse
    reasoning: ReasoningBreakdownResponse


class FeedbackResponse(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


class DebateTurnResponse(BaseModel):
    session_id: str
    user_argument: str
    ai_rebuttal: str
    is_valid: bool | None = None
    cer: CERScoreResponse | None = None
    cer_breakdown: CERBreakdownResponse | None = None
    feedback: FeedbackResponse | None = None
    turn_number: int | None = None
    max_turns: int | None = None
    status: str


class DebateTurnResponseV2(DebateTurnResponse):
    cer: CERScoreResponse
    feedback: FeedbackResponse
    turn_number: int
    max_turns: int


class SessionInfoResponse(BaseModel):
    session_id: str
    topic: str
    topic_id: str | None = None
    topic_category: str | None = None
    topic_tags: list[str] | None = None
    custom_topic: str | None = None
    stance: str
    difficulty: str
    input_mode: str
    age_group: str
    debate_level: str
    coach_model: str
    language: str
    mode: str = "free_debate"
    response_time: str | None = None
    max_turns: int
    turn_count: int
    status: str


class SessionSummaryResponse(BaseModel):
    session_id: str
    topic: str
    stance: str
    difficulty: str
    turn_count: int
    max_turns: int
    status: str
    avg_claim_score: float
    avg_evidence_score: float
    avg_reasoning_score: float
    overall_score: float
    strength_summary: list[str]
    weakness_summary: list[str]
    next_steps: list[str]


class ProgressOverviewResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    avg_claim_score: float
    avg_evidence_score: float
    avg_reasoning_score: float
    overall_score: float
    streak_days: int
    recent_topics: list[dict]
    topic_category_breakdown: list[dict] = Field(default_factory=list)
    weekly_avg_score: float = 0.0
    monthly_avg_score: float = 0.0
    recent_trend_delta: float = 0.0
    best_topic: dict | None = None
    worst_topic: dict | None = None
    skill_strength: str
    skill_weakness: str
