import asyncio
import json
import os

from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

from filesystem import *

app = Server("File System MCP")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_files",
            description="List all files in the current directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path":{
                        "type": "string",
                        "description": "Directory path relative to the workspace."
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file in the current directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write a file in the current directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to the workspace."},
                    "data": {"type": "string", "description": "Instruction on what to write into the file."}
                },
                "required": ["path", "data"]
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory for the current workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["path"]
            },
        ),
        Tool(
            name="delete_file",
            description="Delete a files and directories in the current directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="tree",
            description="Display a tree of files in the current workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="rename",
            description="Rename a file in the current workspace.Can also change its relative path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_path": {"type": "string", "description": "Directory path relative to the workspace."},
                    "new_path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["old_path", "new_path"]
            }
        ),
        Tool(
            name="copy",
            description="Copy a file or directory to another location in the current workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_path": {"type": "string", "description": "Source path relative to the workspace."},
                    "new_path": {"type": "string", "description": "Destination path relative to the workspace."}
                },
                "required": ["old_path", "new_path"]
            }
        ),
        Tool(
            name="search",
            description="Recursively searches for files and directories "
                        "inside the workspace using a glob pattern. "
                        "Examples: '*.py', '*.txt', '*notes*'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern to search for files and directories"},
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["pattern", "path"]
            }
        ),
        Tool(
            name="search_content",
            description="Recursively searches for files and directories for the query content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query content relative to the workspace."},
                    "path": {"type": "string", "description": "Directory path relative to the workspace."}
                },
                "required": ["query", "path"]
            }
        ),
        Tool(
            name="file_info",
            description="Get the metadata about a file or a directory in the workspace.",
            inputSchema={
                "type": "object",
                "properties":{
                    "path": {"type": "string", "description": "File or directory path related to the workspace."}
                },
                "required": ["path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_files":
        path = arguments["path"]
        try:
            files = list_files(path)
            return [
                TextContent(
                    type="text",
                    text="\n".join(files),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "read_file":
        path = arguments["path"]
        try:
            content = read_file(path)
            return [
                TextContent(
                    type="text",
                    text=content
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "write_file":
        path = arguments["path"]
        try:
            content = arguments["data"]
            write_file(path, content)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully wrote to {path}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "create_directory":
        path = arguments["path"]
        try:
            create_directory(path)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully created the directory {path}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "delete_file":
        path = arguments["path"]
        try:
            delete_file(path)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully deleted the file {path}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "tree":
        path = arguments["path"]
        try:
            content = tree(path)
            return [
                TextContent(
                    type="text",
                    text=content
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "rename":
        old_path = arguments["old_path"]
        new_path = arguments["new_path"]
        try:
            rename(old_path, new_path)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully renamed {old_path} to {new_path}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "copy":
        old_path = arguments["old_path"]
        new_path = arguments["new_path"]
        try:
            copy(old_path, new_path)
            return [
                TextContent(
                    type="text",
                    text=f"Successfully copied {old_path} to {new_path}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "search":
        path = arguments["path"]
        pattern = arguments["pattern"]
        try:
            content = search(pattern, path)
            if not content:
                results = "No matches found."
            else:
                results = "\n".join(content)
            return [
                TextContent(
                    type="text",
                    text=results
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "search_content":
        path = arguments["path"]
        query = arguments["query"]
        try:
            content = search_content(query, path)
            if content:
                results = "\n".join(content)
            else:
                results = "No matches found."
            return [
                TextContent(
                    type="text",
                    text=results
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=str(e)
                )
            ]
    elif name == "file_info":
        path = arguments["path"]
        try:
            content = file_info(path)
            result = json.dumps(content, indent=2)
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
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())

