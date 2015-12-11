import time

from rorn.utils import *

def ensureIter(l):
	return l if isinstance(l, list) or isinstance(l, tuple) else [l]

def dtToJSTime(dt):
	return int(time.mktime(dt.timetuple()) * 1000)

def zeroes(keys):
	return {k: 0 for k in keys}

def sumByKey(maps, extraMap = {}):
	rtn = extraMap.copy()
	for m in maps:
		for k in m:
			rtn[k] = rtn.get(k, 0) + m[k]
	return rtn
