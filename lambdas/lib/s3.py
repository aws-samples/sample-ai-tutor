import boto3
import os
from . import (
    utils
)

def upload_file(file_path: str, bucket_name: str, object_prefix: str) -> str:
    """
    Uploads a local file to an Amazon S3 bucket with a specified prefix.
    Returns the object key of the uploaded file in S3 as a string.
    """
    s3_client = boto3.client('s3')

    try:
        # Get the file name from the file path
        junk, sep, file_name = file_path.rpartition('/')

        # Construct the object key by combining the prefix and file name
        object_prefix = object_prefix[:-1] if object_prefix[-1] == '/' else object_prefix
        object_key = f"{object_prefix}/{file_name}"

        # Upload the file to S3
        s3_client.upload_file(file_path, bucket_name, object_key)

        print(f"File '{file_name}' uploaded successfully to '{bucket_name}/{object_key}'")
        return object_key

    except Exception as e:
        print(f"\nERROR in upload_file_to_s3: {e}")
        raise e
    

def download_file(bucket_name: str, key, local_path: str) -> str:
    """
    Downloads a file from an Amazon S3 bucket to a local path.
    The local path should include a trailing '/'. For example, 'temp/'.
    Returns the filepath to the local file.
    """
    
    try:
        # Create an S3 client
        s3 = boto3.client('s3')

        # Parse the filename and create local directory if not exists
        junk, sep, filename_ext = key.rpartition('/')
        output_filepath = f"{local_path}{filename_ext}"
        utils.create_directory(local_path)

        # Download the file
        s3.download_file(Bucket=bucket_name, Key=key, Filename=output_filepath)

        return output_filepath
    
    except Exception as e:
        print(f"\nERROR in download_file_from_s3: {e}")
        raise e
    

def list_bucket(bucket_name: str) -> list:
    '''
    Retrieves a list of object keys from the given bucket.
    Returns a list of strings.
    '''

    s3 = boto3.client('s3')
    objects = []

    response = s3.list_objects_v2(Bucket=bucket_name)

    if 'Contents' in response:
        for obj in response['Contents']:            
            objects.append(obj['Key'])

        while response['IsTruncated']:
            response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=response['NextContinuationToken'])
            for obj in response['Contents']:                
                objects.append(obj['Key'])

    return objects
