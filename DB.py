import os
import shelve

class PendingChange:
	def __init__(self, shelf, key):
		self.shelf = shelf
		self.key = key

	def __enter__(self):
		self.value = self.shelf[self.key]
		return self.value

	def __exit__(self, type, value, tb):
		self.shelf[self.key] = self.value

class LoudMap:
	def __init__(self, db, key):
		self.db = db
		self.key = key
		self.m = db.shelf[key]
		for fn in ('clear', 'pop', 'popitem', 'update', '__setitem__', '__delitem__'):
			def _(fn):
				def override(*args, **kw):
					try:
						return getattr(self.m, fn)(*args, **kw)
					finally:
						self.db[self.key] = self.m
				return override
			setattr(self, fn, _(fn))

	def __getattr__(self, k):
		return getattr(self.m, k)

class DB:
	def __init__(self, dbFilename):
		self.shelf = shelve.open(dbFilename)

	def __del__(self):
		if hasattr(self, 'shelf'):
			self.shelf.close()

	def __contains__(self, k):
		return k in self.shelf

	def __getitem__(self, k):
		rtn = self.shelf[k]
		if isinstance(rtn, dict):
			return LoudMap(self, k)
		return rtn

	def __setitem__(self, k, v):
		if isinstance(v, LoudMap):
			v = v.m
		self.shelf[k] = v

	def change(self, key):
		return PendingChange(self, key)

db = DB(os.path.join(os.path.dirname(__file__), 'db'))

for k in ('games',):
	if k not in db:
		db[k] = {}

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
	rtn = db['games'].m
	if activeGame is not None:
		rtn[activeGame.logFilename] = activeGame
	return rtn
