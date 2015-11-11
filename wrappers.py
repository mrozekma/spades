from json import dumps as toJS

def header(handler):
	if handler.pageTitle is None:
		title = bodyTitle = 'Spades'
	else:
		bodyTitle = handler.pageTitle
		title = "%s - Spades" % bodyTitle

	print "<!DOCTYPE html>"
	print "<html>"
	print "<head>"
	print "<title>%s</title>" % title
	print "<link rel=\"shortcut icon\" href=\"/static/images/favicon.ico\">"

	# jQuery
	print "<script src=\"//ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js\"></script>"
	print "<link rel=\"stylesheet\" href=\"//ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/themes/smoothness/jquery-ui.css\" />"
	print "<script src=\"//ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/jquery-ui.min.js\"></script>"

	# Bootstrap
	print "<link rel=\"stylesheet\" href=\"//maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css\" integrity=\"sha512-dTfge/zgoMYpP7QbHy4gWMEGsbsdZeCXz7irItjcC3sPUFtf0kuFbDz/ixG7ArTxmDjLXDmezHubeNikyKGVyQ==\" crossorigin=\"anonymous\">"
	print "<link rel=\"stylesheet\" href=\"//maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css\" integrity=\"sha384-aUGj/X2zp5rLCbBxumKTCw2Z50WgIr1vs/PFN4praOTvYXWlVyh2UtNUU0KAUhAX\" crossorigin=\"anonymous\">"
	print "<script src=\"//maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js\" integrity=\"sha512-K1qjQ+NcF2TYO/eI3M6v8EiNYZfA95pQumfvcVrTHtwQVDG+aHRqLi/ETn2uB+1JqwYqVG3LIvdm9lj6imS/pQ==\" crossorigin=\"anonymous\"></script>"

	if handler.wrapperData['jsOnReady']:
		print "<script type=\"text/javascript\">"
		print "$(document).ready(function() {"
		for js in handler.wrapperData['jsOnReady']:
			print "    %s" % js
		print "});"
		print "</script>"

	# Less
	print "<link rel=\"stylesheet/less\" type=\"text/css\" href=\"/static/style.less\">"
	print "<script type=\"text/javascript\">"
	print "less = %s;" % toJS({'env': 'production', 'async': False, 'dumpLineNumbers': 'comments'})
	print "</script>"
	print "<script src=\"/static/third-party/less.js\" type=\"text/javascript\"></script>"

	print "</head>"
	print "<body>"
	print "<div class=\"content\">"
	print "%s" % bodyTitle

def footer(handler):
	print "</div>"
	print "</body>"
	print "</html>"
