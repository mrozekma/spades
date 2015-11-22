class Nav:
	# brand can be True, False, 'left', 'right', or a tuple containing one of those plus the text to display
	def __init__(self, brand = False):
		self.tabs = []
		if isinstance(brand, tuple):
			brand, self.brandText = brand
		else:
			self.brandText = ''
		self.brandAlignment = 'left' if brand in (True, 'left') else 'right' if brand == 'right' else None

	def __setitem__(self, name, path):
		self.tabs.append({'name': name, 'path': path})

	def out(self, where, **kw):
		print "<nav class=\"navbar navbar-default\">"
		if self.brandAlignment == 'left':
			print "<div class=\"navbar-header\"><div class=\"navbar-brand\">%s</div></div>" % self.brandText
		elif self.brandAlignment == 'right':
			print "<div class=\"navbar-right\"><div class=\"navbar-brand\">%s</div>&nbsp;&nbsp;</div>" % self.brandText
		print "<ul class=\"nav navbar-nav\">"
		for tab in self.tabs:
			print "<li%s><a href=\"%s\">%s</a></li>" % (' class="active"' if tab['name'] == where else '', tab['path'] % kw, tab['name'].title())
		print "</ul>"
		print "</nav>"
