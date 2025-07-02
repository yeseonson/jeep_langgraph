from jeepchat.logger import logger
from jeepchat.state import ChatState
from jeepchat.services.model_loader import openai_response
from jeepchat.config.prompts import (
    intent_classify_prompt,
    intent_clarify_followup_instruction,
    intent_context_relevance_instruction,
)

def router_node(state: ChatState):
    user_input = state["user_input"]
    user_id = state["user_id"]
    thread_id = state["thread_id"]
    is_clarify_followup = state.get("is_clarify_followup", False)
    conversation_history = state.get("conversation_history", [])
    vehicle_fitment = state.get("vehicle_fitment", None)

    history_text = ""
    if user_id and thread_id:
        history_text = "\n".join(
            f"사용자: {msg['user']}\n시스템: {msg['system']}" for msg in conversation_history
        )

    if is_clarify_followup:
        intent = classify_intent(user_input, history_text, is_clarify_followup, vehicle_fitment)
        logger.info(f"[Router] Clarify 후속 질문 감지 → intent: {intent}")

        if intent.strip().lower() == "clarify":
            logger.warning(f"[Router] intent가 Clarify로 재분류됨 → 무한루프 방지를 위해 intent를 {intent}로 변경")
            intent = "recommendation"

        return {
            **state,
            "intent": intent,
            "is_followup": False,
            "is_clarify_followup": False,
            "output": ""
        }

    # 일반 흐름: 후속 여부 판단 및 intent 분류
    intent = classify_intent(user_input, history_text, is_clarify_followup, vehicle_fitment)
    is_followup = state.get("is_followup", False)

    logger.info(f"질문: {user_input} > 다음 노드: {intent} (followup: {is_followup})")

    return {
        **state,
        "intent": intent,
        "is_followup": is_followup,
        "output": ""
    }

def classify_intent(user_input: str, context: str = "", is_clarify: bool = False, vehicle_fitment: str = "") -> str:
    prompt_parts = [intent_classify_prompt]

    if vehicle_fitment:
        prompt_parts.append(f"사용자 차량 정보: {vehicle_fitment}")
    if context:
        prompt_parts.append(context)
    if is_clarify:
        prompt_parts.append(intent_clarify_followup_instruction)
    elif context:
        prompt_parts.append(intent_context_relevance_instruction)

    prompt = "\n\n".join(prompt_parts)

    response = openai_response(system_prompt=prompt, user_input=user_input)
    return response.strip()