#!/bin/bash
mkdir -p ~/.local/bin/
PATH="$PATH:~/.local/bin/"
python3 get-pip.py --break-system-packages
pip install -r requirements.txt --break-system-packages
clear
python3 start.py
