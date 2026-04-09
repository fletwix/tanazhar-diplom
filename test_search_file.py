import asyncio
import io
import sys
from app.services.search_service import search_places

async def main():
    queries = ["ресторан", "кафе пушкин", "Сбербанк", "парк горького", "Достопримечательность"]
    
    with open("search_results.txt", "w", encoding="utf-8") as f:
        for q in queries:
            f.write(f"--- QUERY: {q} ---\n")
            try:
                # Moscow coordinates
                res = await search_places(q, 37.61, 55.75)
                f.write(f"FOUND: {len(res)}\n")
                if res:
                    f.write(f"1. {res[0]['name']} ({res[0]['category']}) - {res[0]['address']}\n")
            except Exception as e:
                f.write(f"ERROR: {e}\n")
            f.write("\n")

if __name__ == "__main__":
    asyncio.run(main())
