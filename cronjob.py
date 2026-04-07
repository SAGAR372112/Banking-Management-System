import requests
import time

url = "http://127.0.0.1:8000/api/accounts/5/"

headers = {
    "Authorization": "Bearer <access_token>"
}

data = {
    "amount": "1000.00",
    "reference": "Scheduled deposit"
}
Start_time = time.time()
response = requests.post(url, json=data, headers=headers)
End_time = time.time()
print(End_time - Start_time)
print(f"Response: {response.json()}")