from collections import OrderedDict

class Nav:
	# brand can be True, False, 'left', 'right', or a tuple containing one of those plus the text to display
	def __init__(self, brand = False):
		self.tabs = OrderedDict()
		if isinstance(brand, tuple):
			brand, self.brandText = brand
		else:
			self.brandText = ''
		self.brandAlignment = 'left' if brand in (True, 'left') else 'right' if brand == 'right' else None

	def __setitem__(self, name, path):
		if isinstance(name, tuple):
			self.tabs[name[0]]['subtabs'][name[1]] = {'path': path, 'desc': name[1].title()}
		else:
			self.tabs[name] = {'path': path, 'desc': name.title(), 'subtabs': OrderedDict()}

	def out(self, where, **kw):
		print "<nav class=\"navbar navbar-default\">"
		if self.brandAlignment == 'left':
			print "<div class=\"navbar-header\"><div class=\"navbar-brand\">%s</div></div>" % self.brandText
		elif self.brandAlignment == 'right':
			print "<div class=\"navbar-right\"><div class=\"navbar-brand\">%s</div>&nbsp;&nbsp;</div>" % self.brandText
		print "<ul class=\"nav navbar-nav\">"
		for name, tab in self.tabs.iteritems():
			# Subtabs are only shown if we're on that tab (since the dropdown disables clicking)
			if tab['subtabs'] and name == where:
				print "<li class=\"active\">"
				print "<a href=\"#\" class=\"dropdown-toggle\" data-toggle=\"dropdown\">%s <span class=\"caret\"></span></a>" % tab['desc']
				print "<ul class=\"dropdown-menu\">"
				for subname, subtab in tab['subtabs'].iteritems():
					print "<li><a href=\"%s\">%s</a></li>" % (subtab['path'] % kw, subtab['desc'])
				print "</ul>"
				print "</li>"
			else:
				print "<li%s><a href=\"%s\">%s</a></li>" % (' class="active"' if name == where else '', tab['path'] % kw, tab['desc'])
		print "</ul>"
		print "</nav>"
