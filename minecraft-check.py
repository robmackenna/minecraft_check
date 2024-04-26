#!/usr/bin/python3

import re
import smtplib
import argparse
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import configparser
import os

# Function to parse syslog entries
def parse_syslog_entry(entry):
    # Regular expression to match timestamp format
    timestamp_regex = r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'
    timestamp_match = re.match(timestamp_regex, entry)

    if timestamp_match:
        timestamp_str = timestamp_match.group(0)
        # Append current year to the timestamp string
        timestamp_str += f' {datetime.now().year}'
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(timestamp_str, '%b %d %H:%M:%S %Y')

        # Check if the timestamp is within the last 24 hours
        last_24_hours = datetime.now() - timedelta(hours=24)
        if timestamp >= last_24_hours:
            # Check if the entry contains the word "game"
            if 'game' in entry.lower():
                return entry.strip()  # Return the entry
    
    return None

# Function to parse syslog files
def parse_syslog_file(file_path):
    results = []
    # Open syslog file for reading
    with open(file_path, 'r') as file:
        # Read each line in the file
        for line in file:
            # Check if the line contains a syslog entry
            entry = parse_syslog_entry(line)
            if entry:
                # Add the entry to the results
                results.append(entry)
    return results

# Function to send email
def send_email(email_body, sender_email, receiver_email, password):
    # Create the email message
    message = MIMEText(email_body)
    message['Subject'] = 'Minecraft Activity Report for the Last 24 Hours'
    message['From'] = sender_email
    message['To'] = receiver_email

    # Connect to the Gmail SMTP server with TLS encryption
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)

    # Send the email
    server.sendmail(sender_email, receiver_email, message.as_string())

    # Disconnect from the server
    server.quit()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Parse syslog files for Minecraft activity in the last 24 hours and send an email report.')
parser.add_argument('--no-email', action='store_true', help='Print the email body to the console instead of sending the email')
args = parser.parse_args()

# Get path to config file
config_dir = os.path.expanduser('~/.config/minecraft-check')
config_file = os.path.join(config_dir, 'minecraft-check.conf')

# Read configuration from ~/.config/minecraft-check/minecraft-check.conf
config = configparser.ConfigParser()
config.read(config_file)

sender_email = config.get('Email', 'sender_email')
receiver_email = config.get('Email', 'receiver_email')
password = config.get('Email', 'password')

# Paths to syslog files
syslog_paths = ['/var/log/syslog.1', '/var/log/syslog']

# Parse each syslog file
email_body = ""
for path in syslog_paths:
    entries = parse_syslog_file(path)
    email_body += "\n".join(entries) + "\n\n"

# Check if the --no-email option is provided
if args.no_email:
    print(email_body)
else:
    send_email(email_body, sender_email, receiver_email, password)
