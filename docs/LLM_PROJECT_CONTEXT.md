# AI Debate Trainer - Project Context for LLMs

Last reviewed from live repository code: 2026-05-27.

This file is meant to be pasted into another LLM session so the model can understand the project quickly before editing, reviewing, or answering questions about it. Treat this as a project map, not as a replacement for reading the current files.

## 1. One-sentence summary

AI Debate Trainer is a Vietnamese debate-practice desktop web app. Users choose or enter a debate topic, submit arguments by text or voice, receive an AI rebuttal, get CER scores for Claim, Evidence, and Reasoning, and can track debate progress across sessions.

## 2. Product goals

- Help Vietnamese users practice structured debate and argument quality.
- Act as both an opponent and a coach: the AI should rebut the user's argument and give actionable feedback.
- Score arguments with a CER rubric:
  - Claim: clarity and relevance of the main position.
  - Evidence: concrete source, data, examples, or factual support.
  - Reasoning: causal/logical connection and fallacy control.
- Support beginner-friendly UX with topic bank, onboarding/tutorial/demo, progress tracking, and voice input.
- Run locally as a Windows desktop app using a local FastAPI backend plus a static HTML frontend inside pywebview.

## 3. Current architecture

```text
desktop_app.py
  starts FastAPI backend at http://127.0.0.1:8000
  serves frontend/ as a local static HTTP server on a random port
  opens frontend/web.html in pywebview, or browser fallback

frontend/web.html
  single-file app with CSS and JavaScript
  calls backend REST APIs
  uses MediaRecorder for voice input
  plays backend-generated TTS audio blobs

backend/app/main.py
  FastAPI app
  routers:
    /api/v1/auth
    /api/v1/debate
    /api/v1/speech

backend/app/services/
  business logic, Groq client, scoring parser, Firestore storage, speech stack

Firebase Firestore
  cloud database for users, auth sessions, debate sessions, turns, scores, feedback, flags

External AI/speech providers
  Groq chat completions for debate analysis and transcript cleanup
  ElevenLabs STT as default primary speech-to-text provider
  Groq Whisper STT as fallback
  Microsoft Edge TTS for text-to-speech
```

## 4. Important entrypoints and files

- `desktop_app.py`: Windows desktop launcher. Configures runtime, starts backend, serves `frontend/`, opens pywebview window.
- `scripts/run_windows_app.ps1`: canonical dev launcher from repo root.
- `backend/app/main.py`: FastAPI app, health endpoint, router registration, CORS, startup `init_db()`.
- `backend/app/core/config.py`: environment-backed settings.
- `frontend/web.html`: main UI, app state, API calls, auth flow, debate arena, topic bank, practice modes, voice UI.
- `backend/app/api/auth.py`: register/login/me/logout endpoints.
- `backend/app/api/debate.py`: topic/session/turn/summary/progress/practice-prompt endpoints.
- `backend/app/api/speech.py`: STT/TTS endpoints and aliases.
- `backend/app/services/session_store.py`: authoritative storage layer. It uses Firebase Firestore now.
- `backend/app/services/ai_service.py`: orchestrates validation, prompt building, Groq call, CER parsing, error handling.
- `backend/app/services/prompt_builder.py`: builds Vietnamese system/user prompts and mode-specific scoring prompts.
- `backend/app/services/cer_scorer.py`: parses JSON/marker LLM output, validates arguments, normalizes CER to 0-100, applies evidence gate.
- `backend/app/services/speech_service.py`: validates audio, selects STT provider, runs transcript cleanup, generates Edge TTS.
- `backend/app/data/topics.py`: seed topic bank and filtering/recommendation logic.
- `tests/`: unit tests and frontend string-contract tests.

## 5. How to run

From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

The script:

- creates/reuses `.venv`;
- installs `backend/requirements.txt` and `requirements-desktop.txt`;
- runs `desktop_app.py`;
- starts backend on `127.0.0.1:8000`;
- serves the frontend locally;
- opens the app window.

Optional backend-only run:

```powershell
.venv\Scripts\activate
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger is at `http://127.0.0.1:8000/docs` when the backend is running.

