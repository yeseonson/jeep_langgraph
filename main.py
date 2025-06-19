from langgraph_pipeline import graph
from langchain_core.runnables import RunnableConfig
from chat_memory import ChatMemoryManager
from config import GPT_4O_MINI_MODEL_ID
from logger import logger 
from generate_id import generate_user_id, generate_thread_id, generate_message_id
from typing import cast

memory_manager = ChatMemoryManager()

def run_interactive_chat():
    user_id = generate_user_id()
    thread_id = generate_thread_id()
    
    configure = cast(RunnableConfig, {
        "configurable": {
            "thread_id": thread_id
        }
    })

    while True:
        user_input = input("\n질문을 입력하세요 (종료: 'quit'): ")
        if user_input.lower() == 'quit':
            break 
            
        try:
            message_id = generate_message_id()
            
            # 이전 상태 확인
            memory_manager = ChatMemoryManager()
            previous_messages = memory_manager.get_thread_messages(user_id, thread_id)
            
            is_clarify_followup = False
            if previous_messages:
                is_clarify_followup = True
            
            # 그래프 실행 - 맥락 분석부터 자동으로 시작
            result = graph.invoke(
                input={
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "user_input": user_input,
                    "is_clarify_followup": is_clarify_followup
                }, 
                config=configure
            )
            
            output = result.get('output', '응답을 생성할 수 없습니다.')
            print(f"\n{GPT_4O_MINI_MODEL_ID}: {output}")
            
        except Exception as e:
            logger.error(f"오류 발생: {e}", exc_info=True)
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    run_interactive_chat()