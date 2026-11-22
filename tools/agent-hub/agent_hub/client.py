"""Bounded, authenticated calls to a configured Streamable HTTP MCP endpoint."""
import asyncio
import json
from urllib.parse import urlsplit


def check_endpoint(endpoint):
    url = urlsplit(endpoint)
    local = url.hostname in {'127.0.0.1', 'localhost', '::1'}
    if (not url.hostname or url.username is not None or url.password is not None
            or url.query or url.fragment or not (url.scheme == 'https' or local and url.scheme == 'http')):
        raise ValueError('invalid_mcp_endpoint')


async def call_tool_async(name, arguments, *, endpoint, token):
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    check_endpoint(endpoint)
    if not token or not token.isascii() or any(ord(c) < 33 or ord(c) > 126 for c in token):
        raise ValueError('invalid_mcp_credential')

    async def invoke():
        headers = {'Authorization': 'Bearer ' + token}
        async with httpx.AsyncClient(headers=headers, timeout=12, trust_env=False, follow_redirects=False) as http:
            async with streamable_http_client(endpoint, http_client=http) as (reader, writer, _):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    reply = await client.call_tool(name, arguments)
                    result = reply.structuredContent
                    if (not reply.isError and result is None and len(reply.content) == 1
                            and reply.content[0].type == 'text'):
                        result = json.loads(reply.content[0].text)
                    if reply.isError or not isinstance(result, dict):
                        raise ValueError('mcp_request_failed')
                    return result

    return await asyncio.wait_for(invoke(), 20)


def call_tool(name, arguments, *, endpoint, token):
    return asyncio.run(call_tool_async(name, arguments, endpoint=endpoint, token=token))
