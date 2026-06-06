import json
import time
from uuid import uuid4
import structlog
import structlog.contextvars
from data.loader import ProfileData
from agent.tools import tools, TOOL_REGISTRY
from agent.prompts import system_prompt
from agent.evaluate import evaluate, rerun

log = structlog.get_logger()
MAX_TOOL_ITERATIONS = 5
MAX_MESSAGE_LENGTH = 2000

class Me:
    def __init__(self, client, model: str, eval_client, eval_model:str, profile: ProfileData):
        self.client = client
        self.model = model
        self.eval_client = eval_client
        self.eval_model = eval_model
        self.profile = profile

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if "parameters" in arguments and isinstance(arguments["parameters"], dict):
                arguments = arguments["parameters"]

            tool = TOOL_REGISTRY.get(tool_name)
            if tool:
                log.info("tool_called", tool=tool_name)
                result = tool(**arguments)
            else:
                log.warning("unknown_tool", tool=tool_name)
                result = {"error": f"Tool '{tool_name}' not found"}

            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def chat(self, message, history):
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(conversation_id=str(uuid4())[:8])

        if len(message) > MAX_MESSAGE_LENGTH:
            log.warning("message_too_long", length=len(message), limit=MAX_MESSAGE_LENGTH)
            return f"Message too long ({len(message)} chars). Please keep it under {MAX_MESSAGE_LENGTH} characters."

        messages = [{"role": "system", "content": system_prompt(self.profile)}] + history + [{"role": "user", "content": message}]
        done = False
        iterations = 0
        reply = "I'm sorry, I wasn't able to complete your request."

        while not done and iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            t0 = time.perf_counter()
            response = self.client.chat.completions.create(model=self.model, messages=messages, tools=tools)
            latency = round(time.perf_counter() - t0, 3)

            finish_reason = response.choices[0].finish_reason
            response_message = response.choices[0].message
            usage = response.usage

            log.info(
                "llm_call",
                step="main",
                model=self.model,
                iteration=iterations,
                latency_s=latency,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                finish_reason=finish_reason,
            )

            if finish_reason == "tool_calls" and response_message.tool_calls:
                results = self.handle_tool_calls(response_message.tool_calls)
                messages.append(response_message)
                messages.extend(results)
            elif finish_reason == "length":
                log.warning("response_truncated")
                return "Response was too long, please try a more specific question."
            else:
                reply = response_message.content or ""
                evaluation = evaluate(self.eval_client, self.eval_model, self.profile, reply, message, history)
                if evaluation.is_acceptable:
                    log.info("evaluation_passed", eval_model=self.eval_model)
                else:
                    log.warning("evaluation_failed", eval_model=self.eval_model, feedback=evaluation.feedback)
                    reply = rerun(self.client, self.model, self.profile, reply, message, history, evaluation.feedback)
                done = True
        return reply
