import json
import asyncio
import os

from openai import AsyncOpenAI

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

client = AsyncOpenAI()