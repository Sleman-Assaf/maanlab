"""
Placeholder cover art for demo projects (Pillow only — no extra dependencies).
Every image is labelled "PLACEHOLDER" so it is never mistaken for real work.
"""
import math
import random
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

INK = (11, 10, 9)
SAND = (201, 183, 156)
BONE = (242, 238, 231)
ACCENT = (221, 107, 47)

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def _font(size):
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _radial_base(size, inner, outer, center=(0.5, 0.5)):
    w, h = size
    grad = Image.radial_gradient("L").resize((int(w * 1.6), int(h * 1.6)))
    left = int(w * 0.8 - center[0] * w)
    top = int(h * 0.8 - center[1] * h)
    grad = grad.crop((left, top, left + w, top + h))
    return Image.merge(
        "RGB",
        [grad.point(lambda p, c=i: int(inner[c] + (outer[c] - inner[c]) * p / 255)) for i in range(3)],
    )


def _glow(img, box, color, blur, strength=1.0):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse(box, fill=int(255 * strength))
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(Image.new("RGB", img.size, color), img, mask)


def _grain(img, amount=0.06):
    noise = Image.effect_noise(img.size, 40).convert("RGB")
    return Image.blend(img, noise, amount)


def _label(img, text):
    d = ImageDraw.Draw(img)
    w, h = img.size
    f = _font(max(18, w // 80))
    pad = w // 40
    tag = f"PLACEHOLDER  ·  {text.upper()}"
    bbox = d.textbbox((0, 0), tag, font=f)
    d.rounded_rectangle(
        [pad - 14, h - pad - (bbox[3] - bbox[1]) - 22, pad + (bbox[2] - bbox[0]) + 14, h - pad + 6],
        radius=40,
        fill=(11, 10, 9),
        outline=(90, 84, 76),
    )
    d.text((pad, h - pad - (bbox[3] - bbox[1]) - 12), tag, font=f, fill=SAND)
    return img


def film_frame(size, seed):
    rnd = random.Random(seed)
    w, h = size
    img = _radial_base(size, (38, 26, 18), INK, (rnd.uniform(0.35, 0.65), 0.55))
    sun_x = rnd.uniform(0.3, 0.7) * w
    horizon = h * rnd.uniform(0.56, 0.64)
    img = _glow(img, [sun_x - w * 0.45, horizon - h * 0.55, sun_x + w * 0.45, horizon + h * 0.35], (120, 60, 30), w // 12, 0.9)
    img = _glow(img, [sun_x - w * 0.08, horizon - w * 0.08, sun_x + w * 0.08, horizon + w * 0.08], ACCENT, w // 60)
    img = _glow(img, [sun_x - w * 0.035, horizon - w * 0.035, sun_x + w * 0.035, horizon + w * 0.035], (255, 214, 170), w // 120)
    d = ImageDraw.Draw(img)
    # ground plane
    d.rectangle([0, horizon, w, h], fill=(14, 12, 10))
    for i in range(1, 14):
        y = horizon + (h - horizon) * (i / 14) ** 1.8
        d.line([(0, y), (w, y)], fill=(40, 34, 29), width=1)
    # dunes
    pts = [(0, horizon + 4)]
    for x in range(0, w + 60, 60):
        pts.append((x, horizon - 18 - 40 * abs(math.sin(x / w * 5 + seed))))
    pts += [(w, horizon + 4)]
    d.polygon(pts, fill=(18, 15, 12))
    img = _grain(img, 0.05)
    d = ImageDraw.Draw(img)
    bar = int(h * 0.11)
    d.rectangle([0, 0, w, bar], fill=INK)
    d.rectangle([0, h - bar, w, h], fill=INK)
    f = _font(w // 90)
    d.text((w * 0.03, bar * 0.35), "● REC", font=f, fill=ACCENT)
    d.text((w * 0.83, bar * 0.35), "2.39 : 1", font=f, fill=SAND)
    return img


def node_graph(size, seed):
    rnd = random.Random(seed)
    w, h = size
    img = _radial_base(size, (30, 26, 22), INK, (0.55, 0.45))
    img = _glow(img, [w * 0.35, h * 0.2, w * 0.9, h * 0.9], (70, 38, 22), w // 10, 0.8)
    d = ImageDraw.Draw(img)
    for x in range(0, w, 40):
        for y in range(0, h, 40):
            d.point((x, y), fill=(60, 55, 50))
    nodes = [(rnd.uniform(0.08, 0.92) * w, rnd.uniform(0.12, 0.88) * h) for _ in range(18)]
    for i, a in enumerate(nodes):
        for b in nodes[i + 1 : i + 3]:
            d.line([a, b], fill=(95, 86, 76), width=2)
    path = sorted(rnd.sample(nodes, 6), key=lambda p: p[0])
    d.line(path, fill=ACCENT, width=5, joint="curve")
    for x, y in nodes:
        r = rnd.choice([8, 10, 14])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(24, 21, 18), outline=SAND, width=2)
    for x, y in path:
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=ACCENT)
        d.ellipse([x - 30, y - 30, x + 30, y + 30], outline=(120, 62, 32), width=2)
    return _grain(img, 0.04)


def interface(size, seed):
    rnd = random.Random(seed)
    w, h = size
    img = _radial_base(size, (34, 30, 26), INK, (rnd.uniform(0.3, 0.7), 0.4))
    d = ImageDraw.Draw(img)
    x0, y0 = int(w * rnd.uniform(0.06, 0.14)), int(h * rnd.uniform(0.1, 0.18))
    fw, fh = int(w * 0.62), int(h * 0.7)
    d.rounded_rectangle([x0, y0, x0 + fw, y0 + fh], radius=28, fill=(20, 18, 16), outline=(80, 74, 66), width=2)
    d.line([(x0, y0 + 70), (x0 + fw, y0 + 70)], fill=(60, 55, 50), width=2)
    for i, c in enumerate([(80, 74, 66), (80, 74, 66), ACCENT]):
        d.ellipse([x0 + 30 + i * 30, y0 + 26, x0 + 48 + i * 30, y0 + 44], fill=c)
    d.rounded_rectangle([x0 + 60, y0 + 140, x0 + int(fw * 0.5), y0 + 190], radius=8, fill=BONE)
    d.rounded_rectangle([x0 + 60, y0 + 206, x0 + int(fw * 0.38), y0 + 256], radius=8, fill=ACCENT)
    for i in range(3):
        d.rounded_rectangle([x0 + 60, y0 + 300 + i * 34, x0 + int(fw * (0.45 - i * 0.06)), y0 + 316 + i * 34], radius=8, fill=(90, 84, 76))
    img_box = [x0 + int(fw * 0.56), y0 + 130, x0 + fw - 60, y0 + int(fh * 0.62)]
    panel = _radial_base((img_box[2] - img_box[0], img_box[3] - img_box[1]), ACCENT, (40, 24, 16), (0.4, 0.4))
    img.paste(panel, img_box[:2])
    cw = (fw - 120 - 60) // 3
    for i in range(3):
        cx = x0 + 60 + i * (cw + 30)
        d.rounded_rectangle([cx, y0 + int(fh * 0.7), cx + cw, y0 + fh - 50], radius=18, fill=(30, 27, 24))
    mx, my = int(w * 0.66), int(h * 0.3)
    d.rounded_rectangle([mx, my, mx + int(w * 0.2), my + int(h * 0.6)], radius=40, fill=(20, 18, 16), outline=(80, 74, 66), width=2)
    d.rounded_rectangle([mx + 40, my + 90, mx + int(w * 0.2) - 40, my + 300], radius=20, fill=(60, 36, 22))
    d.rounded_rectangle([mx + 40, my + int(h * 0.6) - 110, mx + int(w * 0.2) - 40, my + int(h * 0.6) - 50], radius=30, fill=ACCENT)
    return _grain(img, 0.035)


def dashboard(size, seed):
    rnd = random.Random(seed)
    w, h = size
    img = _radial_base(size, (32, 28, 24), INK, (0.6, 0.5))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x, y = rnd.uniform(0.03, 0.3) * w, rnd.uniform(0.1, 0.8) * h
        d.rounded_rectangle([x, y, x + w * 0.12, y + h * 0.08], radius=10, fill=(24, 21, 18), outline=(70, 64, 58))
        for r in range(3):
            d.rounded_rectangle([x + 14, y + 16 + r * 18, x + w * 0.12 - rnd.randint(20, 80), y + 24 + r * 18], radius=4, fill=(80, 74, 66))
    px, py, pw, ph = int(w * 0.4), int(h * 0.14), int(w * 0.54), int(h * 0.72)
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=30, fill=(20, 18, 16), outline=(90, 84, 76), width=2)
    for i in range(3):
        tx = px + 40 + i * (pw - 80) // 3
        d.rounded_rectangle([tx, py + 50, tx + (pw - 80) // 3 - 24, py + 190], radius=16, fill=(30, 27, 24))
        d.rounded_rectangle([tx + 24, py + 120, tx + 150, py + 160], radius=6, fill=ACCENT if i == 1 else BONE)
    base_y = py + ph - 60
    bw = (pw - 120) // 12
    for i in range(12):
        bh = rnd.randint(60, int(ph * 0.45))
        bx = px + 60 + i * bw
        d.rectangle([bx, base_y - bh, bx + bw - 14, base_y], fill=ACCENT if i in (7, 8) else (90, 84, 76))
    for i in range(4):
        d.line([(int(w * 0.3), int(h * (0.3 + i * 0.14))), (px, int(py + 120 + i * 60))], fill=(120, 62, 32), width=2)
    return _grain(img, 0.04)


GENERATORS = {
    "ai_video": film_frame,
    "ai_automation": node_graph,
    "web_development": interface,
    "digital_transformation": dashboard,
}


def render(category: str, label: str, seed: int, size=(2400, 1500)) -> bytes:
    img = GENERATORS[category](size, seed)
    img = _label(img, label)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=88, optimize=True, progressive=True)
    return buffer.getvalue()
