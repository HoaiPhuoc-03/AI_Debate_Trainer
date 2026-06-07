from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.auth import router as auth_router
from app.api.debate import router as debate_router
from app.api.speech import router as speech_router
from app.services.session_store import init_db
from app.services.storage_errors import StorageError

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


@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError):
    _ = request
    return JSONResponse(status_code=503, content={"detail": str(exc)})

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
