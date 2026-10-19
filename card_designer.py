import os
import random
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

# 6 Highly Distinct Visual Color Themes
THEMES = {
    "cyber_cyan": {
        "name": "Cyber Cyan (Stealth & Automation)",
        "bg": (8, 13, 22),
        "glow1": (12, 54, 102),
        "glow2": (8, 66, 60),
        "border": (32, 52, 78),
        "accent": (0, 205, 255),
        "badge_fill": (14, 28, 48),
        "badge_border": (0, 160, 255),
        "badge_text": (0, 225, 255),
        "title": (255, 255, 255),
        "subtitle": (0, 235, 195),
        "pill_fill": (14, 22, 34),
        "pill_border": (35, 55, 80),
        "pill_text": (165, 195, 235),
        "handle": (0, 210, 255),
        "pattern": "dots"
    },
    "crimson_alert": {
        "name": "Crimson Alert (Security & Anti-Ban)",
        "bg": (18, 9, 12),
        "glow1": (100, 18, 28),
        "glow2": (85, 38, 12),
        "border": (70, 32, 42),
        "accent": (255, 55, 75),
        "badge_fill": (40, 15, 22),
        "badge_border": (255, 70, 85),
        "badge_text": (255, 115, 125),
        "title": (255, 250, 250),
        "subtitle": (255, 195, 80),
        "pill_fill": (32, 14, 18),
        "pill_border": (75, 30, 40),
        "pill_text": (245, 180, 185),
        "handle": (255, 80, 95),
        "pattern": "crosshairs"
    },
    "emerald_cash": {
        "name": "Emerald Cash (Monetization & Arbitrage)",
        "bg": (7, 18, 13),
        "glow1": (10, 78, 46),
        "glow2": (16, 58, 82),
        "border": (26, 62, 45),
        "accent": (0, 235, 130),
        "badge_fill": (13, 36, 26),
        "badge_border": (0, 210, 120),
        "badge_text": (80, 255, 170),
        "title": (255, 255, 255),
        "subtitle": (115, 245, 255),
        "pill_fill": (13, 30, 22),
        "pill_border": (30, 68, 48),
        "pill_text": (160, 235, 190),
        "handle": (0, 235, 140),
        "pattern": "grid"
    },
    "royal_purple": {
        "name": "Royal Purple (VIP PRO & Masterclass)",
        "bg": (14, 9, 24),
        "glow1": (75, 20, 105),
        "glow2": (25, 38, 95),
        "border": (58, 36, 84),
        "accent": (205, 80, 255),
        "badge_fill": (32, 16, 52),
        "badge_border": (185, 70, 255),
        "badge_text": (225, 140, 255),
        "title": (255, 255, 255),
        "subtitle": (155, 220, 255),
        "pill_fill": (26, 16, 42),
        "pill_border": (68, 42, 95),
        "pill_text": (215, 185, 245),
        "handle": (210, 95, 255),
        "pattern": "diamonds"
    },
    "sunset_amber": {
        "name": "Sunset Amber (Growth Velocity & Viral Hacks)",
        "bg": (20, 11, 9),
        "glow1": (110, 48, 14),
        "glow2": (95, 22, 55),
        "border": (72, 40, 28),
        "accent": (255, 128, 40),
        "badge_fill": (44, 20, 14),
        "badge_border": (255, 135, 45),
        "badge_text": (255, 180, 95),
        "title": (255, 255, 255),
        "subtitle": (255, 110, 160),
        "pill_fill": (36, 18, 14),
        "pill_border": (75, 42, 28),
        "pill_text": (245, 195, 165),
        "handle": (255, 140, 60),
        "pattern": "speed"
    },
    "stealth_mono": {
        "name": "Stealth Titanium (Enterprise Precision)",
        "bg": (12, 14, 18),
        "glow1": (48, 54, 66),
        "glow2": (32, 36, 46),
        "border": (48, 54, 66),
        "accent": (240, 245, 255),
        "badge_fill": (24, 26, 32),
        "badge_border": (160, 172, 190),
        "badge_text": (240, 245, 255),
        "title": (255, 255, 255),
        "subtitle": (180, 192, 210),
        "pill_fill": (20, 22, 28),
        "pill_border": (52, 58, 70),
        "pill_text": (205, 215, 230),
        "handle": (240, 245, 255),
        "pattern": "dots"
    }
}

