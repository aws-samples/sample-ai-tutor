from . import (
    transcribe,
    bedrock
)
from concurrent.futures import ThreadPoolExecutor


def get_summary_and_topics(response: dict) -> str:
    '''
    Writes a summary of the transcript. Returns a string.
    '''

    transcript_text = transcribe.get_transcript_text(response)

    instructions = f"""
    <transcript>
    {transcript_text}
    </transcript>

    You are given a video transcript above in <transcript></transcript> tags. Your task is to identify the key topics in the video and write a summary of the content. 
    
    For each topic in the key topics, output the topics as within <topic></topic> tags. You must list the topics in the order in which they appear and include the intro and outro sections. Then, output the summary within <summary></summary> tags. The summary should be at most 250 words.
    
    Below is an example of the expected output format.  

    <topic>
    First Topic
    </topic>

    <topic>
    Second Topic
    </topic>

    <summary>
    This is a short summary of the transcript.
    </summary>
    """

    try:
        response = bedrock.invoke_model_text(instructions)
        summary = bedrock.parse_tags(response, 'summary')[0]
        topics = parse_topics(response)

        return {
            'summary': summary,
            'topics': topics,
        }
    
    except Exception as e:
        print(f"ERROR in get_summary_and_topics: {e}")
        raise e
    

def parse_topics(response: str) -> list:
    '''
    Parses the topics as a list of strings. The expected input format is a newline-separated numbered list.
    '''

    res = response
    topics = []

    while res != "":
        topic, res = bedrock.parse_tags(res, 'topic')
        if topic != "":
            topics.append(topic)
    
    return topics


def get_chapters(transcribe_response: dict, topics: list) -> list:
    '''
    Extracts the relevant section of the transcript that relates to each topic.
    Returns an ordered list of dictionaries containing
    {
        'id': index, 
        'title': topic, 
        'transcript': section,
        'start_time': int(timestamp),
        'end_time': int(timestamp),
        'segments': list(audio_segments)
    }
    '''

    transcript_text = transcribe.get_transcript_text(transcribe_response)
    
    chapters = []
    fanout = 10

    with ThreadPoolExecutor(max_workers=fanout) as pool:
        for i in range(len(topics)):
            t = topics[i]
            pool.submit(mult_split_transcript_by_topic, transcript_text, t, i, chapters)

    chapters = sorted(chapters, key=lambda x: x["id"])
    chapters = get_chapter_timestamps(transcribe_response, chapters)

    return chapters


def mult_split_transcript_by_topic(transcript_text: str, topic: str, index: int, buffer: list) -> None:
    '''
    Extracts a continous section of the transcript that is related to the topic.
    Appends the results to the buffer as a dictionary containing
    {
        'id': index, 
        'title': topic, 
        'transcript': section
    }
    '''

    instructions = f"""
    <transcript>
    {transcript_text}
    </transcript>

    You are give a video transcript and a topic. Your task is to analyze the transcript in <transcript></transcript> and find the section that is most relevant to the topic "{topic}". The section should be a continuous block from the transcript.

    You are strictly required to use the original wording verbatim. Output the section within <section></section> tags.
    """

    response = bedrock.invoke_model_text(instructions)
    section = bedrock.parse_tags(response, 'section')[0]

    buffer.append({
        'id': index, 
        'title': topic, 
        'transcript': section
        })


def get_chapter_timestamps(transcribe_response: dict, chapters: list) -> list:
    '''
    Finds the start and stop timestamp for each chapter. The chapters parameter should be a list of dictionaries containing (id, title, transcript) keys.
    '''

    audio_segments = transcribe.get_audio_segments(transcribe_response)
    fanout = 10
    threshold = .8

    for c in chapters:
        transcript = c['transcript']
        chapter_segments = []

        while len(audio_segments) > 0:
            batch_segments = []

            # pop a batch of segments to process
            with ThreadPoolExecutor(max_workers=fanout) as pool:
                for i in range(fanout):
                    if len(audio_segments) <= 0:
                        break

                    segment = audio_segments.pop(0)
                    pool.submit(mult_is_in_chapter, transcript, segment, i, batch_segments)

            # isolate consecutive False segments at the end of the batch
            batch_segments.sort(reverse=True)
            last_true = 0

            for i, s, b in batch_segments:
                if b is True:
                    last_true = i
                    break

            # get ordered list of segments in and not in chapter
            batch_segments.sort()
            in_chapter = batch_segments[:last_true + 1]
            not_in_chapter = batch_segments[last_true + 1:]

            # print(f"\nDEBUG in_chapter segments:")
            # debug = '\n\n- '.join([s['transcript'] for i, s, b in in_chapter])
            # print(f"- {debug}")

            # save in-chapter segments and put back not-in-chapter segments
            chapter_segments += [s for i, s, b in in_chapter]
            audio_segments = [s for i, s, b in not_in_chapter] + audio_segments

            # break if percentage True is below threshold
            if len(in_chapter) / len(batch_segments) < threshold:
                break

        # if last chapter AND audio_segments is not empty, append to last chapter
        if c['id'] == chapters[-1]['id'] and len(audio_segments) > 0:
            chapter_segments += audio_segments
                            
        # find chapter start and stop timestamps
        timestamps = [s['start_time'] for s in chapter_segments] + [s['end_time'] for s in chapter_segments]
        min_timestamp = min(timestamps)
        max_timestamp = max(timestamps)
        c['start_time'] = min_timestamp
        c['end_time'] = max_timestamp
        c['segments'] = chapter_segments.copy()

    return chapters


def mult_is_in_chapter(chapter_transcript: str, segment: dict, index: int, buffer: list) -> None:
    '''
    Checks if the segment is present in the chapter transcript.
    Writes a tuple to the buffer containing (index, segment, is_present_bool).
    '''

    segment_text = segment['transcript']

    instructions = f"""
    <transcript>
    {chapter_transcript}
    </transcript>

    You are a given a full video transcript and a segment of text. Your task is to determine if the text segment is part of the video transcript or not. Minor variations are acceptable.

    Determime if the video transcript given above in <transcript></transcript> tags contains the following text segment: {segment_text}

    Output exactly one word, "yes" or "no" within <ans></ans> tags.
    """
    
    response = bedrock.invoke_model_text(instructions)
    ans = bedrock.parse_tags(response, 'ans')[0]
    is_present = True if "yes" in ans.lower() else False

    buffer.append((index, segment, is_present))
