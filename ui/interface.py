import gradio as gr
from jeepchat.utils import generate_user_id
from jeepchat.config.constants import vehicle_codes, css
from jeepchat.ui.handlers import (
    run_pipeline_for_gradio,
    on_thread_select,
    on_new_thread,
    create_new_thread,
    initialize_interface
)
from jeepchat.services.chat_memory import ChatMemoryManager

chat_manager = ChatMemoryManager()

interface = gr.Blocks(css=css)

def create_chat_interface():
    with gr.Blocks(title="Jeep Chat", css=css) as interface:
        default_user = generate_user_id()

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Jeep Chat")
                user_id_text = gr.Textbox(label="사용자", value=default_user, interactive=False)
                thread_selector = gr.Dropdown(label="목록", choices=chat_manager.get_user_threads(default_user), allow_custom_value=True)
                thread_status = gr.Textbox(label="상태", interactive=False, visible=False)
                new_thread_btn = gr.Button("새 채팅")
                vehicle_selector = gr.Dropdown(
                    label = "차량 모델 선택",
                    choices=["전체"] + vehicle_codes,
                    value="전체",
                    interactive=True
                )
                
                # 협력업체 안내 섹션
                with gr.Group():
                    gr.HTML('<div class="partner-title">협력업체 안내</div>')
                    
                    with gr.Column(elem_classes="partner-card"):
                        gr.Markdown("### 오프로드모터스")
                        gr.Markdown("📍[위치](https://maps.app.goo.gl/C28trgycL3oZDujv8): 경기도 화성시 봉담읍 세자로 369-5")
                        gr.Markdown("🔗 [웹사이트](https://offroadmotors.kr)")
                        gr.Markdown("📱연락처: 0505-330-7252")
                    
                    with gr.Column(elem_classes="partner-card"):
                        gr.Markdown("### 오프로드코리아")
                        gr.Markdown("📍[위치](https://maps.app.goo.gl/ZDp63vU2Dp3JExYq9): 경기도 남양주시 석실로 336번길 30")
                        gr.Markdown("🔗 [웹사이트](http://off-roadkorea.com/index.html)")
                        gr.Markdown("📱연락처: 010-5224-9086 / 010-8704-8764")
                    
                    with gr.Column(elem_classes="partner-card"):
                        gr.Markdown("### 모든모터스")
                        gr.Markdown("📍[위치](https://maps.app.goo.gl/SgzKkfSdv4rauNQ66): 경기도 고양시 일산동구 견달산로 178-55")
                        gr.Markdown("🔗 [유튜브](https://www.youtube.com/@MODEUNMOTORS/)")
                        gr.Markdown("📱연락처: 010-4341-1941")
                
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
