import json
import os

import openai
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set your OpenAI API key in an environment variable named 'OPENAI_API_KEY'
openai.api_key = os.getenv('OPENAI_API_KEY')


class OpenAIBot:
    """
    A chatbot class that interfaces with OpenAI's GPT model to conduct conversations.
    """

    def __init__(self, initial_prompt, model="gpt-4-0125-preview"):
        self.model = model
        self.initial_prompt = initial_prompt
        self.history = []

    def add_to_history(self, role, content):
        self.history.append({'role': role, 'content': content})
        file_path = "./history.json"
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(self.history, file, ensure_ascii=False, indent=4)

    @staticmethod
    def ensure_dict(answer):
        # If answer is already a dict, return it directly.
        if answer[0] == "`":
            answer = answer.strip().removeprefix("```json\n").removesuffix("\n```")
        # If answer is a string, try parsing it as JSON.
        try:
            return json.loads(answer)
        except ValueError as e:
            # Handle the case where parsing fails.
            print(f"Failed to parse 'answer' as JSON: {e}")
            # Return a default structure or raise an error as appropriate.
            return {"error": "Failed to parse response"}

    def ask(self, question):
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.initial_prompt},
                    {"role": "user", "content": question},
                ]
            )
            answer = response.choices[0].message.content
            self.add_to_history('user', question)
            self.add_to_history('bot', answer)
            print(type(answer))
            print(answer)
            answer_dict = self.ensure_dict(answer)
            return answer_dict
        except Exception as e:
            print(f"An error occurred: {e}")
            json_string = '{"message": "I am sorry, I couldn\'t process that request."}'
            return json.loads(json_string)



