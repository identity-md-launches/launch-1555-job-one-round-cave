"""Add one bounded earth-pigment proof-bundle mark to the inherited Line 1 wall."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WALL = ROOT / 'artifacts/line-1/wall-v22.png'
JPEG = ROOT / 'dist/line-1/41.jpg'
RECORD = ROOT / 'dist/line-1/41.json'
REVIEW = ROOT / 'line-1/wall-review-41.json'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distance_to_segment(x, y, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    if not length:
        return ((x - ax) ** 2 + (y - ay) ** 2) ** .5
    t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / length))
    return ((x - (ax + t * dx)) ** 2 + (y - (ay + t * dy)) ** 2) ** .5


def pigment(local_x, local_y):
    """A compact hand-drawn cord with three worn pebbles; never text or a hand."""
    stones = ((31, 58, 18, 15, (151, 61, 31)),
              (95, 59, 16, 18, (220, 208, 173)),
              (61, 84, 18, 14, (183, 125, 42)))
    for cx, cy, rx, ry, tone in stones:
        ellipse = ((local_x-cx)/rx) ** 2 + ((local_y-cy)/ry) ** 2
        if ellipse <= 1:
            if (local_x * 19 + local_y * 13) % 17 not in (0, 1):
                return tone, .70
    cord = ((31, 46), (28, 20), (57, 13), (85, 29), (96, 45),
            (94, 53), (62, 68), (32, 51))
    for a, b in zip(cord, cord[1:]):
        if distance_to_segment(local_x, local_y, a, b) <= 2.2:
            if (local_x * 11 + local_y * 7) % 13:
                return (40, 29, 21), .76
    for a, b in (((32, 57), (58, 78)), ((92, 57), (64, 80))):
        if distance_to_segment(local_x, local_y, a, b) <= 1.8:
            return (40, 29, 21), .72
    return None


def main():
    png = load('png_helpers', ROOT / 'line-1/finalize-35.py')
    thumb = load('thumbnail', ROOT / 'gathering/make_thumbnail.py')
    original = WALL.read_bytes()
    old_digest = hashlib.sha256(original).hexdigest()
    previous = json.loads((ROOT / 'dist/line-1/40.json').read_text())
    assert old_digest == previous['image'].rsplit('/', 1)[1]
    assert not RECORD.exists()
    width, height, channels, rows = png.decode_png(original)
    assert (width, height, channels) == (1254, 1254, 3)
    left, top, patch_width, patch_height = 110, 680, 130, 110
    changed = 0
    for y in range(patch_height):
        for x in range(patch_width):
            mark = pigment(x, y)
            if not mark:
                continue
            tone, strength = mark
            at = (left + x) * 3
            before = rows[top+y][at:at+3]
            after = bytes(round(before[c] * (1-strength) + tone[c] * strength)
                          for c in range(3))
            if after != before:
                rows[top+y][at:at+3] = after
                changed += 1
    assert changed > 400
    final = png.encode_rgb(rows, width, height)
    _, _, _, before_rows = png.decode_png(original)
    fw, fh, fc, after_rows = png.decode_png(final)
    actual_changed = outside = 0
    for y in range(height):
        for x in range(width):
            offset = x * 3
            if before_rows[y][offset:offset+3] != after_rows[y][offset:offset+3]:
                actual_changed += 1
                if not (left <= x < left + patch_width and top <= y < top + patch_height):
                    outside += 1
    assert (fw, fh, fc) == (1254, 1254, 3)
    assert actual_changed == changed and outside == 0
    jpeg = thumb.jpeg(thumb.resize(width, height, after_rows))
    assert len(jpeg) < 100000
    WALL.write_bytes(final)
    JPEG.write_bytes(jpeg)
    digest = hashlib.sha256(final).hexdigest()
    meaning = 'Three pebbles tied by one cord keep a proof bundle together for another reader.'
    metadata = {'name': 'The Bound Three',
                'image': 'https://api.imd.fun/artifacts/' + digest,
                'attributes': [{'trait_type': k, 'value': v} for k, v in (
                    ('Cave', 'Base'), ('Wall', 'Line 1'), ('Number', 41),
                    ('Left behind', 'proof-bundle-manifest'), ('Meaning', meaning),
                    ('One thing', 'portable live Ethereum state snapshots'))]}
    RECORD.write_text(json.dumps(metadata, indent=2) + '\n')
    review = {'source_record': 40, 'record_number': 41,
              'source_sha256': old_digest, 'wall_sha256': digest,
              'png_dimensions': [width, height], 'png_format': '8-bit RGB PNG',
              'png_bytes': len(final), 'jpeg_dimensions': [512, 512],
              'jpeg_format': 'baseline JPEG', 'jpeg_bytes': len(jpeg),
              'addition_rectangle': [left, top, patch_width, patch_height],
              'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
              'new_hands_or_stencils': 0,
              'visual_review': 'Pending final PNG and JPEG inspection.',
              'unmet_visual_requirements': [
                  'Inherited rock looks photographic and was preserved to retain the cave.']}
    REVIEW.write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
