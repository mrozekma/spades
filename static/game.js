game_name = location.href.split('/').slice(-1)[0];

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

make_seats = function() {
	rtn = [];
	// Seat positions don't matter (as long as play order is preserved), but it's logical to me that the first player is south
	$.each(['south', 'west', 'north', 'east'], function(i, location) {
		rtn[i] = seat = $('<div/>').addClass('seat seat-open seat-' + location);
		seat.data('location', location);
		tags = $('<div/>').addClass('tags').appendTo(seat);
		tags.append($('<span/>').addClass('label label-danger tag-turn').text('Turn'));
		tags.append($('<span/>').addClass('label label-success tag-winning').text('Winning'));
		tags.append($('<span/>').addClass('label label-primary tag-lead').text('Lead'));
		seat.append($('<img/>').addClass('card').attr('src', '/card/back'));
		bottom = $('<div/>').addClass('bottom').appendTo(seat);
		bottom.append($('<img/>').addClass('avatar').attr('src', '/player/-/avatar'));
		right = $('<div/>').addClass('right').appendTo(bottom);
		right.append($('<div/>').addClass('username').text('Open'));
		right.append($('<div/>').addClass('tricks'));
	});
	return rtn;
}

$(document).ready(function() {
	turn_clock = null;

	$('button.remaining-cards').click(function() {
		div = $('div.remaining-cards');
		if(div.length > 0) {
			div.show();
			this.remove();
		}
	});

	SpadesWS.on_message(function(e, data) {
		console.log(data);
		// Figure out difference between local time and server time
		time_off = Date.now() - data['now'];

		if(turn_clock) {
			clearInterval(turn_clock);
			turn_clock = null;
		}

		$('title').text(data['description'].join(' ') + ' - ' + data['friendly_name'] + ' - Spades');
		$('h1').text(data['friendly_name']);
		$('.navbar .navbar-brand').html(data['description'].join('&nbsp;&bull;&nbsp;'));

		// Players aren't seated yet, so don't bother showing all that
		// Just show a list of players
		if(data['pregame_players']) {
			$('.seat').hide();
			parent = $('<div/>').addClass('pregame-players').appendTo($('.current-trick'));
			for(i = 0; i < 4; i++) {
				player = data['pregame_players'][i];
				box = $('<div/>').addClass('pregame-player').toggleClass('seat-open', player == null).appendTo(parent);
				box.append($('<img/>').attr('src', '/player/' + (player ? player : '-') + '/avatar'));
				box.append($('<div/>').addClass('username').text(player ? player : '<open>'));
			}
			return;
		}

		seats = make_seats();
		$('.tags .label', seats).hide();
		$('.tag-turn', seats).text('Turn');
		if(data['leader']) {
			seat = seats[data['players'].indexOf(data['leader'])];
			$('.tag-lead', seat).css('display', 'block');
		}
		if(data['turn']) {
			seat = seats[data['players'].indexOf(data['turn'])];
			if(data['turn_started']) {
				(function(anchor, start) {
					update_clock = function() {
						elapsed = (Date.now() - start) / 1000;
						hours = Math.floor(elapsed / (60 * 60));
						minutes = Math.floor((elapsed - hours * 60 * 60) / 60);
						seconds = Math.floor(elapsed - (hours * 60 * 60) - (minutes * 60));
						txt = "";
						if(hours > 0) {
							txt += hours + ":";
						}
						if(minutes < 10) {
							txt += "0";
						}
						txt += minutes + ":";
						if(seconds < 10) {
							txt += "0";
						}
						txt += seconds;
						anchor.html('Turn<br>' + txt);
					};
					update_clock();
					turn_clock = setInterval(update_clock, 1000);
				})($('.tag-turn', seat), data['turn_started'] + time_off);
			}
			$('.tag-turn', seat).css('display', 'block');
			// For asthetic reasons, we only leave enough room for two rows of tags above each card, and turn takes both
			// If the current player is also the leader, we hide that tag (it should be obvious they're leading since it's their turn and nobody has played)
			$('.tag-lead', seat).hide();
		}
		if(data['winning']) {
			seat = seats[data['players'].indexOf(data['winning'])];
			$('.tag-winning', seat).css('display', 'block');
		}

		for(i = 0; i < 4; i++) {
			seat = seats[i];
			if(data['players'][i] == null) {
				seat.addClass('seat-open');
				$('.avatar', seat).attr('src', '/player/-/avatar');
				$('.username', seat).text('Open');
			} else {
				username = data['players'][i];
				seat.removeClass('seat-open');
				$('.avatar', seat).attr('src', '/player/' + username + '/avatar');
				$('.username', seat).text(username);
			}
			if(data['bids']) {
				tricks = $('.tricks', seat);
				tricks.empty();
				bid = data['bids'][i];
				taken = data['taken'][i];
				// For a player with an unknown bid, we count all taken tricks as non-bags and show no out tricks
				if(bid == null) {
					tricks.attr('title', 'Took ' + taken + ' ' + (taken == 1 ? 'trick' : 'tricks') + ' (unknown bid)');
					for(j = 0; j < taken; j++) {
						tricks.append($('<img/>').attr('src', '/card/back').addClass('taken'));
					}
				} else {
					tricks.attr('title', 'Took ' + taken + '/' + bid + ' ' + (taken == 1 ? 'trick' : 'tricks') + (taken <= bid ? '' : (' (' + (taken - bid) + ' ' + (taken - bid == 1 ? 'bag' : 'bags') + ')')));
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
			}
			if(data['plays']) {
				$('.card', seat).attr('title', data['plays'][i] || '').attr('src', '/card/' + (data['plays'][i] ? data['plays'][i] : 'back'));
			}
		}

		parent = $('<table/>').addClass('past-tricks');
		if(data['players'][3]) { // All players known
			row = $('<tr/>').appendTo(parent);
			$.each(data['players'], function(i, player) {
				cell = $('<th/>').addClass('player').appendTo(row);
				cell.append($('<img/>').addClass('avatar').attr('src', '/player/' + player + '/avatar'));
				cell.append($('<div/>').addClass('username').text(player));
			});
			$.each(data['past_tricks'], function(i, trick) {
				row = $('<tr/>').appendTo(parent);
				for(i = 0; i < 4; i++) {
					cell = $('<td/>').appendTo(row);
					if(trick['leader'] == data['players'][i]) {
						cell.append($('<span/>').addClass('label label-primary tag-lead').text('Lead'));
					}
					if(trick['winner'] == data['players'][i]) {
						cell.append($('<span/>').addClass('label label-success tag-winning').text('Won'));
					}
					cell.append($('<img/>').addClass('card').attr('src', '/card/' + trick['plays'][i]));
				}
			});
		}
		$('.past-tricks').replaceWith(parent);

		box = $('div.remaining-cards');
		box.empty();
		$.each(data['deck'], function(i, card) {
			box.append($('<img/>').addClass('card').attr('src', '/card/' + card));
		});

		// Replace old seats DOM (if there was one) with the new one
		$.each(seats, function(_, seat) {
			$('.seat-' + seat.data('location')).replaceWith(seat);
		});
	});

	connection_timer = setInterval(attempt_connection, 15000);
	attempt_connection();
});