def draw_background_pattern(draw, width, height, pattern_type, base_col):
    if pattern_type == "dots":
        for x in range(60, width - 60, 48):
            for y in range(60, height - 60, 48):
                draw.point((x, y), fill=base_col)
    elif pattern_type == "grid":
        for x in range(80, width - 80, 80):
            draw.line([(x, 60), (x, height - 60)], fill=base_col, width=1)
        for y in range(80, height - 80, 80):
            draw.line([(60, y), (width - 60, y)], fill=base_col, width=1)
    elif pattern_type == "crosshairs":
        for x in range(100, width - 100, 120):
            for y in range(90, height - 90, 110):
                draw.line([(x - 4, y), (x + 4, y)], fill=base_col, width=1)
                draw.line([(x, y - 4), (x, y + 4)], fill=base_col, width=1)
    elif pattern_type == "diamonds":
        for x in range(80, width - 80, 96):
            for y in range(80, height - 80, 96):
                draw.polygon([(x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)], outline=base_col)
    elif pattern_type == "speed":
        for y in range(70, height - 70, 36):
            for x in range(80, width - 80, 160):
                draw.line([(x, y), (x + 22, y)], fill=base_col, width=1)

def create_visual_card(
    title="ANTI-BAN JITTER DELAY",
    subtitle="DODGE TELEGRAM SPAM LOCKS WITH HUMAN TIMING",
    category="PRO TIP",
    theme="cyber_cyan",
    feature_pills=None,
    output_path="visual_card.png"
):
    width, height = 1200, 630

    # Validate theme
    if not theme or theme not in THEMES:
        theme = random.choice(list(THEMES.keys()))
    t = THEMES[theme]

    img = Image.new("RGB", (width, height), color=t["bg"])
    draw = ImageDraw.Draw(img)

    # 1. Radiant Ambient Glow Orbs
    glow1_col = t["glow1"]
    glow2_col = t["glow2"]
    for r in range(500, 0, -10):
        # Top-Left Glow
        draw.ellipse([(140 - r, 110 - r), (140 + r, 110 + r)], fill=glow1_col)
        # Bottom-Right Glow
        draw.ellipse([(1060 - r, 520 - r), (1060 + r, 520 + r)], fill=glow2_col)

    # 2. Dynamic Geometric Backdrop Pattern
    pat_col = (min(255, t["border"][0] + 10), min(255, t["border"][1] + 10), min(255, t["border"][2] + 10))
    draw_background_pattern(draw, width, height, t.get("pattern", "dots"), pat_col)

    # 3. Outer Glassmorphism Card Border & Sleek Corner Notches
    draw.rounded_rectangle([(32, 32), (width - 32, height - 32)], radius=24, outline=t["border"], width=2)
    # Vibrant Accent Glow Bar
    draw.line([(80, 32), (360, 32)], fill=t["accent"], width=4)

    # Technical Corner HUD Brackets
    hud_c = t["accent"]
    draw.line([(44, 44), (56, 44)], fill=hud_c, width=2)
    draw.line([(44, 44), (44, 56)], fill=hud_c, width=2)
    draw.line([(width - 44, 44), (width - 56, 44)], fill=hud_c, width=2)
    draw.line([(width - 44, 44), (width - 44, 56)], fill=hud_c, width=2)

    # Fonts
    font_badge = get_font("segoeuib.ttf", 20)
    font_title_large = get_font("segoeuib.ttf", 52)
    font_title_compact = get_font("segoeuib.ttf", 44)
    font_subtitle = get_font("segoeuib.ttf", 22)
    font_pill = get_font("segoeuib.ttf", 16)

    # 4. Top Category Badge (Pill)
    badge_clean = category.replace("WP RELAY", "").replace("•", "").strip().upper()
    if not badge_clean:
        badge_clean = "INTELLIGENCE"
    badge_text = f"WP RELAY • {badge_clean}"
    bbox = font_badge.getbbox(badge_text)
    badge_w = bbox[2] - bbox[0] + 36
    draw.rounded_rectangle([(70, 65), (70 + badge_w, 105)], radius=12, fill=t["badge_fill"], outline=t["badge_border"], width=1)
    draw.text((88, 73), badge_text, font=font_badge, fill=t["badge_text"])

    # Official Channel Watermark
    channel_text = "@webtgfv1"
    draw.text((width - 190, 73), channel_text, font=font_badge, fill=(130, 145, 170))

    # 5. Clean Title Formatting & Smart Wrapping
    title_words = title.upper().replace('"', '').replace("'", "").split()
    lines = []
    curr = ""
    # Choose font size depending on total length
    font_title = font_title_large if len(title) < 45 else font_title_compact
    max_char_per_line = 24 if font_title == font_title_large else 30

    for w in title_words:
        test = f"{curr} {w}".strip()
        if len(test) <= max_char_per_line:
            curr = test
        else:
            if curr:
                lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)

    lines = lines[:3] # Maximum 3 lines

    start_y = 210 if len(lines) == 1 else (175 if len(lines) == 2 else 150)
    line_height = 64 if font_title == font_title_large else 54

    for line in lines:
        draw.text((70, start_y), line, font=font_title, fill=t["title"])
        start_y += line_height

    # 6. Dynamic Subtitle / Value Hook (Clean 1-2 line wrap)
    sub_words = subtitle.upper().replace('"', '').replace("'", "").split()
    sub_lines = []
    scurr = ""
    for sw in sub_words:
        stest = f"{scurr} {sw}".strip()
        if len(stest) <= 46:
            scurr = stest
        else:
            if scurr:
                sub_lines.append(scurr)
            scurr = sw
    if scurr:
        sub_lines.append(scurr)

    sub_start_y = start_y + 16
    for sline in sub_lines[:2]:
        draw.text((70, sub_start_y), sline, font=font_subtitle, fill=t["subtitle"])
        sub_start_y += 30

    # 7. Sleek Divider with Center Accent Dot
    draw.line([(70, height - 135), (width - 70, height - 135)], fill=t["border"], width=1)
    draw.ellipse([(width // 2 - 3, height - 138), (width // 2 + 3, height - 132)], fill=t["accent"])

    # 8. Dynamic Feature Pills
    if not feature_pills or not isinstance(feature_pills, list) or len(feature_pills) == 0:
        feature_pills = ["100% BAN-PROOF", "SMART PACER", "ENTERPRISE STEALTH"]

    cur_x = 70
    for feat in feature_pills[:3]:
        feat_clean = str(feat).strip().upper()[:22]
        pbox = font_pill.getbbox(feat_clean)
        pw = pbox[2] - pbox[0] + 32
        draw.rounded_rectangle([(cur_x, height - 105), (cur_x + pw, height - 68)], radius=8, fill=t["pill_fill"], outline=t["pill_border"], width=1)
        draw.text((cur_x + 16, height - 95), feat_clean, font=font_pill, fill=t["pill_text"])
        cur_x += pw + 16

    # Right Bottom: Bot Handle
    bot_callout = "@wprelaybot"
    draw.text((width - 220, height - 95), bot_callout, font=font_badge, fill=t["handle"])

    img.save(output_path, quality=95)
    return output_path

if __name__ == "__main__":
    for theme_name in THEMES.keys():
        out = f"test_{theme_name}.png"
        create_visual_card(
            title="HUMAN JITTER TIMING",
            subtitle="HOW TO PREVENT TELEGRAM SPAM LOCKS PERMANENTLY",
            category="SECURITY ALERT",
            theme=theme_name,
            feature_pills=["8-35S JITTER", "FLOOD SHIELD", "UNDETECTED"],
            output_path=out
        )
        print(f"Generated: {out}")
