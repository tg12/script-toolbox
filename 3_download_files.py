import hashlib
import os

import boto3

# Set the name of the S3 bucket
bucket_name = 'my-secure-sql-backup-bucket'

# Set the directory where the BAK files will be saved
directory = '/path/to/bak/files'

# Create an S3 client
s3 = boto3.client('s3')

# Iterate over the objects in the S3 bucket
for obj in s3.list_objects(Bucket=bucket_name)['Contents']:
    # Check if the object is a BAK file
    if obj['Key'].endswith('.bak'):
        # Download the BAK file to the specified directory
        s3.download_file(bucket_name, obj['Key'], os.path.join(directory, obj['Key']))


# Set the directory where the BAK files are saved
directory = '/path/to/bak/files'

# Read the hash text file
with open('/path/to/hash/text/file.txt') as f:
    hashes = f.readlines()

# Create a dictionary to store the original file hashes
original_hashes = {}

# Iterate over the hashes in the file
for h in hashes:
    # Split the hash and filename
    filename, file_hash = h.split(': ')
    
    # Strip the newline character from the hash
    file_hash = file_hash.strip()
    
    # Add the hash to the dictionary
    original_hashes[filename] = file_hash

# Iterate over the files in the directory
for filename in os.listdir(directory):
    # Check if the file is a BAK file
    if filename.endswith('.bak'):
        # Calculate the hash of the downloaded BAK file
        with open(os.path.join(directory, filename), 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Check if the calculated hash matches the original hash
            if file_hash == original_hashes[filename]:
                print(f'{filename} is verified')
            else:
                print(f'{filename} is NOT verified')
