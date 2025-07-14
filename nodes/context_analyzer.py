from jeepchat.logger import logger
from jeepchat.state import ChatState
from jeepchat.config.prompts import relevance_prompt
from jeepchat.services.context import build_history_context, get_recent_conversation

def analyze_context(state: ChatState) -> ChatState:
    """맥락 분석 노드 - 이전 대화와 연관성 판단"""

    from jeepchat.services.chat_memory import ChatMemoryManager
    from jeepchat.services.model_loader import openai_response
    
    user_input = state.get("user_input", "")
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
    is_clarify_followup = state.get("is_clarify_followup", False)
    vehicle_fitment = state.get("vehicle_fitment", "")

    logger.info(f"[CONTEXT_ANALYZER] 입력 분석: user_input - {user_input}, vehicle_fitment - {vehicle_fitment}")
    logger.info(f"[CONTEXT_ANALYZER] clarify 후속 여부: {is_clarify_followup}")

    is_followup = False
    conversation_history = []

    if user_id and thread_id:
        memory_manager = ChatMemoryManager()
        previous_messages = memory_manager.get_thread_messages(user_id, thread_id)

        if previous_messages:
            conversation_history = get_recent_conversation(previous_messages, max_turns=3)
            logger.info(f"[CONTEXT_ANALYZER] conversation history: {conversation_history}")

            history_context = build_history_context(conversation_history)
            prompt = relevance_prompt(
                history_context=history_context, 
                user_input=user_input, 
                vehicle_fitment=vehicle_fitment
            )

            try:
                relevance_result = openai_response(
                    system_prompt=prompt,
                    user_input=user_input
                )
                is_followup = relevance_result.strip().lower() == 'relevant'
                logger.info(f"[CONTEXT_ANALYZER] 연관성 분석 결과: {is_followup}")

            except Exception as e:
                logger.error(f"[CONTEXT_ANALYZER] 연관성 분석 중 오류: {e}")

    new_state = dict(state)
    new_state.update({
        "conversation_history": conversation_history,
        "is_followup": is_followup,
        "output": ""
    })

    return new_state
