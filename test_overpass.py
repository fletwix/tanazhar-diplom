import asyncio
from app.services.search_service import search_places
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    places = await search_places(text="пицца", lon=76.889, lat=43.238, spn_lon=0.1, spn_lat=0.1)
    print(f"FOUND: {len(places)} places")
    if places:
        print(places[0])

asyncio.run(test())
