from json import dumps as toJS, loads as fromJS
from json.encoder import JSONEncoder
import re

class Index(object):
	def __init__(self, name, chartOrParent):
		self._name = name
		if isinstance(chartOrParent, Index):
			self._parent = chartOrParent
			self._chart = self._parent._chart
		else:
			self._parent = None
			self._chart = chartOrParent

	def get(self):
		path = []
		next = self
		while next:
			path.append(next)
			next = next._parent
		val = self._chart._m
		path.reverse()
		for node in path:
			val = val[node._name]
		return val

	def __getitem__(self, k):
		return Index(k, self)

	def __setitem__(self, k, v):
		self._chart.set(self, k, v)

	def __getattr__(self, k):
		try:
			return object.__getattr__(self, k)
		except AttributeError:
			return self[k]

	def __setattr__(self, k, v):
		if k[0] == '_':
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def __enter__(self): return self
	def __exit__(self, type, value, traceback): pass

	def __str__(self):
		return "%s > %s" % (self._parent, self._name) if self._parent else self._name

	def createKeys(self):
		m = self._parent.createKeys() if self._parent else self._chart._m
		try:
			m[self._name]
		except: # If it doesn't exist ("in" checks fail for types like lists)
			m[self._name] = {}
		return m[self._name]

class raw(object):
	wrapper = 'RAW\x01\x02%s\x02\x01'

	def __init__(self, data):
		self.data = data

	def wrapped(self):
		return raw.wrapper % self.data

class CustomEncoder(JSONEncoder):
	# This is hacky as hell because the JSONEncoder interface is terrible and trying to specify your own encoding for a type is nigh-impossible
	# Instead we give a replacement string for raw objects, let JSONEncoder encode it as a string, and then replace it in Chart.js
	def default(self, o):
		return o.wrapped() if isinstance(o, raw) else super(CustomEncoder, self).default(o)

class Chart(object):
	def __init__(self, placeholder):
		self._m = {}
		self._id = placeholder
		self.credits.enabled = False

	def __getitem__(self, k):
		return Index(k, self)

	def __setitem__(self, k, v):
		self._m[k] = v

	def __getattr__(self, k):
		try:
			return object.__getattr__(self, k)
		except AttributeError:
			return self[k]

	def __setattr__(self, k, v):
		if k[0] == '_':
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def __enter__(self): return self
	def __exit__(self, type, value, traceback): pass

	def set(self, index, k, v):
		m = index.createKeys()
		if isinstance(v, dict):
			m[k].update(v)
		else:
			m[k] = v

	@staticmethod
	def include():
		# print "<script type=\"text/javascript\" src=\"/static/third-party/highcharts/js/highcharts.js\"></script>"
		print "<script type=\"text/javascript\" src=\"/static/third-party/highcharts/highstock/js/highstock.js\"></script>"
		print "<script type=\"text/javascript\" src=\"/static/third-party/highcharts/js/highcharts-more.js\"></script>"
		print "<script type=\"text/javascript\" src=\"/static/third-party/highcharts/js/modules/heatmap.js\"></script>"

	def js(self):
		print "$(%s).highcharts(" % toJS('#' + self._id),
		js = toJS(self._m, sort_keys = True, indent = 4, cls = CustomEncoder)
		# Unwrap raw data. See the comment above in CustomEncoder for the reason for this insanity
		js = re.sub(re.escape(toJS(raw.wrapper)).replace("\\%s", "(.*)"), lambda match: fromJS('"%s"' % match.group(1)), js)
		print js
		print ");"

	def placeholder(self):
		print "<div id=\"%s\" class=\"highchart\"></div>" % self._id

	def emplace(self, handler):
		handler.jsOnLoad(self.js)
		self.placeholder()
