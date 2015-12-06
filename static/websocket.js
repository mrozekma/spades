SpadesWS = (function() {
	event_anchor = {};
	socket = null;
	port = get_websocket_port(); // /dyn.js (dyn.py handler)

	function init() {
		socket = new WebSocket('ws://' + window.location.hostname + ':' + port + '/ws');
		socket.onopen = function() {
			$(event_anchor).trigger('open.spadesws');
		}
		socket.onmessage = function(e) {
			$(event_anchor).trigger('message.spadesws', [JSON.parse(e.data)]);
		}
		socket.onclose = function() {
			$(event_anchor).trigger('close.spadesws');
		}
		$(window).unload(function() {
			socket.close();
		});
	}

	function send(data) {
		socket.send(JSON.stringify(data));
	}

	function on_open(handler) {
		$(event_anchor).on('open.spadesws', handler);
	}

	function on_message(handler) {
		$(event_anchor).on('message.spadesws', handler);
	}

	function on_close(handler) {
		$(event_anchor).on('close.spadesws', handler);
	}

	return {
		init: init,
		send: send,
		on_open: on_open,
		on_message: on_message,
		on_close: on_close,
	};
})();
