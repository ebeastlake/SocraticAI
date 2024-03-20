import json
import logging
import openai
import os
import sys

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
        directory = "prompts"
        prompts = {}

        with open(os.path.join(directory, "prompt_config.json"), 'r') as config_file:
            config = json.load(config_file)
            for persona, info in config.items():
                prompt_text = load_prompt_from_file(info['prompt_file'], directory)
                prompts[persona] = {
                    "display_name": info['display_name'],
                    "prompt": prompt_text
                }

        print(f"Prompts loaded successfully. Prompts: {list(prompts.keys())}")
        return prompts
    except (FileNotFoundError, json.JSONDecodeError) as e:
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