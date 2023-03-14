import configparser
import asyncio
import telethon
from telethon import TelegramClient, events
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import mysql.connector
from mysql.connector import Error
from chatgpt import ChatGPT


class TelegramBot:
    def __init__(self, config):
        self.api_id = config.getint('Telegram', 'api_id')
        self.api_hash = config.get('Telegram', 'api_hash')
        self.bot_token = config.get('Telegram', 'bot_token')
        self.chatgpt = ChatGPT(config)

        # Initialize the Telegram client
        self.client = TelegramClient('chatgpt_bot', self.api_id, self.api_hash)
        self.client.start(bot_token=self.bot_token)

        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            config.get('Kafka', 'topic_name'),
            bootstrap_servers=config.get('Kafka', 'bootstrap_servers'),
            auto_offset_reset='latest',
            value_deserializer=lambda x: x.decode('utf-8'),
            consumer_timeout_ms=1000,
        )

        # Initialize MySQL connection
        try:
            self.mysql_conn = mysql.connector.connect(
                host=config.get('MySQL', 'host'),
                user=config.get('MySQL', 'user'),
                password=config.get('MySQL', 'password'),
                database=config.get('MySQL', 'database')
            )
            if self.mysql_conn.is_connected():
                print('Connected to MySQL database')
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            self.mysql_conn = None

    async def handle_message(self, event):
        # get the message text
        message_text = event.message.message

        # store the message in MySQL
        if self.mysql_conn is not None:
            cursor = self.mysql_conn.cursor()
            query = "INSERT INTO messages (chat_id, message) VALUES (%s, %s)"
            val = (event.chat_id, message_text)
            cursor.execute(query, val)
            self.mysql_conn.commit()
            cursor.close()

        # generate a response from ChatGPT
        await self.chatgpt.generate_response(message_text)

    async def run(self):
        # start the Kafka consumer and handle incoming messages
        self.consumer.subscribe([self.chatgpt.response_topic])
        while True:
            for message in self.consumer:
                try:
                    # send the response back to the user
                    await self.client.send_message('me', message.value)
                except telethon.errors.rpcerrorlist.FloodWaitError as e:
                    # wait for the flood wait time and try again
                    print(f"Encountered FloodWaitError: {e}")
                    await asyncio.sleep(e.seconds)
                except telethon.errors.rpcerrorlist.ChatAdminRequiredError as e:
                    print(f"Encountered ChatAdminRequiredError: {e}")
                except telethon.errors.rpcerrorlist.BotMethodInvalidError as e:
                    print(f"Encountered BotMethodInvalidError: {e}")
                except KafkaError as e:
                    print(f"Error while consuming from Kafka: {e}")
                except Exception as e:
                    print(f"Unknown error: {e}")
                    
    def start(self):
        # add an event handler for incoming messages
        self.client.add_event_handler(
            lambda event: asyncio.ensure_future(self.handle_message(event)),
            events.NewMessage(incoming=True, from_users='me'),
        )

        # start the event loop
        with self.client:
            self.client.loop.run_until_complete(self.run())
