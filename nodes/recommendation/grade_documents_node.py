from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.model_loader import openai_response
from jeepchat.config.prompts import retrieval_grader_prompt

def grade_documents_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("\n==== [CHECK PRODUCT RELEVANCE TO QUESTION] ====\n")
    user_input = state['user_input']
    product_hits = state.get('product_hits', [])

    if not isinstance(product_hits, list):
        logger.error("[GradeDocuments] 'product_hits'는 리스트여야 합니다.")
        return {**state, 'trigger_plan_b': True, 'relevant_docs': []}
    
    # 필터링된 문서
    relevant_docs = []
    relevant_doc_count = 0

    for hit in product_hits:
        doc_text = format_base_info(hit)
        print(f"doc_text: {doc_text}")
        grade = retrieval_grader(user_input=user_input, documents=doc_text)
        logger.debug(f"[GradeDocuments] 문서 관련성 평가 결과: {grade}")
        
        if grade == 'yes':
            logger.info("==== [GRADE: DOCUMENT RELEVANT] ====")
            
            relevant_docs.append(hit)
            relevant_doc_count += 1
        else:
            logger.info("==== [GRADE: DOCUMENT NOT RELEVANT] ====")
            continue
    
    logger.info(f"[GradeDocuments] 관련 문서 수: {relevant_doc_count}")
    logger.info(f"[GradeDocuments] 관련 문서: {relevant_docs}")

    if relevant_doc_count == 0:
        logger.info("[GradeDocuments] 관련 문서가 없습니다. Neo4j Plan B 검색으로 이동합니다.")
        return {
            **state,
            'relevant_docs': [],
            'trigger_plan_b': True
        }

    return {
        **state,
        'relevant_docs': relevant_docs,
        'trigger_plan_b': False
    }

def retrieval_grader(user_input: str, documents: str) -> str:
    # GradeDocuments 데이터 모델을 사용하여 구조화된 출력을 생성하는 LLM
    try:
        retrieval_grader = openai_response(
            system_prompt=retrieval_grader_prompt(documents=documents), 
            user_input=user_input
        )
        
        return retrieval_grader
    
    except Exception as e:
        logger.error(f"[GradeDocuments] 문서 관련성 평가 중 오류 발생: {e}", exc_info=True)
        return "no"
    
def format_base_info(hit: Dict[str, Any]) -> str:
    return (
        f"model_no: {hit.get('model_no', '')}\n"
        f"product_name_ko: {hit.get('name_ko', '')}\n"
        f"score: {hit.get('score', 0)}\n"
        f"product_name: {hit.get('product_name', '')}\n"
        f"price: ${hit.get('base_price', 0):.2f}\n"
        f"manufacturer: {hit.get('manufacturer_name', '')}\n"
        f"main_category: {hit.get('category_name', '')}"
    )