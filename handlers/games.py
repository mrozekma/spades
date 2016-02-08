from datetime import datetime
from json import dumps as toJS
from os.path import splitext

import DB
from DB import db, getGames, getActiveGame
from utils import *

@get('games', statics = 'games')
def games(handler):
	def makeEvent(game):
		event = {'log': splitext(game.logFilename)[0],
		         'title': game.friendlyName,
		         'start': game.start.strftime('%Y-%m-%dT%H:%M:%S')}
		if game.finished:
			event['end'] = game.end
		else:
			event['end'] = datetime.utcnow()
			event['color'] = '#d4604a'
		event['end'] = event['end'].strftime('%Y-%m-%dT%H:%M:%S')
		return event

	events = [makeEvent(game) for game in getGames().values()]
	handler.jsOnReady("makeCalendar(%s);" % toJS(events))

	print "<script src=\"/static/third-party/moment.js\" type=\"text/javascript\"></script>"
	print "<link href=\"/static/third-party/fullcalendar.css\" rel=\"stylesheet\" type=\"text/css\" />"
	print "<script src=\"/static/third-party/fullcalendar.js\" type=\"text/javascript\"></script>"
	print "<div id=\"calendar\"></div>"
	print "<br><br>"

@get('')
def currentGame(handler):
	game = getActiveGame()
	if game is None:
		redirect('/games')
	else:
		redirect("/games/%s" % splitext(game.logFilename)[0])
