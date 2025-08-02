#!/bin/bash

# 🔧 Termux Toolbox by Manzar
# Shows system info and tools menu

clear
echo "=================================="
echo "    🛠️  Termux Toolbox"
echo "    By: Manzar"
echo "    $(date)"
echo "=================================="

# System Info
echo "📱 Device Info:"
echo "  User: $(whoami)"
echo "  OS: $(uname -o) $(uname -r)"
echo "  Arch: $(uname -m)"
echo

# Storage
echo "💾 Storage Usage:"
df -h $HOME | awk 'NR==2 {print "  Home: " $3 "/" $2 " (" $5 " used)"}'
echo

# RAM (if available)
if command -v free &> /dev/null; then
    free -h | grep "Mem" | awk '{print "🧠 RAM: " $3 "/" $2 " used"}'
else
    echo "🧠 RAM: Not available"
fi

# Git Status (if in repo)
if git rev-parse --is-inside-work-tree &> /dev/null; then
    echo
    echo "📦 Git Repo: $(basename $(git config --get remote.origin.url))"
    echo "  Branch: $(git branch --show-current)"
    echo "  Status: $(git status --porcelain | wc -l) changes"
fi

echo
echo "🔧 Choose an action:"
echo "1) Update Termux packages"
echo "2) Backup home folder (to /storage/shared)"
echo "3) View GitHub repo status"
echo "4) Exit"
echo

read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "🔄 Updating packages..."
        pkg update && pkg upgrade -y
        ;;
    2)
        echo "📦 Backing up ~/ to shared storage..."
        cp -r $HOME ~/$HOME-backup-temp
        zip -qr /storage/shared/Termux-Home-Backup-$(date +%F).zip ~/$HOME-backup-temp
        rm -rf ~/$HOME-backup-temp
        echo "✅ Backup saved to /storage/shared/"
        ;;
    3)
        git log --oneline -5 2>/dev/null || echo "Not in a Git repo"
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option!"
        ;;
esac
