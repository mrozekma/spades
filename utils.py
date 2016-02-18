import time

from rorn.utils import *

def ensureIter(l):
	return l if isinstance(l, list) or isinstance(l, tuple) else [l]

def dtToJSTime(dt):
	return int(time.mktime(dt.timetuple()) * 1000)

def zeroes(keys):
	return {k: 0 for k in keys}

def sumByKey(maps, extraMap = {}):
	rtn = extraMap.copy()
	for m in maps:
		for k in m:
			rtn[k] = rtn.get(k, 0) + m[k]
	return rtn

def getPlayerColor(username):
	bgHex = hex(hash(username))[2:][-6:].zfill(6) # Strip the 0x prefix and take the last 6 characters (if there aren't enough, left-pad with 0s)
	return int(bgHex[0:2], 16), int(bgHex[2:4], 16), int(bgHex[4:6], 16)

def annotatedTeamName(game, team):
	name = game.teamNames[team]
	players = '/'.join(team)
	if name == players:
		return name
	return "%s (%s)" % (name, players)
