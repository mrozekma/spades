class Shim:
	@staticmethod
	def onLogLoad(log):
		# This is the first log created when logging was first added to the bot. It starts mid-game, so we skip it
		if log == '20150823_201536.log':
			return None

		# These are logs from when .fliptable was added and a "USER goes on a rampage" message was temporarily outputted. Nothing else happens in the games, so we skip them
		if log in ('20160202_072421.log', '20160202_072833.log', '20160202_073116.log'):
			return None

		return log

	@staticmethod
	def onGameCon(gameCon):
		return gameCon

	@staticmethod
	def onLine(gameCon, offset, line):
		# The original bid recap message: "USER/USER bid BID, USER/USER bid BID, BAGS bags remain"
		if gameCon.logFilename == '20151103_042128.log' and offset == 47398:
			return None

		# Buggy/old lines from the first draft of team names
		if gameCon.logFilename == '20160116_035923.log' and offset in (355, 407, 475, 1340, 1398):
			return None

		return line

	@staticmethod
	def onEvent(gameCon,offset, event):
		# Problem where team names weren't saved. The team name in this event is 'dick sledge', but it should've been 'asdf'
		if gameCon.logFilename == '20160116_035923.log' and offset == 7483:
			event['team'] = 'asdf'
			return event

		return event
