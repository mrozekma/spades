from Charts import *
from DB import db, getActiveGame
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

@get('games/(?P<name>[0-9]{8}_[0-9]{6})')
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

	# handler.title('Game', game.friendlyName)

	print "%s<br>" % ' '.join(game.players)
	for player in game.players:
		print "<img src=\"http://www.gravatar.com/avatar/%s?s=64&d=wavatar&r=x\">" % md5(player)
	print "<br><br>"

	handler.callFromHeader(Chart.include)

	c = ScoreChart('score-chart', game)
	handler.jsOnLoad(c.js)
	c.placeholder()

@get('games/active')
def gamesActive(handler):
	game = getActiveGame()
	if game is None:
		ErrorBox.die("No currently active Spades game")
	redirect("/games/%s" % splitext(game.logFilename)[0])
