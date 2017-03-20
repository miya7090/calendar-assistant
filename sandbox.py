from __future__ import print_function # for calendar, must be at beginning of file
print("\nLoading assistant...")
###########################
import time
import random
random.seed(time.time())
# Google Calendar components
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import datetime
try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'assistant'

# Variables
myName = "user"
mood = "happy"
NXTHOURS = 3 # in calendar, definition of an impending event in 2 hours

###########################
print("assistant has been loaded.\n")


def timeOfDay():
	aroundTime = time.localtime().tm_hour + random.randint(-1,1)
	if(aroundTime <= 10):
		return "morning"
	elif(aroundTime <= 16):
		return "afternoon"
	else:
		return "evening"

# for Google calendar
def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
								   'calendar-python-quickstart.json')

	store = Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)

def formatGT(eventTime): # stands for format google thingy
	eventTime = eventTime.split('T')
	eventTime = ' '.join(eventTime)
	eventTime = eventTime.split('-')
	eventTime.pop(3)
	eventTime = '-'.join(eventTime)
	eventTime = datetime.datetime.strptime(eventTime, "%Y-%m-%d %H:%M:%S")
	eventTime = datetime.timedelta(hours=5)+eventTime # change to UTC
	return eventTime

def imminEvent(nowEvent, maxNow = datetime.datetime.utcnow(), maxEvents = 1, maxLater = datetime.timedelta(hours=NXTHOURS)+datetime.datetime.utcnow()): # the imminent event
	now = datetime.datetime.utcnow()
	later = datetime.timedelta(hours=NXTHOURS)+datetime.datetime.utcnow()
	# Getting the next 1 event
	# 'Z' indicates UTC time
	eventsResult = service.events().list(
		calendarId='primary', timeMin=maxNow.isoformat()+'Z', timeMax=maxLater.isoformat()+'Z', maxResults=maxEvents, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	if not events:
		if nowEvent == 0: # not doing anything now either
			print("You've got nothing planned for the next few hours." % NXTHOURS)
		else:
			print("After this, you've got some free time.")
		return 0
	i = 0
	for event in events:
		i = i + 1
		eventTime = event['start']["dateTime"]
		eventTime = formatGT(eventTime)
		# print(maxNow.isoformat())
		timeTill = round(((eventTime-now).seconds)/60)
		if i == 1:
			print("You've got", event['summary'], "in", timeTill, "minutes.")
		elif i == 2:
			print("You've also scheduled for:\n"+event['summary'])
		else:
			print(event['summary'])
	return events[0]["id"]
	
def nextEvent(nowEvent, maxNow = datetime.datetime.utcnow(), notify = "on"):
	now = datetime.datetime.utcnow()
	# Getting the next 1 event
	# 'Z' indicates UTC time
	eventsResult = service.events().list(
		calendarId='primary', timeMin=maxNow.isoformat()+'Z', maxResults=1, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	if not events:
		print("There doesn't seem to be another event on your calendar.")
		return 0
	for event in events:
		eventTime = event['start']["dateTime"]
		eventTime = formatGT(eventTime)
		timeTill = round(((eventTime-now).seconds)/60)
		if notify == "on":
			print("The next thing you have scheduled is", event['summary'], "which is in", timeTill, "minutes.")
	return events[0]
	
def nowEvent():
	now = datetime.datetime.utcnow()
	before = datetime.datetime.utcnow()-datetime.timedelta(hours=NXTHOURS)
	# Getting the next 1 event
	# 'Z' indicates UTC time
	eventsResult = service.events().list(
		calendarId='primary', timeMin=before.isoformat()+'Z', timeMax=now.isoformat()+'Z', maxResults=1, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	if not events:
		return 0, now
	for event in events:
		print("You're currently scheduled for %s." % event['summary'])
		evenEnd = event['end']["dateTime"]
		evenEnd = formatGT(evenEnd)
	return events[0]["id"], evenEnd
	
def isImportant(myEvent):
	print(myEvent)
		
print("Good %s, %s. It's %s." % (timeOfDay(), myName, datetime.datetime.now().strftime('%A, %I:%M%p')))
myNowEvent, myNowEventEnd = nowEvent()

user = input()
while user != "Thanks":
	# check for conflicts XXXX
	if user == "When's my next event?":
		myNextEvent = nextEvent(myNowEvent, maxNow = myNowEventEnd)
		isImportant(myNextEvent)
	if user == "Anything coming up?":
		imminEvent(myNowEvent, maxNow = myNowEventEnd, maxEvents = 5)
	if user == "Can I move my next event up?":
		nextEvent = nextEvent(myNowEvent, maxNow = myNowEventEnd, notify = "off")
		if nextEvent != 0:
			# get length of next event
			eventLength = formatGT(nextEvent["end"]["dateTime"]) - formatGT(nextEvent["start"]["dateTime"])
			eventLength = round((eventLength.seconds)/60)
			print("length of event %s is %d" % (nextEvent["summary"], eventLength))
			busySpace = imminEvent(myNowEvent, maxNow = myNowEventEnd, maxEvents = 1, maxLater = formatGT(nextEvent["start"]["dateTime"])) # the imminent event
			if busySpace != 0:
				print("You've scheduled", busySpace["summary"], "at that time.");
				print("Do you want me to move", nextEvent["summary"], "up anyway? Or swap the two events?");
			else:
				print("Yeah. [cue move next event up]");
	if user == "Add an event":
		pass
	user = input()

print("Closing assistant...")

