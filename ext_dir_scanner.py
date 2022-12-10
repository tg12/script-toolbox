# Description: This script is used to scan a directory and count the number of files in each directory
# Author: James Sawyer
# Email: githubtools@jamessawyer.co.uk
# Website: http://www.jamessawyer.co.uk/

from tabulate import tabulate
import os
import pandas as pd

# Set the directory to index
directory = "/Users/james/github-archive/repos/"

# Create a dictionary to store the file counts
file_counts = {}

# Recursively iterate through all directories and files in the directory
for root, dirs, files in os.walk(directory):
    for filename in files:
        # Get the file extension
        file_extension = os.path.splitext(filename)[1]

        # If the file extension is not in the dictionary, add it with a count
        # of 1
        if file_extension not in file_counts:
            file_counts[file_extension] = 1
        # Otherwise, increment the count for that file extension
        else:
            file_counts[file_extension] += 1

# Create a dataframe from the file counts dictionary
file_counts_df = pd.DataFrame.from_dict(
    file_counts, orient="index", columns=["Count"])

# Sort the dataframe by the file counts in descending order
file_counts_df = file_counts_df.sort_values(by="Count", ascending=False)

# print the entire dataframe using python tabulate

print(tabulate(file_counts_df, headers="keys", tablefmt="psql"))
