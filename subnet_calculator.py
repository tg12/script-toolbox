# Description: This script is used to calculate subnet information
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/

def calculate_subnet(ip_address, mask):
    # Split the IP address and subnet mask into their respective parts
    ip_parts = ip_address.split("/")
    ip = ip_parts[0]
    mask = int(ip_parts[1])

    # Convert the IP address and mask to binary
    ip_binary = "".join([bin(int(x) + 256)[3:] for x in ip.split(".")])
    mask_binary = "1" * mask + "0" * (32 - mask)

    # Calculate the network address and broadcast address
    network_address_binary = ip_binary[:mask] + "0" * (32 - mask)
    broadcast_address_binary = ip_binary[:mask] + "1" * (32 - mask)

    # Convert the binary values to decimal notation
    network_address = ".".join([str(int(x, 2)) for x in [network_address_binary[0:8], network_address_binary[8:16], network_address_binary[16:24], network_address_binary[24:32]]])
    broadcast_address = ".".join([str(int(x, 2)) for x in [broadcast_address_binary[0:8], broadcast_address_binary[8:16], broadcast_address_binary[16:24], broadcast_address_binary[24:32]]])

    # Calculate the range of host addresses
    host_min = network_address.split(".")
    host_max = broadcast_address.split(".")

    # Increment the fourth octet of the minimum host address by 1
    host_min[3] = str(int(host_min[3]) + 1)

    # Decrement the fourth octet of the maximum host address by 1
    host_max[3] = str(int(host_max[3]) - 1)

    # Calculate the number of valid hosts
    num_hosts = 2 ** (32 - mask) - 2

    # Return the results
    return (network_address, broadcast_address, ".".join(host_min), ".".join(host_max), num_hosts)

# Prompt the user to enter the IP address and subnet mask
ip_address = input("Enter the IP address and subnet mask (in CIDR notation): ")

try:
    # Split the IP address and subnet mask into their respective parts
    ip_parts = ip_address.split("/")
    ip = ip_parts[0]
    mask = int(ip_parts[1])

    # Calculate the subnet information
    network_address, broadcast_address, host_range_min, host_range_max, num_hosts = calculate_subnet(ip_address, mask)

    # print the results using tabulate

    from tabulate import tabulate

    headers = ["Network address", "Broadcast address", "Range of hosts", "Number of hosts"]

    data = [[network_address, broadcast_address, host_range_min + " - " + host_range_max, num_hosts]]

    print(tabulate(data, headers, tablefmt="grid"))


except ValueError:
    print("Error: Invalid IP address or subnet mask")
