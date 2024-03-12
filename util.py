import logging
import os
import sys

import openai

def load_prompt_from_file(filename, directory="prompts"):
    """Reads a prompt from a text file in a specified directory and returns it as a string."""
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The prompt file '{filepath}' was not found.")
    
def load_system_prompts():
    try:
        ai_tutor_system_prompt = load_prompt_from_file("ai_tutor_system_prompt.txt")
        student_persona_system_prompt = load_prompt_from_file("student_persona_system_prompt.txt")
        proofreader_system_prompt = load_prompt_from_file("proofreader_system_prompt.txt")
        return ai_tutor_system_prompt, student_persona_system_prompt, proofreader_system_prompt
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
        
def set_openai_credentials():
    openai_org = os.environ.get("OPENAI_ORG")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if not openai_org or not openai_key:
        logging.error("OpenAI organization ID or API key not set in environment variables.")
        sys.exit("Exiting: Missing OpenAI credentials.")
    else:
        openai.organization = openai_org
        openai.api_key = openai_key
        logging.info("OpenAI credentials successfully set.")