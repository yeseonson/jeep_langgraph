from typing import TypedDict, Optional, List, Dict

class ChatState(TypedDict):
    # 기본 정보
    user_id: str
    thread_id: str
    message_id: str
    user_input: str

    # 대화 흐름 관련
    intent: Optional[str]
    output: Optional[str]
    context_relevant: Optional[bool]
    is_followup: Optional[bool] 
    is_clarify_followup: Optional[bool]
    conversation_history: Optional[List[Dict[str, str]]]
    original_query: Optional[str]
    trigger_plan_b: Optional[bool]

    # 상품 추천 관련
    vehicle_fitment: Optional[str] = None
    product_model_no: Optional[List[Dict]]
    product_hits: Optional[List[Dict]]
    neo4j_hits: Optional[Dict[str, Dict]]
    product_info: Optional[str]
    relevant_docs: Optional[Dict[str, Dict]]
    knowledge_hits: Optional[List[Dict]]
    knowledge_summary: Optional[str]