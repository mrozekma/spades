class Shim:
	@staticmethod
	def onUsername(username):
		# andy753421 sometimes joins from his phone
		if username == 'andydroid':
			return 'andy753421'

		return username

	@staticmethod
	def onPlayerColor(username):
		# [01:25:22] < loxodes> can I be orange?
		# [01:25:34] < necroyeti> ORANGE
		# [01:25:38] < mrozekma> do you want to be orange, or is this subtle social commentary?
		# [01:25:46] < loxodes> yes?
		if username == 'loxodes':
			return 255, 127, 0

		return None

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

		# The tie message: "It's tie! Playing an extra round!"
		if gameCon.logFilename == '20160119_014340.log' and offset == 19671:
			return "2016-01-28 05:10:47 | It's a tie! Playing an extra round!\n"

		return line

	@staticmethod
	def onEvent(gameCon, offset, event):
		# Problem where team names weren't saved. The team name in this event is 'dick sledge', but it should've been 'asdf'
		if gameCon.logFilename == '20160116_035923.log' and offset == 7483:
			event['team'] = 'asdf'
			return event

		# The first time we ever had a tied game, and the sudden death round didn't happen
		if gameCon.logFilename == '20160119_014340.log' and offset in (18804, 18862, 18896, 18955, 19030, 19071, 19104, 19162, 19196, 19196, 19255, 19255, 19330, 19371):
			return None

		# Game was aborted and then the bot went down without saving, and the game continued when it came back up
		if gameCon.logFilename == '20160217_071027.log' and offset == 215:
			return None

		# rhnoise was tricked into rampaging, then the game was reloaded
		if gameCon.logFilename == '20160520_004922.log' and offset == 14236:
			return None

		return event
