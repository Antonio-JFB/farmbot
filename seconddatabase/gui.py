import json
import requests
import threading
import paho.mqtt.client as mqtt
from time import sleep
from farmbot import Farmbot, FarmbotToken
import customtkinter as ctk
from tkinter import END, Frame, Scrollbar, VERTICAL, RIGHT, LEFT, Y, W, BooleanVar, filedialog, Toplevel, Label, TOP, \
    StringVar, ttk, simpledialog
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageTk

NOTION_TOKEN = "secret_5q53H8KNG0AIREFzANy3rENKmQMaHFf89eK0n8IlEgp"
DATABASE_ID_1 = "ba8ae4b2e1e1477f9e55a1931bebd488"
DATABASE_ID_2 = "2c514885f5804ab08ac9674ab7c63cd1"

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Load token from file
with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

SERVER = 'https://my.farm.bot'
EMAIL = 'tonywongtk@gmail.com'
PASSWORD = 'Garden4ngel'

# Connect to the MQTT broker
client = mqtt.Client()
client.username_pw_set(
    TOKEN["token"]["unencoded"]["bot"],
    password=TOKEN["token"]["encoded"])
client.connect(TOKEN["token"]["unencoded"]["mqtt"])
print('connected')
channel = f'bot/{TOKEN["token"]["unencoded"]["bot"]}/from_clients'

# Construct the URL and headers
farmbot_url = f"https:{TOKEN['token']['unencoded']['iss']}/api/images"
farmbot_headers = {'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
                   'content-type': 'application/json'}

# Send the request and get all images
response = requests.get(farmbot_url, headers=farmbot_headers)
images = response.json()



def prepare_message(command):
    return {
        "kind": "rpc_request",
        "args": {
            "label": "abcdef"
        },
        "body": [command]
    }


