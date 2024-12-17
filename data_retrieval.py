import asyncio
import logging
from req_http import http_get


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def get_data(url: str) -> None:
    data = await http_get(url)
    print(data)


if __name__ == "__main__":
    url = "https://jsonplaceholder.typicode.com/posts/1"
    asyncio.run(get_data(url))
