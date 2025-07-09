# check-rdp-ssh-exposure.py

# This script checks if the current operating system is showing open ports for rdp or ssh
# Script will log ports info to JSON file

import platform         # To detect the OS type (Windows, Linux, etc.)
import subprocess       # Run system commands (like netstat or ss)
import json             # Save results in JSON file
from datetime import datetime   # For timestamping

# Run shell/system commands
def run_command(command, shell=False):
    try:
        # Run the command, capture its output as text
        result = subprocess.run(command, capture_output=True, text=True, shell=shell)
        return result.stdout.strip().splitlines(), result.returncode
    except Exception as error:
        return [str(error)], 1

# Linux: Scan open ports using `ss`
def check_open_ports_linux():
    result = {"os": "Linux", "services": []}
    # Run the 'ss -tuln' command to list listening TCP/UDP ports
    output, code = run_command(["ss", "-tuln"])

    # If the command failed, record the error and exit early
    if code != 0:
        result["error"] = "\n".join(output)
        return result

    # Process each line of the output
    for line in output:
        if "LISTEN" in line:
            parts = line.split()
            protocol = parts[0]        # e.g. 'tcp'
            # Get the second-to-last column, which contains the local address
            local_address = parts[-2]  # e.g. 0.0.0.0:22 or :::3389
            ip_port = local_address.split(":")
            # Take the last element of ip_port as port
            port = ip_port[-1]
            # ip_port[:-1] is everything except the last element, so excluding the port and just take the IP
            ip = ":".join(ip_port[:-1]) or "0.0.0.0"    # default to "0.0.0.0" if IP is empty

            if port in ("22", "3389"):
                result["services"].append({
                    "protocol": protocol,
                    "port": int(port),
                    "bind": ip,
                    "status": "public" if ip in ["0.0.0.0", "::"] else "private"
                })

    # If no port 22 or 3389 are open, print message
    if not result["services"]:
        result["message"] = "No port 22 or 3389 open"
    return result

# Windows: Scan open ports using `netstat`
def check_open_ports_windows():
    result = {"os": "Windows", "services": []}
    # Show all network connections and listening ports
    output, code = run_command(["netstat", "-an"])

    # If the command fails, record the error and exit early
    if code != 0:
        result["error"] = "\n".join(output)
        return result

    # Parse each line
    for line in output:
        if "LISTENING" in line:
            parts = line.split()
            local = parts[1]  # e.g. 0.0.0.0:3389

            if ":" in local:
                # Split from the right side, one time, at the last colon (:)
                ip, port = local.rsplit(":", 1)
                if port in ("22", "3389"):
                    result["services"].append({
                        "protocol": "tcp",
                        "port": int(port),
                        "bind": ip,
                        "status": "public" if ip in ["0.0.0.0", "::"] else "private"
                    })
    
    # If no port 22 or 3389 are open, print message
    if not result["services"]:
        result["message"] = "No port 22 or 3389 open"
    return result

# Main Execution
def main():
    os_type = platform.system()
    scan_data = {
        "timestamp": datetime.now().isoformat(),
        "result": None
    }

    # Run the correct scan depending on OS
    if os_type == "Linux":
        scan_data["result"] = check_open_ports_linux()
    elif os_type == "Windows":
        scan_data["result"] = check_open_ports_windows()
    else:
        scan_data["error"] = "Unsupported OS"

    # Save results to a JSON file
    with open("open_port_scan.json", "w") as json_file:
        json.dump(scan_data, json_file, indent=4)

    print("Scan complete. Output saved to open_port_scan.json")

if __name__ == "__main__":
    main()