class MyHandler:
    def __init__(self, bot):
        self.queue = []
        self.busy = True
        self.bot = bot

    def add_job(self, job):
        self.queue.append(job)
        self.bot.read_status()

    def try_next_job(self):
        if (len(self.queue) > 0) and (not self.busy):
            job = self.queue.pop(0)
            print("executing job")
            self.busy = True
            job()

    def take_photo(self, plant_x, plant_y, plant_z):
        command = {
            "kind": "execute",
            "args": {
                "sequence_id": 210608
            },
            "body": [
                {
                    "kind": "parameter_application",
                    "args": {
                        "label": "plant",
                        "data_value": {
                            "kind": "coordinate",
                            "args": {
                                "x": plant_x,
                                "y": plant_y,
                                "z": plant_z
                            }
                        }
                    }
                }
            ]
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    def on_connect(self, bot, mqtt_client):
        self.bot.read_status()

    def on_change(self, bot, state):
        is_busy = state['informational_settings']['busy']
        if is_busy != self.busy:
            if is_busy:
                print("Device is busy")
            else:
                print("Device is idle")

        self.busy = is_busy
        self.try_next_job()

    def on_log(self, _bot, log):
        print("LOG: " + log['message'])

    def on_response(self, _bot, _response):
        pass

    def on_error(self, _bot, response):
        print("ERROR: " + response.id)
        print("Reason(s) for failure: " + str(response.errors))


# Initialize the FarmBot and handler
raw_token = FarmbotToken.download_token(EMAIL, PASSWORD, SERVER)
fb = Farmbot(raw_token)
handler = MyHandler(fb)
threading.Thread(target=fb.connect, name="foo", args=[handler]).start()


def get_pages(database_id, num_pages=None):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data["results"]


def get_property_value(properties, key, prop_type='rich_text', content_field='content'):
    prop = properties.get(key, {})
    if prop_type == 'select':
        select_prop = prop.get('select')
        if select_prop:
            return select_prop.get('name')
        return None
    elif prop_type == 'relation':
        relation_prop = prop.get('relation')
        if relation_prop:
            return [relation['id'] for relation in relation_prop]
        return []
    elif prop_type == 'formula':
        formula_prop = prop.get('formula')
        if formula_prop:
            return formula_prop.get(formula_prop['type'])
        return None
    elif prop_type == 'date':
        date_prop = prop.get('date')
        if date_prop:
            return date_prop.get('start')
        return None
    else:
        prop_data = prop.get(prop_type, [])
        if prop_data and len(prop_data) > 0:
            return prop_data[0].get('text', {}).get(content_field)
    return None


def parse_coordinates(coordinate_string):
    if coordinate_string:
        coordinates = coordinate_string.split(',')
        if len(coordinates) == 2:
            x = coordinates[0].strip()
            y = coordinates[1].strip()
            return x, y
    return None, None


def fetch_plant_data():
    pages_db1 = get_pages(DATABASE_ID_1)
    plants_info = []

    for page in pages_db1:
        page_id = page["id"]
        props = page["properties"]

        plant_id = get_property_value(props, "Plant ID", 'formula')
        plant_type = get_property_value(props, "Plant Type", 'formula')
        species = get_property_value(props, "Species", 'formula')
        scientific_name = get_property_value(props, "Scientific Name", 'formula')
        start_date = get_property_value(props, "Start Date", 'formula')
        farmbot_coordinates = get_property_value(props, "Farmbot Coordinates", 'rich_text')

        if farmbot_coordinates:  # Only add plants that have FarmBot coordinates
            plant_info = {
                "Page ID": page_id,
                "Plant ID": plant_id,
                "Plant Type": plant_type,
                "Species": species,
                "Scientific Name": scientific_name,
                "Start Date": start_date,
                "FarmBot Coordinates": farmbot_coordinates
            }
            plants_info.append(plant_info)

    return plants_info


def display_plant_names(plants_info):
    for widget in listbox_frame.winfo_children():
        widget.destroy()
    for plant in plants_info:
        plant_label = ctk.CTkLabel(listbox_frame, text=plant["Plant ID"], padx=10, pady=5, anchor="w")
        plant_label.pack(fill="x", pady=2)
        plant_label.bind("<Button-1>", lambda e, p=plant: show_plant_details(p))


def show_plant_details(selected_plant):
    # Clear existing details
    for widget in details_frame.winfo_children():
        widget.destroy()

    # Parse coordinates
    x, y = parse_coordinates(selected_plant['FarmBot Coordinates'])

    # Display new details
    ctk.CTkLabel(details_frame, text=f"Plant ID: {selected_plant['Plant ID']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Plant Type: {selected_plant['Plant Type']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Species: {selected_plant['Species']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Scientific Name: {selected_plant['Scientific Name']}", anchor=W).pack(pady=2,
                                                                                                             anchor=W)
    ctk.CTkLabel(details_frame, text=f"Start Date: {selected_plant['Start Date']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"FarmBot Coordinates: {selected_plant['FarmBot Coordinates']}", anchor=W).pack(
        pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"X Coordinate: {x}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Y Coordinate: {y}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Seed Bag IDs: {selected_plant.get('Seed Bag IDs')}", anchor=W).pack(pady=2,
                                                                                                           anchor=W)
    ctk.CTkLabel(details_frame, text=f"Location: {selected_plant.get('Location')}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"End Date: {selected_plant.get('End Date')}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_frame, text=f"Growing: {selected_plant.get('Growing')}", anchor=W).pack(pady=2, anchor=W)

    # Show the "Show Photo" button only if the plant has FarmBot coordinates
    show_photo_button = ctk.CTkButton(details_frame, text="Show Photo",
                                      command=lambda: show_photo(selected_plant, x, y))
    show_photo_button.pack(pady=10)

    # Add a button to take a photo
    take_photo_button = ctk.CTkButton(details_frame, text="Take Photo",
                                      command=lambda: prompt_photo_distance(selected_plant, x, y))
    take_photo_button.pack(pady=10)

    # Add a button to create a farm event
    create_event_button = ctk.CTkButton(details_frame, text="Create Farm Event",
                                        command=lambda: prompt_moisture_level(selected_plant, x, y))
    create_event_button.pack(pady=10)


def find_closest_image(images, x, y, z):
    closest_image = None
    smallest_distance = float('inf')
    for image in images:
        img_x = image['meta']['x']
        img_y = image['meta']['y']
        img_z = image['meta'].get('z', 0)  # Default to 0 if z is not available
        distance = ((img_x - x) ** 2 + (img_y - y) ** 2 + (img_z - z) ** 2) ** 0.5
        if distance < smallest_distance:
            smallest_distance = distance
            closest_image = image
    return closest_image


def show_photo(selected_plant, x, y):
    z_values = [-200, -110, -50]  # Possible z-values based on distances (close, medium, far)
    image_found = False

    for z in z_values:
        closest_image = find_closest_image(images, float(x), float(y), z)
        if closest_image:
            image_url = closest_image['attachment_url']
            response = requests.get(image_url)
            image_data = response.content
            image = Image.open(BytesIO(image_data))
            image = ImageTk.PhotoImage(image)

            image_window = Toplevel(root)
            image_window.title(f"Photo of {selected_plant['Plant ID']}")

            image_label = Label(image_window, image=image)
            image_label.image = image  # Keep a reference to avoid garbage collection
            image_label.pack()

            # Add a button to download the image
            download_button = ctk.CTkButton(image_window, text="Download Photo",
                                            command=lambda: download_photo(image_url))
            download_button.pack(pady=10)

            image_found = True
            break

    if not image_found:
        print("No image found close to the given coordinates.")


def prompt_photo_distance(selected_plant, x, y):
    popup = Toplevel(root)
    popup.title("Select Photo Distance")
    popup.geometry("300x200")

    # Frame for better layout management
    frame = ctk.CTkFrame(popup)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Label
    label = ctk.CTkLabel(frame, text="Select distance for the photo:")
    label.pack(pady=(10, 20))

    # Dropdown for distance selection
    distance_var = StringVar(value="medium")
    distance_dropdown = ttk.Combobox(frame, textvariable=distance_var, state="readonly")
    distance_dropdown['values'] = ("close", "medium", "far")
    distance_dropdown.pack(pady=(0, 20))

    # Confirm button
    confirm_button = ctk.CTkButton(frame, text="Take Photo",
                                   command=lambda: [take_photo(selected_plant, x, y, distance_var.get()), popup.destroy()])
    confirm_button.pack(pady=(20, 10))

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)



