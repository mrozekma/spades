from collections import OrderedDict
import time

from utils import *

ordering = [rank + suit for suit in 'sdch' for rank in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']]

def bidValue(bid):
	return 0 if bid in ('nil', 'blind') else bid

def findWinner(cards):
	if len(filter(None, cards)) == 0:
		return None
	return sorted(filter(lambda card: card is not None and card[-1] in (cards[0][-1], 's'), cards), key = ordering.index)[0]

class Game:
	def __init__(self, logFilename, start, creator, goal, bagLimit):
		self.logFilename = logFilename
		self.start = start
		self.end = None
		self.creator = creator
		self.goal = goal
		self.bagLimit = bagLimit

		self.players = [None] * 4
		self.teamNames = {}
		self.rounds = []

	def __getstate__(self):
		return {k: getattr(self, k) for k in ('logFilename', 'start', 'end', 'creator', 'goal', 'bagLimit', 'players', 'teamNames', 'rounds')}

	def __setstate__(self, v):
		self.__dict__ = v
		for round in self.rounds:
			round.game = self

	def getPlayersStartingWith(self, first):
		idx = self.players.index(first)
		return (self.players + self.players)[idx:idx+4]

	@property
	def friendlyName(self):
		players = [player or '?' for player in self.players]
		return "%s vs. %s to %d" % (self.teamNames.get((players[0], players[2]), '?'), self.teamNames.get((players[1], players[3]), '?'), self.goal)

	@property
	def teams(self):
		return [(self.players[0], self.players[2]), (self.players[1], self.players[3])]

	@property
	def partners(self):
		return {self.players[i]: self.players[(i + 2) % 4] for i in range(4)}

	@property
	def playersByTeamName(self):
		return {v: k for k, v in self.teamNames.iteritems()}

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
		if len(self.rounds) == 0:
			return {team: 0 for team in self.teams}
		return self.rounds[-1].score

	@property
	def currentRound(self):
		if self.finished:
			return None
		if len(self.rounds) == 0:
			return None
		return self.rounds[-1]

	@property
	def currentTrick(self):
		if self.currentRound is None:
			return None
		for trick in self.currentRound.tricks[::-1]:
			if trick is not None:
				return trick
		return None

	# Used to update websocket clients
	@property
	def runState(self):
		rtn = {
			'game': self.logFilename,
			'friendly_name': self.friendlyName,
			'players': self.players,
		}
		if hasattr(self, 'gameCon') and hasattr(self.gameCon, 'err'): # This only happens if this is the current game and the EventThread has crashed
			rtn['err'] = self.gameCon.err
		if self.finished: # The only time this propery should be accessed by finished games is if they were already open in a client; otherwise the client should have been redirected on page load
			rtn['description'] = ['Game over']
		elif self.currentRound is None:
			rtn['description'] = ['Seating']
			# The players list is empty at this point, since teams haven't been assigned
			# Instead we set the pregame list, and adjust the friendly name accordingly
			del rtn['players']
			rtn['pregame_players'] = self.gameCon.players
			num = len(rtn['pregame_players'])
			rtn['friendly_name'] = (("Game to %d" % self.goal) if num == 0 else
			                        ("%s and 3 more to %d" % (rtn['pregame_players'][0], self.goal)) if num == 1 else
			                        ("%s, and %d more to %d" % (', '.join(rtn['pregame_players']), 4 - num, self.goal)) if num < 4 else
			                        ("%s, and %s to %d" % (', '.join(rtn['pregame_players'][:-1]), rtn['pregame_players'][-1], self.goal)))
		else:
			rtn['description'] = ["Round %d" % len(self.rounds)]
			# Round data is in round player order, but the client needs it in game player order
			def order(data):
				data = {player: v for player, v in zip(self.currentRound.players, data)}
				return [data.get(player, None) for player in self.players]
			if sum(1 if player is None else 0 for player in rtn['players']) == 1: # Process of elimination
				(lastPlayer,) = set(self.gameCon.players) - set(self.players)
				rtn['players'] = [player or lastPlayer for player in rtn['players']]
			tricksByWinner = self.currentRound.tricksByWinner
			rtn['taken'] = [len(tricksByWinner.get(player, [])) for player in self.players]
			rtn['bids'] = order(self.currentRound.bids)
			if self.currentTrick is None:
				rtn['description'].append('Bidding')
				if hasattr(self.gameCon, 'currentPlayer'):
					rtn['turn'] = self.gameCon.currentPlayer
					if hasattr(self.gameCon, 'thisBidStart'):
						rtn['turn_started'] = dtToJSTime(self.gameCon.thisBidStart)
				rtn['deck'] = ordering
			else:
				rtn['description'].append("Trick %d" % (self.currentRound.tricks.index(self.currentTrick) + 1))
				rtn['deck'] = self.currentRound.cardsLeft
				# Again for trick order
				def order(data):
					data = {player: v for player, v in zip(self.getPlayersStartingWith(self.currentTrick.leader), data)}
					return [data[player] for player in self.players]
				rtn['leader'] = self.currentTrick.leader
				rtn['plays'] = order(self.currentTrick.plays)
				if None in self.currentTrick.plays:
					rtn['turn'] = self.getPlayersStartingWith(self.currentTrick.leader)[self.currentTrick.plays.index(None)]
					if hasattr(self.gameCon, 'thisPlayStart'):
						rtn['turn_started'] = dtToJSTime(self.gameCon.thisPlayStart)
				if self.currentTrick.plays[0] is not None:
					rtn['winning'] = self.currentTrick.playersByPlay[findWinner(self.currentTrick.plays)]
				rtn['past_tricks'] = []
				for trick in self.currentRound.tricks:
					if trick == self.currentTrick:
						break
					rtn['past_tricks'].append({
						# Continue to keep Javascript play arrays in game order, despite how Trick stores them
						'plays': [trick.playsByPlayer[player] for player in self.players],
						'leader': trick.leader,
						'winner': trick.winner,
						'duration': dtToJSTime(trick.end) - dtToJSTime(trick.start),
					})
		return rtn

	def out(self):
		print "Game created by %s, %d goal, %d bags" % (self.creator, self.goal, self.bagLimit)
		print "  Players: %s" % ', '.join(map(str, self.players))
		for round in self.rounds:
			round.out()

class Round:
	def __init__(self, start):
		self.start = start
		self.end = None
		self.players = [None] * 4
		self.bids = [None] * 4 # self.bids[i] made by self.players[i]
		self.tricks = [None] * 13

	def __getstate__(self):
		return {k: getattr(self, k) for k in ('start', 'end', 'players', 'bids', 'tricks')}

	def __setstate__(self, v):
		self.__dict__ = v
		for trick in self.tricks:
			trick.round = self

	@property
	def finished(self):
		return self.tricks[-1] is not None and self.tricks[-1].plays[-1] is not None

	@property
	def bidsByPlayer(self):
		return dict(zip(self.players, self.bids))

	@property
	def deal(self):
		return {player: sorted(filter(None, (trick.playsByPlayer[player] for trick in self.tricks if trick is not None)), key = ordering.index) for player in self.players}

	@property
	def tricksByWinner(self):
		rtn = {player: [] for player in self.players}
		for trick in self.tricks:
			if trick is not None and trick.winner is not None:
				rtn[trick.winner].append(trick)
		return rtn

	@property
	def cardsPlayed(self):
		return sum((trick.plays for trick in self.tricks if trick is not None), [])

	@property
	def cardsLeft(self):
		played = self.cardsPlayed
		return filter(lambda card: card not in played, ordering)

	# scoreChange and bags copy spades.awk's incorrect handling of nil (nil tricks aren't bags if they cover a partner's missing tricks)

	# This *doesn't* include negative points for bagging out, since it requires the round-to-round bag total
	@property
	def scoreChange(self):
		# We don't compute the score for incomplete rounds
		if not self.finished:
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
		if not self.finished:
			return {team: 0 for team in self.game.teams}

		bids = self.bidsByPlayer
		taken = {player: len(tricks) for player, tricks in self.tricksByWinner.iteritems()}
		return {team: max(0, sum(taken[player] for player in team) - sum(bidValue(bids[player]) for player in team)) for team in self.game.teams}

	# This is kind of a strange property, but it's needed by several others
	@property
	def previousRounds(self):
		for round in self.game.rounds:
			if round == self:
				return
			yield round

	# Score in the game at the end of this round (or end of the last round, if this round is incomplete)
	@property
	def score(self):
		scores = sumByKey((round.scoreChange for round in self.previousRounds), self.scoreChange)
		bags = sumByKey((round.bags for round in self.previousRounds), self.bags)
		return {team: scores.get(team, 0) - 10 * self.game.bagLimit * int(bags.get(team, 0) / self.game.bagLimit) for team in self.game.teams}

	def out(self):
		print "  Round"
		print "    Bids: %s" % ', '.join("%s (%s)" % x for x in zip(self.players, self.bids))
		for trick in self.tricks:
			if trick is not None:
				trick.out()

class Trick:
	def __init__(self, start, leader):
		self.start = start
		self.end = None
		self.leader = leader
		self.plays = [None] * 4 # Starting with self.leader's play

	def __getstate__(self):
		return {k: getattr(self, k) for k in ('start', 'end', 'leader', 'plays')}

	def __setstate__(self, v):
		self.__dict__ = v

	@property
	def playsByPlayer(self):
		return OrderedDict(zip(self.round.game.getPlayersStartingWith(self.leader), self.plays))

	@property
	def playersByPlay(self):
		return OrderedDict(zip(self.plays, self.round.game.getPlayersStartingWith(self.leader)))

	@property
	def finished(self):
		return self.plays[-1] is not None

	@property
	def win(self):
		return findWinner(self.plays) if self.finished else None

	@property
	def winner(self):
		return self.playersByPlay[self.win] if self.finished else None

	def out(self):
		print "    Trick (led by %s): %s" % (self.leader, ' '.join(map(str, self.plays)))
