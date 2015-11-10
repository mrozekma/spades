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
		self.game = None

	def pump(self, event):
		print event
		if event['off'] < self.logOffset:
			raise RuntimeError("Received event at offset %d, but already at offset %d" % (event['off'], self.logOffset))
		if self.state == 'idle':
			if event['type'] == 'game_start':
				self.state = 'sitting'
				self.game = Game(event['who'], event['goal'], event['bags'])
				self.players = []
				return
			self.mismatch(event)

		if event['type'] == 'game_abort':
			self.state = 'idle'
			if hasattr(self, 'players'):
				self.game.players += self.players
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
				if hasattr(self, 'players'):
					if not event['who'] in self.players:
						raise RuntimeError("Bidding player %s not seated" % event['who'])
					self.game.players.append(event['who'])
					if len(self.game.players) == len(self.players):
						del self.players
				if not hasattr(self, 'currentRound'):
					self.currentRound = Round()
					self.currentRound.game = self.game
					self.game.rounds.append(self.currentRound)
				# Currently we have no immediate event for the last bid, so we switch states here. We figure out the last bidder by process of elimination, and leave the last bid unset
				if len(self.currentRound.bids) == 3:
					(lastPlayer,) = set(self.game.players) - set(self.currentRound.players)
					self.currentRound.players.append(lastPlayer)
					self.state = 'playing'
				return
			if event['type'] == 'bid':
				self.currentRound.players.append(self.currentPlayer)
				self.currentRound.bids.append(event['bid'])
				del self.currentPlayer
				return
			if event['type'] == 'nil_signal':
				# A nil_signal in the bidding state must not be the last player (see nil_signal in the playing state)
				# We get non-final-player nil bids from bid events, so we can ignore this
				return
			self.mismatch(event)

		if self.state == 'playing':
			if event['type'] == 'playing':
				self.currentPlayer = event['who']
				if not hasattr(self, 'currentTrick'):
					self.currentTrick = Trick(self.currentPlayer)
					self.currentTrick.round = self.currentRound
					self.currentRound.tricks.append(self.currentTrick)
				return
			if event['type'] == 'play':
				self.currentTrick.plays.append(event['play'])
				if len(self.currentTrick.plays) == len(self.game.players):
					del self.currentTrick
					# We wait for round_end or game_end instead of going straight to bidding
					# if len(self.currentRound.tricks) == 13:
						# del self.currentRound
						# self.state = 'bidding'
				return
			if event['type'] == 'round_summary':
				# Using the power of subtraction, we can figure out what the last bid was this round
				if len(self.currentRound.bids) == len(self.currentRound.players) - 1 and self.currentRound.players[-1] in event['who']:
					missingPlayer = self.currentRound.players[-1]
					(partner,) = set(event['who']) - {missingPlayer}
					self.currentRound.bids.append(bidValue(event['bid']) - bidValue(self.currentRound.bids[self.currentRound.players.index(partner)]))
				return
			if event['type'] == 'nil_signal':
				# We need this only to distinguish the last bid, since round_summary would just tell us it's zero
				# If we're getting it in the playing state, it must be the last bid, but we double-check
				if len(self.currentRound.bids) != len(self.currentRound.players) - 1:
					raise RuntimeError("Got non-final nil_signal in playing state")
				self.currentRound.bids.append(event['bid'])
				return
			if event['type'] == 'game_end':
				self.commitGame()
				del self.game
				self.state = 'idle'
				return
			if event['type'] == 'deal':
				del self.currentRound
				self.state = 'bidding'
				return


			self.mismatch(event)
