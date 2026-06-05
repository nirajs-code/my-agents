from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import smtplib
from pypdf import PdfReader
import gradio as gr
import smtplib
from pydantic import BaseModel

load_dotenv(override=True)

def send_email(text):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_to = os.getenv("GMAIL_TO")
    msg = MIMEText(text)
    msg['Subject'] = 'Notification from My Agents'
    msg['From'] = gmail_user
    msg['To'] = gmail_to
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail_user, os.getenv("GMAIL_APP_PASSWORD"))
        server.sendmail(gmail_user, gmail_to, msg.as_string())
        print("Notification sent successfully.")


def record_user_details(email, name ="Name not provided", notes="not provided"):
   send_email(f"Recording {name} with email {email} and notes {notes}")
   return {"recorded": "ok"}

def record_unknown_question(question):
    send_email(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}


record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}]

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class Me:

    def __init__(self):
        self.model = os.getenv("MODEL")
        model = self.model
        if "gemini" in model:
            self.client = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))
        elif "llama" in model:
            self.client = OpenAI(api_key=os.getenv("OLLAMA_API_KEY"), base_url=os.getenv("OLLAMA_BASE_URL"))
        else:
            self.client = OpenAI()

        self.name = "Niraj Singh"
        self.linkedin = ""

        with open("sample-data/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        reader = PdfReader("sample-data/profile.pdf")
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text


    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            # Some Ollama models wrap arguments under a 'parameters' key instead of flat JSON
            if "parameters" in arguments and isinstance(arguments["parameters"], dict):
                arguments = arguments["parameters"]

            tool = globals().get(tool_name)
            result = tool(**arguments)  if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    

    def system_prompt(self):  
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career.\
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
        The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        The Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:"
        evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        evaluator_system_prompt += "\n\nRespond only with a JSON object in this exact format: {\"is_acceptable\": true or false, \"feedback\": \"your feedback here\"}, — no markdown, no extra text"
        return evaluator_system_prompt
    

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt
    
    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}, {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=Evaluation
        )
        evaluation_response = response.choices[0].message.parsed
        return evaluation_response
    
    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False

        while not done:
            response = self.client.chat.completions.create(model=self.model, messages=messages, tools=tools)
            finish_reason = response.choices[0].finish_reason
            response_message = response.choices[0].message

            if finish_reason=="tool_calls":
                tool_calls = response_message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(response_message)
                messages.extend(results) 
            else:
                reply = response_message.content
                evaluation = self.evaluate(reply, message, history)
                if evaluation.is_acceptable:
                    print("Passed evaluation - returning reply")
                else:
                    print("Failed evaluation - retrying")
                    print(evaluation.feedback)
                    reply = self.rerun(reply, message, history, evaluation.feedback)
                done = True   
        return reply
    
if __name__ == "__main__": 
    me = Me()
    gr.ChatInterface(me.chat).launch()