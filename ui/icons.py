from PIL import Image, ImageDraw
import customtkinter as ctk

def _create_supersampled(size, draw_func):
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw_func(draw, w, h)
    final = canvas.resize(size, Image.Resampling.LANCZOS)
    return ctk.CTkImage(light_image=final, dark_image=final, size=size)

def get_icon(name, size=(20, 20), color="#FFFFFF"):
    name = name.lower()

    if name == "play":
        def draw(d, w, h):
            pts = [(w * 0.32, h * 0.22), (w * 0.78, h * 0.5), (w * 0.32, h * 0.78)]
            d.polygon(pts, fill=color)
        return _create_supersampled(size, draw)

    elif name == "pause":
        def draw(d, w, h):
            d.rounded_rectangle((w * 0.26, h * 0.22, w * 0.42, h * 0.78), radius=w * 0.06, fill=color)
            d.rounded_rectangle((w * 0.58, h * 0.22, w * 0.74, h * 0.78), radius=w * 0.06, fill=color)
        return _create_supersampled(size, draw)

    elif name == "next":
        def draw(d, w, h):
            pts = [(w * 0.22, h * 0.24), (w * 0.62, h * 0.5), (w * 0.22, h * 0.76)]
            d.polygon(pts, fill=color)
            d.rounded_rectangle((w * 0.68, h * 0.24, w * 0.78, h * 0.76), radius=w * 0.04, fill=color)
        return _create_supersampled(size, draw)

    elif name == "prev":
        def draw(d, w, h):
            pts = [(w * 0.78, h * 0.24), (w * 0.38, h * 0.5), (w * 0.78, h * 0.76)]
            d.polygon(pts, fill=color)
            d.rounded_rectangle((w * 0.22, h * 0.24, w * 0.32, h * 0.76), radius=w * 0.04, fill=color)
        return _create_supersampled(size, draw)

    elif name == "shuffle":
        def draw(d, w, h):
            lw = int(max(1, w * 0.08))
            d.line([(w * 0.2, h * 0.7), (w * 0.45, h * 0.7), (w * 0.65, h * 0.3), (w * 0.8, h * 0.3)], fill=color, width=lw)
            d.polygon([(w * 0.75, h * 0.18), (w * 0.88, h * 0.3), (w * 0.75, h * 0.42)], fill=color)
            d.line([(w * 0.2, h * 0.3), (w * 0.45, h * 0.3), (w * 0.65, h * 0.7), (w * 0.8, h * 0.7)], fill=color, width=lw)
            d.polygon([(w * 0.75, h * 0.58), (w * 0.88, h * 0.7), (w * 0.75, h * 0.82)], fill=color)
        return _create_supersampled(size, draw)

    elif name == "repeat":
        def draw(d, w, h):
            lw = int(max(1, w * 0.08))
            d.arc((w * 0.2, h * 0.2, w * 0.8, h * 0.8), start=45, end=315, fill=color, width=lw)
            d.polygon([(w * 0.7, h * 0.1), (w * 0.85, h * 0.25), (w * 0.7, h * 0.4)], fill=color)
        return _create_supersampled(size, draw)

    elif name == "heart_filled":
        def draw(d, w, h):
            r = w * 0.18
            d.ellipse((w * 0.2, h * 0.2, w * 0.55, h * 0.55), fill=color)
            d.ellipse((w * 0.45, h * 0.2, w * 0.8, h * 0.55), fill=color)
            d.polygon([(w * 0.22, h * 0.45), (w * 0.78, h * 0.45), (w * 0.5, h * 0.82)], fill=color)
        return _create_supersampled(size, draw)

    elif name == "heart_outline":
        def draw(d, w, h):
            lw = int(max(1, w * 0.07))
            d.arc((w * 0.2, h * 0.2, w * 0.55, h * 0.55), start=140, end=360, fill=color, width=lw)
            d.arc((w * 0.45, h * 0.2, w * 0.8, h * 0.55), start=180, end=40, fill=color, width=lw)
            d.line([(w * 0.22, h * 0.44), (w * 0.5, h * 0.8)], fill=color, width=lw)
            d.line([(w * 0.78, h * 0.44), (w * 0.5, h * 0.8)], fill=color, width=lw)
        return _create_supersampled(size, draw)

    elif name == "more":
        def draw(d, w, h):
            r = w * 0.07
            d.ellipse((w * 0.5 - r, h * 0.25 - r, w * 0.5 + r, h * 0.25 + r), fill=color)
            d.ellipse((w * 0.5 - r, h * 0.5 - r, w * 0.5 + r, h * 0.5 + r), fill=color)
            d.ellipse((w * 0.5 - r, h * 0.75 - r, w * 0.5 + r, h * 0.75 + r), fill=color)
        return _create_supersampled(size, draw)

    elif name == "search":
        def draw(d, w, h):
            lw = int(max(1, w * 0.08))
            d.ellipse((w * 0.2, h * 0.2, w * 0.62, h * 0.62), outline=color, width=lw)
            d.line([(w * 0.52, h * 0.52), (w * 0.8, h * 0.8)], fill=color, width=lw + 1)
        return _create_supersampled(size, draw)

    elif name == "volume":
        def draw(d, w, h):
            lw = int(max(1, w * 0.07))
            d.polygon([(w * 0.18, h * 0.38), (w * 0.32, h * 0.38), (w * 0.48, h * 0.22), (w * 0.48, h * 0.78), (w * 0.32, h * 0.62), (w * 0.18, h * 0.62)], fill=color)
            d.arc((w * 0.42, h * 0.32, w * 0.68, h * 0.68), start=-60, end=60, fill=color, width=lw)
            d.arc((w * 0.36, h * 0.2, w * 0.84, h * 0.8), start=-60, end=60, fill=color, width=lw)
        return _create_supersampled(size, draw)

    elif name == "drawer":
        def draw(d, w, h):
            lw = int(max(1, w * 0.08))
            d.rounded_rectangle((w * 0.2, h * 0.22, w * 0.8, h * 0.78), radius=w * 0.06, outline=color, width=lw)
            d.line([(w * 0.6, h * 0.22), (w * 0.6, h * 0.78)], fill=color, width=lw)
        return _create_supersampled(size, draw)

    elif name == "download":
        def draw(d, w, h):
            lw = int(max(1, w * 0.08))
            d.line([(w * 0.5, h * 0.2), (w * 0.5, h * 0.64)], fill=color, width=lw)
            d.polygon([(w * 0.34, h * 0.52), (w * 0.66, h * 0.52), (w * 0.5, h * 0.72)], fill=color)
            d.line([(w * 0.22, h * 0.8), (w * 0.78, h * 0.8)], fill=color, width=lw)
        return _create_supersampled(size, draw)

    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    return ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)