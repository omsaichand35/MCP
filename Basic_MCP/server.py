import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize the server
app = Server("Basic-mcp-server")

# define tools available to the llm
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_text",
            description="Analyze the text and returns character and word count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to analyze."}
                },
                "required": ["text"]
            }
        )
    ]

# Handle the execution of the tool
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "analyze_text":
        raise ValueError(f"Unknown tool: {name}")
    text = arguments.get("text", "")
    word_count = len(text.split())
    char_count = len(text)

    print(f"Processing text with {word_count} words and {char_count} characters", file=sys.stderr)

    return [
        TextContent(
            type="text",
            text=f"Analysis complete. Words: {word_count}, Characters: {char_count}"
        )
    ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())