from Chart import Chart, raw
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

		self.series = [{'name': game.teamNames[team], 'data': [score[team] for score in scores]} for team in teams]
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
