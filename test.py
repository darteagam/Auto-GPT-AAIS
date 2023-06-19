import requests
import json

print('test')
url = "http://localhost:8000/aaia_message/"
data = [{"user_id": "DMAM1", "text": "q", "language": "EN", "start_key": True},
        {"user_id": "DMAM1", "text": "Play a video about Peru vs Korea", "language": "EN", "start_key": False},
        {"user_id": "BEGCV2", "text": "q", "language": "EN", "start_key": True},
        {"user_id": "BEGCV2", "text": "Play a video of Shakira", "language": "EN", "start_key": False},
        {"user_id": "DMAM1", "text": "Thank you", "language": "EN", "start_key": False}]
headers = {'Content-type': 'application/json'}

for d in data:
    response = requests.post(url, data=json.dumps(d), headers=headers)
    print(response.json())
    text = input('Press "y" to continue')
    if text == 'y':
        continue