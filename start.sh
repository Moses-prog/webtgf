#!/bin/bash
python forwarder.py &
python control_bot.py &
python web.py
