import requests
import json
from datetime import datetime, timezone

NOTION_TOKEN = "secret_5q53H8KNG0AIREFzANy3rENKmQMaHFf89eK0n8IlEgp"
DATABASE_ID_1 = "ba8ae4b2e1e1477f9e55a1931bebd488"
DATABASE_ID_2 = "2c514885f5804ab08ac9674ab7c63cd1"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_pages(database_id, num_pages=None):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data["results"]

def get_property_value(properties, key, prop_type='rich_text', content_field='content'):
    if prop_type == 'select':
        select_prop = properties.get(key, {}).get('select')
        if select_prop:
            return select_prop.get('name')
        return None
    elif prop_type == 'relation':
        relation_prop = properties.get(key, {}).get('relation')
        if relation_prop:
            return [relation['id'] for relation in relation_prop]
        return []
    elif prop_type == 'formula':
        formula_prop = properties.get(key, {}).get('formula')
        if formula_prop:
            return formula_prop.get(formula_prop['type'])
        return None
    else:
        prop_data = properties.get(key, {}).get(prop_type, [])
        if prop_data and len(prop_data) > 0:
            return prop_data[0].get('text', {}).get(content_field)
    return None

def get_safe_date(properties, key):
    date_info = properties.get(key, {}).get("date")
    return date_info.get("start") if date_info else None

def parse_coordinates(coordinate_string):
    if coordinate_string:
        coordinates = coordinate_string.split(',')
        if len(coordinates) == 2:
            x = coordinates[0].strip()
            y = coordinates[1].strip()
            return x, y
    return None, None

def extract_relation_ids(properties, key):
    relation_prop = properties.get(key, {}).get('relation')
    if relation_prop:
        return [relation['id'] for relation in relation_prop]
    return None

def extract_select_property(properties, key):
    select_prop = properties.get(key, {}).get('select')
    if select_prop:
        return select_prop.get('name')
    return None

def extract_formula_number(page, property_name):
    prop = page['properties'].get(property_name)
    if prop and prop['type'] == 'formula':
        if prop['formula']['type'] == 'number':
            return prop['formula']['number']
    return None


# Fetch data from the first database
plants_info = []

pages_db1 = get_pages(DATABASE_ID_1)
for page in pages_db1:
    page_id = page["id"]
    props = page["properties"]

    plant_id = get_property_value(props, "Plant ID", 'formula')
    plant_type = get_property_value(props, "Plant Type", 'formula')
    species = get_property_value(props, "Species", 'formula')
    scientific_name = get_property_value(props, "Scientific Name", 'formula')
    start_date = get_property_value(props, "Start Date", 'formula')
    farmbot_coordinates = get_property_value(props, "Farmbot Coordinates", 'rich_text')

    x_coordinate, y_coordinate = parse_coordinates(farmbot_coordinates)

    plant_info = {
        "Page ID": page_id,
        "Plant ID": plant_id,
        "Plant Type": plant_type,
        "Species": species,
        "Scientific Name": scientific_name,
        "Start Date": start_date,
        "FarmBot Coordinates": farmbot_coordinates,
        "X Coordinate": x_coordinate,
        "Y Coordinate": y_coordinate
    }
    plants_info.append(plant_info)

# Fetch data from the second database and integrate with the first
plants_in_gc = []

pages_db2 = get_pages(DATABASE_ID_2)
for page in pages_db2:
    page_id = page["id"]
    props = page["properties"]

    title = get_property_value(props, "Title", 'title')
    seed_bag_ids = extract_relation_ids(props, "Seed Bag")
    location = extract_select_property(props, "Location")
    start_date = get_safe_date(props, "Start Date")
    end_date = get_safe_date(props, "End Date")
    growing = extract_formula_number(page, "Growing")

    for plant in plants_info:
        if plant["Plant ID"] == title:
            plant.update({
                "Seed Bag IDs": seed_bag_ids,
                "Location": location,
                "End Date": end_date,
                "Growing": growing
            })
            break

    if location == "GC":
        plant_info_gc = {
            "Page ID": page_id,
            "Title": title,
            "Seed Bag IDs": seed_bag_ids,
            "Location": location,
            "Start Date": start_date,
            "End Date": end_date,
            "Growing": growing
        }
        plants_in_gc.append(plant_info_gc)

# Print combined data
for plant in plants_info:
    print(f"Page ID: {plant['Page ID']}, Plant ID: {plant['Plant ID']}, Plant Type: {plant['Plant Type']}, Species: {plant['Species']}, Scientific Name: {plant['Scientific Name']}, Start Date: {plant['Start Date']}, X Coordinate: {plant['X Coordinate']}, Y Coordinate: {plant['Y Coordinate']}, Seed Bag IDs: {plant.get('Seed Bag IDs')}, Location: {plant.get('Location')}, End Date: {plant.get('End Date')}, Growing: {plant.get('Growing')}")

# Save combined plant data to JSON file
with open('plants_info.json', 'w') as json_file:
    json.dump(plants_info, json_file, indent=4)

print("Plant data saved to plants_info.json")









# Save GC plant data to JSON file
#with open('plants_in_gc.json', 'w') as json_file:
#    json.dump(plants_in_gc, json_file, indent=4)

#("Plant data saved to plants_in_gc.json")
