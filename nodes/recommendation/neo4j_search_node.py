from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.neo4j_recommend import recommend_parts, neo4j_graph

def neo4j_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        product_hits = state.get("product_hits", [])
        if not product_hits:
            logger.warning("[neo4j_search_node] product_hits가 비어 있어 추천을 건너뜁니다.")
            return {
                **state,
                "neo4j_hits": {},
            }
        
        neo4j_hits = recommend_parts(neo4j_graph(), product_hits)
        logger.info(f"[neo4j_search_node] 추천 결과: {len(neo4j_hits)}개")
        logger.debug(f"[neo4j_search_node] 추천 상세: {neo4j_hits}")

        return {
            **state,
            "neo4j_hits": neo4j_hits
        }

    except Exception as e:
        logger.error(f"[neo4j_search_node] 검색 중 오류 발생: {e}", exc_info=True)
        return {
            **state,
            "neo4j_hits": {},
            "output": "추천 중 오류가 발생했습니다."
        }