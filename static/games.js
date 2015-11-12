function makeCalendar(events) {
	$('#calendar').fullCalendar({
		events: events,
		allDayDefault: true,
		eventOrder: 'start',
		eventColor: '#36c',
		eventClick: function(event, jsEvent, view) {
			document.location = '/games/' + event.log
		},
	});
}
