#!/usr/bin/env python3
"""Composite generated earth pigment on a small open patch; no extra images."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

spec = importlib.util.spec_from_file_location('thumbnail', 'gathering/make_thumbnail.py')
thumb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumb)
base_path = Path('artifacts/line-2/wall.png')
output_path = Path('artifacts/line-2/wall-v22.png')
base_bytes = base_path.read_bytes()
record = json.loads(Path('dist/line-2/40.json').read_text())
assert hashlib.sha256(base_bytes).hexdigest() == record['image'].rsplit('/', 1)[1]
w, h, base = thumb.png_rgb(base_bytes)
sw, sh, source = thumb.png_rgb(output_path.read_bytes())
assert (w, h) == (1254, 1254)
# Identify pigment against the tool's pure white paper, entirely in memory.
points = [(x, y) for y in range(sh) for x in range(sw)
          if min(source[y][x*3:x*3+3]) < 180]
left = min(x for x, y in points)
right = max(x for x, y in points)+1
top = min(y for x, y in points)
bottom = max(y for x, y in points)+1
x0, y0, tw, th = 475, 846, 160, 78
rows = [bytearray(row) for row in base]
for ty in range(th):
    ya = top + ty*(bottom-top)//th
    yb = max(ya+1, top+(ty+1)*(bottom-top)//th)
    for tx in range(tw):
        xa = left + tx*(right-left)//tw
        xb = max(xa+1, left+(tx+1)*(right-left)//tw)
        weights, colors = 0.0, [0.0]*3
        count = (xb-xa)*(yb-ya)
        for sy in range(ya, yb):
            for sx in range(xa, xb):
                r, g, b = source[sy][sx*3:sx*3+3]
                if min(r,g,b) >= 210:
                    continue
                alpha = 0.88*(255-min(r,g,b))/255
                if r > 1.55*max(g,1) and r-g > 30:
                    pigment = (150,58,27)
                elif r-g > 25:
                    pigment = (177,119,43)
                else:
                    pigment = (42,31,20)
                weights += alpha
                for c in range(3):
                    colors[c] += alpha*pigment[c]
        if weights:
            alpha = weights/count
            offset = (x0+tx)*3
            for c in range(3):
                old = rows[y0+ty][offset+c]
                rows[y0+ty][offset+c] = round(old*(1-alpha)+colors[c]/count)
changed = sum(base[y][x*3:x*3+3] != rows[y][x*3:x*3+3]
              for y in range(h) for x in range(w))
outside = sum(base[y][x*3:x*3+3] != rows[y][x*3:x*3+3]
              for y in range(h) for x in range(w)
              if not (x0 <= x < x0+tw and y0 <= y < y0+th))
assert changed > 0 and outside == 0

def chunk(tag, body):
    return struct.pack('>I',len(body))+tag+body+struct.pack('>I',zlib.crc32(tag+body))
png = (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
       +chunk(b'IDAT',zlib.compress(b''.join(b'\x00'+bytes(row) for row in rows),9))
       +chunk(b'IEND',b''))
# Overwrite the generated motif with the entire finished wall; retain no insert.
output_path.write_bytes(png)
base_path.write_bytes(png)
jpg = thumb.jpeg(thumb.resize(w,h,rows))
assert len(jpg) < 100000
Path('dist/line-2/41.jpg').write_bytes(jpg)
review = {'number':41,'source_sha256':hashlib.sha256(base_bytes).hexdigest(),
          'wall_sha256':hashlib.sha256(png).hexdigest(),
          'wall':{'format':'PNG','dimensions':[w,h],'color':'8-bit RGB','bytes':len(png)},
          'preview':{'format':'baseline JPEG','dimensions':[512,512],'bytes':len(jpg)},
          'addition_rectangle':[x0,y0,x0+tw,y0+th],
          'rectangle_upper_bounds':'exclusive','changed_pixels':changed,
          'changed_pixels_outside_rectangle':outside,
          'visual_review':'pending','unmet_visual_requirements':[]}
Path('line-2/wall-review-41.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(review,indent=2))
