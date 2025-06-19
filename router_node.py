from logger import logger
from intent_classifier import classify_intent
from followup_analyzer import is_followup_question

def router_node(state):
    user_input = state["user_input"]
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
    is_clarify_followup = state.get("is_clarify_followup", False)
    conversation_history = state.get("conversation_history", [])

    history_text = ""
    
    if user_id and thread_id:
        history_text = "\n".join(
            f"사용자: {msg['user']}\n시스템: {msg['system']}" for msg in conversation_history
        )

    # 의도 분류
    intent = classify_intent(user_input, history_text, is_clarify_followup)

    # 후속 질문 여부 판단
    is_followup = is_followup_question(user_input, conversation_history, is_clarify_followup)

    logger.info(f"질문: {user_input} > 다음 노드: {intent} (followup: {is_followup})")

    return {
        **state,
        "intent": intent,
        "is_followup": is_followup,
        "output": ""
    }