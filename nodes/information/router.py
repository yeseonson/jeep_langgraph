from jeepchat.state import ChatState

def decide_to_generate(state: ChatState):
    # 평가된 문서를 기반으로 다음 단계 결정
    print("==== [ASSESS GRADED DOCUMENTS] ====")
    
    # 웹 검색 필요 여부
    web_search = state['web_search']
    
    if web_search == 'Yes':
        # 웹 검색으로 정보 보강이 필요한 경우
        print(
            "[DECISION: INSUFFICIENT RELEVANT DOCUMENTS FOUND, INITIATING QUERY REWRITE FOR WEB SEARCH]"
        )
        # 쿼리 재작성 노드로 라우팅
        return "query_rewrite"
    else:
        # 관련 문서가 존재하므로 답변 생성 단계(generate)로 진행
        print("==== [DECISION: GENERATE] ====")
        return "generate"