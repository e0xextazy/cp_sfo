import requests
import json
import ast


# r1 = requests.get("http://0.0.0.0:5000/")
r1 = requests.get("https://24eb-62-217-190-168.ngrok.io/")
print(r1.text)

# r2 = requests.post("http://0.0.0.0:5000/get_answer",
#                    data=json.dumps({"query": "Какой размер пособия по временной нетрудоспособности?"}))
r2 = requests.post("https://24eb-62-217-190-168.ngrok.io/get_answer",
                   data=json.dumps({"query": "Какой размер пособия по временной нетрудоспособности?"}))

print(json.loads(r2.text))

# gunicorn --timeout 120 --bind 0.0.0.0:5000 app:app
# ngrok http 5000
