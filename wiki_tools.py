"""Tools to search and read Wikipedia, including older versions of a page."""
from langchain.tools import tool
import json
import requests
import wikipediaapi
import config

USER_AGENT = f"GAIA ({config.CONTACT_EMAIL})"
API_URL = "https://en.wikipedia.org/w/api.php"
MAX_SUMMARY = 2000
MAX_SECTION = 4000

wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language='en')


def _query(**params) -> dict:
    """Call the MediaWiki API. Raises requests exceptions, returns the parsed json."""
    params.update(action="query", format="json")
    response = requests.get(API_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    return response.json()


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia and return the titles of the matching pages with a short extract.
    Use it first to find the exact title of a page before reading it."""
    try:
        results = _query(list="search", srsearch=query, srlimit=5)["query"]["search"]
    except requests.RequestException as e:
        return f"Error: could not search Wikipedia ({e})."
    if not results:
        return f"No Wikipedia page found for '{query}'."

    return json.dumps([
        {
            "title": result["title"],
            "snippet": result["snippet"].replace('<span class="searchmatch">', "").replace("</span>", ""),
        }
        for result in results
    ])


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
        return "Error : The given page does not exist. Use wikipedia_search tool to find the exact title of a page."
    else:
        return json.dumps({"title": page.title, "summary" : page.summary[0:MAX_SUMMARY], "sections_names": [section.title for section in page.sections]})

@tool
def get_wikipedia_sections(page_name: str, sections_name : list[str]) -> str:
    """Retrieve the sections content based on their name."""
    page = wiki.page(page_name)
    if not page.exists():
        return "Error : The given page does not exist. Use wikipedia_search tool to find the exact title of a page."

    sections = []
    for section_name in sections_name:
        section = page.section_by_title(section_name)
        if section is None:
            sections.append({
                "section_name": section_name,
                "error": "No section with this exact name. Available sections : "
                         + ", ".join(s.title for s in page.sections),
            })
        else:
            sections.append({"section_name": section_name, "content": section.full_text()[:MAX_SECTION]})
    return json.dumps(sections)


@tool
def wikipedia_revision_at_date(page_name: str, date: str) -> str:
    """Find the version of a Wikipedia page as it was at a given date (format YYYY-MM-DD).
    Returns a permanent link to that old version, that you can then read with fetch_webpage
    or extract_tables_from_url. Use it when the question asks about a past version of a page."""
    try:
        pages = _query(
            prop="revisions", titles=page_name, rvlimit=1, rvdir="older",
            rvstart=f"{date}T23:59:59Z", rvprop="ids|timestamp",
        )["query"]["pages"]
    except requests.RequestException as e:
        return f"Error: could not reach Wikipedia ({e})."

    page = list(pages.values())[0]
    if "missing" in page or not page.get("revisions"):
        return f"Error: no version of '{page_name}' found before {date}. Check the title with wikipedia_search."

    revision = page["revisions"][0]
    return json.dumps({
        "title": page["title"],
        "revision_date": revision["timestamp"],
        "url": f"https://en.wikipedia.org/w/index.php?oldid={revision['revid']}",
    })


TOOLS = [wikipedia_search, wikipedia_exists, retrieve_wikipedia_page, get_wikipedia_sections, wikipedia_revision_at_date]

if __name__ == "__main__":
    print(wikipedia_search.invoke("Mercedes Sosa singer"))
    print(wikipedia_exists.invoke("Emmanuel Macron"))
    print(retrieve_wikipedia_page.invoke("Emmanuel Macron"))
    print(get_wikipedia_sections.invoke({"page_name": "Emmanuel Macron", "sections_name": ["Early life", "Nonexistent Section"]}))
    print(wikipedia_revision_at_date.invoke({"page_name": "Mercedes Sosa", "date": "2022-12-31"}))
