import base64
import requests

class TanzaniaSMSService:
    BASE_URL = "https://messaging-service.co.tz/api/sms/v1/test/text/single"

    def __init__(self, username, password):
        auth_string = f"{username}:{password}"
        self.token = base64.b64encode(auth_string.encode()).decode()

    def send_sms(self, to, text, sender="N-SMS", reference=None):
        payload = {
            "from": sender,
            "to": to,
            "text": text,
            "reference": reference or "ref-" + str(id(self))
        }

        headers = {
            "Authorization": f"Basic {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        r = requests.post(self.BASE_URL, json=payload, headers=headers)
        return r.json(), r.status_code


if __name__ == "__main__":
    sms = TanzaniaSMSService("Maghettoni", "32b9136904e6b5a7878008e455934e61")
    response, status = sms.send_sms("255716718040", "Hello GCL here!")
    print(response)
