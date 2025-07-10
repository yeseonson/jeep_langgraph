from langgraph.graph import StateGraph, END
from jeepchat.state import ChatState

# 세분화된 추천 노드들
from jeepchat.nodes.recommendation.product_search_node import product_search_node
from jeepchat.nodes.recommendation.neo4j_search_node import neo4j_search_node, neo4j_plan_b_node
from jeepchat.nodes.recommendation.format_product_info_node import format_product_info_node
from jeepchat.nodes.recommendation.grade_products_node import grade_products_node
from jeepchat.nodes.recommendation.knowledge_search_node import knowledge_search_node
from jeepchat.nodes.recommendation.summarize_knowledge_node import summarize_knowledge_node
from jeepchat.nodes.recommendation.generate_response_node import generate_response_node

def build_recommendation_graph():
    builder = StateGraph(ChatState)

    builder.add_node("product_search", product_search_node)
    builder.add_node("grade_products", grade_products_node)
    builder.add_node("neo4j_search", neo4j_search_node)
    builder.add_node("format_product_info", format_product_info_node)
    builder.add_node("neo4j_plan_b_search", neo4j_plan_b_node)
    builder.add_node("knowledge_search", knowledge_search_node)
    builder.add_node("summarize_knowledge", summarize_knowledge_node)
    builder.add_node("generate_response", generate_response_node)

    builder.set_entry_point("product_search")

    builder.add_edge("product_search", "grade_products")

    builder.add_conditional_edges(
        "grade_products",
        plan_b_condition,
        {
            "normal": "neo4j_search",
            "plan_b": "neo4j_plan_b_search"
        }
    )
    builder.add_edge("neo4j_search", "format_product_info")
    builder.add_edge("neo4j_plan_b_search", "format_product_info")
    builder.add_edge("format_product_info", "knowledge_search")
    builder.add_edge("knowledge_search", "generate_response")
    # builder.add_edge("summarize_knowledge", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile()

def plan_b_condition(state: ChatState) -> str:
    return "plan_b" if state.get("trigger_plan_b") else "normal"