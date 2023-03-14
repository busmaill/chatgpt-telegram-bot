import openai
import spacy
import re
import asyncio
from openai.api_key import Client
from openai.errors import APIError
from spacy.lang.en import English
from kafka import KafkaProducer


class ChatGPT:
    def __init__(self, config):
        self.api_key = config.get('OpenAI', 'api_key')
        self.model_engine = config.get('OpenAI', 'model_engine')
        self.max_tokens = config.getint('OpenAI', 'max_tokens')
        self.nlp = spacy.load('en_core_web_sm')
        self.producer = KafkaProducer(
            bootstrap_servers=config.get('Kafka', 'bootstrap_servers'),
            value_serializer=lambda x: x.encode('utf-8'),
        )
        self.response_topic = config.get('Kafka', 'topic_name')

        self.greetings = [
            "Hello! How can I help you today?",
            "Hi there! What can I do for you?",
            "Hey! How can I assist you?",
            "Hi! What can I help you with?",
            "Hello! What do you want to know?",
            "Greetings! What brings you here?",
        ]
        
        self.client = Client(api_key=self.api_key)

    async def generate_response(self, message):
        # preprocess the message text
        message = re.sub(r'[^\w\s]', '', message.strip().lower())
        
        # use spaCy to extract the subject of the message
        subject = ''
        doc = self.nlp(message)
        for token in doc:
            if token.dep_ == 'nsubj':
                subject = token.text
                break
        
        # generate a response from the OpenAI GPT-3 model
        prompt = f"{subject}: {message}"
        try:
            response = self.client.completions.create(
                engine=self.model_engine,
                prompt=prompt,
                max_tokens=self.max_tokens,
            ).choices[0].text
        except APIError as error:
            print(f"Error: {error}")
            response = "Sorry, I am not able to process your request at the moment."

        # send the response to the Kafka topic
        await self.send_to_kafka(response)

    async def send_to_kafka(self, response):
        # send the response to the Kafka topic
        try:
            self.producer.send(self.response_topic, response)
            self.producer.flush()
        except Exception as e:
            print(f"Error while sending to Kafka: {e}")

