"""
Generates the texture/typography assets used by qaed_al_fursan.py.

    python3 make_assets.py            (needs: pillow uharfbuzz fonttools shapely)

Outputs (in ./assets):
    arabic_title.json   correctly shaped outlines of "قائد الفرسان" (HarfBuzz + Amiri Bold)
    label_mask.png      2048 px front-label foil mask (white = gold foil)
    box_mask.png        front-panel foil mask for the retail box

The label is a procedural stand-in in the style of the storyboard (black and
gold interlocking geometric bands, horse emblem, Arabic + Latin name). To use
the real artwork, replace label_mask.png with a high-res scan of the original
label converted to black (lacquer) / white (gold foil), same file name.
horse_emblem.png comes from:  blender -b -P qaed_al_fursan.py -- --emblem
"""
import json
import os
import random

import uharfbuzz as hb
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
AR_FONT = os.path.join(A, "fonts", "Amiri-Bold.ttf")
EN_FONT = os.path.join(A, "fonts", "EBGaramond12-Regular.otf")
TITLE_AR = "قائد الفرسان"


# ---------------------------------------------------------------------------
def flatten(rec, steps=10):
    """RecordingPen ops -> list of closed polylines."""
    rings, cur, last = [], [], None

    def quad(p0, p1, p2):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])
                for t in (i / steps for i in range(1, steps + 1))]

    def cubic(p0, p1, p2, p3):
        out = []
        for i in range(1, steps + 1):
            t = i / steps
            mt = 1 - t
            out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                        mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
        return out
    for op, args in rec.value:
        if op == "moveTo":
            cur = [args[0]]; last = args[0]
        elif op == "lineTo":
            cur.append(args[0]); last = args[0]
        elif op == "qCurveTo":
            pts = list(args)
            if pts[-1] is None:          # implied on-curve closed contour
                pts = pts[:-1]
            # split TrueType implied on-curve points
            p0 = last
            for i in range(len(pts) - 1):
                c = pts[i]
                end = pts[i + 1] if i == len(pts) - 2 else ((pts[i][0] + pts[i + 1][0]) / 2,
                                                            (pts[i][1] + pts[i + 1][1]) / 2)
                cur += quad(p0, c, end)
                p0 = end
            last = p0
        elif op == "curveTo":
            cur += cubic(last, *args); last = args[-1]
        elif op in ("closePath", "endPath"):
            if len(cur) > 2:
                rings.append(cur)
            cur = []
    return rings


def shaped_outline(text, font_path):
    """HarfBuzz-shaped text -> shapely (multi)polygon in font units."""
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"liga": True, "calt": True})
    tt = TTFont(font_path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    glyph_shapes = []
    x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = DecomposingRecordingPen(gs)
        gs[order[info.codepoint]].draw(pen)
        ox, oy = x + pos.x_offset, pos.y_offset
        outer, holes = [], []
        for ring in flatten(pen):
            pts = [(px + ox, py + oy) for px, py in ring]
            area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
            pg = Polygon(pts).buffer(0)
            if pg.is_empty:
                continue
            # TrueType: outer contours clockwise (negative area), counters anticlockwise
            (outer if area2 < 0 else holes).append(pg)
        if outer:
            g = unary_union(outer)
            if holes:
                g = g.difference(unary_union(holes))
            glyph_shapes.append(g)
        x += pos.x_advance
    return unary_union(glyph_shapes)


def shape_rings(shape):
    geoms = getattr(shape, "geoms", [shape])
    rings = []
    for g in geoms:
        rings.append(list(g.exterior.coords)[:-1])
        for h in g.interiors:
            rings.append(list(h.coords)[:-1])
    return geoms, rings


def raster_shape(shape, size, box, img=None, fill=255):
    """Draw a shapely shape into box=(x0,y0,x1,y1) of an L image, aspect kept."""
    minx, miny, maxx, maxy = shape.bounds
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / (maxx - minx), bh / (maxy - miny))
    ox = box[0] + (bw - (maxx - minx) * s) / 2
    oy = box[1] + (bh - (maxy - miny) * s) / 2
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for g in getattr(shape, "geoms", [shape]):
        d.polygon([(ox + (x - minx) * s, oy + (maxy - y) * s) for x, y in g.exterior.coords], fill=255)
        for h in g.interiors:
            d.polygon([(ox + (x - minx) * s, oy + (maxy - y) * s) for x, y in h.coords], fill=0)
    if img is not None:
        img.paste(fill if img.mode != "L" or not isinstance(fill, tuple) else 255, mask=mask)
    return mask


# ---------------------------------------------------------------------------
def arabic_json(shape):
    geoms, rings = shape_rings(shape)
    minx, miny, maxx, maxy = shape.bounds
    data = {"text": TITLE_AR, "font": "Amiri Bold (OFL)", "width": maxx - minx,
            "height": maxy - miny, "ymin": miny,
            "rings": [[(x - minx, y) for x, y in r] for r in rings]}
    # store x relative to left edge so the Blender side can centre it
    data["rings"] = [[(round(x, 2), round(y, 2)) for x, y in r] for r in data["rings"]]
    json.dump(data, open(os.path.join(A, "arabic_title.json"), "w"))
    print("arabic_title.json:", len(rings), "rings")


