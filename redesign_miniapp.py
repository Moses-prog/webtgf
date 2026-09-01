with open('web.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_miniapp = c[c.find("@app.route('/miniapp')"):]
old_miniapp = old_miniapp[:old_miniapp.find('\nif __name__')]

new_miniapp = r"""
@app.route('/miniapp')
def miniapp():
    html = """
    html += r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WebTGF</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #181818;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            min-height: 100vh;
            padding-bottom: 40px;
        }
        .header {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px 20px 20px;
        }
        .avatar {
            width: 80px; height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f79533, #f37055, #ef4e7b, #a166ab, #5073b8);
            display: flex; align-items: center; justify-content: center;
            font-size: 36px;
            margin-bottom: 14px;
            box-shadow: 0 4px 20px rgba(239,78,123,0.4);
        }
        .bot-name {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .bot-username {
            font-size: 14px;
            color: #8e8e93;
        }
        .badge {
            margin-top: 10px;
            background: #2c2c2e;
            border-radius: 20px;
            padding: 4px 14px;
            font-size: 12px;
            color: #f59e0b;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .section-label {
            font-size: 13px;
            font-weight: 600;
            color: #8e8e93;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            padding: 18px 20px 8px;
        }
        .card {
            background: #2c2c2e;
            margin: 0 16px 2px;
            border-radius: 0;
            overflow: hidden;
        }
        .card:first-of-type { border-radius: 12px 12px 0 0; }
        .card:last-of-type { border-radius: 0 0 12px 12px; margin-bottom: 10px; }
        .card.solo { border-radius: 12px; }
        .row {
            display: flex;
            align-items: center;
            padding: 14px 16px;
            border-bottom: 0.5px solid rgba(255,255,255,0.06);
            gap: 14px;
        }
        .card:last-child .row:last-child, .card.solo .row { border-bottom: none; }
        .row-icon {
            width: 32px; height: 32px;
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 17px;
            flex-shrink: 0;
        }
        .row-text { flex: 1; }
        .row-title { font-size: 16px; font-weight: 500; }
        .row-subtitle { font-size: 12px; color: #8e8e93; margin-top: 2px; }
        .row-right { color: #8e8e93; font-size: 18px; }
        .coming-soon-chip {
            background: rgba(88, 86, 214, 0.25);
            color: #a78bfa;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 10px;
        }
        .launch-btn {
            margin: 20px 16px 10px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            border: none;
            padding: 16px;
            font-size: 17px;
            font-weight: 700;
            border-radius: 14px;
            cursor: pointer;
            width: calc(100% - 32px);
            letter-spacing: 0.3px;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
            transition: opacity 0.15s;
        }
        .launch-btn:active { opacity: 0.8; }
        .footer {
            text-align: center;
            font-size: 12px;
            color: #555;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="avatar">⚙️</div>
        <div class="bot-name">WebTGF</div>
        <div class="bot-username">@Webtgfbot</div>
        <div class="badge">🚀 COMING SOON</div>
    </div>

    <div class="section-label">Features</div>
    <div class="card" style="border-radius:12px 12px 0 0">
        <div class="row">
            <div class="row-icon" style="background:#1d3a5f">📡</div>
            <div class="row-text">
                <div class="row-title">Auto Forwarding</div>
                <div class="row-subtitle">Copy messages across channels</div>
            </div>
            <span class="coming-soon-chip">Soon</span>
        </div>
    </div>
    <div class="card">
        <div class="row">
            <div class="row-icon" style="background:#1d3d2e">✏️</div>
            <div class="row-text">
                <div class="row-title">Message Modifier</div>
                <div class="row-subtitle">Replace words, links & usernames</div>
            </div>
            <span class="coming-soon-chip">Soon</span>
        </div>
    </div>
    <div class="card">
        <div class="row">
            <div class="row-icon" style="background:#3d2020">🤖</div>
            <div class="row-text">
                <div class="row-title">AI Watermark Remover</div>
                <div class="row-subtitle">Powered by Gemini AI</div>
            </div>
            <span class="coming-soon-chip">Soon</span>
        </div>
    </div>
    <div class="card" style="border-radius:0 0 12px 12px">
        <div class="row">
            <div class="row-icon" style="background:#2d2a0f">⏱️</div>
            <div class="row-text">
                <div class="row-title">Drip Posting & Scheduler</div>
                <div class="row-subtitle">Auto-post on your schedule</div>
            </div>
            <span class="coming-soon-chip">Soon</span>
        </div>
    </div>

    <div class="section-label">Stay Updated</div>
    <div class="card solo">
        <div class="row">
            <div class="row-icon" style="background:#1a2f4a">💬</div>
            <div class="row-text">
                <div class="row-title">Join our Channel</div>
                <div class="row-subtitle">Get notified on launch</div>
            </div>
            <div class="row-right">›</div>
        </div>
    </div>

    <button class="launch-btn" onclick="Telegram.WebApp.close()">Close App</button>
    <div class="footer">Full app launching very soon. Stay tuned!</div>

    <script>
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        window.Telegram.WebApp.setHeaderColor('#181818');
        window.Telegram.WebApp.setBackgroundColor('#181818');
    </script>
</body>
</html>'''
    return html
"""

if "@app.route('/miniapp')" in c:
    c = c[:c.find("@app.route('/miniapp')")] + new_miniapp + c[c.find("\nif __name__"):]
    with open('web.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Mini app redesigned.")
else:
    print("Route not found")
