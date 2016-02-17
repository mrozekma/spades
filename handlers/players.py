from Charts import *
from Data import ordering, bidValue
from DB import getGames
from ProgressBar import ProgressBar
from utils import *
from rorn.Box import ErrorBox

from bleach import clean
from collections import OrderedDict
import os
from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO

@get('players', statics = 'players')
def players(handler):
	handler.title('Players')

	players = set()
	for game in getGames().values():
		players |= set(game.players)
	players = sorted(players - {None})

	for player in players:
		print "<div class=\"player\">"
		print "<a href=\"/players/%s\"><img src=\"/players/%s/avatar\">" % (player, player)
		print "<div class=\"username\">%s</div></a>" % player
		print "</div>"

@get('players/(?P<player>[^/]+)', statics = 'player')
def player(handler, player):
	handler.title(player)
	handler.callFromHeader(Chart.include)
	allGames = getGames().values()
	games = filter(lambda game: player in game.players, allGames)
	if len(games) == 0:
		ErrorBox.die("Player not found", "No player named <b>%s</b> has played in a recorded game" % clean(player))

	print "<img class=\"avatar\" src=\"/players/%s/avatar\">" % player

	counts = OrderedDict((cat, 0) for cat in ('games', 'rounds', 'tricks', 'nils', 'blind_nils', 'nil_defenses'))
	wins = {cat: 0 for cat in counts}
	cards = {card: 0 for card in ordering}
	leads = {card: 0 for card in ordering}
	for game in games:
		counts['games'] += 1
		if player in (game.winner or []):
			wins['games'] += 1
		partner = game.partners[player]
		for round in game.rounds:
			if not round.finished:
				continue
			counts['rounds'] += 1
			bid = round.bidsByPlayer[player]
			partnerBid = round.bidsByPlayer[partner]
			taken, partnerTaken = 0, 0
			for trick in round.tricks:
				if trick is not None:
					counts['tricks'] += 1
					play = trick.playsByPlayer[player]
					if play is not None:
						cards[play] += 1
						if trick.leader == player:
							leads[play] += 1
					if trick.winner == player:
						taken += 1
						wins['tricks'] += 1
					elif trick.winner == partner:
						partnerTaken += 1
			# "Won" if player's nil was successful or the player didn't go nil and the team made their bid
			if bid in ('nil', 'blind'):
				cat = {'nil': 'nils', 'blind': 'blind_nils'}[bid]
				counts[cat] += 1
				if taken == 0:
					wins[cat] += 1
					wins['rounds'] += 1
			elif taken + partnerTaken >= bid + bidValue(partnerBid):
				wins['rounds'] += 1
			if partnerBid in ('nil', 'blind'):
				counts['nil_defenses'] += 1
				if partnerTaken == 0:
					wins['nil_defenses'] += 1

	print "<a name=\"counts\"/>"
	print "<h2><a href=\"#counts\">Counts</a></h2>"
	print "A round counts as a win if you bid nil and make it, or bid non-nil and don't go bust. A trick counts as a win only when you take it. Never let your partner win tricks, it hurts your stats.<br><br>"
	print "<table class=\"counts\">"
	print "<tr><th>&nbsp;</th><th>Played</th><th>Won</th></tr>"
	for cat, count in counts.iteritems():
		print "<tr>"
		print "<td>%s</td>" % ' '.join(word.title() for word in cat.split('_'))
		print "<td>%d</td>" % count
		print "<td class=\"progresscell\">%s</td>" % ProgressBar(wins[cat], count)
		print "</tr>"
	print "</table>"

	print "<a name=\"frequencies\"/>"
	print "<h2><a href=\"#frequencies\">Frequencies</a></h2>"
	print "<a name=\"bids\"/>"
	print "<h3><a href=\"#bids\">Bids</a></h3>"
	bids = {i: {'count': 0, 'made': 0} for i in range(14)}
	for game in games:
		partner = game.partners[player]
		for round in game.rounds:
			if not round.finished:
				continue
			bid = bidValue(round.bidsByPlayer[player])
			partnerBid = bidValue(round.bidsByPlayer[partner])
			taken = len(round.tricksByWinner[player])
			partnerTaken = len(round.tricksByWinner[partner])
			bids[bid]['count'] += 1
			# Going to count a bid as "made" if you made nil, you alone made your bid (even if going bust as a team), or the team made its collective bid
			if (taken == 0) if (bid == 0) else (taken >= bid or taken + partnerTaken >= bid + partnerBid):
				bids[bid]['made'] += 1
	BidSuccessChart('bid-success-chart', bids).emplace(handler)

	print "<a name=\"partners\"/>"
	print "<h3><a href=\"#partners\">Partners</a></h3>"
	partners = {}
	for game in games:
		partner = game.partners[player]
		if partner is None:
			continue
		if partner not in partners:
			partners[partner] = {'games': 0, 'wins': 0}
		partners[partner]['games'] += 1
		if player in (game.winner or []):
			partners[partner]['wins'] += 1
	print "<table class=\"partners\">"
	print "<tr><th>&nbsp;</th><th>Wins</th></tr>"
	for partner in sorted(partners):
		info = partners[partner]
		print "<tr>"
		print "<td><a href=\"/players/%s\"><img src=\"/players/%s/avatar\"></a></td>" % (partner, partner)
		print "<td class=\"progresscell\">%s</div>" % ProgressBar(info['wins'], info['games'], partner, "/players/%s" % partner)
		print "</tr>"
	print "</table>"
	PartnersChart('partners-chart', partners).emplace(handler)

	def printCardCounts(title, data):
		print "<a name=\"freq-%s\"/>" % title.lower()
		print "<h3><a href=\"freq-%s\">%s</a></h3>" % (title.lower(), title)
		for count in sorted(list(set(data.values())), reverse = True):
			print "<div class=\"freq-cards\">"
			print "<div class=\"count\">%d</div>" % count
			theseCards = [card for card, c in data.iteritems() if c == count]
			theseCards.sort(key = ordering.index)
			for card in theseCards:
				print "<img src=\"/card/%s\">" % card
			print "</div>"
	printCardCounts('Cards', cards)
	printCardCounts('Leads', leads)

