from logger import logger

def analyze_context(state):
    """맥락 분석 노드 - 이전 대화와 연관성 판단"""

    from chat_memory import ChatMemoryManager
    from model_loader import openai_response
    
    user_input = state.get("user_input", "")
    user_id = state.get("user_id")
    thread_id = state.get("thread_id")
    is_clarify_followup = state.get("is_clarify_followup", False)

    logger.info(f"[CONTEXT_ANALYZER] 입력 분석: {user_input}")
    logger.info(f"[CONTEXT_ANALYZER] clarify 후속 여부: {is_clarify_followup}")

    context_relevant = False
    conversation_history = []

    if user_id and thread_id:
        memory_manager = ChatMemoryManager()
        previous_messages = memory_manager.get_thread_messages(user_id, thread_id)

        if previous_messages:
            for msg in previous_messages[-3:]:
                user_text = msg.get("user_input", "")
                system_text = msg.get("output", "")
                if user_text and system_text:
                    conversation_history.append({
                        "user": user_text,
                        "system": system_text
                    })

            logger.info(f"[CONTEXT_ANALYZER] conversation history: {conversation_history}")

            relevance_prompt = f"""
            이전 대화:
            {conversation_history}

            현재 질문: {user_input}

            현재 질문이 이전 대화와 맥락상 연관되어 있는지 판단해주세요.

            연관성 판단 기준:
            1. 직접적 언급
               - 이전 대화에서 언급된 구체적인 제품/부품명에 대한 추가 질문
               - 이전 대화에서 언급된 차종/모델에 대한 추가 질문
               - 이전 대화에서 언급된 튜닝 종류에 대한 추가 질문

            2. 주제의 연속성
               - 이전 대화에서 언급된 튜닝 관련 주제의 심화 질문
               - 이전 대화에서 언급된 제품의 구체적인 사양이나 가격 문의
               - 이전 대화에서 언급된 제품의 설치나 사용법 문의

            3. 맥락적 연관성
               - 이전 대화의 맥락을 이해해야 정확한 답변이 가능한 경우
               - 이전 추천이나 정보에 대한 추가 문의
               - 논리적으로 이어지는 질문이나 심화 내용

            연관성이 있으면 'relevant'로, 없으면 'not_relevant'로 답해주세요.
            """

            try:
                relevance_result = openai_response(
                    system_prompt=relevance_prompt,
                    user_input=user_input
                )
                context_relevant = relevance_result.strip().lower() == 'relevant'
                logger.info(f"[CONTEXT_ANALYZER] 연관성 분석 결과: {context_relevant}")

            except Exception as e:
                logger.error(f"[CONTEXT_ANALYZER] 연관성 분석 중 오류: {e}")

    new_state = dict(state)
    new_state.update({
        "context_relevant": context_relevant,
        "conversation_history": conversation_history,
        "is_followup": context_relevant,
        "output": ""
    })

    return new_state
