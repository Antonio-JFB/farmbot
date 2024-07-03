import requests
import json
from datetime import datetime, timezone

NOTION_TOKEN = "secret_5q53H8KNG0AIREFzANy3rENKmQMaHFf89eK0n8IlEgp"
DATABASE_ID = "2c514885f5804ab08ac9674ab7c63cd1"


headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_pages(num_pages=None):
    """
    If num_pages is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data["results"]

def extract_multi_select(properties, key):
    """
    Extracts the names of the selected options from a multi-select property.
    """
    options = properties.get(key, {}).get("multi_select", [])
    return [option['name'] for option in options]

def get_safe_date(properties, key):
    date_info = properties.get(key, {}).get("date")
    return date_info.get("start") if date_info else None

def get_property_value(properties, key, prop_type='rich_text', content_field='content'):
    prop_data = properties.get(key, {}).get(prop_type, [])
    if prop_data and len(prop_data) > 0:
        return prop_data[0].get('text', {}).get(content_field)
    return None

def extract_formula_number(page, property_name):
    # Access the properties dictionary
    prop = page['properties'].get(property_name)

    # Check if the property exists and is of type 'formula'
    if prop and prop['type'] == 'formula':
        # Check if the formula is of type 'number'
        if prop['formula']['type'] == 'number':
            # Return the number if available, otherwise return None
            return prop['formula']['number']
    return None

def extract_select_property(properties, key):
    """
    Extracts the name of the selected option from a select property.
    """
    select_prop = properties.get(key, {}).get('select')
    if select_prop:
        return select_prop.get('name')
    return None

def extract_relation_ids(properties, key):
    """
    Extracts the IDs from a relation property.
    """
    relation_prop = properties.get(key, {}).get('relation')
    if relation_prop:
        return [relation['id'] for relation in relation_prop]
    return None

# Initialize list to hold plant data
plants_in_gc = []

pages = get_pages()
for page in pages:
    page_id = page["id"]
    props = page["properties"]

    title = get_property_value(props, "Title", 'title')
    seed_bag_ids = extract_relation_ids(props, "Seed Bag")
    location = extract_select_property(props, "Location")
    start_date = get_safe_date(props, "Start Date")
    end_date = get_safe_date(props, "End Date")
    growing = extract_formula_number(page, "Growing")

    if location == "GC":
        plant_info = {
            "Page ID": page_id,
            "Title": title,
            "Seed Bag IDs": seed_bag_ids,
            "Location": location,
            "Start Date": start_date,
            "End Date": end_date,
            "Growing": growing
        }
        plants_in_gc.append(plant_info)

        print(f"Page ID: {page_id}, Title: {title}, Seed Bag IDs: {seed_bag_ids}, Location: {location}, Start Date: {start_date}, End Date: {end_date}, Growing: {growing}")

# Save plant data to JSON file
with open('plants_in_gc.json', 'w') as json_file:
    json.dump(plants_in_gc, json_file, indent=4)

print("Plant data saved to plants_in_gc.json")


()


