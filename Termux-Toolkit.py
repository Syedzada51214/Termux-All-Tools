#!/usr/bin/env python3
import subprocess
import sys
import os
import re
import json
from tqdm import tqdm
from datetime import datetime

# ===== ASCII ART LOGO =====
LOGO = r"""
  _______                       _  __ _       _ _    _ _ _ 
 |__   __|                     | |/ _| |     | | |  (_) | |
    | | ___ _ __ ___ _ __ ___  | | |_| | ___ | | | ___| | |
    | |/ _ \ '__/ _ \ '__/ __| | |  _| |/ _ \| | |/ / | | |
    | |  __/ | |  __/ |  \__ \ | | | | | (_) | |   <| | | |
    |_|\___|_|  \___|_|  |___/ |_|_| |_|\___/|_|_|\_\_|_|_|
"""

# ===== CONSTANTS =====
BACKUP_DIR = os.path.expanduser("~/.termux_backups")
LOG_FILE = os.path.join(BACKUP_DIR, "termux_toolkit.log")
PIN_FILE = os.path.expanduser("~/.termux_pinned_packages")
REPO_FILE = os.path.expanduser("~/.termux_custom_repos")
CONFIG_FILE = os.path.expanduser("~/.termux_toolkit_config.json")

# ===== COLOR THEMES =====
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ===== LOGO DISPLAY =====
def display_logo():
    """Display the Termux-Toolkit ASCII art logo"""
    color_print(LOGO, Colors.CYAN)
    color_print("Termux-Toolkit: The Ultimate Termux Package Manager", Colors.BOLD + Colors.MAGENTA)
    color_print("=" * 60, Colors.BLUE)

# ===== MAIN SCRIPT =====
def main():
    # Display logo
    display_logo()

    # Check if running in Termux
    if not os.path.exists("/data/data/com.termux/files/usr"):
        color_print("This script must be run in Termux!", Colors.RED)
        sys.exit(1)

    # Check for root-repo
    if not os.path.exists("/data/data/com.termux/files/usr/etc/apt/sources.list.d/root.list"):
        color_print("Warning: root repository not enabled!", Colors.YELLOW)
        if confirm_action("Enable root repository now?"):
            subprocess.run("pkg install root-repo -y", shell=True)

    # Main menu
    try:
        while True:
            show_menu()
            choice = input("\nSelect option (1-11): ")

            if choice == "1":
                # Basic packages installation
                color_print("\nBasic package categories:", Colors.BOLD)
                for cat in BASIC_PACKAGES:
                    color_print(f"- {cat}: {', '.join(BASIC_PACKAGES[cat])}", Colors.BLUE)

                if confirm_action("\nInstall all basic packages?"):
                    all_packages = [pkg for cat in BASIC_PACKAGES for pkg in BASIC_PACKAGES[cat]]
                    if confirm_action("Create backup before installation?"):
                        create_backup()
                    success, failed = install_packages(all_packages)
                    show_summary(success, failed)

            elif choice == "2":
                # Custom packages installation
                custom = input("\nEnter packages (space-separated): ").strip()
                if custom:
                    packages = custom.split()
                    if confirm_action("Create backup before installation?"):
                        create_backup()
                    success, failed = install_packages(packages)
                    show_summary(success, failed)
                else:
                    color_print("No packages entered!", Colors.YELLOW)

            elif choice == "3":
                # Package removal
                remove = input("\nEnter packages to remove (space-separated): ").strip()
                if remove:
                    packages = remove.split()
                    if confirm_action("Create backup before removal?"):
                        create_backup()
                    success, failed = remove_packages(packages, auto_clean=True)
                    show_summary(success, failed)
                else:
                    color_print("No packages entered!", Colors.YELLOW)

            elif choice == "4":
                # Version pinning
                pkg = input("\nEnter package name: ").strip()
                version = input("Enter version to pin (leave blank to unpin): ").strip()
                if pkg:
                    pin_package(pkg, version if version else None)
                else:
                    color_print("No package entered!", Colors.YELLOW)

            elif choice == "5":
                # Search packages
                query = input("\nEnter search query: ").strip()
                if query:
                    search_packages(query)
                else:
                    color_print("No query entered!", Colors.YELLOW)

            elif choice == "6":
                # Package info
                pkg = input("\nEnter package name: ").strip()
                if pkg:
                    package_info(pkg)
                else:
                    color_print("No package entered!", Colors.YELLOW)

            elif choice == "7":
                # Export/Import pins
                color_print("\n1. Export pinned packages", Colors.BLUE)
                color_print("2. Import pinned packages", Colors.MAGENTA)
                sub_choice = input("\nSelect option (1-2): ").strip()
                if sub_choice == "1":
                    export_pins()
                elif sub_choice == "2":
                    import_pins()
                else:
                    color_print("Invalid choice!", Colors.RED)

            elif choice == "8":
                # Backup creation
                if confirm_action("Create backup of current packages?"):
                    create_backup()

            elif choice == "9":
                # Backup restoration
                if confirm_action("Restore from backup?"):
                    restore_backup()

            elif choice == "10":
                # Interactive shell
                color_print("\nDropping into interactive shell...", Colors.YELLOW)
                subprocess.run("bash", shell=True)

            elif choice == "11":
                color_print("\nExiting...", Colors.YELLOW)
                break

            else:
                color_print("Invalid choice!", Colors.RED)

            input("\nPress Enter to continue...")

    except KeyboardInterrupt:
        color_print("\nOperation cancelled", Colors.RED)
        sys.exit(1)

# ===== INSTALLATION FUNCTIONS =====
def install_packages(packages):
    """Install packages with dependency resolution"""
    # Resolve dependencies first
    dependencies = resolve_dependencies(packages)
    all_packages = list(set(packages + dependencies))

    success = []
    failed = []

    for pkg in tqdm(all_packages, desc="Installing", unit="pkg"):
        if not validate_package(pkg):
            color_print(f"Invalid package name: {pkg}", Colors.RED)
            failed.append(pkg)
            continue

        if check_installed(pkg):
            color_print(f"Already installed: {pkg}", Colors.YELLOW)
            success.append(pkg)
            continue

        try:
            subprocess.run(
                f"pkg install -y {pkg}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            success.append(pkg)
        except subprocess.CalledProcessError:
            failed.append(pkg)

    return success, failed

# ===== REST OF THE FUNCTIONS =====
# (Include all other functions from the previous script here)

if __name__ == "__main__":
    main()
