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
    # Try Linux common fonts (Render)
    linux_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        f"/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
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

def create_visual_card(title="ANTI-BAN JITTER DELAY", subtitle="DODGE TELEGRAM SPAM LOCKS WITH HUMAN TIMING", category="PRO TIP", output_path="visual_card.png"):
    width, height = 1200, 630
    img = Image.new("RGB", (width, height), color=(10, 13, 20))
    draw = ImageDraw.Draw(img)

    # 1. Background Cyber Glow (Electric Blue on left, Emerald Neon on right)
    for r in range(480, 0, -8):
        draw.ellipse([(140 - r, 100 - r), (140 + r, 100 + r)], fill=(12, 38, 75))
        draw.ellipse([(1060 - r, 530 - r), (1060 + r, 530 + r)], fill=(8, 42, 36))

    # 2. Subtle Grid Matrix Dots
    for x in range(60, width - 60, 48):
        for y in range(60, height - 60, 48):
            draw.point((x, y), fill=(28, 36, 48))

    # 3. Outer Glassmorphism Border with Neon Edge Accent
    draw.rounded_rectangle([(32, 32), (width - 32, height - 32)], radius=24, outline=(38, 48, 66), width=2)
    draw.line([(80, 32), (320, 32)], fill=(0, 150, 255), width=3)

    # Fonts
    font_badge = get_font("segoeuib.ttf", 20)
    font_title = get_font("segoeuib.ttf", 52)
    font_subtitle = get_font("segoeuib.ttf", 22)
    font_pill = get_font("segoeuib.ttf", 16)

    # 4. Top Header Badge (Auto-fit pill)
    badge_text = f"WP RELAY • {category.upper()}"
    bbox = font_badge.getbbox(badge_text)
    badge_w = bbox[2] - bbox[0] + 36
    draw.rounded_rectangle([(70, 65), (70 + badge_w, 105)], radius=12, fill=(16, 26, 42), outline=(0, 140, 255), width=1)
    draw.text((88, 73), badge_text, font=font_badge, fill=(0, 210, 255))

    channel_text = "@webtgfv1"
    draw.text((width - 190, 73), channel_text, font=font_badge, fill=(120, 140, 170))

    # 5. Main Center Title (Wrapped cleanly)
    title_words = title.upper().split()
    lines = []
    curr = ""
    for w in title_words:
        test = f"{curr} {w}".strip()
        if len(test) <= 24:
            curr = test
        else:
            lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)

    start_y = 210 if len(lines) == 1 else 175
    for line in lines:
        draw.text((70, start_y), line, font=font_title, fill=(255, 255, 255))
        start_y += 66

    # 6. Subtitle / Value Hook (Clean multi-line wrapping)
    sub_words = subtitle.upper().split()
    sub_lines = []
    scurr = ""
    for sw in sub_words:
        stest = f"{scurr} {sw}".strip()
        if len(stest) <= 48:
            scurr = stest
        else:
            sub_lines.append(scurr)
            scurr = sw
    if scurr:
        sub_lines.append(scurr)

    for sline in sub_lines[:2]:
        draw.text((70, start_y + 14), sline, font=font_subtitle, fill=(0, 230, 180))
        start_y += 30

    # 7. Decorative Divider
    draw.line([(70, height - 135), (width - 70, height - 135)], fill=(30, 38, 52), width=1)

    # 8. Bottom Feature Pills
    features = ["100% BAN-PROOF", "SMART PACER", "ENTERPRISE STEALTH"]
    cur_x = 70
    for feat in features:
        pbox = font_pill.getbbox(feat)
        pw = pbox[2] - pbox[0] + 32
        draw.rounded_rectangle([(cur_x, height - 105), (cur_x + pw, height - 68)], radius=8, fill=(16, 22, 34), outline=(40, 52, 72), width=1)
        draw.text((cur_x + 16, height - 95), feat, font=font_pill, fill=(160, 180, 210))
        cur_x += pw + 16

    # Right Bottom: Bot Handle
    bot_callout = "@wprelaybot"
    draw.text((width - 220, height - 95), bot_callout, font=font_badge, fill=(0, 200, 255))

    img.save(output_path, quality=95)
    return output_path

if __name__ == "__main__":
    card = create_visual_card()
    print(f"Generated card: {card}")
