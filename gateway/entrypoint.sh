#!/bin/sh
set -e

# ensure scripts are executable
chmod +x /switch.sh /discard.sh /control.py

# start control service in background
python3 /control.py &

# run nginx (foreground)
nginx -g "daemon off;"
