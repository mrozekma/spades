import time

from rorn.utils import *

def ensureIter(l):
	return l if isinstance(l, list) or isinstance(l, tuple) else [l]

def dtToJSTime(dt):
	return int(time.mktime(dt.timetuple()) * 1000)
