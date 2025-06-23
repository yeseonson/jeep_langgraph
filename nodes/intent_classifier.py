from jeepchat.services.model_loader import openai_response

SYSTEM_PROMPT = """
당신은 지프 튜닝 챗봇의 의도 분류기입니다. 사용자 질문의 핵심 의도를 파악하여 다음 다섯 분기 중 하나로만 분류하세요.

## 분류 기준 (우선순위 순)

1. **recommendation**
    - 상품 추천 요청 (선호/상황/랭킹/가격대 기반)
    - 예시: "2020 지프 랭글러에 맞는 리프트 키트 알려줘", "인기 있는 튜닝 휠 알려줘"
2. **information**
    - 튜닝 관련 지식, 법규, 장착방법, 영향 등에 대한 정보 요청
    - 예시: "엔진 출력 향상을 위한 튜닝 방법이 있을까요?", "랭글러 JL 하체 보호는 어떻게 하죠?"
3. **question about intent**
    - 차종 정보, 부품 종류, 사용 목적 등 답변에 필요한 정보 부족으로 추가 정보 요청 필요
    - 예시: "튜닝 휠 어떤 게 좋아?" -> "차종이 어떻게 되시나요?"
4. **out of context**
    - 자동차/지프/튜닝과 무관한 주제
    - 예시: "내일 날씨 어때?", "튜닝하고 싶은데 와이프 눈치 보여..."

전체 질문 맥락을 고려하여 분석한 후, 최종답변으로 분기명만 출력하세요.
""".strip()

def classify_intent(user_input: str, context: str = "", is_clarify: bool = False) -> str:
    prompt = f"{SYSTEM_PROMPT}\n{context}"

    if is_clarify:
        prompt += """
        이 질문은 이전에 추가 정보를 요청한 후속 질문입니다.
        이전 대화의 맥락을 고려하여, 사용자의 의도를 정확하게 파악해주세요.
        예를 들어:
        - 이전에 "어떤 종류의 튜닝을 원하시나요?"라고 물었고, 사용자가 "서스펜션 튜닝"이라고 답했다면
          이는 서스펜션 튜닝에 대한 recommendation 의도로 분류해야 합니다.
        - 이전에 "어떤 모델의 지프를 가지고 계신가요?"라고 물었고, 사용자가 "랭글러 JL"이라고 답했다면
          이는 랭글러 JL에 대한 recommendation 의도로 분류해야 합니다.
        """
    elif context:
        prompt += """
        이전 대화와 현재 질문의 연관성을 분석해주세요:
        1. 현재 질문이 이전 대화의 주제와 직접적으로 연관되어 있는지
        2. 이전 대화에서 언급된 내용에 대한 추가 질문인지
        3. 이전 대화의 맥락을 이해해야 정확한 답변이 가능한지

        연관성이 있다고 판단되면, 이전 대화의 맥락을 고려하여 분류해주세요.
        """

    response = openai_response(system_prompt=prompt, user_input=user_input)
    return response.strip()