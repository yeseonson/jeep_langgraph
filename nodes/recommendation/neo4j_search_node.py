from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.neo4j_recommend import recommend_parts, neo4j_graph

def neo4j_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return neo4j_search_node_common(state, query_type="same")

def neo4j_plan_b_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return neo4j_search_node_common(state, query_type="different")

def neo4j_search_node_common(state: Dict[str, Any], query_type: str = "same") -> Dict[str, Any]:
    try:
        relevant_products = state.get("relevant_docs", [])
        if not relevant_products:
            logger.warning(f"[neo4j_search_node_common] relevant_products가 비어 있어 neo4j recommend를 건너뜁니다. (query_type={query_type})")
            return {
                **state,
                "neo4j_hits": {},
            }

        from jeepchat.config.constants import same_manufacturer_query, different_manufacturer_query
        optional_query = same_manufacturer_query if query_type == "same" else different_manufacturer_query

        model_no_list = [item["model_no"] for item in relevant_products if item.get("model_no")]
        neo4j_hits = recommend_parts(graph=neo4j_graph(),
                                     input_model_nos=model_no_list,
                                     optional_query=optional_query)
        
        logger.info(f"[neo4j_search_node_common] 추천 결과: {len(neo4j_hits)}개 (query_type={query_type})")
        logger.debug(f"[neo4j_search_node_common] 추천 상세: {neo4j_hits}")

        return {
            **state,
            "neo4j_hits": neo4j_hits
        }

    except Exception as e:
        logger.error(f"[neo4j_search_node_common] 검색 중 오류 발생: {e} (query_type={query_type})", exc_info=True)
        return {
            **state,
            "neo4j_hits": {},
            "output": "추천 중 오류가 발생했습니다."
        }
