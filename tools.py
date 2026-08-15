from langchain.tools import tool
import subprocess, sys
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
import file_tools
import web_tools
import wiki_tools

load_dotenv()
search_tool = TavilySearch(
        max_results=4,
        topic="general",
        include_answer=True,
        search_depth="basic",
    )


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


tools_list = [search_tool, run_python, *file_tools.TOOLS, *web_tools.TOOLS, *wiki_tools.TOOLS]

if __name__ == "__main__":
    print([getattr(t, "name", type(t).__name__) for t in tools_list])
    print(search_tool.invoke("Who is Macron ?"))
    print(run_python.invoke("print(sum(range(10)))"))
