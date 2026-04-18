import sys
sys.path.insert(1, r'D:\Notebooks\LLM\env')
from enviorment import load_env
load_env()

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import SystemMessage, HumanMessage
from textwrap import dedent
import asyncio
import json

model = ChatOpenAI(model="gpt-4o")

# servers = {
#     "playwright": {
#         "command": "npx",
#         "args": ["@playwright/mcp@latest", "--browser=chrome"],
#         "transport": "stdio"
#     }
# }

import json
with open(r'D:\Notebooks\Langraph\MCP\Playright\mcp_config_playright.json', "r") as f:
        config = json.load(f)
servers =config.get("mcpServers", {})
for _, server in servers.items():
        if "command" in server and "transport" not in server:
            server["transport"] = "stdio"
        if "url" in server and "transport" not in server:
            server["transport"] = "streamable_http"

URL_PLANNER_PROMPT = dedent("""
    You are a web research planner. Given a user's task, return a JSON object with:
    - "urls": a list of 1-4 Google search URLs that would answer the task
    - "synthesis_instruction": a one-paragraph instruction for how to summarize the scraped data

    Rules:
    - Use Google search URLs like: https://www.google.com/search?q=...
    - Encode spaces as + in query strings
    - Return ONLY valid JSON, no markdown, no explanation

    Example output:
    {
      "urls": ["https://www.google.com/search?q=flights+London+to+Paris+price"],
      "synthesis_instruction": "Extract flight prices and return 2-3 options with costs."
    }
""")


def get_tool(tools, name):
    return next((t for t in tools if t.name == name), None)


def plan_urls(user_task: str) -> tuple[list[str], str]:
    """Synchronously ask the LLM to produce search URLs and synthesis instructions."""
    response = model.invoke([
        SystemMessage(content=URL_PLANNER_PROMPT),
        HumanMessage(content=user_task),
    ])
    data = json.loads(response.content)
    return data["urls"], data["synthesis_instruction"]


async def browse(nav, snapshot, url: str) -> str:
    """Navigate to a URL and return the accessibility tree snapshot as text."""
    await nav.ainvoke({"url": url})
    await asyncio.sleep(3)
    result = await snapshot.ainvoke({})
    return str(result)


async def run_research(
    user_task: str,
    urls: list[str],
    synthesis_instruction: str,
    on_status=None,
) -> str:
    """
    Browse each URL and synthesize an answer for user_task.
    on_status(msg: str) is called at each progress step (optional).
    Returns the final answer as a string.
    """
    def status(msg: str):
        if on_status:
            on_status(msg)

    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()

    nav      = get_tool(tools, "browser_navigate")
    snapshot = get_tool(tools, "browser_snapshot")

    if not nav or not snapshot:
        raise RuntimeError(f"Required Playwright tools not found. Available: {[t.name for t in tools]}")

    snapshots = []
    for i, url in enumerate(urls, 1):
        status(f"Browsing ({i}/{len(urls)}): {url}")
        data = await browse(nav, snapshot, url)
        snapshots.append(f"## Search result {i}:\n{data[:5000]}")

    combined = "\n\n".join(snapshots)
    status("Synthesizing answer...")

    response = model.invoke([
        SystemMessage(content=synthesis_instruction),
        HumanMessage(content=f"User task: {user_task}\n\n{combined}"),
    ])
    return response.content


# ── CLI entry point ────────────────────────────────────────────────────────────
async def _cli():
    user_task = input("What do you need help with? > ").strip()
    if not user_task:
        print("No task entered. Exiting.")
        return

    print("\nPlanning search URLs...")
    urls, synthesis_instruction = plan_urls(user_task)
    print("Will browse:\n  " + "\n  ".join(urls))

    result = await run_research(
        user_task, urls, synthesis_instruction,
        on_status=lambda msg: print(f"  {msg}"),
    )
    print(f"\n{result}")


if __name__ == "__main__":
    asyncio.run(_cli())
