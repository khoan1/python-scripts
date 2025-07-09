# failed-login-audit.py

# This script checks different OS platform for failed login attempts and parses failed login info to .JSON file

import platform     # Detect the OS type (Windows, Linux, etc.)
import subprocess   # Run shell commands
import re           # Match patterns in text
import json         # Work with JSON files
from datetime import datetime   # For timestamping

# Run system command and return output and exit code
def run_command(command, shell=False):
    try:
        # Run the command, capture its output as text
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as error:
        return str(error), 1

# Wrap an error message into a standard dict and return a list object
def make_error(message):
    return [{"error": message}]

# Parse Linux failed login attempts from /var/log/auth.log
def parse_linux_failed_logins():
    log_path = "/var/log/auth.log"
    failed_logins = []

    try:
        with open(log_path, "r") as file:
            for line in file:
                if "Failed password" in line:
                    match = re.search(r'^(\S+)\s+\S+\s+sshd\[\d+\]: Failed password for (\w+) from (\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        timestamp = match.group(1)
                        username = match.group(2)
                        ip = match.group(3)
                        failed_logins.append({"timestamp": timestamp, "username": username, "ip": ip})
    except FileNotFoundError:
        return make_error(f"{log_path} not found or inaccessible")

    return failed_logins

# Parse Windows failed login attempts (Event ID 4625)
def parse_windows_failed_logins():
    failed_logins = []
    powershell_cmd = (
        'Get-WinEvent -FilterHashtable @{LogName="Security"; Id=4625} | '
        'Select-Object -First 50 -Property @{Name="TimeCreated";Expression={($_.TimeCreated).ToString("s")}}, Message | ' 
        'ConvertTo-Json -Depth 3'
    )

    output, code = run_command(["powershell", "-Command", powershell_cmd], shell=True)

    # If command failed or output is empty
    if code != 0 or not output:
        return make_error("Unable to read Windows Event Logs")

    try:
        events = json.loads(output)
        # If result from output is a dict, make it into a list to iterate over easier in loops
        if isinstance(events, dict):
            events = [events]

        for entry in events:
            time = entry.get("TimeCreated")
            msg = entry.get("Message", "")      # If the "Message" field doesn't exist, defaults to an empty string
            match = re.search(
                # re.DOTALL includes matching new line characters since error message can be multi-line string
                r'Account For Which Logon Failed:\s+Security ID:\s+.*?\s+Account Name:\s+(.*?)\s', msg, re.DOTALL
            )
            if match:
                username = match.group(1).strip()
                failed_logins.append({
                    "timestamp": time,
                    "username": username,
                    "source": "Windows Security Log"
                })
    except json.JSONDecodeError:
        return make_error("Error parsing JSON from PowerShell output")

    return failed_logins

# Main logic to detect platform and write log file
def main():
    system = platform.system()
    timestamp = datetime.now().isoformat()
    # log_data is a dict with "failed_logins" initialized as an empty list (to be filled)
    log_data = {
        "timestamp": timestamp,
        "system": system,
        "failed_logins": []
    }

    if system == "Linux":
        log_data["failed_logins"] = parse_linux_failed_logins()
    elif system == "Windows":
        log_data["failed_logins"] = parse_windows_failed_logins()
    else:
        log_data["failed_logins"] = make_error(f"Unsupported OS: {system}")

    # Save result to JSON file
    output_file = "failed_login_report.json"
    with open(output_file, "w") as json_file:
        json.dump(log_data, json_file, indent=4)

    print(f"[*] Failed login report saved to: {output_file}")

if __name__ == "__main__":
    main()
