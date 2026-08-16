"""Reads the configuration of the project from the environment (.env).

Importing this module loads the .env file, so the other modules do not have to call
load_dotenv() themselves. Everything that is not a credential has a default : a missing
or empty variable keeps the value the project was written with.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# src/gaia_agent/config.py -> gaia_agent/ : the root of the repository, where the
# .env sits and the attachments are cached, next to main.py.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Point at the file instead of letting load_dotenv() search upwards from the
# current directory, so the agent reads the same .env whatever it is run from.
# Variables already set in the real environment still win.
load_dotenv(REPO_ROOT / ".env")


def env_str(name: str, default: str) -> str:
    """Read a variable, falling back to the default when it is missing or empty."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


MISTRAL_API = os.getenv("MISTRAL_API")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

BASE_URL = env_str("BASE_URL", "")
GAIA_USERNAME = env_str("GAIA_USERNAME", "")
AGENT_CODE = env_str("AGENT_CODE", "")

GAIA_DATASET_URL = env_str(
    "GAIA_DATASET_URL",
    "https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation",
)
ATTACHMENTS_DIR = env_str("ATTACHMENTS_DIR", str(REPO_ROOT / "attachments"))

CONTACT_EMAIL = env_str("CONTACT_EMAIL", "")