## 6. Environment configuration

Use `backend/.env_example` as the template. Do not expose real `backend/.env` contents or commit secrets.

Important settings:

```env
GROQ_API_KEY=...
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT_SECONDS=90

VOICE_STT_PROVIDER=elevenlabs
VOICE_STT_FALLBACK=groq
ELEVENLABS_API_KEY=...
ELEVENLABS_STT_BASE_URL=https://api.elevenlabs.io/v1/speech-to-text
ELEVENLABS_STT_MODEL=scribe_v2

GROQ_STT_BASE_URL=https://api.groq.com/openai/v1/audio/transcriptions
GROQ_STT_MODEL=whisper-large-v3

EDGE_TTS_VOICE=vi-VN-NamMinhNeural
EDGE_TTS_RATE=+10%

FIREBASE_CREDENTIALS_JSON=...
FIREBASE_CREDENTIALS_PATH=
FIREBASE_PROJECT_ID=...
```

`DATABASE_PATH` still exists in config and old artifacts like `backend/ai_debate_trainer.db` exist, but the active storage implementation is Firestore in `session_store.py`.

## 7. Backend API surface

Base URL: `http://localhost:8000` or `http://127.0.0.1:8000`.

Health:

- `GET /health` -> `{"status":"ok"}`

Auth:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

Debate topics:

- `GET /api/v1/debate/topics`
- `GET /api/v1/debate/topics/recommended`
- `GET /api/v1/debate/topic-categories`

Debate sessions:

- `POST /api/v1/debate/session`
- `POST /api/v1/debate/turn`
- `GET /api/v1/debate/session/{session_id}`
- `POST /api/v1/debate/session/{session_id}/end`
- `GET /api/v1/debate/session/{session_id}/summary`
- `GET /api/v1/debate/progress/overview`
- `POST /api/v1/debate/practice-prompt`

Speech:

- `POST /api/v1/speech/stt`
- `POST /api/v1/speech/transcribe`
- `POST /api/v1/speech/tts`
- `POST /api/v1/speech/synthesize`

## 8. Auth model

`auth_service.py` handles:

- email normalization;
- basic email/password validation;
- PBKDF2-SHA256 password hashing;
- bearer token auth sessions;
- 7-day session expiry.

There are two user modes:

- Authenticated users: requests include `Authorization: Bearer <token>`.
- Guest/demo mode: debate endpoints can fall back to `demo-user` through `get_debate_user()` if no bearer token is supplied.

The stricter `/auth/me` route requires authentication.

## 9. Firestore storage model

`session_store.py` is the authoritative storage file. It initializes Firebase from `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_PATH`, then seeds a demo user.

Collections used:

- `users`: one document per user.
- `auth_sessions`: one document per auth token/session.
- `debate_sessions`: one document per debate session.
- `debate_turns`: one document per user turn.
- `cer_scores`: one document per score attached to a turn.
- `feedback_items`: strengths/weaknesses/suggestions attached to a turn.
- `content_flags`: AI error/invalid/content flags attached to a turn.

Required Firestore composite indexes listed in `session_store.py`:

- `debate_turns`: `session_id ASC`, `turn_number ASC`.
- `feedback_items`: `turn_id ASC`, `created_at ASC`.
- `debate_sessions`: `user_id ASC`, `created_at DESC`.

Storage flow:

1. `create_session()` writes a `debate_sessions` document.
2. `save_debate_turn()` uses a batch write for `debate_turns`, `cer_scores`, `feedback_items`, and `content_flags`.
3. After saving a turn, it updates parent session `turn_count`, `status`, `average_score`, `updated_at`, and sometimes `completed_at`.
4. `get_session_turns()` joins turn documents with score and feedback documents by querying related collections.
5. `get_session_summary()` aggregates valid turns only, excluding `error` and `invalid`.
6. `get_progress_overview()` aggregates sessions and scores for the current user.

## 10. Debate turn flow

Primary route: `POST /api/v1/debate/turn` in `backend/app/api/debate.py`.

High-level flow:

