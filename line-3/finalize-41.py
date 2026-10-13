"""One-time confined pigment composite; reads only declared workspace images.

Run before replacing the recovered record-40 wall. The installed image tool's
insert temporarily occupies the final wall-v22 path; it is replaced with the
complete wall in this command. No other image is saved.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('ancestor_formats', ROOT / 'line-3/finalize-31.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def main():
    directory = ROOT / 'artifacts/line-3'
    previous = (directory / 'wall.png').read_bytes()
    previous_hash = hashlib.sha256(previous).hexdigest()
    prior_record = json.loads((ROOT / 'dist/line-3/40.json').read_text())
    assert previous_hash == prior_record['image'].rsplit('/', 1)[1]
    assert len(list((ROOT / 'dist/line-3').glob('[0-9][0-9].json'))) == 40
    width, height, ancestors = F.thumbnail.png_rgb(previous)
    assert (width, height) == (1254, 1254)
    cutout = (directory / 'wall-v22.png').read_bytes()
    sw, sh, source = F.png_rgba(cutout)
    # Crop only transparent margins, retaining all actual generated pigment.
    visible = [(x,y) for y,row in enumerate(source) for x in range(sw) if row[4*x+3] > 20]
    assert visible
    sx0 = min(x for x,y in visible); sx1 = max(x for x,y in visible)+1
    sy0 = min(y for x,y in visible); sy1 = max(y for x,y in visible)+1
    del visible
    box = (65, 240, 220, 385)  # Open left stone; clear of ancestral marks.
    x0, y0, x1, y1 = box
    crop_w, crop_h = sx1-sx0, sy1-sy0
    scale = min((x1-x0)/crop_w, (y1-y0)/crop_h)
    tw, th = max(1,int(crop_w*scale)), max(1,int(crop_h*scale))
    px0, py0 = x0+(x1-x0-tw)//2, y0+(y1-y0-th)//2
    rows = [bytearray(row) for row in ancestors]
    changed = 0
    for dy in range(th):
        top, bottom = sy0+dy*crop_h//th, sy0+(dy+1)*crop_h//th
        for dx in range(tw):
            left, right = sx0+dx*crop_w//tw, sx0+(dx+1)*crop_w//tw
            sums = [0,0,0]; alpha=0
            count = (bottom-top)*(right-left)
            for sy in range(top,bottom):
                for sx in range(left,right):
                    r,g,b,a=source[sy][4*sx:4*sx+4]
                    alpha += a
                    for c,v in enumerate((r,g,b)): sums[c] += v*a
            if not alpha: continue
            opacity = min(185, alpha//count*3//4)
            if opacity < 10: continue
            pigment=[v//alpha for v in sums]
            at=3*(px0+dx)
            old=rows[py0+dy][at:at+3]
            new=bytes((old[c]*(255-opacity)+pigment[c]*opacity+127)//255 for c in range(3))
            if new!=old:
                rows[py0+dy][at:at+3]=new
                changed += 1
    assert changed > 1000, changed
    outside=sum(rows[y][3*x:3*x+3]!=ancestors[y][3*x:3*x+3]
                for y in range(height) for x in range(width)
                if not (x0<=x<x1 and y0<=y<y1))
    assert outside==0
    png=F.encode_rgb(width,height,rows)
    assert F.thumbnail.png_rgb(png)[2]==[bytes(row) for row in rows]
    jpg=F.thumbnail.jpeg(F.thumbnail.resize(width,height,rows))
    assert len(jpg)<100000
    digest=hashlib.sha256(png).hexdigest()
    for path in ('wall.png','wall-v22.png'): (directory/path).write_bytes(png)
    (ROOT/'dist/line-3/41.jpg').write_bytes(jpg)
    meaning='Pepe follows a cord of stones and gathers their provisions into one bowl.'
    record={'name':'The Sequence and the Bowl', 'image':'https://api.imd.fun/artifacts/'+digest,
            'attributes':[{'trait_type':k,'value':v} for k,v in [
                ('Cave','Base'),('Wall','Line 3'),('Number',41),
                ('Left behind','transaction-sequence'),('Meaning',meaning),
                ('One thing','Offline EIP-1559 transaction decoding')]]}
    (ROOT/'dist/line-3/41.json').write_text(json.dumps(record,indent=2)+'\n')
    review={'wall':{'paths':['artifacts/line-3/wall-v22.png','artifacts/line-3/wall.png'],
                    'width':width,'height':height,'format':'PNG','mode':'RGB',
                    'bytes':len(png),'sha256':digest},
            'thumbnail':{'path':'dist/line-3/41.jpg','width':512,'height':512,
                         'format':'JPEG','bytes':len(jpg)},
            'preservation':{'inheritedRecord':40,'inheritedSha256':previous_hash,
                            'editRectangleXYXY':list(box),'changedPixels':changed,
                            'changedPixelsOutsideRectangle':outside},
            'generatedInsert':{'format':'PNG','mode':'RGBA','width':sw,'height':sh,
                               'sourceSha256':hashlib.sha256(cutout).hexdigest(),
                               'sourceCropXYXY':[sx0,sy0,sx1,sy1]},
            'visualReview':{'reviewed':False},
            'unmetVisualRequirements':['Final visual review pending']}
    (ROOT/'line-3/round-41-review.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__=='__main__': main()
