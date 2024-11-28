import asyncio

import requests


def http_get_sync(url: str) -> dict:
    response = requests.get(url)
    return response.json()


async def http_get(url: str) -> dict:
    return await asyncio.to_thread(http_get_sync, url)
