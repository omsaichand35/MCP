import json
import os
import asyncio
import sys

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY")
)

async def main():
    server_path = os.path.join(os.path.dirname(__file__), "server.py")
    params = StdioServerParameters(
        command=sys.executable,
        args = [server_path],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            while True:
                tools = await session.list_tools()
                question = str(input("HI, which city shall I look up for the weather: "))

                if question == "exit":
                    break

                openai_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    } for tool in tools.tools
                ]
                messages = [{
                    "role": "user",
                    "content": question
                }]

                response = await client.chat.completions.create(
                    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                    messages=messages,
                    tools=openai_tools,
                )

                msg = response.choices[0].message

                if msg.tool_calls:
                    tool = msg.tool_calls[0]
                    args = json.loads(tool.function.arguments)
                    result = await session.call_tool(tool.function.name, args)

                    print(result.content[0].text)
                else:
                    print(msg.content)

if __name__ == "__main__":
        asyncio.run(main())