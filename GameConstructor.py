from Data import *

class GameConstructor:
	def __init__(self, logFilename, onCommit = lambda game: None):
		self.state = 'idle'
		self.logFilename = logFilename
		self.logOffset = 0
		self.onCommit = onCommit

	def mismatch(self, event):
		if hasattr(self, 'game'):
			self.game.out()
		raise ValueError("Unexpected event at this point (state: %s): %s" % (self.state, event))

	def commitGame(self):
		self.onCommit(self.game)
		del self.game

	# Replace the first None in 'l' with 'v'
	def emplace(self, l, v):
		l[l.index(None)] = v

	def filled(self, l):
		return l[-1] is not None

	def pump(self, event):
		print event
		if event['off'] < self.logOffset:
			raise RuntimeError("Received event at offset %d, but already at offset %d" % (event['off'], self.logOffset))

		if event['type'] == 'teamname':
			self.game.teamNames[event['who']] = event['name'] if event['name'] is not None else '/'.join(event['who'])
			return

		if self.state == 'idle':
			if event['type'] == 'game_start':
				self.state = 'sitting'
				self.game = Game(self.logFilename, event['ts'], event['who'], event['goal'], event['bags'])
				self.players = []

				# Ugh. The only thing that should really be using this is Game.runState:
				self.game.gameCon = self

				return
			self.mismatch(event)

		if event['type'] == 'game_abort':
			self.state = 'idle'
			self.game.end = event['ts']
			if hasattr(self, 'players'):
				del self.players
			self.commitGame()
			return

		if self.state == 'sitting':
			if event['type'] == 'sit':
				if len(self.players) == 4:
					raise RuntimeError("More than four players sitting (%s, %s)" % (', '.join(self.players), event['who']))
				self.players.append(event['who'])
				return
			if event['type'] == 'deal':
				self.state = 'bidding'
				return
			self.mismatch(event)

		if self.state == 'bidding':
			if event['type'] == 'bidding':
				self.currentPlayer = event['who']
				self.thisBidStart = event['ts'] # This is used by Game.runState
				if hasattr(self, 'players'):
					if not event['who'] in self.players:
						raise RuntimeError("Bidding player %s not seated" % event['who'])
					self.emplace(self.game.players, event['who'])
					if self.filled(self.game.players):
						del self.players
						for team in self.game.teams:
							if team not in self.game.teamNames:
								self.game.teamNames[team] = '/'.join(team)
				if not hasattr(self, 'currentRound'):
					self.currentRound = Round(event['ts'])
					self.currentRound.game = self.game
					self.game.rounds.append(self.currentRound)
				return
			if event['type'] == 'nil_signal':
				# For old logs, this event is necessary to distinguish nil/blind bids from 0 bids for the final bid of the round
				# In new logs a separate 'bid' event is generated, but this one happens first. The 'bid' event handles this case
				self.emplace(self.currentRound.players, self.currentPlayer)
				self.emplace(self.currentRound.bids, event['bid'])
				del self.currentPlayer, self.thisBidStart
				if self.currentRound.bids[-1] is not None:
					self.state = 'playing'
				return
			if event['type'] == 'bid':
				if event['bid'] in ('nil', 'blind'): # Recorded by 'nil_signal'
					return
				self.emplace(self.currentRound.players, self.currentPlayer)
				self.emplace(self.currentRound.bids, event['bid'])
				del self.currentPlayer, self.thisBidStart
				if self.currentRound.bids[-1] is not None:
					self.state = 'playing'
				return
			if event['type'] == 'bid_recap':
				self.emplace(self.currentRound.players, self.currentPlayer)
				self.emplace(self.currentRound.bids, event['bids'][self.currentPlayer])
				del self.currentPlayer, self.thisBidStart
				self.state = 'playing'
				return

			# In older logs, there was no event for the last bid. If we see a 'playing' event while looking for the last bid, we record the last player and switch to
			# the playing state, leaving the last bid unset. It will be filled in by the round_summary event at the end of the round
			if event['type'] == 'playing' and self.currentRound.bids[-1] is None and self.currentRound.bids[-2] is not None:
				self.emplace(self.currentRound.players, self.currentPlayer)
				del self.currentPlayer, self.thisBidStart
				self.state = 'playing'
				# Re-pump this event in the playing state
				return self.pump(event)

			self.mismatch(event)

		if self.state == 'playing':
			# For newer logs, if the last player goes nil/blind, the 'nil_signal' event pushes us into the playing state, but then a 'bid' event still follows
			if event['type'] == 'bid' and event['bid'] in ('nil', 'blind'):
				return

			if event['type'] == 'playing':
				self.currentPlayer = event['who']
				if not hasattr(self, 'currentTrick'):
					self.currentTrick = Trick(event['ts'], self.currentPlayer)
					self.currentTrick.round = self.currentRound
					self.emplace(self.currentRound.tricks, self.currentTrick)
				self.thisPlayStart = event['ts'] # This is used by Game.runState
				return
			if event['type'] == 'play':
				self.emplace(self.currentTrick.plays, event['play'])
				del self.thisPlayStart
				if self.filled(self.currentTrick.plays):
					self.currentTrick.end = event['ts']
					del self.currentTrick
					# We wait for round_end or game_end instead of going straight to bidding
					# if self.filled(self.currentRound.tricks):
						# del self.currentRound
						# self.state = 'bidding'
				return
			if event['type'] == 'round_summary':
				self.currentRound.end = event['ts']
				who = self.game.playersByTeamName[event['team']]
				# Using the power of subtraction, we can figure out what the last bid was this round in old logs
				if self.currentRound.bids[-1] is None and self.currentRound.players[-1] in who:
					missingPlayer = self.currentRound.players[-1]
					(partner,) = set(who) - {missingPlayer}
					self.emplace(self.currentRound.bids, bidValue(event['bid']) - bidValue(self.currentRound.bids[self.currentRound.players.index(partner)]))
				return
			if event['type'] == 'game_end':
				self.game.end = event['ts']
				self.commitGame()
				self.state = 'idle'
				return
			if event['type'] == 'deal':
				del self.currentRound
				self.state = 'bidding'
				return
			self.mismatch(event)

		raise RuntimeError("Invalid state: %s" % self.state)
