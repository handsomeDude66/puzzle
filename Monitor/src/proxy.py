import asyncio

import httpx

_proxies: list[str] = []


async def _get_proxies():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:5010/all/")
    json_data: set[str] = {i['proxy'] for i in response.json() if i['https']}
    _proxies.clear()
    _proxies.extend(json_data)


async def test_available():
    async def test(proxy: str):
        async with httpx.AsyncClient(
            proxies={
                'http://': f'http://{proxy}',
                'https://': f'http://{proxy}',
            }
        ) as client:
            try:
                response = await client.get("https://www.baidu.com")
            except httpx.HTTPError:
                return None
        print(response.text)
        return proxy

    available_proxies = await asyncio.gather(*[test(proxy) for proxy in _proxies])
    print(available_proxies)


async def get_proxy():
    if not _proxies:
        await _get_proxies()
    return _proxies.pop()


async def delete_proxy(proxy: str):
    async with httpx.AsyncClient() as client:
        await client.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


async def main():
    await get_proxy()
    await test_available()


if __name__ == "__main__":
    asyncio.run(main())
