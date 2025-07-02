from langgraph.graph import StateGraph, END
from jeepchat.state import ChatState
from jeepchat.logger import logger

from jeepchat.nodes.regulation.nodes import (
    is_process_administrative_step_node,
    process_administrative_step_node,
    classify_device_category_node,
    non_approval_node,
    is_minor_tuning_node,
    minor_tuning_node,
    major_tuning_node
)

def build_regulation_graph() -> StateGraph:
    builder = StateGraph(ChatState)

    builder.add_node("is_process_admin", is_process_administrative_step_node)
    builder.add_node("classify_device", classify_device_category_node)
    builder.add_node("check_minor", is_minor_tuning_node)
    builder.add_node("minor", minor_tuning_node)
    builder.add_node("major", major_tuning_node)
    builder.add_node("non_approval", non_approval_node)
    builder.add_node("process_admin", process_administrative_step_node)

    # 분기 로직 정의
    def route_admin_check(state: ChatState) -> str:
        answer = state.get("regulation_admin_answer", "")
        return "process_admin" if answer in ("네", "예") else "classify_device"
    
    def route_device_category(state: ChatState) -> str:
        device_category = state.get("device_category", "")
        parts = device_category.split(".", 1)

        code = parts[0].strip() if len(parts) > 0 else ""
        label = parts[1].strip() if len(parts) > 1 else ""

        logger.info(f"[2차 분류/튜닝 승인 관련 법령 질문] 질문의 장치 분류: {label or '알 수 없음'}")
        
        return "non_approval" if code in ['3', '6', '11', '15', '16', '17', '18', '19'] else "check_minor"


    def route_minor_check(state: ChatState) -> str:
        return "minor" if state.get("is_minor_tuning", "") == "네" else "major"

    # 연결 설정
    builder.set_entry_point("is_process_admin")
    builder.add_conditional_edges("is_process_admin", route_admin_check, {
        "process_admin": "process_admin",
        "classify_device": "classify_device"
    })
    builder.add_conditional_edges("classify_device", route_device_category, {
        "non_approval": "non_approval",
        "check_minor": "check_minor"
    })
    builder.add_conditional_edges("check_minor", route_minor_check, {
        "minor": "minor",
        "major": "major"
    })

    builder.add_edge("process_admin", END)
    builder.add_edge("minor", END)
    builder.add_edge("major", END)
    builder.add_edge("non_approval", END)

    return builder.compile()
