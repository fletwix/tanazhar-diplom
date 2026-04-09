import asyncio
from app.services.search_service import search_places
import logging

logging.basicConfig(level=logging.DEBUG)

async def test():
    try:
        # Almaty coordinates
        places = await search_places(text="ресторан", lon=76.889, lat=43.238, spn_lon=0.1, spn_lat=0.1)
        print("======== RESULTS ========")
        print(f"FOUND: {len(places)} places")
        if places:
            for i, p in enumerate(places[:3]):
                print(f"{i+1}. {p['name']} ({p['category']}) - {p['address']}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
