@echo off
start /B python forwarder.py
start /B python control_bot.py
python web.py
