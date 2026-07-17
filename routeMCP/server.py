import asyncio
import sys
import ipaddress
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("packet-router-sim")

# Hardcoded simulation state
ROUTING_TABLE = {
    "192.168.1.0/24": {"interface": "eth0", "next_hop": "direct", "mtu": 1500},
    "10.0.0.0/8": {"interface": "tun0", "next_hop": "10.0.0.1", "mtu": 1200},
    "0.0.0.0/0": {"interface": "eth1", "next_hop": "172.16.0.1", "mtu": 1500}  # Default route
}

FIREWALL_RULES = [
    {"action": "deny", "network": "192.168.1.100/32", "port": "any"},  # Block specific host
    {"action": "allow", "network": "192.168.1.0/24", "port": 80},  # Allow HTTP to subnet
    {"action": "deny", "network": "any", "port": 23}  # Block Telnet globally
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="route_lookup",
            description="Finds the outgoing interface and MTU for a destination IP.",
            inputSchema={
                "type": "object",
                "properties": {"dest_ip": {"type": "string"}},
                "required": ["dest_ip"]
            }
        ),
        Tool(
            name="check_firewall",
            description="Evaluates if a packet is permitted by the firewall ACL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "src_ip": {"type": "string"},
                    "dest_port": {"type": "integer"}
                },
                "required": ["src_ip", "dest_port"]
            }
        ),
        Tool(
            name="fragment_packet",
            description="Fragments a packet if it exceeds the interface MTU.",
            inputSchema={
                "type": "object",
                "properties": {
                    "packet_size": {"type": "integer"},
                    "mtu": {"type": "integer"}
                },
                "required": ["packet_size", "mtu"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "route_lookup":
        dest = ipaddress.IPv4Address(arguments["dest_ip"])
        best_match = "0.0.0.0/0"
        max_prefix = -1

        # Longest prefix match routing
        for route_cidr in ROUTING_TABLE.keys():
            network = ipaddress.IPv4Network(route_cidr)
            if dest in network and network.prefixlen > max_prefix:
                best_match = route_cidr
                max_prefix = network.prefixlen

        route_info = ROUTING_TABLE[best_match]
        return [TextContent(type="text",
                            text=f"Route found via {route_info['interface']}. Next hop: {route_info['next_hop']}. MTU: {route_info['mtu']}")]

    elif name == "check_firewall":
        src = ipaddress.IPv4Address(arguments["src_ip"])
        port = arguments["dest_port"]

        for rule in FIREWALL_RULES:
            port_match = rule["port"] == "any" or rule["port"] == port
            net_match = rule["network"] == "any" or src in ipaddress.IPv4Network(rule["network"])

            if port_match and net_match:
                return [
                    TextContent(type="text", text=f"Firewall result: {rule['action'].upper()} (Matched rule: {rule})")]

        return [TextContent(type="text", text="Firewall result: ALLOW (Default policy)")]

    elif name == "fragment_packet":
        size = arguments["packet_size"]
        mtu = arguments["mtu"]

        if size <= mtu:
            return [TextContent(type="text", text="No fragmentation needed.")]

        # Simple fragmentation math (assuming 20 byte IP header)
        payload_per_frag = (mtu - 20) // 8 * 8  # Must be multiple of 8
        num_frags = ((size - 20) + payload_per_frag - 1) // payload_per_frag
        return [TextContent(type="text", text=f"Packet fragmented into {num_frags} pieces of max size {mtu} bytes.")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())