def prompt_moisture_level(selected_plant, x, y):
    popup = Toplevel(root)
    popup.title("Create Farm Event")

    ctk.CTkLabel(popup, text="Enter the moisture level (0-100):", text_color="black").pack(pady=10)
    moisture_var = StringVar()
    moisture_entry = ctk.CTkEntry(popup, textvariable=moisture_var)
    moisture_entry.pack(pady=10)

    ctk.CTkLabel(popup, text="Enter duration in weeks:", text_color="black").pack(pady=10)
    duration_var = StringVar()
    duration_entry = ctk.CTkEntry(popup, textvariable=duration_var)
    duration_entry.pack(pady=10)

    confirm_button = ctk.CTkButton(popup, text="Create Event",
                                   command=lambda: [create_farm_event(selected_plant, x, y, moisture_var.get(), duration_var.get()), popup.destroy()])
    confirm_button.pack(pady=10)



def create_farm_event(selected_plant, x, y, moisture_level, duration_weeks):
    try:
        moisture_level = int(moisture_level)
        duration_weeks = int(duration_weeks)
    except ValueError:
        print("Invalid input. Please enter numerical values for moisture level and duration.")
        return

    # Extract and clean the iss value
    iss = TOKEN['token']['unencoded']['iss'].strip('/')
    if not iss.startswith('http'):
        iss = f"https://{iss}"
    else:
        iss = f"{iss}"

    # Calculate next day's date and time in UTC
    now = datetime.utcnow()
    start_time = now.replace(hour=15, minute=30, second=0, microsecond=0).isoformat() + "Z"
    end_time = (now + timedelta(weeks=duration_weeks)).replace(hour=15, minute=30, second=0, microsecond=0).isoformat() + "Z"

    # FarmBot API endpoint for creating farm events
    farmbot_url = f"{iss}/api/farm_events"
    farmbot_headers = {'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
                       'content-type': 'application/json'}

    # Payload for creating the farm event with adjusted time
    payload = {
        "start_time": start_time,
        "end_time": end_time,
        "repeat": 1,
        "time_unit": "daily",
        "executable_id": 208750,
        "executable_type": "Sequence",
        "body": [
            {
                "kind": "parameter_application",
                "args": {
                    "label": "moisture",
                    "data_value": {
                        "kind": "numeric",
                        "args": {
                            "number": moisture_level
                        }
                    }
                }
            },
            {
                "kind": "parameter_application",
                "args": {
                    "label": "plant",
                    "data_value": {
                        "kind": "coordinate",
                        "args": {
                            "x": float(x),
                            "y": float(y),
                            "z": 0
                        }
                    }
                }
            }
        ]
    }

    # Make the request to create the farm event
    response = requests.post(farmbot_url, headers=farmbot_headers, json=payload)

    # Print the response
    print(json.dumps(response.json(), indent=2))


