# multi-system-audit.py

# This script collects system info on any OS platform and saves info to a .JSON file

# How to Install psulti: On Windows, run "pip install psutil". On Linux, run "sudo apt install python3-psutil"
import psutil       # External library for CPU, RAM, disk, and uptime
import platform     # Access OS, architecture, CPU info
import socket       # Get hostname and IP info
import json         # Used to write output in .json format
from datetime import datetime   # For timestamping

# Function to Collect all system info
def get_system_info():
    info = {}
    info["timestamp"] = datetime.now().isoformat()
    info["hostname"] = socket.gethostname()

    try:
        info["ip_address"] = socket.gethostbyname(info["hostname"])     # Check if IP available for current hostname
    except:
        info["ip_address"] = "Unavailable"

    info["os"] = platform.system()
    info["os_version"] = platform.version()
    info["architecture"] = platform.machine()
    info["cpu"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=False)
    info["cpu_threads"] = psutil.cpu_count(logical=True)
    # Get total memory in bytes > convert to GB > round to 2 decimal
    info["memory_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    # Gets disk size and usage from root / partition
    info["disk_total_gb"] = round(psutil.disk_usage('/').total / (1024 ** 3), 2)
    info["disk_used_percent"] = psutil.disk_usage('/').percent

    try:
        uptime_seconds = datetime.now().timestamp() - psutil.boot_time()
        info["uptime_minutes"] = round(uptime_seconds / 60, 2)
    except Exception as e:
        info["uptime_minutes"] = "Unavailable"

    return info

if __name__ == "__main__":
    data = get_system_info()

    # Output to JSON file
    with open("system_inventory.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("System inventory collected. Saved to system_inventory.json.")
