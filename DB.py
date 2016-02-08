import os
from stasis.DiskMap import DiskMap

class LoudMap:
	def __init__(self, bs, key, m):
		self.bs = bs
		self.key = key
		self.m = m

	def __setitem__(self, key, value):
		self.m[key] = value
		self.bs[self.key][key] = value

	# There's no real reason these can't be supported, but I don't use them
	def clear(self, *args, **kw): self.unimplemented()
	def pop(self, *args, **kw): self.unimplemented()
	def popitem(self, *args, **kw): self.unimplemented()
	def update(self, *args, **kw): self.unimplemented()
	def unimplemented(self):
		raise RuntimeError("Unimplemented LoudMap method")

	# Anything not implemented here, pass-through to self.m
	def __getattr__(self, k):
		return getattr(self.m, k)

class DB:
	def __init__(self, dbFilename):
		self.bs = DiskMap(dbFilename, create = True, cache = True)

	def __contains__(self, k):
		return k in self.bs

	def __getitem__(self, k):
		rtn = self.bs[k]
		if isinstance(rtn, dict):
			return LoudMap(self.bs, k, rtn)
		return rtn

db = DB(os.path.join(os.path.dirname(__file__), 'db'))

# We store this in the DB module because it's where other games are stored
# It's set/unset by the EventThread, but not actually serialized
activeGame = None
def getActiveGame():
	return activeGame
def setActiveGame(newActiveGame):
	global activeGame
	activeGame = newActiveGame

def getGames():
	# Get the raw map (not a LoudMap), and append the active game if there is one
	rtn = db['games'].all()
	if activeGame is not None:
		rtn[activeGame.logFilename] = activeGame
	return rtn
