from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design-export"
ASSETS = ROOT / "assets"

URL = "https://rattvisdemokrati.pro/"

NAVY = "#1E2A5E"
DEEP_NAVY = "#141B44"
BLUE = "#3B4CA8"
YELLOW = "#F5A81E"
CREAM = "#FAF9F5"
MUTED = "#5A628C"
WHITE = "#FFFFFF"

W, H = 2480, 3508  # A4 at 300 dpi


def resolve_font(*candidates: str) -> str:
    """Return the first installed font from a cross-platform candidate list."""
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"No supported font found. Tried: {', '.join(candidates)}")


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


FONT_HEAD = resolve_font(
    r"C:\Windows\Fonts\DejaVuSansCondensed-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
)
FONT_BODY = resolve_font(
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
FONT_BOLD = resolve_font(
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def centered(draw: ImageDraw.ImageDraw, y: int, text: str, fnt, fill, spacing=0):
    tw, th = text_size(draw, text, fnt)
    draw.text(((W - tw) // 2, y), text, font=fnt, fill=fill, spacing=spacing)
    return y + th


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def make_qr() -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=24,
        border=4,
    )
    qr.add_data(URL)
    qr.make(fit=True)
    return qr.make_image(fill_color=DEEP_NAVY, back_color=WHITE).convert("RGB")


def draw_village_silhouette(draw: ImageDraw.ImageDraw, y_base: int):
    draw.rectangle((0, y_base, W, H), fill=DEEP_NAVY)
    scale = W / 1440
    points = [
        [(25, 110), (55, 38), (85, 110)],
        [(120, 110), (120, 64), (155, 42), (190, 64), (190, 110)],
        [(205, 110), (228, 54), (251, 110)],
        [(272, 110), (272, 60), (322, 38), (372, 60), (372, 110)],
        [(400, 110), (400, 72), (428, 54), (456, 72), (456, 110)],
        [(470, 110), (500, 30), (530, 110)],
        [(604, 110), (604, 70), (639, 52), (674, 70), (674, 110)],
        [(700, 110), (700, 66), (738, 44), (776, 66), (776, 110)],
        [(792, 110), (820, 40), (848, 110)],
        [(920, 110), (920, 58), (975, 36), (1030, 58), (1030, 110)],
        [(1130, 110), (1162, 26), (1194, 110)],
        [(1220, 110), (1220, 64), (1256, 44), (1292, 64), (1292, 110)],
        [(1310, 110), (1338, 48), (1366, 110)],
        [(1385, 110), (1385, 76), (1410, 58), (1435, 76), (1435, 110)],
    ]
    for poly in points:
        p = [(int(x * scale), int(y_base - 190 + y * 1.7)) for x, y in poly]
        draw.polygon(p, fill=NAVY)
    draw.rectangle((0, y_base - 34, W, y_base + 10), fill=NAVY)


def generate():
    OUT.mkdir(parents=True, exist_ok=True)

    qr_img = make_qr()
    qr_path = OUT / "rattvisdemokrati-qr.png"
    qr_img.save(qr_path, dpi=(300, 300))

    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # Premium dark frame with the site's yellow accent.
    draw.rectangle((0, 0, W, H), fill=CREAM)
    draw.rectangle((0, 0, W, 560), fill=NAVY)
    draw.rectangle((0, 520, W, 590), fill=YELLOW)
    draw.rectangle((0, 590, W, 606), fill=DEEP_NAVY)

    draw_village_silhouette(draw, H - 230)

    logo_path = ASSETS / "logo.jpg"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGB")
        logo.thumbnail((210, 210), Image.Resampling.LANCZOS)
        logo_box = Image.new("RGB", (240, 240), WHITE)
        logo_box.paste(logo, ((240 - logo.width) // 2, (240 - logo.height) // 2))
        mask = Image.new("L", (240, 240), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, 240, 240), radius=34, fill=255)
        img.paste(logo_box, (W // 2 - 120, 124), mask)

    f_brand = font(FONT_HEAD, 96)
    f_sub = font(FONT_BOLD, 38)
    f_h1 = font(FONT_HEAD, 238)
    f_body = font(FONT_BODY, 52)
    f_url = font(FONT_BOLD, 48)
    f_small = font(FONT_BODY, 34)

    centered(draw, 388, "RÄTTVIS DEMOKRATI", f_brand, WHITE)
    centered(draw, 494, "Strömsunds kommun", f_sub, "#DDE3FF")

    centered(draw, 820, "Läs mer här", f_h1, DEEP_NAVY)
    centered(draw, 1082, "Skanna QR-koden med kameran", f_body, MUTED)

    qr_size = 1140
    qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    card_w = 1390
    card_h = 1390
    card_x = (W - card_w) // 2
    card_y = 1280
    shadow = Image.new("RGBA", (card_w + 70, card_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((35, 30, card_w + 35, card_h + 30), radius=72, fill=(20, 27, 68, 42))
    img.paste(shadow.convert("RGB"), (card_x - 35, card_y - 30), shadow)
    rounded(draw, (card_x, card_y, card_x + card_w, card_y + card_h), 72, WHITE)
    rounded(draw, (card_x + 24, card_y + 24, card_x + card_w - 24, card_y + card_h - 24), 56, WHITE, YELLOW, 10)
    img.paste(qr_resized, (W // 2 - qr_size // 2, card_y + 122))

    # Small accents that echo the website's pill/button language.
    pill = "rattvisdemokrati.pro"
    tw, th = text_size(draw, pill, f_url)
    pill_w = tw + 120
    pill_h = 106
    pill_x = (W - pill_w) // 2
    pill_y = card_y + card_h + 118
    rounded(draw, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), 28, YELLOW)
    draw.text((pill_x + 60, pill_y + 27), pill, font=f_url, fill=DEEP_NAVY)

    centered(draw, pill_y + 170, "Ett lokalt parti — hela vårt hjärta i Strömsund", f_small, "#6B7196")

    # Print-safe margin guide accent.
    draw.rectangle((104, 104, W - 104, H - 104), outline=(30, 42, 94), width=4)
    draw.rectangle((104, 104, W - 104, 118), fill=YELLOW)

    png_path = OUT / "rattvisdemokrati-a4-qr-poster.png"
    pdf_path = OUT / "rattvisdemokrati-a4-qr-poster.pdf"
    img.save(png_path, dpi=(300, 300))
    img.save(pdf_path, "PDF", resolution=300.0)
    print(png_path)
    print(pdf_path)
    print(qr_path)


if __name__ == "__main__":
    generate()
