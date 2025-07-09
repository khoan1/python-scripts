# poll-weather.py

# This script polls weather info from specified location using Open-Meteo API
# Script will log weather info to JSON file

import os       # For file path handling
import sys      # For script/system-specific functions
import json     # For working with JSON data
from datetime import datetime   # For timestamping

# Try importing requests, prompt for manual install if not present
try:
    import requests
except ImportError:
    print("Requests (used to get data) not installed. Please run on Windows: pip install requests; on Linux: sudo apt install python3-requests")
    exit(1)

# Set location info
LOCATION_NAME = "Tokyo"
LATITUDE = 35.652832
LONGITUDE = 139.839478

# Open-Meteo API endpoint
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"

# Output log file to where script file is located
LOG_FILE = os.path.join(os.getcwd(), "weather_log.json")

# Handles core logic of contacting the weather API and saving data to log
def poll_weather():
    try:
        response = requests.get(API_URL, timeout=10)    # Makes the HTTP GET request
        response.raise_for_status()     # Raises an error if the response code is not 200 for OK
        weather_data = response.json().get("current_weather", {})   # Parses JSON received from API and extracts "current_weather" info

        # Build a dict with current timestamp, location and weather data
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "name": LOCATION_NAME,
                "latitude": LATITUDE,
                "longitude": LONGITUDE
            },
            "weather": weather_data     # Actual weather data from API
        }

        append_log(log_entry)   # Calls helper function to write log to file
        print(f"[+] Weather logged for {LOCATION_NAME} at {log_entry['timestamp']}")

    except requests.RequestException as error:
        print(f"[!] Weather API request failed: {error}")

# Helper function for appending a new log entry to the JSON file
def append_log(entry):
    logs = []   # Start with an empty list of logs

    # Check if log file exists
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE, "r") as log_file:
            try:
                logs = json.load(log_file)  # Try reading existing logs
            except json.JSONDecodeError:
                logs = []   # If file is corrupted or empty, reset to empty list

    logs.append(entry)  # Add new log entry

    with open(LOG_FILE, "w") as json_file:
        json.dump(logs, json_file, indent=4)    # Write the full updated list back to the JSON file

if __name__ == "__main__":
    poll_weather()
