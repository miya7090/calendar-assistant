from __future__ import print_function # for calendar, must be at beginning of file

print("\nLoading assistant...")
#################################
import datetime as DT
import random
random.seed(DT.time.microsecond)
# Google Calendar components
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
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
NXTHOURS = DT.timedelta(hours=3) # in calendar, definition of an impending event in 3 hours
timeZone = DT.timedelta(hours=5) # shouldn't use this if possible
startUpTime = DT.datetime.now() # used for refreshing
#################################
print("assistant has been loaded.\n")

def timeOfDay():
	print(DT.time().hour,"P")
	aroundTime = DT.datetime.now().hour + random.randint(-1,1)
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
	eventTime = DT.datetime.strptime(eventTime, "%Y-%m-%d %H:%M:%S")
	return eventTime

def formatMinHr(numMinutes, fuzzy=0):
	if numMinutes == 1:
		return "1 minute"
	elif numMinutes < 60:
		if fuzzy == 1:
			numMinutes = 10*round(numMinutes/10)
			return "about "+str(numMinutes)+" minutes"
		else:
			return str(numMinutes)+" minutes"
	else:
		hrs = int(numMinutes/60) # floors it
		mins = numMinutes%60
		if hrs == 1:
			hrs = "1 hour"
		else:
			hrs = str(hrs)+" hours"
		if mins == 0:
			return hrs # 0 minutes
		elif mins == 1:
			if fuzzy == 1:
				return "about "+hrs # 0 minutes
			else:
				mins = "1 minute"
		else:
			if fuzzy == 1:
				mins = 10*round(mins/10)
				return "about "+hrs+", "+str(mins)+" minutes"
			mins = str(mins)+" minutes"
		return hrs+", "+mins
	
def eventLen(myEvent):
	timeT = formatGT(myEvent["end"]["dateTime"])-formatGT(myEvent["start"]["dateTime"])
	return round(timeT.seconds/60)
	
def nextEvent(nowEvent = 0):
	# returns the next event to occur after the nowEvent, or if no next event, then 0; also returns time till
	if nowEvent == 0:
		maxNow = DT.datetime.utcnow()
	else:
		maxNow = formatGT(nowEvent["end"]["dateTime"])
	# Getting the next 1 event
	# 'Z' indicates UTC time
	eventsResult = service.events().list(calendarId='primary', timeMin=maxNow.isoformat()+"-05:00", maxResults=1, singleEvents=True,orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	if not events:
		return 0
	# get time till
	timeTill = formatGT(events[0]["start"]["dateTime"])-DT.datetime.now()
	return (events[0], round(timeTill.seconds/60))
	
def imminEvent(nowEvent = 0, maxEvents = 20, maxLater = DT.datetime.now() + NXTHOURS):
	# returns all events within the next few hours, or a number representing the minutes of free time until the next event (-1 if no next)
	if nowEvent == 0:
		maxNow = DT.datetime.now()
	else:
		maxNow = formatGT(nowEvent["end"]["dateTime"])
	# Getting the next 1 event
	# 'Z' indicates UTC time (taken off)
	eventsResult = service.events().list(calendarId='primary', timeMin=maxNow.isoformat()+"-05:00", timeMax=maxLater.isoformat()+"-05:00", maxResults=maxEvents, singleEvents=True,orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	if not events:
		# return time till next event
			nxt, nxtTill = nextEvent(nowEvent)
			if nxt != 0:
				return nxtTill
			else:
				return -1
	return events
	
def nowEvent():
	# returns the current event and number of other events, or (0,0) if none
	now = DT.datetime.now()
	# Getting the "current" event
	# 'Z' indicates UTC time
	eventsResult = service.events().list(calendarId='primary', timeMin=(now-2*NXTHOURS).isoformat()+"-05:00", timeMax=(now+2*NXTHOURS).isoformat()+"-05:00", maxResults=10, singleEvents=True,orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	events = list(reversed(events))
	if not events:
		return (0, now)
	finalAns = []
	for event in events:
		if formatGT(event["end"]["dateTime"]) > now and formatGT(event["start"]["dateTime"]) < now: # make sure is still running
			finalAns.append(event)
	if len(finalAns) == 0:
		return (0, 0)
	return (finalAns[0], len(finalAns)-1)

print("Good %s, %s. It's %s." % (timeOfDay(), myName, DT.datetime.now().strftime('%A, %I:%M%p')))
myNowEvent, myNowEventEnd = nowEvent()

user = input()
while user != "thanks":
	if user == "refresh please":
		myNowEvent, myNowEventEnd = nowEvent()
		print("Got it,", myName)
	# check for conflicts XXXX
	if user == "when's my next event?":
		myNextEvent, tillNextEvent = nextEvent(myNowEvent)
		print("You've got",myNextEvent["summary"],"scheduled for",formatGT(myNextEvent["start"]["dateTime"]).strftime("%I:%M"))
	if user == "how long until my next event?":
		myNextEvent, tillNextEvent = nextEvent(myNowEvent)
		print("You've got",formatMinHr(tillNextEvent,1))
	if user == "how long is my next event?":
		myNextEvent, tillNextEvent = nextEvent(myNowEvent)
		print(myNextEvent["summary"],"is for",formatMinHr(eventLen(myNextEvent)))
	if user == "anything coming up?":
		imEvents = imminEvent(myNowEvent)
		if isinstance(imEvents, int): # no events, just number
			if imEvents == -1:
				print("You have no events coming up!")
			else:
				print("You've got",imEvents,"till your next event.")
		else:
			print("Yep. Next you have:")
			for imEv in imEvents:
				print(imEv["summary"])
	if user == "can i move my next event up?":
		myNextEvent, tillNextEvent = nextEvent(myNowEvent)
		nxtEvLength = eventLen(myNextEvent)
		if myNextEvent == 0:
			print("You don't have any events next.")
		else:
			# get length of next event
			nxtImEvs = imminEvent(myNowEvent, maxLater=formatGT(myNextEvent["start"]["dateTime"]))
			if isinstance(nxtImEvs,int) and nxtImEvs != -1:
				if nxtImEvs>nxtEvLength:
					print("Sure, I can do that")
				else:
					print("You have",formatMinHr(nxtImEvs),"of time at X but it won't be enough")
			else:
				print("There's an event immediately after this so I can't do anything yet")
	if user == "add an event":
		pass
	user = input()
	user = user.lower()

print("Closing assistant...")
