"""
DISCLAIMER:
This script is provided for educational purposes only. 
It attempts to check if a given Reddit user might be shadowbanned by analyzing publicly available information on Reddit's old interface. The method used is based on common indicators and should not be considered foolproof or entirely reliable. Shadowban detection can be complex and subject to Reddit's internal mechanisms, which are not publicly disclosed.
Furthermore, this script simulates web requests with randomized headers to mimic different user agents and preferences. While this approach is common in web scraping and testing, users should be mindful of Reddit's terms of service and guidelines regarding automated access and user privacy.
The creators of this script cannot guarantee its accuracy, effectiveness, or compliance with Reddit's policies at all times. Users should use this tool responsibly and at their own risk. No responsibility is assumed for any consequences directly or indirectly related to any action or inaction you take based on the information, services, or other material provided.
It's also important to respect privacy and not use this tool for any form of harassment or violation of Reddit's community standards.
USE AT YOUR OWN RISK.
"""

import logging
import random
import sys

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to generate randomized headers

def generate_headers():
    user_agent = UserAgent().random
    accept_language = random.choice(
        ['en-US,en;q=0.9', 'en;q=0.8', 'en-US;q=0.7,en;q=0.3'])
    accept_encoding = random.choice(['gzip, deflate, br', 'identity'])
    headers = {
        'User-Agent': user_agent,
        'Accept-Language': accept_language,
        'Accept-Encoding': accept_encoding,
        'DNT': '1',  # Do Not Track requests header
        'Upgrade-Insecure-Requests': '1'
    }
    return headers

def check_shadowban(username):
    url = f"https://old.reddit.com/user/{username}"
    headers = generate_headers()

    logging.info(f"Checking user: {username}")

    response = requests.get(url, headers=headers)

    # debug, what is the status code and the text
    # print(response.status_code)
    # print(response.text)

    if response.status_code == 404:
        logging.info("Successfully retrieved the page (404 Not Found) Correct Page for shadowban check.")
        if "the page you requested does not exist" in response.text and f"u/{username}: page not found" in response.text:
            logging.info(f"Forbidden: The user '{username}' is potentially shadowbanned.")
            return True
    elif response.status_code == 200:
        logging.info("Successfully retrieved the page (200 OK)")
        logging.info(f"Success: The user '{username}' does not appear to be shadowbanned.")
        return False
    else:
        logging.warning(f"Failed to retrieve the page, status code: {response.status_code}")
        return False

    return False

disclaimer = """
DISCLAIMER:
-=-=-=-=-=-
This script is provided for educational purposes only. 
It attempts to check if a given Reddit user might be shadowbanned by analyzing publicly available information on Reddit's old interface. The method used is based on common indicators and should not be considered foolproof or entirely reliable. Shadowban detection can be complex and subject to Reddit's internal mechanisms, which are not publicly disclosed.
Furthermore, this script simulates web requests with randomized headers to mimic different user agents and preferences. While this approach is common in web scraping and testing, users should be mindful of Reddit's terms of service and guidelines regarding automated access and user privacy.
The creators of this script cannot guarantee its accuracy, effectiveness, or compliance with Reddit's policies at all times. Users should use this tool responsibly and at their own risk. No responsibility is assumed for any consequences directly or indirectly related to any action or inaction you take based on the information, services, or other material provided.
It's also important to respect privacy and not use this tool for any form of harassment or violation of Reddit's community standards.
-=-=-=-=-=-
USE AT YOUR OWN RISK.
"""

# Function to display disclaimer and require user agreement
def require_agreement():
    print(disclaimer)
    agreement = input("Type 'I AGREE' to accept the terms and proceed: ").strip()
    if agreement.upper() != "I AGREE":
        logging.info("You did not agree to the disclaimer. Exiting.")
        sys.exit()


if __name__ == "__main__":
    require_agreement()
    logging.info(
        "Warning: You need to be logged out from Reddit for this check to work correctly.")
    logged_out = input("Are you logged out? (Y/N): ").strip().upper()

    if logged_out == "Y":
        username = input("Enter the Reddit username to check: ").strip()
        if check_shadowban(username):
            logging.info(f"The user '{username}' is potentially shadowbanned.")
        else:
            logging.info(
                f"The user '{username}' does not appear to be shadowbanned.")
    else:
        logging.error("Please log out from Reddit and try again.")
