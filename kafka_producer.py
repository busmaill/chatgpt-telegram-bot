import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError


class KafkaProducer:
    def __init__(self, kafka_config):
        self.kafka_config = kafka_config

    async def start(self):
        producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_config['bootstrap_servers'])

        try:
            # Wait for the producer to connect to the broker
            await producer.start()

            while True:
                # Wait for the user to input a message
                message = input('Enter your message: ')

                # Send the message to the Kafka topic
                await producer.send(self.kafka_config['topic_name'], message.encode('utf-8'))

        except KafkaError as e:
            print(f'Error while producing message: {e}')

        finally:
            # Wait for all outstanding messages to be delivered and delivery reports
            await producer.flush()

            # Close the producer connection
            await producer.stop()
