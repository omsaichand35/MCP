from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

import asyncio
import json
import os

from MCP.TerminalMCP.terminal import run_command

app = Server("Terminal MCP")

@app.list_tools()
def list_tools() -> list[Tool]:
    return [
        Tool(
            name="runCommand",
            description="Runs the terminal commands.",
            inputSchema={
                "type": "string",
                "properties": {
                    "command": {"type": "string", "description": "The command to run."},
                },
                "required": ["command"],
            }
        )
    ]

@app.call_tool()
def call_tool(name: str, argument: dict) -> list[TextContent]:
    if name == "run_command":
        command = argument["command"]
        result = run_command(command)
        try:
            return [
                TextContent(
                    type="text",
                    text=result
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]

async def main():
    async with stdio_server() as (reader, writer):
        await app.run(reader, writer, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())