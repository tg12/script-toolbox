import boto3

# Create an S3 client
s3 = boto3.client('s3')

# Create a new bucket
response = s3.create_bucket(
    Bucket='my-secure-sql-backup-bucket'
)

# Set bucket policy to allow only the S3 bucket owner to access the bucket
s3.put_bucket_policy(
    Bucket='my-secure-sql-backup-bucket',
    Policy="""
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowBucketOwner",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::<ACCOUNT-ID>:root"
                },
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::my-secure-sql-backup-bucket/*"
            }
        ]
    }
    """
)
