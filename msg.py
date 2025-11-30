import requests

url = "https://messaging-service.co.tz/api/sms/v2/test/text/single"  # test endpoint
# url = "https://messaging-service.co.tz/api/sms/v2/text/single"    # production endpoint

headers = {
    "Authorization": "Bearer a80bec15ddc31b667525d9813daeaf54",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

data = {
    "from": "",
    "to": "255762082712",
    "text": "Your message",
    "flash": 0,
    "reference": "aswqetgcv"
}

response = requests.post(url, json=data, headers=headers)
print(response.status_code)
print(response.json())
