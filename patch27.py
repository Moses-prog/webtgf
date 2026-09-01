with open('forwarder.py', 'r', encoding='utf-8') as f:
    c = f.read()

import_block = '''import sys

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("forwarder.log", "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()
sys.stderr = sys.stdout
'''

c = c.replace('import asyncio\n', 'import asyncio\n' + import_block)

with open('forwarder.py', 'w', encoding='utf-8') as f:
    f.write(c)
