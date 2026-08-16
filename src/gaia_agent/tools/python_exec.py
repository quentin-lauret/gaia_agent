"""Python execution tool, used for every calculation instead of the LLM's arithmetic."""
from langchain.tools import tool
import subprocess, sys


@tool
def run_python(code: str) -> str:
    """Execute Python code and return its stdout. Use this for any calculation
    or logic task. You must print() the result (only stdout is returned)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "Error: execution timed out after 30s"

    if result.returncode != 0:
        return f"Error (exit {result.returncode}):\n{result.stderr}"
    return result.stdout or "(no output)"
