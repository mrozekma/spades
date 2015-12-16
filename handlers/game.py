from Charts import *
from DB import db, getActiveGame, getGames
from Nav import Nav
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

def nav(where, game):
	nav = Nav(brand = 'right')
	if not game.finished:
		nav['current round'] = '/games/%(name)s'
	nav['history'] = '/games/%(name)s/history'
	nav['log'] = '//pileus.org/andy/spades/%(name)s.log'

	if where == 'history':
		nav['history', 'game'] = '#g'
		numRounds = len(game.rounds)
		if numRounds > 0 and not game.rounds[-1].finished:
			numRounds -= 1
		for i in range(numRounds):
			nav['history', "round %d" % (i + 1)] = "#r%d" % (i + 1)

	nav.out(where, name = game.logFilename[:-4])

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
	nav('current round', game)

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

@get('games/(?P<name>[0-9]{8}_[0-9]{6})/history', statics = ['game-history'])
def gameHistory(handler, name):
	logFilename = "%s.log" % name
	game = getGames().get(logFilename, None)
	if game is None:
		ErrorBox.die("Game not found", name)
	teams = game.teams

	handler.title(game.friendlyName)
	nav('history', game)
	handler.callFromHeader(Chart.include)

	print "<div class=\"nav-arrows\">"
	print "<div>"
	print "<a class=\"prev\" href=\"#\"><img src=\"/static/images/prev.png\"></a>"
	print "<a class=\"next\" href=\"#\"><img src=\"/static/images/next.png\"></a>"
	print "</div>"
	print "</div>"

	# If we haven't even filled the seats yet, bail out pretty early
	if None in game.players:
		if game.finished:
			ErrorBox.die("Game aborted before first round")
		else:
			ErrorBox.die("Waiting for first round to begin")

	print "<div class=\"round-box\" id=\"box-g\">"
	print "<h2>Score</h2>"
	ScoreChart('score-chart', game).emplace(handler)
	print "</div>"

	for i, round in enumerate(game.rounds):
		if not round.finished:
			continue
		print "<div class=\"round-box\" id=\"box-r%d\">" % (i + 1)
		print "<h2>Deal</h2>"
		print "<div class=\"deal\">"
		deal = round.deal
		for player in game.players:
			print "<div class=\"player\">"
			print "<img src=\"/player/%s/avatar\">" % player
			print "<div class=\"username\">%s</div>" % player
			print "</div>"
			print "<div class=\"cards\">"
			for card in deal[player]:
				print "<img src=\"/card/%s\">" % card
			print "</div>"
		print "</div>"
		HandsHeatmap("r%d-hands-heatmap" % (i + 1), round).emplace(handler)
		print "</div>"
