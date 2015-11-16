from tornado.websocket import WebSocketHandler
import tornado.ioloop

from json import loads as fromJS, dumps as toJS
from threading import Thread

from DB import getGames
from Log import console
from utils import *

handlers = []
channels = {}

class WebSocket:
	@staticmethod
	def start(port):
		WSThread(port).start()

	@staticmethod
	def broadcast(data):
		for handler in handlers:
			handler.write_message(toJS(data))

	@staticmethod
	def sendChannel(channel, data):
		if not 'channel' in data:
			data['channel'] = channel
		for handler in channels.get(channel, []):
			handler.write_message(toJS(data))

class WSThread(Thread):
	def __init__(self, port):
		Thread.__init__(self)
		self.name = 'websocket'
		self.daemon = True
		self.port = port

	def run(self):
		app = tornado.web.Application([('/', WSHandler)])
		app.listen(self.port, '0.0.0.0')
		console('websocket', "Listening")
		tornado.ioloop.IOLoop.instance().start()

class WSHandler(WebSocketHandler):
	def __init__(self, *args, **kw):
		super(WSHandler, self).__init__(*args, **kw)
		self.channels = set()

	def check_origin(self, origin):
		return True

	def open(self):
		handlers.append(self)
		console('websocket', "Opened")

	def on_message(self, message):
		console('websocket', "Message received: %s" % message)
		try:
			data = fromJS(message)
		except:
			return

		if 'subscribe' in data and isinstance(data['subscribe'], list):
			addChannels = (set(data['subscribe']) - self.channels)
			self.channels |= addChannels
			for channel in addChannels:
				if channel not in channels:
					channels[channel] = set()
				if channel.startswith('game#'):
					filename = channel[5:] + '.log'
					games = getGames()
					if filename in games:
						self.write_message(toJS(games[filename].state))
				channels[channel].add(self)

		if 'unsubscribe' in data and isinstance(data['unsubscribe'], list):
			rmChannels = (self.channels & set(data['unsubscribe']))
			self.channels -= rmChannels
			for channel in rmChannels:
				channels[channel].remove(self)
				if len(channels[channel]) == 0:
					del channels[channel]

	def on_close(self):
		for channel in self.channels:
			channels[channel].remove(self)
			if len(channels[channel]) == 0:
				del channels[channel]
		handlers.remove(self)
		console('websocket', "Closed")
