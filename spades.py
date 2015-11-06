from datetime import datetime
import re

from GameConstructor import GameConstructor

botNick = 'rhawk'
prefix = "(?P<ts>[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}) <.%s> " % botNick

# This could be a little more selective, but I'm lazy
nickPattern = '[^ ]+'

# pattern template string -> fun(pattern groups) -> event dict
eventPatterns = {
	"(?P<user>USER) starts a game of Spades to (?P<goal>NUMBER) with (?P<bags>NUMBER) bags!": lambda user, goal, bags: {'type': 'game_start', 'who': user, 'goal': int(goal), 'bags': int(bags)},
	"(?P<user>USER) ends the game": lambda user: {'type': 'game_abort', 'who': user},
	"(?P<user>USER) joins the game!": lambda user: {'type': 'sit', 'who': user},
	"(?P<user>USER): you bid first!": lambda user: {'type': 'bidding', 'who': user},
	"(?P<user>USER): it is your bid!": lambda user: {'type': 'bidding', 'who': user},
	"(?P<user>USER): it is your bid! \\(.*:(?P<bid>NUMBER)\\)": [lambda bid, **kw: {'type': 'bid', 'bid': bid if bid in ('nil', 'blind') else int(bid)}, lambda user, **kw: {'type': 'bidding', 'who': user}],
	"(?P<user>USER): you have the opening lead!": lambda user: {'type': 'playing', 'who': user},
	"(?P<user>USER): it is your turn!": lambda user: {'type': 'playing', 'who': user},
	"(?P<user>USER): it is your turn! \\(.*(?P<play>PLAY)\\)": [lambda play, **kw: {'type': 'play', 'play': play}, lambda user, **kw: {'type': 'playing', 'who': user}],
	# "(?P<user>USER) wins with PLAY \\(.*(?P<play>PLAY)\\)": [lambda play, **kw: {'type': 'play', 'play': play}, lambda user, **kw: {'type': 'trick_win', 'who': user}],
	"USER wins with PLAY \\(.*(?P<play>PLAY)\\)": lambda play: {'type': 'play', 'play': play},

	# "Round over!": lambda: {'type': 'round_end'},
	"Game over!": lambda: {'type': 'game_end'},
	# "(?P<user1>USER)/(?P<user2>USER) (?:make their bid|go bust): (?P<taken>NUMBER)/(?P<bid>NUMBER)": lambda user1, user2, taken, bid: {'type': 'round_summary', 'who': (user1, user2), 'taken': int(taken), 'bid': int(bid)},
	# "(?P<user1>USER)/(?P<user2>USER) lead (?P<score1>NUMBER) to (?P<score2>NUMBER) of (?P<goal>NUMBER)": lambda user1, user2, score1, score2, goal: {'type': 'game_checkpoint', 'leader': (user1, user2), 'lead_score': score1, 'trailing_score': score2, 'goal': goal},
	# "tied at (?P<score>NUMBER)"
	# "(?P<user1>USER)/(?P<user2>USER) bag out": lambda user1, user2: {'type': 'bag_out', 'who': (user1, user2)},
	# "(?P<user>USER) makes nil!": lambda user: {'type': 'nil_success', 'who': user},
	# "(?P<user>USER) fails at nil!": lambda user: {'type': 'nil_fail', 'who': user},
	# "(?P<user>USER) makes blind nil!": lambda user: {'type': 'blind_success', 'who': user},
	# "(?P<user>USER) fails miserably at blind nil!": lambda user: {'type': 'blind_fail', 'who': user},
}

# [(compiled line pattern, fun(pattern groups) -> event dict)]
eventPatterns = [(re.compile(prefix + p.replace('USER', nickPattern).replace('NUMBER', '[0-9]+|nil|blind').replace('PLAY', '(?:[23456789JQKA]|10)[sdch]') + '$'), fn) for p, fn in eventPatterns.iteritems()]

def fixSuits(str):
	suits = {
		'\342\231\240': 's',
		'\342\231\246': 'd',
		'\342\231\243': 'c',
		'\342\231\245': 'h'
	}
	for (unicode, plain) in suits.iteritems():
		str = str.replace(unicode, plain)
	return str

events = []
with open('log') as f:
	# for line in f:
	while True:
		off = f.tell()
		line = f.readline()
		if line == '':
			break
		line = fixSuits(line)
		for pattern, fns in eventPatterns:
			match = pattern.match(line)
			if match:
				if not hasattr(fns, '__iter__'):
					fns = [fns]
				for fn in fns:
					g = match.groupdict() # Copy; the original match groupdict is not changed below
					event = {'ts': g['ts'], 'off': off}
					del g['ts']
					event.update(fn(**g))
					events.append(event)
				break

from pprint import pprint
pprint(events)

print
print '-'*80
print

handler = GameConstructor()
for event in events:
	handler.pump(event)
