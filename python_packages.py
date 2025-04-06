#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import logging
from datetime import datetime
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor
from packaging import version
import json

# ======== CONFIGURATION ========
CONFIG_FILE = "installer_config.json"
DEFAULT_PACKAGES = {
    "requests": ">=2.28.0",
    "beautifulsoup4": ">=4.11.0",
    "scapy": ">=2.5.0",
    "numpy": ">=1.22.0",
    "pandas": ">=1.5.0",
    "matplotlib": ">=3.6.0",
    "flask": ">=2.2.0",
    "django": ">=4.1.0",
    "pycryptodome": ">=3.15.0",
    "paramiko": ">=3.0.0",
    "selenium": ">=4.7.0",
    "colorama": ">=0.4.0",
    "pillow": ">=9.3.0",
    "pyautogui": ">=0.9.0",
    "pynput": ">=1.7.0",
    "pyfiglet": ">=0.8.0",
    "termcolor": ">=2.2.0",
    "speedtest-cli": ">=2.1.0",
    "whois": ">=0.9.0"
}

MAX_WORKERS = 3  # Threads for parallel installation
NETWORK_RETRIES = 2  # Max retries for network failures
NETWORK_TIMEOUT = 30  # Timeout in seconds

# ======== INITIALIZATION ========
LOG_FILE = f"installer_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Terminal Colors
SUCCESS = colored("[✓]", "green")
FAIL = colored("[✗]", "red")
INFO = colored("[i]", "blue")
WARNING = colored("[!]", "yellow")
DEBUG = colored("[DEBUG]", "magenta")

# ======== CORE FUNCTIONS ========
def check_root():
    """Prevent unsafe root execution."""
    if os.geteuid() == 0:
        print(f"{WARNING} Running as root is unsafe in Termux!", flush=True)
        sys.exit(1)

def check_termux_api():
    """Check if Termux-API is available for notifications."""
    try:
        subprocess.run(["termux-notification", "--help"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        return True
    except:
        logging.warning("Termux-API not available")
        return False

def send_notification(title, message):
    """Send Android notification via Termux-API."""
    if check_termux_api():
        try:
            subprocess.run([
                "termux-notification",
                "-t", title,
                "-c", message,
                "--id", "python_installer"
            ], timeout=5)
        except subprocess.TimeoutExpired:
            logging.warning("Termux notification timed out")

def load_config():
    """Load package configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_PACKAGES

def save_config(packages):
    """Save package configuration to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(packages, f, indent=4)

def get_installed_version(package):
    """Check currently installed version of a package."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pip", "show", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':')[1].strip()
        return None
    except:
        return None

def install_package(package, spec):
    """Install package with version checking and network resilience."""
    current_version = get_installed_version(package)
    
    if current_version and version.parse(current_version) >= version.parse(spec.lstrip('>=')):
        logging.info(f"{package} {current_version} already satisfies {spec}")
        return (package, True, "Already installed")
    
    for attempt in range(NETWORK_RETRIES + 1):
        try:
            logging.debug(f"Attempt {attempt+1} for {package}")
            cmd = [
                "python3", "-m", "pip", "install",
                "--user", f"{package}{spec}" if spec else package,
                "--timeout", str(NETWORK_TIMEOUT)
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=NETWORK_TIMEOUT*2
            )
            
            return (package, True, "Success")
            
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip().split('\n')[-1]
            logging.error(f"{package} failed: {error}")
            
            if attempt == NETWORK_RETRIES:
                return (package, False, error)
            
            time.sleep(5 * (attempt + 1))  # Exponential backoff
            
        except subprocess.TimeoutExpired:
            logging.error(f"{package} timed out")
            if attempt == NETWORK_RETRIES:
                return (package, False, "Timeout")
            time.sleep(10 * (attempt + 1))

def parallel_install(packages):
    """Install packages in parallel with progress tracking."""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for package, spec in packages.items():
            futures.append(executor.submit(install_package, package, spec))
            
        completed = 0
        failed = []
        
        print(f"\n{INFO} Installing {len(packages)} packages with {MAX_WORKERS} workers...")
        
        for future in futures:
            package, success, message = future.result()
            completed += 1
            
            status = SUCCESS if success else FAIL
            print(f"{status} [{completed}/{len(packages)}] {package}: {message}")
            
            if not success:
                failed.append(package)
                
            # Update notification every 5 packages
            if completed % 5 == 0:
                send_notification(
                    "Installation Progress",
                    f"{completed}/{len(packages)} packages installed"
                )
    
    return failed

def uninstall_packages(packages):
    """Uninstall specified packages."""
    failed = []
    for package in packages:
        try:
            subprocess.run(
                ["python3", "-m", "pip", "uninstall", "-y", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"{SUCCESS} Uninstalled {package}")
        except subprocess.CalledProcessError as e:
            error = e.stderr.strip().split('\n')[-1]
            logging.error(f"{package} uninstall failed: {error}")
            failed.append(package)
    return failed

# ======== MAIN EXECUTION ========
def main():
    check_root()
    
    print("\n" + colored("» Termux Python Package Installer «", "cyan", attrs=["bold"]))
    print(colored(f"Log: {LOG_FILE}", "grey"))
    print(colored(f"Threads: {MAX_WORKERS}  Timeout: {NETWORK_TIMEOUT}s", "grey"))
    
    # Load or create config
    packages = load_config()
    
    # User customization
    print(f"\n{INFO} Current package list:")
    for i, (package, spec) in enumerate(packages.items(), 1):
        print(f"  {i}. {package} {spec}")
    
    print(f"\n{WARNING} Edit the package list? (y/N): ", end="")
    if input().lower() == "y":
        custom_packages = input("Enter packages (comma-separated, e.g., 'requests>=2.28.0, flask'): ").strip().split(",")
        for pkg_spec in custom_packages:
            if '>=' in pkg_spec:
                package, spec = pkg_spec.split('>=')
                packages[package.strip()] = f">={spec.strip()}"
            else:
                packages[pkg_spec.strip()] = ""
        save_config(packages)
    
    # Install system dependencies
    try:
        subprocess.run(
            ["pkg", "install", "-y", "python", "clang", "libffi", "libjpeg-turbo"],
            check=True,
            timeout=300
        )
    except subprocess.CalledProcessError as e:
        logging.critical(f"System package install failed: {e}")
        print(f"{FAIL} Critical system dependencies missing!")
        send_notification("Installation Failed", "System packages error")
        sys.exit(1)
    
    # Upgrade pip
    try:
        subprocess.run(
            ["python3", "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            timeout=120
        )
    except subprocess.CalledProcessError as e:
        logging.warning(f"Pip upgrade failed: {e.stderr}")
    
    # Install packages
    start_time = time.time()
    failed_packages = parallel_install(packages)
    total_time = round(time.time() - start_time, 2)
    
    # Summary
    print("\n" + colored("» Summary «", "cyan"))
    print(f"{INFO} Success: {len(packages)-len(failed_packages)}/{len(packages)}")
    print(f"{INFO} Time: {total_time}s")
    
    if failed_packages:
        print(f"\n{FAIL} Failed packages saved to {LOG_FILE}")
        send_notification(
            "Installation Complete",
            f"{len(failed_packages)} packages failed"
        )
    else:
        send_notification(
            "Installation Complete",
            "All packages installed successfully!"
        )

if __name__ == "__main__":
    main()
