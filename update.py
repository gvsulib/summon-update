#!/usr/bin/env python3

import requests
import base64
import json
import datetime
import credentials
import pytz

eastern = pytz.timezone("US/Eastern")

now = datetime.datetime.now(eastern)

offset = datetime.timedelta(days=5)

previous = now - offset

previous = previous.strftime("%Y-%m-%dT01:00:00")

now = now.strftime("%Y-%m-%dT01:00:00")

searchString = "[" + previous + "Z," + now + "Z]"

credentials = credentials.APIkey + ":" + credentials.clientSecret

encoded = base64.b64encode(credentials.encode("utf-8"))

headers = {'Authorization': 'Basic %s' % encoded.decode("utf-8"), 'Content-Type' : 'application/x-www-form-urlencoded', }

r = requests.post('https://sandbox.iii.com/iii/sierra-api/v3/token', data = {'grant_type':'client_credentials'}, headers=headers)

json_response = json.loads(r.text)

token = json_response["access_token"]

tokenType = json_response["token_type"]

headers = {'Authorization': 'Bearer ' + token}
params = {'updatedDate' : searchString, 'fields':'id'}

url = "https://sandbox.iii.com:443/iii/sierra-api/v5/bibs/"

r = requests.get(url, params=params, headers=headers)

json_response = json.loads(r.text)

ids = json_response["entries"]

query = ""

for id in ids:

	query = query + "," + id["id"]

query = query[1:]

params={'id':query}

url = 'https://sandbox.iii.com:443/iii/sierra-api/v5/bibs/marc'

r = requests.get(url, params=params, headers=headers)

json_response = json.loads(r.text)

marcURL = json_response["file"]

r = requests.get(marcURL, headers=headers)

file = open("updated_files.out", "w+")

file.write(r.text)

file.close

