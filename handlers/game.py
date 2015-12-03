from Charts import *
from DB import db, getActiveGame
from Nav import Nav
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

nav = Nav(brand = 'right')
nav['current round'] = '/games/%(name)s'
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

	handler.title(game.friendlyName)
	nav.out('current round', name = name)

	print ErrorBox(title = '', text = '', id = 'game-error')
	print "<div class=\"cols\">"
	print   "<div class=\"disconnected-icon glyphicon glyphicon-transfer\" title=\"Disconnected from server\"></div>"
	print   "<div class=\"current-trick col\">"
	print     "<div class=\"pregame-players\">"
	for i in range(4):
		print   "<div class=\"pregame-player seat-open\">"
		print     "<img class=\"avatar\" src=\"/player/-/avatar\">"
		print     "<div class=\"username\">&lt;open&gt;</div>"
		print   "</div>"
	print     "</div>"
	for seat in ('south', 'west', 'north', 'east'):
		print "<div class=\"seat seat-%s seat-open\">" % seat
		print   "<div class=\"tags\">"
		print     "<span class=\"label label-danger tag-turn\">Turn</span>"
		print     "<span class=\"label label-success tag-winning\">Winning</span>"
		print     "<span class=\"label label-primary tag-lead\">Lead</span>"
		print   "</div>"
		print   "<img class=\"card\" src=\"/card/back\">"
		print   "<div class=\"bottom\">"
		print     "<img class=\"avatar\" src=\"/player/-/avatar\"></img>"
		print     "<div class=\"right\">"
		print       "<div class=\"username\">&lt;open&gt;</div>"
		print       "<div class=\"tricks\">"
		# print       "<img class=\"out\" src=\"/card/nil\">"
		# print       "<img class=\"out\" src=\"/card/blind\">"
		# for i in range(13):
			# print     "<img class=\"out\" src=\"/card/blank\">"
		print       "</div>"
		print     "</div>"
		print   "</div>"
		print "</div>"
	print   "</div>"
	print   "<div class=\"col\">"
	print     "<h2>Previous tricks</h2>"
	print     "<table class=\"past-tricks\">"
	print       "<tr>"
	print         "<th></th>"
	for i in range(4):
		print     "<th class=\"seat-open\"><img class=\"avatar\" src=\"/player/-/avatar\"><div class=\"username\">&lt;open&gt;</div></th>"
	print       "</tr>"
	for i in range(13, 0, -1):
		print   "<tr data-trick-number=\"%d\">" % i
		print     "<td class=\"trick-number\"><span class=\"label label-default\">Trick %d</span></td>" % i
		for j in range(4):
			print "<td class=\"trick\">"
			print   "<span class=\"label label-primary tag-lead\">Lead</span>"
			print   "<span class=\"label label-success tag-winning\">Won</span>"
			print   "<img class=\"card\" src=\"/card/back\">"
			print "</td>"
		print   "</tr>"
	print     "</table>"
	print   "</div>"
	print   "<div class=\"col\">"
	print     "<h2>Remaining cards</h2>"
	print     "<button class=\"remaining-cards\">Show unplayed cards</button>"
	print     "<div class=\"remaining-cards\">"
	for suit in 'sdch':
		for rank in ('A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'):
			print "<img class=\"card\" src=\"/card/%s%s\">" % (rank, suit)
		print "<br>"
	print     "</div>"
	print     "<br><br>"
	print   "</div>"
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
