import logging
import requests
import pandas as pd
from tabulate import tabulate

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

def download_json_file(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error(f"HTTP request failed: {err}")
        return None

    try:
        data = response.json()
    except ValueError:
        logging.error("Failed to parse JSON")
        return None

    return data

def process_data(data):
    # Extract the 'prefixes' and 'ipv6_prefixes' into separate dataframes
    prefixes_df = pd.DataFrame(data['prefixes'])
    ipv6_prefixes_df = pd.DataFrame(data['ipv6_prefixes'])

    # Combine both into a single DataFrame
    combined_df = pd.concat([prefixes_df, ipv6_prefixes_df])
    
    return combined_df

def filter_and_sort(df):
    # Filter rows in the London region
    london_df = df[df['region'] == 'eu-west-2']

    # Filter rows with the AMAZON service
    amazon_df = london_df[london_df['service'] == 'AMAZON']

    # Sort by the column 'ip_prefix'
    amazon_df.sort_values(by=['ip_prefix'], inplace=True)

    # Reset the index
    amazon_df.reset_index(drop=True, inplace=True)

    return amazon_df

def main():
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    logging.info(f"Downloading JSON file from {url}")
    data = download_json_file(url)
    
    if data is None:
        logging.error("Failed to download or parse JSON file")
        return

    logging.info("Processing data")
    df = process_data(data)

    logging.info("Filtering and sorting data")
    final_df = filter_and_sort(df)

    # Print the dataframe in a nice format
    print(tabulate(final_df, headers='keys', tablefmt='psql'))

if __name__ == "__main__":
    main()
