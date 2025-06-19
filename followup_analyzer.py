from model_loader import openai_response
from logger import logger

def is_followup_question(user_input: str, previous_messages: list, is_clarify: bool = False) -> bool:
    # clarify 노드에서 온 경우는 무조건 후속으로 처리
    if is_clarify:
        return True

    if not previous_messages:
        return False

    # 대화 이력 포맷
    conversation_context = "\n".join(
        f"사용자: {msg['user_input']}\n시스템: {msg['output']}"
        for msg in previous_messages if 'user_input' in msg and 'output' in msg
    )

    # 후속 질문 분석 프롬프트
    followup_analysis_prompt = f"""
    이전 대화:
    {conversation_context}

    현재 질문: {user_input}

    위 대화를 분석하여, 현재 질문이 이전 대화의 맥락을 이어받는 후속 질문인지 판단해주세요.
    다음 기준으로 판단해주세요:
    1. 이전 대화의 주제와 직접적으로 연관되어 있는지
    2. 이전 대화에서 언급된 내용에 대한 추가 질문인지
    3. 이전 대화의 맥락을 이해해야 정확한 답변이 가능한지

    답변은 'yes' 또는 'no'로만 해주세요.
    """

    followup_analysis = openai_response(system_prompt=followup_analysis_prompt, user_input="")
    is_followup = followup_analysis.lower().strip() == 'yes'

    logger.info(f"후속 질문 여부: {is_followup}")
    return is_followup
