from pydantic import BaseModel
from data.loader import ProfileData
from agent.prompts import evaluator_system_prompt, evaluator_user_prompt, system_prompt


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluate(client, model: str, profile: ProfileData, reply: str, message: str, history) -> Evaluation:
    messages = [
        {"role": "system", "content": evaluator_system_prompt(profile)},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=Evaluation,
    )
    return response.choices[0].message.parsed


def rerun(client, model: str, profile: ProfileData, reply: str, message: str, history, feedback: str) -> str:
    updated = system_prompt(profile) + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated += f"## Your attempted answer:\n{reply}\n\n"
    updated += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated}] + history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
