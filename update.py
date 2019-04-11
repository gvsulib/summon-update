#!/usr/bin/env python3

#Module for issuing http requests and reading responses
import requests

#sierra authentication requires that we encode the credentials, this module does that
import base64

#module for manipulating and reading JSON data
import json

#module that allows FTP
import ftplib

#modules for creating and working with dates and times
import datetime
import pytz

#access credentials, kept in separate file
import credentials

import os

#libraries to send emails
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

notificationEmail = "felkerk@gvsu.edu"

#open error log
try:
	error = open("error.log", "w+")
except OSError as err:
	print ("Unable to open error logfile: {0}".format(err))
	sendEmail("Unable to open error log for writing, terminating script: {0}".format(err), "Error Updating Summon", notificationEmail)
	quit()


def sendEmail(msgString, subject, address, error=None, timestamp=""):
	server = smtplib.SMTP('smtp.gvsu.edu', 25)
	msg = MIMEMultipart()
	#msg["From"] = "felkerk@gvsu.edu"
	msg["To"] = address
	msg["Subject"] = subject
	msg.attach(MIMEText(msgString, 'plain'))
	try:
		server.sendmail("felkerk@gvsu.edu", address, msg.as_string())         
   
	except smtplib.SMTPException as err:
		if error is not None:
			error.write(timestamp + 'Error: unable to send email: {}\n'.format(err))
		print("Error: unable to send email")



#set the time parameters for the query.  We want any record updated since 1:00AM the previous day
eastern = pytz.timezone("US/Eastern")

now = datetime.datetime.now(eastern)

offset = datetime.timedelta(hours=24)

previous = now - offset

previous = previous.strftime("%Y-%m-%dT%H:%M:%S")

#format dates for use in query string

filename = "TEST_DO_NOT_USE_gvsu" + now.strftime("%Y-%m-%d") + ".out"

timestamp = now.strftime("%Y-%m-%d:%H:%M")

now = now.strftime("%Y-%m-%dT%H:%M:%S")

searchString = "[" + previous + "Z," + now + "Z]"
print("Trying to retrieve records modified between {} and {}".format(previous, now))

print("Attempting to obtaina ccess token")
#now form and encode the access credentials:

credential = credentials.APIkey + ":" + credentials.clientSecret

encoded = base64.b64encode(credential.encode("utf-8"))

#create headers for the authentication request to the API
headers = {'Authorization': 'Basic %s' % encoded.decode("utf-8"), 'Content-Type' : 'application/x-www-form-urlencoded', }

r = requests.post('https://library.catalog.gvsu.edu/iii/sierra-api/v5/token', data = {'grant_type':'client_credentials'}, headers=headers)

#if the request fails, terminate and raise an error

if r.status_code != 200:
	sendEmail("Error Authenticating to the Sierra Server, Check error log", "Sierra update Error", notificationEmail, error, timestamp)
	error.write(timestamp + " " + str(r.status_code) + " " + r.text)
	print("Unable to get authentication token from sierra, check error log for more data")
	quit()
	
print("Access token obtained.")

print("Attempting to retrieve bibids.")
#get the access token from the reply

json_response = json.loads(r.text)

token = json_response["access_token"]

tokenType = json_response["token_type"]

headers = {'Authorization': 'Bearer ' + token}
params = {'updatedDate' : searchString, 'fields':'id', 'limit':'1000000', 'offset':'0'}

url = "https://library.catalog.gvsu.edu:443/iii/sierra-api/v5/bibs/"

r = requests.get(url, params=params, headers=headers)


if r.status_code == 404:
	sendEmail("No changed records found", "Sierra update", notificationEmail, error, timestamp)
	error.write(timestamp + " " + str(r.status_code) + " " + r.text + "\n")
	print("No changed records found")
	quit()

if r.status_code != 200:
        sendEmail("Error getting bib records from the Sierra Server, Check error log", "Sierra update Error", notificationEmail, error, timestamp)
        error.write(timestamp + " " + str(r.status_code) + " " + r.text)
        print("Error Getting bib records from sierra, check error log for more data")
        quit()



json_response = json.loads(r.text)

ids = json_response["entries"]



if not ids:
	sendEmail("No changed records found", "Sierra update", notificationEmail, error, timestamp)
	error.write(timestamp + " " + str(r.status_code) + " " + r.text)
	print("No changed records found")
	quit()

numRecords = (len(ids))

print("Successfully Retrieved bibids, {} records found.".format(numRecords))

cutoff = 100

query = ""
count = 0
totalCount = 0

print("Trying to open datafile for writing...")

#open data logfile
try:
        file = open(filename, "w+")
except OSError as err:
	sendEmail("Cannot open datafile for writing", "Sierra update Error", notificationEmail, error, timestamp)
	print ("Unable to open datafile: {0}".format(err))
	str = timestamp + " " + "Unable to open datafile: {0}".format(err)
	error.write(str)
	quit()	

print("starting to retrieve MARC records...")

for id in ids:
	count += 1
	totalCount += 1

	if count == 1:
		query = id["id"]
	else:
		query = query + "," + id["id"]

	if count == cutoff or totalCount == numRecords:
		count = 0
		query = query[1:]


		params={'id':query}

		url = 'https://library.catalog.gvsu.edu:443/iii/sierra-api/v4/bibs/marc'

		r = requests.get(url, params=params, headers=headers)

		if r.status_code != 200:
			sendEmail("Error generating Marc records, Check error log", "Sierra update Error", notificationEmail, error, timestamp)
			error.write(timestamp + " " + str(r.status_code) + " " + r.text)
			error.write(r.url)
			print("Unable to generate Marc records, check error log for more data")
			exit()

		json_response = json.loads(r.text)

		marcURL = json_response["file"]

		r = requests.get(marcURL, headers=headers)

		if r.status_code != 200:
			sendEmail("Error retrieving Marc record file, Check error log", "Sierra update Error", notificationEmail, error, timestamp)
			error.write(timestamp + " " + str(r.status_code) + " " + r.text)
			error.write(r.url)
			print("Unable to generate Marc records, check error log for more data")
			exit()

		file.write(r.text)
		query = ""
		print("{} of {} records written to file.".format(totalCount, numRecords))
#close the file to reset the pointer
file.close()

try:
        file = open(filename, "rb")
except OSError as err:
	sendEmail("Cannot open datafile for reading", "Sierra update Error", notificationEmail, error, timestamp)
	print ("Unable to open datafile: {0}".format(err))
	str = timestamp + " " + "Unable to open datafile: {0}".format(err)
	error.write(str)
	quit()

size = os.path.getsize(filename)

print("Attempting to transfer file of size {}".format(size))

summonFTP = ftplib.FTP("ftp.summon.serialssolutions.com", "gvsu", credentials.FTPPass)

summonFTP.cwd('/updates') 

filename = "STOR " + filename

summonFTP.storbinary(filename, file)

summonFTP.quit()



msg = "Uploaded {} records".format(numRecords)


sendEmail(msg, "Summon Update completed", notificationEmail, error, timestamp)


error.close()
file.close()
