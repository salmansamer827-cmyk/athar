import requests

TOKEN = 'YOUR_BOT_TOKEN'
channel_username = '@EXCGlobl'
url = f'https://api.telegram.org/bot{TOKEN}/getChat?chat_id={channel_username}'

response = requests.get(url)
print(response.json())
