import asyncio
import os
import json
import sys

from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

api_key = os.environ.get("NVIDIA_API_KEY")
if not api_key:
    raise RuntimeError("Set the NVIDIA_API_KEY environment variable before running this client.")

llm_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

async def main():
    server_path = os.path.join(os.path.dirname(__file__), "server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path]
    )

    print("Starting subnet MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            init_response = await session.initialize()
            mcp_tools = await session.list_tools()
            openai_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in mcp_tools.tools]

            messages = [
                {
                    "role": "user",
                    "content": "I am configuring a new router for a lab environment using the 10.50.0.0/22 block. Please calculate the subnet details for me."
                }
            ]

            print("Asking AI to analyze the network topology...\n")

            completion = await llm_client.chat.completions.create(
                model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                messages=messages,
                tools=openai_tools,
                temperature=0.6,
                top_p=0.95,
                max_tokens=20480
            )

            response_msg = completion.choices[0].message

            if response_msg.tool_calls:
                for tool_call in response_msg.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    print(f"[{name}] called by AI with arguments: {args}")

                    result = await session.call_tool(name, args)
                    print("Raw output from the MCP server.")
                    print(result.content[0].text)
            else:
                print("The AI didn't use the tool. Response:", response_msg.content)

if __name__ == "__main__":
    asyncio.run(main())