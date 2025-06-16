import boto3
import uuid
import json


def start_transcription_job(bucket: str, object_key: str) -> str:
    '''
    Starts a transcription on on the input_s3_uri, which writes the Transcribe output to output_s3_uri.
    The input file must be in mp4 format and in English.
    Returns the job_name as a string, which can be used to poll the job status.
    '''

    # submit job to transcribe --> write the transcript to the source location
    transcribe_client = boto3.client('transcribe')
    folder_key, sep, filename_ext = object_key.rpartition('/')

    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=f"{uuid.uuid4()}",
        Media={'MediaFileUri': f"s3://{bucket}/{object_key}"},
        MediaFormat='mp4',
        LanguageCode='en-US',
        OutputBucketName=bucket,
        OutputKey=f"{folder_key}/transcript.json"
    )

    # return job name from transcribe
    return response['TranscriptionJob']['TranscriptionJobName']


def lambda_handler(event, context):
    '''
    Starts a Transcribe job. The input video must be .mp4.
    The results will be written as a JSON file in the same S3 location as the input file.
    Returns the job name.
    '''

    try:
        # parse s3 bucket and object key for video file
        record = event['Records'][0]
        message_body = json.loads(record['body'])
        bucket = message_body['detail']['bucket']['name']
        object_key = message_body['detail']['object']['key']

        # check if video is mp4   
        junk, sep, ext = object_key.rpartition('.') 
        if ext.lower().strip() != 'mp4':
            return {
                'statusCode': 404,
                'body': 'File is not in mp4 format.'
            }

        # start transcribe job with uuid as job_id
        job_name = start_transcription_job(bucket, object_key)

        # return job name
        return {
                'statusCode': 200,
                'body': json.dumps({'job_name': job_name})
            }

    except Exception as e:
        print(f"\nERROR in lambda_handler: {e}")
        return {
                'statusCode': 500,
                'body': json.dumps({'ERROR': str(e)})
            }
    