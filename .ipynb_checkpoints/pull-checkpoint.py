import requests
import pandas as pd
import json
import datetime

startd = datetime.date.today() - datetime.timedelta(days=1)

print(startd)

token = "a1a4bef7-17c6-492c-8341-7430ffe415b1"

def api(method, endpoint, data=None, headers = {'Authorization': f'token {token}'}):
    response = requests.request(method, endpoint, params=data, headers=headers)
    return response

data = {
            'includePhotometry': 'true',
            'startDate': str(startd)
            }

response = api('GET', 'https://fritz.science/api/candidates', data = data)

print(f'HTTP code: {response.status_code}, {response.reason}')
if response.status_code == 200:
    output = response.json()["data"]

    with open('data.json', 'w') as outfile:
        json.dump(output, outfile)