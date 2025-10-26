from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import sys
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
sys.path.insert(1, r'C:\Users\Dharmendra Vartika\LLM\env')
from enviorment import load_env
load_env()
import os 
import asyncio
model =ChatOpenAI(model="gpt-4o")

async def main():
     client=MultiServerMCPClient(
        {
            "Math":{
                "command":"python",
                "args":["mathserver.py"], ## Ensure correct absolute path
                "transport":"stdio",
            
            },
            "stock": {
                "url": "http://localhost:8000/mcp",  # Ensure server is running here
                "transport": "streamable_http",
            }

        }
    )
     tools=await client.get_tools()
     agent=create_react_agent(model,tools)
     math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]})
     print("Math response:", math_response['messages'][-1].content)

     weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the price of QSI stock?"}]}
        )
     print("Weather response:", weather_response['messages'][-1].content)
asyncio.run(main())
