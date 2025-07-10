from jeepchat.services.model_loader import openai_response
from jeepchat.logger import logger
from jeepchat.state import ChatState
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.utils import generate_message_id
from jeepchat.config.prompts import fallback_prompt
from datetime import datetime

def fallback_node(state: ChatState):
    query = state['user_input']
    user_id = state['user_id']
    thread_id = state['thread_id']
    conversation_history = state.get("conversation_history", [])

    memory_manager = ChatMemoryManager()

    history_context = ""
    if conversation_history:
        history_context = "\n".join(
            f"사용자: {msg['user']}\n시스템: {msg['system']}" for msg in conversation_history
        )

    prompt = fallback_prompt(history_context=history_context)

    try:
        response = openai_response(system_prompt=prompt, user_input=query)
        
        # 메시지 객체 생성
        message = {
            "user_input": query,
            "output": response,
            "timestamp": datetime.now().isoformat(),
            "type": "fallback"
        }
        
        # 메모리에 저장 (user_id와 thread_id가 있는 경우에만)
        if user_id and thread_id:
            message_id = generate_message_id(user_id=user_id)
            memory_manager.save_message(user_id, thread_id, message_id, message)

        return {
            "output": response,
            "conversation_history": conversation_history
        }

    except Exception as e:
        logger.error(f"[FallbackNode] fallback 응답 생성 중 오류: {e}", exc_info=True)
        
        # 오류 발생 시 기본 응답
        error_response = "죄송합니다. 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        # LangGraph state 형식으로 반환
        return {
            "output": error_response,
            "conversation_history": conversation_history
        }