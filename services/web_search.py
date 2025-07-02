from jeepchat.config.prompts import web_search_query_generator_prompt
from jeepchat.services.model_loader import openai_response
from langchain_teddynote.tools.tavily import TavilySearch
from jeepchat.config.config import TAVILY_API_KEY
from tavily import TavilyClient

def web_search_tool(user_input: str, max_results: int = 3) -> str:
    web_search = TavilySearch(max_results=max_results, api_key=TAVILY_API_KEY)
    
    # 웹 검색 도구 실행
    return web_search.invoke({'query': user_input})


def format_search_results(response: dict) -> str:
    """Tavily 결과를 간결하게 마크다운 형식으로 정리"""
    if not response.get("results"):
        return "No results found."
    
    md = ["### Search Results:\n"]
    for idx, r in enumerate(response["results"], 1):
        title = r.get("title", "No title")
        content = r.get("content", "")
        md.append(f"**{idx}.** [{title}]")
        if content:
            md.append(f"> **Content:** {content}\n")
        md.append("")
    
    if response.get("answer"):
        md.append(f"### Answer:\n{response['answer']}\n")
    return "\n".join(md)


def tavily_search(query: str, num_results: int = 5) -> str:
    """Tavily로 웹 검색 실행 후 결과 정리"""
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        resp = tavily_client.search(
            query=query,
            max_results=num_results,
            search_depth="basic"
        )
        return format_search_results(resp)
    except Exception as e:
        return f"Error during Tavily search: {e}"


def tavily_search_node(question: str, category: str = None) -> str:
    """GPT로 쿼리 생성 + Tavily 검색"""

    query_for_tavily = openai_response(system_prompt=web_search_query_generator_prompt,
                                       user_prompt=f"Q: {question}\nA:",
                                       temperature=0)
    # 결과 1: 쿼리 기반 검색
    result_query = tavily_search(query_for_tavily)

    # 결과 2: 카테고리 기반 보조 검색
    result2_category = ""
    if category:
        category_query = f"{category}에 관한 튜닝 제약"
        result2_category = tavily_search(category_query)

    return result_query + result2_category
