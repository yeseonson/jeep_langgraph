from datetime import datetime
from typing import List, Dict, Any
from jeepchat.utils import generate_message_id
from jeepchat.logger import logger
from jeepchat.config.prompts import product_recommend_prompt
from jeepchat.services.model_loader import openai_response
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.state import ChatState

def generate_response_node(state: ChatState) -> Dict[str, Any]:
    user_input = state["user_input"]
    
    user_id = state["user_id"]
    thread_id = state["thread_id"]
    conversation_history = state.get("conversation_history", [])

    product_info = state.get("product_info", "")
    knowledge_summary = state.get("knowledge_summary", "")

    memory_manager = ChatMemoryManager()

    try:
        # 제품 정보와 지식 정보를 결합하여 최종 컨텍스트 구성
        final_context = f"""제품 정보:
        {product_info}

        관련 지식:
        {knowledge_summary}"""

        # LLM 호출하여 응답 생성
        response = call_llm_with_context(user_input=user_input, context=final_context, conversation_history=conversation_history)
        if user_id and thread_id:
            message = {
                "user_input": user_input,
                "output": response,
                "timestamp": datetime.now().isoformat(),
                "type": "recommendation"
            }
            message_id = generate_message_id(user_id=user_id)
            memory_manager.save_message(user_id, thread_id, message_id, message)

        logger.info(f"LLM 응답: {response}")

        return {
            **state,
            "output": response,
            'original_query': user_input
        }

    except Exception as e:
        logger.error(f"[generate_response_node] 응답 생성 중 오류: {e}", exc_info=True)
        return {
            **state,
            "output": "죄송합니다. 처리 중 오류가 발생했습니다."
        }
    
def call_llm_with_context(user_input: str, context: str, conversation_history: List[Dict] = []):
    """컨텍스트와 함께 LLM 호출"""

    if not user_input.strip() or not context.strip():
        return "입력 정보가 부족합니다."
    
    history_context = ""
    if conversation_history:
        recent_history = conversation_history[-3:]
        history_context = "\n".join(
            f"사용자: {item['user']}\n시스템: {item['system']}" for item in recent_history
        ) + "\n"

    prompt = product_recommend_prompt(history_context=history_context, context=context, user_input=user_input)

    logger.info(f"history_context: {history_context}")

    try:
        response = openai_response(system_prompt=prompt, user_input=user_input, max_tokens=1024)
        return response

    except Exception as e:
        logger.error(f"LLM 호출 중 오류 발생: {e}", exc_info=True)
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
