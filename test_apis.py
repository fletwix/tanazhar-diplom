import asyncio
import httpx
import sys

async def main():
    async with httpx.AsyncClient() as client:
        # Test Photon
        print("Testing Photon...")
        try:
            r1 = await client.get(
                "https://photon.komoot.io/api/",
                params={"q": "кафе", "lat": 55.75, "lon": 37.61, "limit": 5},
                headers={"User-Agent": "Mozilla/5.0"}
            )
            print("Photon status:", r1.status_code)
            if r1.status_code == 200:
                print("Photon found:", len(r1.json().get("features", [])))
        except Exception as e:
            print("Photon error:", e)

        # Test Nominatim
        print("Testing Nominatim...")
        try:
            r2 = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": "сбербанк", "format": "json", "limit": 5, "accept-language": "ru"},
                headers={"User-Agent": "TrailWeaverApp/1.0 (contact@example.com)"}
            )
            print("Nominatim status:", r2.status_code)
            if r2.status_code == 200:
                print("Nominatim found:", len(r2.json()))
        except Exception as e:
            print("Nominatim error:", e)

if __name__ == "__main__":
    asyncio.run(main())
