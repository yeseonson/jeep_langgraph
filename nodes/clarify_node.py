from jeepchat.services.model_loader import openai_response
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.services.context import build_history_context
from jeepchat.config.prompts import clarification_prompt, info_check_prompt
from jeepchat.state import ChatState
from jeepchat.logger import logger
from jeepchat.utils import generate_message_id
from datetime import datetime

def clarify_node(state: ChatState):
    user_input = state["user_input"]
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
    conversation_history = state.get("conversation_history", "")
    vehicle_fitment = state.get('vehicle_fitment', None)

    clarify_attempts = state.get("clarify_attempts", 0)

    if clarify_attempts >= 2:
        logger.warning(f"[ClarifyNode] clarify_attempts {clarify_attempts}회 초과 → fallback 이동")
        clarify_prompt = clarification_prompt(history_context=history_context, user_input=query)
        response = openai_response(system_prompt=clarify_prompt, user_input=query)

        return {
            **state,
            "output": response,
            "clarify_attempts": clarify_attempts,
            "force_fallback": True
        }

    if vehicle_fitment:
        query = f"{user_input} (vehicle fitment: {vehicle_fitment})"
    else:
        query = user_input

    history_context = ""
    history_context = build_history_context(conversation_history=conversation_history)
    memory_manager = ChatMemoryManager()
    
    try:
        # 정보 충분 여부 판단
        prompt = info_check_prompt(history_context=history_context, user_input=query)
        info_check = openai_response(system_prompt=prompt, user_input=query)
        
        if info_check.strip().lower() == 'sufficient':
            logger.info(f"[ClarifyNode] 충분한 정보 확인 → 재라우팅")
            return {
                **state,
                "is_clarify_followup": True,
                "original_query": user_input,
                "needs_rerouting": True,
                "clarify_attempts": 0 # 초기화
            }
        
        logger.info(f"[ClarifyNode] 추가 정보 필요 → 추가 질문 생성")
        clarify_prompt = clarification_prompt(history_context=history_context, user_input=query)
        response = openai_response(system_prompt=clarify_prompt, user_input=query)
        
        # Save the clarification question to chat memory
        if user_id and thread_id:
            message = {
                "user_input": user_input,
                "output": response,
                "timestamp": datetime.now().isoformat(),
                "type": "clarification"
            }
            message_id = generate_message_id(user_id=user_id)
            memory_manager.save_message(user_id, thread_id, message_id, message)
        
        return {
            **state,
            'output': response,
            'original_query': user_input,
            'needs_rerouting': False,
            "clarify_attempts": clarify_attempts + 1
            }

    except Exception as e:
        logger.error(f"[ClarifyNode] 추가 질문 생성 중 오류: {e}", exc_info=True)
        return {
            **state,
            "output": "죄송합니다. 추가 질문을 생성하는 데 문제가 발생했습니다."
            }