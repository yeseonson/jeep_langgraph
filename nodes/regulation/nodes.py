from datetime import datetime
from jeepchat.state import ChatState
from jeepchat.utils import generate_message_id
from jeepchat.services.regulation_search import hybrid_search_filtering, run_filtering_search
from jeepchat.config.prompts import (device_category_classifier_prompt, 
                                     administrative_step_classifier_prompt,
                                     minor_tuning_classifier_prompt, 
                                     major_tuning_judgment_prompt,
                                     minor_tuning_judgment_prompt,
                                     non_approval_guidance_prompt,
                                     administrative_process_guidance_prompt
                                     )
from jeepchat.services.model_loader import openai_response
from jeepchat.services.web_search import tavily_search_node
from jeepchat.services.regulation_search import semantic_search
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.logger import logger

memory_manager = ChatMemoryManager()

def main_decision_node(state: ChatState) -> ChatState:
    user_input = state.get("user_input", "")

    # 1. 행정절차 여부 판단
    is_admin_process_result = openai_response(
        user_input=user_input,
        system_prompt=administrative_step_classifier_prompt,
        temperature=0
    ).strip()
    if is_admin_process_result == "네":
        return {
            **state,
            "regulation_admin_answer": is_admin_process_result,
            "early_exit": "process_admin"
        }

    # 2. 장치 분류
    device_category_result = openai_response(
        user_input=user_input,
        system_prompt=device_category_classifier_prompt,
        temperature=0
    ).strip()

    parts = device_category_result.split(".", 1)
    code = parts[0].strip() if len(parts) > 0 else ""
    print(code)
    if code in ['3', '6', '11', '15', '16', '17', '18', '19']:
        return {
            **state,
            "device_category": device_category_result,
            "early_exit": "non_approval"
        }

    # 3. 경미한 튜닝 여부 판단
    hybrid_result = hybrid_search_filtering(user_input, {"title": ["별표 1"]}, top_k=3)
    minor_tuning_prompt = minor_tuning_classifier_prompt(example_result=hybrid_result)

    is_minor_tuning_result = openai_response(
        system_prompt=minor_tuning_prompt,
        user_input=f"Q: {user_input} 질문은 경미한 장치 튜닝인가\nA:",
        temperature=0
    ).strip()

    return {
        **state,
        "regulation_admin_answer": is_admin_process_result,
        "device_category": device_category_result,
        "is_minor_tuning": is_minor_tuning_result
    }


def major_tuning_node(state: ChatState) -> ChatState:
    user_input = state.get("user_input", "")
    example_result = hybrid_search_filtering(user_input, { "source": ["2024 자동차 튜닝 사례집"] })
    regulation_result = hybrid_search_filtering(user_input, { "source": ["2025 TS자동차튜닝사무편람"] }, top_k=3)
    structure_car_result = run_filtering_search({ "category": "자동차의 구조" })
    
    system_prompt = major_tuning_judgment_prompt(
        example_result=example_result, 
        regulation_result=regulation_result, 
        structure_car_result=structure_car_result
    )

    return {
        **state,
        "system_prompt": system_prompt
    }


def minor_tuning_node(state: ChatState) -> ChatState:
    user_input = state.get("user_input", "")
    example_result = hybrid_search_filtering(user_input, { "source": ["2024 자동차 튜닝 사례집"] })
    trivial_result = run_filtering_search({ "name": "제4조" })
    structure_car_result = run_filtering_search({ "category": "자동차의 구조" })
    
    system_prompt = minor_tuning_judgment_prompt(
        trivial_result=trivial_result, 
        structure_car_result=structure_car_result,
        example_result=example_result
    )
    
    return {
        **state,
        "system_prompt": system_prompt
    }


def non_approval_node(state: ChatState) -> ChatState:
    """
    분류 카테고리를 기준으로 구조와 관련된 정보를 들고와 웹검색의 정보와 합쳐 정보를 제공한다.
    """
    user_input = state.get("user_input", "")
    device_category = state.get("device_category", "")
    category_label = ""
    if device_category and "." in device_category:
        category_label = device_category.split(".", 1)[1].strip()

    result_semantic_search = run_filtering_search({ "binary": "구조", "source": "2025 TS자동차튜닝사무편람" })
    result_tavily_search = tavily_search_node(user_input, category_label)
    system_prompt = non_approval_guidance_prompt(category=category_label, 
                                                 result_semantic_search=result_semantic_search, 
                                                 result_tavily_search=result_tavily_search)
    
    return {
        **state,
        "system_prompt": system_prompt
    }


# 사무 내용 관련 정보 제공 최종 노드(사용 모델 4o)
def process_administrative_step_node(state: ChatState) -> ChatState:
    """
    시멘틱 서치와 웹검색을 활용하여 정보를 제공한다.
    """
    user_input = state.get("user_input", "")
    result_semantic_search = semantic_search(user_input)
    result_tavily_search = tavily_search_node(user_input)
    system_prompt = administrative_process_guidance_prompt(result_semantic_search=result_semantic_search, 
                                                           result_tavily_search=result_tavily_search)
    return {
        **state,
        "system_prompt": system_prompt
    }

def openai_responses_node(state: ChatState) -> ChatState:
    user_id = state.get("user_id", "")
    thread_id = state.get("thread_id", "")
    user_input = state.get("user_input", "")
    system_prompt = state.get("system_prompt", "")
    is_followup = state.get("is_followup", "not_relevant")
    conversation_history = state.get("conversation_history", "")

    message_id = generate_message_id(user_id=user_id)
    

    history_context = ""
    if is_followup == "relevant" and conversation_history:
        recent_history = conversation_history[-3:]
        history_context = "\n".join(
            f"사용자: {item['user']}\n시스템: {item['system']}" for item in recent_history
        ) + "\n"

    result = openai_response(
    system_prompt=system_prompt,
    user_input=f"""
        # Here is the previous conversation context (if any):
        {history_context}
        
        # Here is the user's QUESTION that you should answer:
        Q: {user_input}\nA:""",
    temperature=0,
    model_id="gpt-4.1-mini"
    )

    message = {
        "user_input": user_input,
        "output": result,
        "timestamp": datetime.now().isoformat(),
        "type": "regulation"
    }
    memory_manager.save_message(user_id, thread_id, message_id, message)
    logger.info(f"[openai_responses_node] 메모리 저장 완료 - message_id: {message_id}")
    return {
        **state,
        "output": result
    }