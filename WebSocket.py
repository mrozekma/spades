from tornado.websocket import WebSocketHandler
import tornado.ioloop

from datetime import datetime
from json import loads as fromJS, dumps as toJS
import os
from threading import Thread
import time

from DB import getGames
from Log import console
from utils import *

handlers = []
channels = {}
uaPort = None

class WebSocket:
	@staticmethod
	def start(thisPort, thisUAPort):
		global uaPort
		if uaPort is not None:
			raise RuntimeError("WebSocket started multiple times")
		uaPort = thisUAPort
		WSThread(thisPort).start()

	@staticmethod
	def broadcast(data):
		for handler in handlers:
			handler.write_message(toJS(data))

	@staticmethod
	def sendChannel(channel, data):
		for handler in channels.get(channel, []):
			handler.sendChannel(channel, data)

	@staticmethod
	def getUAPort():
		if uaPort is None:
			raise RuntimeError("WebSocket not yet started")
		return uaPort

class WSThread(Thread):
	def __init__(self, port):
		Thread.__init__(self)
		self.name = 'websocket'
		self.daemon = True
		self.port = port

	def run(self):
		app = tornado.web.Application([('/', WSSpadesHandler), ('/ws', WSSpadesHandler)])
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

	def sendChannel(self, channel, data):
		if 'channel' not in data:
			data['channel'] = channel
		if 'now' not in data:
			data['now'] = int(time.mktime(datetime.now().timetuple()) * 1000) # Javascript times are in ms
		self.write_message(toJS(data))

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
				self.on_subscribe(channel)
				channels[channel].add(self)

		if 'unsubscribe' in data and isinstance(data['unsubscribe'], list):
			rmChannels = (self.channels & set(data['unsubscribe']))
			self.channels -= rmChannels
			for channel in rmChannels:
				self.on_unsubscribe(channel)
				channels[channel].remove(self)
				if len(channels[channel]) == 0:
					del channels[channel]

	def on_close(self):
		for channel in self.channels:
			self.on_unsubscribe(channel)
			channels[channel].remove(self)
			if len(channels[channel]) == 0:
				del channels[channel]
		handlers.remove(self)
		console('websocket', "Closed")

	def on_subscribe(self, channel): pass
	def on_unsubscribe(self, channel): pass

class WSSpadesHandler(WSHandler):
	def on_subscribe(self, channel):
		if channel.startswith('game#'):
			filename = channel[5:] + '.log'
			games = getGames()
			if filename in games:
				self.sendChannel(channel, games[filename].runState)

	@staticmethod
	def on_game_change(game):
		name = os.path.splitext(game.logFilename)[0]
		WebSocket.sendChannel("game#%s" % name, game.runState)
