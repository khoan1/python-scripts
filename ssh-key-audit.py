# ssh-key-audit.py

# This script checks if each user has authorized public SSH keys
# If SSH keys exist, script exports keys info to a .JSON file

import os       # Used for file path operation
import pwd      # Used to retrieve info about local user in UNIX/LINUX system
import json     # Used to convert data into .JSON file
from datetime import datetime   # For timestamping

AUDIT_LOG = "/var/log/ssh_key_audit.json"

# Gathers SSH key data
def get_authorized_keys():
    report = {}
    
    # Iterate through each user account's list of entries
    for user in pwd.getpwall():
        home_dir = user.pw_dir
        username = user.pw_name

        # Skip system users
        if not home_dir.startswith("/home/"):
            continue
        
        # Create path to stored key file (e.g. /home/username/.ssh/authorized_keys)
        auth_keys_path = os.path.join(home_dir, ".ssh", "authorized_keys")

        # Check if file exists
        if os.path.isfile(auth_keys_path):
            try:
                # Open file to read
                with open(auth_keys_path, "r") as file:
                    # Read all non-empty and non-comment (#) lines as public keys
                    keys = [line.strip() for line in file if line.strip() and not line.startswith("#")]

                # Gets file metadata
                file_stat = os.stat(auth_keys_path)
                # Extract last modified timestamp and convert to ISO format 
                last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

                # Saves the data to a dictionary
                report[username] = {
                    "home": home_dir,
                    "authorized_keys_count": len(keys),
                    "last_modified": last_modified,
                    "keys": keys
                }

            except Exception as error:
                report[username] = {"error": str(error)}

    return report

# Ensures script only runs when executed directly, not called as module
if __name__ == "__main__":
    audit_data = {
        "timestamp": datetime.now().isoformat(),
        "users": get_authorized_keys()
    }

    # Save to .JSON log file
    with open(AUDIT_LOG, "w") as json_file:
        json.dump(audit_data, json_file, indent=4)

    print(f"SSH key audit complete. Results saved to {AUDIT_LOG}")
