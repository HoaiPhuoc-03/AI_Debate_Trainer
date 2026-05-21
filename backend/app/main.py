from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.debate import router as debate_router
from app.api.speech import router as speech_router
from app.services.session_store import init_db

app = FastAPI(
    title="AI Debate Trainer API",
    description="Backend MVP cho AI Debate Trainer",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    init_db()

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(debate_router, prefix="/api/v1/debate", tags=["Debate"])
app.include_router(speech_router, prefix="/api/v1/speech", tags=["Speech"])


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
