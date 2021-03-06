import calendar
from datetime import datetime, timedelta
import lxml.html
import re
import requests
from threading import Thread
import time
from tornado import gen
from tornado.websocket import websocket_connect
from tornado.ioloop import IOLoop
import traceback
from unidecode import unidecode

import DB
from DB import db, getGames
from GameConstructor import GameConstructor
from Log import console
from Shim import Shim
from WebSocket import WSSpadesHandler

logURL = 'http://pileus.org/andy/spades/'
wsURL = 'ws://pileus.org:6180/socket'
period = 10 # seconds
prefix = "(?P<ts>[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) \\| "

# This could be a little more selective, but I'm lazy
nickPattern = '[^ ]+'

# pattern template string -> fun(pattern groups) -> event dict
eventPatterns = {
	"(?P<user>USER) starts a game of Spades to (?P<goal>NUMBER) with (?P<bags>NUMBER) bags!": lambda user, goal, bags: {'type': 'game_start', 'who': user, 'goal': int(goal), 'bags': int(bags)},
	"(?P<user>USER) ends the game": lambda user: {'type': 'game_abort', 'who': user},
	"(?P<user>USER) joins the game!": lambda user: {'type': 'sit', 'who': user},
	"(?P<user>USER): you bid first!": lambda user: {'type': 'bidding', 'who': user},
	"(?P<user>USER): it is your bid!": lambda user: {'type': 'bidding', 'who': user},
	"(?P<user>USER): it is your bid! \\(.*:(?P<bid>NUMBER|nil|blind)\\)": [lambda bid, **kw: {'type': 'bid', 'bid': bid if bid in ('nil', 'blind') else int(bid)}, lambda user, **kw: {'type': 'bidding', 'who': user}],
	"(?:Playing with NUMBER bags?!|No bags!|Fighting for NUMBER tricks?!) \\(.*:(?P<bid>NUMBER|nil|blind)\\)": lambda bid: {'type': 'bid', 'bid': bid if bid in ('nil', 'blind') else int(bid)},
	"(?P<user>USER): you have the opening lead!": lambda user: {'type': 'playing', 'who': user},
	"(?P<user>USER): it is your turn!": lambda user: {'type': 'playing', 'who': user},
	"(?P<user>USER): it is your turn! \\(.*(?P<play>PLAY)\\)": [lambda play, **kw: {'type': 'play', 'play': play}, lambda user, **kw: {'type': 'playing', 'who': user}],
	# "(?P<user>USER) wins with PLAY \\(.*(?P<play>PLAY)\\)": [lambda play, **kw: {'type': 'play', 'play': play}, lambda user, **kw: {'type': 'trick_win', 'who': user}],
	"USER wins with PLAY \\(.*(?P<play>PLAY)\\)": lambda play: {'type': 'play', 'play': play},
	"(?P<user1>USER)/(?P<user2>USER) are now known as (?P<teamname>.*)": lambda user1, user2, teamname: {'type': 'teamname', 'who': (user1, user2), 'name': teamname},
	"(?P<user1>USER)/(?P<user2>USER) are boring": lambda user1, user2: {'type': 'teamname', 'who': (user1, user2), 'name': None},

	# We use deal/game_end as a marker instead of determining if the game is over ourselves, and round_summary/nil_signal to figure out the last player's bid in old logs
	"/me deals the cards": lambda: {'type': 'deal'},
	"Game over!": lambda: {'type': 'game_end'},
	"(?P<team>TEAM) (?:make their bid|go bust): (?P<taken>NUMBER)/(?P<bid>NUMBER)": lambda team, taken, bid: {'type': 'round_summary', 'team': team, 'taken': int(taken), 'bid': int(bid)},
	"(?P<user>USER) goes nil!": lambda user: {'type': 'nil_signal', 'who': user, 'bid': 'nil'},
	"(?P<user>USER) goes blind nil!": lambda user: {'type': 'nil_signal', 'who': user, 'bid': 'blind'},
	"(?P<user1>USER)/(?P<user2>USER): select a card to pass \\(/msg USER \\.pass <card>\\)": lambda user1, user2: {'type': 'passing', 'who': (user1, user2)},
	"(?P<user>USER) passes a card": lambda user: {'type': 'passed', 'who': user, 'finished': False},
	"Cards have been passed!": lambda: {'type': 'passed', 'finished': True},

	# These are unnecessary messages and generate no events
	"Round over!": None,
	"TEAM lead NUMBER to NUMBER of NUMBER": None,
	"tied at NUMBER of NUMBER": None,
	"TEAM bag (?:way )?out": None,
	"USER (?:makes|fails at|makes blind|fails miserably at blind) nil!": None,
	"USER (?:\\(USER\\) )?can (?:now|no longer) play for USER": None,
	"USER allowed:.*": None,
	"It's a tie! Playing an extra round!": None,
	"(?P<user>USER) goes on a rampage": lambda user: {'type': 'game_abort', 'who': user},
}

