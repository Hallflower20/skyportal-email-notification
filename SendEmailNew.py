import requests
import pandas as pd
import json
import datetime
import numpy as np
import os

from bs4 import BeautifulSoup
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient

# Two lines with API keys, first line is Fritz key and second line is sendgrid key.
# MUST BE UNIQUELY GENERATED
f = open("api.js", "r")
tokens = f.readlines()

fritz_token = tokens[0].strip()
swilio_token = tokens[1].strip()

def send_email():
    # Get correct time-frame
    startd = datetime.datetime.combine(datetime.date.today() - datetime.timedelta(days=1), datetime.datetime.min.time())
    #endd = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
    token = fritz_token
    baselink = "https://fritz.science/source/"

    # Performs query, returns Response
    def api(method, endpoint, data=None, headers = {'Authorization': f'token {token}'}):
        response = requests.request(method, endpoint, params=data, headers=headers)
        return response

    # RCF group ID is 41
    data = {
                'includePhotometry': 'false',
                'numPerPage': 25,
                'startDate': datetime.datetime.strftime(startd, '%Y-%m-%dT%H:%M:%S.%f'),
                #'endDate': datetime.datetime.strftime(endd, '%Y-%m-%dT%H:%M:%S.%f'),
                'savedStatus': 'all',
                'groupIDs': "41"
                }

    response = api('GET', 'https://fritz.science/api/candidates', data = data)

    # Valid response returns code 200, invalid is 400
    print(f'HTTP code: {response.status_code}, {response.reason}')
    if response.status_code == 200:
        output = response.json()["data"]
        response_candidates_json = response.json()
        response_candidates_data = response_candidates_json['data']['candidates']
        new_sources=response_candidates_json['data']['totalMatches']

        with open('data.json', 'w') as outfile:
            json.dump(output, outfile)

    response_followup = api('GET', 'https://fritz.science/api/followup_request')
    response_followup_json = response_followup.json()

    data = {
                'includePhotometry': 'true',
                'numPerPage': 99999,
                'savedAfter': datetime.datetime.strftime(startd, '%Y-%m-%dT%H:%M:%S.%f'),
                #'savedBefore': datetime.datetime.strftime(endd, '%Y-%m-%dT%H:%M:%S.%f'),
                'group_ids': "41"
                }
    response_sources = api('GET', 'https://fritz.science/api/sources', data = data)
    response_sources.reason

    # Print entire source HTML if needed
    #with open('full.txt', 'w') as full:
        #full.write(BeautifulSoup(response_sources.text, 'html.parser').prettify())

    response_sources_json = response_sources.json()
    response_sources_data = response_sources_json['data']['sources']

    obj_id = []
    for i in response_followup_json["data"]:
        if(i["status"] != "deleted"):
            obj_id.append([i["obj_id"], int(i["payload"]["priority"])])
    obj_id = np.asarray(obj_id)
    new_saved = 0
    html_content = '<table class="styled-table"><thead><tr><th>Name</th><th>Filter</th><th>Current Mag</th><th>Priority</th><th>Saved Date</th><th>Type</th><th>Saver</th></thead><tbody>'
    print(str(len(response_sources_data)) + ' in list.')
    for i in response_sources_data:
        ztfid = '-'
        Type = '-'
        priority = '-'
        mag = '-'
        usedfilter = '-'
        saved_by_first = '-'
        saved_by_email = '-'

        ztfid = i["id"]
        created_at = i["created_at"]
        datetime_created_at = datetime.datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%f')

        # this photometry step should be changed to loop thrugh the photometry in case the most recent entry is None go back to the previous
        # alternatively get rid of all None entries first and then run the below
        if(len(i["photometry"]) != 0):
            photometry = i["photometry"][-1]
            usedfilter = ""
            mostRecent = 0
            for j in i["photometry"]:
                if(j["flux"] is not None):
                    mostRecent = j["flux"]
                    usedfilter = j["filter"]
            if(mostRecent != 0):
                mag = round(-2.5 * np.log10(float(mostRecent)/(3.631*10**9)), 2)

        index = np.where(obj_id[:,0] == ztfid)[0]
        if(ztfid in obj_id[:,0]):
            priority = (np.max(obj_id[index][:,1].astype(int)))

        if(len(i["classifications"]) != 0):
            Type = i["classifications"][0]["classification"]

        # Use to write out dict of source if needed
        #with open(ztfid + '_full.txt', 'w') as full:
            #full.write(json.dumps(i, indent=2))

        if(len(i["groups"]) != 0):
            maxd = startd
            for j in i["groups"]:
                if j["id"] == 41 and datetime.datetime.strptime(j["saved_at"], '%Y-%m-%dT%H:%M:%S.%f') > startd:
                    maxs = j
                    maxd = datetime.datetime.strptime(j["saved_at"], '%Y-%m-%dT%H:%M:%S.%f')

            datetime_saved_at = maxd
            saved_by_first = maxs["saved_by"]["first_name"]
            saved_by_email = maxs["saved_by"]["contact_email"]
            new_saved += 1
            line = '<tr class = "{}"><th><a href = "{}{}">{}</a></th> <th>{}</th> <th>{}</th> <th>{}</th> <th>{}</th> <th>{}</th> <th><a href = "mailto: {}">{}</a></th>'.format(usedfilter, baselink, ztfid, ztfid, usedfilter, mag, priority, datetime_saved_at.date(), Type, saved_by_email, saved_by_first)
            html_content += line
            html_content += "</tr>"

    html_content += "</tbody>"

    output = '''<style> .styled-table {         border-collapse: collapse;        margin: 25px 0;        font-size: 0.9em;        font-family: sans-serif;        min-width: 50vw;        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);    }    .styled-table thead tr {        background-color: #009879;\
            color: #ffffff;\
            text-align: center;\
        }\
    \
        .styled-table td {\
            padding: 12px 15px;\
        }\
        .styled-table tbody tr {\
            border-bottom: 1px solid #dddddd;\
        }\
    \
        .styled-table tbody tr:last-of-type {\
            border-bottom: 2px solid #009879;\
        }\
    \
    </style>'''
    output += "There have been {} new sources and {} new saved sources, from {} to {}. <br>".format(new_sources, new_saved, startd.date(), datetime.datetime.today().date()) + html_content

    file = open("EmailList.txt", "r")
    emails = []
    lines = file.readlines()
    for i in lines: emails.append(i.strip())

    message = Mail(
                    from_email="xhall@caltech.edu",
                    to_emails= emails,
                    subject="[RCF] New Saved Sources Email for {}".format(datetime.datetime.today().date()),
                    html_content=output,
                )

    sg = SendGridAPIClient(swilio_token)
    response = sg.send(message)

    print(response.status_code)
