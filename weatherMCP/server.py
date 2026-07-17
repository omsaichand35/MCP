import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from weather import get_coordinates, get_weather, WEATHER_CODES

app = Server("Weather MCP")

@app.list_tools()
async def list_tools()-> list[Tool]:
    return [
        Tool(
            name="get_current_weather",
            description="Get the current weather for a city.",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "Name of the city"}},
                "required": ["city"]
            }
        ),
        Tool(
            name="get_forecast",
            description="Get the forecast at a city.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Name of the city."},
                    "days": {"type": "integer", "description": "The number of days to get."},
                },
                "required": ["city", "days"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "get_current_weather":
        raise ValueError(f"Unknown tool: {name}")
    city = arguments["city"]
    coords = get_coordinates(city)

    if coords is None:
        return[TextContent(
            type="text",
            text=f"Couldn't find the {city}'s weather.",
        )]
    lat, lon = coords
    weather = get_weather(lat, lon)

    current = weather["current"]

    if current["weather_code"] != WEATHER_CODES:
        code = WEATHER_CODES[current["weather_code"]]

    result = f"""
    City: {city}
    Temperature: {current['temperature_2m']}°C
    Humidity: {current['relative_humidity_2m']}%
    Wind Speed: {current['wind_speed_10m']} km/h
    Weather Code: {code}
    """


    return [
        TextContent(
            type="text",
            text=result
        )
    ]

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())