1. Resolve current user via bearer token or demo user.
2. Load the session and enforce user ownership.
3. Reject empty arguments and completed sessions.
4. Fetch last 3 turns as bounded conversation history.
5. Call `ai_service.generate_debate_analysis(...)`.
6. Normalize returned CER to 0-100.
7. Persist the turn, CER score, feedback, and flags.
8. Return `DebateTurnResponseV2`.

Current response fields include:

```json
{
  "session_id": "...",
  "user_argument": "...",
  "ai_rebuttal": "...",
  "is_valid": true,
  "cer": {
    "claim": 70.0,
    "evidence": 40.0,
    "reasoning": 60.0,
    "overall": 57.0,
    "total": 57.0
  },
  "cer_breakdown": {
    "claim": {"clarity": 0, "relevance": 0, "specificity": 0},
    "evidence": {"presence": 0, "specificity": 0, "relevance": 0},
    "reasoning": {"logical_connection": 0, "causal_explanation": 0, "fallacy_control": 0}
  },
  "feedback": {
    "strengths": [],
    "weaknesses": [],
    "suggestions": []
  },
  "turn_number": 1,
  "max_turns": 5,
  "status": "active"
}
```

Do not casually change this contract: the single-file frontend depends on these names.

## 11. AI provider and error behavior

Groq is the chat LLM provider. `groq_client.py` owns the direct `httpx.post()` call. `ai_service.py` intentionally delegates provider HTTP work to `groq_client.py`.

Important behavior:

- Missing `GROQ_API_KEY` returns a friendly error result, not a crash.
- HTTP/network/Groq failures produce `status="error"`, zero/default CER, and friendly user-facing text.
- The app should not silently use a fake/sample rebuttal when Groq fails.
- Error sanitizers mask API keys and bearer tokens.

`scripts/check_groq_provider.py` is the manual check script. It prints provider/model/status/text/error and does not print the API key.

## 12. Prompting and CER scoring

Active scoring path:

```text
api/debate.py
  -> ai_service.generate_debate_analysis()
  -> validate_user_argument()
  -> prompt_builder.build_cer_messages()
  -> groq_client.call_groq()
  -> cer_scorer.parse_cer_rubric_output()
  -> normalize_cer_to_100()
  -> session_store.save_debate_turn()
```

Prompt design:

- Prompts are written in Vietnamese to lock output language.
- The model is asked to return a single JSON object, not markdown.
- Rebuttal should be 4-6 Vietnamese sentences and directly reference the user's argument.
- Prompt includes explicit evidence detection and anti-score-clustering rules.
- It supports turn history so rebuttals evolve instead of repeating.

CER scale:

- Active CER scores are 0-100.
- `overall = round(claim * 0.3 + evidence * 0.3 + reasoning * 0.4)`.
- `normalize_cer_to_100()` also accepts legacy 0-1 values and converts them.

Evidence gate:

- In `parse_cer_rubric_output()`, if model output has `evidence_quote == "NONE"` or `checklist.has_real_evidence == false`, backend forces evidence score and evidence breakdown to `0.0`.
- This is backend enforcement, not just prompt wording.

Argument validation:

- `validate_user_argument()` rejects empty, too short, spam/repetition, symbol-only, and some toxic inputs.
- Invalid arguments return `status="invalid"`, `is_valid=false`, zero CER, and do not need an AI call.

Compatibility:

- `parse_cer_rubric_output()` can parse the current JSON format.
- It also has fallback support for older marker format with `[REBUTTAL]`, `[CER]`, and `[FEEDBACK]`.
- `output_parser.py` is a legacy marker-format parser used by older tests/contracts.

Important caveat:

- `backend/app/services/cer_detector.py` exists and can strictly detect Claim/Evidence/Reasoning components, but the active `ai_service.generate_debate_analysis()` path currently does not call `detect_cer_components()`. Do not claim strict missing-component detection is live unless you wire it into the active path and test it.

## 13. Practice modes

The app has free debate plus single-skill practice modes.

Backend mode aliases live in `prompt_builder.py`:

- `free_debate`
- `claim_writing` / `claim_practice`
- `find_evidence` / `evidence_practice`
- `quick_rebuttal`
- `full_argument` / `argument_builder`

