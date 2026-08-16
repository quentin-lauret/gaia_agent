"""Smoke test of the search and python tools. Calls the Tavily API."""
from gaia_agent.tools import tools_list
from gaia_agent.tools.search import search_tool
from gaia_agent.tools.python_exec import run_python

if __name__ == "__main__":
    print([getattr(t, "name", type(t).__name__) for t in tools_list])
    print(search_tool.invoke("Who is Macron ?"))
    print(run_python.invoke("print(sum(range(10)))"))
