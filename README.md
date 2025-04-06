# Termux Python Package Installer

        A Python script to automate installation of essential packages in Termux with parallel installation support, version checking, and Android notifications.

## Features

        - ⚡ Parallel package installations (3x faster)
        - 🔍 Version-aware installation
        - 📱 Termux-API notification integration
        - 🔄 Network resilience with auto-retry
        - 🛡️ Security checks and root prevention
        - 📊 Detailed logging with timestamps
        - 🛠️ Built-in uninstaller

## Installation

        1. Clone the repository:
        ```
        git clone https://github.com/syedzada51214/Termux-All-Tools.git
        cd Termux-All-Tools
        ```

        2. Run the installer:
        ```
        python3 install_packages.py
        ```

## Configuration

        Edit `installer_config.json` to customize packages:
        ```json
        {
                "requests": ">=2.30.0",
                "numpy": "",
                "flask": ">=2.2.0"
        }
        ```

## Usage

        ### Basic Installation:
        ```
        python3 install_packages.py
        ```

        ### Custom Package List:
        1. Edit the interactive prompt
        2. Or modify `installer_config.json`

        ### Uninstall Packages:
        ```
        python3 -c "from install_packages import uninstall_packages; uninstall_packages(['requests'])"
        ```

## Package List

        | Package         | Min Version | Category       |
        |-----------------|-------------|----------------|
        | requests        | 2.28.0      | HTTP           |
        | scapy           | 2.5.0       | Networking     |
        | numpy           | 1.22.0      | Data Science   |
        | selenium        | 4.7.0       | Automation     |

## Troubleshooting

        Common fixes:
        ```
        pkg install clang libffi libjpeg-turbo
        ```

        View logs:
        ```
        cat installer_errors_*.log
        ```

## License

        MIT License - See [LICENSE](LICENSE)

