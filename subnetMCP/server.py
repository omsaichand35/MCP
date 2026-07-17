import asyncio
import sys
import ipaddress

from fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent


app = Server("Subnet-analyzer")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="Calculate_subnets",
            description="Calculates network details from a CIDR block (eg: 10.0.0.0/24).",
            inputSchema={
                "type": "object",
                "properties": {
                    "cidr": {
                        "type" : "string",
                        "description": "The IPv4 or IPv6 CIDR notation"
                    }
                },
                "required": ["cidr"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "Calculate_subnets":
        raise ValueError(f"Unknown tool: {name}")

    cidr_input = arguments.get("cidr", "")
    try:
        network = ipaddress.ip_network(cidr_input, strict=False)

        netmask = str(network.netmask)
        network_addr = str(network.network_address)
        broadcast_addr = str(network.broadcast_address)
        usable_hosts = network.num_addresses - 2 if network.version == 4 else network.num_addresses

        print(f"Calculated metrics for {cidr_input}", file=sys.stderr)

        result = (
            f"Network: {network_addr}\n"
            f"Netmask: {netmask}\n"
            f"Braodcast: {broadcast_addr}\n"
            f"Usable hosts: {max(0, usable_hosts)}\n"
        )

        return [TextContent(type="text", text=result)]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error parsing CIDR: {str(e)}")]

async def main():
    async with stdio_server() as (reader, writer):
        await app.run(reader, writer, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
