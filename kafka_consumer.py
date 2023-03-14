import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from chatgpt import ChatGPT
from mysql import MySQL


class KafkaConsumer:
    def __init__(self, kafka_config, chatgpt, mysql):
        self.kafka_config = kafka_config
        self.chatgpt = chatgpt
        self.mysql = mysql

    async def start(self):
        consumer = AIOKafkaConsumer(
            self.kafka_config['topic_name'],
            bootstrap_servers=self.kafka_config['bootstrap_servers'],
            group_id='my-group')

        try:
            # Wait for the consumer to subscribe to the topic
            await consumer.start()

            async for msg in consumer:
                # Convert the message value to a string
                message = msg.value.decode('utf-8')

                # Get the user ID and message from the message string
                user_id, user_message = message.split('|')

                # Generate the chatbot response
                chatbot_response = self.chatgpt.generate_response(user_message)

                # Save the user message and chatbot response to the database
                self.mysql.save_message(user_id, user_message, chatbot_response)

        except KafkaError as e:
            print(f'Error while consuming messages: {e}')

        finally:
            # Close the consumer connection
            await consumer.stop()
