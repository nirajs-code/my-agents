import json
from data.loader import ProfileData
from agent.tools import tools, TOOL_REGISTRY
from agent.prompts import system_prompt
from agent.evaluate import evaluate, rerun

MAX_TOOL_ITERATIONS = 10

class Me:
    def __init__(self, client, model: str, profile: ProfileData):
        self.client = client
        self.model = model
        self.profile = profile

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)

            if "parameters" in arguments and isinstance(arguments["parameters"], dict):
                arguments = arguments["parameters"]

            tool = TOOL_REGISTRY.get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def chat(self, message, history):
        messages = [{"role": "system", "content": system_prompt(self.profile)}] + history + [{"role": "user", "content": message}]
        done = False
        iterations = 0

        while not done and iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            response = self.client.chat.completions.create(model=self.model, messages=messages, tools=tools)
            finish_reason = response.choices[0].finish_reason
            response_message = response.choices[0].message

            if finish_reason == "tool_calls" and response_message.tool_calls:
                results = self.handle_tool_calls(response_message.tool_calls)
                messages.append(response_message)
                messages.extend(results)
            else:
                reply = response_message.content or ""
                evaluation = evaluate(self.client, self.model, self.profile, reply, message, history)
                if evaluation.is_acceptable:
                    print("Passed evaluation - returning reply")
                else:
                    print("Failed evaluation - retrying")
                    print(evaluation.feedback)
                    reply = rerun(self.client, self.model, self.profile, reply, message, history, evaluation.feedback)
                done = True

        return reply
