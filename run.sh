#!/bin/bash

echo "📦 Audiobook metadata tagger running every 5 minutes..."

while true; do
    echo "🔍 Scanning for new books at $(date)"
    python3 /app/enrich.py
    echo "🕔 Sleeping for 5 minutes..."
    sleep 300
done
