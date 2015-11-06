class Game:
	def __init__(self, creator, goal, bags):
		self.creator = creator
		self.goal = goal
		self.bags = bags

		self.players = []
		self.rounds = []

	def out(self):
		print "Game created by %s, %d goal, %d bags" % (self.creator, self.goal, self.bags)
		print "  Players: %s" % ', '.join(self.players)
		for round in self.rounds:
			round.out()

class Round:
	def __init__(self):
		self.players = []
		self.bids = []
		self.tricks = []

	def out(self):
		print "  Round"
		print "    Bids: %s" % ', '.join("%s (%s)" % x for x in zip(self.players, self.bids))
		for trick in self.tricks:
			trick.out()

class Trick:
	def __init__(self, leader):
		self.leader = leader
		self.plays = []

	def out(self):
		print "    Trick (led by %s): %s" % (self.leader, ' '.join(self.plays))
