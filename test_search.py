import asyncio
from app.services.search_service import search_places

async def main():
    res1 = await search_places("ресторан", 37.61, 55.75)
    print("ресторан:", len(res1))
    if res1: print(res1[0])

    res2 = await search_places("кафе пушкин", 37.61, 55.75)
    print("кафе пушкин:", len(res2))
    
    res3 = await search_places("Отель", 37.61, 55.75)
    print("Отель:", len(res3))

if __name__ == "__main__":
    asyncio.run(main())
