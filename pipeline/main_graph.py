from langgraph.graph import StateGraph, END
from jeepchat.schema import ChatState
from jeepchat.pipeline.recommendation_graph import build_recommendation_graph
from typing import Any

# 노드 임포트
from jeepchat.nodes.context_analyzer import analyze_context
from jeepchat.nodes.router_node import router_node
from jeepchat.nodes.clarify_node import clarify_node
from jeepchat.nodes.fallback_node import fallback_node

def temp_information_node(state: ChatState) -> dict[str, Any]:
    return {
        **state,
        "output": "정보 요청 기능은 현재 개발 중입니다.",
    }

def temp_regulation_node(state: ChatState) -> dict[str, Any]:
    return {
        **state, 
        "output": "규제 정보 기능은 현재 개발 중입니다."
    }

def route_condition(state: ChatState) -> str:
    """라우터 노드의 결과에 따라 다음 노드를 결정"""
    intent = state.get("intent", "")
    
    if intent == "recommendation":
        return "recommendation_flow"
    elif intent == "information":
        return "info_node"
    elif intent == "question about intent":
        return "clarify_node"
    elif intent == "out of context":
        return "fallback_node"
    else:
        return "fallback_node"

recommendation_graph = build_recommendation_graph()

# LangGraph 구성
builder = StateGraph(ChatState)

# 노드 추가
builder.add_node("context_analyzer", analyze_context)
builder.add_node("router_node", router_node)
builder.add_node("information_node", temp_information_node)
builder.add_node("regulation_node", temp_regulation_node)
builder.add_node("clarify_node", clarify_node)
builder.add_node("fallback_node", fallback_node)
builder.add_node("recommendation_flow", recommendation_graph)

builder.set_entry_point("context_analyzer")
builder.add_edge("context_analyzer", "router_node")

# 라우터에서 각 노드로 분기
builder.add_conditional_edges(
    "router_node",
    route_condition,
    {
        "recommendation_flow": "recommendation_flow",
        "information_node": "information_node",
        "regulation_node": "regulation_node",
        "clarify_node": "clarify_node", 
        "fallback_node": "fallback_node"
    }
)

builder.add_edge("recommendation_flow", END)
builder.add_edge("information_node", END)
builder.add_edge("regulation_node", END)
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