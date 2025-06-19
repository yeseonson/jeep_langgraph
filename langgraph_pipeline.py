from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from context_analyzer import analyze_context
from logger import logger

# 노드 임포트
from router_node import router_node
from recommendation_node import recommendation_node
from clarify_node import clarify_node
from fallback_node import fallback_node

# 상태 정의
class ChatState(TypedDict):
    user_id: str
    thread_id: str
    message_id: str
    user_input: str

    intent: str
    output: str
    context_relevant: bool
    is_followup: bool

    original_query: Optional[str]
    conversation_history: list[dict[str, str]]
    is_clarify_followup: Optional[bool]


def temp_info_node(state: ChatState) -> dict[str, Any]:
    """임시 정보 노드"""
    logger.info(f"[INFO_NODE] 입력 상태: {state}")
    
    updated_state = {
        **state,
        "output": "정보 요청 기능은 현재 개발 중입니다.",
    }
    
    logger.info(f"[INFO_NODE] 출력 상태: {updated_state}")
    return updated_state

def route_condition(state: ChatState) -> str:
    """라우터 노드의 결과에 따라 다음 노드를 결정"""
    intent = state.get("intent", "")
    
    logger.info(f"[ROUTE_CONDITION] intent: {intent}")
    
    if intent == "recommendation":
        return "recommendation_node"
    elif intent == "information":
        return "info_node"
    elif intent == "question about intent":
        return "clarify_node"
    elif intent == "out of context":
        return "fallback_node"
    else:
        logger.warning(f"[ROUTE_CONDITION] 알 수 없는 intent: {intent} -> fallback_node")
        return "fallback_node"

# LangGraph 구성
builder = StateGraph(ChatState)

# 노드 추가
builder.add_node("context_analyzer", analyze_context)  # 맥락 분석 노드
builder.add_node("router_node", router_node)
builder.add_node("recommendation_node", recommendation_node)
builder.add_node("info_node", temp_info_node)
builder.add_node("clarify_node", clarify_node)
builder.add_node("fallback_node", fallback_node)

# 엔트리 포인트를 맥락 분석으로 설정
builder.set_entry_point("context_analyzer")

# 맥락 분석 후 라우터로
builder.add_edge("context_analyzer", "router_node")

# 라우터에서 각 노드로 분기
builder.add_conditional_edges(
    "router_node",
    route_condition,
    {
        "recommendation_node": "recommendation_node",
        "info_node": "info_node",
        "clarify_node": "clarify_node", 
        "fallback_node": "fallback_node"
    }
)

builder.add_edge("recommendation_node", END)
builder.add_edge("info_node", END)
builder.add_edge("clarify_node", END)
builder.add_edge("fallback_node", END)

# 그래프 컴파일
graph = builder.compile()

if __name__ == "__main__":
    filename="graph_output.png"
    png_data = graph.get_graph().draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)
    print(f"이미지가 {filename}로 저장되었습니다.")