from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path('assets')
OUT.mkdir(exist_ok=True)

BG = '#020817'
PANEL = '#07182d'
TEXT = '#f5f9ff'
MUTED = '#a8b8cd'
BLUE = '#2e9cff'
GREEN = '#25cc8b'
PURPLE = '#a435f0'

FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def vertical_gradient(size, top, bottom):
    from PIL import ImageColor
    w, h = size
    a = ImageColor.getrgb(top)
    b = ImageColor.getrgb(bottom)
    im = Image.new('RGB', size)
    px = im.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return im

def make_favicon(size, path):
    im = vertical_gradient((size, size), '#0b2949', BG)
    d = ImageDraw.Draw(im)
    pad = int(size * .12)
    d.rounded_rectangle((pad, pad, size-pad, size-pad), radius=int(size*.22), outline=BLUE, width=max(4, size//35), fill=PANEL)
    d.ellipse((int(size*.20), int(size*.20), int(size*.80), int(size*.80)), outline=GREEN, width=max(4, size//42))
    label = 'OV'
    f = font(int(size*.29), True)
    box = d.textbbox((0,0), label, font=f)
    tw, th = box[2]-box[0], box[3]-box[1]
    d.text(((size-tw)/2, (size-th)/2-int(size*.035)), label, font=f, fill=TEXT)
    im.save(path, 'PNG', optimize=True)

def make_og(filename, kicker, title, subtitle, accent):
    w, h = 1200, 630
    im = vertical_gradient((w, h), '#0a2039', BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((54, 48, 1146, 582), radius=34, fill=PANEL, outline='#203552', width=2)
    d.rounded_rectangle((54, 48, 72, 582), radius=9, fill=accent)
    d.ellipse((925, 70, 1130, 275), outline=accent, width=6)
    d.ellipse((980, 125, 1075, 220), outline=GREEN, width=4)
    d.text((105, 86), 'ORIVECTOR', font=font(34, True), fill=TEXT)
    d.text((105, 142), kicker, font=font(24, True), fill=accent)
    d.text((105, 225), title, font=font(58, True), fill=TEXT)
    d.text((105, 310), subtitle, font=font(27), fill=MUTED)
    chips = [('AWS', BLUE), ('NETWORK', GREEN), ('TOEIC', PURPLE)]
    x = 105
    for label, color in chips:
        f = font(21, True)
        box = d.textbbox((0,0), label, font=f)
        cw = box[2]-box[0] + 34
        d.rounded_rectangle((x, 457, x+cw, 505), radius=18, outline=color, width=2)
        d.text((x+17, 468), label, font=f, fill=TEXT)
        x += cw + 14
    d.text((105, 535), 'Free practice · Visual guides · Review', font=font(20), fill=MUTED)
    im.save(OUT / filename, 'PNG', optimize=True)

make_favicon(512, OUT / 'favicon-512.png')
make_favicon(180, OUT / 'apple-touch-icon.png')

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0b2949"/><stop offset="1" stop-color="#020817"/></linearGradient></defs>
<rect width="512" height="512" rx="112" fill="url(#g)"/>
<rect x="62" y="62" width="388" height="388" rx="108" fill="#07182d" stroke="#2e9cff" stroke-width="14"/>
<circle cx="256" cy="256" r="150" fill="none" stroke="#25cc8b" stroke-width="12"/>
<text x="256" y="294" text-anchor="middle" font-family="Arial,sans-serif" font-weight="800" font-size="150" fill="#f5f9ff">OV</text>
</svg>'''
(OUT / 'favicon.svg').write_text(svg, encoding='utf-8')

make_og('og-orivector.png', 'QUALIFICATION & ENGLISH STUDY', 'Learn smarter.', 'AWS · Network Specialist · TOEIC', BLUE)
make_og('og-aws.png', 'AWS CLOUD PRACTITIONER', 'AWS CLF-C02', 'Practice questions · Visual guides · Comparisons', BLUE)
make_og('og-network.png', 'NETWORK SPECIALIST', 'Network Specialist', 'Practice questions · Protocols · Architecture', GREEN)
make_og('og-toeic.png', 'ENGLISH STUDY', 'TOEIC', 'Vocabulary · Grammar · Part 5 practice', PURPLE)
print('Generated ORIVECTOR favicon and OG image assets.')
