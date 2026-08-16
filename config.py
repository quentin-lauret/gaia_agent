"""Reads the configuration of the project from the environment (.env).

Importing this module loads the .env file, so the other modules do not have to call
load_dotenv() themselves. Everything that is not a credential has a default : a missing
or empty variable keeps the value the project was written with.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def env_str(name: str, default: str) -> str:
    """Read a variable, falling back to the default when it is missing or empty."""
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


MISTRAL_API = os.getenv("MISTRAL_API")
HF_TOKEN = os.getenv("HF_TOKEN")

BASE_URL = env_str("BASE_URL", "")
GAIA_USERNAME = env_str("GAIA_USERNAME", "")
AGENT_CODE = env_str("AGENT_CODE", "")

GAIA_DATASET_URL = env_str(
    "GAIA_DATASET_URL",
    "https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation",
)
ATTACHMENTS_DIR = env_str(
    "ATTACHMENTS_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "attachments"),
)

CONTACT_EMAIL = env_str("CONTACT_EMAIL", "")
