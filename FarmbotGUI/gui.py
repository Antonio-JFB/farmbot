import json
import requests
import threading
import paho.mqtt.client as mqtt
from time import sleep
from farmbot import Farmbot, FarmbotToken
import customtkinter as ctk
from tkinter import END, BooleanVar, filedialog, Toplevel, Label, TOP, StringVar, simpledialog,LEFT,RIGHT,W
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageTk
from email.message import EmailMessage
import ssl
import smtplib
from datetime import datetime
import pytz




# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

NOTION_TOKEN = config['NOTION_TOKEN']
DATABASE_ID_1 = config['DATABASE_ID_1']
DATABASE_ID_2 = config['DATABASE_ID_2']
SERVER = config['SERVER']
EMAIL = config['EMAIL']
PASSWORD = config['PASSWORD']

email_sender = 'juanlopez1234334@gmail.com'
email_password = 'fsgc pdbv oxue yotk'
email_receiver = 'dreamchuyito@gmail.com'

subject = 'Farmbot Alert'
body = """
Farmbot has encountered a problem. Please remove the mounted tool and execute the find home command.
"""



def send_alert_email():
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Mark the email as important
    em['X-Priority'] = '1'  # Highest priority
    em['Priority'] = 'urgent'
    em['Importance'] = 'high'

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Load token from file
with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)



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
        log_message = "LOG: " + log['message']
        print(log_message)
        log_label.configure(text=log_message)

        error_messages = [
            "Tool mounting failed - no electrical connection between UTM pins B and C.",
            "A tool is already mounted to the UTM - there is an electrical connection between UTM pins B and C."
        ]

        # Check if any of the specified error messages are in the log message
        if any(error_msg in log_message for error_msg in error_messages):
            send_alert_email()

    def on_response(self, _bot, _response):
        pass

    def on_error(self, _bot, response):
        error_message = "ERROR: " + response.id + " - " + str(response.errors)
        print(error_message)
        log_label.configure(text=error_message)

        # New functions

    # Function to move to absolute coordinates
    def move_absolute(self, x, y, z, speed=100):
        command = {
            "kind": "move_absolute",
            "args": {
                "location": {"kind": "coordinate", "args": {"x": x, "y": y, "z": z}},
                "offset": {"kind": "coordinate", "args": {"x": 0, "y": 0, "z": 0}},
                "speed": speed
            }
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to move relative to current position
    def move_relative(self, x, y, z):
        command = {
            "kind": "move_relative",
            "args": {"x": x, "y": y, "z": z}
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to send a message
    def send_message(self, message_type, message):
        command = {
            "kind": "send_message",
            "args": {
                "message": message,
                "message_type": message_type
            }
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to lock the device in an emergency
    def emergency_lock(self):
        command = {"kind": "emergency_lock", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to unlock the device after an emergency
    def emergency_unlock(self):
        command = {"kind": "emergency_unlock", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to find the home position
    def find_home(self, axis):
        command = {
            "kind": "find_home",
            "args": {"axis": axis}
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to find the length of an axis
    def find_length(self, axis):
        command = {
            "kind": "find_length",
            "args": {"axis": axis}
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to read the device status
    def read_status(self):
        command = {"kind": "read_status", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to reboot the device
    def reboot(self):
        command = {"kind": "reboot", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to reset the device to factory settings
    def factory_reset(self):
        command = {"kind": "factory_reset", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    # Function to synchronize the device
    def sync(self):
        command = {"kind": "sync", "args": {}}
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False


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

def fetch_farm_events():
    iss = TOKEN['token']['unencoded']['iss'].strip('/')
    if not iss.startswith('http'):
        iss = f"https://{iss}"
    else:
        iss = f"{iss}"

    # FarmBot API endpoint for fetching farm events
    farmbot_url = f"{iss}/api/farm_events"
    farmbot_headers = {'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
                       'content-type': 'application/json'}

    # Make the request to get the farm events
    response = requests.get(farmbot_url, headers=farmbot_headers)
    return response.json()



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
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    filtered_plants = [plant for plant in plants_info if plant["FarmBot Coordinates"]]  # Apply the filter

    for plant in filtered_plants:
        plant_label = ctk.CTkLabel(scrollable_frame, text=plant["Plant ID"], padx=10, pady=5, anchor="w")
        plant_label.pack(fill="x", pady=2)
        plant_label.bind("<Button-1>", lambda e, p=plant: show_plant_details(p))


def show_plant_details(selected_plant):
    # Clear existing details
    for widget in details_scrollable_frame.winfo_children():
        widget.destroy()

    # Parse coordinates
    x, y = parse_coordinates(selected_plant['FarmBot Coordinates'])

    # Display new details
    ctk.CTkLabel(details_scrollable_frame, text=f"Plant ID: {selected_plant['Plant ID']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Plant Type: {selected_plant['Plant Type']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Species: {selected_plant['Species']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Scientific Name: {selected_plant['Scientific Name']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Start Date: {selected_plant['Start Date']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"FarmBot Coordinates: {selected_plant['FarmBot Coordinates']}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"X Coordinate: {x}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Y Coordinate: {y}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Seed Bag IDs: {selected_plant.get('Seed Bag IDs')}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Location: {selected_plant.get('Location')}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"End Date: {selected_plant.get('End Date')}", anchor=W).pack(pady=2, anchor=W)
    ctk.CTkLabel(details_scrollable_frame, text=f"Growing: {selected_plant.get('Growing')}", anchor=W).pack(pady=2, anchor=W)

    # Show the "Show Photo" button only if the plant has FarmBot coordinates
    show_photo_button = ctk.CTkButton(details_scrollable_frame, text="Show Photo",
                                      command=lambda: show_photo(selected_plant, x, y))
    show_photo_button.pack(pady=10)

    # Add a button to take a photo
    take_photo_button = ctk.CTkButton(details_scrollable_frame, text="Take Photo",
                                      command=lambda: prompt_photo_distance(selected_plant, x, y))
    take_photo_button.pack(pady=10)

    # Add a button to export plant details to JSON
    export_plant_button = ctk.CTkButton(details_scrollable_frame, text="Export Plant Details",
                                        command=lambda: export_plant_details(selected_plant, x, y))
    export_plant_button.pack(pady=10)

    # Fetch and display events related to the plant
    events = fetch_farm_events()
    related_events = [event for event in events if 'body' in event and any(
        app['args'].get('data_value', {}).get('args', {}).get('x') == float(x) and
        app['args'].get('data_value', {}).get('args', {}).get('y') == float(y)
        for app in event['body'] if app['kind'] == 'parameter_application')]

    local_tz = pytz.timezone('America/Winnipeg')  # Central Daylight Time (CDT)

    if related_events:
        ctk.CTkLabel(details_scrollable_frame, text="Related Events:", anchor=W).pack(pady=10, anchor=W)
        for event in related_events:
            start_time = event['start_time']
            end_time = event['end_time']
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')).astimezone(local_tz)
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')).astimezone(local_tz)
            duration_weeks = (end_dt - start_dt).days // 7
            event_label = ctk.CTkLabel(details_scrollable_frame, text=f"Event: {start_dt} to {end_dt} ({duration_weeks} weeks)", anchor=W)
            event_label.pack(pady=2, anchor=W)
            delete_button = ctk.CTkButton(details_scrollable_frame, text="Delete Event",
                                          command=lambda e=event['id']: delete_farm_event(e))
            delete_button.pack(pady=2)
    else:
        # Add a button to create a farm event if no related events are found
        create_event_button = ctk.CTkButton(details_scrollable_frame, text="Create Farm Event",
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
    popup.geometry("350x200")

    # Frame for better layout management
    frame = ctk.CTkFrame(popup)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Label
    label = ctk.CTkLabel(frame, text="Select distance for the photo:")
    label.pack(pady=(10, 20))

    # Dropdown for distance selection using CTkComboBox
    distance_var = StringVar(value="medium")
    distance_dropdown = ctk.CTkComboBox(frame, variable=distance_var, values=["close", "medium", "far"])
    distance_dropdown.pack(pady=(0, 20))

    # Confirm button
    confirm_button = ctk.CTkButton(frame, text="Take Photo",
                                   command=lambda: [start_photo_process(selected_plant, x, y, distance_var.get()), popup.destroy()])
    confirm_button.pack(pady=(20, 10))

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)


def start_photo_process(selected_plant, x, y, distance):
    # Create a loading screen
    loading_popup = Toplevel(root)
    loading_popup.title("Taking Photo")
    loading_popup.geometry("300x150")

    loading_label = ctk.CTkLabel(loading_popup, text="Taking photo, please wait...")
    loading_label.pack(pady=10)

    progress_bar = ctk.CTkProgressBar(loading_popup)
    progress_bar.pack(pady=20)
    progress_bar.set(0)

    # Update the progress bar in a separate thread
    def update_progress():
        for i in range(30):
            sleep(1)
            progress_bar.set(i / 30)

        # Close the loading popup and show the photo
        loading_popup.destroy()
        show_photo(selected_plant, x, y)

    # Start the photo process in a separate thread to avoid blocking the UI
    threading.Thread(target=lambda: [take_photo(selected_plant, x, y, distance), update_progress()]).start()


def prompt_moisture_level(selected_plant, x, y):
    popup = Toplevel(root)
    popup.title("Create Farm Event")
    popup.geometry("400x400")  # Adjusted size

    # Frame for better layout management
    frame = ctk.CTkFrame(popup)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(frame, text="Enter the moisture level (0-100):", text_color="white").pack(pady=10)
    moisture_var = StringVar()
    moisture_entry = ctk.CTkEntry(frame, textvariable=moisture_var)
    moisture_entry.pack(pady=10)

    ctk.CTkLabel(frame, text="Enter duration in weeks:", text_color="white").pack(pady=10)
    duration_var = StringVar()
    duration_entry = ctk.CTkEntry(frame, textvariable=duration_var)
    duration_entry.pack(pady=10)

    ctk.CTkLabel(frame, text="Select event time:", text_color="white").pack(pady=10)
    time_var = StringVar(value="15:30")
    time_dropdown = ctk.CTkComboBox(frame, values=["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00",
                                                   "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
                                                   "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"])
    time_dropdown.set("15:30")
    time_dropdown.pack(pady=10)

    confirm_button = ctk.CTkButton(frame, text="Create Event",
                                   command=lambda: create_farm_event(selected_plant, x, y, moisture_var.get(), duration_var.get(), time_dropdown.get(), popup))
    confirm_button.pack(pady=10)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)



def show_error_message(message):
    popup = Toplevel(root)
    popup.title("Error")
    popup.geometry("300x150")

    frame = ctk.CTkFrame(popup)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(frame, text=message, text_color="red").pack(pady=10)
    ctk.CTkButton(frame, text="OK", command=popup.destroy).pack(pady=10)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)


def check_event_overlap(events, start_time, end_time, buffer_minutes=10):
    buffer_delta = timedelta(minutes=buffer_minutes)
    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

    for event in events:
        event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
        event_end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))

        if (start_time - buffer_delta <= event_end) and (end_time + buffer_delta >= event_start):
            return True
    return False



def create_farm_event(selected_plant, x, y, moisture_level, duration_weeks, event_time, popup):
    try:
        moisture_level = int(moisture_level)
        duration_weeks = int(duration_weeks)
        event_hour, event_minute = map(int, event_time.split(":"))
    except ValueError:
        show_error_message("Invalid input. Please enter numerical values for moisture level, duration, and a valid time.")
        return

    # Extract and clean the iss value
    iss = TOKEN['token']['unencoded']['iss'].strip('/')
    if not iss.startswith('http'):
        iss = f"https://{iss}"
    else:
        iss = f"{iss}"

    # Get the local timezone
    local_tz = pytz.timezone('America/Winnipeg')

    # Calculate next day's date and time in local timezone
    now = datetime.now(local_tz)
    start_time_local = now.replace(hour=event_hour, minute=event_minute, second=0, microsecond=0) + timedelta(days=1)
    end_time_local = start_time_local + timedelta(weeks=duration_weeks)

    # Convert to UTC
    start_time_utc = start_time_local.astimezone(pytz.utc)
    end_time_utc = end_time_local.astimezone(pytz.utc)

    # Format as ISO 8601 strings
    start_time_iso = start_time_utc.isoformat()
    end_time_iso = end_time_utc.isoformat()

    # FarmBot API endpoint for creating farm events
    farmbot_url = f"{iss}/api/farm_events"
    farmbot_headers = {'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
                       'content-type': 'application/json'}

    # Payload for creating the farm event with adjusted time
    payload = {
        "start_time": start_time_iso,
        "end_time": end_time_iso,
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

    # Close the popup window if the request is successful
    popup.destroy()



def show_popup_message(message):
    popup = Toplevel(root)
    popup.title("Notification")

    # Set dark mode for the pop-up
    ctk.set_appearance_mode("dark")

    popup_frame = ctk.CTkFrame(popup)
    popup_frame.pack(padx=20, pady=20)

    ctk.CTkLabel(popup_frame, text=message).pack(pady=10)
    ctk.CTkButton(popup_frame, text="OK", command=popup.destroy).pack(pady=10)

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)


def delete_farm_event(event_id):
    # Extract and clean the iss value
    iss = TOKEN['token']['unencoded']['iss'].strip('/')
    if not iss.startswith('http'):
        iss = f"https://{iss}"
    else:
        iss = f"{iss}"

    # FarmBot API endpoint for deleting farm events
    farmbot_url = f"{iss}/api/farm_events/{event_id}"
    farmbot_headers = {'Authorization': 'Bearer ' + TOKEN['token']['encoded'],
                       'content-type': 'application/json'}

    # Make the request to delete the farm event
    response = requests.delete(farmbot_url, headers=farmbot_headers)

    if response.status_code == 200:  # No Content status code indicates success
        print(f"Farm event {event_id} deleted successfully.")
        show_popup_message(f"Event {event_id} deleted successfully.")
    else:
        print(f"Failed to delete farm event {event_id}.")
        show_popup_message(f"Failed to delete event {event_id}.")




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


def export_plant_details(selected_plant, x, y):
    plant_data = {
        "Plant ID": selected_plant['Plant ID'],
        "Plant Type": selected_plant['Plant Type'],
        "Species": selected_plant['Species'],
        "Scientific Name": selected_plant['Scientific Name'],
        "Start Date": selected_plant['Start Date'],
        "FarmBot Coordinates": selected_plant['FarmBot Coordinates'],
        "X Coordinate": x,
        "Y Coordinate": y,
        "Seed Bag IDs": selected_plant.get('Seed Bag IDs'),
        "Location": selected_plant.get('Location'),
        "End Date": selected_plant.get('End Date'),
        "Growing": selected_plant.get('Growing')
    }

    # Use the same logic as show_photo to find the closest image
    z_values = [-200, -110, -50]  # Possible z-values based on distances (close, medium, far)
    closest_image = None

    for z in z_values:
        closest_image = find_closest_image(images, float(x), float(y), z)
        if closest_image:
            break

    if closest_image:
        plant_data["Image URL"] = closest_image['attachment_url']
        response = requests.get(closest_image['attachment_url'])
        image_data = response.content

        # Replace slashes in plant ID with dots
        safe_plant_id = selected_plant['Plant ID'].replace('/', '.')

        # Prompt user to save the JSON file with default filename
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 initialfile=f"{safe_plant_id}.json",
                                                 filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            # Save the plant data to JSON
            with open(file_path, 'w') as json_file:
                json.dump(plant_data, json_file, indent=4)

            # Save the image
            image_file_path = file_path.replace('.json', '.jpg')
            with open(image_file_path, 'wb') as image_file:
                image_file.write(image_data)
            print(f"Plant details and image saved to {file_path} and {image_file_path}")
    else:
        print("No image found close to the given coordinates.")



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

# Create a scrollable frame for the listbox
scrollable_frame = ctk.CTkScrollableFrame(root, width=300)
scrollable_frame.pack(side=LEFT, fill="y", padx=10, pady=10, expand=True)

# Create a scrollable frame for the plant details
details_scrollable_frame = ctk.CTkScrollableFrame(root, width=300)
details_scrollable_frame.pack(side=RIGHT, fill="both", expand=True, padx=10, pady=10)


# Create a checkbox to filter plants with FarmBot coordinates
show_farmbot_only = BooleanVar(value=True)  # Default to only showing FarmBot plants


# Create a button to fetch and display plant names
fetch_button = ctk.CTkButton(root, text="Fetch Plant Names", command=lambda: display_plant_names(plants_info))
fetch_button.pack(pady=10)



# Create a button to export the data to a JSON file
export_button = ctk.CTkButton(root, text="Export to JSON", command=export_to_json)
export_button.pack(pady=10)

# Create a label for logs at the bottom of the window
log_label = ctk.CTkLabel(root, text="Logs will be shown here", anchor=W)
log_label.pack(side="bottom", fill="x", padx=10, pady=5)

# Fetch the initial plant data and display
plants_info = fetch_plant_data()
display_plant_names(plants_info)

# Start the GUI main loop
root.mainloop()
