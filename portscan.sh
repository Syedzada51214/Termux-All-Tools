#!/bin/bash
echo "📡 Enter IP to scan (e.g. 192.168.1.1):"
read ip
for port in {22,80,443,8080}; do
    (echo >/dev/tcp/$ip/$port) &>/dev/null && \
    echo "✅ Port $port open" || \
    echo "❌ Port $port closed"
done
