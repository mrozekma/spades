from datetime import datetime, timedelta
from json import dumps as toJS
from os.path import splitext

import DB
from DB import db, getGames

@get('', statics = 'games')
def games(handler):
	def makeEvent(game):
		event = {'log': splitext(game.logFilename)[0],
		         'title': game.friendlyName,
		         'start': game.start.strftime('%Y-%m-%dT%H:%M:%S')}
		if game.finished:
			event['end'] = game.end
		else:
			event['end'] = datetime.now()
			event['color'] = '#d4604a'
		# For some unknown reason the new version of fullcalendar is shorting all the events by one day, so we lie about the end date
		event['end'] += timedelta(days = 1)
		event['end'] = event['end'].strftime('%Y-%m-%dT%H:%M:%S')
		return event

	events = [makeEvent(game) for game in getGames().values()]
	handler.jsOnReady("makeCalendar(%s);" % toJS(events))

	print "<script src=\"/static/moment.js\" type=\"text/javascript\"></script>"
	print "<link href=\"/static/fullcalendar.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/fullcalendar.js\" type=\"text/javascript\"></script>"
	print "<div id=\"calendar\"></div>"
	print "<br><br>"

@get('test')
def test(handler):
	for i in range(100):
		print "Content<br>"
