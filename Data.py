from collections import OrderedDict

ordering = [rank + suit for suit in 'sdch' for rank in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']]

def bidValue(bid):
	return 0 if bid in ('nil', 'blind') else bid

def findWinner(cards):
	if not cards:
		raise ValueError("No cards passed")
	return sorted(filter(lambda card: card[-1] in (cards[0][-1], 's'), cards), key = ordering.index)[0]

class Game:
	def __init__(self, logFilename, start, creator, goal, bagLimit):
		self.logFilename = logFilename
		self.start = start
		self.end = None
		self.creator = creator
		self.goal = goal
		self.bagLimit = bagLimit

		self.players = []
		self.rounds = []

	def __getstate__(self):
		return {k: getattr(self, k) for k in ('logFilename', 'start', 'end', 'creator', 'goal', 'bagLimit', 'players', 'rounds')}

	def __setstate__(self, v):
		self.__dict__ = v
		for round in self.rounds:
			round.game = self

	def getPlayersStartingWith(self, first):
		idx = self.players.index(first)
		return (self.players + self.players)[idx:idx+4]

	@property
	def teams(self):
		return [(self.players[0], self.players[2]), (self.players[1], self.players[3])]

	@property
	def winner(self):
		scores = [{'team': team, 'score': score} for team, score in self.score.iteritems()]
		if scores[0]['score'] >= self.goal or scores[1]['score'] >= self.goal:
			if scores[0]['score'] > scores[1]['score']:
				return scores[0]['team']
			elif scores[1]['score'] > scores[0]['score']:
				return scores[1]['team']
			# Both over the goal but tied; game goes into overtime
		return None

	@property
	def finished(self):
		return self.end is not None

	@property
	def score(self):
		scores = {team: 0 for team in self.teams}
		bags = {team: 0 for team in self.teams}
		for round in self.rounds:
			for team, score in round.score.iteritems():
				scores[team] += score
			for team, bag in round.bags.iteritems():
				bags[team] += bag
		return {team: scores[team] - 10 * self.bagLimit * int(bags[team] / self.bagLimit) for team in self.teams}

	def out(self):
		print "Game created by %s, %d goal, %d bags" % (self.creator, self.goal, self.bagLimit)
		print "  Players: %s" % ', '.join(self.players)
		for round in self.rounds:
			round.out()

class Round:
	def __init__(self):
		self.players = []
		self.bids = []
		self.tricks = []

	def __getstate__(self):
		return {k: getattr(self, k) for k in ('players', 'bids', 'tricks')}

	def __setstate__(self, v):
		self.__dict__ = v
		for trick in self.tricks:
			trick.round = self

	@property
	def finished(self):
		return len(self.tricks) == 13

	@property
	def bidsByPlayer(self):
		return dict(zip(self.players, self.bids))

	@property
	def tricksByWinner(self):
		rtn = {player: [] for player in self.players}
		for trick in self.tricks:
			rtn[trick.winner].append(trick)
		return rtn

	@property
	def cardsPlayed(self):
		return sum((trick.plays for trick in self.tricks), [])

	@property
	def cardsLeft(self):
		played = self.cardsPlayed
		return filter(lambda card: card not in played, ordering)

	# score and bags copy spades.awk's incorrect handling of nil (nil tricks aren't bags if they cover a partner's missing tricks)

	# This *doesn't* include negative points for bagging out, since it requires the round-to-round bag total
	@property
	def score(self):
		# We don't compute the score for incomplete rounds
		if len(self.tricks) < 13:
			return {team: 0 for team in self.game.teams}

		# If bid made, score 10 points per bid trick and 1 point per bag
		# If set, lose 10 points per bid trick
		# If bagged out, lose 10 * bagLimit points (not computed here)
		# If nil, gain/lose 10 * bagLimit points
		# If blind nil, gain/lose 20 * bagLimit points
		bids = self.bidsByPlayer
		taken = {player: len(tricks) for player, tricks in self.tricksByWinner.iteritems()}
		def teamScore((player1, player2)):
			score = 0
			teamBids = bidValue(bids[player1]) + bidValue(bids[player2])
			teamTaken = taken[player1] + taken[player2]
			if teamTaken >= teamBids:
				score += 10 * teamBids + (teamTaken - teamBids)
			else:
				score -= 10 * teamBids
			for player in (player1, player2):
				if bids[player] in ('nil', 'blind'):
					score += 10 * self.game.bagLimit * (2 if bids[player] == 'blind' else 1) * (1 if taken[player] == 0 else -1)
			return score
		return {team: teamScore(team) for team in self.game.teams}

	@property
	def bags(self):
		# We don't compute the bags for incomplete rounds
		if len(self.tricks) < 13:
			return {team: 0 for team in self.game.teams}

		bids = self.bidsByPlayer
		taken = {player: len(tricks) for player, tricks in self.tricksByWinner.iteritems()}
		return {team: max(0, sum(taken[player] for player in team) - sum(bidValue(bids[player]) for player in team)) for team in self.game.teams}

	def out(self):
		print "  Round"
		print "    Bids: %s" % ', '.join("%s (%s)" % x for x in zip(self.players, self.bids))
		for trick in self.tricks:
			trick.out()

class Trick:
	def __init__(self, leader):
		self.leader = leader
		self.plays = []

	@property
	def playsByPlayer(self):
		return OrderedDict(zip(self.round.game.getPlayersStartingWith(self.leader), self.plays))

	@property
	def playersByPlay(self):
		return OrderedDict(zip(self.plays, self.round.game.getPlayersStartingWith(self.leader)))

	@property
	def win(self):
		return findWinner(self.plays)

	@property
	def winner(self):
		return self.playersByPlay[self.win]

	def out(self):
		print "    Trick (led by %s): %s" % (self.leader, ' '.join(self.plays))
