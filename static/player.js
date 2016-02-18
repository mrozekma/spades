$(document).ready(function() {
	$('img[src="/static/images/expand.png"],img[src="/static/images/collapse.png"]').click(function() {
		arrow = $(this);
		target = $('#' + arrow.data('toggle'));
		target.toggle();
		if(target.is(':visible')) {
			arrow.attr('src', '/static/images/collapse.png');
		} else {
			arrow.attr('src', '/static/images/expand.png');
		}
	});
});
