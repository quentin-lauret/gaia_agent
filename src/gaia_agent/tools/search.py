"""Web search tool, used to find the sources the other tools then read in full."""
from langchain_tavily import TavilySearch

from gaia_agent import config

# The key is passed explicitly rather than read from the environment by TavilySearch
# itself : that only worked as long as config (which loads the .env) happened to be
# imported first.
search_tool = TavilySearch(
        tavily_api_key=config.TAVILY_API_KEY,
        max_results=4,
        topic="general",
        include_answer=True,
        search_depth="basic",
    )