# [(compiled line pattern, [fun(pattern groups) -> event dict])]
eventPatterns = [(re.compile(prefix + p.replace('USER', nickPattern).replace('TEAM', '[a-zA-Z0-9].*').replace('NUMBER', '-?[0-9]+').replace('PLAY', '(?:[23456789JQKA]|10)[sdch]') + '\n$'), [] if fns is None else fns if hasattr(fns, '__iter__') else [fns]) for p, fns in eventPatterns.iteritems()]

def unpretty(str):
	str = str.encode('utf-8')
	# IRC color codes
	str = str.replace("\0031,00\002", "").replace("\0034,00\002", "").replace("\017", "")
	# Unicode suits
	suits = {
		'\002\342\231\240': 's',
		'\002\342\231\246': 'd',
		'\002\342\231\243': 'c',
		'\002\342\231\245': 'h'
	}
	for (uc, plain) in suits.iteritems():
		str = str.replace(uc, plain)
	return unidecode(str.decode('utf-8'))

class EventThread(Thread):
	def __init__(self, mode):
		Thread.__init__(self)
		self.name = 'event thread'
		self.daemon = True
		self.gameCon = None
		self.tickWait = True

		# For testing. If non-None, represents the number of events that should be read from the current game before stopping
		self.test = None

		self.run = {
			'poll': self.runPolling,
			'websocket': self.runWebsocket,
		}[mode]

	def runPolling(self):
		while True:
			if self.tickWrap() is False:
				return
			if self.tickWait:
				time.sleep(period)
			else:
				self.tickWait = True

	def runWebsocket(self):
		@gen.coroutine
		def wrap():
			while True:
				console('websocket client', "Connecting to %s" % wsURL)
				ws = yield websocket_connect(wsURL)
				console('websocket client', 'Connected')
				# Trigger once immediately to fetch the current game
				while True:
					self.tickWrap()
					if self.tickWait:
						break
					else:
						self.tickWait = True
				while True:
					# Wait for a message, then poll the logs (we could theoretically just use the message directly, but this is easier to fit into the existing setup that expects offsets and timestamps)
					msg = yield ws.read_message()
					if msg is None:
						break
					console('websocket client', "Message: %s" % msg)
					self.tickWrap()
				console('websocket client', 'Disconnected')
		wrap()

	def tickWrap(self):
		try:
			self.tick()
			return True
		except Exception, e:
			print "EventThread error:"
			if self.gameCon is not None:
				self.gameCon.err = str(e)
				if hasattr(self.gameCon, 'game'):
					WSSpadesHandler.on_game_change(self.gameCon.game)
			traceback.print_exc()
			return False
		finally:
			DB.setActiveGame(getattr(self.gameCon, 'game', None))

	def tick(self):
		if self.gameCon is None:
			# Get list of logs (['YYYY-mm-dd_HHMMSS.log'])
			# Unfortunately the server doesn't return an etag for this page; instead we cache based on the number of logs displayed, on the assumption that logs will never be removed
			req = requests.get(logURL)
			if req.status_code != 200:
				raise RuntimeError("Server returned %d looking up log list" % req.status_code)
			logs = map(str, lxml.html.fromstring(req.text).xpath('//a[substring-after(@href, ".")="log"]/@href'))
			logs = filter(None, map(Shim.onLogLoad, logs))

			numGames = len(getGames())
			if len(logs) < numGames:
				raise RuntimeError("Only got %d %s from server (have %d in database)" % (len(logs), 'log' if len(logs) == 1 else 'logs', numGames))
			elif len(logs) == numGames: # No new logs
				return

			# Find the first one we don't have a game for
			for log in logs:
				if log not in db['games']:
					console('event thread', "Starting new game for %s" % log)
					self.gameCon = Shim.onGameCon(GameConstructor(log, self.onGameEnd))
					break
			else:
				console('event thread', "No games in progress")
				return

		# Look for new events in the current log
		data = self.cachedGet(logURL + self.gameCon.logFilename)
		if data is None: # Nothing new
			console('event thread', "No new data in %s" % self.gameCon.logFilename)
			return
		elif data is False: # Server is down. Hopefully temporarily; try again next tick
			console('event thread', "Failed to fetch data from %s" % self.gameCon.logFilename)
			return
		elif len(data) < self.gameCon.logOffset:
			raise RuntimeError("Fetched %d-byte log file %s, but next event expected at %d" % (len(data), self.gameCon.logFilename, self.gameCon.logOffset))
		while self.gameCon and self.gameCon.logOffset < len(data) and self.test != 0:
			line = data[self.gameCon.logOffset:data.index('\n', self.gameCon.logOffset)+1]
			print "%8d %s" % (self.gameCon.logOffset, line)
			originalLen = len(line)
			line = Shim.onLine(self.gameCon, self.gameCon.logOffset, unpretty(line))
			if line is None:
				self.gameCon.logOffset += originalLen
				continue
			# print "Searching for pattern at %s offset %d: %s" % (self.gameCon.logFilename, self.gameCon.logOffset, line)
			for pattern, fns in eventPatterns:
				match = pattern.match(line)
				if match:
					for fn in fns:
						g = match.groupdict() # Copy; the original match groupdict is not changed below
						# Bit of a hack. We want to rewrite any group that contains a PLAY, but there's no way to tell now. Currently all those groups are named 'play', so we only rewrite those
						if 'play' in g:
							g['play'] = unpretty(g['play'])
						# Same hack with USER
						for k in ('user', 'user1', 'user2'):
							if k in g:
								shimmed = Shim.onUsername(g[k])
								if shimmed != g[k]:
									self.gameCon.usernameShims[shimmed] = g[k]
									g[k] = shimmed
						tz = int(round((datetime.now() - datetime.utcnow()).total_seconds() / 3600))
						event = {'ts': datetime.strptime(g['ts'], '%Y-%m-%d %H:%M:%S') + timedelta(hours = tz), 'off': self.gameCon.logOffset}
						del g['ts']
						event.update(fn(**g))
						if self.test > 0:
							self.test -= 1
						event = Shim.onEvent(self.gameCon, self.gameCon.logOffset, event)
						if event is not None:
							self.gameCon.pump(event)
					# pump() may have triggered onGameEnd and killed the current gameCon
					if self.gameCon is not None:
						self.gameCon.logOffset += originalLen
					break
			else:
				raise RuntimeError("Unrecognized log line at %s:%d: %s" % (self.gameCon.logFilename, self.gameCon.logOffset, line))
		if hasattr(self.gameCon, 'game'):
			self.gameCon.game.out()
			WSSpadesHandler.on_game_change(self.gameCon.game)

	def cachedGet(self, url, etags = {}):
		headers = {}
		if url in etags:
			headers['If-None-Match'] = etags[url]
		req = requests.get(url, headers = headers)
		if req.status_code == 304: # Not Modified
			return None
		elif req.status_code == 404:
			return False
		elif req.status_code != 200:
			raise RuntimeError("Server returned %d fetching %s" % (req.status_code, url))
		if 'etag' in req.headers:
			etags[url] = req.headers['etag']
		return req.text

	def onGameEnd(self, game):
		console('event thread', "Game over: %s" % self.gameCon.logFilename)
		game.out()
		db['games'][self.gameCon.logFilename] = game
		self.gameCon = None
		# After this tick, immediately check again for a new game. This is mostly used when populating the database for the first time
		self.tickWait = False
