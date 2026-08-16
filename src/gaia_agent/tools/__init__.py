"""Every tool the agent can call, gathered in tools_list.

The order matters : it is the order the tools are shown to the model in, so keep
new tools grouped with the module they come from.
"""
from gaia_agent.tools.search import search_tool
from gaia_agent.tools.python_exec import run_python
from gaia_agent.tools import files, web, wiki

tools_list = [search_tool, run_python, *files.TOOLS, *web.TOOLS, *wiki.TOOLS]
