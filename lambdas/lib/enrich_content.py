# from lib import (
from . import (
    bedrock
)
from concurrent.futures import ThreadPoolExecutor


def mult_get_mcq(chapter: dict) -> None:
    '''
    Generates multiple choice quiz questions for the given chapter. The chapter dictionary should contain
    {
        'id': index, 
        'title': topic, 
        'transcript': section,
        'start_time': int(timestamp),
        'end_time': int(timestamp),
        'segments': list(audio_segments)
    }
    Updates the chapter dictionary in-place to add a "quiz" key with a list of questions.
    Each question is a dictionary containing {question_text: str, options: list, correct_ans: int}.
    '''

    chapter_text = f"Title: {chapter['title']}\n\n{chapter['transcript']}"

    instructions = f"""
    <chap>
    {chapter_text}
    </chap>

    Bloom's Taxonomy is a framework used in education to classify different levels of cognitive skills and learning objectives. The taxonomy is hierarchical and consists of six levels, arranged from the simplest to the most complex cognitive skills:
    1) Remember (Knowledge): Recalling facts, terms, concepts, principles, or theories.
    2) Understand (Comprehension): Demonstrating an understanding of the meaning of instructional materials.
    3) Apply: Using learned materials in new and concrete situations.
    4) Analyze: Breaking down information into its components to understand its organizational structure.
    5) Evaluate: Making judgments or decisions based on criteria and standards.
    6) Create (Synthesis): Putting elements together to form a coherent or functional whole; reorganizing elements into a new pattern or structure.

    Your task is to generate one multiple choice quiz question for each level in Bloom's Taxonomy based on the content in <chap></chap>. The goal is to test a student's understanding of the topic.

    Output each quiz question within <quiz></quiz> tags. Each question should contain the level description within <lvl></lvl> tags, the question text within <qn></qn> tags, a list of exactly four choices within <choices></choices> tags where each choice is encapsulated within <opt></opt> tags, and the correct answer within <ans></ans> tags.

    Here is an example of the expected output format:
    <quiz>
        <lvl>
        Remember (Knowledge)
        </lvl>

        <qn>
        The question text.
        </qn>

        <choices>
            <opt>
            Answer choice one
            </opt>
            
            <opt>
            Answer choice two
            </opt>
            
            <opt>
            Answer choice three
            </opt>
            
            <opt>
            Answer choice four
            </opt>
        </choices>

        <ans>
        Answer choice three
        </ans>
    </quiz>
    """

    # get llm response and parse quiz questions
    res = bedrock.invoke_model_text(instructions)

    quiz_qns = []

    while len(res) > 0:
        quiz_content, res = bedrock.parse_tags(res, 'quiz')
        lvl, quiz_content = bedrock.parse_tags(quiz_content, 'lvl')
        qn, quiz_content = bedrock.parse_tags(quiz_content, 'qn')
        choices, quiz_content = bedrock.parse_tags(quiz_content, 'choices')
        ans, quiz_content = bedrock.parse_tags(quiz_content, 'ans')

        options = []
        while len(choices) > 0:
            option, choices = bedrock.parse_tags(choices, 'opt')
            if option.strip() != "":
                options.append(option.strip())

        if lvl.strip() != "" and qn.strip() != "" and len(options) > 0 and ans.strip() != "":
            quiz_qns.append({
                'level': lvl.strip(),
                'question': qn.strip(),
                'choices': options,
                'answer': ans.strip()
            })

    chapter['quiz'] = quiz_qns


def get_chapter_mcq(chapters: dict) -> None:
    '''
    Generates multiple choice questions and answers for each chapter using Bloom's Taxonomy.
    Updates the input dictionary in-place to add a "quiz" key to each chapter. The "quiz" value is a list of dictionaries containing the 'level', 'question', 'choices', and 'answer' keys.
    '''

    print(f"\nGenerating chapter multiple choice questions")

    fanout = 10

    with ThreadPoolExecutor(max_workers=fanout) as pool:
        for c in chapters:
            pool.submit(mult_get_mcq, c)

    print(f"Successfully generated chapter multiple choice questions")
    return chapters


def mult_get_chapter_summary(chapter: dict) -> None:
    '''
    Generates a summary of the chapter and appends add a "summary" key to the chapters dictionary in-place.
    '''

    chapter_text = f"Title: {chapter['title']}\n\n{chapter['transcript']}"

    instructions = f"""
    <chap>
    {chapter_text}
    </chap>
    
    Summarize the text given in <chap></chap> tags using less than 200 words. Output your summary within <summary></summary> tags.
    """

    try:
        response = bedrock.invoke_model_text(instructions)
        summary = bedrock.parse_tags(response, 'summary')[0]
        chapter['summary'] = summary

    except Exception as e:
        print(f"\nERROR in mult_get_chapter_summary: {e}")


def get_chapter_summaries(chapters: dict) -> None:
    '''
    Generates a summary for each chapter.
    A "summary" key is added to the each chapter in-place.
    '''

    print(f"\nGenerating chapter summaries")

    fanout = 10

    with ThreadPoolExecutor(max_workers=fanout) as pool:
        for c in chapters:
            pool.submit(mult_get_chapter_summary, c)

    print(f"Successfully generated chapter summaries")
    return chapters

