from jeepchat.ui.interface import create_chat_interface

if __name__ == "__main__":
    interface = create_chat_interface()
    interface.launch(server_name="0.0.0.0", share=True, debug=True)
