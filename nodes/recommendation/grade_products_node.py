from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from jeepchat.logger import logger
from jeepchat.services.model_loader import openai_response
from jeepchat.services.context import build_user_history_context
from jeepchat.config.prompts import product_grader_prompt
from jeepchat.config.config import GPT_4_1_MINI_MODEL_ID
from jeepchat.state import ChatState

def grade_products_node(state: ChatState) -> Dict[str, Any]:
    logger.info("\n==== [CHECK PRODUCT RELEVANCE TO QUESTION] ====\n")
    query = state["user_input"]
    product_hits = state.get("product_hits", [])
    is_followup = state.get("is_followup", False)
    vehicle_fitment = state.get("vehicle_fitment", None)

    if not isinstance(product_hits, list):
        logger.error("[GradeProducts] 'product_hits'는 리스트여야 합니다.")
        return {**state, "trigger_plan_b": True, "relevant_docs": []}

    if vehicle_fitment:
        query += f"vehicle fitment: {vehicle_fitment}"
    
    if is_followup:
        conversation_history = state.get("conversation_history", [])
        history_context = build_user_history_context(conversation_history)
        query += f"conversation history: {history_context}"
    
    def eval_product(item):
        i, hit = item
        doc_text = format_base_info(hit)
        grade = retrieval_grader(user_input=query, documents=doc_text)
        return (grade, hit, i, doc_text)

    # 병렬 평가: 최대 5개 동시 실행
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(eval_product, enumerate(product_hits)))
    
    # 필터링된 상품
    relevant_docs = []
    relevant_doc_count = 0
    for grade, hit, i, doc_text in results:
        logger.info(f"상품 [{i}]: {doc_text}\n관련 여부: {grade}")
        
        if grade == "yes":
            relevant_docs.append(hit)
            relevant_doc_count += 1
        else:
            logger.info("==== [GRADE: DOCUMENT NOT RELEVANT] ====")
    
    logger.info(f"[GradeProducts] 관련 상품 수: {relevant_doc_count}")
    
    if relevant_doc_count == 0:
        logger.info("[GradeProducts] 관련 상품이 없습니다. Product hits를 반환합니다.")
        return {
            **state,
            "relevant_docs": product_hits,
            "trigger_plan_b": False
        }
    
    if relevant_doc_count == 1:
        logger.info("[GradeProducts] 관련 상품이 부족합니다. Neo4j Plan B 검색으로 이동합니다.")
        return {
            **state,
            "relevant_docs": relevant_docs,
            "trigger_plan_b": True
        }
    
    return {
        **state,
        "relevant_docs": relevant_docs,
        "trigger_plan_b": False
    }

def retrieval_grader(user_input: str, documents: str) -> str:
    # GradeProducts 데이터 모델을 사용하여 구조화된 출력을 생성하는 LLM
    try:
        response = openai_response(
            system_prompt=product_grader_prompt(documents),
            user_input=user_input,
            model_id=GPT_4_1_MINI_MODEL_ID
        )
        
        return response
    
    except Exception as e:
        logger.error(f"[GradeProducts] 상품 관련성 평가 중 오류 발생: {e}", exc_info=True)
        return "no"
    
def format_base_info(hit: Dict[str, Any]) -> str:
    return (
        f"model_no: {hit.get("model_no", "")}\n"
        f"product_name_ko: {hit.get("product_name_ko", "")}\n"
        f"score: {hit.get("score", 0)}\n"
        f"product_name: {hit.get("product_name", "")}\n"
        f"manufacturer: {hit.get("manufacturer", "")}\n"
        f"price: ${hit.get("price", 0):.2f}\n"
        f"main_category: {hit.get("category_name", "")}\n"
        f"product_url: {hit.get("product_url", "")}"
    )