import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

with open('command.json', 'r') as f:
  commands = json.load(f)

APP_ID = os.environ['APP_ID']
SERVER_ID = os.environ['SERVER_ID']
BOT_TOKEN = os.environ['BOT_TOKEN']

url = f'https://discord.com/api/v10/applications/{APP_ID}/guilds/{SERVER_ID}/commands'

print(url)
print(commands)
print()

response = requests.put(url, headers={
  'Authorization': f'Bot {BOT_TOKEN}'
}, json=commands)

print(response.json())
