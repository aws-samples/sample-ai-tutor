#!/usr/bin/env python3
from aws_cdk import (
    Stack,
    CfnOutput,
    Aspects
)
import aws_cdk as cdk
from constructs import Construct
from cdk_stacks.video_processing_stack import VideoProcessingStack
import os
import cdk_nag

app_name = 'ai-tutor'

class GenAiBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        video_backend = VideoProcessingStack(self, f"{app_name}-VideoProcessingStack", app_name)

        CfnOutput(
            self, f"{app_name}-BucketName",
            value=video_backend.bucket_name
        )

        # Aspects.of(self).add(cdk_nag.AwsSolutionsChecks())

app = cdk.App()
GenAiBackendStack(app, f"{app_name}-GenAiBackendStack")
app.synth()
