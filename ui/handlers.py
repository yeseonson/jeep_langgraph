import gradio as gr
from typing import List, Dict

from jeepchat.logger import logger
from jeepchat.services.chat_memory import ChatMemoryManager
from jeepchat.services.chat_storage import S3ChatHistoryManager
from jeepchat.utils import generate_user_id, generate_thread_id, generate_message_id
from jeepchat.pipeline.main_graph import graph

memory_manager = ChatMemoryManager()
chat_manager = S3ChatHistoryManager()

def run_pipeline_for_gradio(message: str, history: List[Dict[str, str]], user_id: str, thread_id: str | None):
    try:
        if not thread_id:
            thread_id = generate_thread_id(user_id=user_id)

        message_id = generate_message_id(user_id=user_id)
        previous_messages = memory_manager.get_thread_messages(user_id, thread_id)
        is_clarify_followup = (
            previous_messages[-1].get("type") == "clarification"
            if previous_messages else False
        )

        result = graph.invoke(
            input={
                "user_id": user_id,
                "thread_id": thread_id,
                "message_id": message_id,
                "user_input": message,
                "is_clarify_followup": is_clarify_followup
            }
        )

        output = result.get("output", "응답을 생성할 수 없습니다.")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": output})

        updated_threads = chat_manager.get_user_threads(user_id)
        if thread_id not in updated_threads:
            updated_threads.append(thread_id)
        return "", history, gr.update(choices=updated_threads, value=thread_id)

    except Exception as e:
        logger.error(f"[Gradio run_pipeline] 오류 발생: {e}", exc_info=True)
        return "", history, gr.update(value=thread_id or "오류 발생")

def load_chat_history(user_id: str, thread_id: str) -> List[Dict[str, str]]:
    try:
        messages = chat_manager.get_thread_messages(user_id, thread_id)
        chat_history = []
        for msg_data in messages:
            raw_message = msg_data.get("message", {})
            message = raw_message.get("message") if isinstance(raw_message.get("message"), dict) else raw_message
            user_input = message.get("user_input", "").strip()
            output = message.get("output", "").strip()
            if user_input:
                chat_history.append({"role": "user", "content": user_input})
            if output:
                chat_history.append({"role": "assistant", "content": output})
        return chat_history
    except Exception as e:
        logger.error(f"[ERROR] 채팅 히스토리 로드 실패: {e}")
        return []

def on_thread_select(thread_id: str, user_id: str):
    if not thread_id:
        return [], ""
    history = load_chat_history(user_id, thread_id)
    status_msg = f"Thread {thread_id} 로드됨 ({len(history)//2}개 메시지 쌍)"
    return history, status_msg

def on_new_thread(user_id: str):
    new_thread_id = generate_thread_id(user_id=user_id)

    updated_threads = chat_manager.get_user_threads(user_id)

    return [], gr.update(choices=updated_threads + [new_thread_id], value=new_thread_id), f"새 Thread 생성됨: {new_thread_id}"

def create_new_thread(user_id: str):
    new_thread_id = generate_thread_id(user_id)
    updated_threads = chat_manager.get_user_threads(user_id)
    if new_thread_id not in updated_threads:
        updated_threads.append(new_thread_id)
    
    return gr.update(choices=updated_threads, value=new_thread_id), [], f"신규 Thread {new_thread_id} 생성됨"

def initialize_interface():
    user_id = generate_user_id()
    threads = chat_manager.get_user_threads(user_id)
    debug_msg = f"{user_id} 사용자에게 {len(threads)}개의 대화가 있습니다."
    return user_id, gr.update(choices=threads, value=None), gr.update(value=debug_msg)