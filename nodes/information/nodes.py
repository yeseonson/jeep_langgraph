from concurrent.futures import ThreadPoolExecutor
from jeepchat.state import ChatState, Document
from jeepchat.nodes.information.chains import retrieval_grader, generate_answer, question_rewriter
from jeepchat.services.web_search import web_search_tool
from jeepchat.services.knowledge_search import hybrid_search, semantic_search
from jeepchat.logger import logger
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.utils import generate_message_id
from typing import Dict, Any


# 문서 검색 노드
def retrieve(state: ChatState):
    logger.info("\n==== RETRIEVE ====\n")
    user_input = state['user_input']
    
    # 문서 검색 수행
    documents = semantic_search(user_input)
    logger.info(f"[retrieve] 검색된 문서: {documents}...")
    return {'documents': documents}


# 답변 생성 노드
def generate(state: ChatState) -> Dict[str, Any]:
    logger.info("\n==== GENERATE ====\n")
    user_input = state['user_input']
    documents = state.get('documents', [])
    
    # RAG를 사용한 답변 생성
    generation = generate_answer(user_input, documents)
    
    # 대화 메모리에 저장
    memory_manager = ChatMemoryManager()
    message_id = generate_message_id(user_id=state['user_id'])
    
    message_data = {
        "user_input": user_input,
        "output": generation
    }
    
    memory_manager.save_message(
        user_id=state['user_id'],
        thread_id=state['thread_id'],
        message_id=message_id,
        message=message_data
    )
    
    logger.info(f"[generate] 메모리 저장 완료 - message_id: {message_id}")
    
    return {'output': generation}

# 쿼리 재작성 노드
def query_rewrite(state: ChatState):
    logger.info("\n==== [REWRITE QUERY] ====\n")
    user_input = state['user_input']
    
    # 질문 재작성
    rewritten = question_rewriter(user_input)
    logger.info(f"[QueryRewrite] 재작성된 질문: {rewritten}...")
    return {"user_input": rewritten}

# 문서 평가 노드
def grade_documents(state: ChatState):
    logger.info("\n==== [CHECK DOCUMENT RELEVANCE TO QUESTION] ====\n")
    user_input = state['user_input']
    documents = state['documents']

    # 평가 함수 (grade, doc 반환)
    def eval_doc(d):
        score = retrieval_grader(user_input, d['document'])
        grade = score.binary_score
        return (grade, d)

    # 병렬 평가: 최대 5개 동시 실행
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(eval_doc, documents))

    # 필터링 및 결과 집계
    filtered_docs = []
    relevant_doc_count = 0

    for grade, d in results:
        logger.info(f"문서: {d}\n관련 여부: {grade}")
        if grade == 'yes':
            logger.info("==== [GRADE: DOCUMENT RELEVANT] ====")
            filtered_docs.append(d)
            relevant_doc_count += 1
        else:
            logger.info("==== [GRADE: DOCUMENT NOT RELEVANT] ====")

    # 관련 문서가 없으면 웹 검색 수행
    web_search = 'Yes' if relevant_doc_count <= 3 else 'No'
    return {'documents': filtered_docs, 'web_search': web_search}


# 웹 검색 노드
def web_search(state: ChatState):
    logger.info("\n==== [WEB SEARCH] ====\n")
    user_input = state['user_input']
    documents = state['documents']

    # 웹 검색 수행
    docs = web_search_tool(user_input, max_results=3)
    
    # 검색 결과를 문서 형식으로 변환
    web_results = "\n".join(d['content'] for d in docs)
    web_results = Document(page_content=web_results)
    documents.append(web_results)
    logger.info(f"[Documents] 웹 검색 결과: {documents}...")

    return {"documents": documents}