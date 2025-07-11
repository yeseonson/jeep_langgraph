import re
from jeepchat.logger import logger
from jeepchat.state import ChatState
from jeepchat.services.model_loader import openai_response
from jeepchat.services.context import build_history_context
from jeepchat.config.prompts import (
    intent_classify_prompt,
    intent_clarify_followup_instruction,
    intent_context_relevance_instruction,
)

def router_node(state: ChatState):
    user_input = state["user_input"]
    is_clarify_followup = state.get("is_clarify_followup", False)
    is_followup = state.get("is_followup", False)
    conversation_history = state.get("conversation_history", [])
    vehicle_fitment = state.get("vehicle_fitment", None)

    # 최근 맥락 추출
    history_context = build_history_context(conversation_history)

    # 의도 분류
    if is_followup:
        intent = classify_intent(
            user_input=user_input, 
            context=history_context, 
            is_clarify=is_clarify_followup, 
            vehicle_fitment=vehicle_fitment
        )
    
    else:
        intent = classify_intent(
            user_input=user_input, 
            context="", 
            is_clarify=is_clarify_followup, 
            vehicle_fitment=vehicle_fitment
        )

    # clarify 후속 로직 분리 처리
    if is_clarify_followup and intent == "question about intent":
        return handle_clarify_followup_failure(state)

    # 일반 처리
    result_state = {
        **state,
        "intent": intent,
        "is_followup": is_followup,
        "output": "",
    }

    if is_clarify_followup:
        result_state["is_clarify_followup"] = False
        logger.info(f"[Router] clarify 후속 처리 완료 → intent: {intent}")

    logger.info(f"[Router] 질문: {user_input} > intent: {intent}, followup: {is_followup}")
    return result_state

def handle_clarify_followup_failure(state: ChatState) -> ChatState:
    clarify_attempts = state.get("clarify_attempts", 0)
    logger.warning(f"[Router] clarify 후속에서도 의도 판단 실패 (clarify_attempts={clarify_attempts})")

    if clarify_attempts >= 2:
        logger.info("[Router] clarify_attempts 초과 → fallback 유도")
        return {
            **state,
            "intent": "fallback",
            "force_fallback": True,
            "is_clarify_followup": False,
        }

    return {
        **state,
        "intent": "question about intent",
        "output": "",
    }

def classify_intent(user_input: str, context: str = "", is_clarify: bool = False, vehicle_fitment: str = "") -> str:
    prompt_parts = [intent_classify_prompt]

    if vehicle_fitment:
        prompt_parts.append(f"사용자 차량 정보(vehicle_fitment): {vehicle_fitment}")
    if context:
        prompt_parts.append(f"대화 맥락(history_context): \n{context}")
    if is_clarify:
        prompt_parts.append(intent_clarify_followup_instruction)
    elif context:
        prompt_parts.append(intent_context_relevance_instruction)

    prompt = "\n\n".join(prompt_parts)

    try:
        response = openai_response(system_prompt=prompt, user_input=user_input, model_id="gpt-4.1-mini")
        match = re.search(r"\b(recommendation|information|regulation|question about intent|out of context)\b", response.lower())
        return match.group(1) if match else "question about intent"
    
    except Exception as e:
        logger.error(f"[Router] 의도 분류 중 오류: {e}", exc_info=True)
        return "question about intent"