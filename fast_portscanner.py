import pandas as pd
import socket
from concurrent.futures import ThreadPoolExecutor

# Define a function to scan a single host and port
def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((host, port))
            return True
    except:
        return False

# Define a list of hosts and ports to scan
hosts = ['google.com', 'facebook.com', 'amazon.com']
ports = [80, 443, 8080]

# Scan the hosts and ports using multithreading
results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    for host in hosts:
        for port in ports:
            results.append({'Host': host, 'Port': port, 'Open': executor.submit(scan_port, host, port).result()})

# Create a Pandas DataFrame from the results
df = pd.DataFrame(results)

# Print the results
print(df)
