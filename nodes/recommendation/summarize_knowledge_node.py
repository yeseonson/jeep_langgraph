from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.model_loader import openai_response
from jeepchat.config.prompts import generate_product_recommendation_prompt, knowledge_summary_system_prompt

def summarize_knowledge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        query = state['user_input']
        knowledge_hits = state.get("knowledge_hits", [])

        if not knowledge_hits:
            logger.warning("[summarize_knowledge_node] knowledge_hits가 비어 있어 요약을 건너뜁니다.")
            return {
                **state,
                "knowledge_summary": ""
            }
        
        knowledge_context = "\n".join([hit.get('document', '') for hit in knowledge_hits])
        knowledge_summary = summarize_knowledge_hits(query, knowledge_context)

        return {
            **state,
            "knowledge_summary": knowledge_summary
        }

    except Exception as e:
        logger.error(f"[knowledge_search_node] 검색 중 오류 발생: {e}", exc_info=True)
        return {
            **state,
            "knowledge_summary": "",
            "output": "지식 검색 중 오류가 발생했습니다."
        }

def summarize_knowledge_hits(user_input: str, documents: str) -> str:
    
    summarization_prompt = generate_product_recommendation_prompt(user_input=user_input, documents=documents)
    summary = openai_response(
        system_prompt=knowledge_summary_system_prompt,
        user_input=summarization_prompt
    )

    if not summary:
        return "관련 지식 정보를 찾을 수 없습니다."

    return summary