@get('players/(?P<username>[^/]+)/avatar')
def playerAvatar(handler, username):
	width = height = 64
	pt = 44

	# The frontend uses the username '-' for empty seats; we special-case the text and colors of that
	if username == '-':
		text = '?'
		r = g = b = 0
	else:
		text = username[:2].capitalize()
		r, g, b = getPlayerColor(username)

	image = Image.new('RGB', (width, height), (r, g, b))
	draw = ImageDraw.Draw(image)
	font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'font.ttf'), pt)
	size = font.getsize(text)

	# I'm not sure why, but attempting to exactly center the text leaves it a little low
	# Offseting it by 10 seems to be around right, experimentally.
	# On second look, this is somehow machine-specific, and 8 is better on my VPS
	x, y = (width - size[0]) / 2, (height - size[1] - 8) / 2

	# Originally tried shadowing the text to make it visible, but don't really like how it looks
	# draw.text((x - 1, y - 1), text, font = font, fill = '#000')
	# draw.text((x + 1, y - 1), text, font = font, fill = '#000')
	# draw.text((x - 1, y + 1), text, font = font, fill = '#000')
	# draw.text((x + 1, y + 1), text, font = font, fill = '#000')

	# Instead choose whichever foreground color is more visible, white or black
	# There are probably still usernames that will be hard to read, but meh for now
	# http://stackoverflow.com/a/946734/309308
	brightness = r * .299 + g * .587 + b * .114
	fg = (0, 0, 0) if brightness > 160 else (255, 255, 255)
	draw.text((x, y), text, font = font, fill = fg)

	out = StringIO()
	image.save(out, 'png')
	print out.getvalue()
	handler.wrappers = None
	handler.contentType = 'image/png'
