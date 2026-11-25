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
    server_params = StdioServerParameters(command=sys.executable, args=[server_path])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = await session.list_tools()
            openai_tools = [{"type": "function",
                             "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}}
                            for t in mcp_tools.tools]

            scenario = (
                "A packet has arrived at the router. "
                "Source IP: 192.168.1.50, Destination IP: 10.5.5.5, Destination Port: 80, Total Size: 2500 bytes. "
                "You are the router's control plane. Process this packet. "
                "First, check if it's allowed through the firewall. "
                "If allowed, determine the route. "
                "Finally, determine if fragmentation is needed for that route's MTU. "
                "Provide a final summary of the packet's fate."
            )

            messages = [{"role": "user", "content": scenario}]

            print("Starting Router Simulation...\n")

            # We use a loop because the AI might need to call tools sequentially
            while True:
                completion = await llm_client.chat.completions.create(
                    model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                    messages=messages,
                    tools=openai_tools,
                    temperature=0.1,
                    max_tokens=4096,
                    extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 2048}
                )

                response = completion.choices[0].message
                messages.append(response)

                if response.tool_calls:
                    print(f"AI is calling {len(response.tool_calls)} tool(s)...")
                    for tool_call in response.tool_calls:
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        print(f" -> Executing {name} with args: {args}")
                        result = await session.call_tool(name, arguments=args)
                        server_response = result.content[0].text
                        print(f" <- Server returned: {server_response}")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": server_response
                        })
                else:
                    print("\n=== FINAL ROUTER DECISION ===")
                    print(response.content)
                    break


if __name__ == "__main__":
    asyncio.run(main())