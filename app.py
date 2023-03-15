import asyncio
import configparser
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
import openai
from response_handler import ResponseHandler
from mysql_handler import MySQLHandler

config = configparser.ConfigParser()
config.read('config.ini')

# Telegram API credentials
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
bot_token = config['Telegram']['bot_token']
session_file = config['Telegram']['session_file']

# OpenAI API key
openai.api_key = config['OpenAI']['api_key']

# MySQL database handler
mysql_handler = MySQLHandler()

# Telegram client
client = TelegramClient(StringSession(session_file), api_id, api_hash)

# Response handler
response_handler = ResponseHandler()

# Connect to Telegram
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply('Hello! I am ChatGPT bot. How may I assist you?')

# Handle messages
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = event.from_id
    user_message = event.message.message

    # Save user request to MySQL database
    mysql_handler.save_request(user_id, user_message)

    # Get response from ChatGPT
    response = await response_handler.get_response(user_message)

    # Split response if it exceeds character limit
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await event.reply(response[i:i+4000])
            await asyncio.sleep(1)
    else:
        await event.reply(response)

# Get all user requests from MySQL database
@client.on(events.NewMessage(pattern='/get_requests'))
async def get_requests(event):
    requests = mysql_handler.get_requests()
    message = 'User requests:\n\n'
    for request in requests:
        message += f'User ID: {request[1]}\nUser Message: {request[2]}\n\n'
    await event.reply(message)

# Start the bot
async def main():
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()

asyncio.run(main())
