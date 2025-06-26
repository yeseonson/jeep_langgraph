from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.knowledge_search import hybrid_search
from jeepchat.config.constants import KNOWLEDGE_TOP_K

def knowledge_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        query = state["user_input"]
        knowledge_hits = hybrid_search(query, top_k=KNOWLEDGE_TOP_K)
        
        if not knowledge_hits:
            logger.warning("[knowledge_search_node] knowledge_hits가 비어 있어 지식 검색 단계를 건너뜁니다.")
            return {
                **state,
                "knowledge_hits": [],
            }

        return {
            **state,
            "knowledge_hits": knowledge_hits
        }

    except Exception as e:
        logger.error(f"[knowledge_search_node] 검색 중 오류 발생: {e}", exc_info=True)
        return {
            **state,
            "knowledge_hits": [],
            "output": "지식 검색 중 오류가 발생했습니다."
        }