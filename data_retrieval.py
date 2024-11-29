import asyncio
import logging
from req_http import http_get


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def get_data() -> None:
    url = "https://api.worldpop.org/v1/services/stats?dataset=wpgppop&year=2010&geojson={“type”:”FeatureCollection”,”features”:[{“type”:”Feature”,”properties”:{},”geometry”:{“type”:”Polygon”,”coordinates”:[[[10.546875,47.62097541515849],[9.95361328125,46.437856895024204],[11.315917968749998,45.98169518512228],[12.63427734375,46.66451741754235],[12.65625,47.85740289465826],[10.546875,47.62097541515849]]]}}]}"
    data = await http_get(url)
    print(data)


if __name__ == "__main__":
    asyncio.run(get_data())
