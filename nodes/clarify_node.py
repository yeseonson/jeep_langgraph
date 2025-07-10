from jeepchat.services.model_loader import openai_response
from jeepchat.services.chat_memory import ChatMemoryManager
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

    if vehicle_fitment:
        query = f"{user_input} (vehicle fitment: {vehicle_fitment})"
    else:
        query = user_input

    history_context = ""
    if conversation_history:
        recent_history = conversation_history[-3:]
        history_context = "\n".join(
            f"사용자: {item['user']}\n시스템: {item['system']}" for item in recent_history
        ) + "\n"
    
    memory_manager = ChatMemoryManager()

    # 먼저 충분한 정보가 있는지 확인
    prompt = info_check_prompt(history_context=history_context, user_input=query)
    
    try:
        info_check = openai_response(system_prompt=prompt, user_input=query)
        
        logger.info(f"[ClarifyNode] 충분한 정보 확인 → 재라우팅")

        if info_check.strip().lower() == 'sufficient':
            return {
                **state,
                "is_clarify_followup": True,
                "original_query": user_input,
                "needs_rerouting": True
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
            'needs_rerouting': False
            }

    except Exception as e:
        logger.error(f"[ClarifyNode] 추가 질문 생성 중 오류: {e}", exc_info=True)
        return {
            **state,
            "output": "죄송합니다. 추가 질문을 생성하는 데 문제가 발생했습니다."
            }