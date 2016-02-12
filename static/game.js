game_name = location.href.match(/\/games\/([0-9]{8}_[0-9]{6})(\/|$)/)[1];

connection_timer = null;
attempt_connection = function() {
	SpadesWS.init();
}

SpadesWS.on_open(function() {
	console.log('Websocket open');
	SpadesWS.send({subscribe: ['game#' + game_name]});
	if(connection_timer) {
		clearInterval(connection_timer);
		connection_timer = null;
	}
	$('.disconnected-icon').hide();
});

SpadesWS.on_close(function() {
	console.log('Websocket closed');
	$('.disconnected-icon').show();
	connection_timer = setInterval(attempt_connection, 15000);
});

msToString = function(ts) {
	ts /= 1000;
	hours = Math.floor(ts / (60 * 60));
	minutes = Math.floor((ts - hours * 60 * 60) / 60);
	seconds = Math.floor(ts - (hours * 60 * 60) - (minutes * 60));
	rtn = "";
	if(hours > 0) {
		rtn += hours + ":";
	}
	if(minutes < 10) {
		rtn += "0";
	}
	rtn += minutes + ":";
	if(seconds < 10) {
		rtn += "0";
	}
	rtn += seconds;
	return rtn;
}

set_player = function(handle, player) {
	handle.data('player', player);
	handle.toggleClass('seat-open', player == null);
	url = '/players/' + (player ? player : '-') + '/avatar';
	username = player ? player : '<unknown>';
	if($('.avatar', handle).attr('src') != url) {
		$('.avatar', handle).attr('src', url);
	}
	if($('.username', handle).text() != username) {
		$('.username', handle).text(username);
	}
}

set_card = function(handle, card) {
	url = '/card/' + card;
	if(handle.attr('src') != url) {
		handle.attr('src', url);
	}
}

notify = function(text) {
    if(Notification.permission == 'granted') {
        new Notification('Spades', {body: text});
    }
}

