from langgraph.graph import StateGraph, END, START
from jeepchat.nodes.information.nodes import retrieve, generate, query_rewrite, grade_documents, web_search
from jeepchat.nodes.information.router import decide_to_generate
from jeepchat.state import ChatState


# 그래프 생성
def build_information_graph():
    # 그래프 상태 초기화
    workflow = StateGraph(ChatState)
    
    # 노드 정의
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("query_rewrite", query_rewrite)
    workflow.add_node("web_search_node", web_search)
    workflow.add_node("generate", generate)
    
    # 엣지 연결
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    
    # 문서 평가 노드에서 조건부 엣지 추가
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "query_rewrite": "query_rewrite",
            "generate": "generate"
        }
    )
    
    # 엣지 연결
    workflow.add_edge("query_rewrite", "web_search_node")
    workflow.add_edge("web_search_node", "generate")
    workflow.add_edge("generate", END)
   
    # 그래프 컴파일
    app = workflow.compile()
   
    return app