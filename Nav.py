class Nav:
	def __init__(self):
		self.tabs = []

	def __setitem__(self, name, path):
		self.tabs.append({'name': name, 'path': path})

	def out(self, where, **kw):
		print "<nav class=\"navbar navbar-default\">"
		print "<ul class=\"nav navbar-nav\">"
		for tab in self.tabs:
			print "<li%s><a href=\"%s\">%s</a></li>" % (' class="active"' if tab['name'] == where else '', tab['path'] % kw, tab['name'].capitalize())
		print "</ul>"
		print "</nav>"
