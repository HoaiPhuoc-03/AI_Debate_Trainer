from fastapi import FastAPI
from app.api.debate import router as debate_router

app = FastAPI(
    title="AI Debate Trainer API",
    description="Backend MVP cho AI Debate Trainer",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(debate_router, prefix="/api/v1/debate", tags=["Debate"])


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)