#!/bin/bash
while true
do
    sudo fuser -k 2556/tcp
    python3 start.py
done
