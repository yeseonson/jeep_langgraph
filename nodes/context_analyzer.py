from jeepchat.core.logger import logger

def analyze_context(state):
    """맥락 분석 노드 - 이전 대화와 연관성 판단"""

    from jeepchat.services.chat_memory import ChatMemoryManager
    from jeepchat.services.model_loader import openai_response
    
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

            현재 질문:
            {user_input}

            위의 '이전 대화'와 '현재 질문'이 **맥락상 연관되어 있는지** 판단해 주세요.

            ※ 아래 기준을 모두 고려해 판단해 주세요.

            [연관성 판단 기준]

            1. **명시적 연속성**
            - 이전 대화에서 언급된 구체적인 차량 모델, 부품명, 제품군, 또는 튜닝 종류에 대한 후속 질문
            - 예: 같은 차종에 대해 성능, 설치법, 가격 등 상세 내용을 묻는 질문

            2. **주제 연속성**
            - 동일한 차량을 기준으로 하여, 유사한 목적(예: 오프로드 성능 개선)을 가진 질문
            - 동일한 제품군(예: 소프트탑, 서스펜션 등)에 대해 추가로 묻는 경우

            3. **맥락적 연관성**
            - 이전 추천, 정보, 설명을 기반으로 판단이 필요한 질문
            - 대화 흐름을 고려했을 때 자연스럽게 이어지는 후속 질문

            [비연관성 판단 기준]

            - 차량 모델이 변경되었고, 새로운 모델에 대해 다른 주제(부품/목적)를 묻는 경우
            - 제품 카테고리나 튜닝 목적이 완전히 바뀐 경우
            - 새로운 대화를 시작한 것처럼 보이는 경우 (예: 'JK의 데쓰워블 튜닝 추천')

            ---

            판단 결과를 다음 중 하나로만 출력하세요:
            'relevant' 또는 'not_relevant'
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
