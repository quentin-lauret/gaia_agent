"""The Mistral client shared by the tools that need it.

Both the file readers (vision, audio) and the web readers (OCR) call the Mistral
API, so the client lives here rather than in either of them.
"""
from mistralai.client import Mistral

from gaia_agent import config

mistral = Mistral(api_key=config.MISTRAL_API)


def call_mistral(action, **kwargs):
    """Call a method of the Mistral client, and turn its errors into a message for the agent
    instead of an exception, so that a failed call only costs one turn."""
    try:
        return action(**kwargs)
    except Exception as e:
        return f"Error: the Mistral API call failed ({type(e).__name__}: {str(e)[:300]})."
