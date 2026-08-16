"""Smoke test of the Wikipedia tools. Only calls the free MediaWiki API."""
from gaia_agent.tools.wiki import (
    wikipedia_search,
    wikipedia_exists,
    retrieve_wikipedia_page,
    get_wikipedia_sections,
    wikipedia_revision_at_date,
)

if __name__ == "__main__":
    print(wikipedia_search.invoke("Mercedes Sosa singer"))
    print(wikipedia_exists.invoke("Emmanuel Macron"))
    print(retrieve_wikipedia_page.invoke("Emmanuel Macron"))
    print(get_wikipedia_sections.invoke({"page_name": "Emmanuel Macron", "sections_name": ["Early life", "Nonexistent Section"]}))
    print(wikipedia_revision_at_date.invoke({"page_name": "Mercedes Sosa", "date": "2022-12-31"}))
