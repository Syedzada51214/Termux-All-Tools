#!/bin/bash
cd ~/Termux-All-Tools || exit
echo "🔁 Syncing with GitHub..."
git add .
git commit -m "Auto-sync: $(date)" 2>/dev/null || echo "No changes to commit"
git push
echo "✅ Pushed to GitHub"
