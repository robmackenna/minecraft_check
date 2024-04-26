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
    # Regular expression to match date and time format in syslog entry
    date_regex = r'^\w{3}\s+\d{1,2}'
    date_match = re.match(date_regex, entry)

    if date_match:
        date_str = date_match.group(0)
        # Convert date string to datetime object
        entry_date = datetime.strptime(date_str, '%b %d')

        # Check if the entry date is yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        if entry_date.month == yesterday.month and entry_date.day == yesterday.day:
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
    # Get yesterday's date
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%b %d')

    # Create the email message
    message = MIMEText(email_body)
    message['Subject'] = f'Minecraft Activity Report from {yesterday_date}'
    message['From'] = sender_email
    message['To'] = receiver_email

    # Connect to the Gmail SMTP server
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, password)

    # Send the email
    server.sendmail(sender_email, receiver_email, message.as_string())

    # Disconnect from the server
    server.quit()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Parse syslog files for Minecraft activity and optionally send an email report.')
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
syslog_paths = ['/var/log/syslog', '/var/log/syslog.1']

# Parse each syslog file
email_body = ""
for path in syslog_paths:
    entries = parse_syslog_file(path)
    # Sort entries from oldest to newest
    entries.sort(key=lambda x: datetime.strptime(re.match(r'^\w{3}\s+\d{1,2}', x).group(0), '%b %d'))
    email_body += "\n".join(entries) + "\n\n"

# Check if the --no-email option is provided
if args.no_email:
    print(email_body)
else:
    send_email(email_body, sender_email, receiver_email, password)
