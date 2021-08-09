import requests
import pandas as pd
import json
import datetime
import numpy as np
import os

f = open("api.js", "r")
tokens = f.readlines()

token = tokens[0].strip()

# Performs query, returns Response
def api(method, endpoint, data=None, headers = {'Authorization': f'token {token}'}):
  response = requests.request(method, endpoint, params=data, headers=headers)
  return response

# Priority ajustment starts here
def adjust_priority():
    dat1 = np.genfromtxt('ztf2_iband_fields_maingrid.csv', dtype=int)
    dat2 = np.genfromtxt('ztf2_iband_fields_secondarygrid.csv', dtype=int)
    dat = np.concatenate((dat1, dat2))

    followups = api('GET', 'https://fritz.science/api/followup_request').json()['data']

    SEDM_queue = []
    priorities = []
    SEDM_fields = []

    for f in followups:
      fu_end = datetime.datetime.strptime(f['payload']['end_date'], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)

      if fu_end >= datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) and f['status'] == 'submitted':
          if f['payload']['priority'] == 1:

              alerts = api('GET', 'https://fritz.science/api/alerts/'+f['obj_id']+'?includeAllFields=True')['data']

              if alerts[-1]['candidate']['field'] in dat:
                  #print(f['obj_id'] + ' in field ' + str(alerts[-1]['candidate']['field']) + ' with priority ' + str(f['payload']['priority']) + ' to be adjusted to priority 1.5')
                  payload = f['payload']
                  payload['priority'] = 1.5

                  data = {'allocation_id': 1, 'payload': payload, 'obj_id': 'ZTF21abmzpmc'}

              #print(api('PUT', 'https://fritz.science/api/followup_request/'+str(f['id']), data=data))
              api('PUT', 'https://fritz.science/api/followup_request/'+str(f['id']), data=data)
