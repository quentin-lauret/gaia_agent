import requests
import gaia_agent
import config

questions_url = config.BASE_URL + "questions"
submission_url = config.BASE_URL + "submit"
def submit(answers: list[dict[str, str]]):
    body = {
    "username": config.GAIA_USERNAME,
    "agent_code": config.AGENT_CODE,
    "answers": answers
    }
    response = requests.post(submission_url, json=body)
    print("Task submitted :", response.json())

def build_prompt(question: dict) -> str:
    """Build the agent prompt, telling it how to get the attached file if there is one."""
    prompt = question["question"]
    if question.get("file_name"):
        prompt += f"\n\nA file named {question['file_name']} is attached to this question." \
                  f" Call download_attachment with task_id='{question['task_id']}' to retrieve it."
    return prompt

def run_all():
    """Answer every question of the benchmark and submit the answers."""
    questions = requests.get(questions_url)
    answers = []
    for question in questions.json():
        print("Question :", question["question"])
        try:
            answer = gaia_agent.call_agent(build_prompt(question))
        except Exception as e:
            print(e)
            continue
        print("Response :", answer)
        answers.append({"task_id": question["task_id"], "submitted_answer": answer})
    submit(answers)

if __name__ == "__main__":
    run_all()
