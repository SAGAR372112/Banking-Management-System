import requests
import time

url = "http://127.0.0.1:8000/api/accounts/5/"

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczMjkzNzIyLCJpYXQiOjE3NzMyMDg0NzIsImp0aSI6Ijg1ZTAyYzVkNGYxYjQzOTg4ZTVjZGMzZDM2NGE2ZTQyIiwidXNlcl9pZCI6Nn0.FcLxQ2s5HPcHZ_BjjSEgh1lqOXZIPED5NBIJ9zAPCvg"
}

data = {
    "amount": "1000.00",
    "reference": "Scheduled deposit"
}
Start_time = time.time()
response = requests.get(url, json=data, headers=headers)
End_time = time.time()
print(End_time - Start_time)
print(f"Response: {response.json()}")