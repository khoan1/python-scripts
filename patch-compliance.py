# patch-compliance.py

# This script checks if there are updates available on current operating system and performs system update
# Some Linux package(s) won't be updated due to phasing (meaning Linux is delaying updates to be rolled out in phases)
# Script will show phasing package(s) and phase warning if phasing exists

import platform     # Module for detecting OS type (Windows, Linux, etc.)
import subprocess   # Module to run system commands
from datetime import datetime   # For timestamping

# Run the given system command (command parameter is a list)
def run_command(command, shell=False):
    try:
        # Run the command, capture its output as text
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.stdout.strip()    # Returns output as a string
    except Exception as error:
        return str(error)

# Install PSWindowsUpdate module without prompts
def install_pswindowsupdate():
    install_script = '''
    Install-PackageProvider -Name NuGet -Force -Scope CurrentUser
    Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
    Install-Module -Name PSWindowsUpdate -Force -AllowClobber -Scope CurrentUser
    Import-Module PSWindowsUpdate
    '''
    run_command(["powershell", "-Command", install_script], shell=True)

# Match system type and run_command update accordingly
def check_updates(system):
    if system == "Linux":
        print("[*] Checking for Linux updates...")
        run_command(["sudo", "apt", "update"])      # To refresh package list
        output = run_command(["apt", "list", "--upgradable"])   # To check for upgradeable packages
        # Filter out lines that look like packages and returns the list of outdated packages
        updates = [line for line in output.splitlines() if '/' in line and "Listing..." not in line]

        # Check for deferred phasing message by running upgrade dry-run
        upgrade_output = run_command(["sudo", "apt", "upgrade", "-y"])
        phasing_warning = None
        if "deferred due to phasing" in upgrade_output.lower():
            phasing_warning = "Some updates are deferred due to phasing and will be applied later."

        # Return both updates and warning
        return updates, phasing_warning

    elif system == "Windows":
        print("[*] Checking for Windows updates...")
        install_pswindowsupdate()

        # Run_command PowerShell command to get update info as JSON for easy access
        # Title and KB fields have to be converted to a custom object to avoid outputting null values
        # -Depth 5 is to avoid any nested value from Get-WindowsUpdate
        ps_script = "Import-Module PSWindowsUpdate; Get-WindowsUpdate | ForEach-Object {[PSCustomObject]@{Title=$_.Title;KB=($_.KB -join ', ')}} | ConvertTo-Json -Depth 5"
        output = run_command(["powershell", "-Command", ps_script], shell=True)
        return output.strip(), None
    return f"{system} not supported", None

# Perform updates according to OS type
def apply_updates(system):
    if system == "Linux":
        print("[+] Applying Linux updates...")
        run_command(["sudo", "apt", "upgrade", "-y"])
        return False

    elif system == "Windows":
        print("[+] Applying Windows updates...")
        install_pswindowsupdate()
        
        # Install updates
        install_ps = 'Install-WindowsUpdate -AcceptAll -Confirm:$false'
        run_command(["powershell", "-Command", install_ps], shell=True)

        # Check if reboot is required and return bool value
        check_reboot_ps = '(Get-WindowsUpdate -Install -AcceptAll -Confirm:$false).RebootRequired'
        output = run_command(["powershell", "-Command", check_reboot_ps], shell=True)
        return output.strip().lower() == "true"     # Check if output string is equal to "true"

# Generate report based on update list, update / reboot flag, and OS type
def generate_report(updates, update_flag, system, warning_msg=None, reboot_required=False):
    now = datetime.now().isoformat()
    lines = [f"=== Patch Compliance Report ({system}) ===", f"Generated: {now}", ""]
    # Check if updates parameter is a list, a string, or does not exist
    if updates:
        # If updates is a list
        if isinstance(updates, list):
            lines.append("Outdated Packages:")
            lines.extend(updates)
        # If updates is a string
        else:
            lines.append("Update Output:")
            lines.append(updates)
    # If updates does not exist
    else:
        lines.append("System is up to date.")

    # If deferred phasing warning message exist
    if warning_msg:
        lines.append("")
        lines.append(f"Warning: {warning_msg}")

    # If reboot_required is true, print message
    if reboot_required:
        lines.append("")
        lines.append("Note: A system reboot is required. Please reboot manually.")
        
    lines.append("")
    lines.append(f"Auto Update: {'Delayed' if warning_msg else ('Performed' if update_flag else 'Skipped')}")
    return "\n".join(lines)

if __name__ == "__main__":
    system = platform.system()
    updates, phasing_warning = check_updates(system)
    update_flag = False
    reboot_required = False

    if (system == "Linux" and updates) or (system == "Windows" and "KB" in updates):
        reboot_required = apply_updates(system)
        update_flag = True

    report = generate_report(updates, update_flag, system, phasing_warning, reboot_required)
    print(report)

    with open("patch_compliance_report.txt", "w") as file:
        file.write(report)
