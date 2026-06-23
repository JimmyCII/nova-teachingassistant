import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import os

_CURRICULUM = StdioServerParameters(
    command="python", 
    args=["-m", "mcp_servers.curriculum_server.server"],
    env=os.environ.copy() | {"PYTHONUTF8": "1"}
)

async def _read(uri: str) -> str:
    async with stdio_client(_CURRICULUM) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.read_resource(uri)
            return res.contents[0].text  # FastMCP resource returns text contents

def read_resource(uri: str) -> str:
    """Sync: read an MCP resource (e.g. 'standards://az-math-6'). Raises on failure."""
    return asyncio.run(_read(uri))
