import boto3
import time


bedrock_client = boto3.client("bedrock-runtime")
default_model = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # claude 3.5 sonnet v2


def invoke_model(messages: list, model_id = "", streaming = False, retries = 0) -> dict:
    '''
    Invokes the model, optionally with streaming. 
    If a throttling exception is encountered, retries with exponential backoff until the max retries (10) is reached.
    Returns the response object.
    '''

    if model_id == "":
        model_id = default_model

    try:
        if streaming:
            response = bedrock_client.converse_stream(
                modelId = model_id,
                messages = messages
            )

        else:
            response = bedrock_client.converse(
                modelId = model_id,
                messages = messages
            )

        return response

    except Exception as e:
        print(f"\nERROR in invoke_model: {e}")

        if ("ThrottlingException" in str(e)):
            retries += 1
            delay = retries * 10
            print(f"Retrying in {delay}s... (retry #{retries})\n")
            time.sleep(delay)
            return invoke_model(messages, model_id, streaming, retries)
        
        raise e
    

def invoke_model_text(prompt: str) -> str:
    '''
    Sends a text-only prompt to the LLM and returns the text-only response as a string.
    '''

    messages = [
        {'role': 'user',
         'content': [{
             'text': prompt,
         }]}
    ]

    response = invoke_model(messages)
    response_text = get_response_text(response)

    return response_text


def get_response_text(raw_response: dict) -> str:
    '''
    Extracts the text response from the raw response. Returns a string.
    '''

    return raw_response['output']['message']['content'][0]['text']


def parse_tags(response_text: str, tag: str) -> str:
    '''
    Extracts the text from between the given tag. 
    Returns a tuple containing (extracted content, remaining text).
    '''

    junk, sep, remaining_text = response_text.partition(f"<{tag}>")
    content, sep, junk = remaining_text.partition(f"</{tag}>")

    return (content.strip(), remaining_text)

