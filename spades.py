from datetime import datetime
import re

from DB import db
from EventThread import EventThread

EventThread().start()

'''
	events = []
	with open('/tmp/#rhspades.log') as f:
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
					for fn in fns:
						g = match.groupdict() # Copy; the original match groupdict is not changed below
						event = {'ts': datetime.strptime(g['ts'], '%Y-%m-%d %H:%M:%S'), 'off': off}
						del g['ts']
						event.update(fn(**g))
						events.append(event)
					break
	d['events'] = events

events = d['events']

handler = GameConstructor()
for event in events:
	handler.pump(event)
'''

print 'Paused'
raw_input()
