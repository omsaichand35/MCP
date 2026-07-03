import asyncio
import json
import os
import sys

from openai import AsyncOpenAI
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="YOUR_API_KEY"
)


async def main():

    server_path = os.path.join(
        os.path.dirname(__file__),
        "server.py"
    )

    params = StdioServerParameters(
        command=sys.executable,
        args=[server_path]
    )

    async with stdio_client(params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # Discover MCP tools
            tools_response = await session.list_tools()

            # Convert MCP tools into OpenAI-compatible tools
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in tools_response.tools
            ]

            messages = [
                {
                    "role": "system",
                    "content": (
                        """You are a filesystem agent with access to MCP tools.
                            Your job is to fully complete the user's request.
                            Rules:
                            1. Use filesystem tools whenever the task requires reading,
                               writing, moving, renaming, searching, or inspecting files.
                            2. For multi-step tasks, track every requirement from the
                               user's request.
                            3. After performing filesystem mutations, verify the final
                               state using an appropriate inspection tool such as:
                               - tree
                               - list_files
                               - read_file
                               - file_info
                            4. Before giving a final answer, compare the verified
                               filesystem state against every requirement in the
                               original user request.
                            5. If any requirement is incomplete or incorrect:
                               - do not finish
                               - call the necessary tools
                               - verify again
                            6. Never claim an operation succeeded unless a tool result
                               confirms it.
                            7. Never invent the current filesystem structure.
                            8. Continue until the complete request is satisfied or
                               a tool error makes completion impossible.
                            """
                    )
                }
            ]

            while True:

                question = await asyncio.to_thread(
                    input,
                    "\nYou: "
                )

                if question.lower().strip() in {
                    "exit",
                    "quit"
                }:
                    break

                messages.append(
                    {
                        "role": "user",
                        "content": question
                    }
                )

                # Agent loop
                while True:

                    response = await client.chat.completions.create(
                        model=(
                            "nvidia/"
                            "nemotron-3-nano-omni-30b-a3b-reasoning"
                        ),
                        messages=messages,
                        tools=openai_tools
                    )

                    assistant_message = (
                        response.choices[0].message
                    )

                    # Save assistant response
                    messages.append(
                        assistant_message.model_dump(
                            exclude_none=True
                        )
                    )

                    # No tool call means final answer
                    if not assistant_message.tool_calls:

                        verification_msg = messages + [
                           {
                               "role": "system",
                               "content": """
                                            Before finishing, verify whether the user's latest request
                                            has been fully completed.
                                            Compare:
                                            1. Every requirement in the latest user request
                                            2. All tool calls already performed
                                            3. All tool results and verified filesystem state
                                            If everything is complete, respond exactly:
                                            TASK_COMPLETE
                                            If anything is incomplete, respond exactly:
                                            TASK_INCOMPLETE: <short explanation>
                               """
                           }
                        ]
                        verification_reponse = await client.chat.completions.create(
                            model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
                            messages=verification_msg,
                        )
                        verification = (
                            verification_reponse
                            .choices[0]
                            .message
                            .content
                            .strip()
                        )
                        print(f"\n[Verification] {verification}")
                        if verification.startswith("TASK_COMPLETE"):
                            print("\nAssistant:", assistant_message.content)
                            break

                        else:
                            messages.append(
                                {
                                    "role": "system",
                                    "content": f"""
                            Verification found the task incomplete.

                            Reason:
                            {verification}

                            Continue working on the original user request.
                            Use the available tools to fix the missing requirements.
                            Do not stop until the task is verified.
                            """
                                }
                            )
                            continue
                    # Execute every requested tool
                    for tool_call in assistant_message.tool_calls:

                        tool_name = (
                            tool_call.function.name
                        )

                        tool_args = json.loads(
                            tool_call.function.arguments
                        )

                        print(
                            f"\n[Tool Call] {tool_name}"
                        )

                        print(
                            f"[Arguments] {tool_args}"
                        )

                        result = await session.call_tool(
                            tool_name,
                            tool_args
                        )

                        tool_result = "\n".join(
                            content.text
                            for content in result.content
                            if hasattr(content, "text")
                        )

                        print(
                            f"[Tool Result]\n{tool_result}"
                        )

                        # Critical step:
                        # send tool result back to LLM
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result
                            }
                        )


if __name__ == "__main__":
    asyncio.run(main())