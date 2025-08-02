#!/bin/bash
echo "🔧 Setting up Termux Hacker Toolkit..."
pkg update -y
pkg install git curl jq zip -y
termux-setup-storage
echo "✅ Dependencies installed!"
echo "Run: ./toolbox.sh"
