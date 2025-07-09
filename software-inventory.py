# software-inventory.py

# This script pulls a list of software installed on current operating system and logs the list to JSON file

import platform     # Used to detect the OS type (Windows, Linux, etc.)
import os           # For working with file paths and directories
import json         # For saving data in JSON format
import subprocess   # To run external system commands
from datetime import datetime   # For timestamping

# Windows-specific import
if platform.system() == "Windows":
    import winreg   # Used to access Windows Registry to find installed software

# Collect installed software from Windows using winreg
def collect_windows_software():
    uninstall_keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]   # These are the Registry locations where installed programs are listed, r"" means raw string literal
    
    software = []   # List to hold software details

    # Loop through root registry
    # HKEY_LOCAL_MACHINE for system-wide installed software, HKEY_CURRENT_USER for software installed only for the logged-in user
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        # Loop through both registry paths
        for key_path in uninstall_keys:
            try:
                reg_key = winreg.OpenKey(root, key_path)
                # Loop through subkeys (each program)
                for i in range(winreg.QueryInfoKey(reg_key)[0]):
                    # subkey_name is a GUID or app-specific name (e.g., {7DF54EFA-AB4E-4E10-B34D-A3D9C6C45B80})
                    subkey_name = winreg.EnumKey(reg_key, i)
                    subkey_path = key_path + "\\" + subkey_name
                    try:
                        subkey = winreg.OpenKey(root, subkey_path)
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")    # Try to get the "DisplayName" (program name)
                        version, _ = winreg.QueryValueEx(subkey, "DisplayVersion") # Try to get the "DisplayVersion" (version number)
                        software.append({"name": name, "version": version})
                    except FileNotFoundError:
                        continue
                    except OSError:
                        continue
            except OSError:
                continue
    return software

# Collect installed packages from Linux using dpkg
def collect_linux_software():
    try:
        # Run dpkg-query to get package name and version
        output = subprocess.check_output(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\n"], text=True)
        lines = output.strip().split('\n')
        software = []
        for each_line in lines:
            parts = each_line.split('\t')
            if len(parts) == 2:
                software.append({"name": parts[0], "version": parts[1]})
        return software
    except FileNotFoundError:
        return [{"error": "dpkg not available"}]

# Save software list to JSON file
def save_report(data):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")    # e.g., 20250707-123456
    filename = f"software_inventory_{platform.node()}_{timestamp}.json"
    
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)
    
    print(f"[+] Report saved to: {filename}")


def main():
    system = platform.system()      # Get OS name (e.g., "Windows" or "Linux")
    hostname = platform.node()      # Get computer name
    inventory = {
        "hostname": hostname,
        "os": system,
        "timestamp": datetime.now().isoformat()     # e.g., 2025-07-07T12:34:56
    }

    # Based on OS, collect software
    if system == "Windows":
        inventory["software"] = collect_windows_software()
    elif system == "Linux":
        inventory["software"] = collect_linux_software()
    else:
        inventory["error"] = "Unsupported OS"

    save_report(inventory)  # Save the collected data


if __name__ == "__main__":
    main()
