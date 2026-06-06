import json
import re
import structlog
from pydantic import BaseModel, ValidationError
from data.loader import ProfileData
from agent.prompts import evaluator_system_prompt, evaluator_user_prompt, system_prompt

log = structlog.get_logger()

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluate(client, model: str, profile: ProfileData, reply: str, message: str, history) -> Evaluation:
    messages = [
        {"role": "system", "content": evaluator_system_prompt(profile)},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content

    if not content:
        log.warning("evaluator_empty_response", model=model)
        return Evaluation(is_acceptable=True, feedback="empty response from evaluator — defaulting to accept")

    content = content.strip()

    # strip markdown code fences if the model wrapped the JSON
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)

    try:
        data = json.loads(content)
        return Evaluation(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        log.warning("evaluator_parse_failed", model=model, error=str(e), raw=content)
        return Evaluation(is_acceptable=True, feedback=f"parse error — defaulting to accept")


def rerun(client, model: str, profile: ProfileData, reply: str, message: str, history, feedback: str) -> str:
    updated = system_prompt(profile) + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated += f"## Your attempted answer:\n{reply}\n\n"
    updated += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated}] + history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
