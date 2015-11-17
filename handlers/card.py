import os
import sys

root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cards')

@get('card/(?P<card>[23456789JQKA][cdhs]|10[cdhs])')
def card(handler, card):
	#TODO Support the other card types on a per-user basis
	# For now, always use classic
	with open(os.path.join(root, 'classic', card + '.png')) as f:
		sys.stdout.write(f.read())
	handler.wrappers = False
	handler.contentType = 'image/png'

@get('card/back')
def cardBack(handler):
	card(handler, 'back')

#TODO This only exists for classic so far
@get('card/blank')
def cardBlank(handler):
	card(handler, 'blank')
