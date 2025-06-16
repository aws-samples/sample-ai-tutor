from aws_cdk import (
    NestedStack,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    RemovalPolicy,
)
from constructs import Construct

vid_lambda_timeout = Duration.minutes(15)

class VideoProcessingStack(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, app_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 bucket for logging
        logs_bucket = s3.Bucket(
            self, f"{app_name}-logs-Bucket", 
            bucket_name=f"{app_name}-logs-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
        )

        # Create an S3 bucket to store uploaded files
        uploads_bucket = s3.Bucket(
            self, f"{app_name}-Uploads-Bucket", 
            bucket_name=f"{app_name}-uploads-{self.account}",
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
            server_access_logs_bucket=logs_bucket,
            server_access_logs_prefix=f"{app_name}-logs",
        )

        # region Transcribe
        # Create an transcription job SQS queue with a dead-letter queue
        transcribe_dlq = sqs.Queue(
            self, f"{app_name}-Transcribe-DLQ",
            queue_name=f"{app_name}-Transcribe-DLQ",
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
        )

        transcribe_queue = sqs.Queue(
            self, f"{app_name}-Transcribe-Queue",
            queue_name=f"{app_name}-Transcribe-Queue",
            visibility_timeout=Duration.seconds(100),
            receive_message_wait_time=Duration.seconds(20),
            removal_policy=RemovalPolicy.DESTROY,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=2,
                queue=transcribe_dlq
            ),
            enforce_ssl=True,
        )

        # Lambda function to start the Transcribe job
        lambda_transcribe_job = lambda_.Function(
            self, f"{app_name}-Transcribe-Lambda",
            function_name=f"{app_name}-Transcribe-Lambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset("lambdas"),
            handler="transcribe_video.lambda_handler",
        )
        lambda_transcribe_job.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=transcribe_queue,
                batch_size=1,
                max_concurrency=2
            )
        )

        # Grant Lambda Transcribe permissions
        lambda_transcribe_job.add_to_role_policy(iam.PolicyStatement(
            actions=['transcribe:StartTranscriptionJob'], resources=['*']))    # wildcard permission is enabled to allow access to uploaded files for which the filenames cannot be predetermined
        uploads_bucket.grant_read_write(lambda_transcribe_job)
        transcribe_queue.grant_consume_messages(lambda_transcribe_job)

        # EventBridge rule to trigger on S3 PutObject events for video files
        transcribe_event_rule = events.Rule(
            self, f"{app_name}-Transcribe-EventRule",
            rule_name=f"{app_name}-transcribe-rule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [uploads_bucket.bucket_name]},
                    "object": {"key": [{"suffix": ".mp4"}]},
                },
            ),
        )
        transcribe_event_rule.add_target(targets.SqsQueue(transcribe_queue))

        # endregion

        # region Process Transcript
        # Create an transcription job SQS queue with a dead-letter queue
        process_transcript_dlq = sqs.Queue(
            self, f"{app_name}-ProcessTranscript-DLQ",
            queue_name=f"{app_name}-ProcessTranscript-DLQ",
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
        )

        process_transcript_queue = sqs.Queue(
            self, f"{app_name}-ProcessTranscript-Queue",
            queue_name=f"{app_name}-ProcessTranscript-Queue",
            visibility_timeout=vid_lambda_timeout,
            receive_message_wait_time=Duration.seconds(20),
            removal_policy=RemovalPolicy.DESTROY,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=2,
                queue=process_transcript_dlq
            ),
            enforce_ssl=True,
        )

        # Lambda function to process and enrich the transcript
        lambda_process_transcript = lambda_.Function(
            self, f"{app_name}-ProcessTranscript-Lambda",
            function_name=f"{app_name}-ProcessTranscript-Lambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset("lambdas"),
            handler="process_transcript.lambda_handler",
            timeout=vid_lambda_timeout,
        )
        lambda_process_transcript.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=process_transcript_queue,
                batch_size=1,
                max_concurrency=2
            )
        )

        # Grant Lambda Transcribe permissions
        lambda_process_transcript.add_to_role_policy(iam.PolicyStatement(
            actions=['bedrock:InvokeModel'], resources=['*']))    # wildcard permission is enabled to allow access to any model that is available within the account
        uploads_bucket.grant_read_write(lambda_process_transcript)
        process_transcript_queue.grant_consume_messages(lambda_process_transcript)

        # EventBridge rule to trigger on S3 PutObject events for transcript files
        process_transcript_event_rule = events.Rule(
            self, f"{app_name}-ProcessTranscript-EventRule",
            rule_name=f"{app_name}-ProcessTranscript-rule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [uploads_bucket.bucket_name]},
                    "object": {"key": [{"suffix": ".json"}]},
                },
            ),
        )
        process_transcript_event_rule.add_target(targets.SqsQueue(process_transcript_queue))

        # outputs
        self.bucket_name = uploads_bucket.bucket_name

        # endregion

