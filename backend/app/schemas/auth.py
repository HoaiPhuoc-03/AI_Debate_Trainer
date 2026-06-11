from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., examples=["minh@example.com"])
    password: str = Field(..., examples=["password123"])
    display_name: str = Field(..., examples=["Minh Nguyen"])
    age_group: str = Field(default="adult", examples=["adult"])
    debate_level: str = Field(default="intermediate", examples=["intermediate"])
    language: str = Field(default="vi", examples=["vi"])


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["minh@example.com"])
    password: str = Field(..., examples=["password123"])


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
