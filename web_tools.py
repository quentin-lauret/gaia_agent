"""Tools to read a web source in full, instead of relying on search snippets."""
from langchain.tools import tool
import io
import requests
import pandas as pd
from bs4 import BeautifulSoup
from file_tools import call_mistral, mistral

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) GAIA (quentin.lauret@epita.fr)"
MAX_CHARS = 6000
MAX_TABLES = 10
MAX_ROWS = 30
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "form"]


def _get_html(url: str) -> str:
    """Download a page. Returns the html or a string starting with 'Error:'."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    except requests.RequestException as e:
        return f"Error: could not reach {url} ({e})."
    if response.status_code != 200:
        return f"Error: {url} returned status {response.status_code}."
    return response.text


@tool
def fetch_webpage(url: str, offset: int = 0) -> str:
    """Read the full text of a web page. Use it to check a source found with the search tool,
    as search results only give short snippets. Long pages are truncated : call again with a
    bigger offset to read the next part. For a PDF url, use read_pdf instead."""
    html = _get_html(url)
    if html.startswith("Error:"):
        return html

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())

    window = text[offset:offset + MAX_CHARS]
    if not window:
        return f"The page has {len(text)} characters, there is nothing to read at offset {offset}."
    if offset + MAX_CHARS < len(text):
        window += f"\n[... truncated, call fetch_webpage again with offset={offset + MAX_CHARS} to read the next part ...]"
    return window


_pdf_cache: dict[str, list] = {}


@tool
def read_pdf(url: str, page: int = 0) -> str:
    """Read one page of a PDF document given its url, as markdown. Pages are numbered from 0."""
    if url not in _pdf_cache:
        result = call_mistral(
            mistral.ocr.process,
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": url},
        )
        if isinstance(result, str):
            return result
        _pdf_cache[url] = result.pages

    pages = _pdf_cache[url]
    if not pages:
        return f"Error: no content could be extracted from {url}."
    if page >= len(pages):
        return f"Error: this document only has {len(pages)} pages (numbered from 0)."
    return f"[Page {page} of {len(pages) - 1}]\n" + pages[page].markdown[:MAX_CHARS]


@tool
def extract_tables_from_url(url: str) -> str:
    """Extract the tables of a web page as markdown. Use it instead of fetch_webpage when the
    information you need is in a table, for example a discography, a ranking or statistics."""
    html = _get_html(url)
    if html.startswith("Error:"):
        return html

    try:
        frames = pd.read_html(io.StringIO(html))
    except ValueError:
        return f"No table found on {url}. Use fetch_webpage to read the page as text."
    except Exception as e:
        return f"Error: could not read the tables of {url} ({e})."

    parts = [f"{len(frames)} tables found."]
    for index, frame in enumerate(frames[:MAX_TABLES]):
        part = f"### Table {index} ({len(frame)} rows, {len(frame.columns)} columns)\n"
        part += frame.head(MAX_ROWS).to_markdown(index=False)
        if len(frame) > MAX_ROWS:
            part += f"\n[... {len(frame) - MAX_ROWS} more rows not shown ...]"
        parts.append(part)
    if len(frames) > MAX_TABLES:
        parts.append(f"[... {len(frames) - MAX_TABLES} more tables not shown ...]")
    return "\n\n".join(parts)


TOOLS = [fetch_webpage, read_pdf, extract_tables_from_url]

if __name__ == "__main__":
    print(fetch_webpage.invoke({"url": "https://www.universetoday.com/"}))
    print(read_pdf.invoke({"url": "https://arxiv.org/pdf/2306.01116v1"}))
    print(extract_tables_from_url.invoke({"url": "https://en.wikipedia.org/w/index.php?oldid=1126540422"}))
