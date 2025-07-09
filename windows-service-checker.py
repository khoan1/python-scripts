# windows-service-checker.py

# This script checks if Active Directory (AD), Domain Name System (DNS), and Dynamic Host Configuration Protocol (DHCP) services are running
# Script will log result text file

# Usage: Run script only on Windows Server

import os           # Used for file path operation
import platform     # Used to detect the OS type (Windows, Linux, etc.)
from datetime import datetime   # For timestamping

# Attempt to import the pywin32 service utility module (used to check Windows service status)
try:
    import win32serviceutil  # Requires pywin32
except ImportError:
    print("pywin32 is not installed. Please install it using: pip install pywin32")
    exit(1)

# List of Windows services to check
SERVICES = [
    "NTDS",      # Active Directory Domain Services
    "DNS",       # DNS Server
    "DHCPServer" # DHCP Server
]

# # Path to the log file: current directory + "service_status.log"
LOG_FILE = os.path.join(os.getcwd(), "service_status.log")

# Check the status of each service in the list
def check_services(services):
    results = {}    # Dictionary to store service name and its status
    for service in services:
        try:
            # Query the current status of the service
            # win32serviceutil.QueryServiceStatus() returns a tuple, index [1] is the service state code
            status = win32serviceutil.QueryServiceStatus(service)[1]
            # Status code 4 means the service is running
            results[service] = "Running" if status == 4 else "Not Running"
        except Exception as error:
            results[service] = f"Error: {str(error)}"
    return results

if __name__ == "__main__":
    # Ensure this script only runs on Windows
    if platform.system() != "Windows":
        print("This script only works on Windows.")
        exit(1)

    status_report = check_services(SERVICES)

    with open(LOG_FILE, "a") as log:
        log.write(f"\n=== Windows Service Status ({datetime.now().isoformat()}) ===\n")
        for service, status in status_report.items():
            log.write(f"{service}: {status}\n")

    print(f"Service check complete. Results saved to {LOG_FILE}")
