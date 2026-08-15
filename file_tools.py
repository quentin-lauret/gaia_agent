"""Tools to download and read the files attached to GAIA questions.

The scoring API's /files/{task_id} endpoint returns 404 for every task, so the
attachments are fetched from the gaia-benchmark/GAIA dataset instead.
"""
from langchain.tools import tool
import base64
import mimetypes
import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

mistral = Mistral(api_key=os.getenv("MISTRAL_API"))

DATASET_URL = "https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation"
ATTACHMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attachments")
TASK_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
EXTENSIONS = [".xlsx", ".png", ".mp3", ".py", ".csv", ".pdf", ".docx", ".txt", ".jsonld", ".pdb", ".zip"]
READER_HINT = {
    ".xlsx": "read_table_file", ".csv": "read_table_file",
    ".py": "read_text_file", ".txt": "read_text_file", ".jsonld": "read_text_file", ".pdb": "read_text_file",
    ".png": "describe_image", ".jpg": "describe_image", ".jpeg": "describe_image",
    ".mp3": "transcribe_audio",
}
MAX_CHARS = 6000
MAX_ROWS = 100


def call_mistral(action, **kwargs):
    """Call a method of the Mistral client, and turn its errors into a message for the agent
    instead of an exception, so that a failed call only costs one turn."""
    try:
        return action(**kwargs)
    except Exception as e:
        return f"Error: the Mistral API call failed ({type(e).__name__}: {str(e)[:300]})."


@tool
def download_attachment(task_id: str) -> str:
    """Download the file attached to a GAIA question, identified by its task_id.
    Returns the local path of the file and the name of the tool to read it with."""
    if not TASK_ID_RE.match(task_id.strip().lower()):
        return "Error: task_id must be a GAIA task identifier (36 characters, e.g. 7bd855d8-463d-4ed5-93ca-5fe35145f733)."
    task_id = task_id.strip().lower()
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    for extension in EXTENSIONS:
        path = os.path.join(ATTACHMENTS_DIR, task_id + extension)
        if os.path.exists(path):
            break
        response = requests.get(
            f"{DATASET_URL}/{task_id}{extension}",
            headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
            timeout=60,
        )
        if response.status_code == 200:
            with open(path, "wb") as f:
                f.write(response.content)
            break
    else:
        return f"Error: no attachment found for task_id {task_id}."

    reader = READER_HINT.get(extension, "read_text_file")
    return f"File downloaded to {path}. Use the {reader} tool to read it."


@tool
def read_table_file(path: str) -> str:
    """Read a spreadsheet (.xlsx) or a .csv file and return its content as markdown tables."""
    if not os.path.exists(path):
        return f"Error: no file at {path}. Use download_attachment to get the file first."
    try:
        if path.endswith(".csv"):
            sheets = {"csv": pd.read_csv(path)}
        else:
            sheets = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        return f"Error: could not read {path} ({e})."

    parts = []
    for name, frame in sheets.items():
        part = f"### Sheet {name} ({len(frame)} rows, {len(frame.columns)} columns)\n"
        part += frame.head(MAX_ROWS).to_markdown(index=False)
        if len(frame) > MAX_ROWS:
            part += f"\n[... {len(frame) - MAX_ROWS} more rows not shown ...]"
        parts.append(part)
    return "\n\n".join(parts)


@tool
def read_text_file(path: str) -> str:
    """Read a text file (.py, .txt, .json, .md, .csv) and return its content."""
    if not os.path.exists(path):
        return f"Error: no file at {path}. Use download_attachment to get the file first."
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return f"Error: could not read {path} ({e})."
    if len(content) > MAX_CHARS:
        return content[:MAX_CHARS] + f"\n[... truncated, {len(content) - MAX_CHARS} characters left ...]"
    return content


@tool
def describe_image(path: str, question: str) -> str:
    """Look at an image and answer a question about it. Ask for the details you need,
    for example the text written on it or the position of the objects it shows."""
    if not os.path.exists(path):
        return f"Error: no file at {path}. Use download_attachment to get the file first."
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    mime = mimetypes.guess_type(path)[0] or "image/png"

    result = call_mistral(
        mistral.chat.complete,
        model="mistral-medium-latest",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": f"data:{mime};base64,{encoded}"},
        ]}],
    )
    if isinstance(result, str):
        return result
    return result.choices[0].message.content


@tool
def transcribe_audio(path: str) -> str:
    """Transcribe an audio file (.mp3) and return the spoken text."""
    if not os.path.exists(path):
        return f"Error: no file at {path}. Use download_attachment to get the file first."
    with open(path, "rb") as f:
        result = call_mistral(
            mistral.audio.transcriptions.complete,
            model="voxtral-mini-latest",
            file={"file_name": os.path.basename(path), "content": f},
        )
    if isinstance(result, str):
        return result
    return result.text


TOOLS = [download_attachment, read_table_file, read_text_file, describe_image, transcribe_audio]

if __name__ == "__main__":
    print(download_attachment.invoke("7bd855d8-463d-4ed5-93ca-5fe35145f733"))
    print(read_table_file.invoke(os.path.join(ATTACHMENTS_DIR, "7bd855d8-463d-4ed5-93ca-5fe35145f733.xlsx")))
    print(download_attachment.invoke("99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3"))
    print(transcribe_audio.invoke(os.path.join(ATTACHMENTS_DIR, "99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3")))
    print(download_attachment.invoke("cca530fc-4052-43b2-b130-b30968d8aa44"))
    print(describe_image.invoke({
        "path": os.path.join(ATTACHMENTS_DIR, "cca530fc-4052-43b2-b130-b30968d8aa44.png"),
        "question": "What are the piece positions?",
    }))
    print(download_attachment.invoke("metadata"))
