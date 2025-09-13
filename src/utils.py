# src/utils.py


def remove_duplicate_cities(data: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for item in data:
        city_id = item["city"]["id"]
        if city_id not in seen:
            seen.add(city_id)
            unique.append(item)
    return unique
