# GAIA Agent

A tool-calling agent built with LangGraph and Mistral. It answers questions from the [GAIA benchmark](https://huggingface.co/datasets/gaia-benchmark/GAIA) for the Hugging Face Agents course. It searches the web, reads attached files, runs Python, and sends answers to the course scoring API.

## How it works

The agent is a LangGraph state machine with four nodes:

```
START → llm ⇄ tools → clear_tools → llm → formatter → END
```

- **llm**: `mistral-large-latest` connects to every tool. It reasons and decides which tool to use.
- **tools**: runs the requested tools and returns their output.
- **clear_tools**: replaces the content of every tool's answer except the last `KEEP_FULL` (3) with a placeholder. This keeps the context small over long tool chains.
- **formatter**: `mistral-medium-latest` reads the final reasoning and extracts the bare answer because GAIA scores an exact match (no articles, no units, no abbreviations).

## Tools

| Tool | File | Purpose |
| --- | --- | --- |
| `search_tool` | `tools.py` | Tavily web search, four results with a generated answer |
| `run_python` | `tools.py` | Runs Python in a subprocess (30 s timeout), returns stdout |
| `download_attachment` | `file_tools.py` | Fetches a question's attachment by `task_id`, returns its path and the reader to use |
| `read_table_file` | `file_tools.py` | Converts `.xlsx` / `.csv` to markdown tables |
| `read_text_file` | `file_tools.py` | Reads any text file, truncated at 6000 characters |
| `describe_image` | `file_tools.py` | Answers a question about an image via `mistral-medium-latest` |
| `transcribe_audio` | `file_tools.py` | Converts `.mp3` to text via `voxtral-mini-latest` |
| `fetch_webpage` | `web_tools.py` | Captures full page text, cleaned up, paginated with `offset` |
| `read_pdf` | `web_tools.py` | Reads one PDF page as markdown via `mistral-ocr-latest`, cached per URL |
| `extract_tables_from_url` | `web_tools.py` | Extracts page tables as markdown |
| `wikipedia_search` | `wiki_tools.py` | Finds the exact title of a page |
| `wikipedia_exists` | `wiki_tools.py` | Checks that a page exists |
| `retrieve_wikipedia_page` | `wiki_tools.py` | Gets title, summary, and section names |
| `get_wikipedia_sections` | `wiki_tools.py` | Gets content of named sections |
| `wikipedia_revision_at_date` | `wiki_tools.py` | Provides permalink to a page as it was on a specific date |

Attachments are downloaded from the `gaia-benchmark/GAIA` dataset instead of the scoring API. The `/files/{task_id}` endpoint returns 404 for every task. They are cached in `attachments/`.

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
```

| Variable | Used for | Default |
| --- | --- | --- |
| `MISTRAL_API` | Mistral API key for chat, OCR, vision, and audio | — |
| `TAVILY_API_KEY` | Tavily web search | — |
| `HF_TOKEN` | Hugging Face token to download the GAIA attachments | — |
| `BASE_URL` | Scoring API, must end with a slash | — |
| `GAIA_USERNAME` | Hugging Face username sent with the submission | — |
| `AGENT_CODE` | URL of the agent code sent with the submission | — |
| `GAIA_DATASET_URL` | Dataset folder the attachments are downloaded from | `.../gaia-benchmark/GAIA/resolve/main/2023/validation` |
| `ATTACHMENTS_DIR` | Where the attachments are cached | `attachments/` in the project |
| `CONTACT_EMAIL` | Address sent in the `User-Agent` of the web requests | — |
| `LANGFUSE_PUBLIC_KEY` | Langfuse tracing | — |
| `LANGFUSE_SECRET_KEY` | Langfuse tracing | — |
| `LANGFUSE_HOST` | Langfuse tracing | — |

`config.py` reads these variables and applies the defaults. The model names, limits, rate limiter, and retry policy remain in the code.

You must accept the terms of the gated `gaia-benchmark/GAIA` dataset with this token to download the attachments.

## Usage

Answer every question of the benchmark and submit the run:

```bash
python main.py
```

Ask a single question:

```python
import gaia_agent
print(gaia_agent.call_agent("How many studio albums did Mercedes Sosa release between 2000 and 2009?"))
```

Each tool module runs its own smoke test when executed directly:

```bash
python tools.py
python file_tools.py
python web_tools.py
python wiki_tools.py
```

## Files

| File | Role |
| --- | --- |
| `main.py` | Fetches the questions, runs the agent for each, and submits the answers |
| `config.py` | Loads the `.env` and exposes the configuration variables |
| `gaia_agent.py` | Contains graph, prompts, models, retry, and rate limiting |
| `tools.py` | Contains search and Python tools, assembles `tools_list` |
| `file_tools.py` | Handles attachment downloads and readers |
| `web_tools.py` | Reads web pages, PDFs, and tables |
| `wiki_tools.py` | Contains Wikipedia tools |