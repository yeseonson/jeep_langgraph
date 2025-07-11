from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel

class BaseChatState(TypedDict):
    user_id: str
    thread_id: str
    message_id: str
    user_input: str
    intent: Optional[str]
    output: Optional[str]
    context_relevant: Optional[bool]
    is_followup: Optional[bool]
    conversation_history: Optional[List[Dict[str, str]]]
    original_query: Optional[str]
    trigger_plan_b: Optional[bool]


class RecommendationState(TypedDict):
    vehicle_fitment: Optional[str]
    product_model_no: Optional[List[Dict]]
    product_hits: Optional[List[Dict]]
    neo4j_hits: Optional[Dict[str, Dict]]
    product_info: Optional[str]
    relevant_docs: Optional[Dict[str, Dict]]
    knowledge_hits: Optional[List[Dict]]
    knowledge_summary: Optional[str]


class InformationState(TypedDict):
    query_rewritten: Optional[str]
    web_search: Optional[str]
    documents: Optional[List[Dict]]
    relevant_doc_count: Optional[int]
    is_retry_count: int = 0


class RegulationState(TypedDict):
    regulation_admin_answer: Optional[str]
    device_category: Optional[str]
    is_minor_tuning: Optional[str]
    early_exit: Optional[str]
    system_prompt:Optional[str]


class ClarifyState(TypedDict):
    is_clarify_followup: Optional[bool]
    clarify_attempts: Optional[int]
    needs_rerouting: Optional[bool]
    force_fallback: Optional[bool]


class ChatState(BaseChatState, RecommendationState, InformationState, RegulationState, ClarifyState):
    pass


class Document(BaseModel):
    page_content: str
    metadata: Dict[str, Any] = {}