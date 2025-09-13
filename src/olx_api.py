from typing import Any

import httpx

URL_OLX_LOCATAION = "https://www.olx.ua/api/v1/geo-encoder/location-autocomplete/"


async def get_city_info(query: str) -> dict[Any, Any]:
    """
    Async call to OLX geo-encoder API to get city info by name.
    """
    if len(query) < 3:
        raise ValueError("Query must be at least 3 characters long.")
    params = {"query": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url=URL_OLX_LOCATAION, params=params, headers=headers)
        response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]
