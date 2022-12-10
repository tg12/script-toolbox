# Description: This script is used to convert domain suffixes to hexadecimal for use in DHCP option 43
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/


"""
The domain suffixes presented in hexadecimal with a number indicate the length in front of it. For example, "draytek.com"
should be presented as "076472617974656b03636f6d" where 07 means there are 7 characters followed, 6472617974656b is "draytek",
03 means there are 3 characters followed, and 636f6d is "com"""


""" This tool is specifically designed for DreyTek routers. It allows users to easily configure and manage their DreyTek routers,
including setting up network security, parental controls, and other advanced features.

Disclaimer: This tool is not affiliated with or endorsed by DreyTek. Use of this tool is at your own risk.
We are not responsible for any damage or data loss that may result from using this tool.
Please make sure to backup your router settings before using this tool. """


# https://www.draytek.com/support/knowledge-base/5314

def domain_to_hex(domain):
    # Split the domain into its individual segments
    segments = domain.split(".")

    # Initialize a list to store the hexadecimal representation of each segment
    hex_segments = []

    # Loop through each segment of the domain
    for segment in segments:
        # Convert the segment to its hexadecimal representation
        hex_segment = segment.encode("utf-8").hex()

        # Add the length of the segment (in hexadecimal) to the beginning of
        # the hexadecimal representation
        hex_segment = "{:02x}".format(len(segment)) + hex_segment

        # Add the segment to the list of hexadecimal segments
        hex_segments.append(hex_segment)

    # Join the hexadecimal segments together with a "." to create the final
    # hexadecimal representation of the domain
    hex_domain = "".join(hex_segments)

    return hex_domain


def create_dhcp_43(domain_suffixes):
    # Convert the domain suffixes to their hexadecimal representation
    hex_suffixes = domain_to_hex(domain_suffixes)

    # Create the 6-byte DHCP option 43 by concatenating the hexadecimal representation of the domain suffixes
    # with the necessary padding to make the total length 6 bytes
    dhcp_43 = hex_suffixes + "00" * (6 - (len(hex_suffixes) // 2))

    return dhcp_43


# Test the function with the domain "local.lan"
print(domain_to_hex("local.lan"))  # should output "056c6f63616c036c616e"

print(domain_to_hex("192.168.1.250"))
