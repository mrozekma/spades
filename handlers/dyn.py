from WebSocket import WebSocket

@get('dyn.js')
def dynJS(handler):
	port = WebSocket.getUAPort()
	handler.wrappers = False
	handler.contentType = 'text/javascript'
	print "function get_websocket_port() {return %d;}" % port
