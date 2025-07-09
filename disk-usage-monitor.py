# disk-usage-monitor.py

# This script checks if system disk usage is more than set threshold.
# If disk usage is more than threshold, script will log usage info and send an email alert
# To use email functionality, please include a .env file with the following info:
    # SMTP_SERVER=smtp.gmail.com
    # SMTP_PORT=587
    # EMAIL_SENDER=youremail@gmail.com
    # EMAIL_APP_PASSWORD=your_app_password_here
    # EMAIL_RECIPIENT=recipient@example.com

# Dependency check for python-dotenv
try:
    from dotenv import load_dotenv  # Used to load info from .env file
except ImportError:
    print("python-dotenv is not installed.\n"
        "If Windows, please install it using: 'pip install python-dotenv'\n"
        "If Linux, use: 'sudo apt install python3-pip' then 'pip3 install python-dotenv'"
    )
    exit(1)


import os           # For environment variables and file paths
import psutil       # For checking disk usage and partitions
import smtplib      # For sending email
from email.message import EmailMessage  # For formatting email content
from pathlib import Path    # To specify file path
import platform     # To detect the OS type (Windows, Linux, etc.)
import socket       # To get hostname and IP
from datetime import datetime   # For timestamps

# Load the .env file explicitly from current directory
load_dotenv(dotenv_path=Path('.') / 'disk-usage-monitor.env')   # .env file name can be changed

# Configuration from .env file
SMTP_SERVER = os.getenv("SMTP_SERVER")          # e.g., smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # fallback to 587 if SMTP_PORT is empty
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
THRESHOLD_PERCENT = 80  # Alert threshold
LOG_FILE = 'disk_usage_monitor.log'

# Send alert email using SMTP
def send_email(subject, body):
    msg = EmailMessage()    # Used to format email
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = subject
    msg.set_content(body)

    # Try to connect to SMTP to send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as error:
        log_event(f"Failed to send email: {error}")
        return False

# Log events to both file and stdout
def log_event(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"{timestamp} - {message}"
    print(entry)
    # Append to log file
    with open(LOG_FILE, 'a') as file:
        file.write(entry + '\n')

# Get system hostname and IP
def get_hostname_ip():
    hostname = socket.gethostname()         # Get device name
    try:
        ip = socket.gethostbyname(hostname) # Get IP address
    except:
        ip = 'Unknown IP'
    return hostname, ip

# Main function to check disk usage and send alert if needed
def check_disk_usage():
    hostname, ip = get_hostname_ip()
    partitions = psutil.disk_partitions(all=False)  # Get mounted disks

    alert_triggered = False
    alert_messages = []

    # Loops through all disk partitions. If access is denied, it skips the drive.
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)  # Get disk usage stats
        except PermissionError:
            continue  # Skip drives we can't access

        percent_used = usage.percent
        msg = f"Drive {part.device} mounted on {part.mountpoint}: {percent_used}% used."

        if percent_used >= THRESHOLD_PERCENT:
            alert_triggered = True
            alert_messages.append(msg)

        log_event(msg)

    if alert_triggered:
        subject = f"Disk Usage Alert on {hostname} ({ip})"
        body = "Warning: Disk usage exceeded threshold!\n\n" + "\n".join(alert_messages)
        if send_email(subject, body):
            log_event("Alert email sent successfully.")
        else:
            log_event("Alert email failed to send.")

if __name__ == "__main__":
    check_disk_usage()
