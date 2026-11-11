#!/usr/bin/env bash
# One-command take (macOS): records the main display while record-demo.mjs runs, and saves a .mov.
# screencapture cannot be stopped early without losing the file, so the length is fixed (RECORD_SECONDS).
# Needs Screen Recording permission for the app you run this from. Usage: e2e/demo/record.sh [output.mov]
set -e
cd "$(dirname "$0")/.."  # e2e/

SECS=${RECORD_SECONDS:-58}  # a little under a minute, for the 1-minute limit
OUT=${1:-$HOME/Movies/ticketlens-demo-$(date +%Y%m%d-%H%M%S).mov}
mkdir -p "$(dirname "$OUT")"

screencapture -v -V "$SECS" -D 1 "$OUT" &  # -D 1 is the main display
recorder=$!
sleep 1  # the recorder needs a moment to start
DEMO_RECORD_SECONDS=$SECS node demo/record-demo.mjs
wait "$recorder"
echo "Saved $OUT"
