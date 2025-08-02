#!/bin/bash
echo "📦 Creating backup..."
zip -qr /storage/shared/Termux-Backup-$(date +%F).zip $HOME
echo "✅ Backup saved to /storage/shared/"
