from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from jeepchat.state import ChatState
from jeepchat.nodes.information.chains import retrieval_grader, generate_answer, question_rewriter
from jeepchat.services.web_search import web_search_tool
from jeepchat.services.knowledge_search import hybrid_search, semantic_search
from jeepchat.logger import logger
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.utils import generate_message_id
from typing import Dict, Any


# 문서 검색 노드
def retrieve(state: ChatState):
    logger.info("==== RETRIEVE ====\n")
    user_input = state['user_input']
    
    # 문서 검색 수행
    documents = semantic_search(user_input)
    logger.info(f"[retrieve] 검색된 문서: {documents}...")
    return {'documents': documents}


# 답변 생성 노드
def generate(state: ChatState) -> Dict[str, Any]:
    logger.info("==== GENERATE ====\n")
    user_input = state['user_input']
    documents = state.get('documents', [])
    
    # RAG를 사용한 답변 생성
    # TODO: [CHECK] documents_text 작업이 필요한지 확인
    documents_text = ""
    if documents:
        documents_text = "\n\n".join([doc.get('document', '') for doc in documents])
    
    generation = generate_answer(user_input, documents_text)
    
    logger.info(f"[generate] 생성된 답변: {generation}")
    
    # 대화 메모리에 저장
    memory_manager = ChatMemoryManager()
    message_id = generate_message_id(user_id=state['user_id'])
    
    message_data = {
        "user_input": user_input,
        "output": generation,
        "timestamp": datetime.now().isoformat(),
        "type": "information"
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
    logger.info("==== [REWRITE QUERY] ====\n")
    user_input = state['user_input']
    
    # 질문 재작성
    rewritten = question_rewriter(user_input)
    logger.info(f"[QueryRewrite] 재작성된 질문: {rewritten}...")
    return {"query_rewritten": rewritten}

# 문서 평가 노드
def grade_documents(state: ChatState):
    logger.info("==== [CHECK DOCUMENT RELEVANCE TO QUESTION] ====\n")
    user_input = state['user_input']
    documents = state.get('documents', [])

    if not documents:
        return {'documents': [], 'web_search': 'Yes'}

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
    logger.info("==== [WEB SEARCH] ====\n")
    rewritten_user_input = state['query_rewritten']
    documents = state.get('documents', [])

    # 웹 검색 수행
    docs = web_search_tool(rewritten_user_input, max_results=3)
    
    # 검색 결과를 문서 형식으로 변환
    if docs and isinstance(docs, list):
        web_results = "\n".join(d.get('content', '') for d in docs)
        
        # 기존 형식과 맞춰서 Dict로 변환
        web_doc = {
            'document': web_results,
            'source': 'web_search'
        }
        
        # documents가 리스트인지 확인하고 추가
        if isinstance(documents, list):
            documents.append(web_doc)
        else:
            documents = [web_doc]
        
        logger.info(f"[Documents] 웹 검색 결과: {documents}...")

    return {"documents": documents}