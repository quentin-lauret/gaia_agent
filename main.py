import requests
import gaia_agent
from dotenv import load_dotenv
import os
import time

load_dotenv()

base_url = os.getenv("BASE_URL")
questions_url = base_url + "questions"
submission_url = base_url + "submit"
questions = requests.get(questions_url)

def submit(answers: list[dict[str, str]]):
    body = {
    "username": "quentin-lauret",
    "agent_code": "https://huggingface.co/spaces/quentin-lauret/agent-course",
    "answers": answers
    }
    response = requests.post(submission_url, json=body)
    print("Task submitted :", response.json())

answers = []
for question in questions.json():
    print("Question :", question["question"])
    try:
        answer = gaia_agent.call_agent(question["question"])
    except Exception as e:
        print(e)
        continue
    print("Response :", answer)
    answers.append({"task_id": question["task_id"], "submitted_answer": answer})
submit(answers)
