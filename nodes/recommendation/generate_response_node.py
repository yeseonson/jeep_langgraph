from datetime import datetime
from typing import Dict, Any
from jeepchat.utils import generate_message_id
from jeepchat.logger import logger
from jeepchat.config.prompts import product_recommend_prompt
from jeepchat.config.config import GPT_4_1_MINI_MODEL_ID
from jeepchat.services.model_loader import openai_response
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.services.context import build_history_context
from jeepchat.state import ChatState

def generate_response_node(state: ChatState) -> Dict[str, Any]:
    user_input = state["user_input"]
    
    user_id = state["user_id"]
    thread_id = state["thread_id"]
    vehicle_fitment = state.get("vehicle_fitment", "")
    is_followup = state.get("is_followup", False)

    product_info = state.get("product_info", "")
    knowledge_summary = state.get("knowledge_summary", "")
    
    if not knowledge_summary:
        knowledge_hits = state.get("knowledge_hits", [])
        knowledge_summary = "\n".join(
            hit.get('document', '') for hit in knowledge_hits
        ) if knowledge_hits else ""

    memory_manager = ChatMemoryManager()

    history_context = ""
    if is_followup:
        conversation_history = state.get("conversation_history", [])
        history_context = build_history_context(conversation_history, max_turns=1)

    try:
        # 제품 정보와 지식 정보를 결합하여 최종 컨텍스트 구성
        final_context = f"""
        제품 정보(product_info):
        {product_info}

        [지식 정보는 참조용입니다]
        관련 지식(knowledge_hits):
        {knowledge_summary}"""

        # LLM 호출하여 응답 생성
        response = call_llm_with_context(
            user_input + f"\n차종 정보(vehicle_fitment):{vehicle_fitment}", 
            final_context, 
            history_context
        )
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
    
def call_llm_with_context(user_input: str, context: str, history_context: str):
    """컨텍스트와 함께 LLM 호출"""

    if not user_input.strip() or not context.strip():
        return "입력 정보가 부족합니다."
    
    prompt = product_recommend_prompt(history_context, context, user_input)

    try:
        response = openai_response(
            system_prompt=prompt, 
            user_input=user_input, 
            max_tokens=2048,
            model_id=GPT_4_1_MINI_MODEL_ID
        )
        return response

    except Exception as e:
        logger.error(f"LLM 호출 중 오류 발생: {e}", exc_info=True)
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
