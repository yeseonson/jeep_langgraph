from jeepchat.logger import logger
from jeepchat.config.constants import PRODUCT_TOP_K
from jeepchat.services.product_search import JeepSearchService
from jeepchat.services.product_search_kw import JeepSearchServiceKW

def product_search_node(state):
    try:
        query = state.get("user_input", "")

        if not query:
            return {
                **state,
                "output": "질문을 입력해주세요.",
                "product_hits": []
            }
        
        vehicle_fitment = state.get("vehicle_fitment", None)

        product_search_service = JeepSearchService()

        product_hits = product_search_service.search(query, size=PRODUCT_TOP_K, vehicle_fitment=vehicle_fitment)

        if not product_hits:
            logger.info("[product_search_node] 기본 검색 결과 없음, 키워드 부스팅 검색 시도")
            product_search_service = JeepSearchServiceKW()
            product_hits = product_search_service.search(query_text=query, size=PRODUCT_TOP_K, vehicle_fitment=vehicle_fitment)

        if not product_hits:
            return {
                **state,
                "product_hits": [],
                "output": "적절한 상품을 찾을 수 없습니다. 질문을 조금 더 구체적으로 입력해 주세요."
            }
        
        return {
            **state,
            "product_hits": product_hits
        }

    except Exception as e:
        logger.error(f"[product_search_node] 검색 중 오류 발생: {e}", exc_info=True)
        return {
            **state,
            "product_hits": [],
            "output": "상품 검색 중 오류가 발생했습니다."
        }