import sys
import os
import re
import time
import openai
import logging

from openai.error import InvalidRequestError
from dotenv import load_dotenv

from util import load_system_prompts, set_openai_credentials

load_dotenv()
set_openai_credentials()
# TODO: Refactor to use nested system prompt objects
ai_tutor_system_prompt, student_persona_system_prompt, proofreader_system_prompt = load_system_prompts()

"""
TODO: 
[] Make sure the implementation of get_proofread aligns with how I envision the proofreader interacting within the dialogue (i.e., add logic regarding when and how proofreading feedback is incorporated into the conversation).
[] The role specified in proofread_template is "user". Is this the most appropriate role for the proofreading feedback?

"""

class StudentPersonaGPT:
    def __init__(self, role, n_round, model="gpt-3.5-turbo"):
        self.role = role
        self.model = model
        self.n_round = n_round
        
        if self.role == "ai_tutor":
            self.other_role = "student"
        elif self.role == "student":
            self.other_role = "ai_tutor"
        
        self.history = []
        
    def initialize_chat(self, student_persona="default"):
        system_content = ""
        if self.role == "ai_tutor":
            # system_content = system_prompts["ai_tutor"]
            # self.history.append({
            #     "role": "system",
            #     "content": system_content
            # })
            self.history.append({
                "role": "system",
                "content": ai_tutor_system_prompt
            })
        elif self.role == "student":
            # persona_prompt = system_prompts["student"].get(student_persona, system_prompts["student"]["default"])
            # system_content = persona_prompt
            # self.history.append({
            #     "role": "system",
            #     "content": system_content
            # })
            self.history.append({
                "role": "system",
                "content": student_persona_system_prompt
            })
        # TODO: Add logic for proofreader
        # elif self.role == "proofreader":
        #     system_content = system_prompts["proofreader"]
        #     self.history.append({
        #         "role": "system",
        #         "content": system_content
        #     })

        # TODO: Determine if the initial message for ai_tutor should be set here        
        # if self.role == "ai_tutor":
        #     return system_content
        
    
    def generate_chat_response(self, additional_messages=None, temperature=None):
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
        return message_content

    def get_response(self, temperature=None):
        logging.info(f"getting response from AliceBobCindy, self.role: {self.role}")
        msg = self.generate_chat_response(temperature=temperature)
        self.history.append({"role": "assistant", "content": msg})
        return msg
    
    def get_proofread(self, temperature=None):
        proofread_template = {"role": "user", "content": proofreader_system_prompt}
        msg = self.generate_chat_response(additional_messages=[proofread_template], temperature=temperature)
        if msg[:2] not in ["NO", "No", "no"]:
            self.history.append({"role": "assistant", "content": msg})
        return msg

    def update_history(self, message):
        self.history.append({
            "role": "user",
            "content": message
        })

    def add_proofread(self, proofread):
        self.history.append({
            "role": "system",
            "content": f"Message from a proofreader Plato to you two: {proofread}"
        })