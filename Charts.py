from Chart import Chart, raw
from Data import bidValue
from utils import *

from math import ceil

class ScoreChart(Chart):
	def __init__(self, placeholder, game):
		Chart.__init__(self, placeholder)

		teams = game.teams
		# This is O(n log n) internally out of laziness; it could be O(n) if we calculated the round scores manually with round.scoreChange instead of round.score
		# We skip the active round as it has no score change (it will show as the same score as the previous round)
		scores = [{team: 0 for team in teams}] + [round.score for round in game.rounds if round.finished]

		self.chart.type = 'line'
		self.chart.marginTop = 30
		self.title.text = ''
		self.tooltip.shared = True
		self.plotOptions.line.dataLabels.enabled = True
		self.xAxis.categories = [''] + ["Round %d" % (i + 1) for i in range(len(game.rounds))]
		self.yAxis.title.enabled = False
		self.yAxis.plotLines = [{
			'value': game.goal,
			'color': '#0a0',
			'width': 2,
		}]

		# Largest score seen or goal score, rounded up to next multiple of 100
		self.yAxis.max = int(ceil(max(max(max(*score.values()) for score in scores), game.goal) / 100.)) * 100

		# Show a line every 100 points, unless the score is gigantic; then just let highcharts choose automatically
		if game.goal <= 1000:
			self.yAxis.tickInterval = 100

		flags = {team: [] for team in teams}
		flagSeries = [{
			'type': 'flags',
			'data': data,
			'color': '#4572a7',
			'shape': 'flag',
			'onSeries': '/'.join(team),
			'showInLegend': False,
			'shape': 'squarepin',
			'y': -50,
		} for team, data in flags.iteritems()]

		for team in teams:
			bags = 0
			for i, round in enumerate(game.rounds):
				if not round.finished:
					continue
				toShow = []
				bids = [round.bidsByPlayer[player] for player in team]
				taken = [len(round.tricksByWinner[player]) for player in team]
				for player, bid, took in zip(team, bids, taken):
					if bid in ('nil', 'blind'):
						toShow.append(('N', "%s %s %s" % (player, 'made' if took == 0 else 'failed', 'nil' if bid == 'nil' else 'blind nil')))
				thisBags = sum(taken) - sum(map(bidValue, bids))
				if thisBags > 0:
					bags += thisBags
					if bags >= game.bagLimit:
						bags %= game.bagLimit
						toShow.append(('B', 'Bagged out'))
				if toShow:
					flags[team].append({'x': i + 1, 'title': ','.join(title for title, text in toShow), 'text': '<br>'.join(text for title, text in toShow)})

		self.series = [{'id': '/'.join(team), 'name': game.teamNames[team], 'data': [score[team] for score in scores]} for team in teams] + flagSeries
		self.series[0]['color'] = '#a00';
		self.series[1]['color'] = '#00a';

class HandsHeatmap(Chart):
	def __init__(self, placeholder, round):
		Chart.__init__(self, placeholder)

		self.chart.type = 'heatmap'
		self.title.text = ''
		self.legend.enabled = False
		self.xAxis.categories = round.game.players
		self.yAxis.categories = ['Spades', 'Diamonds', 'Clubs', 'Hearts']
		self.yAxis.title = ''
		with self.colorAxis as axis:
			axis.min = 0
			axis.max = 13. / 2 # I don't know why, but halving the max makes the axis come out right
			# We assume most people will have <= 5 cards in a suit, so we bunch the gradient around the lower numbers. #ff3f3f is 75% of the way to #ff0000 (HSV 0/.75/1)
			axis.stops = [[0, '#ffffff'], [5./13, '#ff3f3f'], [1, '#ff0000']]

		# player: ['As', '10c', ...]
		deal = round.deal
		data = [[xI, yI, sum(card[-1] == y[0].lower() for card in deal.get(x, []))] for xI, x in enumerate(self.xAxis.categories.get()) for yI, y in enumerate(self.yAxis.categories.get())]
		self.series = [{'data': data}]

	def placeholder(self):
		print "<div id=\"%s\" class=\"highchart hands-heatmap\"></div>" % self._id