def take_photo(selected_plant, x, y, distance):
    if distance == "close":
        z = -200
    elif distance == "medium":
        z = -110
    elif distance == "far":
        z = -50
    else:
        print("Invalid distance selected.")
        return

    handler.add_job(lambda: handler.take_photo(float(x), float(y), float(z)))
    handler.try_next_job()


def download_photo(image_url):
    response = requests.get(image_url)
    file_path = filedialog.asksaveasfilename(defaultextension=".jpg",
                                             filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Photo saved to {file_path}")


def toggle_farmbot_filter():
    display_plant_names(plants_info)


def export_to_json():
    export_data = [plant for plant in plants_info if plant["FarmBot Coordinates"]]
    file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                             filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'w') as json_file:
            json.dump(export_data, json_file, indent=4)
        print(f"Data exported to {file_path}")


def add_banner():
    # Create a frame for the banner
    banner_frame = ctk.CTkFrame(root)
    banner_frame.pack(side=TOP, fill="x")

    # Add a label for the banner text
    banner_label = ctk.CTkLabel(banner_frame, text="FarmBot Plant Manager", font=("Helvetica", 18, "bold"), padx=10,
                                pady=5)
    banner_label.pack()



# Create the main window
root = ctk.CTk()
root.title("Plant Names")
root.geometry("800x600")  # Set the window size

# Set the appearance mode and color theme to dark
ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Light", "Dark"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (default), "dark-blue", "green"


# Call the function to add the banner
add_banner()

# Create a frame for the listbox
listbox_frame = ctk.CTkFrame(root)
listbox_frame.pack(side=LEFT, fill="y", padx=10, pady=10, expand=True)

# Create a frame for the plant details
details_frame = ctk.CTkFrame(root)
details_frame.pack(side=RIGHT, fill="both", expand=True, padx=10, pady=10)

# Create a checkbox to filter plants with FarmBot coordinates
show_farmbot_only = BooleanVar(value=True)  # Default to only showing FarmBot plants
farmbot_checkbox = ctk.CTkCheckBox(root, text="Show only FarmBot plants", variable=show_farmbot_only,
                                   command=toggle_farmbot_filter)
farmbot_checkbox.pack(pady=10)

# Create a button to fetch and display plant names
fetch_button = ctk.CTkButton(root, text="Fetch Plant Names", command=lambda: display_plant_names(plants_info))
fetch_button.pack(pady=10)

# Create a button to export the data to a JSON file
export_button = ctk.CTkButton(root, text="Export to JSON", command=export_to_json)
export_button.pack(pady=10)

# Fetch the initial plant data and display
plants_info = fetch_plant_data()
display_plant_names(plants_info)

# Start the GUI main loop
root.mainloop()
