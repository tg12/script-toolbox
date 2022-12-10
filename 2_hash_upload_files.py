import hashlib
import os

import boto3

# Set the directory to search for BAK files
directory = '/path/to/bak/files'

# Create a list to store the BAK files and hashes
bak_files = []
file_hashes = []

# Iterate over the files in the directory
for filename in os.listdir(directory):
    # Check if the file is a BAK file
    if filename.endswith('.bak'):
        # Calculate the hash of the BAK file
        with open(os.path.join(directory, filename), 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            bak_files.append(filename)
            file_hashes.append(file_hash)

# Print the list of BAK files and hashes
for bak_file, file_hash in zip(bak_files, file_hashes):
    print(f'{bak_file}: {file_hash}')


# Set the name of the S3 bucket
bucket_name = 'my-secure-sql-backup-bucket'

# Create an S3 client
s3 = boto3.client('s3')

# Iterate over the files in the directory
for filename in os.listdir(directory):
    # Check if the file is a BAK file
    if filename.endswith('.bak'):
        # Upload the BAK file to the S3 bucket
        s3.upload_file(os.path.join(directory, filename), bucket_name, filename)
