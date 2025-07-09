# auto-file-backup.py

# This script backs up files on the current operating system, saves files to local directory, and uploads files to remote Linux server
# If Linux, "/etc" and "/home" folders; Else if Windows, "C:\\Data" will be backed up. (can be changed to any folder)

# Try importing paramiko, prompt for manual install if not present
try:
    import paramiko # SSH/SFTP library to upload files to remote server
except ImportError:
    print("Paramiko (used for remote file upload) not installed. Please run on Windows: pip install paramiko; on Linux: sudo apt install python3-paramiko")
    exit(1)

import os           # For interacting with the file system
import tarfile      # For creating .tar.gz backups on Linux/macOS
import zipfile      # For creating .zip backups on Windows
import platform     # Used to detect the OS type (Windows, Linux, etc.)
import getpass      # For securely prompting password
from datetime import datetime   # For timestamping

# Configuration Setup
BACKUP_PATHS = ["/etc", "/home"] if os.name != "nt" else ["C:\\Data"]     # Set backup source paths based on OS, "nt" means Windows
BACKUP_OUTPUT_DIR = os.path.expanduser("~/backups") if os.name != "nt" else "C:\\Backups"   # Set local backup destination folder (~/backups or C:\Backups)
REMOTE_HOST = "your.vps.ip"     # IP address or hostname of remote server
REMOTE_PORT = 22                # SSH port (22 by default)
REMOTE_USER = "youruser"        # Remote SSH username
REMOTE_PASS = getpass.getpass("Enter remote server password: ")    # SSH password (can be replaced with SSH key)
REMOTE_DIR = "/home/youruser/remote-backups"    # Directory on remote server to upload to

# Create backup based on system type
def create_backup(backup_paths, output_dir):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")    # e.g. "20250706-153012"
    system = platform.system()
    
    os.makedirs(output_dir, exist_ok=True)      # make sure output directory exists, create if not exist

    # Construct the backup filename (e.g., backup-Windows-20250706-153012)
    backup_file = os.path.join(output_dir, f"backup-{system}-{timestamp}")
    # Check if OS is Windows or Linux
    if system == "Windows":
        backup_file += ".zip"      # Add .zip extension to the filename
        # Create a ZIP file (zipf) in write mode, ZIP_DEFLATED will compress zip file
        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Loop through each backup path (e.g., C:\Data)
            for path in backup_paths:
                if os.path.exists(path):
                    # Recursively walk through all folders and files, _ means subfolders (ignore them here)
                    for root, _, files in os.walk(path):
                        for each_file in files:
                            # Create full path to file (e.g. "C:\\Data\\Project\\file2.txt")
                            full_path = os.path.join(root, each_file)
                            # Create relative path to file (e.g. "Project\\file2.txt")
                            rel_path = os.path.relpath(full_path, path)
                            # Add file to ZIP archive with correct folder layout
                            # full_path is where the file is now (on disk)
                            # os.path.join("Data", "Project\\file2.txt") --> "Data\\Project\\file2.txt" (how file should appear inside the ZIP file)
                            zipf.write(full_path, os.path.join(os.path.basename(path), rel_path))
    else:
        backup_file += ".tar.gz"    # Add .tar.gz extension to filename
        # Create tar.gz archive file
        with tarfile.open(backup_file, "w:gz") as tar_file:
            # Loop through each folder to back up
            for path in backup_paths:
                if os.path.exists(path):
                    # Add the whole folder into the tar archive
                    # arcname=os.path.basename(path) stores only the folder name in the archive instead of the full path
                    tar_file.add(path, arcname=os.path.basename(path))
    return backup_file     # returns the file path string to created backup file

# Upload backup file to remote server via paramiko (SFTP)
def upload_to_remote(local_path, remote_path):
    try:
        # Create SSH transport connection to remote host
        transport = paramiko.Transport((REMOTE_HOST, REMOTE_PORT))
        transport.connect(username=REMOTE_USER, password=REMOTE_PASS)
        # Create an SFTP session over the transport
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_filename = os.path.basename(local_path)      # Get only the file name from the full local path
        remote_full_path = f"{remote_path.rstrip('/')}/{remote_filename}"   # Format as Linux style path

        # Try to change into the remote backup directory
        try:
            sftp.chdir(remote_path)     # Does the directory exist?
        except IOError:
            sftp.mkdir(remote_path)     # If not, create it

        # Upload the local file to the remote directory
        sftp.put(local_path, remote_full_path)
        # Close connections cleanly
        sftp.close()
        transport.close()

        print(f"[+] Uploaded {local_path} to {remote_full_path}")
    except Exception as error:
        print(f"[!] Upload failed: {error}")

# Main function
if __name__ == "__main__":
    print("[*] Starting backup process...")

    backup_file = create_backup(BACKUP_PATHS, BACKUP_OUTPUT_DIR)
    print(f"[+] Backup created at {backup_file}")

    upload_to_remote(backup_file, REMOTE_DIR)
