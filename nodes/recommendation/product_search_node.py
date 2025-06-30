from jeepchat.logger import logger
from jeepchat.config.constants import PRODUCT_TOP_K
from jeepchat.services.product_search import JeepSearchService

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