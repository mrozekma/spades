from Chart import Chart

from math import ceil

class ScoreChart(Chart):
	def __init__(self, placeholder, game):
		Chart.__init__(self, placeholder)

		teams = game.teams
		# This is O(n log n) internally out of laziness; it could be O(n) if we calculated the round scores manually with round.scoreChange instead of round.score
		# We skip the active round as it has no score change (it will show as the same score as the previous round)
		scores = [{team: 0 for team in teams}] + [round.score for round in game.rounds if round.finished]

		self.chart.type = 'line'
		self.title.text = 'Score'
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

		self.series = [{'name': '/'.join(team), 'data': [score[team] for score in scores]} for team in teams]
		self.series[0]['color'] = '#a00';
		self.series[1]['color'] = '#00a';
