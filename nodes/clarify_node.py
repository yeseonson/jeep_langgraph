from jeepchat.services.model_loader import openai_response
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.core.logger import logger
from jeepchat.core.utils import generate_message_id
from datetime import datetime

def clarify_node(state):
    query = state["user_input"]
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
    conversation_history = state.get("conversation_history", "")
    
    memory_manager = ChatMemoryManager()
    
    logger.info(f"conversation history: {conversation_history}")

    # 먼저 충분한 정보가 있는지 확인
    info_check_prompt = f"""<|im_start|>system
                당신은 지프 튜닝 전문가 챗봇입니다.
                사용자의 질문에 답변하기 위해 충분한 정보가 있는지 확인해주세요.
                충분한 정보가 있으면 'sufficient'로, 추가 정보가 필요하면 'insufficient'로 답해주세요.
                {conversation_history}
                <|im_end|>
                <|im_start|>user
                사용자 질문: "{query}"
                <|im_end|>
                <|im_start|>assistant
                """
    
    try:
        info_check = openai_response(system_prompt=info_check_prompt, user_input=query)
        
        # 충분한 정보가 있는 경우 -> 라우터 노드로 이동 필요
        if info_check.strip().lower() == 'sufficient':
            return {
                **state,
                "is_clarify_followup": True,
                "original_query": query
            }
        
        # 추가 정보가 필요한 경우
        prompt = f"""<|im_start|>system
                    당신은 지프 튜닝 전문가 챗봇입니다.
                    고객이 질문했지만, 답변을 위해 필요한 정보가 부족합니다.
                    고객에게 추가로 어떤 정보를 물어봐야 할지 적절한 질문을 생성해주세요.
                    되도록 사용자가 사용한 단어를 유지하되, 오타를 포함하지 말고 정확하게 표기하세요.
                    {conversation_history}
                    <|im_end|>
                    <|im_start|>user
                    사용자 질문: "{query}"
                    <|im_end|>
                    <|im_start|>assistant
                    """
        
        response = openai_response(system_prompt=prompt, user_input=query)
        
        # Save the clarification question to chat memory
        if user_id and thread_id:
            message = {
                "user_input": query,
                "output": response,
                "timestamp": datetime.now().isoformat(),
                "type": "clarification"
            }
            message_id = generate_message_id(user_id=user_id)
            memory_manager.save_message(user_id, thread_id, message_id, message)
        
        return {
            **state,
            'output': response,
            'original_query': query  # 원래 질문 저장
            }

    except Exception as e:
        logger.error(f"[ClarifyNode] 추가 질문 생성 중 오류: {e}", exc_info=True)
        return {
            **state,
            "output": "죄송합니다. 추가 질문을 생성하는 데 문제가 발생했습니다."
            }