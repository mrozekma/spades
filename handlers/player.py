import os
from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO

@get('player/(?P<username>.+)/avatar')
def playerAvatar(handler, username):
	width = height = 64
	pt = 44

	# The frontend uses the username '-' for empty seats; we special-case the text and colors of that
	if username == '-':
		text = '?'
		r = g = b = 0
	else:
		text = username[:2].capitalize()
		bgHex = hex(hash(username))[2:][-6:].zfill(6) # Strip the 0x prefix and take the last 6 characters (if there aren't enough, left-pad with 0s)
		r, g, b = int(bgHex[0:2], 16), int(bgHex[2:4], 16), int(bgHex[4:6], 16)

	image = Image.new('RGB', (width, height), (r, g, b))
	draw = ImageDraw.Draw(image)
	font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'font.ttf'), pt)
	size = font.getsize(text)

	# I'm not sure why, but attempting to exactly center the text leaves it a little low
	# Offseting it by 10 seems to be around right, experimentally
	x, y = (width - size[0]) / 2, (height - size[1] - 10) / 2

	# Originally tried shadowing the text to make it visible, but don't really like how it looks
	# draw.text((x - 1, y - 1), text, font = font, fill = '#000')
	# draw.text((x + 1, y - 1), text, font = font, fill = '#000')
	# draw.text((x - 1, y + 1), text, font = font, fill = '#000')
	# draw.text((x + 1, y + 1), text, font = font, fill = '#000')

	# Instead choose whichever foreground color is more visible, white or black
	# There are probably still usernames that will be hard to read, but meh for now
	# http://stackoverflow.com/a/946734/309308
	brightness = r * .299 + g * .587 + b * .114
	fg = (0, 0, 0) if brightness > 160 else (255, 255, 255)
	draw.text((x, y), text, font = font, fill = fg)

	out = StringIO()
	image.save(out, 'png')
	print out.getvalue()
	handler.wrappers = None
	handler.contentType = 'image/png'