class TricksTakenChart(Chart):
	def __init__(self, placeholder, round):
		Chart.__init__(self, placeholder)

		self.chart.type = 'column'
		self.title.text = ''
		self.xAxis.categories = ["Trick %d" % (i + 1) for i in range(13)]
		# self.yAxis = [
			# {'title': {'text': 'Tricks'}, 'min': 0, 'max': 13, 'tickInterval': 1},
			# {'title': {'text': 'Bids'}, 'opposite': True, 'min': 0, 'max': 13},
		# ]
		with self.yAxis as axis:
			axis.title.text = 'Tricks'
			axis.min = 0
			axis.max = 13
			axis.tickInterval = 1

			axis.plotLines = plotLines = []
			clrs = ['red', 'green']
			import sys
			for team in round.game.teams:
				plotLines.append({
					'label': {'text': annotatedTeamName(round.game, team)},
					'width': 2,
					'color': clrs.pop(0),
					'value': sum(bidValue(round.bidsByPlayer.get(player, 0)) for player in team),
				})
			if plotLines[0]['value'] == plotLines[1]['value']:
				plotLines[0]['label']['text'] = 'Both teams'
				plotLines.pop(1)
		self.tooltip.enabled = False
		self.plotOptions.column.stacking = 'normal'

		# Not sure if there's a nice use for flags
		# Was planning to mark when players made their bid, but it doesn't look good and the team bids are obvious from the plotlines
		# flagSeries = {
			# 'type': 'flags',
			# 'data': [],
			# 'color': '#4572a7',
			# 'shape': 'flag',
			# 'onSeries': '',
			# 'showInLegend': False,
			# 'shape': 'squarepin',
		# }

		winners = [trick.winner if trick else None for trick in round.tricks]
		taken = {player: [0] for player in round.game.players}
		for winner in winners:
			for player, l in taken.iteritems():
				l.append(l[-1] + (1 if player == winner else 0))
		for l in taken.values():
			l.pop(0)
		self.series = [{
			'name': player,
			'stack': "Team %d" % (i%2 + 1),
			'color': "#%02x%02x%02x" % getPlayerColor(player),
			'data': taken[player],
		} for i, player in enumerate(round.game.players)]

	def placeholder(self):
		print "<div id=\"%s\" class=\"highchart tricks-taken\"></div>" % self._id

class PartnersChart(Chart):
	def __init__(self, placeholder, data):
		Chart.__init__(self, placeholder)
		self.chart.type = 'pie'
		self.title.text = ''
		self.tooltip.enabled = False

		partnerData, resultData = [], []
		self.series = [
			{'name': 'Partners', 'data': partnerData, 'size': '60%', 'dataLabels': {'distance': 50}},
			{'name': 'Results', 'data': resultData, 'size': '80%', 'innerSize': '60%', 'dataLabels': {'enabled': False}},
		]
		for partner in sorted(data):
			info = data[partner]
			clr = "#%02x%02x%02x" % getPlayerColor(partner)
			partnerData.append({
				'name': partner,
				'y': info['games'],
				'color': clr,
			})
			resultData.append({
				'name': 'Wins',
				'y': info['wins'],
				'color': clr,
			})
			resultData.append({
				'name': 'Losses',
				'y': info['games'] - info['wins'],
				'color': clr,
			})

class BidSuccessChart(Chart):
	def __init__(self, placeholder, data):
		Chart.__init__(self, placeholder)
		self.chart.type = 'column'
		self.title.text = ''
		self.tooltip.shared = True
		self.tooltip.formatter = raw("function() {return 'Made <b>' + this.points[1].y + '</b>/<b>' + this.points[0].y + '</b> when bidding <b>' + this.x + '</b>';}")
		self.plotOptions.column.grouping = False
		self.plotOptions.column.borderWidth = 0

		with self.xAxis as axis:
			axis.title.text = 'Bid'
			axis.min = 0
			axis.max = 13
			axis.tickInterval = 1
			axis.categories = ['Nil'] + range(1, 14)

		with self.yAxis as axis:
			axis.title.text = 'Times'
			axis.min = 0
			axis.tickInterval = 1

		bid, made = [], []
		self.series = [
			{'name': 'Bid', 'pointPadding': .3, 'data': bid},
			{'name': 'Made', 'pointPadding': .4, 'data': made},
		]

		for i in range(14):
			bid.append(data[i]['count'])
			made.append(data[i]['made'])
