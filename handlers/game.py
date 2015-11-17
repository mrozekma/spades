from Charts import *
from DB import db, getActiveGame
from Nav import Nav
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

nav = Nav(brand = 'right')
nav['gameplay'] = '/games/%(name)s'
nav['history'] = '/games/%(name)s/history'
nav['log'] = '//pileus.org/andy/spades/%(name)s.log'

# Seat positions don't matter (as long as play order is preserved), but it's logical to me that the first player is south
# This order is actually specified in game.js
seats = ('south', 'west', 'north', 'east')

@get('games/(?P<name>[0-9]{8}_[0-9]{6})', statics = ['websocket', 'game'])
def game(handler, name):
	logFilename = "%s.log" % name
	activeGame = getActiveGame()

	if activeGame is not None and activeGame.logFilename == logFilename:
		game = activeGame
		active = True
	elif logFilename in db['games']:
		game = db['games'][logFilename]
		active = False
	else:
		ErrorBox.die("Game not found", name)
	del activeGame

	handler.title(game.friendlyName)
	nav.out('gameplay', name = name)

	print "<div class=\"current-trick\">"
	for seat in seats:
		print "<div class=\"seat seat-%s seat-open\">" % seat
		print   "<div class=\"tags\"><span class=\"label label-danger tag-turn\">Turn</span><span class=\"label label-success tag-winning\">Winning</span><span class=\"label label-primary tag-lead\">Lead</span></div>"
		print   "<img class=\"play\" src=\"/card/back\">"
		print   "<div class=\"bottom\">"
		print     "<img class=\"avatar\" src=\"/player/-/avatar\">"
		print     "<div class=\"right\">"
		print       "<div class=\"username\">Open</div>"
		print         "<div class=\"tricks\"></div>"
		# print       "<div class=\"progress-text\">?/?</div>"
		# print       "<div class=\"progress\">"
		# print         "<div class=\"progress-bar\" style=\"width: 0%\"></div>"
		# print       "</div>"
		print     "</div>"
		print   "</div>"
		print "</div>"
	print "</div>"
	print "<br><br>"

	# handler.callFromHeader(Chart.include)

	# c = ScoreChart('score-chart', game)
	# handler.jsOnLoad(c.js)
	# c.placeholder()

@get('games/active')
def gamesActive(handler):
	game = getActiveGame()
	if game is None:
		ErrorBox.die("No currently active Spades game")
	redirect("/games/%s" % splitext(game.logFilename)[0])
