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

$(document).ready(function() {
	seats = [$('.seat-south'), $('.seat-west'), $('.seat-north'), $('.seat-east')];

	original_title = $('title').text();
	turn_clock = null;

	SpadesWS.on_message(function(e, data) {
		console.log(data);
		// Figure out difference between local time and server time
		time_off = Date.now() - data['now'];

		if(turn_clock) {
			clearInterval(turn_clock);
			turn_clock = null;
		}

		$('title').text(data['description'].join(' ') + ' - ' + original_title);
		$('.navbar .navbar-brand').html(data['description'].join('&nbsp;&bull;&nbsp;'));
		$('.tags .label').hide();
		$('.tag-turn').text('Turn');
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
				$('.play', seat).attr('title', data['plays'][i] || '').attr('src', '/card/' + (data['plays'][i] ? data['plays'][i] : 'back'));
			}
		}
	});

	connection_timer = setInterval(attempt_connection, 15000);
	attempt_connection();
});