$(document).ready(function() {
	turn_clock = null;

	$('button.remaining-cards').click(function() {
		$('div.remaining-cards').show();
		this.remove();
	});

	barn = new Barn(localStorage);

	setup_focus = function() {
		player = barn.get('focus');
		seats = $('.seat');
		order = ['south', 'west', 'north', 'east'];
		if(player) {
			seats.each(function(i, seat) {
				if($(seat).data('player') == player) {
					return false; // stop iterating
				}
				order.unshift(order.pop()); // rotate right
			});
		}
		// If any of the seats are wrong, fix them all
		// (NB: the arguments to the callback to every() are reversed from jQuery's each())
		if(!seats.get().every(function(seat, i) {return $(seat).hasClass('seat-' + order[i]);})) {
			seats.removeClass('seat-south seat-west seat-north seat-east');
			seats.each(function(i, seat) {
				$(seat).addClass('seat-' + order[i]);
			});
		}
	}

	$.contextMenu({
		selector: ".avatar,.username",
		build: function($trigger, e) {
			// Find the DOM parent that contains the player as attached data (set by set_player())
			player = $trigger.parents(':data(player)').data('player');
			if(!player) {
				return false;
			}
			items = {
				profile: {
					name: "Player profile",
					callback: function(key, opt) {
						window.location = '/players/' + player;
					}
				},
			}
			if(barn.get('focus') != player) {
				items.focus = {
					name: "Force south",
					callback: function(key, opt) {
						barn.set('focus', player);
						setup_focus();
					}
				};
			} else {
				items.unfocus = {
					name: "Stop forcing south",
					callback: function(key, opt) {
						barn.del('focus');
						setup_focus();
					}
				};
			}
			if((barn.smembers('alerts') || []).indexOf(player) < 0) {
				items.alert = {
					name: "Show turn alerts",
					callback: function(key, opt) {
						barn.sadd('alerts', player);
					}
				};
			} else {
				items.unalert = {
					name: "Stop showing turn alerts",
					callback: function(key, opt) {
						barn.srem('alerts', player);
					}
				};
			}
			return {items: items};
		},
	});

	if(Notification.permission == 'default') {
		Notification.requestPermission();
	}

	current_turn = null;
	SpadesWS.on_message(function(e, data) {
		console.log(data);
		if(data['description'] == 'Game over') {
			window.location += '/history';
		}
		// Figure out difference between local time and server time
		time_off = Date.now() - data['now'];

		/** Current Trick **/

		if(turn_clock) {
			clearInterval(turn_clock);
			turn_clock = null;
		}

		$('title').text(data['description'].join(' ') + ' - ' + data['friendly_name'] + ' - Spades');
		$('h1').text(data['friendly_name']);
		$('.navbar .navbar-brand').html(data['description'].join('&nbsp;&bull;&nbsp;'));
		if(data['err']) {
			$('#game-error').text(data['err']).show();
		} else {
			$('#game-error').hide();
		}
		if(data['turn']) {
			$('title').text(data['turn'] + "'s turn - " + $('title').text());
			if(current_turn != data['turn']) {
				current_turn = data['turn'];
				if((barn.smembers('alerts') || []).indexOf(current_turn) >= 0) {
					notify("It is " + current_turn + "'s turn");
				}
			}
		}

		$('.cols').show();

		// Players aren't seated yet, so don't bother showing all that
		// Just show a list of players
		if(data['pregame_players']) {
			$('.col:not(.current-trick)').hide();
			$('.seat').hide();
			$('.pregame-players').show();
			boxes = $('.pregame-player');
			for(i = 0; i < 4; i++) {
				set_player($(boxes[i]), data['pregame_players'][i]);
			}
			return;
		}

		$('.col').show();
		$('.seat').show();
		$('.pregame-players').hide();

		$('.current-trick .seat').each(function(i, seat) {
			seat = $(this);
			player = data['players'][i];
			set_player(seat, player);
			set_player($($('table.past-tricks tr th')[i + 1]), player);

			$('.tag-lead', seat).toggle(player != null && data['leader'] == player);
			$('.tag-turn', seat).toggle(player != null && data['turn'] == player);
			$('.tag-winning', seat).toggle(player != null && data['winning'] == player);

			if(data['bids']) {
				tricks = $('.tricks', seat);
				tricks.empty();
				bid = data['bids'][i];
				taken = data['taken'][i];
				if(bid == 'nil' || bid == 'blind') {
					tricks.attr('title', (bid == 'blind' ? 'Blind ' : '') + 'Nil' + (taken ? (' (' + taken + (taken == 1 ? 'bag' : 'bags') + ')') : ''));
					tricks.append($('<img/>').attr('src', '/card/' + bid));
					bid = 0;
				} else {
					tricks.attr('title', 'Took ' + taken + '/' + bid + ' ' + 'tricks' + (taken <= bid ? '' : (' (' + (taken - bid) + ' ' + (taken - bid == 1 ? 'bag' : 'bags') + ')')));
				}
				for(j = 0; j < Math.min(bid, taken); j++) {
					tricks.append($('<img/>').attr('src', '/card/back').addClass('taken'));
				}
				for(j = bid; j < taken; j++) {
					tricks.append($('<img/>').attr('src', '/card/back').addClass('bag'));
				}
				for(j = taken; j < bid; j++) {
					tricks.append($('<img/>').attr('src', '/card/blank').addClass('out'));
				}
			}

			set_card($('img.card', seat), (data['plays'] && data['plays'][i]) ? data['plays'][i] : 'back');
		});

		// It's possible (if unlikely) to have a turn field but no turn_started if we happen to pull from the server at the wrong instant
		anchor = $($('.tag-turn:visible')[0]);
		if(data['turn_started']) {
			// Update the turn clock every second.
			// There will only ever be one visible turn tag
			start = data['turn_started'] + time_off;
			turn_clock = null;
			update_clock = function() {
				anchor.html('Turn<br>' + msToString(Date.now() - start));
			};
			turn_clock = setInterval(update_clock, 1000);
			update_clock();
		} else {
			anchor.text('Turn');
		}

		// For asthetic reasons, we only leave enough room for two rows of tags above each card, and turn takes both.
		// If the current player is also the leader, we hide that tag (it should be obvious they're leading since it's their turn and nobody has played)
		if(data['leader'] == data['turn']) {
			$('.tag-lead').hide();
		}

		setup_focus();

		/** Past Tricks **/

		if(data['past_tricks']) {
			$.each($('table.past-tricks tr:not(:first-child)').get().reverse(), function(j, row) {
				row = $(row);
				if(data['past_tricks'][j]) {
					trick = data['past_tricks'][j];
					$('td.trick-number .label', row).html('Trick ' + (j + 1) + '&nbsp;&nbsp;(' + msToString(trick['duration']) + ')');
					$('td.trick', row).each(function(k, handle) {
						set_card($('img', handle), trick['plays'][k]);
						$('.tag-lead', handle).toggle(trick['leader'] == data['players'][k]);
						$('.tag-winning', handle).toggle(trick['winner'] == data['players'][k]);
					});
					row.show();
				} else {
					row.hide();
				}
			});
		} else {
			$('table.past-tricks tr:not(:first-child)').hide();
		}

		/** Remaining cards **/

		$('.remaining-cards img').hide();
		$.each(data['deck'] || [], function(j, card) {
			$('.remaining-cards img[src$=' + card + ']').show();
		});
	});

	connection_timer = setInterval(attempt_connection, 15000);
	attempt_connection();
});