Single-skill modes in `api/debate.py`:

- `claim_writing`
- `find_evidence`
- `quick_rebuttal`
- aliases `claim_practice`, `evidence_practice`

Practice prompt flow:

1. Frontend calls `POST /api/v1/debate/practice-prompt`.
2. `ai_service.generate_practice_prompt()` asks Groq for a small JSON prompt.
3. If Groq fails or output is malformed, backend returns a local fallback prompt.
4. Frontend stores `practice_mode`, `practice_prompt`, and `practice_round`.
5. User answer is sent through `/api/v1/debate/turn` with those practice fields.

Completion behavior:

- Full/free debate turns count toward session completion.
- Single-skill practice can save evaluations without immediately completing the session in the same way.

## 14. Topic bank

`backend/app/data/topics.py` contains local seed topics and category metadata.

Current capabilities:

- At least 50 seed topics.
- 10 categories.
- Filtering by category, difficulty, search query, tag, and limit.
- Recommended topics are currently based on local seed data and difficulty/category preference.
- `user_id` is accepted by the recommended endpoint for future history-aware ranking, but current implementation does not use Firestore history for recommendation.

Frontend topic bank:

- Loads `/api/v1/debate/topics?limit=100` and `/api/v1/debate/topic-categories`.
- Has local fallback topic data if backend topic bank fails.
- Supports recommended tab, category chips, search, difficulty filter, topic cards, and load more.
- If user enters a custom topic, that overrides selected bank topic metadata.

## 15. Speech stack

Frontend voice input:

- Uses browser `MediaRecorder`.
- Does not use `SpeechRecognition`, `webkitSpeechRecognition`, or `window.speechSynthesis`.
- Records audio chunks, saves a local object URL for source audio state, sends blob to backend STT, then fills the text argument box.
- User can edit transcript before submitting the debate turn.

Backend STT:

- Endpoints: `/api/v1/speech/stt` and `/api/v1/speech/transcribe`.
- Accepts raw audio blob in supported MIME types: webm, ogg, wav, flac, mp3, mp4/m4a.
- Enforces max audio bytes from `SPEECH_MAX_AUDIO_BYTES`.
- Default primary provider is ElevenLabs STT (`VOICE_STT_PROVIDER=elevenlabs`).
- Fallback can be Groq Whisper (`VOICE_STT_FALLBACK=groq`).
- Groq STT uses `whisper-large-v3`.
- STT can receive session context so transcription prompt includes topic, stance, and difficulty.

Transcript cleanup:

- After STT, `cleanup_voice_transcript()` calls Groq chat to clean Vietnamese transcript text using session context.
- It should not add new claims/evidence or change the user's stance.

Backend TTS:

- Endpoints: `/api/v1/speech/tts` and `/api/v1/speech/synthesize`.
- Always uses Edge TTS through `edge-tts`.
- Returns an `audio/mpeg` response body plus `X-Speech-Provider` and `X-Speech-Model` headers.
- Sanitizes markdown-ish text before TTS.
- Enforces max text length from `SPEECH_TTS_MAX_CHARS`.

## 16. Frontend structure and UX

`frontend/web.html` is a large single-file application. It includes:

- auth landing/signup/login/preferences;
- guest mode;
- post-login navigation hub;
- session setup;
- topic bank;
- debate arena;
- CER score visualization;
- feedback panels;
- summary view;
- progress view;
- voice draft toolbar;
- rebuttal audio playback;
- practice round UI;
- Lumi mascot companion;
- onboarding/tutorial/demo assets.

Important frontend constants/functions:

- `BACKEND_API_URL = "http://localhost:8000"`
- `DEFAULT_THEME = "blue-pastel"`
- global `state` object around the app state.
- `enterApp()`
- `loadDebateTopics()`
- `apiRequest()`
- `submitArgument()`
- `transcribeSpeechBlob()`

Theme:

- Default body theme is `blue-pastel`.
- There is also dark theme styling.

Assets:

