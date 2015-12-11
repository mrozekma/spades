$(document).ready(function() {
	max_round = parseInt($('.nav .dropdown-menu li a[href^="#r"]').last().attr('href').substr(2), 10);
	$(window).bind('hashchange', function(e) {
		match = window.location.hash.match(/^#r([0-9]+)$/);
		if(match) {
			round = parseInt(match[1], 10);
			key = 'r' + round;
			title = 'Round ' + round + ' / ' + max_round;
			prev = (round == 1) ? 'g' : 'r' + (round - 1);
			next = (round < max_round) ? 'r' + (round + 1) : null;
		} else {
			key = 'g';
			title = 'Game';
			prev = null;
			next = (max_round >= 1) ? 'r1' : null;
		}

		$('.navbar .navbar-brand').text(title);
		$('.navbar .dropdown-menu li').removeClass('active');
		$('.navbar .dropdown-menu li a[href="#' + key + '"]').parent('li').addClass('active');
		$('.nav-arrows a.prev').attr('href', '#' + (prev || '')).toggle(prev != null);
		$('.nav-arrows a.next').attr('href', '#' + (next || '')).toggle(next != null);
		$('.round-box').hide();
		$('#box-' + key).show();
		$.each(Highcharts.charts, function() {
			if($(this.container).is(':visible')) {
				this.reflow();
			}
		});
	}).trigger('hashchange');
});
