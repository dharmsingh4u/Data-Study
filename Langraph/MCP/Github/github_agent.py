import streamlit as st
import json
from textwrap import dedent
import sys
import asyncio

# -------------------------
# ENV SETUP
# -------------------------
sys.path.insert(1, r'D:\Notebooks\LLM\env')
from enviorment import load_env
load_env()

# -------------------------
# LANGCHAIN / MCP IMPORTS
# -------------------------
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="GitHub MCP Agent", layout="wide")
st.title("🚀 GitHub MCP Agent (Streaming)")

# -------------------------
# SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = dedent("""
You are a coding assistant.
Help the user implement code changes safely and clearly.
When needed, use available tools to inspect files, run commands, and verify results.
Before making changes, briefly state what you will do.
After changes, summarize what was changed and why.

Now, act as if the user has asked the following:

Use my authenticated GitHub account.

First, call the repository listing tool and retrieve my repositories.
Only use the exact repository names returned by the tool.

Select the 3 most recently updated repositories from that list.
Do NOT invent, guess, or modify repository names.
Do NOT call issues or releases APIs.

Based only on those repositories, infer what I'm focusing on lately.

Respond in one paragraph.
""")

# -------------------------
# LOAD MCP TOOLS
# -------------------------
@st.cache_resource
def load_mcp_tools():
    with open(r'D:\Notebooks\Langraph\MCP\Github\mcp_config_git_hub.json', "r") as f:
        config = json.load(f)
    servers = config.get("mcpServers", {})
    client = MultiServerMCPClient(servers)

    # async get_tools wrapped in asyncio.run()
    tools = asyncio.run(client.get_tools())

    # Block problematic tools if needed
    blocked = ["list_releases", "list_issues", "list_branches", "list_pull_requests"]
    tools_filtered = [t for t in tools if t.name not in blocked]
    return tools_filtered

# -------------------------
# CREATE AGENT
# -------------------------
@st.cache_resource
def create_mcp_agent():
    model = ChatOpenAI(temperature=0)
    tools = load_mcp_tools()
    agent = create_agent(
        model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )
    return agent

agent = create_mcp_agent()

# -------------------------
# SESSION STATE
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------
# USER INPUT
# -------------------------
user_input = st.chat_input("Ask something about your GitHub repos...")

# -------------------------
# HELPER: RUN AGENT WITH STREAMING
# -------------------------
async def _run_agent_stream(prompt):
    """
    Async generator that streams agent output chunk by chunk.
    """
    full_response=''
    async for chunk in agent.astream({"messages": [{"role": "user", "content": prompt}]}):
        token = ""

        # 1️⃣ Try standard keys first
        if isinstance(chunk, dict):
            token = chunk.get("text") or chunk.get("output_text", "")
        
        # 2️⃣ Handle MCP structured response with 'model' -> 'messages'
        if not token and isinstance(chunk, dict) and "model" in chunk:
            messages = chunk["model"].get("messages", [])
            for msg in messages:
                # msg can be AIMessage object or dict
                if hasattr(msg, "content") and msg.content:
                    token += msg.content
                elif isinstance(msg, dict) and "content" in msg:
                    token += msg["content"]

        # Append to full response
        full_response += token
        yield full_response

def run_agent_stream(prompt):
    """
    Wrap async generator to synchronous Streamlit-friendly list of chunks.
    """
    async def _collect():
        chunks = []
        async for val in _run_agent_stream(prompt):
            chunks.append(val)
        return chunks
    return asyncio.run(_collect())

# -------------------------
# HANDLE USER MESSAGE
# -------------------------
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            # Run agent and stream responses
            stream_chunks = run_agent_stream(user_input)
            for chunk in stream_chunks:
                placeholder.markdown(chunk)

            st.session_state.messages.append({
                "role":"assistant",
                "content": stream_chunks[-1] if stream_chunks else ""
            })
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            placeholder.markdown(error_msg)
            st.session_state.messages.append({"role":"assistant","content":error_msg})

# -------------------------
# DEFAULT TEST BUTTON
# -------------------------
if st.button("⚡ Run GitHub Analysis"):
    test_prompt = """Use my authenticated GitHub account.

First, call the repository listing tool and retrieve my repositories.
Only use the exact repository names returned by the tool.

Select the 3 most recently updated repositories from that list.
Do NOT invent, guess, or modify repository names.
Do NOT call issues or releases APIs.

Based only on those repositories, infer what I'm focusing on lately.

Respond in one paragraph."""

    st.session_state.messages.append({"role":"user","content":test_prompt})

    with st.chat_message("user"):
        st.markdown(test_prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            stream_chunks = run_agent_stream(test_prompt)
            for chunk in stream_chunks:
                placeholder.markdown(chunk)

            st.session_state.messages.append({
                "role":"assistant",
                "content": stream_chunks[-1] if stream_chunks else ""
            })
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            placeholder.markdown(error_msg)
            st.session_state.messages.append({"role":"assistant","content":error_msg})