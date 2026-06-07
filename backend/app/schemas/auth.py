from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., example="minh@example.com")
    password: str = Field(..., example="password123")
    display_name: str = Field(..., example="Minh Nguyen")
    age_group: str = Field(default="adult", example="adult")
    debate_level: str = Field(default="intermediate", example="intermediate")
    language: str = Field(default="vi", example="vi")


class LoginRequest(BaseModel):
    email: str = Field(..., example="minh@example.com")
    password: str = Field(..., example="password123")


class AuthUserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    age_group: str | None = None
    debate_level: str | None = None
    language: str


class AuthTokenResponse(BaseModel):
    token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: AuthUserResponse
    message: str | None = None


class LogoutResponse(BaseModel):
    status: str
