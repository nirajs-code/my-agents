import os
import gradio as gr
from dotenv import load_dotenv
from config import create_client
from data.loader import load_profile
from agent.chat import Me
from logger import configure_logging

load_dotenv(override=True)
configure_logging()

model = os.getenv("MODEL")
eval_model = os.getenv("EVAL_MODEL", model)
me = Me(
    client=create_client(model),
    model=model, 
    eval_client=create_client(eval_model), 
    eval_model=eval_model, 
    profile=load_profile()
    )

share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
username = os.getenv("GRADIO_USERNAME")
password = os.getenv("GRADIO_PASSWORD")
auth = (username, password) if username and password else None

gradio_chat = gr.ChatInterface(me.chat)

if __name__ == "__main__":
    gradio_chat.launch(share=share, auth=auth)
