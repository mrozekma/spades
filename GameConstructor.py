from Data import *

class GameConstructor:
	def __init__(self):
		self.state = 'idle'

	def mismatch(self, event):
		raise ValueError("Unexpected event at this point (state: %s): %s" % (self.state, event))

	def commitGame(self):
		#TODO Write self.game to database
		self.game.out()
		del self.game

	def pump(self, event):
		print event

		if self.state == 'idle':
			if event['type'] == 'game_start':
				self.state = 'sitting'
				self.game = Game(event['who'], event['goal'], event['bags'])
				self.players = set()
				return
			self.mismatch(event)

		if event['type'] == 'game_abort':
			self.state = 'idle'
			self.commitGame()
			return

		if self.state == 'sitting':
			if event['type'] == 'sit':
				self.players.add(event['who'])
				if len(self.players) == 4:
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
					self.game.rounds.append(self.currentRound)
				# Currently we have no event for the last bid, so we switch states here
				if len(self.currentRound.bids) == 3:
					self.state = 'playing'
				return
			if event['type'] == 'bid':
				self.currentRound.players.append(self.currentPlayer)
				self.currentRound.bids.append(event['bid'])
				del self.currentPlayer
				return
			if event['type'] == 'game_end':
				self.commitGame()
				return
			self.mismatch(event)

		if self.state == 'playing':
			if event['type'] == 'playing':
				self.currentPlayer = event['who']
				if not hasattr(self, 'currentTrick'):
					self.currentTrick = Trick(self.currentPlayer)
					self.currentRound.tricks.append(self.currentTrick)
				return
			if event['type'] == 'play':
				self.currentTrick.plays.append(event['play'])
				if len(self.currentTrick.plays) == len(self.game.players):
					del self.currentTrick
					if len(self.currentRound.tricks) == 13:
						del self.currentRound
						self.state = 'bidding' # Maybe. Or the game is over
				return

			self.mismatch(event)
