import configparser
import asyncio
from telegram_bot import TelegramBot
from kafka_producer import KafkaProducer
from kafka_consumer import KafkaConsumer
from mysql import MySQL
from chatgpt import ChatGPT

# Load the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Initialize the MySQL database connection
mysql = MySQL(config['MySQL'])
mysql.connect()

# Initialize the ChatGPT model
chatgpt = ChatGPT()

# Initialize the Kafka Producer and Consumer
kafka_producer = KafkaProducer(config['Kafka'])
kafka_consumer = KafkaConsumer(config['Kafka'], chatgpt, mysql)

# Initialize the Telegram Bot
telegram_bot = TelegramBot(config['Telegram'], kafka_producer, mysql)


async def main():
    # Start the Kafka Consumer
    consumer_task = asyncio.create_task(kafka_consumer.start())

    # Start the Telegram Bot
    await telegram_bot.start()

    # Wait for the Kafka Consumer to finish
    await consumer_task

    # Close the MySQL connection
    mysql.close()


if __name__ == '__main__':
    asyncio.run(main())
