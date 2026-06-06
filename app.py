import os
import gradio as gr
from dotenv import load_dotenv
from config import create_client
from data.loader import load_profile
from agent.chat import Me

load_dotenv(override=True)

if __name__ == "__main__":
    model = os.getenv("MODEL")
    eval_model = os.getenv("EVAL_MODEL", model)
    me = Me(client=create_client(model), model=model, eval_client=create_client(eval_model), eval_model=eval_model, profile=load_profile())
    share=os.getenv("GRADIO_SHARE", "false").lower() == "true"
    gr.ChatInterface(me.chat).launch(share=share)
