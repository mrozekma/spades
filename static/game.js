game_name = location.href.split('/').slice(-1)[0];

SpadesWS.on_open(function() {
	console.log('Websocket open');
	SpadesWS.send({subscribe: ['game#' + game_name]});
});

$(document).ready(function() {
	seats = [$('.seat-south'), $('.seat-west'), $('.seat-north'), $('.seat-east')];

	SpadesWS.on_message(function(e, data) {
		console.log(data);
		$('.seat .progress,.seat .progress-text,.tags .label').hide();
		if(data['leader']) {
			seat = seats[data['players'].indexOf(data['leader'])];
			$('.tag-lead', seat).css('display', 'block');
		}
		if(data['turn']) {
			seat = seats[data['players'].indexOf(data['turn'])];
			$('.tag-turn', seat).css('display', 'block');
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
				if(data['bids'][i] == null) {
					$('.progress-text', seat).text(data['taken'][i] + '/?');
					$('.progress-bar', seat).css('width', '0%');
				} else {
					$('.progress-text', seat).text(data['taken'][i] + '/' + data['bids'][i]);
					$('.progress-bar', seat).css('width', (data['taken'][i] / data['bids'][i] * 100) + '%');
				}
				$('.seat .progress,.seat .progress-text').show();
			}
			if(data['plays']) {
				$('.play', seat).attr('src', '/card/' + (data['plays'][i] ? data['plays'][i] : 'back'));
			}
		}
	});

	SpadesWS.init();
});
