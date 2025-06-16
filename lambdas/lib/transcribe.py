import boto3


transcribe_client = boto3.client('transcribe')

def start_transcription_job(bucket: str, object_key: str) -> str:
    '''
    Starts a transcription on on the input_s3_uri, which writes the Transcribe output to output_s3_uri.
    The input file must be in mp4 format and in English.
    Returns the job_name as a string, which can be used to poll the job status.
    '''

    # expected format --> bucket/job_id/filename.ext
    paths = object_key.split('/')
    job_id = paths[0]
    filename_ext = paths[1]
    filename, sep, ext = filename_ext.rpartition('.')

    # submit job to transcribe
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=f"{job_id}",
        Media={'MediaFileUri': f"s3://{bucket}/{object_key}"},
        MediaFormat='mp4',
        LanguageCode='en-US',
        OutputBucketName=bucket,
        OutputKey=f"{job_id}/{filename}_transcript.json"
    )

    # return job name from transcribe
    return response['TranscriptionJob']['TranscriptionJobName']


def get_transcript_s3_uri(job_name: str) -> dict:
    '''
    Gets the transcription job for job_name.
    Returns a dictionary.
    '''

    try:
        response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        return response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    
    except Exception as e:
        print(f"ERROR in get_transcript_s3_uri: {e}")
        raise e


def get_job_status(job_name: str) -> str:
    '''
    Checks the job status for job_name.
    Returns a string.
    '''

    try:
        response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        status = response['TranscriptionJob']['TranscriptionJobStatus']
        return status
    
    except Exception as e:
        print(f"ERROR in get_job_status: {e}")
        raise e


def retrieve_transcript_json(output_s3_uri, job_name):
    '''
    Retrieves the JSON transcript from the output_s3_uri and job_name.
    '''

    s3_client = boto3.client('s3')
    bucket_name = output_s3_uri.split('/')[2]
    key = f"{'/'.join(output_s3_uri.split('/')[3:])}/{job_name}.json"
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read().decode('utf-8')


def get_transcript_text(raw_response: dict) -> str:
    '''
    Extracts the transcript text from the raw response.      
    Returns the transcript as a continuous block of text in a string.
    '''

    return raw_response['results']['transcripts'][0]['transcript']


def get_audio_segments(raw_response: dict) -> list:
    '''
    Extracts the audio segments from the raw response.      
    Returns a list of dictionaries containing the keys "id", "start_time", "end_time", and "transcript".
    '''

    audio_segments = [{
        'id': s['id'],
        'start_time': get_seconds(s['start_time']),
        'end_time': get_seconds(s['end_time']),
        'transcript': s['transcript'],
        } 
        for s in raw_response['results']['audio_segments']]
    
    audio_segments = sorted(audio_segments, key=lambda x: x['start_time'])

    return audio_segments


def get_seconds(timestamp: str) -> int:
    '''
    Extracts the seconds value from Transcribe's timestamp string.
    Returns an int.
    '''

    s, sep, junk = timestamp.rpartition('.')
    return int(s)
