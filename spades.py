from datetime import datetime
from argparse import ArgumentParser
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

parser = ArgumentParser()
parser.add_argument('--http-port', type = int, default = 8083, help = 'HTTP port')
parser.add_argument('--ws-port', type = int, default = 8084, help = 'Websocket port')
parser.add_argument('--ws-ua-port', type = int, help = 'Websocket port user agents should connect to')
args = parser.parse_args()

currentThread().name = 'main'
EventThread().start()
WebSocket.start(args.ws_port, args.ws_ua_port or args.ws_port)

server = HTTPServer(('', args.http_port), HTTPHandler)
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
