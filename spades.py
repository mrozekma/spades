from datetime import datetime
import os
import re
import sys
from threading import currentThread

from DB import db
from EventThread import EventThread
from Log import console
from WebSocket import WebSocket

from HTTPHandler import HTTPHandler
from rorn.HTTPServer import HTTPServer

# Different classnames for the new version of bootstrap
from rorn.Box import classnames as boxClasses
boxClasses.update({'base': 'alert', 'info': 'alert-info', 'success': 'alert-success', 'warning': 'alert-warning', 'error': 'alert-danger'})

PORT = 8083
currentThread().name = 'main'
EventThread().start()
WebSocket.start(PORT + 1)

server = HTTPServer(('', PORT), HTTPHandler)
try:
	console('rorn', 'Listening for connections')
	server.serve_forever()
except KeyboardInterrupt:
	sys.__stdout__.write("\n\n")
	console('main', 'Exiting at user request')
except (Exception, SystemExit), e:
	sys.__stdout__.write("\n\n")
	console('main', "%s", e)

console('main', 'Closing server sockets')
server.server_close()

console('main', 'Done')