- Main frontend assets include `frontend/assets/login-dragon-battle-bg.png`, `frontend/assets/lumi-paper-dragon-cutout.png`, and mascot/tutorial assets under `frontend/assets/mascot/`.

Frontend contract tests are string-based. Renaming labels/functions/classes may break tests even if runtime behavior still works.

## 17. Tests

Usual command:

```powershell
.venv\Scripts\activate
python -m unittest discover -s tests
```

Focused test examples:

```powershell
python -m unittest tests.test_cer_scorer
python -m unittest tests.test_prompt_builder
python -m unittest tests.test_speech_backend
python -m unittest tests.test_debate_topics
python -m unittest tests.test_frontend_auth_binding
```

Test coverage areas:

- health/auth/session/debate turn/progress contracts;
- topic bank filters and category counts;
- Groq-only behavior and friendly error handling;
- CER parser, normalization, invalid argument behavior;
- prompt-builder requirements;
- speech backend STT/TTS contract;
- frontend auth/topic/practice/voice/theme/Lumi/onboarding string contracts;
- project structure expectations.

Known test drift to verify before trusting the whole suite:

- `tests/test_week6_backend.py` still contains SQLite-era helpers such as `sqlite3` row counts, while `session_store.py` now uses Firestore. It may need updating or dependency overrides/mocks for Firestore.
- `tests/test_project_structure.py` may contain stale expectations about exact import strings in `ai_service.py`.

For small changes, prefer running the focused tests closest to the touched area first.

## 18. Development constraints and change guidance

When another LLM edits this repo:

- Read the current file before editing; the worktree may already have user changes.
- Do not read, print, or commit real `backend/.env` secrets.
- Preserve existing API response shapes unless explicitly changing frontend and tests together.
- Keep backend business rules enforced in Python when correctness matters; do not rely only on prompt wording.
- For provider errors, return clear error status and friendly text; do not invent demo AI output.
- If editing scoring, update both parser/backend enforcement and relevant tests.
- If editing speech, preserve the current contract: browser `MediaRecorder`, backend STT, Edge TTS audio blob, no browser Web Speech API.
- If editing frontend strings/classes/functions, inspect `tests/test_frontend_auth_binding.py` because many assertions are exact string checks.
- If editing storage, treat `session_store.py` as the storage authority and account for Firestore indexes and credentials.
- If editing topic bank, update `backend/app/data/topics.py`, endpoint contracts, and frontend fallback if needed.

## 19. Quick mental model of core flows

Session setup:

```text
frontend selects topic/profile/settings
  -> POST /api/v1/debate/session
  -> normalize_session_payload()
  -> validate_debate_topic()
  -> create_session()
  -> Firestore debate_sessions
```

Text debate turn:

```text
frontend submitArgument()
  -> POST /api/v1/debate/turn
  -> get_session()
  -> get_session_turns(last 3)
  -> generate_debate_analysis()
  -> Groq
  -> parse_cer_rubric_output()
  -> save_debate_turn()
  -> frontend renders rebuttal, CER, feedback, TTS controls
```

Voice draft:

```text
frontend MediaRecorder
  -> POST /api/v1/speech/stt?language=vi&session_id=...
  -> transcribe_audio()
  -> ElevenLabs STT or Groq fallback
  -> cleanup_voice_transcript() through Groq
  -> frontend fills editable text input
```

Rebuttal audio:

```text
frontend getRebuttalSpeechUrl()
  -> POST /api/v1/speech/tts
  -> synthesize_text()
  -> Edge TTS
  -> frontend plays returned MP3 blob
```

Progress:

```text
frontend progress view
  -> GET /api/v1/debate/progress/overview
  -> query current user's sessions and valid turns
  -> aggregate claim/evidence/reasoning/overall, streak, recent topics
```

## 20. Current repo-state notes

At the time this context file was created, the working tree already had uncommitted modifications in backend, frontend, and tests. This file was added as new documentation only. If you are an LLM continuing work later, run `git status --short --branch` first and do not revert unrelated user changes.

The README and some docs may display mojibake in a PowerShell terminal depending on encoding/output settings, but the frontend and tests contain Vietnamese text and should be read/written with UTF-8.
