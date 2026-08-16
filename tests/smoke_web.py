"""Smoke test of the web tools. read_pdf calls the Mistral OCR API."""
from gaia_agent.tools.web import fetch_webpage, read_pdf, extract_tables_from_url

if __name__ == "__main__":
    print(fetch_webpage.invoke({"url": "https://www.universetoday.com/"}))
    print(read_pdf.invoke({"url": "https://arxiv.org/pdf/2306.01116v1"}))
    print(extract_tables_from_url.invoke({"url": "https://en.wikipedia.org/w/index.php?oldid=1126540422"}))
