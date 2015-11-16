from rorn.utils import *

def ensureIter(l):
	return l if isinstance(l, list) or isinstance(l, tuple) else [l]
