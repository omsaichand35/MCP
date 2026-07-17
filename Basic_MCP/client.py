import asyncio
import os
import sys
import json
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession


llm_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY")
)

async def main():
    # Get the path to server.py relative to client.py
    server_path = os.path.join(os.path.dirname(__file__), "server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path]
    )

    print("Starting MCP Server...")
    async with stdio_client(server=server_params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            mcp_tools = await session.list_tools()

            openai_tools = []
            for tool in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            messages = [
                {"role": "user", "content": "Please analyze this text for me: 'Connecting custom tools is incredibly powerful.'"}
            ]
            print("Sending prompt and tools to the LLM.")

            completion = await llm_client.chat.completions.create(
                model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                messages=messages,
                tools=openai_tools,
                temperature=0.5,
                top_p=0.95,
                max_tokens=20480,
                extra_body={"chat_template_kwargs": {"enable_thinking":True, "reasoning_budget":16384}}
            )

            response = completion.choices[0].message

            reasoning = getattr(response, "reasoning", None)

            if reasoning:
                print("\n===== AI REASONING =====")
                print(reasoning)

            if response.tool_calls:
                print("\nAI called a tool\n")
                for tool_call in response.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    print(f"Tool executed: {name}")
                    print(f"Arguments Provided: {args}")

                    result = await session.call_tool(name, args)
                    print(f"\nResult returned from server: {result.content[0].text}")
            else:
                print("Final answer")
                print(response.content)

if __name__ == "__main__":
    asyncio.run(main())