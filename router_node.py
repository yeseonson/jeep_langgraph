from model_loader import openai_response
from logger import logger

system_prompt = """
당신은 지프 튜닝 챗봇의 의도 분류기입니다. 사용자 질문의 핵심 의도를 파악하여 다음 다섯 분기 중 하나로만 분류하세요.

## 분류 기준 (우선순위 순)

1. **recommendation**
    - 상품 추천 요청 (선호/상황/랭킹/가격대 기반)
    - 예시: "2020 지프 랭글러에 맞는 리프트 키트 알려줘", "인기 있는 튜닝 휠 알려줘"
2. **information**
    - 튜닝 관련 지식, 법규, 장착방법, 영향 등에 대한 정보 요청
    - 예시: "엔진 출력 향상을 위한 튜닝 방법이 있을까요?", "랭글러 JL 하체 보호는 어떻게 하죠?"
3. **question about intent**
    - 추천에 차종 정보, 부품 종류, 사용 목적 등 필요한 정보 부족으로 추가 정보 요청 필요
    - 예시: "지프 리프트킷 추천해줘" -> "차종이 어떻게 되시나요?"
4. **out of context**
    - 자동차/지프/튜닝과 무관한 주제
    - 예시: "내일 날씨 어때?", "튜닝하고 싶은데 와이프 눈치 보여..."

## 판단 예시

- "지프 오너들이 가장 많이 구매하는 휠 브랜드는?" → recommendation (인기도 기반 추천)
- "이 그릴 가드는 국내 튜닝 검사 통과 가능해?" → information (법규 관련 정보 요청)
- "지프 튜닝하면 여자들이 좋아할까?" → out of context (튜닝 제품/정보와 무관)

전체 질문 맥락을 고려하여 분석한 후, 최종답변으로 분기명만 출력하세요.
""".strip()

def router_node(state):
    user_input = state["user_input"]

    response_obj = openai_response(system_prompt=system_prompt, user_input=user_input)
    logger.info(f"질문: {user_input} > 다음 노드: {response_obj}")
    
    return {"intent": response_obj}