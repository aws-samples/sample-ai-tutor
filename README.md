# Overview
This project creates an AI Tutor that allows users upload a video, which is then divided into bite-sized chapters. For each chapter, a knowledge check quiz is created following Bloom's taxonomy. 

The backend system uses an event-driven architecture, which is triggered automatically when the user uploads a video to Amazon S3. In essence, Amazon EventBridge triggers Amazon Lambda to process the uploaded video file, which in turn invokes Amazon Transcribe (to transcribe the video) and Amazon Bedrock (to process the transcript, derive chapters, and enrich it with new content such as chapter summaries and quizzes). 

The features in this project such as deriving chapters, summaries, and quizzes are just a few examples of how generative AI can be used in context of an AI Tutor. Other features can be readily developed on top of this foundational project by leveraging the same event-driven architecture to trigger new generative AI workflows.


# Setup guide
1. Before deploying the solution to your AWS account, please ensure the following prerequisites are met:
    - You have appropriate permissions in your AWS account to deploy a CDK application
    - Enable model access in Amazon Bedrock
2. Install the requirements using `pip install -r requirements.txt`
3. Deploy the solution using AWS CDK: `cdk deploy`. The bucket name will be outputted to the console. You can also retrieve the bucket name from CloudFormation outputs.
4. Optionally, a development UI is provided for testing. The UI runs locally to enable users to upload a video file to Amazon S3 and then retrieve and display the results once the processing is complete. To deploy the UI, follow these steps:
    - Install the development requirements using `pip install -r requirements-dev.txt`
    - Update the bucket name in `ui.py` to the bucket that was deployed in Step 2.
    - Run `streamlit run ui.py`


# Best practices recommendations
This project provides a sample technical deployment that follows AWS best practices. In addition to these technical considerations, here are a few people-related best practices that you should also consider in a production environment:
- An owner should periodically check and update each Lambda runtime. Take note of long term support (LTS) versions, patches, and minor releases.
- Assign an owner to monitor and set alarms on AWS Lambda function metrics in Amazon CloudWatch.
- Periodically scan and update all dependencies in AWS Lambda Layers according to lifecycle policies.
- Periodically scan all AWS Lambda container images for vulnerabilities according to lifecycle policies.
- Specify an owner to monitor dead-letter queues. Alert on failures and/or redrive queues automatically when failures occur.
- [Monitor model invocation using CloudWatch Logs and Amazon S3](https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html)
- [Detect and filter harmful content by using Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)


## Contributing
See [CONTRIBUTING](CONTRIBUTING.md) for more information.


## Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


## License
This project is licensed under the MIT-0 License.