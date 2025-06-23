from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.services.database import opensearch_client
from jeepchat.services.model_loader import openai_response
from jeepchat.services.product_search import JeepSearchService
from jeepchat.services.knowledge_search import hybrid_search
from jeepchat.core.generate_id import generate_message_id
from jeepchat.core.logger import logger
from typing import List, Dict
from datetime import datetime

PRODUCT_TOP_K = 5
KNOWLEDGE_TOP_K = 3

client = opensearch_client()
product_search_service = JeepSearchService()

memory_manager = ChatMemoryManager()

def recommendation_node(state):
    """상품 추천 노드"""
    query = state["user_input"]
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
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
        
        # 제품 정보 추출
        product_info = "\n".join([
            f"제품명: {hit.get('product_name_ko', '')}\n"
            f"가격: ${hit.get('price', 0):.2f}\n"
            f"제조사: {hit.get('manufacturer', '')}\n"
            f"카테고리: {hit.get('main_category', '')}\n"
            for hit in product_hits[:3]
        ])

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

    prompt = f"""<|im_start|>system
                당신은 지프 튜닝 및 부품 전문가입니다. 아래 정보를 바탕으로 정확하고 도움이 되는 답변을 제공해주세요.
                되도록 사용자가 사용한 단어를 유지하되, 오타를 포함하지 말고 정확하게 표기하세요.

                답변 시 다음 사항을 고려해주세요:
                1. 제품 추천
                - 추천 제품의 구체적인 특징과 장점을 설명
                - 호환성 정보가 있다면 반드시 언급
                - 가격 정보가 있다면 포함
                - 제품의 주요 사용 사례나 적합한 상황 설명

                2. 관련 지식 정보
                - 제품 사용 시 주의사항이나 팁
                - 설치나 사용에 관련된 기술적 정보
                - 법규나 규정 관련 정보
                - 다른 사용자들의 경험이나 추천 사항

                3. 종합적인 조언
                - 제품 선택 시 고려해야 할 추가 사항
                - 대안 제품이나 관련 제품 추천
                - 구매 전 확인해야 할 사항
                - 설치나 사용 시 필요한 추가 부품이나 도구<|im_end|>
                <|im_start|>user
                {history_context}
                
                다음은 관련 정보입니다:

                {context}

                질문: {user_query}<|im_end|>
                <|im_start|>assistant"""

    logger.info(f"history_context: {history_context}")

    try:
        response = openai_response(system_prompt=prompt, user_input=user_query, max_tokens=1024)
        return response

    except Exception as e:
        logger.error(f"LLM 호출 중 오류 발생: {e}", exc_info=True)
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"

def summarize_knowledge_hits(query, documents):
    summarization_prompt = f"""당신은 지프 차량의 튜닝과 주행 환경에 대한 기술 문서를 분석하는 전문가입니다.

                            다음은 사용자 질문과 관련된 커뮤니티 기반 지식 문서입니다. 아래 문서들의 **내용만을 기반으로** 요약을 작성해 주세요. \
                            외부 지식이나 일반적인 추론을 추가하지 마십시오.

                            - 문서 내에 언급된 **기술 정보, 사용자 경험, 부품 정보**는 요약에 반드시 포함해 주세요.
                            - 문서에 **언급되지 않은 정보**는 절대 삽입하지 마세요.
                            - 요약은 제품 추천에 참고할 수 있도록 구성하되, **문서에 실제로 언급된 내용만** 바탕으로 하세요.

                            질문: "{query}"

                            문서 내용:
                            {documents}

                            요약:"""

    summary = openai_response(
        system_prompt="당신은 지프 튜닝 기술 문서를 요약하는 전문가입니다. 제공된 문서 내용을 기반으로만 요약을 생성하세요. 외부 지식, 유추, 상식에 기반한 내용은 포함하지 마세요.", 
        user_input=summarization_prompt
    )

    if not summary:
        return "관련 지식 정보를 찾을 수 없습니다."

    return summary
