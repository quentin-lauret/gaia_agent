"""GAIA benchmark agent : a LangGraph tool-calling agent built on Mistral.

This module is kept empty on purpose. Importing a submodule such as
gaia_agent.config must not pull in the heavy parts of the project (the Mistral
client, the Tavily search tool, the langfuse handler), which is what re-exporting
anything here would do.
"""
