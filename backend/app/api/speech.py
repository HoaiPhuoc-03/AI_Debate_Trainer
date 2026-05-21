from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.schemas.speech import SpeechSynthesisRequest, SpeechTranscriptionResponse
from app.services.auth_service import get_debate_user
from app.services.session_store import get_session
from app.services.speech_service import (
    EMPTY_AUDIO_ERROR,
    EMPTY_TTS_TEXT_ERROR,
    SUPPORTED_AUDIO_TYPES,
    TOO_LARGE_AUDIO_ERROR,
    TOO_LONG_TTS_TEXT_ERROR,
    UNSUPPORTED_AUDIO_ERROR,
    normalize_speech_language,
    synthesize_text,
    transcribe_audio,
)


router = APIRouter()


@router.post("/transcribe", response_model=SpeechTranscriptionResponse)
async def transcribe_speech(
    request: Request,
    language: str | None = None,
    session_id: str | None = None,
    current_user: dict = Depends(get_debate_user),
):
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail=UNSUPPORTED_AUDIO_ERROR)

    session_context = None
    if session_id:
        session_context = get_session(session_id, user_id=current_user["id"])

    audio_bytes = await request.body()
    result = transcribe_audio(
        audio_bytes,
        content_type=content_type,
        language=normalize_speech_language(language),
        session_context=session_context,
    )
    if not result["ok"]:
        error_code = result.get("error_code", "UNKNOWN_ERROR")
        # Client validation errors -> 400, Server/Network errors -> 502
        status_code = 400 if error_code in {"EMPTY_AUDIO", "AUDIO_TOO_LARGE", "UNSUPPORTED_FORMAT"} else 502
        raise HTTPException(status_code=status_code, detail=result["error"])

    return SpeechTranscriptionResponse(
        transcript=result["text"],
        raw_transcript=result.get("raw_text") or result["text"],
        provider=result["provider"],
        model=result["model"],
    )


@router.post("/synthesize")
async def synthesize_speech(
    payload: SpeechSynthesisRequest,
    current_user: dict = Depends(get_debate_user),
):
    # synthesize_text is async — must await
    result = await synthesize_text(payload.text)
    if not result["ok"]:
        error_code = result.get("error_code", "UNKNOWN_ERROR")
        # Client validation errors -> 400, Server/Network errors -> 502
        status_code = 400 if error_code in {"EMPTY_TEXT", "TEXT_TOO_LONG"} else 502
        raise HTTPException(status_code=status_code, detail=result["error"])

    return Response(
        content=result["audio"],
        media_type=result["content_type"],
        headers={
            "X-Speech-Provider": result["provider"],
            "X-Speech-Model": result["model"],
        },
    )
