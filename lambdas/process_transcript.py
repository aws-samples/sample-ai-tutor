from lib import (
    s3,
    vid_proc,
    enrich_content,
    utils
)
import json
import os
import uuid


def lambda_handler(event, context):
    '''
    Processes the video transcript to extract chapters and enrich with generated content such as quizzes.
    Writes the results as chapters.json back to the same S3 prefix.
    Returns the S3 URI to the chapters.json file.
    '''

    try:
        # parse s3 bucket and object key for video file
        record = event['Records'][0]
        message_body = json.loads(record['body'])
        bucket = message_body['detail']['bucket']['name']
        object_key = message_body['detail']['object']['key']

        # check the filename
        if object_key.lower()[-len('transcript.json'):] != 'transcript.json':
            print(f"File is not transcript.json")
            return {
                'statusCode': 404,
                'body': 'File is not transcript.json'
            }
        
        # create a temporary subfolder with a unique ID within Lambda's tmp folder
        temp_folder = f"/tmp/{uuid.uuid4()}/"

        # get transcript json from s3
        transcript_filepath = s3.download_file(bucket, object_key, temp_folder)

        # validate transcript filepath, then load as a dictionary and delete local json
        if temp_folder in transcript_filepath:
            with open(transcript_filepath, 'r', encoding="utf-8") as file:
                transcript = json.load(file)
            utils.delete_file(transcript_filepath)            
        else:
            raise ValueError()

        # get summary, topics, and chapters
        print(f"\nGetting summary and key topics")
        summary_topics = vid_proc.get_summary_and_topics(transcript)
        topics = summary_topics['topics']
        chapters = vid_proc.get_chapters(transcript, topics)

        # enrich chapters with generated content
        print(f"\nEnriching chapters with generated content, e.g. quizzes, summaries, etc")
        chapters = enrich_content.get_chapter_mcq(chapters)
        chapters = enrich_content.get_chapter_summaries(chapters)

        # write summary and topics to s3 as overview.json
        overview_filepath = f"{temp_folder}overview.json"
        with open(overview_filepath, "w", encoding="utf-8") as f:
            json.dump(summary_topics, f)
        folder_key, sep, filename_ext = object_key.rpartition('/')
        s3_key = s3.upload_file(overview_filepath, bucket, f"{folder_key}")

        # write chapters and enriched content (e.g. quizzes) to s3 as chapters.json
        chapters_filepath = f"{temp_folder}chapters.json"
        with open(chapters_filepath, "w", encoding="utf-8") as f:
            json.dump(chapters, f)
        folder_key, sep, filename_ext = object_key.rpartition('/')
        s3_key = s3.upload_file(chapters_filepath, bucket, f"{folder_key}")

        # delete temp files
        utils.delete_file(overview_filepath)
        utils.delete_file(chapters_filepath)

        print(f"\nTranscript processing complete. Results written to s3://{bucket}/{s3_key}")
        return {
                'statusCode': 200,
                'body': json.dumps({'s3_uri': f"s3://{bucket}/{s3_key}"})
            }

    except Exception as e:
        print(f"\nERROR in lambda_handler: {e}")
        return {
                'statusCode': 500,
                'body': json.dumps({'ERROR': str(e)})
            }
    