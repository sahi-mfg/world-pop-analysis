from req_http import http_get


async def get_data() -> None:
    url = " https://www.worldpop.org/rest/data/pop/wpgp?ISO=NGA"
    data = await http_get(url)
    print(data)