def meander_pattern(N, cells, band, core, seed=11):
    """Continuous interlocking gold bands: a Truchet lattice whose corner
    pieces are rounded squares (superellipse), drawn as twin gold lines."""
    import math
    rnd = random.Random(seed)
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    c = N / cells
    m = c / 2

    def corner(cx, cy, a0):
        # quarter superellipse of radius m around the cell corner (cx, cy)
        pts = []
        for i in range(17):
            t = a0 + (math.pi / 2) * i / 16
            ct, st = math.cos(t), math.sin(t)
            pts.append((cx + m * math.copysign(abs(ct) ** 0.35, ct),
                        cy + m * math.copysign(abs(st) ** 0.35, st)))
        return pts
    paths = []
    for gy in range(cells):
        for gx in range(cells):
            x0, y0 = gx * c, gy * c
            if rnd.random() < 0.5:   # arcs around top-left and bottom-right corners
                paths += [corner(x0, y0, 0.0), corner(x0 + c, y0 + c, math.pi)]
            else:                    # around top-right and bottom-left
                paths += [corner(x0 + c, y0, math.pi / 2), corner(x0, y0 + c, -math.pi / 2)]
    for p in paths:
        d.line(p, fill=255, width=band, joint="curve")
    for p in paths:
        d.line(p, fill=0, width=core, joint="curve")
    return img


def emblem_mask(size):
    p = os.path.join(A, "horse_emblem.png")
    if not os.path.exists(p):
        return None
    a = Image.open(p).getchannel("A").point(lambda v: 255 if v > 128 else 0)
    bbox = a.getbbox()
    a = a.crop(bbox)
    a.thumbnail(size, Image.LANCZOS)
    # gold silhouette with an inset black contour line (engraved look)
    inner = a.filter(ImageFilter.MinFilter(9))
    inner2 = inner.filter(ImageFilter.MinFilter(9))
    line = ImageChops.subtract(inner, inner2)
    return ImageChops.subtract(a, line)


def build_label(ar_shape, N=2048):
    img = Image.new("L", (N, N), 0)
    pat = meander_pattern(N, 7, 78, 26)
    # clear zones: emblem (upper right) and title cartouche (lower left)
    keep = Image.new("L", (N, N), 255)
    kd = ImageDraw.Draw(keep)
    kd.rounded_rectangle((int(N * 0.30), int(N * 0.12), int(N * 0.92), int(N * 0.62)), 60, fill=0)
    kd.rounded_rectangle((int(N * 0.06), int(N * 0.66), int(N * 0.70), int(N * 0.92)), 40, fill=0)
    img.paste(pat, mask=keep)
    d = ImageDraw.Draw(img)
    # gold frame (double rule)
    d.rectangle((24, 24, N - 24, N - 24), outline=255, width=34)
    d.rectangle((84, 84, N - 84, N - 84), outline=255, width=12)
    # cartouche rules
    d.rounded_rectangle((int(N * 0.06), int(N * 0.66), int(N * 0.70), int(N * 0.92)), 40, outline=255, width=10)
    em = emblem_mask((int(N * 0.58), int(N * 0.46)))
    if em is not None:
        img.paste(255, (int(N * 0.33), int(N * 0.14)), mask=em)
    raster_shape(ar_shape, (N, N), (int(N * 0.10), int(N * 0.68), int(N * 0.66), int(N * 0.83)), img)
    f = ImageFont.truetype(EN_FONT, int(N * 0.045))
    txt = "QAED  AL  FURSAN"
    w = d.textlength(txt, font=f)
    d.text((int(N * 0.38) - w / 2, int(N * 0.845)), txt, font=f, fill=255)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img.save(os.path.join(A, "label_mask.png"))
    print("label_mask.png")
    return img


def build_box(label, ar_shape):
    W, H = 1700, 2006            # same aspect as the box front (1.0 x 1.18)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    d.rectangle((30, 30, W - 30, H - 30), outline=255, width=14)
    lab = label.resize((1300, 1300), Image.LANCZOS)
    img.paste(lab, ((W - 1300) // 2, 420))
    raster_shape(ar_shape, (W, H), (W * 0.22, 110, W * 0.78, 300), img)
    f = ImageFont.truetype(EN_FONT, 64)
    for txt, y in (("QAED AL FURSAN", 1790), ("EAU DE PARFUM", 1880)):
        t = " ".join(txt)
        w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=255)
    img.save(os.path.join(A, "box_mask.png"))
    print("box_mask.png")


LABEL_CROP = (866, 1200, 1652, 1986)   # label square in assets/reference/bottle_photo.jpg


def build_photo_label():
    """Front label cut straight from the supplied product photo (exact artwork)."""
    p = os.path.join(A, "reference", "bottle_photo.jpg")
    if not os.path.exists(p):
        return None
    lab = Image.open(p).convert("RGB").crop(LABEL_CROP).resize((2048, 2048), Image.LANCZOS)
    lab.save(os.path.join(A, "label_photo.png"))
    print("label_photo.png")
    return lab


def build_photo_box(lab, ar_shape):
    """Retail box front (colour): black board, gold rules, the real label art,
    Arabic name and category, laid out like the storyboard end pack."""
    W, H = 1700, 2006
    gold = (212, 175, 55)
    img = Image.new("RGB", (W, H), (6, 6, 6))
    d = ImageDraw.Draw(img)
    d.rectangle((30, 30, W - 30, H - 30), outline=gold, width=10)
    img.paste(lab.resize((1300, 1300), Image.LANCZOS), ((W - 1300) // 2, 400))
    raster_shape(ar_shape, (W, H), (W * 0.25, 110, W * 0.75, 290), img, fill=gold)
    f = ImageFont.truetype(EN_FONT, 62)
    for txt, y in (("QAED AL FURSAN", 1780), ("EAU DE PARFUM", 1875)):
        t = " ".join(txt)
        w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=gold)
    img.save(os.path.join(A, "box_photo.png"))
    print("box_photo.png")


if __name__ == "__main__":
    shape = shaped_outline(TITLE_AR, AR_FONT)
    arabic_json(shape)
    lab = build_label(shape)
    build_box(lab, shape)
    photo = build_photo_label()
    if photo is not None:
        build_photo_box(photo, shape)
