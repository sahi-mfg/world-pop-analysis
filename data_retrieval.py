import asyncio
import logging
from req_http import http_get


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def get_data() -> None:
    url = "https://www.worldpop.org/rest/data/pop/"
    data = await http_get(url)
    print(data)


if __name__ == "__main__":
    asyncio.run(get_data())
