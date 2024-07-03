import json
import requests
import threading
import paho.mqtt.client as mqtt
from time import sleep
from farmbot import Farmbot, FarmbotToken

# Load token from file
with open('farmbot_authorization_token.json', 'r') as f:
    TOKEN = json.load(f)

# Inputs
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

    def execute_mount_command(self):
        command = {
            "kind": "execute",
            "args": {
                "sequence_id": 202660
            },
            "body": [
                {
                    "kind": "parameter_application",
                    "args": {
                        "label": "Tool",
                        "data_value": {
                            "kind": "tool",
                            "args": {
                                "tool_id": 71517
                            }
                        }
                    }
                }
            ]
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    def execute_dismount_command(self):
        command = {
            "kind": "execute",
            "args": {
                "sequence_id": 202661
            }
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

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

    def move_to_coordinates(self, x, y, z):
        command = {
            "kind": "move_absolute",
            "args": {
                "location": {"kind": "coordinate", "args": {"x": x, "y": y, "z": z}},
                "offset": {"kind": "coordinate", "args": {"x": 0, "y": 0, "z": 0}},
                "speed": 100
            }
        }
        client.publish(channel, json.dumps(prepare_message(command)))
        self.busy = False

    def execute_sequence_with_parameters(self, plant_x, plant_y, plant_z, moisture_threshold):
        self.plant_x = plant_x
        self.plant_y = plant_y
        self.plant_z = plant_z
        commands = [
            {
                "kind": "execute",
                "args": {
                    "sequence_id": 202661
                }
            },
            {
                "kind": "execute",
                "args": {
                    "sequence_id": 202660
                },
                "body": [
                    {
                        "kind": "parameter_application",
                        "args": {
                            "label": "Tool",
                            "data_value": {
                                "kind": "tool",
                                "args": {
                                    "tool_id": 71517
                                }
                            }
                        }
                    }
                ]
            },
            {
                "kind": "move",
                "args": {},
                "body": [
                    {
                        "kind": "axis_overwrite",
                        "args": {
                            "axis": "x",
                            "axis_operand": {
                                "kind": "coordinate",
                                "args": {
                                    "x": plant_x,
                                    "y": plant_y,
                                    "z": plant_z
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_overwrite",
                        "args": {
                            "axis": "y",
                            "axis_operand": {
                                "kind": "coordinate",
                                "args": {
                                    "x": plant_x,
                                    "y": plant_y,
                                    "z": plant_z
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_overwrite",
                        "args": {
                            "axis": "z",
                            "axis_operand": {
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
            },
            {
                "kind": "move",
                "args": {},
                "body": [
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "x",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": 5
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "y",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": 0
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "z",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": 0
                                }
                            }
                        }
                    }
                ]
            },
            {
                "kind": "move",
                "args": {},
                "body": [
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "x",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": 0
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "y",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": 0
                                }
                            }
                        }
                    },
                    {
                        "kind": "axis_addition",
                        "args": {
                            "axis": "z",
                            "axis_operand": {
                                "kind": "numeric",
                                "args": {
                                    "number": -425
                                }
                            }
                        }
                    }
                ]
            },
            {
                "kind": "lua",
                "args": {
                    "lua": f"""\
                    -- Define the moisture threshold variable
                    local moisture_threshold = tonumber({moisture_threshold})
                    if not moisture_threshold then
                      send_message("error", "Moisture parameter is not set correctly", "toast")
                    else
                      send_message("info", "Moisture threshold (parsed): " .. tostring(moisture_threshold), "toast")
                    end

                    -- Measure soil moisture reading
                    local pin_59 = 59
                    local soil_moisture = tonumber(read_pin(pin_59, "analog"))
                    local xyz = get_xyz()
                    local read_at = utc() -- Get the current time in UTC

                    new_sensor_reading({{
                      x = xyz.x,
                      y = xyz.y,
                      z = xyz.z,
                      mode = 1,
                      pin = pin_59,
                      value = soil_moisture,
                      read_at = read_at -- Include the time with the sensor reading request
                    }})

                    -- Print soil moisture in logs
                    send_message("info", "Soil moisture reading: " .. tostring(soil_moisture), "toast")

                    -- Debugging: Ensure both variables are numbers
                    send_message("info", "Comparing soil moisture (" .. tostring(soil_moisture) .. ") with threshold (" .. tostring(moisture_threshold) .. ")", "toast")

                    if soil_moisture and moisture_threshold and soil_moisture < moisture_threshold then
                      send_message("info", "Soil moisture is below the threshold. Starting watering sequence.", "toast")
                      -- Dismount the tools
                      dismount_tool()

                      -- Wait for 5 seconds
                      wait(5000)

                      -- Mount watering nozzle
                      mount_tool("Watering Nozzle")

                      -- Move Z to 0
                      move_absolute({{z = 0}})

                      -- Move to plant coordinates
                      move_absolute({plant_x}, {plant_y}, {plant_z})

                      -- Water for 50mL
                      dispense(50)

                      -- Wait for 2 minutes
                      wait(60000)

                      -- Dismount the tools
                      dismount_tool()

                      -- Move back to coordinates (0, 0, 0)
                      move_absolute(0, 0, 0)
                    else
                      send_message("info", "Soil moisture is not below the threshold. Returning to home.", "toast")
                      -- Move back to coordinates (0, 0, 0)
                      move_absolute(0, 0, 0)
                    end
                    """
                }
            }
        ]

        for command in commands:
            client.publish(channel, json.dumps(prepare_message(command)))
            sleep(2)  # Ensure enough time for each command to execute

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

if __name__ == '__main__':
    raw_token = FarmbotToken.download_token(EMAIL, PASSWORD, SERVER)
    fb = Farmbot(raw_token)
    handler = MyHandler(fb)
    threading.Thread(target=fb.connect, name="foo", args=[handler]).start()
    print("Enter 'E' for Mount Command, 'M' for Dismount Command, 'P' to Take a Photo, 'C' to Move to Coordinates, or 'S' to Execute Sequence:")

    while True:
        action = input("> ")
        if action == 'E':
            handler.add_job(handler.execute_mount_command)
        elif action == 'M':
            handler.add_job(handler.execute_dismount_command)
        elif action == 'P':
            plant_x = float(input("Enter plant X coordinate: "))
            plant_y = float(input("Enter plant Y coordinate: "))
            plant_z = float(input("Enter plant Z coordinate: "))
            handler.add_job(lambda: handler.take_photo(plant_x, plant_y, plant_z))
        elif action == 'C':
            x = float(input("Enter X coordinate: "))
            y = float(input("Enter Y coordinate: "))
            z = float(input("Enter Z coordinate: "))
            handler.add_job(lambda: handler.move_to_coordinates(x, y, z))
        elif action == 'S':
            plant_x = float(input("Enter plant X coordinate: "))
            plant_y = float(input("Enter plant Y coordinate: "))
            plant_z = float(input("Enter plant Z coordinate: "))
            moisture_threshold = float(input("Enter moisture threshold: "))
            handler.add_job(lambda: handler.execute_sequence_with_parameters(plant_x, plant_y, plant_z, moisture_threshold))
        handler.try_next_job()
