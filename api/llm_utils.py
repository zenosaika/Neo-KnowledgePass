import os
from dotenv import load_dotenv
import json
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# --- Configuration ---

MODEL = "gemini-2.0-flash"

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def llm_generate(chats, config):
    contents = [
        types.Content(
            role="user",
            parts=chats,
        ),
    ]

    responses = [chunk.text for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=contents,
        config=config,
    )]

    return json.loads(''.join(responses))


def extract_skill(input_data, input_type):
    chats = [
        types.Part.from_text(
            text=f"Extract important technical & topic-learning keyword (english only) from this {input_type}\n"
        ),
    ]

    if input_type == 'text':
        chats.append(
            types.Part.from_text(
                text=input_data
            )
        )
    elif input_type in ['image', 'file']:
        files = [client.files.upload(file=input_data)]

        chats.append(
            types.Part.from_uri(
                file_uri=files[0].uri,
                mime_type=files[0].mime_type,
            )
        )

    config = types.GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.OBJECT,
            properties={
                "skills": genai.types.Schema(
                    type=genai.types.Type.ARRAY,
                    items=genai.types.Schema(
                        type=genai.types.Type.STRING,
                    ),
                ),
            },
        ),
    )

    json_obj = llm_generate(chats, config)

    skill_list = json_obj['skills']

    return skill_list


def extract_taxonomy(word_list):
    chats = [
        types.Part.from_text(
            text=f"Generate a detailed taxonomy for the skill keyword {word_list}. Focus on identifying specific, meaningful relationships, and avoid overly general categories like 'technique' unless absolutely necessary."
        ),
    ]

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["ordered_result"],
            properties = {
                "ordered_result": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["is_a", "synonyms", "name", "associate_to", "use_knowledge_of"],
                        properties = {
                            "is_a": genai.types.Schema(
                                type = genai.types.Type.ARRAY,
                                items = genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                ),
                            ),
                            "synonyms": genai.types.Schema(
                                type = genai.types.Type.ARRAY,
                                items = genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                ),
                            ),
                            "name": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "associate_to": genai.types.Schema(
                                type = genai.types.Type.ARRAY,
                                items = genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                ),
                            ),
                            "use_knowledge_of": genai.types.Schema(
                                type = genai.types.Type.ARRAY,
                                items = genai.types.Schema(
                                    type = genai.types.Type.STRING,
                                ),
                            ),
                        },
                    ),
                ),
            },
        ),
    )

    json_obj = llm_generate(chats, config)

    taxonomy_dict = {
        o['name']: {
            'is_a': o['is_a'],
            'associate_to': o['associate_to'],
            'use_knowledge_of': o['use_knowledge_of'],
            'synonyms': o['synonyms'], 
        } for o in json_obj['ordered_result']
    }

    return taxonomy_dict