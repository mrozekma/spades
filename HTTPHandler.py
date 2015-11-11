import sys

from Log import console
from wrappers import header, footer

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		self.wrappers = True
		self.wrapperData = {'jsOnReady': []}
		self.localData = {}
		self.pageTitle = None
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, fmt, *args):
		console('rorn', "%s - %s", self.address_string(), fmt % args)

	def requestDone(self):
		if self.wrappers:
			writer = ResponseWriter()
			header(self)
			sys.stdout.write(self.response)
			footer(self)
			self.response = writer.done()

	def title(self, title):
		self.pageTitle = title

	def jsOnReady(self, js):
		self.wrapperData['jsOnReady'].append(js)

from handlers import *
