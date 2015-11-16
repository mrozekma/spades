from Charts import *
from DB import db, getActiveGame
from Nav import Nav
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

nav = Nav()
nav['gameplay'] = '/games/%(name)s'
nav['history'] = '/games/%(name)s/history'

# Seat positions don't matter (as long as play order is preserved), but it's logical to me that the first player is south
seats = ('south', 'west', 'north', 'east')

@get('games/(?P<name>[0-9]{8}_[0-9]{6})', statics = 'game')
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

	# print "%s<br>" % ' '.join(game.players)
	# for player in game.players:
		# print "<img src=\"http://www.gravatar.com/avatar/%s?s=64&d=wavatar&r=x\">" % md5(player)

	print "<div class=\"current-trick\">"
	for player, seat in zip(game.players, seats):
		print "<div class=\"seat seat-%s seat-open\" data-player=\"%s\">" % (seat, player)
		print   "<img class=\"play\" src=\"/card/back\">"
		print   "<div class=\"bottom\">"
		print     "<img class=\"avatar\" src=\"/player/-/avatar\">"
		print     "<div class=\"right\">"
		print       "<div class=\"username\">Open</div><br>"
		print       "<div class=\"progress-text\">?/?</div>"
		print       "<div class=\"progress\">"
		print         "<div class=\"progress-bar\" style=\"width: 0%\"></div>"
		print       "</div>"
		print     "</div>"
		print   "</div>"
		print "</div>"
	print "</div>"

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
