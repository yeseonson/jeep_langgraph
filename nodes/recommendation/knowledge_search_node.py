from typing import Dict, Any
from jeepchat.logger import logger
from jeepchat.services.knowledge_search import semantic_search
from jeepchat.services.context import build_user_history_context
from jeepchat.config.constants import KNOWLEDGE_TOP_K
from jeepchat.state import ChatState

def knowledge_search_node(state: ChatState) -> Dict[str, Any]:
    try:
        query = state["user_input"]
        vehicle_fitment = state.get("vehicle_fitment", None)
        conversation_history = state.get("conversation_history", [])
        is_followup = state.get("is_followup", False)

        if vehicle_fitment:
            query += f"\nvehicle_fitment: {vehicle_fitment}"

        history_context = ""
        if is_followup:
            history_context = build_user_history_context(conversation_history)
            query += f"\n{history_context}"

        knowledge_hits = semantic_search(query, top_k=KNOWLEDGE_TOP_K)
        
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