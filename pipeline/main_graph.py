from langgraph.graph import StateGraph, END
from jeepchat.state import ChatState
from jeepchat.pipeline.recommendation_graph import build_recommendation_graph
from jeepchat.pipeline.information_graph import build_information_graph
from jeepchat.pipeline.regulation_graph import build_regulation_graph
from jeepchat.logger import logger

# 노드 임포트
from jeepchat.nodes.context_analyzer import analyze_context
from jeepchat.nodes.router_node import router_node
from jeepchat.nodes.clarify_node import clarify_node
from jeepchat.nodes.fallback_node import fallback_node


def route_condition(state: ChatState) -> str:
    """라우터 노드의 결과에 따라 다음 노드를 결정"""
    intent = state.get("intent", "")
    is_clarify_followup = state.get("is_clarify_followup", False)
    clarify_attempts = state.get("clarify_attempts", 0)
    force_fallback = state.get("force_fallback", False)

    if force_fallback or (intent == "question about intent" and clarify_attempts >= 2):
        logger.error("[RouteCondition] clarify 루프 반복 또는 명시적 fallback 요청 → fallback 이동")
        return "fallback_node"

    if is_clarify_followup and intent == "question about intent":
        logger.error("[RouteCondition] clarify 후 intent 판단 실패 → fallback 이동")
        return "fallback_node"
    
    intent_map = {
        "recommendation": "recommendation_flow",
        "information": "information_flow",
        "regulation": "regulation_flow",
        "question about intent": "clarify_node",
        "out of context": "fallback_node"
    }

    next_node = intent_map.get(intent, "fallback_node")
    logger.info(f"[RouteCondition] intent: {intent} → next: {next_node}")
    return next_node


def clarify_condition(state: ChatState) -> str:
    if state.get("needs_rerouting", False):
        logger.info("[ClarifyCondition] 충분한 정보 확보됨 → 라우터 재진입")
        return "router_node"
    
    logger.info("[ClarifyCondition] 추가 질문 전송 완료 → 사용자 후속 질문 필요, 흐름 종료")
    return "END"


recommendation_graph = build_recommendation_graph()
information_graph = build_information_graph()
regulation_graph = build_regulation_graph()

# LangGraph 구성
builder = StateGraph(ChatState)

# 노드 추가
builder.add_node("context_analyzer", analyze_context)
builder.add_node("router_node", router_node)
builder.add_node("clarify_node", clarify_node)
builder.add_node("fallback_node", fallback_node)

builder.add_node("recommendation_flow", recommendation_graph)
builder.add_node("information_flow", information_graph)
builder.add_node("regulation_flow", regulation_graph)

builder.set_entry_point("context_analyzer")
builder.add_edge("context_analyzer", "router_node")

# 라우터에서 각 노드로 분기
builder.add_conditional_edges(
    "router_node",
    route_condition,
    {
        "recommendation_flow": "recommendation_flow",
        "information_flow": "information_flow",
        "regulation_flow": "regulation_flow",
        "clarify_node": "clarify_node", 
        "fallback_node": "fallback_node"
    }
)

builder.add_conditional_edges(
    "clarify_node",
    clarify_condition,
    {
        "router_node": "router_node",
        "END": END
    }
)

builder.add_edge("recommendation_flow", END)
builder.add_edge("information_flow", END)
builder.add_edge("regulation_flow", END)
builder.add_edge("fallback_node", END)

# 그래프 컴파일
graph = builder.compile()

if __name__ == "__main__":
    filename="graph_output.png"
    png_data = graph.get_graph().draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)
    print(f"이미지가 {filename}로 저장되었습니다.")