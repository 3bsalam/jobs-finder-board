#!/bin/bash
# Double-click this file in Finder to open the job board.
# If the board is already running it just opens the tab.

cd "$(dirname "$0")" || exit 1
PORT="${BOARD_PORT:-8765}"
URL="http://localhost:$PORT"

if curl -s -o /dev/null --max-time 2 "$URL"; then
  echo "Board already running."
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
  fi
  echo "Opened $URL. You can close this window."
  sleep 2
  exit 0
fi

echo "Starting job board on $URL"
echo "Drag a card and it saves straight to disk."
echo
echo "Leave this window open while you work. Close it, or press Ctrl-C, to stop."
echo
exec python3 dashboard/serve.py
