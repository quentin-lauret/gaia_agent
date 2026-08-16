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

All tool modules live in `src/gaia_agent/tools/`, and `tools/__init__.py` gathers them into `tools_list`.

| Tool | Module | Purpose |
| --- | --- | --- |
| `search_tool` | `tools/search.py` | Tavily web search, four results with a generated answer |
| `run_python` | `tools/python_exec.py` | Runs Python in a subprocess (30 s timeout), returns stdout |
| `download_attachment` | `tools/files.py` | Fetches a question's attachment by `task_id`, returns its path and the reader to use |
| `read_table_file` | `tools/files.py` | Converts `.xlsx` / `.csv` to markdown tables |
| `read_text_file` | `tools/files.py` | Reads any text file, truncated at 6000 characters |
| `describe_image` | `tools/files.py` | Answers a question about an image via `mistral-medium-latest` |
| `transcribe_audio` | `tools/files.py` | Converts `.mp3` to text via `voxtral-mini-latest` |
| `fetch_webpage` | `tools/web.py` | Captures full page text, cleaned up, paginated with `offset` |
| `read_pdf` | `tools/web.py` | Reads one PDF page as markdown via `mistral-ocr-latest`, cached per URL |
| `extract_tables_from_url` | `tools/web.py` | Extracts page tables as markdown |
| `wikipedia_search` | `tools/wiki.py` | Finds the exact title of a page |
| `wikipedia_exists` | `tools/wiki.py` | Checks that a page exists |
| `retrieve_wikipedia_page` | `tools/wiki.py` | Gets title, summary, and section names |
| `get_wikipedia_sections` | `tools/wiki.py` | Gets content of named sections |
| `wikipedia_revision_at_date` | `tools/wiki.py` | Provides permalink to a page as it was on a specific date |

Attachments are downloaded from the `gaia-benchmark/GAIA` dataset instead of the scoring API. The `/files/{task_id}` endpoint returns 404 for every task. They are cached in `attachments/`.

## Setup

The project is a package under `src/`, so install it before running it. The editable
install reads its dependencies from `requirements.txt`:

```bash
pip install -e .
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

`src/gaia_agent/config.py` reads these variables and applies the defaults. It loads the `.env` sitting at the root of the repository, so the agent reads the same configuration whatever directory it is run from. The model names, limits, rate limiter, and retry policy remain in the code.

You must accept the terms of the gated `gaia-benchmark/GAIA` dataset with this token to download the attachments.

## Usage

Answer every question of the benchmark and submit the run:

```bash
python main.py
```

Ask a single question:

```python
from gaia_agent.agent.graph import call_agent
print(call_agent("How many studio albums did Mercedes Sosa release between 2000 and 2009?"))
```

The smoke tests in `tests/` exercise each group of tools against the real APIs. Only
`smoke_wiki.py` is free to run; the others spend Mistral and Tavily credits:

```bash
python tests/smoke_wiki.py
python tests/smoke_search.py
python tests/smoke_files.py
python tests/smoke_web.py
```

## Layout

```
main.py                         entry point, runs and submits the benchmark
pyproject.toml                  package definition, dependencies from requirements.txt
src/gaia_agent/
├── config.py                   loads the .env and exposes the configuration
├── benchmark.py                fetches the questions, runs the agent, submits the answers
├── agent/
│   ├── prompts.py              the thinker and formatter system prompts
│   └── graph.py                the LangGraph state machine, models, retry, rate limiting
└── tools/
    ├── __init__.py             assembles tools_list
    ├── mistral_client.py       the Mistral client shared by the vision, audio and OCR tools
    ├── search.py               Tavily search
    ├── python_exec.py          Python execution
    ├── files.py                attachment download and readers
    ├── web.py                  web pages, PDFs, tables
    └── wiki.py                 Wikipedia
tests/                          smoke tests, one per group of tools
attachments/                    cache of the downloaded attachments (gitignored)
```