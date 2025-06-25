from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import openai_response
from jeepchat.services.product_search import JeepSearchService
from jeepchat.services.knowledge_search import hybrid_search
from jeepchat.services.neo4j_recommend import recommend_parts, neo4j_graph
from jeepchat.core.utils import generate_message_id
from jeepchat.core.logger import logger
from jeepchat.config.prompts import generate_product_recommendation_prompt, product_recommend_prompt
from typing import List, Dict, Any
from datetime import datetime

PRODUCT_TOP_K = 3
KNOWLEDGE_TOP_K = 3

client = opensearch_client()
product_search_service = JeepSearchService()

memory_manager = ChatMemoryManager()

def recommendation_node(state):
    """상품 추천 노드"""
    query = state["user_input"]
    user_id = state["user_id"]
    thread_id = state["thread_id"]
    conversation_history = state.get("conversation_history", "")

    try:
        query = state.get("user_input", "")
        if not query:
            return {
                **state,
                "output": "질문을 입력해주세요."
            }

        # 제품 검색 수행
        product_hits = product_search_service.search(query, size=PRODUCT_TOP_K)

        neo4j_hits = recommend_parts(neo4j_graph(), product_hits)
        logger.info(f"[Neo4j Recommend] product hits: {product_hits}")
        logger.info(f"[Neo4j Recommend] neo4j hits: {neo4j_hits}")
        
        # 제품 정보 추출
        product_info = format_product_recommendations(neo4j_hits=neo4j_hits)

        logger.info(f"상품 검색 결과: {product_info}")

        # 지식 검색 수행
        knowledge_hits = hybrid_search(query, top_k=KNOWLEDGE_TOP_K)
        knowledge_context = "\n".join([hit.get('document', '') for hit in knowledge_hits])
        logger.info(f"지식 검색 결과: {knowledge_context}")
        knowledge_summary = summarize_knowledge_hits(query, knowledge_context)
        logger.info(f"지식 검색 요약 결과: {knowledge_summary}")

        # 제품 정보와 지식 정보를 결합하여 최종 컨텍스트 구성
        final_context = f"""제품 정보:
        {product_info}

        관련 지식:
        {knowledge_context}"""

        # LLM 호출하여 응답 생성
        response = call_llm_with_context(user_query=query, context=final_context, conversation_history=conversation_history)
        if user_id and thread_id:
            message = {
                "user_input": query,
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
            'original_query': query
        }

    except Exception as e:
        logger.error(f"Error in recommendation_node: {str(e)}")
        return {
            **state,
            "output": "죄송합니다. 처리 중 오류가 발생했습니다."
        }
    
def format_product_recommendations(neo4j_hits: Dict[str, Dict[str, Any]]) -> str:
    """
    기준 부품 및 추천 부품 정보를 문자열로 포맷팅하여 반환
    """
    lines = []

    for base_hit in neo4j_hits.values():
        base = base_hit["base_info"]
        lines.append(f"모델번호: {base.get('model_no', '')}")
        lines.append(f"제품명: {base.get('name_ko', '')}")
        lines.append(f"가격: ${base.get('base_price', 0):.2f}")
        lines.append(f"제조사: {base.get('manufacturer_name', '')}")
        lines.append(f"카테고리: {base.get('category_name', '')}")
        lines.append(f"추천 부품 수: {base_hit.get('recommendation_count', 0)}")

        lines.extend([
            f"- 추천 모델번호: {rec.get('model_no', '')}\n"
            f"  제품명: {rec.get('name_ko', '')}\n"
            f"  가격: ${rec.get('price', 0):.2f}"
            for rec in base_hit.get("recommendations", [])
        ])

        lines.append("")  # 빈 줄

    return "\n".join(lines)

def call_llm_with_context(user_query: str, context: str, conversation_history: List[Dict] = []):
    """컨텍스트와 함께 LLM 호출"""

    if not user_query.strip() or not context.strip():
        return "입력 정보가 부족합니다."
    
    history_context = ""
    if conversation_history:
        recent_history = conversation_history[-3:]
        history_context = "\n".join(
            f"사용자: {item['user']}\n시스템: {item['system']}" for item in recent_history
        ) + "\n"

    prompt = product_recommend_prompt(history_context=history_context, context=context, user_query=user_query)

    logger.info(f"history_context: {history_context}")

    try:
        response = openai_response(system_prompt=prompt, user_input=user_query, max_tokens=1024)
        return response

    except Exception as e:
        logger.error(f"LLM 호출 중 오류 발생: {e}", exc_info=True)
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"

def summarize_knowledge_hits(query, documents):
    
    summarization_prompt = generate_product_recommendation_prompt(query=query, documents=documents)
    summary = openai_response(
        system_prompt="당신은 지프 튜닝 기술 문서를 요약하는 전문가입니다. 제공된 문서 내용을 기반으로만 요약을 생성하세요. 외부 지식, 유추, 상식에 기반한 내용은 포함하지 마세요.", 
        user_input=summarization_prompt
    )

    if not summary:
        return "관련 지식 정보를 찾을 수 없습니다."

    return summary
