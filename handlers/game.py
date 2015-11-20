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
	game = getActiveGame()

	if game is None or game.logFilename != logFilename:
		if logFilename in db['games']:
			redirect("/games/%s/history" % name)
		else:
			ErrorBox.die("Game not found", name)

	handler.title('Loading...') # Filled in by javascript
	nav.out('gameplay', name = name)

	print "<div class=\"cols\">"
	print "<div class=\"current-trick col\">"
	print "<div class=\"disconnected-icon glyphicon glyphicon-transfer\" title=\"Disconnected from server\"></div>"
	for seat in ('south', 'west', 'north', 'east'):
		# Filled in by javascript
		print "<div class=\"seat seat-%s\"></div>" % seat
	print "</div>"
	print "<div class=\"col\">"
	print "<h2>Previous tricks</h2>"
	print "<table class=\"past-tricks\"></table>"
	print "</div>"
	print "<div class=\"col\">"
	print "<h2>Remaining cards</h2>"
	print "<button class=\"remaining-cards\">Show unplayed cards</button><div class=\"remaining-cards\"></div><br><br>"
	print "</div>"
	print "</div>"

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
