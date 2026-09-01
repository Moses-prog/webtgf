with open('web.py', 'r', encoding='utf-8') as f:
    c = f.read()

MINI_APP_HTML = '''
@app.route('/miniapp')
def miniapp():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background-color: var(--tg-theme-bg-color, #121212);
                color: var(--tg-theme-text-color, #ffffff);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                text-align: center;
                padding: 20px;
            }
            .container {
                background: var(--tg-theme-secondary-bg-color, #1e1e1e);
                padding: 40px 30px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                max-width: 90%;
            }
            h1 {
                font-size: 28px;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #0088cc, #00ffaa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p {
                font-size: 16px;
                color: var(--tg-theme-hint-color, #aaaaaa);
                margin-bottom: 30px;
                line-height: 1.5;
            }
            .btn {
                background-color: var(--tg-theme-button-color, #3390ec);
                color: var(--tg-theme-button-text-color, #ffffff);
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
                cursor: pointer;
                width: 100%;
                transition: transform 0.1s;
            }
            .btn:active {
                transform: scale(0.95);
            }
            .icon {
                font-size: 60px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🚀</div>
            <h1>Coming Soon</h1>
            <p>We are building something amazing. Stay tuned for the official launch!</p>
            <button class="btn" onclick="Telegram.WebApp.close()">Close App</button>
        </div>
        <script>
            // Initialize Telegram WebApp
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        </script>
    </body>
    </html>
    """
    return html
'''

if '@app.route(\'/miniapp\')' not in c:
    c = c + '\n' + MINI_APP_HTML
    with open('web.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Added /miniapp route to web.py")
else:
    print("Already exists")
