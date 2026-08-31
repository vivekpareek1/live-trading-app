#!/bin/bash
git pull origin main
pip3 install -r requirements.txt
pkill -f agent4_FINAL_ADAPTIVE.py
pkill -f main.py
nohup python3 agent4_FINAL_ADAPTIVE.py > agent4.log 2>&1 &
nohup python3 main.py > live.log 2>&1 &
echo "Deployed - Adaptive 5/10/15 min active"
tail -f agent4.log
