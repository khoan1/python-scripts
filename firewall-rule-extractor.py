# firewall-rule-extractor.py

# This script extracts firewall rules based on operating system and saves the rules to a JSON file

import platform         # Detect the OS type (Windows, Linux, etc.)
import subprocess       # Run shell or Powershell commands
import json             # Format and save output as JSON
from datetime import datetime   # For timestamping

# Reusable function to run shell commands
def run_command(command, shell=False):
    try:
        # Run the command, capture its output as text
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as error:
        return str(error), 1

# Grab Windows Defender rules via PowerShell
def get_windows_firewall_rules():
    cmd = [
        "powershell", "-Command",
        "Get-NetFirewallRule | Select-Object DisplayName, Direction, Action, Enabled, Profile | ConvertTo-Json"
    ]
    output, code = run_command(cmd, shell=True)
    # If no error code and output exists
    if code == 0 and output:
        try:
            rules = json.loads(output)
            return {"firewall_type": "Windows Defender Firewall", "rules": rules}
        except json.JSONDecodeError:
            return {"error": "Failed to parse PowerShell JSON output"}
    else:
        return {"error": output}

# Check UFW rules on Linux
def get_ufw_rules():
    output, code = run_command(["ufw", "status", "numbered"])
    if code == 0:
        rule_lines = output.splitlines()
        return {"firewall_type": "UFW", "rules": rule_lines}
    else:
        return {"error": output}

# Check iptables if not using UFW
def get_iptables_rules():
    output, code = run_command(["iptables", "-S"])
    if code == 0:
        rule_lines = output.splitlines()
        return {"firewall_type": "iptables", "rules": rule_lines}
    else:
        return {"error": output}

# Main function to run the logic
def main():
    system = platform.system()
    firewall_data = {
        "timestamp": datetime.now().isoformat(),
        "os": system
        "firewall": None
    }

    # Match system type then initialize "firewall" and assign with firewall rules
    if system == "Windows":
        firewall_data["firewall"] = get_windows_firewall_rules()
    elif system == "Linux":
        which_ufw, code = run_command(["which", "ufw"])     # Check if ufw path exists
        if code == 0:
            firewall_data["firewall"] = get_ufw_rules()
        else:
            firewall_data["firewall"] = get_iptables_rules()
    else:
        firewall_data["error"] = "Unsupported operating system"

    # Save to JSON log file
    with open("firewall_rules.json", "w") as json_file:
        json.dump(firewall_data, json_file, indent=4)

    print("Firewall rules extracted and saved to firewall_rules.json")

if __name__ == "__main__":
    main()
