from langchain.tools import tool
import subprocess, sys
import wikipediaapi
import json
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()
search_tool = TavilySearch(
        max_results=4,
        topic="general",
        include_answer=True,
        search_depth="basic",
    )



wiki = wikipediaapi.Wikipedia(user_agent='GAIA (quentin.lauret@epita.fr)', language='en')


@tool
def wikipedia_exists(page_name: str) -> str:
    """Check the existence of a Wikipedia page. Return True if the page exists, False otherwise"""
    page = wiki.page(page_name)
    return str(page.exists())

@tool
def retrieve_wikipedia_page(page_name: str) -> str:
    """Retrieve a wikipedia page. Return the title, summary and sections titles."""
    page = wiki.page(page_name)
    if not page.exists():
        return "Error : The given page does not exist. Use wikipedia_search tool to check the existence of a page."
    else:
        return json.dumps({"title": page.title, "summary" : page.summary[0:60], "sections_names": [section.title for section in page.sections]})

@tool
def get_wikipedia_sections(page_name: str, sections_name : list[str]) -> str:
    """Retrieve the sections content based on their name."""
    page = wiki.page(page_name)
    if not page.exists():
        return "Error : The given page does not exist. Use wikipedia_search tool to check the existence of a page."
    sections = [{"section_name" : section_name, "content" : page.section_by_title(section_name)._text} for section_name in sections_name]
    return json.dumps(sections)

@tool
def run_python(code: str) -> str:
    """Execute Python code and return its stdout. Use this for any calculation
    or logic task. You must print() the result (only stdout is returned)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        return "Error: execution timed out after 30s"

    if result.returncode != 0:
        return f"Error (exit {result.returncode}):\n{result.stderr}"
    return result.stdout or "(no output)"

#, wikipedia_exists, retrieve_wikipedia_page, get_wikipedia_sections
tools_list = [run_python, search_tool]

if __name__ == "__main__":
    print(search_tool.invoke("Who is Macron ?"))
    print(wikipedia_exists.invoke("Emmanuel Macron"))
    print(retrieve_wikipedia_page.invoke("Emmanuel Macron"))
    print(get_wikipedia_sections.invoke({"page_name": "Emmanuel Macron", "sections_name" : ["Early life", "Notes"]}))