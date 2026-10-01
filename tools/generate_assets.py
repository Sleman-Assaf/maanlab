"""
Generate the bundled PLACEHOLDER assets (development tool, not used at runtime).

    pip install numpy imageio-ffmpeg     # dev-only extras
    python tools/generate_assets.py

Outputs (all placeholders — replace with real assets):
  static/img/hero/placeholder-object.{png,webp}   hero technology object (transparent)
  static/img/brand/og-default.jpg                  social share image
  static/img/brand/apple-touch-icon.png
  static/img/brand/contours.svg                    Ma'an contour-line visual
  static/video/showreel-placeholder.{mp4,webp}     2.39:1 abstract film loop + poster
  static/video/clip-sand.{mp4,webp}, clip-night.{mp4,webp}   16:10 loops for demo projects
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
FONT_BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
FONT_REG = Path("C:/Windows/Fonts/segoeui.ttf")


def font(size, bold=True):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default(size=size)


# ---------------------------------------------------------------------------
# Hero object: a matte ceramic "puck" device with a glass lens and ring light.
# ---------------------------------------------------------------------------
def render_hero_object(size=1400, ss=2):
    n = size * ss
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) / n
    cx, cy_top = 0.5, 0.40
    R, k, H = 0.34, 0.36, 0.17

    u = (xs - cx) / R
    w = (ys - cy_top) / R
    rr = np.sqrt(u**2 + (w / k) ** 2)
    top = rr <= 1.0

    inside_u = np.abs(u) <= 1.0
    front = np.sqrt(np.clip(1 - u**2, 0, 1))
    y_bottom = cy_top + H + R * k * front
    side = inside_u & (ys >= cy_top) & (ys <= y_bottom) & ~top

    rgb = np.zeros((n, n, 3), np.float32)
    alpha = (top | side).astype(np.float32)

    # --- Side band: anodised warm titanium, cylinder shading ---------------
    nz = front
    light = np.array([-0.55, 0.25, 0.80], np.float32)
    light /= np.linalg.norm(light)
    diffuse = np.clip(u * light[0] + nz * light[2], 0, 1)
    v = np.clip((ys - (cy_top + R * k * front)) / H, 0, 1)  # 0 at top rim → 1 at base
    base_side = np.array([0.50, 0.45, 0.40], np.float32)
    spec = np.exp(-(((u + 0.55) / 0.10) ** 2)) * 0.55 + np.exp(-(((u - 0.78) / 0.05) ** 2)) * 0.18
    brushed = (np.sin(xs * n * 0.9) * 0.012)
    shade = 0.28 + 0.72 * diffuse
    shade = shade * (1.0 - 0.45 * v**1.6)
    side_col = base_side[None, None, :] * shade[..., None] + spec[..., None] * np.array([1.0, 0.95, 0.88]) + brushed[..., None]
    # thin groove (seam) on the band
    groove = np.exp(-(((v - 0.62) / 0.018) ** 2)) * 0.35
    side_col = side_col * (1 - groove[..., None])
    # chamfer highlight just under the top rim
    chamfer = np.exp(-((v / 0.035) ** 2)) * (0.35 + 0.65 * diffuse)
    side_col += chamfer[..., None] * np.array([0.55, 0.5, 0.44])
    rgb = np.where(side[..., None], side_col, rgb)

    # --- Top face: matte bone ceramic --------------------------------------
    grad = 0.86 + 0.10 * (-u * 0.6 - w / k * 0.5)
    micro = np.sin(rr * 420.0) * 0.006
    bone = np.array([0.93, 0.90, 0.85], np.float32)
    top_col = bone[None, None, :] * (grad + micro)[..., None]
    edge = np.clip((rr - 0.965) / 0.035, 0, 1)
    top_col = top_col * (1 - 0.25 * edge[..., None])

    # ring light (orange, emissive) + glow on the ceramic
    ring = np.exp(-(((rr - 0.52) / 0.012) ** 2))
    glow = np.exp(-np.abs(rr - 0.52) / 0.05) * 0.35
    orange = np.array([0.87, 0.42, 0.18], np.float32)
    top_col = top_col * (1 - ring[..., None] * 0.9) + orange * (ring * 1.15)[..., None] + orange * glow[..., None] * 0.6

    # bezel + glass lens
    bezel = (rr >= 0.40) & (rr < 0.455)
    bez_shade = 0.18 + 0.25 * np.clip(-u * 0.8 - w / k * 0.6 + 0.3, 0, 1)
    top_col = np.where(bezel[..., None], (np.array([0.32, 0.30, 0.28]) * bez_shade[..., None] * 2.2), top_col)
    lens = rr < 0.40
    lens_base = 0.03 + 0.05 * (1 - rr / 0.40)
    lens_col = np.stack([lens_base * 1.05, lens_base, lens_base * 0.95], -1)
    reflect = np.exp(-(((u + 0.10) / 0.14) ** 2 + ((w / k + 0.16) / 0.07) ** 2)) * 0.55
    reflect2 = np.exp(-(((rr - 0.30) / 0.01) ** 2)) * 0.06
    inner_glow = np.exp(-(rr / 0.10) ** 2)[..., None] * np.array([0.25, 0.10, 0.04])
    lens_col = lens_col + reflect[..., None] * np.array([0.9, 0.88, 0.85]) + reflect2[..., None] + inner_glow
    top_col = np.where(lens[..., None], lens_col, top_col)

    rgb = np.where(top[..., None], top_col, rgb)

    img = np.concatenate([np.clip(rgb, 0, 1), alpha[..., None]], -1)
    out = Image.fromarray((img * 255).astype(np.uint8), "RGBA")
    out = out.resize((size, size), Image.Resampling.LANCZOS)

    # soft ambient occlusion underneath (baked into the cut-out)
    shadow = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(shadow)
    sy = int((cy_top + H + R * k) * size)
    d.ellipse([int((cx - R * 0.95) * size), sy - 18, int((cx + R * 0.95) * size), sy + 26], fill=120)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.putalpha(shadow)
    base = Image.alpha_composite(base, out)
    return base


def save_hero():
    target = STATIC / "img/hero"
    target.mkdir(parents=True, exist_ok=True)
    img = render_hero_object()
    img.save(target / "placeholder-object.png", optimize=True)
    img.save(target / "placeholder-object.webp", quality=88, method=6)
    return img


# ---------------------------------------------------------------------------
# Brand images
# ---------------------------------------------------------------------------
def save_brand(hero_img):
    target = STATIC / "img/brand"
    target.mkdir(parents=True, exist_ok=True)

    og = Image.new("RGB", (1200, 630), (11, 10, 9))
    glow = Image.new("L", (1200, 630), 0)
    ImageDraw.Draw(glow).ellipse([640, 40, 1240, 640], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    og = Image.composite(Image.new("RGB", og.size, (221, 107, 47)), og, glow.point(lambda p: int(p * 0.5)))
    obj = hero_img.resize((560, 560), Image.Resampling.LANCZOS)
    og.paste(obj, (620, 30), obj)
    d = ImageDraw.Draw(og)
    d.polygon([(72, 96), (82, 86), (92, 96), (82, 106)], fill=(221, 107, 47))
    d.text((104, 78), "MAAN LAB", font=font(30), fill=(242, 238, 231))
    d.text((70, 250), "DIGITAL IDEAS.", font=font(76), fill=(242, 238, 231))
    d.text((70, 336), "MADE REAL.", font=font(76), fill=(221, 107, 47))
    d.text((72, 470), "Creative technology studio  ·  Ma'an, Jordan", font=font(26, bold=False), fill=(163, 156, 146))
    og.save(target / "og-default.jpg", quality=88, optimize=True, progressive=True)

    icon = Image.new("RGB", (180, 180), (11, 10, 9))
    di = ImageDraw.Draw(icon)
    di.polygon([(90, 40), (140, 90), (90, 140), (40, 90)], fill=(221, 107, 47))
    icon.save(target / "apple-touch-icon.png", optimize=True)


def save_contours():
    """Procedural contour lines — an abstract nod to southern Jordan's terrain."""
    rnd = random.Random(7)
    w, h = 1200, 1500
    peaks = [(rnd.uniform(0.1, 0.9) * w, rnd.uniform(0.1, 0.9) * h, rnd.uniform(160, 420), rnd.uniform(0.6, 1.2)) for _ in range(6)]

    def field(x, y):
        return sum(a * math.exp(-(((x - px) ** 2 + (y - py) ** 2) / (2 * s * s))) for px, py, s, a in peaks)

    step = 12
    gx = np.arange(0, w + step, step)
    gy = np.arange(0, h + step, step)
    grid = np.array([[field(x, y) for x in gx] for y in gy])
    levels = np.linspace(grid.min() + 0.05, grid.max() - 0.02, 26)

    paths = []
    for li, level in enumerate(levels):
        segs = []
        for j in range(len(gy) - 1):
            for i in range(len(gx) - 1):
                c = [grid[j, i], grid[j, i + 1], grid[j + 1, i + 1], grid[j + 1, i]]
                idx = sum(1 << b for b, v in enumerate(c) if v > level)
                if idx in (0, 15):
                    continue
                x0, y0 = gx[i], gy[j]

                def interp(a, b, pa, pb):
                    t = (level - a) / (b - a) if b != a else 0.5
                    return (pa[0] + t * (pb[0] - pa[0]), pa[1] + t * (pb[1] - pa[1]))

                pts = [(x0, y0), (x0 + step, y0), (x0 + step, y0 + step), (x0, y0 + step)]
                edges = []
                for e in range(4):
                    a, b = c[e], c[(e + 1) % 4]
                    if (a > level) != (b > level):
                        edges.append(interp(a, b, pts[e], pts[(e + 1) % 4]))
                for p in range(0, len(edges) - 1, 2):
                    segs.append((edges[p], edges[p + 1]))
        if segs:
            d = " ".join(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" for a, b in segs)
            accent = li == 17
            paths.append(
                f'<path d="{d}" stroke="{"#dd6b2f" if accent else "#c9b79c"}" '
                f'stroke-opacity="{0.9 if accent else 0.28 + 0.02 * (li % 5)}" stroke-width="{1.4 if accent else 1}"/>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice">'
        f'<rect width="{w}" height="{h}" fill="#11100e"/>'
        f'<g fill="none" stroke-linecap="round">{"".join(paths)}</g>'
        f'<circle cx="{peaks[0][0]:.0f}" cy="{peaks[0][1]:.0f}" r="5" fill="#dd6b2f"/>'
        f'<circle cx="{peaks[0][0]:.0f}" cy="{peaks[0][1]:.0f}" r="16" fill="none" stroke="#dd6b2f" stroke-opacity=".5"/>'
        "</svg>"
    )
    (STATIC / "img/brand/contours.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Placeholder film loops (ffmpeg via imageio-ffmpeg)
# ---------------------------------------------------------------------------
def ffmpeg_exe():
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def make_clip(name, size, colors, kind="radial", speed=0.01, seconds=8, seed=1):
    target = STATIC / "video"
    target.mkdir(parents=True, exist_ok=True)
    c = ":".join(f"c{i}=0x{col}" for i, col in enumerate(colors))
    src = f"gradients=s={size}:{c}:nb_colors={len(colors)}:type={kind}:speed={speed}:d={seconds}:r=24:seed={seed}"
    vf = "gblur=sigma=6,noise=alls=12:allf=u,vignette=angle=0.9,eq=contrast=1.06:saturation=1.08,format=yuv420p"
    mp4 = target / f"{name}.mp4"
    subprocess.run(
        [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, "-vf", vf,
         "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", "-an", str(mp4)],
        check=True,
    )
    png = target / f"{name}.png"
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", "2", "-i", str(mp4), "-frames:v", "1", str(png)], check=True)
    Image.open(png).convert("RGB").save(target / f"{name}.webp", quality=82, method=6)
    png.unlink()
    print(f"  {mp4.name}: {mp4.stat().st_size / 1024:.0f} KB")


def save_videos():
    make_clip("showreel-placeholder", "1280x536", ["0b0a09", "2a1810", "dd6b2f", "120e0b", "6b4a33"], "radial", 0.012, seed=3)
    make_clip("clip-sand", "1280x800", ["1a130e", "8c6a4a", "e8c9a0", "2b1d14"], "linear", 0.01, seed=5)
    make_clip("clip-night", "1280x800", ["07080b", "1b2433", "dd6b2f", "0b0a09"], "circular", 0.008, seed=9)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["hero", "brand", "contours", "videos"]
    hero = None
    if "hero" in steps or "brand" in steps:
        print("hero object…")
        hero = save_hero()
    if "brand" in steps:
        print("brand images…")
        save_brand(hero)
    if "contours" in steps:
        print("contours…")
        save_contours()
    if "videos" in steps:
        print("videos…")
        save_videos()
    print("done")
