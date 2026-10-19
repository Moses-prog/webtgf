import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size):
    # Try Windows font path
    win_path = os.path.join(r"C:\Windows\Fonts", font_name)
    if os.path.exists(win_path):
        try:
            return ImageFont.truetype(win_path, size)
        except Exception:
            pass
    # Try Linux common fonts (Render container)
    linux_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        f"/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        f"/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for p in linux_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    # Fallback to default
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

# 6 Dynamic Colorway Themes with 100% Fixed Pixel Alignment
THEMES = {
    "cyber_cyan": {
        "accent": (0, 200, 255),
        "subtitle": (0, 230, 180),
        "badge_border": (0, 160, 255),
        "badge_text": (0, 220, 255),
        "badge_bg": (16, 26, 42)
    },
    "crimson_alert": {
        "accent": (255, 60, 80),
        "subtitle": (255, 185, 80),
        "badge_border": (255, 75, 90),
        "badge_text": (255, 120, 130),
        "badge_bg": (36, 16, 22)
    },
    "emerald_cash": {
        "accent": (0, 235, 130),
        "subtitle": (0, 225, 255),
        "badge_border": (0, 210, 120),
        "badge_text": (80, 255, 170),
        "badge_bg": (14, 32, 24)
    },
    "royal_purple": {
        "accent": (195, 80, 255),
        "subtitle": (160, 220, 255),
        "badge_border": (180, 70, 255),
        "badge_text": (220, 140, 255),
        "badge_bg": (28, 16, 44)
    },
    "sunset_amber": {
        "accent": (255, 130, 45),
        "subtitle": (255, 100, 155),
        "badge_border": (255, 140, 50),
        "badge_text": (255, 180, 95),
        "badge_bg": (38, 20, 16)
    },
    "stealth_mono": {
        "accent": (235, 240, 250),
        "subtitle": (180, 195, 215),
        "badge_border": (160, 175, 195),
        "badge_text": (240, 245, 255),
        "badge_bg": (24, 26, 32)
    }
}

def create_visual_card(
    title="ANTI-BAN JITTER DELAY",
    subtitle="DODGE TELEGRAM SPAM LOCKS WITH HUMAN TIMING",
    category="PRO TIP",
    theme="cyber_cyan",
    feature_pills=None,
    output_path="visual_card.png"
):
    width, height = 1200, 630

    if not theme or theme not in THEMES:
        theme = "cyber_cyan"
    t = THEMES[theme]

    # Base Canvas: Dark Obsidian
    img = Image.new("RGB", (width, height), color=(10, 13, 20))

    # 1. Soft Diffuse Radial Glows (Zero harsh circular borders)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    accent_rgb = t["accent"]
    sub_rgb = t["subtitle"]
    for r in range(500, 0, -10):
        alpha = int(55 * (1 - r / 500) ** 1.8)
        gd.ellipse([(140 - r, 100 - r), (140 + r, 100 + r)], fill=(accent_rgb[0], accent_rgb[1], accent_rgb[2], alpha))
        gd.ellipse([(1060 - r, 530 - r), (1060 + r, 530 + r)], fill=(sub_rgb[0], sub_rgb[1], sub_rgb[2], alpha))
    img.paste(glow, (0, 0), glow)

    draw = ImageDraw.Draw(img)

    # 2. Subtle Matrix Dots (Fixed alignment)
    for x in range(60, width - 60, 48):
        for y in range(60, height - 60, 48):
            draw.point((x, y), fill=(28, 36, 48))

    # 3. Outer Glassmorphism Card Border with Accent Bar (Fixed alignment)
    draw.rounded_rectangle([(32, 32), (width - 32, height - 32)], radius=24, outline=(38, 48, 66), width=2)
    draw.line([(80, 32), (320, 32)], fill=accent_rgb, width=3)

    # Fonts
    font_badge = get_font("segoeuib.ttf", 20)
    font_title = get_font("segoeuib.ttf", 52)
    font_subtitle = get_font("segoeuib.ttf", 22)
    font_pill = get_font("segoeuib.ttf", 16)

    # 4. Top Header Badge (Fixed Y = 65, left X = 70)
    clean_cat = category.replace("WP RELAY", "").replace("•", "").strip().upper() or "PRO TIP"
    badge_text = f"WP RELAY • {clean_cat}"
    bbox = font_badge.getbbox(badge_text)
    badge_w = bbox[2] - bbox[0] + 36
    draw.rounded_rectangle([(70, 65), (70 + badge_w, 105)], radius=12, fill=t["badge_bg"], outline=t["badge_border"], width=1)
    draw.text((88, 73), badge_text, font=font_badge, fill=t["badge_text"])

    # Official Channel Handle (Fixed at width - 190, 73)
    channel_text = "@webtgfv1"
    draw.text((width - 190, 73), channel_text, font=font_badge, fill=(120, 140, 170))

    # 5. Main Title (Wrapped cleanly, fixed left X = 70, fixed line height = 66)
    title_words = title.upper().replace('"', '').replace("'", "").split()
    lines = []
    curr = ""
    for w in title_words:
        test = f"{curr} {w}".strip()
        if len(test) <= 24:
            curr = test
        else:
            if curr:
                lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
    lines = lines[:3]

    start_y = 210 if len(lines) == 1 else (175 if len(lines) == 2 else 150)
    for line in lines:
        draw.text((70, start_y), line, font=font_title, fill=(255, 255, 255))
        start_y += 66

    # 6. Subtitle (Wrapped cleanly, fixed left X = 70, 14px below title, fixed line height = 30)
    sub_words = subtitle.upper().replace('"', '').replace("'", "").split()
    sub_lines = []
    scurr = ""
    for sw in sub_words:
        stest = f"{scurr} {sw}".strip()
        if len(stest) <= 48:
            scurr = stest
        else:
            if scurr:
                sub_lines.append(scurr)
            scurr = sw
    if scurr:
        sub_lines.append(scurr)

    for sline in sub_lines[:2]:
        draw.text((70, start_y + 14), sline, font=font_subtitle, fill=sub_rgb)
        start_y += 30

    # 7. Decorative Divider (Fixed clean rule at height - 135)
    draw.line([(70, height - 135), (width - 70, height - 135)], fill=(30, 38, 52), width=1)

    # 8. Bottom Feature Pills (Fixed Y = height - 105, fixed 3-pill grid)
    if not feature_pills or not isinstance(feature_pills, list) or len(feature_pills) == 0:
        features = ["100% BAN-PROOF", "SMART PACER", "ENTERPRISE STEALTH"]
    else:
        features = [str(f).strip().upper()[:20] for f in feature_pills[:3]]
        while len(features) < 3:
            features.append("ENTERPRISE STEALTH")

    cur_x = 70
    for feat in features:
        pbox = font_pill.getbbox(feat)
        pw = pbox[2] - pbox[0] + 32
        draw.rounded_rectangle([(cur_x, height - 105), (cur_x + pw, height - 68)], radius=8, fill=(16, 22, 34), outline=(40, 52, 72), width=1)
        draw.text((cur_x + 16, height - 95), feat, font=font_pill, fill=(160, 180, 210))
        cur_x += pw + 16

    # Right Bottom: Bot Handle (Fixed at width - 220, height - 95)
    bot_callout = "@wprelaybot"
    draw.text((width - 220, height - 95), bot_callout, font=font_badge, fill=accent_rgb)

    img.save(output_path, quality=95)
    return output_path

if __name__ == "__main__":
    card = create_visual_card()
    print(f"Generated card: {card}")
