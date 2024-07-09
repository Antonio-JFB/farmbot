# FarmBot Plant Manager

The FarmBot Plant Manager is a Python-based application that interacts with a FarmBot and Notion databases to manage plant data, take photos, and create farm events. This application uses the FarmBot API, Notion API, and several Python libraries to provide a graphical interface for plant management.

## Features

- Fetch plant data from Notion databases
- Display plant details
- Take and display photos of plants using FarmBot
- Create farm events based on plant data
- Export plant data to a JSON file

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- FarmBot account and credentials
- Notion account and integration token
- MQTT broker access

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Dreamchuyito03/farmbot
    cd farmbot
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Requesting an API Token

To interact with the FarmBot API, you need an API token. Follow these steps to request and save the API token:

1. **Request the API token:**

    ```python
    from farmbot import FarmbotToken

    EMAIL = 'your-email@example.com'
    PASSWORD = 'your-password'
    SERVER = 'https://my.farm.bot'

    raw_token = FarmbotToken.download_token(EMAIL, PASSWORD, SERVER)

    # Save the token to a JSON file
    with open('farmbot_authorization_token.json', 'w') as f:
        json.dump(raw_token, f)

    print("API token saved to farmbot_authorization_token.json")
    ```

2. **Run the script to generate the token:**

    ```bash
    python request_token.py
    ```

    Make sure to replace `'your-email@example.com'` and `'your-password'` with your actual FarmBot credentials.

3. **Set your Notion API token and database IDs:**

    Update the `NOTION_TOKEN`, `DATABASE_ID_1`, and `DATABASE_ID_2` variables in the script with your Notion API token and database IDs.

## Usage

1. **Run the application:**

    ```bash
    python farmbot_plant_manager.py
    ```

2. **Application Interface:**

    - **Fetch Plant Names:** Click the "Fetch Plant Names" button to fetch plant data from the Notion databases.
    - **Show Only FarmBot Plants:** Check the box to filter and display only plants with FarmBot coordinates.
    - **Display Plant Details:** Click on a plant name to display its details.
    - **Take Photo:** Click the "Take Photo" button in the plant details to take a photo of the plant using FarmBot.
    - **Create Farm Event:** Click the "Create Farm Event" button in the plant details to schedule a farm event based on the plant's data.
    - **Export to JSON:** Click the "Export to JSON" button to export the fetched plant data to a JSON file.

## Dependencies

The application relies on the following Python libraries:

- `json`
- `requests`
- `threading`
- `paho-mqtt`
- `customtkinter`
- `tkinter`
- `PIL`
- `farmbot`

You can install these dependencies using the `requirements.txt` file provided in the repository.



