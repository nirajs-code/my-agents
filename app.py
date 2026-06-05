import os
import gradio as gr
from dotenv import load_dotenv
from config import create_client
from data.loader import load_profile
from agent.chat import Me

load_dotenv(override=True)

if __name__ == "__main__":
    me = Me(client=create_client(), model=os.getenv("MODEL"), profile=load_profile())
    gr.ChatInterface(me.chat).launch()
