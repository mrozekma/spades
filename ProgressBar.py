from __future__ import division

from rorn.ResponseWriter import ResponseWriter

from utils import *

inf = float('inf')

class ProgressBar:
	# zeroDivZero means the progress should be 0 if amt == total == 0. It will be 100 if False. In either case, it will be infinity if amt > 0
	# style is a map of percentages to styles to apply to div.progress-current; the highest percentage <= this bar's percentage will be applied
	def __init__(self, amt, total, label = None, url = None, pcnt = None, zeroDivZero = True, style = None):
		self.label = label
		self.url = url
		self.amt = amt
		self.total = total
		if pcnt:
			self.pcnt = pcnt
		elif total == 0:
			self.pcnt = inf if amt > 0 else 0 if zeroDivZero else 100
		else:
			self.pcnt = amt / total * 100

		if isinstance(style, dict):
			if amt == 0 and total == 0 and None in style:
				self.cls = style[None]
			else:
				topPcnt = maxOr(filter(lambda p: p is not None and p <= self.pcnt, style.keys()))
				self.cls = style[topPcnt] if topPcnt in style else None
		elif isinstance(style, str):
			self.cls = style
		else:
			self.cls = ''


		if self.url and not self.label:
			raise ValueError("Can't have a URL without a label")

	def __str__(self):
		w = ResponseWriter()
		if self.label:
			if self.url:
				print "<a href=\"%s\">%s</a>  " % (self.url, self.label)
			else:
				print "%s " % self.label
		print "<div class=\"progress-total\" style=\"position: relative; top: 5px\">"
		if self.pcnt > 0:
			print "<div class=\"progress-current%s\" style=\"width: %d%%;\">" % (" %s" % self.cls, min(self.pcnt, 100))
		print "<span class=\"progress-text\">%d/%d <span class=\"progress-percentage\">(%s%%)</span></span>" % (self.amt, self.total, '&#8734;' if self.pcnt == inf else "%d" % self.pcnt)
		if self.pcnt > 0:
			print "</div>"
		print "</div>"
		return w.done().replace("\n", "")
