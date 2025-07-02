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
    
    memory_manager = ChatMemoryManager()
    
    logger.info(f"conversation history: {conversation_history}")

    # 먼저 충분한 정보가 있는지 확인
    info_check = info_check_prompt(conversation_history=conversation_history, query=user_input)
    
    try:
        info_check = openai_response(system_prompt=info_check_prompt, user_input=user_input)
        
        # 충분한 정보가 있는 경우 -> 라우터 노드로 이동 필요
        if info_check.strip().lower() == 'sufficient':
            return {
                **state,
                "is_clarify_followup": True,
                "original_query": user_input
            }
        
        # 추가 정보가 필요한 경우
        prompt = clarification_prompt(conversation_history=conversation_history, query=user_input)
        
        response = openai_response(system_prompt=prompt, user_input=user_input)
        
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
            'original_query': user_input
            }

    except Exception as e:
        logger.error(f"[ClarifyNode] 추가 질문 생성 중 오류: {e}", exc_info=True)
        return {
            **state,
            "output": "죄송합니다. 추가 질문을 생성하는 데 문제가 발생했습니다."
            }