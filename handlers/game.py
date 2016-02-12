from Charts import *
from Data import bidValue
from DB import db, getActiveGame, getGames
from Nav import Nav
from utils import *

from rorn.Box import ErrorBox

from os.path import splitext

def nav(where, game):
	nav = Nav(brand = 'right')
	if not game.finished:
		nav['current round'] = '/games/%(name)s'
	nav['history'] = "/games/%%(name)s/history%s" % ('#g' if game.finished else "#r%d" % len(game.rounds))
	nav['log'] = '//pileus.org/andy/spades/%(name)s.log'

	if where == 'history':
		nav['history', 'game'] = '#g'
		numRounds = len(game.rounds)
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
		print     "<img class=\"avatar\" src=\"/players/-/avatar\">"
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
		print     "<img class=\"avatar\" src=\"/players/-/avatar\"></img>"
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
		print     "<th class=\"seat-open\"><img class=\"avatar\" src=\"/players/-/avatar\"><div class=\"username\">&lt;open&gt;</div></th>"
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

@get('games/active')
def gamesActive(handler):
	game = getActiveGame()
	if game is None:
		ErrorBox.die("No currently active Spades game")
	redirect("/games/%s" % splitext(game.logFilename)[0])

def teamName(game, team):
	name = game.teamNames[team]
	players = '/'.join(team)
	if name == players:
		return name
	return "%s (%s)" % (name, players)

def printResults(round, team):
	game = round.game
	bid = sum(bidValue(round.bidsByPlayer[player]) for player in team)
	taken = sum(len(round.tricksByWinner[player]) for player in team)

	if taken >= bid:
		change = 10 * bid
		print "<li>%s bid %d, made it with %d (+%d)" % (teamName(game, team), bid, taken, 10 * bid)
		print "<ul>"
		if taken > bid:
			change += taken - bid
			prevBags = sum(r.bags[team] for r in round.previousRounds) % game.bagLimit
			print "<li>Took %s, up to %d (+%d)</li>" % (pluralize(taken - bid, 'bag', 'bags'), prevBags + taken - bid, taken - bid)
			if prevBags + taken - bid >= game.bagLimit:
				change -= 10 * game.bagLimit
				print "<li>Bagged out (-%d)</li>" % (10 * game.bagLimit)
	else:
		change = -10 * bid
		print "<li>%s bid %d, set with %d (-%d)" % (teamName(game, team), bid, taken, 10 * bid)
		print "<ul>"
	for player in team:
		bid = round.bidsByPlayer[player]
		if bid in ('nil', 'blind'):
			playerTaken = len(round.tricksByWinner[player])
			desc = 'blind nil' if bid == 'blind' else 'nil'
			thisChange = 10 * game.bagLimit * (2 if bid == 'blind' else 1) * (1 if playerTaken == 0 else -1)
			if playerTaken == 0:
				print "<li>%s made %s (%d)</li>" % (player, desc, thisChange)
			else:
				print "<li>%s took %d, failed %s (%d)" % (player, playerTaken, desc, thisChange)
			change += thisChange
	if change == 0:
		print "<li>No score change, still at %d points</li>" % round.score[team]
	else:
		print "<li>%s %s, %s to %d</li>" % (('Gained' if change > 0 else 'Lost'), pluralize(abs(change), 'point', 'points'), ('up' if change > 0 else 'down'), round.score[team])
	print "</ul></li>"

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
		print "<div class=\"round-box\" id=\"box-r%d\">" % (i + 1)

		if round.finished:
			print "<h2>Results</h2>"
			print "<ul>"
			for team in game.teams:
				printResults(round, team)
			scores = round.score
			if len(set(scores.values())) == 1:
				score = scores[game.teams[0]]
				if score >= game.goal:
					print "<li>Tied at %d. Sudden death</li>" % score
				else:
					print "<li>Tied at %d. %d more to win</li>" % (game.goal - score)
			else:
				leader = game.teams[0] if scores[game.teams[0]] > scores[game.teams[1]] else game.teams[1]
				follower = game.teams[0] if leader == game.teams[1] else game.teams[1]
				if scores[leader] >= game.goal:
					print "<li>%s win %s. %s trail by %d</li>" % (teamName(game, leader), ('exactly' if scores[leader] == game.goal else 'by %d' % (scores[leader] - game.goal)), teamName(game, follower), scores[leader] - scores[follower])
				else:
					print "<li>%s lead by %d. %d more to win</li>" % (teamName(game, leader), scores[leader] - scores[follower], game.goal - scores[leader])
			print "</ul>"

		print "<h2>Deal</h2>"
		print "<div class=\"deal\">"
		deal = round.deal
		winners = [trick.win for trick in round.tricks if trick is not None and trick.finished]
		for player in game.players:
			print "<div class=\"player\">"
			print "<img src=\"/players/%s/avatar\">" % player
			print "<div class=\"username\">%s</div>" % player
			print "</div>"
			print "<div class=\"cards\">"
			for card in deal.get(player, []):
				cls = ['card', "card-%s" % card]
				if card in winners:
					cls.append('winner')
				print "<div class=\"%s\"></div>" % ' '.join(cls)
			for i in range(13 - (len(deal[player]) if player in deal else 0)):
				print "<div class=\"card card-back\"></div>"
			print "</div>"
		print "</div>"
		HandsHeatmap("r%d-hands-heatmap" % (i + 1), round).emplace(handler)

		print "<h2>Tricks</h2>"
		print "<table class=\"past-tricks\">"
		print "<tr>"
		print "<th></th>"
		for player in game.players:
			print "<th class=\"seat-open\"><img class=\"avatar\" src=\"/players/%s/avatar\"><div class=\"username\">%s</div></th>" % (player, player)
		print "</tr>"
		for i, trick in enumerate(round.tricks):
			print "<tr data-trick-number=\"%d\">" % (i + 1)
			print "<td class=\"trick-number\"><span class=\"label label-default\">Trick %d</span></td>" % (i + 1)
			if trick:
				plays = [trick.playsByPlayer[player] for player in game.players]
				lead = trick.plays[0]
				win = trick.win
				for play in plays:
					print "<td class=\"trick\">"
					if play:
						if play == lead:
							print "<span class=\"label label-primary tag-lead\">Lead</span>"
						if play == win:
							print "<span class=\"label label-success tag-winning\">Won</span>"
					print "<img class=\"card\" src=\"/card/%s\">" % (play or 'back')
					print "</td>"
			else:
				for j in range(4):
					print "<td class=\"trick\"><img class=\"card\" src=\"/card/back\"></td>"
			print "</tr>"
		print "</table>"

		print "</div>"

@get('games/history.less')
def historyLess(handler):
	handler.wrappers = False
	handler.contentType = 'text/css'
	from Data import ordering
	for card in ['back'] + ordering:
		print """
.cards .card-%(card)s {
    background-image: url(/card/%(card)s);
    &.winner {
        // https://css-tricks.com/tinted-images-multiple-backgrounds/
        background-image: linear-gradient(rgba(0, 255, 0, .25), rgba(0, 255, 0, .25)), url(/card/%(card)s);
    }
}
""" % {'card': card}
