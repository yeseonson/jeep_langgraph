from typing import List, Dict

def contains_korean(text: str) -> bool:
    """텍스트에 한글이 포함되어 있는지 여부를 반환"""
    return any('\uac00' <= char <= '\ud7a3' for char in text)

def build_history_context(conversation_history: List[Dict[str, str]]) -> str:
    if not conversation_history:
        return ""

    return "\n".join(
        f"user: {item.get('user', '')}\nsystem: {item.get('system', '')}"
        for item in conversation_history
    ) + "\n"

def get_recent_conversation(previous_messages: List[Dict], max_turns: int = 3) -> List[Dict[str, str]]:
    return [
        {
            "user": msg["user_input"], 
            "system": msg["output"]
        }
        for msg in previous_messages[-max_turns:]
        if msg.get("user_input") and msg.get("output")
    ]