import gradio as gr
from jeepchat.utils import generate_user_id
from jeepchat.config.constants import vehicle_codes
from jeepchat.ui.handlers import (
    run_pipeline_for_gradio,
    on_thread_select,
    on_new_thread,
    create_new_thread,
    initialize_interface
)
from jeepchat.services.chat_memory import ChatMemoryManager

chat_manager = ChatMemoryManager()

interface = gr.Blocks(css="""
#chat-input textarea {
    height: 48px !important;
    padding-top: 8px;
    padding-bottom: 8px;
}
#send-btn {
    height: 48px !important;
}
""")

def create_chat_interface():
    with gr.Blocks(title="Jeep Chat") as interface:
        default_user = generate_user_id()

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Jeep Chat")
                user_id_text = gr.Textbox(label="사용자", value=default_user, interactive=False)
                thread_selector = gr.Dropdown(label="목록", choices=chat_manager.get_user_threads(default_user))
                thread_status = gr.Textbox(label="상태", interactive=False)
                new_thread_btn = gr.Button("새 채팅")
                vehicle_selector = gr.Dropdown(
                    label = "모델 선택",
                    choices=["전체"] + vehicle_codes,
                    value="전체",
                    interactive=True
                )
                # debug_info = gr.Textbox(label="디버그 정보", interactive=False, visible=True)
                
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="채팅", height=600, type="messages")
                with gr.Row():
                    msg = gr.Textbox(
                        label="메시지 입력", 
                        placeholder="메시지를 입력하세요.", 
                        lines=1, 
                        scale=4,
                        elem_id="chat-input"
                    )
                    send_btn = gr.Button("전송", scale=1, elem_id="send-btn")
                clear_btn = gr.Button("대화 초기화")

        thread_selector.change(fn=on_thread_select, inputs=[thread_selector, user_id_text], outputs=[chatbot, thread_status])
        send_btn.click(fn=run_pipeline_for_gradio, inputs=[msg, chatbot, user_id_text, thread_selector, vehicle_selector], outputs=[msg, chatbot, thread_selector])
        msg.submit(fn=run_pipeline_for_gradio, inputs=[msg, chatbot, user_id_text, thread_selector, vehicle_selector], outputs=[msg, chatbot, thread_selector])
        new_thread_btn.click(fn=on_new_thread, inputs=[user_id_text], outputs=[chatbot, thread_selector, thread_status])
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        new_thread_btn.click(fn=create_new_thread, inputs=[user_id_text], outputs=[thread_selector, chatbot, thread_status])

        interface.load(fn=initialize_interface, outputs=[user_id_text, thread_selector])

    return interface
