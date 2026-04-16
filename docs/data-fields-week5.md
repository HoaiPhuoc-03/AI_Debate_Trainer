# Data Fields - Week 5

## Session fields
- session_id
- topic
- stance
- difficulty
- input_mode

## Debate turn fields
- session_id
- user_argument
- ai_rebuttal
- status

## Suggested structure

### DebateSession
{
  "session_id": "uuid...",
  "topic": "...",
  "stance": "...",
  "difficulty": "...",
  "input_mode": "text"
}

### DebateTurn
{
  "session_id": "uuid...",
  "user_argument": "...",
  "ai_rebuttal": "...",
  "status": "success"
}