"""
Nominatim (OSM) API Service for Places Search.
Replaces Photon for better Russian language support and reliability.
Requires User-Agent.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

PHOTON_URL = "https://photon.komoot.io/api/"
HEADERS = {"User-Agent": "TanazharApp/1.0"}

async def search_places(
    text: str,
    lon: float,
    lat: float,
    spn_lon: float = 0.1,
    spn_lat: float = 0.1,
    results: int = 20,
) -> list[dict]:
    
    # Photon expects just q, lat, lon, limit. It doesn't strictly use viewbox.
    # It prioritizes results around lat/lon.
    params = {
        "q": text.strip(),
        "lat": lat,
        "lon": lon,
        "limit": results,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(PHOTON_URL, params=params, headers=HEADERS)
            if resp.status_code != 200:
                logger.error("Photon API error: status=%s body=%s", resp.status_code, resp.text[:500])
                return []
            data = resp.json()
    except Exception as exc:
        logger.error("Photon API unexpected error: %s", exc)
        return []

    places = []
    
    features = data.get("features", [])

    for feature in features:
        try:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            
            if geometry.get("type", "") != "Point":
                continue
                
            coords = geometry.get("coordinates", [0.0, 0.0])
            item_lon = float(coords[0])
            item_lat = float(coords[1])
            
            name = properties.get("name")
            if not name:
                name = properties.get("street") or properties.get("city") or "Точка на карте"
                
            # Category formatting back to Russian
            osm_value = properties.get("osm_value", "")
            category = osm_value.replace("_", " ").capitalize()
            
            reverse_cat_map = {
                "restaurant": "Ресторан", "cafe": "Кафе", "fast_food": "Фастфуд",
                "hotel": "Отель", "hostel": "Хостел", "bar": "Бар", "pub": "Паб",
                "supermarket": "Супермаркет", "convenience": "Минимаркет", 
                "pharmacy": "Аптека", "park": "Парк", "museum": "Музей", 
                "attraction": "Достопримечательность", "atm": "Банкомат",
                "bank": "Банк", "pizza": "Пиццерия", "sushi": "Суши-бар",
                "commercial": "Коммерческое здание"
            }
            category_rus = reverse_cat_map.get(osm_value, category)
            
            # Address formatting
            street = properties.get("street", "")
            house = properties.get("housenumber", "")
            city = properties.get("city", "") or properties.get("district", "")
            
            address_parts = []
            if street:
                address_parts.append(f"{street} {house}".strip())
             
            # Fallback if no street
            if not address_parts and city:
                address_parts.append(city)
            elif not address_parts and name:
                address_parts.append(properties.get("state", ""))
                
            formatted_address = ", ".join([p for p in address_parts if p and p.strip()])
            
            places.append({
                "name": name,
                "description": formatted_address,
                "lon": item_lon,
                "lat": item_lat,
                "category": str(category_rus)[:30],
                "address": formatted_address,
                "hours": "Открыто" if osm_value in ["restaurant", "cafe", "fast_food", "supermarket", "pharmacy"] else "",
                "phone": properties.get("phone", ""),
                "url": properties.get("website", ""),
            })
        except Exception as exc:
            logger.warning("Error parsing Photon feature: %s", exc)
            continue

    return places
