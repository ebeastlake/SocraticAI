import openai
import logging

from openai.error import InvalidRequestError
from dotenv import load_dotenv

from util import load_system_prompts, set_openai_credentials

load_dotenv()
set_openai_credentials()
prompts = load_system_prompts()

"""
TODO: 
[] Make sure the implementation of get_proofread aligns with how I envision the proofreader interacting within the dialogue (i.e., add logic regarding when and how proofreading feedback is incorporated into the conversation).
[] The role specified in proofread_template is "user". Is this the most appropriate role for the proofreading feedback?

"""

class StudentPersonaGPT:
    def __init__(self, role, model="gpt-3.5-turbo", app=None, other_role=None):
        self.role = role
        self.model = model
        self.other_role = other_role
        
        if self.role == "ai_tutor":
            self.chat_completion_role = "assistant"
        elif self.role == "student":
            self.chat_completion_role = "user"
        
        self.app = app
        self.logger = app.logger if app else logging.getLogger(__name__)
        self.history = []
        
    def initialize_chat(self, selected_persona="student_distracted"):
        key = selected_persona if self.role == "student" else "ai_tutor"
        info = prompts.get(key)
        
        if info is None:
            raise ValueError(f"No valid info found for key: '{key}'.")
        
        prompt = info['prompt']
        self.history.append({"role": "system", "content": prompt})

    def generate_chat_response(self, additional_messages=None, temperature=None):
        self.logger.debug(f"Generating based on history: {self.history}")
        messages = self.history + (additional_messages if additional_messages else [])

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature else 0.5
            )
            message_content = response.get("choices")[0]["message"]["content"]
        except InvalidRequestError as e:
            if "maximum context length" in str(e):
                message_content = "The context length exceeds my limit... "
            else:
                message_content = f"I encountered an error when using my backend model.\n\nError: {str(e)}"
        self.logger.debug(f"Generated response: {message_content}")
        return message_content

    def get_response(self):
        temperature = 1 if self.role == "student" else 0
        msg = self.generate_chat_response(temperature=temperature)
        self.update_history(msg)
        return msg
    
    def update_history(self, message):
        self.history.append({"role": self.chat_completion_role, "content": message})
        if self.other_role:
            self.other_role.history.append({"role": self.chat_completion_role, "content": message})
