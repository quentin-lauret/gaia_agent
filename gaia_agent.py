from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
import random
import string
from langgraph.prebuilt import ToolNode
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import tools_condition
from langchain_mistralai.chat_models import ChatMistralAI
import tools
from langfuse.langchain import CallbackHandler
from dotenv import load_dotenv
import os
from langchain_core.rate_limiters import InMemoryRateLimiter
from langgraph.types import RetryPolicy   # anciennement langgraph.pregel
import httpx

def retry_on_transient(exception: Exception) -> bool:
    """Retry on rate limits (429) and on the temporary server errors of the API (5xx)."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code == 429 or exception.response.status_code >= 500
    return isinstance(exception, (httpx.TimeoutException, httpx.ConnectError))

llm_retry = RetryPolicy(
    retry_on=retry_on_transient,
    max_attempts=6,
    initial_interval=10.0,
    backoff_factor=2.0,
    max_interval=120.0,
    jitter=True,
)

KEEP_FULL = 3

THINKING_PROMPT = "You are a general AI assistant." \
                "I will ask you a question. Report your thoughts, and give an answer" \
                "YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings." \
                "If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise." \
                "If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise." \
                "If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string." \
                "IMPORTANT: Never invent any response. Always use run_python for the mathematical, logic or programming tasks when relevant. Use the search_tool to find new information." \
                "If a file is attached to the question, call download_attachment first, then the reader tool it tells you to use." \
                "Never answer from a search snippet alone : open the source with fetch_webpage, read_pdf, or extract_tables_from_url when the data is in a table." \
                "For Wikipedia, call wikipedia_search first to get the exact title, and wikipedia_revision_at_date when the question is about a past version of a page."

FORMATTER_PROMPT = "You are a general AI assistant." \
"You will be given a question and a associated reasoning with an answer." \
"Extract the final response. Do not add any word." \
"If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise." \
"If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise." \
"If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string."

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.15
)

load_dotenv()

langfuse_handler = CallbackHandler()

chat = ChatMistralAI(api_key=os.getenv("MISTRAL_API"), model_name="mistral-large-latest", rate_limiter=rate_limiter)
chat = chat.bind_tools(tools.tools_list)
formatter = ChatMistralAI(api_key=os.getenv("MISTRAL_API"), model_name="mistral-medium-latest", rate_limiter=rate_limiter)


class AgentState(TypedDict):
    messages : Annotated[list[AnyMessage], add_messages]

def rename_duplicated_tool_calls(message: AIMessage, history: list[AnyMessage]) -> AIMessage:
    """Mistral sometimes reuses a tool call id it already used, and then rejects the
    conversation with 'Duplicate tool call id'. Give a new id to the duplicated calls.
    Done before the tools node runs, so the tool answers keep the same ids."""
    used = {call["id"] for message in history if isinstance(message, AIMessage) for call in message.tool_calls}
    for call in message.tool_calls:
        while call["id"] in used:
            call["id"] = "".join(random.choices(string.ascii_letters + string.digits, k=9))
        used.add(call["id"])
    return message

def run_thinker(state: AgentState):
    return {
        "messages" : [rename_duplicated_tool_calls(chat.invoke(state["messages"]), state["messages"])]
    }

def run_formatter(state: AgentState):
    question = state["messages"][1].content
    reasoning = state["messages"][-1].content
    result = formatter.invoke([
        SystemMessage(content=FORMATTER_PROMPT),
        HumanMessage(content=f"<Question> {question} </Question> <Answer> {reasoning}  </Answer>"),
    ])
    return {
        "messages" : result
    }

def clear_old_tools(state: AgentState):
    tools = [message for message in state["messages"] if isinstance(message, ToolMessage)]
    tools = tools[:-KEEP_FULL] if len(tools) > KEEP_FULL else []
    messages = [ToolMessage(content=f"[This tool call ({tool.name}) is too old and was deleted]", id=tool.id, name=tool.name, tool_call_id=tool.tool_call_id) for tool in tools]
    return {"messages" : messages}
    
builder = StateGraph(AgentState)

builder.add_node("llm", run_thinker, retry_policy=llm_retry)
builder.add_node("tools", ToolNode(tools.tools_list), retry_policy=llm_retry)
builder.add_node("clear_tools", clear_old_tools)
builder.add_node("formatter", run_formatter, retry_policy=llm_retry)

builder.add_edge(START, "llm")
builder.add_conditional_edges("llm", tools_condition, {"tools": "tools", END: "formatter"})
builder.add_edge("tools", "clear_tools")
builder.add_edge("clear_tools", "llm")

agent = builder.compile()


def call_agent(prompt: str) -> str:
    """Call the agent using a simple prompt, get the final response as a text."""
    response = agent.invoke(
    input={"messages" : [
        SystemMessage(content=THINKING_PROMPT),
        HumanMessage(content=prompt)]},
    config={"callbacks": [langfuse_handler]}
    )
    return response["messages"][-1].content