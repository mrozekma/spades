import sys

from Log import console
from os.path import isfile
from utils import *
from wrappers import header, footer

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		self.wrappers = True
		self.wrapperData = {'jsOnReady': [], 'jsOnLoad': [], 'headerFns': []}
		self.localData = {}
		self.pageTitle = None
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, fmt, *args):
		console('rorn', "%s - %s", self.address_string(), fmt % args)

	def requestDone(self):
		if self.wrappers:
			types = ['less', 'css', 'js']
			includes = {type: [] for type in types}
			handler = getattr(self, 'handler', None)
			if handler and 'statics' in handler:
				for key in ensureList(handler['statics']):
					for type in types:
						if isfile("static/%s.%s" % (key, type)):
							includes[type].append("/static/%s.%s" % (key, type))

			writer = ResponseWriter()
			header(self, includes)
			sys.stdout.write(self.response)
			footer(self)
			self.response = writer.done()

	def title(self, title):
		self.pageTitle = title

	def jsOnReady(self, js):
		self.wrapperData['jsOnReady'].append(js)

	def jsOnLoad(self, js):
		self.wrapperData['jsOnLoad'].append(js)

	def callFromHeader(self, fn):
		self.wrapperData['headerFns'].append(fn)

from handlers import *
