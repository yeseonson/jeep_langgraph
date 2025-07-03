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

def classify_device_category_node(state: ChatState) -> ChatState:
    user_input = state.get("user_input", "")
    result = openai_response(
        user_input=user_input,
        system_prompt=device_category_classifier_prompt,
        temperature=0
    )
    return {
        **state,
        "device_category": result.strip()
    }


def is_minor_tuning_node(state: ChatState) -> ChatState:
    """
    승인이 필요한 장치 튜닝인지 판단하는 분기
    """
    user_input = state.get("user_input", "")

    example_result = hybrid_search_filtering(user_input, { "title": ["별표 1",] }, top_k=3)

    system_prompt = minor_tuning_classifier_prompt(example_result=example_result)
    result = openai_response(system_prompt=system_prompt, 
                             user_input=f"Q: {user_input} 질문은 경미한 장치 튜닝인가\nA:", 
                             temperature=0)
    return {
        **state,
        "is_minor_tuning": result.strip()
    }


def is_process_administrative_step_node(state: ChatState) -> ChatState:
    user_input = state.get("user_input", "")
    result = openai_response(user_input=user_input, 
                             system_prompt=administrative_step_classifier_prompt, 
                             temperature=0
                )
    return {
        **state,
        "regulation_admin_answer": result.strip()
    }


def major_tuning_node(state: ChatState) -> ChatState:
    user_id = state.get("user_id", "")
    thread_id = state.get("thread_id", "")

    user_input = state.get("user_input", "")
    example_result = hybrid_search_filtering(user_input, { "source": ["2024 자동차 튜닝 사례집"] })
    regulation_result = hybrid_search_filtering(user_input, { "source": ["2025 TS자동차튜닝사무편람"] }, top_k=3)
    structure_car_result = run_filtering_search({ "category": "자동차의 구조" })
    system_prompt = major_tuning_judgment_prompt(
        example_result=example_result, 
        regulation_result=regulation_result, 
        structure_car_result=structure_car_result
    )

    result = openai_response(
        user_input=f"Q: {user_input}\nA:", 
        system_prompt=system_prompt, 
        temperature=0, 
        model_id="gpt-4o"
    )

    message_id = generate_message_id(user_id=user_id)
    message = {
        "user_input": user_input,
        "output": result,
        "timestamp": datetime.now().isoformat(),
        "type": "regulation"
    }
    
    memory_manager.save_message(user_id, thread_id, message_id, message)
    logger.info(f"[major_tuning_node] 메모리 저장 완료 - message_id: {message_id}")

    return {
        **state,
        "output": result
    }


def minor_tuning_node(state: ChatState) -> ChatState:
    user_id = state.get("user_id", "")
    thread_id = state.get("thread_id", "")
    
    user_input = state.get("user_input", "")
    example_result = hybrid_search_filtering(user_input, { "source": ["2024 자동차 튜닝 사례집"] })
    trivial_result = run_filtering_search({ "name": "제4조" })
    structure_car_result = run_filtering_search({ "category": "자동차의 구조" })
    system_prompt = minor_tuning_judgment_prompt(
        trivial_result=trivial_result, 
        structure_car_result=structure_car_result,
        example_result=example_result
    )
    
    result = openai_response(
        system_prompt=system_prompt,
        user_input=f"Q: {user_input}\nA:",
        temperature=0,
        model_id="gpt-4o"
    )

    message_id = generate_message_id(user_id=user_id)
    message = {
        "user_input": user_input,
        "output": result,
        "timestamp": datetime.now().isoformat(),
        "type": "regulation"
    }
    
    memory_manager.save_message(user_id, thread_id, message_id, message)
    logger.info(f"[minor_tuning_node] 메모리 저장 완료 - message_id: {message_id}")

    return {
        **state,
        "output": result
    }


def non_approval_node(state: ChatState) -> ChatState:
    """
    분류 카테고리를 기준으로 구조와 관련된 정보를 들고와 웹검색의 정보와 합쳐 정보를 제공한다.
    """
    user_id = state.get("user_id", "")
    thread_id = state.get("thread_id", "")

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
    result = openai_response(system_prompt=system_prompt, 
                             user_input=f"Q: {user_input}\nA:", 
                             temperature=0, 
                             model_id="gpt-4o"
            )
    
    message_id = generate_message_id(user_id=user_id)
    message = {
        "user_input": user_input,
        "output": result,
        "timestamp": datetime.now().isoformat(),
        "type": "regulation"
    }
    
    memory_manager.save_message(user_id, thread_id, message_id, message)
    logger.info(f"[non_approval_node] 메모리 저장 완료 - message_id: {message_id}")

    return {
        **state,
        "output": result
    }


# 사무 내용 관련 정보 제공 최종 노드(사용 모델 4o)
def process_administrative_step_node(state: ChatState) -> ChatState:
    """
    시멘틱 서치와 웹검색을 활용하여 정보를 제공한다.
    """
    user_id = state.get("user_id", "")
    thread_id = state.get("thread_id", "")

    user_input = state.get("user_input", "")
    result_semantic_search = semantic_search(user_input)
    result_tavily_search = tavily_search_node(user_input)
    system_prompt = administrative_process_guidance_prompt(result_semantic_search=result_semantic_search, 
                                                           result_tavily_search=result_tavily_search)
    
    result = openai_response(
        system_prompt=system_prompt,
        user_input=f"Q: {user_input}\nA:",
        temperature=0,
        model_id="gpt-4o"
    )

    message_id = generate_message_id(user_id=user_id)
    message = {
        "user_input": user_input,
        "output": result,
        "timestamp": datetime.now().isoformat(),
        "type": "regulation"
    }
    
    memory_manager.save_message(user_id, thread_id, message_id, message)
    logger.info(f"[process_administrative_step_node] 메모리 저장 완료 - message_id: {message_id}")

    return {
        **state,
        "output": result
    }