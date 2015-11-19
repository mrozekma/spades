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
	print "<div class=\"disconnected-icon glyphicon glyphicon-transfer\" title=\"Disconnected from server\"></div>"
	for seat in ('south', 'west', 'north', 'east'):
		# Filled in by javascript
		print "<div class=\"seat-%s\"></div>" % seat
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
