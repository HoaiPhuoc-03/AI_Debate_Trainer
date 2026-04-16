from uuid import uuid4

SESSION_DB = {}

def create_session(topic: str, stance: str, difficulty: str, input_mode: str):
    session_id = str(uuid4())

    session_data = {
        "session_id": session_id,
        "topic": topic,
        "stance": stance,
        "difficulty": difficulty,
        "input_mode": input_mode,
    }

    SESSION_DB[session_id] = session_data
    return session_data

def get_session(session_id: str):
    return SESSION_DB.get(session_id)